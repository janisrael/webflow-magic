import os
import json
import requests
from datetime import datetime, timedelta
import glob
from typing import Dict, List, Optional, Any
import time

class ClickUpPrioritiesIntegration:
    def __init__(self):
        self.base_url = "https://api.clickup.com/api/v2"
        self.api_token = os.getenv('CLICKUP_API_TOKEN') or 'pk_126127973_W2I64C72GTEQA77GMEV0YWG0TJR3GT0J'
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'priorities')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Priority status filters - focus on high priority tasks
        self.priority_status_filters = [
            "to do",
            "planning", 
            "in progress",
            "bugs",
            "urgent",
            "critical"
        ]
        
        # Status filters to exclude
        self.excluded_status_filters = [
            "complete",
            "done", 
            "cancelled",
            "on hold"
        ]
        
        # Priority levels to focus on
        self.priority_levels = ["high", "urgent", "critical"]
        
    def generate_priorities_data(self, force_refresh=False, selected_date=None):
        """Generate priorities data with smart caching"""
        try:
            if selected_date is None:
                selected_date = datetime.now().strftime("%Y-%m-%d")
            
            print(f"🎯 Generating priorities data for: {selected_date}")
            
            # Check for existing cache first
            if not force_refresh:
                cached_data = self._get_cached_priorities_data(selected_date)
                if cached_data:
                    print("✅ Using cached priorities data")
                    return cached_data
            
            # Generate fresh data
            print("🔄 Generating fresh priorities data...")
            priorities_data = self._fetch_priorities_from_clickup(selected_date)
            
            if priorities_data:
                # Save to cache
                self._save_priorities_data(priorities_data, selected_date)
                print("💾 Priorities data saved to cache")
                return priorities_data
            else:
                print("❌ No priorities data generated")
                return None
                
        except Exception as e:
            print(f"❌ Error generating priorities data: {e}")
            return None
    
    def _fetch_priorities_from_clickup(self, selected_date):
        """Fetch high-priority tasks from ClickUp"""
        try:
            if not self.api_token:
                print("❌ No ClickUp API token found")
                return None
            
            print("📡 Fetching priorities from ClickUp...")
            
            # Get user info first
            user_info = self._get_user_info()
            if not user_info:
                return None
            
            # Get teams/spaces
            teams = self._get_teams()
            if not teams:
                return None
            
            all_priorities = []
            total_tasks = 0
            total_projects = 0
            
            # Process each team/space
            for team in teams:
                team_id = team.get('id')
                team_name = team.get('name', 'Unknown Team')
                
                print(f"🏢 Processing team: {team_name}")
                
                # Get spaces in team
                spaces = self._get_spaces(team_id)
                if not spaces:
                    continue
                
                for space in spaces:
                    space_id = space.get('id')
                    space_name = space.get('name', 'Unknown Space')
                    
                    print(f"  📁 Processing space: {space_name}")
                    
                    # Get lists/projects in space
                    lists = self._get_lists(space_id)
                    if not lists:
                        continue
                    
                    for list_item in lists:
                        list_id = list_item.get('id')
                        list_name = list_item.get('name', 'Unknown List')
                        
                        print(f"    📋 Processing list: {list_name}")
                        
                        # Get tasks with priority filters
                        tasks = self._get_priority_tasks(list_id)
                        if tasks:
                            total_tasks += len(tasks)
                            total_projects += 1
                            
                            # Add metadata to tasks
                            for task in tasks:
                                task['team_name'] = team_name
                                task['space_name'] = space_name
                                task['list_name'] = list_name
                                task['list_id'] = list_id
                                task['space_id'] = space_id
                                task['team_id'] = team_id
                            
                            all_priorities.extend(tasks)
            
            # Create priorities data structure
            priorities_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "selected_date": selected_date,
                    "total_tasks": total_tasks,
                    "total_projects": total_projects,
                    "data_source": "clickup_api",
                    "priority_filters": self.priority_status_filters,
                    "excluded_status_filters": self.excluded_status_filters,
                    "priority_levels": self.priority_levels
                },
                "priorities": all_priorities,
                "summary": {
                    "high_priority_tasks": len([t for t in all_priorities if t.get('priority', {}).get('priority') == 'high']),
                    "urgent_tasks": len([t for t in all_priorities if t.get('priority', {}).get('priority') == 'urgent']),
                    "critical_tasks": len([t for t in all_priorities if t.get('priority', {}).get('priority') == 'critical']),
                    "overdue_tasks": len([t for t in all_priorities if self._is_task_overdue(t)]),
                    "due_soon_tasks": len([t for t in all_priorities if self._is_task_due_soon(t)])
                }
            }
            
            print(f"✅ Fetched {total_tasks} priority tasks from {total_projects} projects")
            return priorities_data
            
        except Exception as e:
            print(f"❌ Error fetching priorities from ClickUp: {e}")
            return None
    
    def _get_user_info(self):
        """Get current user info"""
        try:
            response = requests.get(
                f"{self.base_url}/user",
                headers={"Authorization": self.api_token}
            )
            if response.status_code == 200:
                return response.json().get('user')
            return None
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None
    
    def _get_teams(self):
        """Get teams"""
        try:
            response = requests.get(
                f"{self.base_url}/team",
                headers={"Authorization": self.api_token}
            )
            if response.status_code == 200:
                return response.json().get('teams', [])
            return None
        except Exception as e:
            print(f"Error getting teams: {e}")
            return None
    
    def _get_spaces(self, team_id):
        """Get spaces in team"""
        try:
            response = requests.get(
                f"{self.base_url}/team/{team_id}/space",
                headers={"Authorization": self.api_token}
            )
            if response.status_code == 200:
                return response.json().get('spaces', [])
            return None
        except Exception as e:
            print(f"Error getting spaces: {e}")
            return None
    
    def _get_lists(self, space_id):
        """Get lists in space"""
        try:
            response = requests.get(
                f"{self.base_url}/space/{space_id}/list",
                headers={"Authorization": self.api_token}
            )
            if response.status_code == 200:
                return response.json().get('lists', [])
            return None
        except Exception as e:
            print(f"Error getting lists: {e}")
            return None
    
    def _get_priority_tasks(self, list_id):
        """Get priority tasks from list"""
        try:
            # Get tasks with priority filters
            params = {
                "include_closed": False,
                "subtasks": True,
                "include_location": True
            }
            
            response = requests.get(
                f"{self.base_url}/list/{list_id}/task",
                headers={"Authorization": self.api_token},
                params=params
            )
            
            if response.status_code == 200:
                tasks = response.json().get('tasks', [])
                
                # Filter for priority tasks
                priority_tasks = []
                for task in tasks:
                    # Check if task has high priority
                    priority = task.get('priority', {}).get('priority', 'normal')
                    status = task.get('status', {}).get('status', '').lower()
                    
                    # Exclude tasks with excluded statuses
                    if status in self.excluded_status_filters:
                        continue
                    
                    # Include if high priority or in priority status
                    if (priority in self.priority_levels or 
                        status in self.priority_status_filters):
                        priority_tasks.append(task)
                
                return priority_tasks
            
            return None
        except Exception as e:
            print(f"Error getting priority tasks: {e}")
            return None
    
    def _is_task_overdue(self, task):
        """Check if task is overdue"""
        due_date = task.get('due_date')
        if due_date:
            due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
            return due_datetime < datetime.now()
        return False
    
    def _is_task_due_soon(self, task):
        """Check if task is due within 3 days"""
        due_date = task.get('due_date')
        if due_date:
            due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
            three_days_from_now = datetime.now() + timedelta(days=3)
            return due_datetime <= three_days_from_now
        return False
    
    def _get_cached_priorities_data(self, selected_date):
        """Get cached priorities data"""
        try:
            # Look for cache files from today
            today = datetime.now().strftime("%Y%m%d")
            pattern = os.path.join(self.output_dir, f"priorities_{today}_*.json")
            cache_files = glob.glob(pattern)
            
            if cache_files:
                # Get the most recent cache file
                latest_cache = max(cache_files, key=os.path.getctime)
                
                with open(latest_cache, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is from the selected date
                if cached_data.get('metadata', {}).get('selected_date') == selected_date:
                    return cached_data
            
            return None
        except Exception as e:
            print(f"Error getting cached priorities data: {e}")
            return None
    
    def _save_priorities_data(self, data, selected_date):
        """Save priorities data to cache"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"priorities_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Priorities data saved to: {filename}")
            
            # Clean up old cache files (keep last 5)
            self._cleanup_old_cache()
            
        except Exception as e:
            print(f"Error saving priorities data: {e}")
    
    def _cleanup_old_cache(self):
        """Clean up old cache files, keep only the last 5"""
        try:
            cache_files = glob.glob(os.path.join(self.output_dir, "priorities_*.json"))
            if len(cache_files) > 5:
                # Sort by creation time and remove oldest
                cache_files.sort(key=os.path.getctime)
                files_to_remove = cache_files[:-5]
                
                for file_path in files_to_remove:
                    os.remove(file_path)
                    print(f"🗑️ Removed old cache file: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error cleaning up cache: {e}")
