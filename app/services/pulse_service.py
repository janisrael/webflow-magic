"""
Pulse Service - Workload Analytics and Load Balancing
"""
import requests
import json
import os
import glob
from datetime import datetime, timedelta
from collections import defaultdict

class PulseService:
    def __init__(self):
        # These would typically come from config/environment variables
        self.clickup_api_key = "pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K"  # Replace with actual key
        self.clickup_team_id = "9013605091"  # Your team ID
        self.clickup_space_id = "90132462540"
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(self.base_dir, 'output', 'pulse')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_pulse_analytics(self, analysis_date=None, debug=False):
        """
        Main method to get comprehensive workload analytics with caching
        """
        try:
            # Use provided date or default to today
            if analysis_date:
                try:
                    target_date = datetime.strptime(analysis_date, '%Y-%m-%d').date()
                except ValueError:
                    print(f"Invalid date format: {analysis_date}, using today")
                    target_date = datetime.now().date()
            else:
                target_date = datetime.now().date()
            
            print(f"🗓️ Analyzing data for: {target_date}")
            
            # For backdates, ONLY look for cached files from that specific date
            if target_date < datetime.now().date():
                print(f"📅 Backdate selected, looking for existing pulse file from {target_date}")
                cached_data = self._get_cached_pulse_data_for_date(target_date)
                if cached_data:
                    print(f"📊 Found cached pulse data from {target_date}")
                    return cached_data
                else:
                    print(f"❌ No pulse data found for {target_date}")
                    if debug:
                        demo_data = self._get_demo_data()
                        demo_data['debug_info'] = {
                            'analysis_date': str(target_date),
                            'is_backdate': True,
                            'message': f'No pulse data file found for {target_date}. Historical data only available if captured on that date.'
                        }
                        return demo_data
                    return self._get_demo_data_with_message(f"No data available for {target_date}")
            
            # For today's date, try recent cache first (3-hour rule)
            if target_date == datetime.now().date():
                cached_data = self._get_cached_pulse_data()
                if cached_data and not debug:
                    print("📊 Using recent cached pulse data")
                    return cached_data
            
            print("🔄 Generating fresh pulse data from ClickUp...")
            
            # Generate fresh data using ClickUp integration (only for today)
            fresh_data = self._generate_fresh_pulse_data(target_date, debug)
            
            if fresh_data and fresh_data.get('member_workloads'):
                # Save the fresh data (only if analyzing today)
                if target_date == datetime.now().date():
                    self._save_pulse_data(fresh_data)
                return fresh_data
            else:
                print("⚠️ No data found or failed to generate fresh data")
                if debug:
                    print("🐛 DEBUG: Returning demo data with debug info")
                    demo_data = self._get_demo_data()
                    demo_data['debug_info'] = {
                        'analysis_date': str(target_date),
                        'is_weekend': target_date.weekday() >= 5,
                        'message': 'No real data found - this could be due to weekend, no team activity, or API issues'
                    }
                    return demo_data
                return self._get_demo_data()
            
        except Exception as e:
            print(f"Error in pulse analytics: {e}")
            import traceback
            traceback.print_exc()
            return self._get_demo_data()
    
    def _get_cached_pulse_data(self):
        """
        Check for cached pulse data within 3 hours
        """
        try:
            # Look for pulse files
            pulse_files = glob.glob(os.path.join(self.output_dir, "pulse_*.json"))
            
            if not pulse_files:
                return None
            
            # Find the most recent file within 3 hours
            three_hours_ago = datetime.now() - timedelta(hours=3)
            
            for file_path in pulse_files:
                try:
                    # Extract datetime from filename: pulse_YYYYMMDD_HHMM.json
                    filename = os.path.basename(file_path)
                    datetime_str = filename.replace('pulse_', '').replace('.json', '')
                    file_datetime = datetime.strptime(datetime_str, '%Y%m%d_%H%M')
                    
                    if file_datetime >= three_hours_ago:
                        print(f"📁 Found recent pulse data: {filename}")
                        with open(file_path, 'r') as f:
                            return json.load(f)
                except Exception as e:
                    print(f"Error reading pulse file {file_path}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error checking cached pulse data: {e}")
            return None
    
    def _save_pulse_data(self, data):
        """
        Save pulse data to JSON file with timestamp
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"pulse_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Saved pulse data to: {filename}")
            
            # Clean up old files (keep only last 10)
            self._cleanup_old_pulse_files()
            
        except Exception as e:
            print(f"Error saving pulse data: {e}")
    
    def _cleanup_old_pulse_files(self):
        """
        Keep only the 10 most recent pulse files
        """
        try:
            pulse_files = glob.glob(os.path.join(self.output_dir, "pulse_*.json"))
            
            if len(pulse_files) <= 10:
                return
            
            # Sort by modification time
            pulse_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove old files
            for old_file in pulse_files[10:]:
                os.remove(old_file)
                print(f"🗑️ Cleaned up old pulse file: {os.path.basename(old_file)}")
                
        except Exception as e:
            print(f"Error cleaning up old pulse files: {e}")
    
    def _get_cached_pulse_data_for_date(self, target_date):
        """
        Check for cached pulse data from a specific date
        """
        try:
            # Look for pulse files from the specific date
            date_str = target_date.strftime('%Y%m%d')
            pattern = f"pulse_{date_str}_*.json"
            pulse_files = glob.glob(os.path.join(self.output_dir, pattern))
            
            if not pulse_files:
                print(f"📁 No pulse files found for date {target_date}")
                return None
            
            # Sort by time (filename) and get the latest one from that day
            pulse_files.sort()
            latest_file = pulse_files[-1]
            
            filename = os.path.basename(latest_file)
            print(f"📁 Found pulse file from {target_date}: {filename}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
                
            # Add metadata about the cached file
            data['cache_info'] = {
                'source_file': filename,
                'generated_date': target_date.strftime('%Y-%m-%d'),
                'is_historical': True
            }
            
            return data
            
        except Exception as e:
            print(f"Error reading cached pulse data for {target_date}: {e}")
            return None
    
    def _get_demo_data_with_message(self, message):
        """
        Get demo data with a custom message
        """
        demo_data = self._get_demo_data()
        demo_data['custom_message'] = message
        demo_data['no_historical_data'] = True
        return demo_data
    
    def _generate_fresh_pulse_data(self, target_date=None, debug=False):
        """
        Generate fresh pulse data using ClickUp integration
        """
        try:
            from services.clickup_pulse_integration import ClickUpPulseIntegration
            
            clickup_integration = ClickUpPulseIntegration(
                api_token=self.clickup_api_key,
                space_id=self.clickup_space_id
            )
            
            return clickup_integration.generate_pulse_analytics(target_date, debug)
            
        except ImportError:
            print("⚠️ ClickUp integration not available, using demo data")
            return None
        except Exception as e:
            print(f"Error generating fresh pulse data: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            return None
    
    def _get_demo_data(self):
        """
        Return demo data when API is not available
        """
        return {
            "member_workloads": {
                "wiktor": {
                    "username": "wiktor",
                    "active_tasks": 4,
                    "projects_count": 2,
                    "projects": [
                        {"name": "E-commerce Website", "due_date": "2025-08-20T00:00:00"},
                        {"name": "Mobile App Development", "due_date": "2025-08-30T00:00:00"}
                    ],
                    "urgent_tasks": 1,
                    "high_priority_tasks": 1,
                    "due_soon_tasks": 2,
                    "workload_score": 145.5,
                    "status": "high",
                    "total_time_estimate": 1260,
                    "total_time_spent": 210,
                    "remaining_time": 1050
                },
                "sarah": {
                    "username": "sarah",
                    "active_tasks": 2,
                    "projects_count": 2,
                    "projects": [
                        {"name": "E-commerce Website", "due_date": "2025-08-20T00:00:00"},
                        {"name": "Marketing Campaign", "due_date": "2025-08-25T00:00:00"}
                    ],
                    "urgent_tasks": 0,
                    "high_priority_tasks": 0,
                    "due_soon_tasks": 0,
                    "workload_score": 75.2,
                    "status": "balanced",
                    "total_time_estimate": 420,
                    "total_time_spent": 135,
                    "remaining_time": 285
                },
                "alex": {
                    "username": "alex",
                    "active_tasks": 1,
                    "projects_count": 1,
                    "projects": [
                        {"name": "E-commerce Website", "due_date": "2025-08-20T00:00:00"}
                    ],
                    "urgent_tasks": 0,
                    "high_priority_tasks": 1,
                    "due_soon_tasks": 1,
                    "workload_score": 45.0,
                    "status": "light",
                    "total_time_estimate": 200,
                    "total_time_spent": 150,
                    "remaining_time": 50
                }
            },
            "project_analytics": {
                "proj_1": {
                    "name": "E-commerce Website",
                    "active_tasks": 5,
                    "assigned_members": ["wiktor", "sarah", "alex"],
                    "member_count": 3,
                    "total_time_estimate": 1200,
                    "due_date": "2025-08-20T00:00:00",
                    "priority": "high",
                    "status": "active"
                },
                "proj_2": {
                    "name": "Mobile App Development", 
                    "active_tasks": 2,
                    "assigned_members": ["wiktor"],
                    "member_count": 1,
                    "total_time_estimate": 600,
                    "due_date": "2025-08-30T00:00:00",
                    "priority": "medium",
                    "status": "active"
                }
            },
            "timeline_analysis": {
                "urgent_deadlines": [],
                "upcoming_deadlines": [],
                "overdue_tasks": [],
                "high_priority_tasks": [],
                "deadline_pressure_by_member": {}
            },
            "load_balance_insights": {
                "highest_workload": {
                    "username": "wiktor",
                    "score": 145.5,
                    "status": "high"
                },
                "lowest_workload": {
                    "username": "alex",
                    "score": 45.0,
                    "status": "light"
                },
                "overloaded_members": [],
                "available_members": [
                    {"username": "alex", "workload": {"status": "light"}}
                ],
                "transfer_suggestions": [
                    {
                        "from_member": "wiktor",
                        "to_member": "alex", 
                        "task": {"name": "Database Schema"},
                        "reason": "Balance workload - wiktor is high, alex has light load"
                    }
                ]
            },
            "overview_stats": {
                "total_members": 3,
                "total_projects": 3,
                "total_active_tasks": 7,
                "avg_tasks_per_member": 2.3,
                "avg_workload_score": 88.6,
                "workload_distribution": {"high": 1, "balanced": 1, "light": 1},
                "health_score": 75
            },
            "recommendations": [
                {
                    "type": "workload_warning",
                    "priority": "high",
                    "member": "wiktor",
                    "message": "wiktor has high workload with 4 active tasks across 2 projects, one project due soon",
                    "action": "Consider redistributing tasks or extending deadlines"
                }
            ],
            "last_updated": datetime.now().isoformat(),
            "data_source": "demo_data"
        }