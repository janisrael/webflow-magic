import os
import json
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalendarTasksService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(self.base_dir, 'output', 'calendar')
        self.cache_dir = os.path.join(self.output_dir, 'tasks')
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Calendar-specific task statuses and priorities
        self.calendar_statuses = [
            'in progress', 'qa', 'bugs', 'review', 'testing', 'pending', 'to do'
        ]
        
        self.calendar_priorities = ['urgent', 'high', 'normal']
        
    def get_latest_cache_file(self) -> Optional[str]:
        """Get the most recent calendar tasks cache file from today"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            pattern = os.path.join(self.cache_dir, f'calendar_tasks_{today}_*.json')
            files = glob.glob(pattern)
            
            if not files:
                return None
                
            # Sort by modification time and get the latest
            latest_file = max(files, key=os.path.getmtime)
            return latest_file
            
        except Exception as e:
            logger.error(f"Error getting latest cache file: {e}")
            return None
    
    def is_cache_recent(self, cache_file: str, hours: int = 3) -> bool:
        """Check if cache file is recent enough"""
        try:
            if not os.path.exists(cache_file):
                return False
                
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            time_diff = datetime.now() - file_time
            
            return time_diff.total_seconds() < (hours * 3600)
            
        except Exception as e:
            logger.error(f"Error checking cache age: {e}")
            return False
    
    def is_cache_from_today(self, cache_file: str) -> bool:
        """Check if cache file is from today"""
        try:
            if not os.path.exists(cache_file):
                return False
                
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            today = datetime.now().date()
            
            return file_time.date() == today
            
        except Exception as e:
            logger.error(f"Error checking if cache is from today: {e}")
            return False
    
    def load_cached_data(self, cache_file: str) -> Dict:
        """Load data from cache file"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Loaded cached calendar tasks from {cache_file}")
                return data
        except Exception as e:
            logger.error(f"Error loading cached data: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_to_cache(self, data: Dict) -> str:
        """Save data to cache file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f'calendar_tasks_{timestamp}.json'
            filepath = os.path.join(self.cache_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Saved calendar tasks to cache: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            return None
    
    def filter_tasks_for_calendar(self, all_tasks: List[Dict]) -> List[Dict]:
        """Filter tasks that are relevant for calendar display"""
        calendar_tasks = []
        
        for task in all_tasks:
            # Handle status - it can be a string or an object
            status_obj = task.get('status', {})
            if isinstance(status_obj, dict):
                status = status_obj.get('status', '').lower()
            else:
                status = str(status_obj).lower()
            
            # Handle priority
            priority_obj = task.get('priority', {})
            if isinstance(priority_obj, dict):
                priority = priority_obj.get('priority', '').lower()
            else:
                priority = str(priority_obj).lower()
            
            # Include tasks that are active and relevant for calendar
            is_active_status = status in self.calendar_statuses
            is_high_priority = priority in ['urgent', 'high']
            has_due_date = task.get('due_date') is not None
            
            if (is_active_status or is_high_priority) and has_due_date:
                # Add calendar-specific metadata
                task['calendar_relevant'] = True
                task['calendar_reason'] = 'active_status' if is_active_status else 'high_priority'
                calendar_tasks.append(task)
        
        return calendar_tasks
    
    def get_calendar_tasks(self, force_refresh: bool = False, check_cache_only: bool = False, check_today_cache: bool = False) -> Dict:
        """Get calendar tasks with smart caching logic"""
        try:
            # Check cache first
            latest_cache = self.get_latest_cache_file()
            
            if check_cache_only:
                logger.info("📁 Check cache only mode - looking for recent cache...")
                if latest_cache and self.is_cache_recent(latest_cache, 3):
                    logger.info("✅ Found recent cache (< 3 hours old)")
                    return self.load_cached_data(latest_cache)
                else:
                    logger.info("📁 No recent cached data found")
                    return {'success': False, 'message': 'No recent cache found'}
            
            if check_today_cache:
                logger.info("📁 Check today cache mode - looking for today's cache...")
                if latest_cache and self.is_cache_from_today(latest_cache):
                    logger.info("✅ Found today's cached data")
                    return self.load_cached_data(latest_cache)
                else:
                    logger.info("📁 No today's cached data found")
                    return {'success': False, 'message': 'No today cache found'}
            
            # Normal flow - check if we need to refresh
            if not force_refresh and latest_cache and self.is_cache_recent(latest_cache, 3):
                logger.info("✅ Using recent cached data (< 3 hours old)")
                return self.load_cached_data(latest_cache)
            
            if not force_refresh and latest_cache and self.is_cache_from_today(latest_cache):
                logger.info("✅ Using today's cached data")
                return self.load_cached_data(latest_cache)
            
            # Need to fetch fresh data
            logger.info("🔄 Fetching fresh calendar tasks data...")
            
            # Use a simple workaround - call the priorities API directly
            import requests
            
            try:
                response = requests.get('http://localhost:5022/api/priorities-data?force_refresh=true', timeout=30)
                priorities_data = response.json()
                
                if not priorities_data.get('priorities'):
                    logger.error("❌ Failed to fetch priorities data from API")
                    return {
                        'success': False,
                        'error': 'Failed to fetch priorities data',
                        'message': 'Could not retrieve tasks from ClickUp'
                    }
                
                # Filter tasks for calendar
                all_tasks = priorities_data.get('priorities', [])  # Priorities API uses 'priorities' key
                calendar_tasks = self.filter_tasks_for_calendar(all_tasks)
                
            except Exception as e:
                logger.error(f"❌ Error calling priorities API: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to call priorities API'
                }
            
            # Create response structure
            calendar_data = {
                'success': True,
                'total_tasks': len(all_tasks),
                'calendar_tasks': len(calendar_tasks),
                'tasks': calendar_tasks,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'cache_file': latest_cache,
                    'filter_criteria': {
                        'statuses': self.calendar_statuses,
                        'priorities': self.calendar_priorities
                    }
                }
            }
            
            # Cache the data
            cache_file = self.save_to_cache(calendar_data)
            if cache_file:
                calendar_data['metadata']['cache_file'] = cache_file
            
            logger.info(f"✅ Calendar tasks processed: {len(calendar_tasks)} relevant tasks out of {len(all_tasks)} total")
            return calendar_data
            
        except Exception as e:
            logger.error(f"❌ Error in get_calendar_tasks: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process calendar tasks'
            }
    
    def get_demo_calendar_tasks(self) -> Dict:
        """Return demo calendar tasks data"""
        demo_tasks = [
            {
                'id': 'demo_1',
                'name': 'Email updates bug - not receiving win notifications',
                'status': 'in progress',
                'due_date': str(int(datetime.now().timestamp() * 1000)),
                'priority': {'priority': 'urgent', 'color': '#f50000'},
                'assignees': [{'username': 'Tricia Kennedy'}, {'username': 'Jan'}],
                'list_name': 'Bug Fixes',
                'project_name': 'Email System',
                'url': 'https://app.clickup.com/t/demo_1',
                'calendar_relevant': True,
                'calendar_reason': 'active_status'
            },
            {
                'id': 'demo_2',
                'name': 'Photo acceptance issues for tickets',
                'status': 'qa',
                'due_date': str(int((datetime.now() + timedelta(days=1)).timestamp() * 1000)),
                'priority': {'priority': 'urgent', 'color': '#f50000'},
                'assignees': [{'username': 'Tricia Kennedy'}],
                'list_name': 'QA Testing',
                'project_name': 'Photo System',
                'url': 'https://app.clickup.com/t/demo_2',
                'calendar_relevant': True,
                'calendar_reason': 'active_status'
            },
            {
                'id': 'demo_3',
                'name': 'App incorrectly showing no winners',
                'status': 'bugs',
                'due_date': str(int((datetime.now() + timedelta(days=2)).timestamp() * 1000)),
                'priority': {'priority': 'high', 'color': '#ff9800'},
                'assignees': [{'username': 'Jan'}],
                'list_name': 'Bug Fixes',
                'project_name': 'Winner System',
                'url': 'https://app.clickup.com/t/demo_3',
                'calendar_relevant': True,
                'calendar_reason': 'high_priority'
            }
        ]
        
        return {
            'success': True,
            'total_tasks': len(demo_tasks),
            'calendar_tasks': len(demo_tasks),
            'tasks': demo_tasks,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'cache_file': None,
                'demo_data': True,
                'filter_criteria': {
                    'statuses': self.calendar_statuses,
                    'priorities': self.calendar_priorities
                }
            }
        }
