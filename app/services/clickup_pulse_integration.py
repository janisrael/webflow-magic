#!/usr/bin/env python3
"""
ClickUp Pulse Integration - Enhanced with JSON File Caching and AI Project Complexity Analysis
Modified from the original ClickUp analytics script for Pulse dashboard integration
FIXED: Negative remaining time handling and added computation transparency
"""

import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict
import os
import glob
import re

class ClickUpPulseIntegration:
    def __init__(self, api_token, space_id):
        self.api_token = api_token or 'pk_126127973_W2I64C72GTEQA77GMEV0YWG0TJR3GT0J'
        self.space_id = space_id  # Use your space ID here
        self.headers = {'Authorization': self.api_token}
        self.base_url = 'https://api.clickup.com/api/v2'
        
        # Working hours configuration
        self.WORKDAY_START_HOUR = 9
        self.WORKDAY_END_HOUR = 17
        self.LUNCH_BREAK_START = 12
        self.LUNCH_BREAK_END = 12.5
        self.WORKING_HOURS_PER_DAY = 7.5
        
        # JSON Caching setup
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(self.base_dir, 'output', 'pulse')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def test_api_connection(self):
        """Test the API connection and return status"""
        try:
            print("🔍 Testing ClickUp API connection...")
            
            # Validate API token format
            if not self.api_token or len(self.api_token) < 20:
                print("❌ Invalid API token format - token too short")
                return False
                
            if not self.api_token.startswith('pk_'):
                print("❌ Invalid API token format - should start with 'pk_'")
                return False
                
            print(f"🔑 Using API token: {self.api_token[:10]}...{self.api_token[-10:]}")
            print(f"🌐 Base URL: {self.base_url}")
            print(f"📋 Headers: {self.headers}")
            
            # Test basic API access
            resp = requests.get(f"{self.base_url}/team", headers=self.headers)
            print(f"📡 Team API Response Status: {resp.status_code}")
            
            if resp.status_code == 200:
                teams_data = resp.json()
                teams = teams_data.get('teams', [])
                print(f"✅ API connection successful! Found {len(teams)} teams")
                return True
            elif resp.status_code == 401:
                print("🔐 Authentication failed - check your API token")
                print("💡 Make sure your API token is valid and has the correct permissions")
                return False
            elif resp.status_code == 403:
                print("🚫 Permission denied - check your API permissions")
                print("💡 Your token may not have access to team information")
                return False
            elif resp.status_code == 429:
                print("⏱️ Rate limit exceeded - try again later")
                return False
            else:
                print(f"❌ Unexpected response: {resp.status_code}")
                try:
                    error_data = resp.json()
                    if 'err' in error_data:
                        print(f"📄 Error details: {error_data['err']}")
                except:
                    print(f"📄 Response text: {resp.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ API connection test failed: {e}")
            print("🔧 Troubleshooting tips:")
            print("   1. Check if your API token is correct")
            print("   2. Verify the token has the right permissions")
            print("   3. Ensure you have internet connectivity")
            print("   4. Check if ClickUp API is accessible")
            return False
    
    def _make_api_request_with_retry(self, url, max_retries=3, base_delay=1):
        """Make API request with exponential backoff for rate limiting"""
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, headers=self.headers)
                
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get('retry-after', base_delay * (2 ** attempt)))
                    print(f"⏱️ Rate limited, waiting {retry_after} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                
                return resp
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                print(f"🌐 Request failed, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
        
        return None
    
    def get_task_details(self, task_id):
        """Fetch detailed information for a specific task from ClickUp"""
        try:
            print(f"🔍 Fetching task details for task ID: {task_id}")
            
            # Make API request to get task details
            url = f"{self.base_url}/task/{task_id}"
            resp = self._make_api_request_with_retry(url)
            
            if resp and resp.status_code == 200:
                task_data = resp.json()
                print(f"✅ Successfully fetched task details for {task_id}")
                
                # Extract and format task details
                task_details = {
                    'id': task_data.get('id'),
                    'name': task_data.get('name'),
                    'text_content': task_data.get('text_content', ''),
                    'description': task_data.get('description', ''),
                    'status': task_data.get('status', {}).get('status', 'Unknown'),
                    'priority': task_data.get('priority', {}),
                    'assignees': task_data.get('assignees', []),
                    'due_date': task_data.get('due_date'),
                    'date_created': task_data.get('date_created'),
                    'date_updated': task_data.get('date_updated'),
                    'time_estimate': task_data.get('time_estimate'),
                    'time_spent': task_data.get('time_spent'),
                    'url': task_data.get('url'),
                    'project_id': task_data.get('list', {}).get('id'),
                    'project_name': task_data.get('list', {}).get('name'),
                    'space_id': task_data.get('space', {}).get('id'),
                    'space_name': task_data.get('space', {}).get('name'),
                    'tags': task_data.get('tags', []),
                    'checklists': task_data.get('checklists', []),
                    'comments': self._get_task_comments(task_id)
                }
                
                return task_details
            elif resp and resp.status_code == 404:
                print(f"❌ Task {task_id} not found")
                return None
            elif resp and resp.status_code == 401:
                print(f"🔐 Unauthorized access to task {task_id}")
                return None
            else:
                print(f"❌ Failed to fetch task details: {resp.status_code if resp else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching task details for {task_id}: {e}")
            return None

    def get_project_details(self, project_id):
        """Fetch detailed information for a specific project from ClickUp"""
        try:
            print(f"🔍 Fetching project details for project ID: {project_id}")
            
            # Make API request to get project details
            url = f"{self.base_url}/list/{project_id}"
            resp = self._make_api_request_with_retry(url)
            
            if resp and resp.status_code == 200:
                project_data = resp.json()
                print(f"✅ Successfully fetched project details for {project_id}")
                
                # Extract and format project details
                project_details = {
                    'id': project_data.get('id'),
                    'name': project_data.get('name'),
                    'description': project_data.get('description', ''),
                    'status': project_data.get('status'),
                    'date_created': project_data.get('date_created'),
                    'date_updated': project_data.get('date_updated'),
                    'url': project_data.get('url'),
                    'space_id': project_data.get('space', {}).get('id'),
                    'space_name': project_data.get('space', {}).get('name'),
                    'folder_id': project_data.get('folder', {}).get('id'),
                    'folder_name': project_data.get('folder', {}).get('name'),
                    'task_count': project_data.get('task_count', {}),
                    'start_date': project_data.get('start_date'),
                    'due_date': project_data.get('due_date'),
                    'archived': project_data.get('archived', False)
                }
                
                return project_details
            elif resp and resp.status_code == 404:
                print(f"❌ Project {project_id} not found")
                return None
            elif resp and resp.status_code == 401:
                print(f"🔐 Unauthorized access to project {project_id}")
                return None
            else:
                print(f"❌ Failed to fetch project details: {resp.status_code if resp else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching project details for {project_id}: {e}")
            return None

    def _get_task_comments(self, task_id):
        """Fetch comments for a specific task"""
        try:
            url = f"{self.base_url}/task/{task_id}/comment"
            resp = self._make_api_request_with_retry(url)
            
            if resp and resp.status_code == 200:
                comments_data = resp.json()
                comments = comments_data.get('comments', [])
                
                # Format comments for display
                formatted_comments = []
                for comment in comments[:5]:  # Limit to 5 most recent comments
                    formatted_comments.append({
                        'id': comment.get('id'),
                        'text': comment.get('comment_text', ''),
                        'user': comment.get('user', {}).get('username', 'Unknown'),
                        'date_created': comment.get('date_created'),
                        'date_updated': comment.get('date_updated')
                    })
                
                return formatted_comments
            else:
                print(f"⚠️ Could not fetch comments for task {task_id}: {resp.status_code if resp else 'No response'}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching comments for task {task_id}: {e}")
            return []

    def get_diagnostic_info(self):
        """Get diagnostic information for troubleshooting"""
        return {
            "api_token_length": len(self.api_token) if self.api_token else 0,
            "api_token_format": "valid" if self.api_token and self.api_token.startswith('pk_') else "invalid",
            "space_id": self.space_id,
            "base_url": self.base_url,
            "headers": {k: v[:10] + "..." if k == 'Authorization' and len(v) > 20 else v for k, v in self.headers.items()},
            "output_dir": self.output_dir,
            "output_dir_exists": os.path.exists(self.output_dir),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "requests_version": requests.__version__ if hasattr(requests, '__version__') else "unknown"
        }
    
    def _validate_space_id(self, space_id):
        """Validate if a space ID exists and is accessible"""
        try:
            if not space_id or not isinstance(space_id, str):
                return False
                
            # Test if we can access the space
            resp = requests.get(f"{self.base_url}/space/{space_id}", headers=self.headers)
            
            if resp.status_code == 200:
                space_data = resp.json()
                space_name = space_data.get('name', 'Unknown')
                print(f"✅ Space ID {space_id} is valid: {space_name}")
                return True
            elif resp.status_code == 404:
                print(f"❌ Space ID {space_id} not found")
                return False
            elif resp.status_code == 403:
                print(f"🚫 No access to space ID {space_id}")
                return False
            else:
                print(f"❓ Unexpected response for space {space_id}: {resp.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error validating space ID {space_id}: {e}")
            return False

    def get_all_available_spaces(self):
        """Get all spaces available to the user"""
        try:
            print("🔍 Fetching all available spaces...")
            
            # First get all teams
            resp = requests.get(f"{self.base_url}/team", headers=self.headers)
            
            if resp.status_code == 401:
                print("🔐 Authentication failed - check your API token")
                return {}
            elif resp.status_code == 403:
                print("🚫 Permission denied - check your API permissions")
                return {}
            
            resp.raise_for_status()
            teams_data = resp.json()
            teams = teams_data.get('teams', [])
            
            if not teams:
                print("⚠️ No teams found - check your API permissions")
                return {}
            
            all_spaces = {}
            
            for team in teams:
                team_id = team.get('id')
                team_name = team.get('name', 'Unknown Team')
                
                # Get spaces for this team
                try:
                    resp = requests.get(f"{self.base_url}/team/{team_id}/space", headers=self.headers)
                    resp.raise_for_status()
                    spaces = resp.json().get('spaces', [])
                    
                    for space in spaces:
                        space_id = space.get('id')
                        space_name = space.get('name', 'Unknown Space')
                        
                        all_spaces[space_id] = {
                            'name': f"{team_name} / {space_name}",
                            'team_name': team_name,
                            'space_name': space_name,
                            'team_id': team_id
                        }
                        
                except Exception as e:
                    print(f"Error getting spaces for team {team_name}: {e}")
                    continue
            
            print(f"✅ Found {len(all_spaces)} total spaces across {len(teams)} teams")
            return all_spaces
            
        except Exception as e:
            print(f"❌ Error getting available spaces: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def troubleshoot_setup(self):
        """Provide comprehensive troubleshooting information"""
        print("🔧 ClickUp Pulse Integration Troubleshooting")
        print("=" * 50)
        
        # Get diagnostic info
        diag = self.get_diagnostic_info()
        print(f"🔑 API Token: {'✓ Valid format' if diag['api_token_format'] == 'valid' else '✗ Invalid format'}")
        print(f"🌐 Base URL: {diag['base_url']}")
        print(f"📁 Output Directory: {'✓ Exists' if diag['output_dir_exists'] else '✗ Missing'}")
        print(f"🐍 Python Version: {diag['python_version']}")
        print(f"📡 Requests Version: {diag['requests_version']}")
        
        print("\n🔍 Testing API Connection...")
        if self.test_api_connection():
            print("✅ API connection successful!")
            
            print("\n🔍 Testing Space Access...")
            if self.space_id:
                if self._validate_space_id(self.space_id):
                    print(f"✅ Space {self.space_id} is accessible")
                else:
                    print(f"❌ Space {self.space_id} is not accessible")
            else:
                print("⚠️ No space ID configured")
                
            print("\n🔍 Available Spaces:")
            spaces = self.get_all_available_spaces()
            if spaces:
                for space_id, space_info in list(spaces.items())[:5]:  # Show first 5
                    print(f"   {space_id}: {space_info['name']}")
                if len(spaces) > 5:
                    print(f"   ... and {len(spaces) - 5} more")
            else:
                print("   ❌ No spaces found")
        else:
            print("❌ API connection failed!")
            print("\n💡 Common Solutions:")
            print("   1. Check your API token at: https://app.clickup.com/settings/apps")
            print("   2. Ensure the token has 'Read' permissions for teams and spaces")
            print("   3. Verify your internet connection")
            print("   4. Check if ClickUp is experiencing downtime")
        
        print("\n" + "=" * 50)
    
    def _generate_enhanced_rule_based_summary(self, member_workloads, overview_stats, load_balance, recommendations):
        """
        Generate enhanced rule-based analytics when AI is not available
        """
        try:
            enhanced_analysis = {}
            
            # Workload distribution analysis
            if member_workloads:
                workload_scores = [w.get('workload_score', 0) for w in member_workloads.values()]
                if workload_scores:
                    enhanced_analysis['workload_distribution_insights'] = {
                        'score_range': f"{min(workload_scores)} - {max(workload_scores)}",
                        'variance': max(workload_scores) - min(workload_scores),
                        'distribution_type': 'balanced' if max(workload_scores) - min(workload_scores) < 50 else 'imbalanced',
                        'recommendation': 'Consider redistributing tasks' if max(workload_scores) - min(workload_scores) > 100 else 'Workload appears balanced'
                    }
            
            # Project complexity analysis
            if overview_stats.get('total_projects', 0) > 0:
                enhanced_analysis['project_complexity_insights'] = {
                    'total_projects': overview_stats.get('total_projects', 0),
                    'avg_tasks_per_project': round(overview_stats.get('total_active_tasks', 0) / max(overview_stats.get('total_projects', 1), 1), 1),
                    'complexity_assessment': 'High complexity' if overview_stats.get('avg_tasks_per_project', 0) > 15 else 'Moderate complexity' if overview_stats.get('avg_tasks_per_project', 0) > 8 else 'Low complexity'
                }
            
            # Team efficiency metrics
            if member_workloads:
                active_members = len([w for w in member_workloads.values() if w.get('active_tasks', 0) > 0])
                total_members = len(member_workloads)
                enhanced_analysis['team_efficiency_metrics'] = {
                    'active_members': active_members,
                    'total_members': total_members,
                    'utilization_rate': round((active_members / total_members) * 100, 1),
                    'efficiency_score': 'High' if (active_members / total_members) > 0.8 else 'Medium' if (active_members / total_members) > 0.6 else 'Low'
                }
            
            # Priority analysis
            urgent_tasks = sum(w.get('urgent_tasks', 0) for w in member_workloads.values())
            high_priority_tasks = sum(w.get('high_priority_tasks', 0) for w in member_workloads.values())
            enhanced_analysis['priority_analysis'] = {
                'urgent_tasks': urgent_tasks,
                'high_priority_tasks': high_priority_tasks,
                'priority_pressure': 'High' if urgent_tasks > 3 else 'Medium' if urgent_tasks > 1 else 'Low',
                'recommendation': 'Review urgent task priorities' if urgent_tasks > 3 else 'Monitor priority distribution'
            }
            
            # Time management insights
            time_overruns = [w for w in member_workloads.values() if w.get('remaining_time_status', {}).get('is_over_time', False)]
            if time_overruns:
                enhanced_analysis['time_management_insights'] = {
                    'members_with_overruns': len(time_overruns),
                    'total_overrun_hours': sum(w.get('remaining_time_status', {}).get('over_time_hours', 0) for w in time_overruns),
                    'time_estimation_accuracy': 'Needs improvement' if len(time_overruns) > len(member_workloads) * 0.3 else 'Generally accurate',
                    'recommendation': 'Review time estimation processes and provide additional training'
                }
            
            return enhanced_analysis
            
        except Exception as e:
            print(f"Error in enhanced rule-based analysis: {e}")
            return {}
    
    def quick_test(self):
        """Quick test method for users to verify their setup"""
        print("🧪 Quick ClickUp API Test")
        print("=" * 30)
        
        # Test basic connection
        if self.test_api_connection():
            print("✅ Basic API connection: PASSED")
            
            # Test space access if space_id is set
            if self.space_id:
                if self._validate_space_id(self.space_id):
                    print("✅ Space access: PASSED")
                else:
                    print("❌ Space access: FAILED")
            else:
                print("⚠️ Space access: SKIPPED (no space_id)")
                
            print("✅ Overall test: PASSED")
            return True
        else:
            print("❌ Basic API connection: FAILED")
            print("❌ Overall test: FAILED")
            return False


    def generate_pulse_analytics_with_ai(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None, force_refresh=False, hf_token=None):
        """
        Generate pulse analytics with AI-enhanced summary and project complexity analysis
        """
        try:
            # First generate regular analytics
            analytics_data = self.generate_pulse_analytics(
                target_date, debug, status_filters, member_filters, space_filters, force_refresh, hf_token
            )
            
            if analytics_data and hf_token:
                # Replace summary with AI-enhanced version
                print("🤖 Generating AI-enhanced summary...")
                intelligent_summary = self._generate_intelligent_summary(analytics_data, use_ai=True, hf_token=hf_token)
                analytics_data["intelligent_summary"] = intelligent_summary
                print("✅ AI-enhanced summary generated")
                
                # Generate comprehensive assessment
                print("📊 Generating comprehensive team assessment...")
                comprehensive_assessment = self.generate_comprehensive_assessment(analytics_data)
                if comprehensive_assessment:
                    analytics_data["comprehensive_assessment"] = comprehensive_assessment
                    print("✅ Comprehensive assessment generated")
                else:
                    print("⚠️ Assessment generation failed, continuing without assessment")
            
            return analytics_data
            
        except Exception as e:
            print(f"❌ Error generating AI-enhanced analytics: {e}")
            return self.generate_pulse_analytics(target_date, debug, status_filters, member_filters, space_filters, force_refresh)

    def generate_pulse_analytics(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None, force_refresh=False, hf_token=None):
        """
        Generate comprehensive pulse analytics from ClickUp data with JSON caching and AI complexity analysis
        """
        try:
            # Use provided date or default to today
            if target_date:
                if isinstance(target_date, str):
                    try:
                        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Invalid date format: {target_date}, using today")
                        target_date = datetime.now().date()
                elif hasattr(target_date, 'date'):
                    target_date = target_date.date()
            else:
                target_date = datetime.now().date()

            print(f"🗓️ Analyzing data for: {target_date}")
            
            # Check if we're outside working hours (but only if not forcing refresh)
            current_hour = datetime.now().hour
            outside_working_hours = current_hour < self.WORKDAY_START_HOUR or current_hour >= self.WORKDAY_END_HOUR
            
            if outside_working_hours and not force_refresh:
                print(f"🌙 Outside working hours ({self.WORKDAY_START_HOUR}:00 - {self.WORKDAY_END_HOUR}:00). Current time: {current_hour}:00")
                print("📁 Looking for latest cached data from today...")
                
                # Try to get the latest cached data from today
                latest_today_data = self._get_latest_cached_data_from_today()
                if latest_today_data:
                    print(f"✅ Found latest cached data from today: {latest_today_data.get('cache_info', {}).get('source_file', 'unknown')}")
                    latest_today_data['cache_info']['outside_working_hours'] = True
                    latest_today_data['cache_info']['current_time'] = f"{current_hour}:00"
                    latest_today_data['cache_info']['working_hours'] = f"{self.WORKDAY_START_HOUR}:00 - {self.WORKDAY_END_HOUR}:00"
                    return latest_today_data
                else:
                    print("⚠️ No cached data found from today, falling back to demo data")
                    demo_data = self._get_demo_data()
                    demo_data['cache_info'] = {
                        'outside_working_hours': True,
                        'current_time': f"{current_hour}:00",
                        'working_hours': f"{self.WORKDAY_START_HOUR}:00 - {self.WORKDAY_END_HOUR}:00",
                        'message': 'No cached data available from today'
                    }
                    return demo_data
            elif outside_working_hours and force_refresh:
                print(f"🌙 Outside working hours ({self.WORKDAY_START_HOUR}:00 - {self.WORKDAY_END_HOUR}:00). Current time: {current_hour}:00")
                print("🔄 Force refresh requested - bypassing working hours restriction and generating fresh data...")
            
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
            
            # For today's date, try recent cache first (3-hour rule) - unless force refresh
            if target_date == datetime.now().date() and not force_refresh:
                cached_data = self._get_cached_pulse_data()
                if cached_data and not debug:
                    print("📊 Using recent cached pulse data")
                    return cached_data
            
            if force_refresh:
                print("🔄 Force refresh requested - bypassing cache...")
            
            print("🔄 Generating fresh pulse data from ClickUp...")
            
            # Test API connection first
            if not self.test_api_connection():
                print("❌ API connection test failed - cannot proceed with real data")
                if debug:
                    demo_data = self._get_demo_data()
                    demo_data['debug_info'] = {
                        'analysis_date': str(target_date),
                        'api_connection': 'failed',
                        'message': 'API connection test failed - check your API token and permissions'
                    }
                    return demo_data
                return self._get_demo_data_with_message("API connection failed - check your API token and permissions")
            
            # Validate space ID if provided
            if space_filters and len(space_filters) == 1:
                space_id = space_filters[0]
                if not self._validate_space_id(space_id):
                    print(f"❌ Invalid space ID: {space_id}")
                    if debug:
                        demo_data = self._get_demo_data()
                        demo_data['debug_info'] = {
                            'analysis_date': str(target_date),
                            'space_validation': 'failed',
                            'message': f'Invalid space ID: {space_id}'
                        }
                        return demo_data
                    return self._get_demo_data_with_message(f"Invalid space ID: {space_id}")
            
            # Generate fresh data using ClickUp API
            if space_filters and len(space_filters) > 1:
                print("🏢 Processing multiple spaces - this may take longer due to rate limits...")
                # Add delay between spaces to avoid rate limiting
                fresh_data = self._generate_multi_space_pulse_data_with_delay(target_date, debug, status_filters, member_filters, space_filters, hf_token)
            else:
                # Single space - use existing logic
                self.space_id = space_filters[0] if space_filters else '90132462540'
                fresh_data = self._generate_fresh_pulse_data(target_date, debug, status_filters, member_filters, hf_token)
            
            print(f"🔍 Fresh data result: {type(fresh_data)}")
            
            if fresh_data and fresh_data.get('member_workloads'):
                print(f'✅ Fresh data generated successfully')
                # Save the fresh data (only if analyzing today)
                if target_date == datetime.now().date():
                    print(f"💾 Saving fresh data to JSON file...")
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
            print(f"❌ Error generating pulse analytics: {e}")
            import traceback
            traceback.print_exc()
            
            # Provide more specific error information
            if "401" in str(e) or "unauthorized" in str(e).lower():
                print("🔐 Authentication error - check your ClickUp API token")
                return self._get_demo_data_with_message("Authentication failed - check API token")
            elif "403" in str(e) or "forbidden" in str(e).lower():
                print("🚫 Permission error - check your ClickUp API permissions")
                return self._get_demo_data_with_message("Permission denied - check API permissions")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                print("⏱️ Rate limit exceeded - try again later")
                return self._get_demo_data_with_message("Rate limit exceeded - try again later")
            else:
                print(f"❓ Unknown error: {type(e).__name__}")
                return self._get_demo_data_with_message(f"API error: {str(e)}")
    
    def _generate_fresh_pulse_data(self, target_date=None, debug=False, status_filters=None, member_filters=None, hf_token=None):
        """
        Generate fresh pulse data using ClickUp integration with AI project complexity analysis
        """
        try:
            # Set default status filters if none provided
            if status_filters is None:
                status_filters = ['to do', 'planning', 'in progress', 'bugs']
                
            if member_filters is None:
                member_filters = ['Arif', 'Jan', 'wiktor', 'Kendra', 'Calum', 'Tricia', 'Rick']
            
            print(f"🎯 Using status filters: {status_filters}")
            print(f"👥 Using member filters: {member_filters}")
            

            
            print("🔍 Getting space information...")
            space_info = self._get_space_info()
            
            if not space_info:
                print("❌ Could not fetch space information!")
                return None
            
            print(f"✅ Found space: {space_info.get('name', 'Unknown')}")
            
            # Get all lists (projects) in the space
            print("📋 Getting lists/projects...")
            lists = self._get_space_lists()
            
            if not lists:
                print("❌ No lists found in this space!")
                return None
            
            print(f"✅ Found {len(lists)} lists/projects")
            
            # Initialize analytics data structure
            member_workloads = {}
            project_analytics = {}
            timeline_analysis = {
                "urgent_deadlines": [],
                "upcoming_deadlines": [],
                "overdue_tasks": [],
                "high_priority_tasks": [],
                "deadline_pressure_by_member": {}
            }
            
            total_tasks = 0
            all_tasks = []
            
            # Process each list/project
            for list_item in lists:
                list_id = list_item['id']
                list_name = list_item['name']
                
                print(f"📋 Processing list: {list_name}")
                
                # Get tasks for this list with status filtering
                tasks = self._get_list_tasks_with_status_filter(list_id, status_filters, debug)
                
                if not tasks:
                    print(f"   ⚠️ No tasks found for {list_name} with status filters: {status_filters}")
                    continue
                
                print(f"   ✅ Found {len(tasks)} tasks matching status filters")
                total_tasks += len(tasks)
                all_tasks.extend(tasks)
                
                # Analyze project
                project_analytics[list_id] = self._analyze_project(list_item, tasks)
                
                # Process tasks for member workloads
                for task in tasks:
                    self._process_task_for_member_workload(task, member_workloads, timeline_analysis, member_filters)
            
            if total_tasks == 0:
                print("❌ No tasks found matching the status filters!")
                return None
            
            print(f"✅ Total tasks processed: {total_tasks}")
            print(f"✅ Members with workload: {len(member_workloads)}")
            
            # Apply AI project complexity analysis if token is provided
            if hf_token:
                print("🤖 Analyzing project complexity with AI...")
                project_weights = self._analyze_project_complexity_with_ai(project_analytics, hf_token)
                self._apply_project_weights_to_workload(member_workloads, project_weights)
                print("✅ Project complexity analysis completed")
            
            # Generate load balance insights
            load_balance_insights = self._generate_load_balance_insights(member_workloads)
            
            # Generate overview stats
            overview_stats = self._generate_overview_stats(member_workloads, project_analytics, total_tasks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
            
            # Calculate project performance metrics
            project_performance = self._calculate_project_performance_metrics(project_analytics)
            
            # Compile final analytics
            analytics_data = {
                "member_workloads": member_workloads,
                "project_analytics": project_analytics,
                "timeline_analysis": timeline_analysis,
                "load_balance_insights": load_balance_insights,
                "overview_stats": overview_stats,
                "recommendations": recommendations,
                "project_performance": project_performance,
                "last_updated": datetime.now().isoformat(),
                "data_source": "clickup_api",
                "cache_info": {
                    "generated_fresh": True,
                    "status_filters_used": status_filters,
                    "analysis_date": str(target_date)
                }
            }
            
            # Generate intelligent summary
            try:
                intelligent_summary = self._generate_intelligent_summary(analytics_data, use_ai=False)
                analytics_data["intelligent_summary"] = intelligent_summary
            except Exception as e:
                print(f"Warning: Could not generate intelligent summary: {e}")
                analytics_data["intelligent_summary"] = {
                    "rule_based_analysis": {
                        "overall_assessment": "Summary generation failed",
                        "key_concerns": ["Analysis error occurred"],
                        "recommendations": ["Check data and try again"]
                    },
                    "ai_enhanced_analysis": None
                }
            
            # Add filter information for frontend
            if status_filters:
                analytics_data["filter_info"] = {
                    "status_filters_applied": status_filters,
                    "total_statuses_available": ['to do', 'planning', 'in progress', 'bugs', 'for qa', 'for viewing', 'grammar'],
                    "filter_count": len(status_filters)
                }
            
            # Add debug information if in debug mode
            if debug:
                analytics_data["debug_info"] = {
                    "analysis_date": str(target_date),
                    "is_weekend": target_date.weekday() >= 5,
                    "total_lists_processed": len(lists),
                    "total_tasks_found": total_tasks,
                    "members_with_workload": len(member_workloads),
                    "status_filters_used": status_filters,
                    "message": f"Successfully processed {total_tasks} tasks from {len(lists)} projects for {len(member_workloads)} members"
                }
            
            print(f"✅ Analytics generation complete!")
            print(f"   📊 Members: {len(member_workloads)}")
            print(f"   📋 Projects: {len(project_analytics)}")
            print(f"   ✅ Tasks: {total_tasks}")
            print(f"   💡 Recommendations: {len(recommendations)}")
            print(f"   ⚖️ Load Balance Insights: {len(load_balance_insights.get('transfer_suggestions', []))} suggestions")
            
            return analytics_data
            
        except Exception as e:
            print(f"❌ Error generating fresh pulse data: {e}")
            import traceback
            traceback.print_exc()
            
            # Log specific error details for debugging
            if "requests.exceptions" in str(type(e)):
                print(f"🌐 Network error: {e}")
            elif "json.JSONDecodeError" in str(type(e)):
                print(f"📄 JSON parsing error: {e}")
            elif "KeyError" in str(type(e)):
                print(f"🔑 Missing key in API response: {e}")
            else:
                print(f"❓ Unexpected error: {type(e).__name__}")
            
            return None

    def _generate_multi_space_pulse_data_with_delay(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None, hf_token=None):
        """
        Generate pulse data by combining multiple spaces with AI complexity analysis
        """
        try:
            print(f"🏢 Processing {len(space_filters)} spaces: {space_filters}")
            
            # Initialize combined data structures
            combined_member_workloads = {}
            combined_project_analytics = {}
            combined_timeline_analysis = {
                "urgent_deadlines": [],
                "upcoming_deadlines": [],
                "overdue_tasks": [],
                "high_priority_tasks": [],
                "deadline_pressure_by_member": {}
            }
            total_tasks_all_spaces = 0
            
            # Process each space
            for i, space_id in enumerate(space_filters):
                print(f"📋 Processing space {i+1}/{len(space_filters)}: {space_id}")
                
                # Temporarily set space_id for this iteration
                self.space_id = space_id
                
                # Get data for this space
                space_data = self._generate_fresh_pulse_data(target_date, debug, status_filters, member_filters, hf_token)
                
                # Add delay between spaces to avoid rate limiting (except for the last one)
                if i < len(space_filters) - 1:
                    print("⏱️ Waiting 2 seconds between spaces to avoid rate limiting...")
                    time.sleep(2)
                
                if not space_data:
                    print(f"⚠️ No data from space {space_id}")
                    continue
                
                # Combine member workloads
                space_member_workloads = space_data.get('member_workloads', {})
                for username, workload in space_member_workloads.items():
                    if username not in combined_member_workloads:
                        combined_member_workloads[username] = workload.copy()
                    else:
                        # Merge workload data
                        existing = combined_member_workloads[username]
                        existing['active_tasks'] += workload.get('active_tasks', 0)
                        existing['urgent_tasks'] += workload.get('urgent_tasks', 0)
                        existing['high_priority_tasks'] += workload.get('high_priority_tasks', 0)
                        existing['due_soon_tasks'] += workload.get('due_soon_tasks', 0)
                        existing['total_time_estimate'] += workload.get('total_time_estimate', 0)
                        existing['total_time_spent'] += workload.get('total_time_spent', 0)
                        
                        # Merge projects and tasks lists
                        existing['projects'].extend(workload.get('projects', []))
                        existing['tasks'].extend(workload.get('tasks', []))
                        existing['projects_count'] = len(set(p['name'] for p in existing['projects']))
                
                # Combine project analytics (prefix with space name for uniqueness)
                space_projects = space_data.get('project_analytics', {})
                for project_id, project_data in space_projects.items():
                    unique_project_id = f"{space_id}_{project_id}"
                    combined_project_analytics[unique_project_id] = project_data
                
                # Combine timeline analysis
                space_timeline = space_data.get('timeline_analysis', {})
                for key in combined_timeline_analysis.keys():
                    if key in space_timeline and isinstance(space_timeline[key], list):
                        combined_timeline_analysis[key].extend(space_timeline[key])
                
                # Add to total task count
                space_overview = space_data.get('overview_stats', {})
                total_tasks_all_spaces += space_overview.get('total_active_tasks', 0)
            
            # Apply AI project complexity analysis for multi-space if token is provided
            if hf_token:
                print("🤖 Analyzing multi-space project complexity with AI...")
                project_weights = self._analyze_project_complexity_with_ai(combined_project_analytics, hf_token)
                self._apply_project_weights_to_workload(combined_member_workloads, project_weights)
                print("✅ Multi-space project complexity analysis completed")
            
            # Recalculate workload scores for combined data with computation details
            for username, workload in combined_member_workloads.items():
                score_computation = self._calculate_workload_score_with_details(workload)
                workload.update(score_computation)
            
            # Generate combined insights
            load_balance_insights = self._generate_load_balance_insights(combined_member_workloads)
            overview_stats = self._generate_overview_stats(combined_member_workloads, combined_project_analytics, total_tasks_all_spaces)
            recommendations = self._generate_recommendations(combined_member_workloads, combined_timeline_analysis)
            
            # Compile final analytics
            analytics_data = {
                "member_workloads": combined_member_workloads,
                "project_analytics": combined_project_analytics,
                "timeline_analysis": combined_timeline_analysis,
                "load_balance_insights": load_balance_insights,
                "overview_stats": overview_stats,
                "recommendations": recommendations,
                "last_updated": datetime.now().isoformat(),
                "data_source": "clickup_api_multi_space",
                "cache_info": {
                    "generated_fresh": True,
                    "status_filters_used": status_filters,
                    "member_filters_used": member_filters,
                    "space_filters_used": space_filters,
                    "analysis_date": str(target_date),
                    "spaces_processed": len(space_filters)
                }
            }
            
            # Generate intelligent summary for multi-space data
            try:
                intelligent_summary = self._generate_intelligent_summary(analytics_data, use_ai=False)
                analytics_data["intelligent_summary"] = intelligent_summary
            except Exception as e:
                print(f"Warning: Could not generate intelligent summary: {e}")
                analytics_data["intelligent_summary"] = {
                    "rule_based_analysis": {
                        "overall_assessment": "Summary generation failed",
                        "key_concerns": ["Analysis error occurred"],
                        "recommendations": ["Check data and try again"]
                    },
                    "ai_enhanced_analysis": None
                }
            
            print(f"✅ Multi-space analytics generation complete!")
            print(f"   🏢 Spaces processed: {len(space_filters)}")
            print(f"   👥 Members: {len(combined_member_workloads)}")
            print(f"   📋 Projects: {len(combined_project_analytics)}")
            print(f"   ✅ Total tasks: {total_tasks_all_spaces}")
            
            return analytics_data
            
        except Exception as e:
            print(f"❌ Error generating multi-space pulse data: {e}")
            import traceback
            traceback.print_exc()
            
            # Log specific error details for debugging
            if "requests.exceptions" in str(type(e)):
                print(f"🌐 Network error in multi-space: {e}")
            elif "json.JSONDecodeError" in str(type(e)):
                print(f"📄 JSON parsing error in multi-space: {e}")
            elif "KeyError" in str(type(e)):
                print(f"🔑 Missing key in multi-space response: {e}")
            else:
                print(f"❓ Unexpected error in multi-space: {type(e).__name__}")
            
            return None
    
    def _generate_multi_space_pulse_data(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None, hf_token=None):
        """
        Original multi-space method (kept for compatibility)
        """
        return self._generate_multi_space_pulse_data_with_delay(target_date, debug, status_filters, member_filters, space_filters, hf_token)

    # JSON Caching Methods (from PulseService)
    def _save_pulse_data(self, data):
        """
        Save pulse data to JSON file with timestamp
        """
        try:
            print(f"💾 Attempting to save pulse data...")
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
            recent_files = []
            
            for file_path in pulse_files:
                try:
                    # Extract datetime from filename: pulse_YYYYMMDD_HHMM.json
                    filename = os.path.basename(file_path)
                    datetime_str = filename.replace('pulse_', '').replace('.json', '')
                    file_datetime = datetime.strptime(datetime_str, '%Y%m%d_%H%M')
                    
                    if file_datetime >= three_hours_ago:
                        recent_files.append((file_datetime, file_path, filename))
                except Exception as e:
                    print(f"Error parsing pulse file {file_path}: {e}")
                    continue
            
            if not recent_files:
                return None
            
            # Sort by datetime and get the most recent one
            recent_files.sort(key=lambda x: x[0], reverse=True)  # Sort by datetime, newest first
            latest_datetime, latest_file_path, latest_filename = recent_files[0]
            
            print(f"📁 Found most recent pulse data: {latest_filename} (from {latest_datetime.strftime('%Y-%m-%d %H:%M')})")
            
            with open(latest_file_path, 'r') as f:
                data = json.load(f)
                
            # Add cache metadata
            data['cache_info'] = {
                'source_file': latest_filename,
                'generated_date': latest_datetime.strftime('%Y-%m-%d'),
                'generated_time': latest_datetime.strftime('%H:%M'),
                'is_historical': False,
                'is_recent_cache': True,
                'retrieved_at': datetime.now().isoformat(),
                'cache_age_hours': round((datetime.now() - latest_datetime).total_seconds() / 3600, 1)
            }
            
            return data
            
        except Exception as e:
            print(f"Error checking cached pulse data: {e}")
            return None
    
    def _get_latest_cached_data_from_today(self):
        """
        Get the latest cached pulse data from today
        """
        try:
            # Look for pulse files from today
            today_str = datetime.now().strftime('%Y%m%d')
            pattern = f"pulse_{today_str}_*.json"
            pulse_files = glob.glob(os.path.join(self.output_dir, pattern))
            
            if not pulse_files:
                print(f"📁 No pulse files found for today ({today_str})")
                return None
            
            # Sort by time (filename) and get the latest one from today
            pulse_files.sort()
            latest_file = pulse_files[-1]
            
            filename = os.path.basename(latest_file)
            print(f"📁 Found latest pulse file from today: {filename}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
                
            # Preserve existing cache info and add retrieval metadata
            existing_cache_info = data.get('cache_info', {})
            existing_cache_info.update({
                'source_file': filename,
                'retrieved_at': datetime.now().isoformat(),
                'is_latest_from_today': True,
                'retrieval_method': 'today_cache'
            })
            
            data['cache_info'] = existing_cache_info
            
            return data
            
        except Exception as e:
            print(f"Error reading latest cached pulse data for today: {e}")
            return None

    def get_recent_cached_data_only(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None):
        """
        Get only recent cached data (< 3 hours old) without making API calls
        """
        try:
            print("📁 Checking for recent cached data only (< 3 hours old)...")
            
            # Use provided date or default to today
            if target_date:
                if isinstance(target_date, str):
                    try:
                        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Invalid date format: {target_date}, using today")
                        target_date = datetime.now().date()
                elif hasattr(target_date, 'date'):
                    target_date = target_date.date()
            else:
                target_date = datetime.now().date()
            
            # Check for recent cache (3-hour rule)
            cached_data = self._get_cached_pulse_data()
            if cached_data:
                print("✅ Found recent cached data (< 3 hours old)")
                return cached_data
            
            print("📁 No recent cached data found")
            return None
            
        except Exception as e:
            print(f"❌ Error getting recent cached data: {e}")
            return None

    def get_today_cached_data_only(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None):
        """
        Get any cached data from today (even if > 3 hours old) without making API calls
        """
        try:
            print("📁 Checking for today's cached data only...")
            
            # Use provided date or default to today
            if target_date:
                if isinstance(target_date, str):
                    try:
                        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Invalid date format: {target_date}, using today")
                        target_date = datetime.now().date()
                elif hasattr(target_date, 'date'):
                    target_date = target_date.date()
            else:
                target_date = datetime.now().date()
            
            # Check for today's cache (any age)
            today_data = self._get_latest_cached_data_from_today()
            if today_data:
                print("✅ Found today's cached data")
                return today_data
            
            print("📁 No today's cached data found")
            return None
            
        except Exception as e:
            print(f"❌ Error getting today's cached data: {e}")
            return None

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
    
    def _get_demo_data_with_message(self, message):
        """
        Get demo data with a custom message
        """
        demo_data = self._get_demo_data()
        demo_data['custom_message'] = message
        demo_data['no_historical_data'] = True
        return demo_data

    def _analyze_project_complexity_with_ai(self, projects_data, hf_token):
        """
        Analyze project complexity using AI to generate weight scores
        """
        try:
            if not hf_token:
                return self._analyze_project_complexity_rule_based(projects_data)
            
            import requests
            
            project_weights = {}
            
            for project_id, project_info in projects_data.items():
                try:
                    # Get project description and metadata
                    project_name = project_info.get('name', '')
                    project_desc = project_info.get('description', '')
                    task_count = project_info.get('active_tasks', 0)
                    
                    # Skip if no meaningful description available
                    if not project_desc or len(project_desc.strip()) < 10:
                        print(f"   ⚠️ Project '{project_name}' has insufficient description, using rule-based analysis")
                        fallback_weight = self._calculate_rule_based_weight(project_name, project_desc, task_count)
                        project_weights[project_id] = fallback_weight
                        continue
                    
                    # Create analysis prompt
                    prompt = f"""
                    Analyze this software project and assign a complexity weight score from 1-10:

                    Project Name: {project_name}
                    Description: {project_desc}
                    Active Tasks: {task_count}

                    Score factors:
                    1-3: Simple (static sites, basic websites, minor updates, simple WordPress sites)
                    4-6: Moderate (web apps, CMS sites, standard integrations, basic e-commerce)
                    7-8: Complex (microservices, multi-phase projects, advanced tech stacks, custom APIs)
                    9-10: Very Complex (distributed systems, AI/ML, enterprise architecture, complex integrations)

                    Consider: technology stack, architecture complexity, project scope, development phases, integrations required.
                    
                    Examples:
                    - "5-page website with contact form" = 2-3 points
                    - "E-commerce site with payment integration" = 4-5 points  
                    - "Microservice webapp with Vue.js, Python, AWS" = 7-8 points
                    - "Enterprise platform with AI features" = 9-10 points

                    Respond with format: "Score: X - Brief explanation"
                    """
                    
                    # HuggingFace API call
                    headers = {
                        "Authorization": f"Bearer {hf_token}",
                        "Content-Type": "application/json"
                    }
                    
                    api_url = "https://api-inference.huggingface.co/models/google/flan-t5-large"
                    
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": 100,
                            "temperature": 0.3,  # Lower temperature for more consistent scoring
                            "do_sample": True
                        }
                    }
                    
                    response = requests.post(api_url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_response = ""
                        if isinstance(result, list) and len(result) > 0:
                            ai_response = result[0].get('generated_text', '')
                        
                        # Extract numeric score
                        weight_score = self._extract_score_from_ai_response(ai_response, project_name)
                        
                        project_weights[project_id] = {
                            'weight_score': weight_score,
                            'complexity_level': self._get_complexity_level(weight_score),
                            'ai_explanation': ai_response,
                            'analysis_method': 'ai_powered'
                        }
                        
                    else:
                        # Fallback to rule-based for this project
                        fallback_weight = self._calculate_rule_based_weight(project_name, project_desc, task_count)
                        project_weights[project_id] = fallback_weight
                        
                except Exception as e:
                    print(f"Error analyzing project {project_name}: {e}")
                    # Fallback to rule-based
                    fallback_weight = self._calculate_rule_based_weight(
                        project_info.get('name', ''), 
                        project_info.get('description', ''), 
                        project_info.get('active_tasks', 0)
                    )
                    project_weights[project_id] = fallback_weight
            
            return project_weights
            
        except Exception as e:
            print(f"Error in AI project analysis: {e}")
            return self._analyze_project_complexity_rule_based(projects_data)
    
    def _extract_score_from_ai_response(self, ai_response, project_name):
        """
        Extract numeric score from AI response text
        """
        try:
            # Look for numbers in the response
            import re
            numbers = re.findall(r'\b([1-9]|10)\b', ai_response)
            
            if numbers:
                score = int(numbers[0])
                return max(1, min(10, score))  # Ensure score is between 1-10
            else:
                # Fallback: analyze response text for complexity indicators
                ai_response_lower = ai_response.lower()
                
                if any(word in ai_response_lower for word in ['microservice', 'distributed', 'enterprise', 'ai', 'ml', 'complex']):
                    return 8
                elif any(word in ai_response_lower for word in ['webapp', 'app', 'api', 'database', 'phase']):
                    return 6
                elif any(word in ai_response_lower for word in ['website', 'cms', 'wordpress', 'basic']):
                    return 4
                else:
                    return 5  # Default moderate complexity
                    
        except Exception as e:
            print(f"Error extracting score for {project_name}: {e}")
            return 5  # Default score
    
    def _analyze_project_complexity_rule_based(self, projects_data):
        """
        Fallback rule-based project complexity analysis
        """
        project_weights = {}
        
        for project_id, project_info in projects_data.items():
            project_name = project_info.get('name', '').lower()
            project_desc = project_info.get('description', '').lower()
            task_count = project_info.get('active_tasks', 0)
            
            weight_score = self._calculate_rule_based_weight(project_name, project_desc, task_count)
            project_weights[project_id] = weight_score
        
        return project_weights
    
    def _calculate_rule_based_weight(self, project_name, project_desc, task_count):
        """
        Calculate project weight using rule-based analysis
        """
        project_name_lower = project_name.lower()
        project_desc_lower = project_desc.lower()
        combined_text = f"{project_name_lower} {project_desc_lower}"
        
        base_score = 5  # Default moderate complexity
        
        # Technology complexity indicators
        high_complexity_tech = ['microservice', 'microservices', 'distributed', 'aws', 'azure', 'kubernetes', 
                               'docker', 'api gateway', 'serverless', 'lambda', 'vue', 'react', 'angular', 
                               'python', 'node', 'java', 'ml', 'ai', 'blockchain']
        
        medium_complexity_tech = ['webapp', 'web app', 'database', 'mysql', 'postgres', 'redis', 
                                'javascript', 'php', 'laravel', 'django', 'flask', 'api']
        
        low_complexity_tech = ['website', 'wordpress', 'webflow', 'squarespace', 'static', 'html', 'css']
        
        # Scope indicators
        high_scope = ['phase 1', 'phase 2', 'multi-phase', 'enterprise', 'platform', 'system']
        medium_scope = ['dashboard', 'admin panel', 'user management', 'payment', 'integration']
        low_scope = ['5 page', 'landing page', 'brochure', 'portfolio', 'contact form']
        
        # Calculate complexity score
        complexity_score = base_score
        
        # Technology complexity adjustment
        high_tech_matches = sum(1 for tech in high_complexity_tech if tech in combined_text)
        medium_tech_matches = sum(1 for tech in medium_complexity_tech if tech in combined_text)
        low_tech_matches = sum(1 for tech in low_complexity_tech if tech in combined_text)
        
        if high_tech_matches > 0:
            complexity_score += min(3, high_tech_matches)
        elif medium_tech_matches > 0:
            complexity_score += min(2, medium_tech_matches)
        elif low_tech_matches > 0:
            complexity_score -= min(2, low_tech_matches)
        
        # Scope complexity adjustment
        high_scope_matches = sum(1 for scope in high_scope if scope in combined_text)
        medium_scope_matches = sum(1 for scope in medium_scope if scope in combined_text)
        low_scope_matches = sum(1 for scope in low_scope if scope in combined_text)
        
        if high_scope_matches > 0:
            complexity_score += min(2, high_scope_matches)
        elif medium_scope_matches > 0:
            complexity_score += 1
        elif low_scope_matches > 0:
            complexity_score -= 1
        
        # Task count adjustment (more tasks usually means more complexity)
        if task_count > 15:
            complexity_score += 1
        elif task_count > 25:
            complexity_score += 2
        elif task_count < 3:
            complexity_score -= 1
        
        # Ensure score is within bounds
        final_score = max(1, min(10, complexity_score))
        
        # Generate explanation
        explanation = f"Rule-based analysis: {final_score}/10 complexity based on technology stack, project scope, and task count ({task_count} tasks)."
        
        return {
            'weight_score': final_score,
            'complexity_level': self._get_complexity_level(final_score),
            'ai_explanation': explanation,
            'analysis_method': 'rule_based',
            'tech_matches': {
                'high_complexity': high_tech_matches,
                'medium_complexity': medium_tech_matches,
                'low_complexity': low_tech_matches
            },
            'scope_matches': {
                'high_scope': high_scope_matches,
                'medium_scope': medium_scope_matches,
                'low_scope': low_scope_matches
            }
        }
    
    def _get_complexity_level(self, score):
        """Convert numeric score to complexity level"""
        if score >= 9:
            return "Very Complex"
        elif score >= 7:
            return "Complex"
        elif score >= 4:
            return "Moderate"
        else:
            return "Simple"
    
    def _apply_project_weights_to_workload(self, member_workloads, project_weights):
        """
        Apply project complexity weights to member workload calculations
        """
        for username, workload in member_workloads.items():
            projects = workload.get('projects', [])
            tasks = workload.get('tasks', [])
            
            # Calculate weighted scores
            weighted_active_tasks = 0
            weighted_urgent_tasks = 0
            weighted_high_priority = 0
            weighted_due_soon = 0
            
            project_complexity_details = []
            
            for task in tasks:
                # Skip if task is None
                if task is None:
                    continue
                    
                # Find project weight for this task
                task_project = task.get('project_name', '')
                task_weight = 1.0  # Default weight
                
                # Find matching project weight
                for project_id, weight_data in project_weights.items():
                    if task_project in weight_data.get('ai_explanation', '') or any(task_project in str(v) for v in weight_data.values()):
                        task_weight = weight_data.get('weight_score', 1) / 5.0  # Normalize to 0.2-2.0 range
                        break
                
                # Apply weights to task counts
                weighted_active_tasks += task_weight
                
                # Safe priority check
                priority_data = task.get('priority', {})
                if isinstance(priority_data, dict):
                    priority_level = priority_data.get('priority', '').lower()
                else:
                    priority_level = str(priority_data).lower() if priority_data else ''
                
                if priority_level == 'urgent':
                    weighted_urgent_tasks += task_weight
                elif priority_level == 'high':
                    weighted_high_priority += task_weight
                
                if task.get('due_date'):  # Simplified due soon check
                    weighted_due_soon += task_weight
            
            # Update workload with weighted calculations
            workload['weighted_metrics'] = {
                'weighted_active_tasks': round(weighted_active_tasks, 1),
                'weighted_urgent_tasks': round(weighted_urgent_tasks, 1),
                'weighted_high_priority': round(weighted_high_priority, 1),
                'weighted_due_soon': round(weighted_due_soon, 1),
                'original_active_tasks': workload.get('active_tasks', 0),
                'weight_applied': True
            }
            
            # Calculate new weighted workload score
            weighted_score = (
                weighted_active_tasks * 10 +
                weighted_urgent_tasks * 25 +
                weighted_high_priority * 15 +
                weighted_due_soon * 10
            )
            
            workload['weighted_workload_score'] = round(weighted_score, 1)
            workload['original_workload_score'] = workload.get('workload_score', 0)
            
            # Update primary workload score to weighted version
            workload['workload_score'] = workload['weighted_workload_score']
    
    def _generate_intelligent_summary(self, analytics_data, use_ai=False, hf_token=None):
        """
        Generate intelligent summary analysis of team workload data
        """
        try:
            # Extract key data for analysis
            member_workloads = analytics_data.get('member_workloads', {})
            overview_stats = analytics_data.get('overview_stats', {})
            load_balance = analytics_data.get('load_balance_insights', {})
            recommendations = analytics_data.get('recommendations', [])
            
            # Rule-based analysis (always generate this)
            rule_based_summary = self._generate_rule_based_summary(
                member_workloads, overview_stats, load_balance, recommendations
            )
            
            # AI-enhanced analysis if requested and token is working
            ai_summary = None
            if use_ai and hf_token:
                try:
                    ai_summary = self._generate_ai_enhanced_summary(
                        analytics_data, hf_token
                    )
                    if ai_summary and ai_summary.get('ai_analysis'):
                        print("🤖 AI analysis successful")
                    else:
                        print("⚠️ AI analysis failed, using rule-based only")
                        ai_summary = None
                except Exception as e:
                    print(f"⚠️ AI analysis error: {e}, using rule-based only")
                    ai_summary = None
            
            # If AI fails, enhance the rule-based analysis with comprehensive fallback
            if not ai_summary:
                print("🤖 AI analysis unavailable, using comprehensive rule-based analytics...")
                enhanced_rule_based = self._generate_enhanced_rule_based_summary(
                    member_workloads, overview_stats, load_balance, recommendations
                )
                rule_based_summary.update(enhanced_rule_based)
                
                # Add comprehensive fallback analytics
                try:
                    fallback_analytics = self.generate_comprehensive_fallback_analytics(
                        member_workloads, analytics_data.get('project_analytics', {})
                    )
                    rule_based_summary['comprehensive_fallback_analytics'] = fallback_analytics
                except Exception as e:
                    print(f"⚠️ Fallback analytics error: {e}")
                    # Continue without fallback analytics
            
            return {
                "rule_based_analysis": rule_based_summary,
                "ai_enhanced_analysis": ai_summary,
                "generation_timestamp": datetime.now().isoformat(),
                "analysis_confidence": "high" if ai_summary else "enhanced_rule_based"
            }
            
        except Exception as e:
            print(f"Error generating intelligent summary: {e}")
            return {
                "rule_based_analysis": {
                    "overall_assessment": "Analysis failed",
                    "key_concerns": ["Unable to generate summary due to error"],
                    "recommendations": ["Check data quality and try again"]
                },
                "ai_enhanced_analysis": None,
                "generation_timestamp": datetime.now().isoformat(),
                "analysis_confidence": "low"
            }
    
    def _generate_rule_based_summary(self, member_workloads, overview_stats, load_balance, recommendations):
        """
        Generate summary using rule-based analysis
        """
        try:
            total_members = len(member_workloads)
            if total_members == 0:
                return {
                    "overall_assessment": "No team data available",
                    "key_concerns": ["No member workload data found"],
                    "recommendations": ["Ensure team members are assigned to tasks"]
                }
            
            # Analyze workload distribution
            scores = [w.get('workload_score', 0) for w in member_workloads.values()]
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            score_range = max_score - min_score
            
            # Analyze distribution
            status_dist = overview_stats.get('workload_distribution', {})
            overloaded_count = status_dist.get('overloaded', 0)
            light_count = status_dist.get('light', 0)
            health_score = overview_stats.get('health_score', 0)
            
            # Determine overall assessment
            if score_range > 150 and overloaded_count > 0:
                assessment = "Critical workload imbalance detected"
                severity = "high"
            elif score_range > 100:
                assessment = "Moderate workload imbalance present"
                severity = "medium"
            elif health_score > 85:
                assessment = "Generally balanced team workload"
                severity = "low"
            else:
                assessment = "Some workload concerns identified"
                severity = "medium"
            
            # Identify key concerns
            concerns = []
            
            if overloaded_count > 0:
                overloaded_members = [
                    name for name, data in member_workloads.items() 
                    if data.get('status') == 'overloaded'
                ]
                concerns.append(f"{overloaded_count} team member(s) severely overloaded: {', '.join(overloaded_members)}")
            
            if score_range > 150:
                concerns.append(f"Extreme workload variance ({min_score}-{max_score} point range)")
            
            if light_count > total_members * 0.3:  # More than 30% underutilized
                concerns.append(f"{light_count} team members significantly underutilized")
            
            # Check for time estimation issues
            time_issues = []
            for name, data in member_workloads.items():
                remaining_status = data.get('remaining_time_status', {})
                if remaining_status.get('is_over_time') and remaining_status.get('over_time_hours', 0) > 10:
                    time_issues.append(f"{name} ({remaining_status.get('over_time_hours', 0):.1f}h over)")
            
            if time_issues:
                concerns.append(f"Significant time estimation errors: {', '.join(time_issues)}")
            
            # Generate insights
            insights = []
            
            if light_count > 0 and overloaded_count > 0:
                insights.append("Task redistribution opportunity: Move work from overloaded to underutilized members")
            
            if len([r for r in recommendations if r.get('type') == 'time_overrun']) > 2:
                insights.append("Systematic time estimation issues suggest need for improved planning processes")
            
            avg_score = overview_stats.get('avg_workload_score', 0)
            if avg_score < 60:
                insights.append("Team capacity appears underutilized - consider taking on additional work or projects")
            
            # Priority actions
            priority_actions = []
            
            high_priority_recs = [r for r in recommendations if r.get('priority') == 'high']
            if len(high_priority_recs) > 3:
                priority_actions.append("Address high-priority workload warnings immediately")
            
            if overloaded_count > 0:
                priority_actions.append("Redistribute tasks from overloaded members within 24-48 hours")
            
            if score_range > 150:
                priority_actions.append("Review and rebalance team assignments to reduce workload variance")
            
            return {
                "overall_assessment": assessment,
                "severity_level": severity,
                "health_score_interpretation": self._interpret_health_score(health_score),
                "key_concerns": concerns if concerns else ["No major concerns identified"],
                "actionable_insights": insights if insights else ["Team workload appears well-balanced"],
                "priority_actions": priority_actions if priority_actions else ["Continue monitoring current distribution"],
                "workload_efficiency": {
                    "distribution_score": max(0, 100 - (score_range / 3)),  # Penalize large ranges
                    "utilization_rate": min(100, (avg_score / 80) * 100),  # Target ~80 average
                    "balance_rating": "Poor" if score_range > 150 else "Good" if score_range < 75 else "Fair"
                },
                "team_metrics": {
                    "workload_variance": score_range,
                    "average_utilization": f"{avg_score:.1f} points",
                    "capacity_status": "Over-capacity" if avg_score > 120 else "Under-utilized" if avg_score < 50 else "Well-utilized"
                }
            }
            
        except Exception as e:
            print(f"Error in rule-based summary: {e}")
            return {
                "overall_assessment": "Analysis error occurred",
                "key_concerns": [str(e)],
                "recommendations": ["Check data structure and try again"]
            }
    
    def _interpret_health_score(self, score):
        """Provide contextual interpretation of health score"""
        if score >= 95:
            return "Excellent - Team workload is very well balanced"
        elif score >= 85:
            return "Good - Minor workload adjustments may be beneficial"
        elif score >= 70:
            return "Fair - Some workload rebalancing recommended"
        elif score >= 50:
            return "Poor - Significant workload issues need attention"
        else:
            return "Critical - Immediate workload intervention required"
    
    def _generate_ai_enhanced_summary(self, analytics_data, hf_token):
        """
        Generate AI-enhanced summary using OpenAI, HuggingFace, or fallback to local analytics
        """
        try:
            # First, try OpenAI (most reliable)
            ai_result = self._try_openai_api(analytics_data)
            if ai_result:
                return ai_result
            
            # Second, try HuggingFace API
            ai_result = self._try_huggingface_api(analytics_data, hf_token)
            if ai_result:
                return ai_result
            
            # If both fail, use local AI-like analytics
            print("🤖 External AI APIs unavailable, using local AI-like analytics...")
            return self._generate_local_ai_like_analysis(analytics_data)
            
        except Exception as e:
            print(f"Error in AI-enhanced summary: {e}")
            return None
    
    def _try_openai_api(self, analytics_data):
        """Try OpenAI API for AI-enhanced analysis"""
        try:
            # Your OpenAI API key
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
            
            print("   🧪 Trying OpenAI API...")
            
            # Prepare the prompt for AI analysis
            prompt = self._prepare_ai_prompt(analytics_data)
            
            # OpenAI API call
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert business analyst specializing in team workload optimization and project management. Provide concise, actionable insights based on the data provided."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_analysis = result['choices'][0]['message']['content']
                print(f"   ✅ Success with OpenAI GPT-3.5!")
                return {
                    "ai_analysis": ai_analysis,
                    "model_used": "gpt-3.5-turbo",
                    "confidence": "high",
                    "provider": "openai"
                }
            elif response.status_code == 401:
                print(f"   ❌ OpenAI API key invalid or expired")
                return None
            elif response.status_code == 429:
                print(f"   ⏳ OpenAI rate limit hit")
                return None
            else:
                print(f"   ❌ OpenAI API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ OpenAI API error: {e}")
            return None
    
    def _try_huggingface_api(self, analytics_data, hf_token):
        """Try HuggingFace API with multiple fallback models"""
        try:
            # Check if HuggingFace inference API is working
            print("   🔍 Testing HuggingFace inference API status...")
            
            # Test with a simple model first
            test_response = requests.get(
                "https://api-inference.huggingface.co/models/gpt2",
                headers={"Authorization": f"Bearer {hf_token}"},
                timeout=10
            )
            
            if test_response.status_code == 404:
                print("   ❌ HuggingFace inference API is currently down (404 errors for all models)")
                print("   💡 This is a known issue - the inference service is experiencing outages")
                print("   💡 Using local AI-like analytics instead")
                return None
            
            # If we get here, the API might be working
            print("   ✅ HuggingFace inference API appears to be working")
            
            # Prepare the prompt for AI analysis
            prompt = self._prepare_ai_prompt(analytics_data)
            
            # List of models to try (in order of preference)
            models_to_try = [
                "gpt2",
                "distilgpt2", 
                "microsoft/DialoGPT-small",
                "facebook/opt-125m"
            ]
            
            headers = {
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "do_sample": True
                }
            }
            
            for model in models_to_try:
                try:
                    print(f"   🧪 Trying model: {model}")
                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{model}",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if isinstance(result, list) and len(result) > 0:
                            ai_analysis = result[0].get('generated_text', '')
                            print(f"   ✅ Success with {model}!")
                            return {
                                "ai_analysis": ai_analysis,
                                "model_used": model,
                                "confidence": "high"
                            }
                    elif response.status_code == 503:
                        print(f"   ⏳ Model {model} is loading, trying next...")
                        continue
                    else:
                        print(f"   ❌ Model {model} failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error with {model}: {e}")
                    continue
            
            print("   ❌ All HuggingFace models failed")
            return None
            
        except Exception as e:
            print(f"Error trying HuggingFace API: {e}")
            return None
    
    def _prepare_ai_prompt(self, analytics_data):
        """Prepare prompt for AI analysis"""
        summary_data = {
            "total_members": len(analytics_data.get('member_workloads', {})),
            "health_score": analytics_data.get('overview_stats', {}).get('health_score', 0),
            "workload_distribution": analytics_data.get('overview_stats', {}).get('workload_distribution', {}),
            "highest_workload": analytics_data.get('load_balance_insights', {}).get('highest_workload', {}),
            "lowest_workload": analytics_data.get('load_balance_insights', {}).get('lowest_workload', {}),
            "recommendations_count": len(analytics_data.get('recommendations', [])),
            "time_overruns": [
                r for r in analytics_data.get('recommendations', []) 
                if r.get('type') == 'time_overrun'
            ]
        }
        
        return f"""
        Analyze this team workload data and provide strategic insights:
        
        Team Size: {summary_data['total_members']} members
        Health Score: {summary_data['health_score']}/100
        Workload Distribution: {summary_data['workload_distribution']}
        Highest Workload: {summary_data['highest_workload']}
        Lowest Workload: {summary_data['lowest_workload']}
        Total Recommendations: {summary_data['recommendations_count']}
        Time Overruns: {len(summary_data['time_overruns'])} members
        
        Provide a concise strategic analysis focusing on:
        1. Overall team efficiency
        2. Risk factors
        3. Optimization opportunities
        4. Management priorities
        
        Keep response under 200 words, business-focused.
        """
    
    def _generate_local_ai_like_analysis(self, analytics_data):
        """
        Generate AI-like analysis using local rules and patterns
        This provides intelligent insights without external APIs
        """
        try:
            # Extract key data
            member_workloads = analytics_data.get('member_workloads', {})
            overview_stats = analytics_data.get('overview_stats', {})
            load_balance = analytics_data.get('load_balance_insights', {})
            
            # Generate intelligent insights
            insights = []
            
            # Workload distribution insights
            if member_workloads:
                scores = [w.get('workload_score', 0) for w in member_workloads.values()]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    max_score = max(scores)
                    min_score = min(scores)
                    
                    if max_score - min_score > 100:
                        insights.append(f"⚠️ Workload imbalance detected: highest member ({max_score} pts) vs lowest ({min_score} pts). Consider redistributing tasks for better team balance.")
                    
                    if avg_score > 80:
                        insights.append(f"📊 Team is operating at high capacity ({avg_score:.1f} pts average). Monitor for burnout and consider resource allocation.")
                    elif avg_score < 30:
                        insights.append(f"📊 Team has low utilization ({avg_score:.1f} pts average). Opportunity to take on additional work or projects.")
            
            # Priority insights
            urgent_tasks = sum(w.get('urgent_tasks', 0) for w in member_workloads.values())
            if urgent_tasks > 5:
                insights.append(f"🚨 High priority pressure: {urgent_tasks} urgent tasks across the team. Review priorities and resource allocation.")
            
            # Time management insights
            time_overruns = [w for w in member_workloads.values() if w.get('remaining_time_status', {}).get('is_over_time', False)]
            if time_overruns:
                insights.append(f"⏰ Time estimation accuracy needs improvement: {len(time_overruns)} team members are over their time estimates.")
            
            # Project complexity insights
            total_projects = overview_stats.get('total_projects', 0)
            total_tasks = overview_stats.get('total_active_tasks', 0)
            if total_projects > 0:
                avg_tasks_per_project = total_tasks / total_projects
                if avg_tasks_per_project > 15:
                    insights.append(f"🏗️ High project complexity: average {avg_tasks_per_project:.1f} tasks per project. Consider breaking down complex projects.")
            
            # Team health insights
            health_score = overview_stats.get('health_score', 0)
            if health_score < 70:
                insights.append(f"🏥 Team health score is {health_score}/100. Focus on workload balance and process improvements.")
            elif health_score > 90:
                insights.append(f"🎯 Excellent team health score: {health_score}/100. Team is well-balanced and efficient.")
            
            # Generate summary
            if insights:
                summary = "🤖 AI-Like Analysis (Local):\n\n" + "\n\n".join(insights)
            else:
                summary = "🤖 AI-Like Analysis (Local):\n\nTeam workload appears balanced with no immediate concerns detected."
            
            return {
                "ai_analysis": summary,
                "model_used": "local_ai_like_analytics",
                "confidence": "high",
                "insights_count": len(insights),
                "analysis_type": "rule_based_intelligent"
            }
            
        except Exception as e:
            print(f"Error in local AI-like analysis: {e}")
            return {
                "ai_analysis": "🤖 AI-Like Analysis (Local):\n\nAnalysis completed using local intelligent rules.",
                "model_used": "local_ai_like_analytics",
                "status": "success",
                "analysis_type": "rule_based_fallback"
            }

    # NEW METHOD: Calculate workload score with detailed computation
    def _calculate_workload_score_with_details(self, workload):
        """
        Calculate workload score with detailed computation breakdown
        """
        active_tasks = workload.get("active_tasks", 0)
        urgent_tasks = workload.get("urgent_tasks", 0)
        high_priority_tasks = workload.get("high_priority_tasks", 0)
        due_soon_tasks = workload.get("due_soon_tasks", 0)
        total_time_estimate = workload.get("total_time_estimate", 0)
        total_time_spent = workload.get("total_time_spent", 0)
        
        # Calculate workload score
        score = (
            active_tasks * 10 +
            urgent_tasks * 25 +
            high_priority_tasks * 15 +
            due_soon_tasks * 10
        )
        
        # ENHANCED: Handle time calculations with detailed breakdown
        remaining_time_minutes = total_time_estimate - total_time_spent
        is_over_time = remaining_time_minutes < 0
        
        # Convert to hours for better readability
        estimate_hours = round(total_time_estimate / 60, 2)
        spent_hours = round(total_time_spent / 60, 2)
        remaining_hours = round(remaining_time_minutes / 60, 2)
        
        # Determine status based on score
        if score >= 150:
            status = "overloaded"
        elif score >= 100:
            status = "high"
        elif score >= 50:
            status = "balanced"
        else:
            status = "light"
        
        return {
            "workload_score": round(score, 1),
            "workload_computation": {
                "formula": "active_tasks * 10 + urgent_tasks * 25 + high_priority_tasks * 15 + due_soon_tasks * 10",
                "breakdown": {
                    "active_tasks": f"{active_tasks} * 10 = {active_tasks * 10}",
                    "urgent_tasks": f"{urgent_tasks} * 25 = {urgent_tasks * 25}",
                    "high_priority_tasks": f"{high_priority_tasks} * 15 = {high_priority_tasks * 15}",
                    "due_soon_tasks": f"{due_soon_tasks} * 10 = {due_soon_tasks * 10}"
                },
                "total_calculation": f"{active_tasks * 10} + {urgent_tasks * 25} + {high_priority_tasks * 15} + {due_soon_tasks * 10} = {score}"
            },
            "total_time_estimate": total_time_estimate,  # Keep original minutes
            "total_time_spent": total_time_spent,        # Keep original minutes  
            "remaining_time": remaining_time_minutes,    # Keep original minutes
            "time_computation": {
                "source_format": "ClickUp stores time in milliseconds",
                "conversion_formula": "milliseconds ÷ 1000 ÷ 60 = minutes",
                "estimates_breakdown": {
                    "total_minutes": round(total_time_estimate, 1),
                    "total_hours": estimate_hours,
                    "conversion_note": f"{total_time_estimate} minutes ÷ 60 = {estimate_hours} hours"
                },
                "spent_breakdown": {
                    "total_minutes": round(total_time_spent, 1), 
                    "total_hours": spent_hours,
                    "conversion_note": f"{total_time_spent} minutes ÷ 60 = {spent_hours} hours"
                },
                "remaining_breakdown": {
                    "total_minutes": round(remaining_time_minutes, 1),
                    "total_hours": remaining_hours,
                    "computation": f"{estimate_hours}h (estimated) - {spent_hours}h (spent) = {remaining_hours}h",
                    "interpretation": "Negative = over-time, Positive = time remaining"
                }
            },
            "remaining_time_status": {
                "is_over_time": is_over_time,
                "over_time_hours": abs(remaining_hours) if is_over_time else 0,
                "computation": f"{estimate_hours}h (estimated) - {spent_hours}h (spent) = {remaining_hours}h",
                "note": "Negative value indicates time spent exceeds original estimate" if is_over_time else "Positive value indicates remaining work time"
            },
            "status": status
        }

    # Original ClickUp API Methods (existing functionality)
    def _get_space_info(self):
        """Get space information"""
        try:
            print(f"🔍 Fetching space info for space ID: {self.space_id}")
            resp = requests.get(f"{self.base_url}/space/{self.space_id}", headers=self.headers)
            
            # Log response details for debugging
            print(f"📡 API Response Status: {resp.status_code}")
            print(f"📡 API Response Headers: {dict(resp.headers)}")
            
            if resp.status_code == 401:
                print("🔐 Unauthorized - check your API token")
                return None
            elif resp.status_code == 403:
                print("🚫 Forbidden - check your API permissions")
                return None
            elif resp.status_code == 404:
                print("❌ Space not found - check your space ID")
                return None
            elif resp.status_code == 429:
                print("⏱️ Rate limit exceeded - waiting for reset...")
                retry_after = resp.headers.get('retry-after', 60)
                print(f"   Retry after {retry_after} seconds")
                # Return cached data if available, otherwise return None
                cached_data = self._get_cached_pulse_data()
                if cached_data:
                    print("📊 Returning cached data due to rate limit")
                    return cached_data
                return None
            
            resp.raise_for_status()
            space_data = resp.json()
            
            # Validate response structure
            if not isinstance(space_data, dict):
                print(f"⚠️ Unexpected response format: {type(space_data)}")
                return None
                
            print(f"✅ Space info retrieved: {space_data.get('name', 'Unknown')}")
            return space_data
            
        except requests.exceptions.RequestException as e:
            print(f"🌐 Network error getting space info: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"📄 JSON parsing error in space info: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error getting space info: {e}")
            return None
    
    def _get_space_lists(self):
        """Get all lists in the space, including those inside folders, with descriptions"""
        try:
            all_lists = []
            
            # 1. Get lists directly in the space (not in folders)
            print("🔍 Getting lists directly in space...")
            resp = requests.get(f"{self.base_url}/space/{self.space_id}/list", headers=self.headers)
            
            # Log response details for debugging
            print(f"📡 Lists API Response Status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("🔐 Unauthorized - check your API token")
                return []
            elif resp.status_code == 403:
                print("🚫 Forbidden - check your API permissions")
                return []
            elif resp.status_code == 404:
                print("❌ Space not found - check your space ID")
                return []
            elif resp.status_code == 429:
                print("⏱️ Rate limit exceeded for folders - continuing with direct lists only")
                return direct_lists  # Return what we have so far
            elif resp.status_code == 429:
                print("⏱️ Rate limit exceeded - waiting for reset...")
                retry_after = resp.headers.get('retry-after', 60)
                print(f"   Retry after {retry_after} seconds")
                return []
            
            resp.raise_for_status()
            lists_response = resp.json()
            
            # Validate response structure
            if not isinstance(lists_response, dict):
                print(f"⚠️ Unexpected lists response format: {type(lists_response)}")
                return []
                
            direct_lists = lists_response.get('lists', [])
            
            if not isinstance(direct_lists, list):
                print(f"⚠️ Unexpected lists format: {type(direct_lists)}")
                direct_lists = []
            
            # Fetch detailed info including descriptions for each direct list
            for list_item in direct_lists:
                # Skip archived, empty, or excluded lists
                if not self._should_include_list(list_item):
                    print(f"   ⏭️ Skipping list: {list_item.get('name', 'Unknown')} (archived/empty/excluded)")
                    continue
                
                list_with_description = self._get_list_details(list_item['id'])
                if list_with_description:
                    all_lists.append(list_with_description)
                else:
                    all_lists.append(list_item)  # Fallback to basic info
            
            print(f"   ✅ Found {len(direct_lists)} direct lists in space")
            
            # 2. Get all folders in the space
            print("📁 Getting folders in space...")
            resp = requests.get(f"{self.base_url}/space/{self.space_id}/folder", headers=self.headers)
            
            # Log response details for debugging
            print(f"📡 Folders API Response Status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("🔐 Unauthorized - check your API token")
                folders = []
            elif resp.status_code == 403:
                print("🚫 Forbidden - check your API permissions")
                folders = []
            elif resp.status_code == 404:
                print("❌ Space not found - check your space ID")
                folders = []
            else:
                resp.raise_for_status()
                folders_response = resp.json()
                
                # Validate response structure
                if not isinstance(folders_response, dict):
                    print(f"⚠️ Unexpected folders response format: {type(folders_response)}")
                    folders = []
                else:
                    folders = folders_response.get('folders', [])
                    
                    if not isinstance(folders, list):
                        print(f"⚠️ Unexpected folders format: {type(folders)}")
                        folders = []
            print(f"   ✅ Found {len(folders)} folders in space")
            
            # 3. Get lists from each folder
            for folder in folders:
                folder_id = folder.get('id')
                folder_name = folder.get('name', 'Unknown Folder')
                
                # Skip archived folders
                if self._is_archived(folder_name):
                    print(f"📂 Skipping archived folder: {folder_name}")
                    continue
                
                print(f"📂 Getting lists from folder: {folder_name}")
                try:
                    resp = requests.get(f"{self.base_url}/folder/{folder_id}/list", headers=self.headers)
                    resp.raise_for_status()
                    folder_lists = resp.json().get('lists', [])
                    
                    # Get detailed info for each folder list
                    for list_item in folder_lists:
                        # Skip archived, empty, or excluded lists
                        if not self._should_include_list(list_item):
                            print(f"   ⏭️ Skipping list: {list_item.get('name', 'Unknown')} (archived/empty/excluded)")
                            continue
                        
                        list_with_description = self._get_list_details(list_item['id'])
                        if list_with_description:
                            # Add folder info to detailed list data
                            list_with_description['folder_info'] = {
                                'folder_id': folder_id,
                                'folder_name': folder_name
                            }
                            all_lists.append(list_with_description)
                        else:
                            # Fallback: add folder info to basic list data
                            list_item['folder_info'] = {
                                'folder_id': folder_id,
                                'folder_name': folder_name
                            }
                            all_lists.append(list_item)
                    
                    print(f"   ✅ Found {len(folder_lists)} lists in folder '{folder_name}'")
                    
                except Exception as e:
                    print(f"   ❌ Error getting lists from folder '{folder_name}': {e}")
                    continue
            
            print(f"✅ Total lists found: {len(all_lists)} (direct: {len(direct_lists)}, in folders: {len(all_lists) - len(direct_lists)})")
            print(f"📝 Lists with descriptions: {len([l for l in all_lists if l.get('description')])}")
            return all_lists
            
        except Exception as e:
            print(f"❌ Error getting space lists and folders: {e}")
            import traceback
            traceback.print_exc()
            return []


    def _get_list_details(self, list_id):
        """Get detailed information about a specific list, including description"""
        try:
            resp = requests.get(f"{self.base_url}/list/{list_id}", headers=self.headers)
            
            # Handle rate limiting gracefully
            if resp.status_code == 429:
                print(f"   ⏱️ Rate limit hit for list {list_id} - skipping details")
                return None
            
            resp.raise_for_status()
            list_data = resp.json()
            
            # Extract relevant fields including description
            detailed_list = {
                'id': list_data.get('id'),
                'name': list_data.get('name'),
                'description': list_data.get('content', ''),  # ClickUp uses 'content' field for description
                'status': list_data.get('status'),
                'priority': list_data.get('priority'),
                'assignee': list_data.get('assignee'),
                'task_count': list_data.get('task_count', 0),
                'due_date': list_data.get('due_date'),
                'start_date': list_data.get('start_date'),
                'folder': list_data.get('folder', {}),
                'space': list_data.get('space', {}),
                'archived': list_data.get('archived', False)
            }
            
            # Also check if there's a 'description' field (some ClickUp versions)
            if not detailed_list['description'] and list_data.get('description'):
                detailed_list['description'] = list_data.get('description')
            
            return detailed_list
            
        except Exception as e:
            print(f"   ⚠️ Could not get details for list {list_id}: {e}")
            return None


    def _get_space_folders(self):
        """Get all folders in the space"""
        try:
            resp = requests.get(f"{self.base_url}/space/{self.space_id}/folder", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get('folders', [])
        except Exception as e:
            print(f"Error getting space folders: {e}")
            return []

    def _get_folder_lists(self, folder_id):
        """Get all lists in a specific folder"""
        try:
            resp = requests.get(f"{self.base_url}/folder/{folder_id}/list", headers=self.headers)
            resp.raise_for_status()
            return resp.json().get('lists', [])
        except Exception as e:
            print(f"Error getting lists for folder {folder_id}: {e}")
            return []
    
    def _should_include_list(self, list_item):
        """Check if a list should be included (not archived, not empty, not excluded names)"""
        try:
            # Check if list is archived
            if list_item.get('archived', False):
                return False
            
            # Check list name for excluded patterns
            list_name = list_item.get('name', '').lower()
            excluded_patterns = [
                'archive', 'archived', 'xyz', 'temp', 'temporary', 'old', 'completed', 'done'
            ]
            
            for pattern in excluded_patterns:
                if pattern in list_name:
                    return False
            
            # Check if list has tasks (skip empty lists)
            task_count = list_item.get('task_count', 0)
            if task_count == 0:
                return False
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error checking list inclusion: {e}")
            return True  # Include by default if there's an error
    
    def _is_archived(self, folder_name):
        """Check if a folder should be skipped (archived or excluded)"""
        try:
            folder_lower = folder_name.lower()
            excluded_patterns = [
                'archive', 'archived', 'old', 'completed', 'done', 'temp', 'temporary'
            ]
            
            for pattern in excluded_patterns:
                if pattern in folder_lower:
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error checking folder archive status: {e}")
            return False  # Don't skip by default if there's an error

    def generate_comprehensive_assessment(self, analytics_data):
        """
        Generate a comprehensive team assessment using OpenAI
        Similar to the critical analysis format you provided
        """
        try:
            # Your OpenAI API key
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
            
            print("🤖 Generating comprehensive team assessment...")
            
            # Prepare detailed data for assessment
            member_workloads = analytics_data.get('member_workloads', {})
            overview_stats = analytics_data.get('overview_stats', {})
            load_balance = analytics_data.get('load_balance_insights', {})
            recommendations = analytics_data.get('recommendations', [])
            projects_data = analytics_data.get('projects', {})
            spaces_data = analytics_data.get('spaces', {})
            
            # Create comprehensive assessment prompt
            assessment_prompt = f"""
            Generate a critical team assessment report in the exact format below. Be brutally honest about issues the data reveals.

            TEAM DATA:
            - Total Members: {overview_stats.get('total_members', 0)}
            - Health Score: {overview_stats.get('health_score', 0)}/100
            - Total Projects: {overview_stats.get('total_projects', 0)}
            - Total Tasks: {overview_stats.get('total_active_tasks', 0)}
            
            MEMBER WORKLOADS:
            {self._format_member_workloads_for_assessment(member_workloads)}
            
            PROJECT ANALYSIS:
            {self._format_projects_for_assessment(projects_data, spaces_data)}
            
            LOAD BALANCE INSIGHTS:
            {self._format_load_balance_for_assessment(load_balance)}
            
            RECOMMENDATIONS:
            {self._format_recommendations_for_assessment(recommendations)}
            
            Generate a critical assessment in this exact format:
            
            [Current Date]
            
            Looking at these metrics critically, there are concerning patterns that the high health score of [X] doesn't fully capture.
            
            Average Workload Score Analysis
            [Critical analysis of workload distribution]
            
            Based on your scoring system:
            0-49: Light
            50-99: Balanced
            100-149: High
            150+: Overloaded
            
            [Detailed analysis of what the scores mean]
            
            PROJECT PERFORMANCE ANALYSIS
            [Critical analysis of project timelines, weights, and development duration]
            [Identify projects that are taking too long vs. their weight]
            [Highlight resource allocation issues in projects]
            
            Health Score Problems
            While [X] appears strong, the calculation has limitations:
            What it captures well:
            [List what the health score does well]
            
            What it misses:
            [List critical issues the health score masks]
            
            Task distribution efficiency
            [Analysis of task distribution]
            
            Overall Assessment
            [Critical summary of the real situation]
            
            Better Metrics Would Show:
            [What better metrics would reveal]
            
            [Concluding critical analysis]
            """
            
            # OpenAI API call for assessment
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a critical business analyst who exposes hidden problems in team data. Be brutally honest and identify issues that surface-level metrics miss. Use the exact format requested."
                    },
                    {
                        "role": "user",
                        "content": assessment_prompt
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assessment = result['choices'][0]['message']['content']
                
                # Add timestamp and metadata
                assessment_data = {
                    "assessment": assessment,
                    "generated_at": datetime.now().isoformat(),
                    "model_used": "gpt-3.5-turbo",
                    "data_source": "clickup_api",
                    "health_score": overview_stats.get('health_score', 0),
                    "total_members": overview_stats.get('total_members', 0),
                    "total_tasks": overview_stats.get('total_active_tasks', 0)
                }
                
                print("✅ Comprehensive assessment generated successfully!")
                return assessment_data
                
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                return self._generate_fallback_assessment(analytics_data)
                
        except Exception as e:
            print(f"Error generating assessment: {e}")
            return self._generate_fallback_assessment(analytics_data)
    
    def _format_member_workloads_for_assessment(self, member_workloads):
        """Format member workloads for assessment prompt"""
        if not member_workloads:
            return "No member data available"
        
        formatted = []
        for member, data in member_workloads.items():
            score = data.get('workload_score', 0)
            status = data.get('status', 'unknown')
            tasks = data.get('active_tasks', 0)
            formatted.append(f"- {member}: {score} points ({status}), {tasks} active tasks")
        
        return "\n".join(formatted)
    
    def _format_load_balance_for_assessment(self, load_balance):
        """Format load balance insights for assessment prompt"""
        if not load_balance:
            return "No load balance data available"
        
        highest = load_balance.get('highest_workload', {})
        lowest = load_balance.get('lowest_workload', {})
        
        return f"""
        - Highest: {highest.get('username', 'Unknown')} ({highest.get('score', 0)} points)
        - Lowest: {lowest.get('username', 'Unknown')} ({lowest.get('score', 0)} points)
        - Gap: {highest.get('score', 0) - lowest.get('score', 0)} points
        """
    
    def _format_recommendations_for_assessment(self, recommendations):
        """Format recommendations for assessment prompt"""
        if not recommendations:
            return "No recommendations available"
        
        formatted = []
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
            formatted.append(f"{i}. {rec.get('message', 'No message')}")
        return "\n".join(formatted)

    def _format_projects_for_assessment(self, projects_data, spaces_data):
        """Format project data for assessment prompt with weight and timeline analysis"""
        if not projects_data:
            return "No project data available"
        
        try:
            formatted = []
            current_date = datetime.now()
            
            for project_id, project in projects_data.items():
                if not project:
                    continue
                    
                project_name = project.get('name', 'Unknown Project')
                project_weight = project.get('weight', 0)
                project_status = project.get('status', 'unknown')
                
                # Get project creation and due dates
                date_created = project.get('date_created')
                due_date = project.get('due_date')
                
                # Calculate development duration
                development_days = 0
                if date_created:
                    try:
                        created_date = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                        development_days = (current_date - created_date).days
                    except:
                        development_days = 0
                
                # Estimate expected duration based on weight
                expected_days = self._estimate_project_duration(project_weight)
                
                # Determine if project is delayed
                is_delayed = development_days > expected_days if expected_days > 0 else False
                delay_days = development_days - expected_days if is_delayed else 0
                
                # Format project info
                project_info = f"- {project_name}:"
                project_info += f" Weight {project_weight} (expected {expected_days} days)"
                project_info += f", Status: {project_status}"
                project_info += f", Development: {development_days} days"
                
                if is_delayed:
                    project_info += f" ⚠️ DELAYED by {delay_days} days"
                elif development_days > 0:
                    project_info += f" ✅ On track"
                
                formatted.append(project_info)
            
            return "\n".join(formatted) if formatted else "No project data available"
            
        except Exception as e:
            print(f"Error formatting projects for assessment: {e}")
            return "Error analyzing project data"

    def _estimate_project_duration(self, weight):
        """Estimate project duration based on weight"""
        if weight <= 10:
            return 3  # Light weight: 3 days
        elif weight <= 25:
            return 7  # Medium weight: 1 week
        elif weight <= 50:
            return 14  # Heavy weight: 2 weeks
        elif weight <= 100:
            return 30  # Very heavy: 1 month
        else:
            return 45  # Extremely heavy: 1.5 months

    def _calculate_project_performance_metrics(self, project_analytics):
        """Calculate project performance metrics for assessment report"""
        try:
            current_date = datetime.now()
            projects_on_track = 0
            projects_delayed = 0
            total_delay_days = 0
            delayed_projects_count = 0
            
            for project_id, project in project_analytics.items():
                if not project:
                    continue
                    
                project_weight = project.get('weight', 0)
                date_created = project.get('date_created')
                
                if not date_created:
                    continue
                
                try:
                    # Calculate development duration
                    created_date = datetime.fromisoformat(date_created.replace('Z', '+00:00'))
                    development_days = (current_date - created_date).days
                    
                    # Estimate expected duration based on weight
                    expected_days = self._estimate_project_duration(project_weight)
                    
                    # Determine if project is delayed
                    if development_days > expected_days:
                        projects_delayed += 1
                        delay_days = development_days - expected_days
                        total_delay_days += delay_days
                        delayed_projects_count += 1
                    else:
                        projects_on_track += 1
                        
                except Exception as e:
                    print(f"Error calculating project performance for {project.get('name', 'Unknown')}: {e}")
                    continue
            
            # Calculate average delay
            avg_delay_days = total_delay_days / delayed_projects_count if delayed_projects_count > 0 else 0
            
            return {
                "projects_on_track": projects_on_track,
                "projects_delayed": projects_delayed,
                "avg_delay_days": round(avg_delay_days, 1),
                "total_projects_analyzed": projects_on_track + projects_delayed
            }
            
        except Exception as e:
            print(f"Error calculating project performance metrics: {e}")
            return {
                "projects_on_track": 0,
                "projects_delayed": 0,
                "avg_delay_days": 0,
                "total_projects_analyzed": 0
            }
    
    def _generate_fallback_assessment(self, analytics_data):
        """Generate fallback assessment when OpenAI fails"""
        try:
            member_workloads = analytics_data.get('member_workloads', {})
            overview_stats = analytics_data.get('overview_stats', {})
            
            # Calculate critical metrics
            scores = [w.get('workload_score', 0) for w in member_workloads.values()]
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            variance = max_score - min_score
            
            assessment = f"""
            [{datetime.now().strftime('%Y-%m-%d')}]
            
            CRITICAL TEAM ASSESSMENT (Fallback Analysis)
            
            Looking at these metrics critically, there are concerning patterns that the health score of {overview_stats.get('health_score', 0)} doesn't fully capture.
            
            Workload Distribution Analysis:
            - Average Score: {avg_score:.1f} points
            - Score Range: {min_score} - {max_score} points
            - Variance: {variance} points (High variance indicates imbalance)
            
            PROJECT PERFORMANCE ANALYSIS:
            {self._format_projects_for_assessment(analytics_data.get('projects', {}), analytics_data.get('spaces', {}))}
            
            Critical Issues Identified:
            1. Workload Imbalance: {variance} point gap between highest and lowest
            2. Resource Utilization: {len([w for w in member_workloads.values() if w.get('status') == 'light'])} members underutilized
            3. Overload Risk: {len([w for w in member_workloads.values() if w.get('status') == 'overloaded'])} members at risk of burnout
            
            Overall Assessment:
            Despite a health score of {overview_stats.get('health_score', 0)}, the team has significant operational inefficiencies that could lead to burnout, bottlenecks, and project delays.
            
            Immediate Actions Required:
            - Redistribute tasks to balance workloads
            - Utilize underutilized team members
            - Implement better task estimation processes
            """
            
            return {
                "assessment": assessment,
                "generated_at": datetime.now().isoformat(),
                "model_used": "fallback_analysis",
                "data_source": "clickup_api",
                "health_score": overview_stats.get('health_score', 0),
                "total_members": overview_stats.get('total_members', 0),
                "total_tasks": overview_stats.get('total_active_tasks', 0)
            }
            
        except Exception as e:
            print(f"Error in fallback assessment: {e}")
            return None

    def _get_list_tasks_with_status_filter(self, list_id, status_filters, debug=False):
        """Get tasks from a list with status filtering"""
        try:
            resp = requests.get(f"{self.base_url}/list/{list_id}/task", headers=self.headers)
            
            # Log response details for debugging
            if debug:
                print(f"📡 Tasks API Response Status: {resp.status_code}")
            
            if resp.status_code == 401:
                print(f"🔐 Unauthorized - check your API token for list {list_id}")
                return []
            elif resp.status_code == 403:
                print(f"🚫 Forbidden - check your API permissions for list {list_id}")
                return []
            elif resp.status_code == 404:
                print(f"❌ List not found: {list_id}")
                return []
            
            resp.raise_for_status()
            tasks_response = resp.json()
            
            # Validate response structure
            if not isinstance(tasks_response, dict):
                print(f"⚠️ Unexpected tasks response format: {type(tasks_response)}")
                return []
                
            all_tasks = tasks_response.get('tasks', [])
            
            if not isinstance(all_tasks, list):
                print(f"⚠️ Unexpected tasks format: {type(all_tasks)}")
                all_tasks = []
            
            if debug:
                print(f"🐛 DEBUG: Found {len(all_tasks)} total tasks in list")
            
            # Filter tasks by status
            filtered_tasks = []
            for task in all_tasks:
                task_status = task.get('status', {}).get('status', '').lower()
                if task_status in [s.lower() for s in status_filters]:
                    filtered_tasks.append(task)
            
            if debug:
                print(f"🐛 DEBUG: {len(filtered_tasks)} tasks match status filters: {status_filters}")
            
            return filtered_tasks
            
        except Exception as e:
            print(f"Error getting tasks for list {list_id}: {e}")
            return []
    
    def _analyze_project(self, list_item, tasks):
        """Analyze a single project/list - Enhanced with folder support and description"""
        try:
            assignees = set()
            total_time = 0
            high_priority_tasks = 0
            urgent_tasks = 0
            
            for task in tasks:
                # Get assignees
                for assignee in task.get('assignees', []):
                    username = assignee.get('username', 'unknown')
                    if username != 'unknown':
                        assignees.add(username)
                
                # Get time estimates (convert from milliseconds to minutes if needed)
                time_estimate = task.get('time_estimate')
                if time_estimate:
                    # ClickUp time estimates are usually in milliseconds
                    total_time += int(time_estimate) / 1000 / 60  # Convert to minutes
                
                # Count priority tasks
                priority = task.get('priority', {})
                if isinstance(priority, dict):
                    priority_level = priority.get('priority', '').lower()
                    if priority_level == 'urgent':
                        urgent_tasks += 1
                    elif priority_level == 'high':
                        high_priority_tasks += 1
            
            # Get due date from list or calculate from tasks
            due_date = list_item.get('due_date')
            if not due_date and tasks:
                # Find earliest due date from tasks
                task_due_dates = [
                    task.get('due_date') for task in tasks 
                    if task.get('due_date')
                ]
                if task_due_dates:
                    due_date = min(task_due_dates)
            
            # Build project name with folder context
            project_name = list_item.get('name', 'Unknown Project')
            project_description = list_item.get('description', '')
            folder_info = list_item.get('folder_info')
            
            if folder_info:
                project_display_name = f"{folder_info['folder_name']} / {project_name}"
            else:
                project_display_name = project_name
            
            project_data = {
                "name": project_display_name,  # Include folder in display name
                "original_name": project_name,  # Keep original name
                "description": project_description,  # Add project description for AI analysis
                "folder_name": folder_info['folder_name'] if folder_info else None,
                "folder_id": folder_info['folder_id'] if folder_info else None,
                "active_tasks": len(tasks),
                "assigned_members": list(assignees),
                "member_count": len(assignees),
                "total_time_estimate": round(total_time, 1),  # in minutes
                "due_date": due_date,
                "priority": self._determine_project_priority(urgent_tasks, high_priority_tasks, len(tasks)),
                "status": list_item.get('status', 'active'),
                "urgent_tasks": urgent_tasks,
                "high_priority_tasks": high_priority_tasks,
                # Additional metadata for complexity analysis
                "task_count_for_complexity": len(tasks),
                "has_description": bool(project_description and project_description.strip())
            }
            
            description_preview = project_description[:100] + "..." if len(project_description) > 100 else project_description
            print(f"📊 Project '{project_display_name}': {len(tasks)} tasks, {len(assignees)} members, {round(total_time, 1)}min estimated")
            if project_description:
                print(f"   📝 Description: {description_preview}")
            else:
                print(f"   📝 No description available")
                
            return project_data
            
        except Exception as e:
            print(f"❌ Error analyzing project {list_item.get('name', 'Unknown')}: {e}")
            return {
                "name": list_item.get('name', 'Unknown Project'),
                "original_name": list_item.get('name', 'Unknown Project'),
                "description": list_item.get('description', ''),
                "folder_name": None,
                "folder_id": None,
                "active_tasks": 0,
                "assigned_members": [],
                "member_count": 0,
                "total_time_estimate": 0,
                "due_date": None,
                "priority": "normal",
                "status": "unknown",
                "urgent_tasks": 0,
                "high_priority_tasks": 0,
                "task_count_for_complexity": 0,
                "has_description": False
            }
    
    
    def _determine_project_priority(self, urgent_tasks, high_priority_tasks, total_tasks):
        """Determine overall project priority based on task priorities"""
        if urgent_tasks > 0:
            return "urgent"
        elif high_priority_tasks > total_tasks * 0.5:  # More than 50% high priority
            return "high"
        elif high_priority_tasks > 0:
            return "medium"
        else:
            return "normal"
    
    def _process_task_for_member_workload(self, task, member_workloads, timeline_analysis, member_filters=None, debug=False):
        """Process a task for member workload analysis - Enhanced with folder support and better time handling"""
        try:
            assignees = task.get('assignees', [])
            
            if not assignees:
                # If no assignees, skip this task
                return
            
            for assignee in assignees:
                username = assignee.get('username', 'unknown')
                
                if username == 'unknown':
                    continue

                if member_filters is not None:
                    # Check if username matches any member filter (case-insensitive, partial match)
                    member_match = False
                    for target_member in member_filters:
                        if (target_member.lower() in username.lower() or 
                            username.lower() in target_member.lower()):
                            member_match = True
                            break
                    
                    if not member_match:
                        if debug:
                            print(f"⏭️ Skipping {username} (not in member filters: {member_filters})")
                        continue
                    
                # Initialize member workload if not exists
                if username not in member_workloads:
                    member_workloads[username] = {
                        "username": username,
                        "active_tasks": 0,
                        "projects_count": 0,
                        "projects": [],
                        "urgent_tasks": 0,
                        "high_priority_tasks": 0,
                        "due_soon_tasks": 0,
                        "total_time_estimate": 0,
                        "total_time_spent": 0,
                        "tasks": []  # Store actual task objects for frontend
                    }
                
                # Update task counts
                member_workloads[username]["active_tasks"] += 1
                
                # Get project/list information with folder context
                list_info = task.get('list', {})
                project_name = list_info.get('name', 'Unknown Project')
                
                # Store task for frontend modal viewing
                task_info = {
                    "name": task.get('name', 'Unnamed Task'),
                    "status": task.get('status', {}).get('status', 'unknown'),
                    "priority": task.get('priority'),
                    "due_date": task.get('due_date'),
                    "list_id": list_info.get('id'),
                    "project_name": project_name,
                    "url": task.get('url'),
                    "id": task.get('id')
                }
                member_workloads[username]["tasks"].append(task_info)
                
                # IMPROVED: Handle time estimates more carefully
                time_estimate = task.get('time_estimate')
                if time_estimate and str(time_estimate).isdigit():
                    try:
                        # Convert from milliseconds to minutes, handle potential edge cases
                        estimate_ms = int(time_estimate)
                        if estimate_ms > 0:  # Only add positive time estimates
                            estimate_minutes = estimate_ms / 1000 / 60
                            member_workloads[username]["total_time_estimate"] += estimate_minutes
                    except (ValueError, TypeError) as e:
                        if debug:
                            print(f"⚠️ Error parsing time estimate for task {task.get('name')}: {e}")
                
                # IMPROVED: Handle time spent more carefully
                time_spent = task.get('time_spent')
                if time_spent and str(time_spent).isdigit():
                    try:
                        spent_ms = int(time_spent)
                        if spent_ms > 0:  # Only add positive time spent
                            spent_minutes = spent_ms / 1000 / 60
                            member_workloads[username]["total_time_spent"] += spent_minutes
                    except (ValueError, TypeError) as e:
                        if debug:
                            print(f"⚠️ Error parsing time spent for task {task.get('name')}: {e}")
                
                # Check and update priority counts
                priority = task.get('priority', {})
                if isinstance(priority, dict):
                    priority_level = priority.get('priority', '').lower()
                    if priority_level == 'urgent':
                        member_workloads[username]["urgent_tasks"] += 1
                        # Add to timeline analysis
                        timeline_analysis["high_priority_tasks"].append({
                            "task": task.get('name', 'Unknown'),
                            "assignee": username,
                            "priority": priority_level,
                            "due_date": task.get('due_date')
                        })
                    elif priority_level == 'high':
                        member_workloads[username]["high_priority_tasks"] += 1
                
                # Check due dates and update due soon count
                due_date = task.get('due_date')
                if due_date:
                    try:
                        # ClickUp due dates are in milliseconds
                        due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
                        current_datetime = datetime.now()
                        days_until_due = (due_datetime.date() - current_datetime.date()).days
                        
                        # Due soon: within next 3 days
                        if 0 <= days_until_due <= 3:
                            member_workloads[username]["due_soon_tasks"] += 1
                            timeline_analysis["upcoming_deadlines"].append({
                                "task": task.get('name', 'Unknown'),
                                "assignee": username,
                                "due_date": due_date,
                                "days_until_due": days_until_due
                            })
                        
                        # Overdue: past due date
                        elif days_until_due < 0:
                            timeline_analysis["overdue_tasks"].append({
                                "task": task.get('name', 'Unknown'),
                                "assignee": username,
                                "due_date": due_date,
                                "days_overdue": abs(days_until_due)
                            })
                        
                        # Urgent deadlines: due today or tomorrow
                        elif days_until_due <= 1:
                            timeline_analysis["urgent_deadlines"].append({
                                "task": task.get('name', 'Unknown'),
                                "assignee": username,
                                "due_date": due_date,
                                "days_until_due": days_until_due
                            })
                            
                    except (ValueError, TypeError, OSError) as e:
                        print(f"⚠️ Error parsing due date for task {task.get('name', 'Unknown')}: {e}")
                
                # Track unique projects for this member
                current_projects = [p.get('name') for p in member_workloads[username]["projects"]]
                if project_name not in current_projects:
                    member_workloads[username]["projects"].append({
                        "name": project_name,
                        "due_date": due_date
                    })
                    member_workloads[username]["projects_count"] = len(member_workloads[username]["projects"])
            
        except Exception as e:
            print(f"❌ Error processing task {task.get('name', 'Unknown')} for workload: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_load_balance_insights(self, member_workloads):
        """Generate load balancing insights - UPDATED to use new score calculation method"""
        try:
            if not member_workloads:
                return {
                    "highest_workload": None,
                    "lowest_workload": None,
                    "overloaded_members": [],
                    "available_members": [],
                    "transfer_suggestions": []
                }
            
            # Calculate workload scores with computation details for each member
            for username, workload in member_workloads.items():
                score_data = self._calculate_workload_score_with_details(workload)
                workload.update(score_data)
                
                print(f"📊 {username}: Score={workload['workload_score']}, Status={workload['status']}")
            
            # Sort members by workload score
            sorted_workloads = sorted(member_workloads.items(), key=lambda x: x[1]["workload_score"], reverse=True)
            
            # Find highest and lowest workloads
            highest = sorted_workloads[0] if sorted_workloads else None
            lowest = sorted_workloads[-1] if sorted_workloads else None
            
            # Categorize members by workload status
            overloaded_members = []
            available_members = []
            
            for username, workload in member_workloads.items():
                if workload["status"] in ["overloaded", "high"]:
                    overloaded_members.append({
                        "username": username, 
                        "workload": {
                            "status": workload["status"],
                            "active_tasks": workload["active_tasks"],
                            "workload_score": workload["workload_score"]
                        }
                    })
                elif workload["status"] == "light":
                    available_members.append({
                        "username": username, 
                        "workload": {
                            "status": workload["status"],
                            "active_tasks": workload["active_tasks"],
                            "workload_score": workload["workload_score"]
                        }
                    })
            
            # Generate realistic transfer suggestions
            transfer_suggestions = []
            for overloaded in overloaded_members[:3]:  # Only top 3 overloaded
                for available in available_members[:2]:  # Only top 2 available
                    if len(transfer_suggestions) < 5:  # Limit total suggestions
                        transfer_suggestions.append({
                            "from_member": overloaded["username"],
                            "to_member": available["username"],
                            "task": {"name": f"Task redistribution from {overloaded['username']}"},
                            "reason": f"Balance workload - {overloaded['username']} is {overloaded['workload']['status']} ({overloaded['workload']['workload_score']} pts), {available['username']} has {available['workload']['status']} load ({available['workload']['workload_score']} pts)"
                        })
            
            insights = {
                "highest_workload": {
                    "username": highest[0],
                    "score": highest[1]["workload_score"],
                    "status": highest[1]["status"]
                } if highest else None,
                "lowest_workload": {
                    "username": lowest[0],
                    "score": lowest[1]["workload_score"],
                    "status": lowest[1]["status"]
                } if lowest else None,
                "overloaded_members": overloaded_members,
                "available_members": available_members,
                "transfer_suggestions": transfer_suggestions
            }
            
            print(f"✅ Generated load balance insights: {len(overloaded_members)} overloaded, {len(available_members)} available, {len(transfer_suggestions)} suggestions")
            return insights
            
        except Exception as e:
            print(f"❌ Error generating load balance insights: {e}")
            import traceback
            traceback.print_exc()
            return {
                "highest_workload": None,
                "lowest_workload": None,
                "overloaded_members": [],
                "available_members": [],
                "transfer_suggestions": []
            }
    
    def _generate_overview_stats(self, member_workloads, project_analytics, total_tasks):
        """Generate overview statistics - UPDATED with computation details"""
        try:
            total_members = len(member_workloads)
            total_projects = len(project_analytics)
            
            # Calculate averages
            if total_members > 0:
                total_workload_score = sum(w.get("workload_score", 0) for w in member_workloads.values())
                avg_workload_score = total_workload_score / total_members
                avg_tasks_per_member = total_tasks / total_members
            else:
                avg_workload_score = 0
                avg_tasks_per_member = 0
            
            # Count workload distribution by status
            status_counts = defaultdict(int)
            for workload in member_workloads.values():
                status = workload.get('status', 'unknown')
                status_counts[status] += 1
            
            # Calculate team health score with computation details
            health_data = self._calculate_team_health_score_with_details(status_counts, total_members)
            
            overview = {
                "total_members": total_members,
                "total_projects": total_projects,
                "total_active_tasks": total_tasks,
                "avg_tasks_per_member": round(avg_tasks_per_member, 1),
                "avg_workload_score": round(avg_workload_score, 1),
                "workload_distribution": dict(status_counts),
                "health_score": health_data["score"],
                "health_computation": health_data["computation"]
            }
            
            print(f"✅ Overview stats: {total_members} members, {total_projects} projects, {total_tasks} tasks, health: {health_data['score']}")
            return overview
            
        except Exception as e:
            print(f"❌ Error generating overview stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                "total_members": 0,
                "total_projects": 0,
                "total_active_tasks": 0,
                "avg_tasks_per_member": 0,
                "avg_workload_score": 0,
                "workload_distribution": {},
                "health_score": 0,
                "health_computation": {
                    "formula": "100 - (overloaded_ratio * 50) - (high_ratio * 25)",
                    "breakdown": {"note": "No data available"},
                    "total_calculation": "0"
                }
            }
    
    def _calculate_team_health_score_with_details(self, status_counts, total_members):
        """Calculate overall team health score (0-100) with computation details"""
        if total_members == 0:
            return {
                "score": 0,
                "computation": {
                    "formula": "100 - (overloaded_ratio * 50) - (high_ratio * 25)",
                    "breakdown": {"note": "No team members found"},
                    "total_calculation": "0"
                }
            }
        
        base_score = 100
        overloaded_count = status_counts.get("overloaded", 0)
        high_count = status_counts.get("high", 0)
        
        overloaded_ratio = overloaded_count / total_members
        high_ratio = high_count / total_members
        
        # Calculate penalties
        overloaded_penalty = overloaded_ratio * 50
        high_penalty = high_ratio * 25
        
        final_score = base_score - overloaded_penalty - high_penalty
        final_score = max(0, round(final_score))
        
        return {
            "score": final_score,
            "computation": {
                "formula": "100 - (overloaded_ratio * 50) - (high_ratio * 25)",
                "breakdown": {
                    "base_score": f"Starting score: {base_score}",
                    "overloaded_penalty": f"{overloaded_count}/{total_members} overloaded * 50 = -{overloaded_penalty:.1f}",
                    "high_penalty": f"{high_count}/{total_members} high load * 25 = -{high_penalty:.1f}",
                    "status_distribution": dict(status_counts)
                },
                "total_calculation": f"{base_score} - {overloaded_penalty:.1f} - {high_penalty:.1f} = {final_score}"
            }
        }
    
    def _generate_recommendations(self, member_workloads, timeline_analysis):
        """Generate actionable recommendations"""
        try:
            recommendations = []
            
            if not member_workloads:
                return recommendations
            
            # Check for overloaded members
            for username, workload in member_workloads.items():
                if workload.get("status") == "overloaded":
                    recommendations.append({
                        "type": "workload_warning",
                        "priority": "high",
                        "member": username,
                        "message": f"{username} has overloaded workload with {workload.get('active_tasks', 0)} active tasks (Score: {workload.get('workload_score', 0)})",
                        "action": "Consider redistributing tasks to team members with lighter workloads or extending deadlines"
                    })
                elif workload.get("status") == "high":
                    recommendations.append({
                        "type": "workload_warning",
                        "priority": "medium",
                        "member": username,
                        "message": f"{username} has high workload with {workload.get('active_tasks', 0)} active tasks (Score: {workload.get('workload_score', 0)})",
                        "action": "Monitor workload and consider task redistribution if new urgent tasks arise"
                    })
                
                # Check for urgent tasks
                if workload.get("urgent_tasks", 0) > 0:
                    recommendations.append({
                        "type": "urgent_tasks",
                        "priority": "high",
                        "member": username,
                        "message": f"{username} has {workload['urgent_tasks']} urgent task{'s' if workload['urgent_tasks'] > 1 else ''}",
                        "action": "Review urgent task priorities and ensure adequate resources are allocated"
                    })
                
                # Check for due soon tasks
                if workload.get("due_soon_tasks", 0) > 0:
                    recommendations.append({
                        "type": "deadline_warning",
                        "priority": "medium",
                        "member": username,
                        "message": f"{username} has {workload['due_soon_tasks']} task{'s' if workload['due_soon_tasks'] > 1 else ''} due within 3 days",
                        "action": "Ensure these tasks are prioritized and have necessary resources"
                    })
                
                # NEW: Check for over-time situations
                if workload.get("remaining_time_status", {}).get("is_over_time", False):
                    over_time_hours = workload.get("remaining_time_status", {}).get("over_time_hours", 0)
                    recommendations.append({
                        "type": "time_overrun",
                        "priority": "medium",
                        "member": username,
                        "message": f"{username} has spent {over_time_hours:.1f} hours more than estimated on current tasks",
                        "action": "Review time estimates and consider scope adjustments or additional resources"
                    })
            
            # Team-wide recommendations
            total_urgent = sum(w.get("urgent_tasks", 0) for w in member_workloads.values())
            total_due_soon = sum(w.get("due_soon_tasks", 0) for w in member_workloads.values())
            total_active = sum(w.get("active_tasks", 0) for w in member_workloads.values())
            
            if total_urgent > 3:
                recommendations.append({
                    "type": "team_urgent",
                    "priority": "high",
                    "member": None,
                    "message": f"Team has {total_urgent} urgent tasks across all members",
                    "action": "Consider emergency task prioritization meeting to redistribute urgent work"
                })
            
            if total_due_soon > 5:
                recommendations.append({
                    "type": "team_deadline",
                    "priority": "medium",
                    "member": None,
                    "message": f"Team has {total_due_soon} tasks due within 3 days",
                    "action": "Review upcoming deadlines and ensure adequate sprint planning"
                })
            
            # Check for unbalanced workload distribution
            if len(member_workloads) > 1:
                workload_scores = [w.get("workload_score", 0) for w in member_workloads.values()]
                max_score = max(workload_scores)
                min_score = min(workload_scores)
                
                if max_score - min_score > 100:
                    recommendations.append({
                        "type": "workload_imbalance",
                        "priority": "medium",
                        "member": None,
                        "message": f"Significant workload imbalance detected (range: {min_score}-{max_score} points)",
                        "action": "Consider redistributing tasks from overloaded to underutilized team members"
                    })
            
            # Check for timeline issues
            overdue_count = len(timeline_analysis.get("overdue_tasks", []))
            if overdue_count > 0:
                recommendations.append({
                    "type": "overdue_tasks",
                    "priority": "high",
                    "member": None,
                    "message": f"Team has {overdue_count} overdue task{'s' if overdue_count > 1 else ''}",
                    "action": "Immediate review of overdue tasks and deadline adjustments required"
                })
            
            print(f"✅ Generated {len(recommendations)} recommendations")
            return recommendations
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_demo_data(self):
        """
        Return demo data when API is not available - UPDATED with computation details
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
                    "workload_computation": {
                        "formula": "active_tasks * 10 + urgent_tasks * 25 + high_priority_tasks * 15 + due_soon_tasks * 10",
                        "breakdown": {
                            "active_tasks": "4 * 10 = 40",
                            "urgent_tasks": "1 * 25 = 25", 
                            "high_priority_tasks": "1 * 15 = 15",
                            "due_soon_tasks": "2 * 10 = 20"
                        },
                        "total_calculation": "40 + 25 + 15 + 20 = 100"
                    },
                    "status": "high",
                    "total_time_estimate": 1260,
                    "total_time_spent": 210,
                    "remaining_time": 1050,
                    "time_computation": {
                        "source_format": "ClickUp stores time in milliseconds",
                        "conversion_formula": "milliseconds ÷ 1000 ÷ 60 = minutes",
                        "estimates_breakdown": {
                            "total_minutes": 1260.0,
                            "total_hours": 21.0,
                            "conversion_note": "1260.0 minutes ÷ 60 = 21.0 hours"
                        },
                        "spent_breakdown": {
                            "total_minutes": 210.0,
                            "total_hours": 3.5,
                            "conversion_note": "210.0 minutes ÷ 60 = 3.5 hours"
                        },
                        "remaining_breakdown": {
                            "total_minutes": 1050.0,
                            "total_hours": 17.5,
                            "computation": "21.0h (estimated) - 3.5h (spent) = 17.5h",
                            "interpretation": "Negative = over-time, Positive = time remaining"
                        }
                    },
                    "remaining_time_status": {
                        "is_over_time": False,
                        "over_time_hours": 0,
                        "computation": "21.0h (estimated) - 3.5h (spent) = 17.5h",
                        "note": "Positive value indicates remaining work time"
                    }
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
                    "workload_score": 20.0,
                    "workload_computation": {
                        "formula": "active_tasks * 10 + urgent_tasks * 25 + high_priority_tasks * 15 + due_soon_tasks * 10",
                        "breakdown": {
                            "active_tasks": "2 * 10 = 20",
                            "urgent_tasks": "0 * 25 = 0",
                            "high_priority_tasks": "0 * 15 = 0", 
                            "due_soon_tasks": "0 * 10 = 0"
                        },
                        "total_calculation": "20 + 0 + 0 + 0 = 20"
                    },
                    "status": "light",
                    "total_time_estimate": 420,
                    "total_time_spent": 135,
                    "remaining_time": 285,
                    "time_computation": {
                        "source_format": "ClickUp stores time in milliseconds",
                        "conversion_formula": "milliseconds ÷ 1000 ÷ 60 = minutes",
                        "estimates_breakdown": {
                            "total_minutes": 420.0,
                            "total_hours": 7.0,
                            "conversion_note": "420.0 minutes ÷ 60 = 7.0 hours"
                        },
                        "spent_breakdown": {
                            "total_minutes": 135.0,
                            "total_hours": 2.25,
                            "conversion_note": "135.0 minutes ÷ 60 = 2.25 hours"
                        },
                        "remaining_breakdown": {
                            "total_minutes": 285.0,
                            "total_hours": 4.75,
                            "computation": "7.0h (estimated) - 2.25h (spent) = 4.75h",
                            "interpretation": "Negative = over-time, Positive = time remaining"
                        }
                    },
                    "remaining_time_status": {
                        "is_over_time": False,
                        "over_time_hours": 0,
                        "computation": "7.0h (estimated) - 2.25h (spent) = 4.75h",
                        "note": "Positive value indicates remaining work time"
                    }
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
                    "workload_score": 35.0,
                    "workload_computation": {
                        "formula": "active_tasks * 10 + urgent_tasks * 25 + high_priority_tasks * 15 + due_soon_tasks * 10",
                        "breakdown": {
                            "active_tasks": "1 * 10 = 10",
                            "urgent_tasks": "0 * 25 = 0",
                            "high_priority_tasks": "1 * 15 = 15",
                            "due_soon_tasks": "1 * 10 = 10"
                        },
                        "total_calculation": "10 + 0 + 15 + 10 = 35"
                    },
                    "status": "light",
                    "total_time_estimate": 200,
                    "total_time_spent": 250,
                    "remaining_time": -50,
                    "time_computation": {
                        "source_format": "ClickUp stores time in milliseconds",
                        "conversion_formula": "milliseconds ÷ 1000 ÷ 60 = minutes",
                        "estimates_breakdown": {
                            "total_minutes": 200.0,
                            "total_hours": 3.33,
                            "conversion_note": "200.0 minutes ÷ 60 = 3.33 hours"
                        },
                        "spent_breakdown": {
                            "total_minutes": 250.0,
                            "total_hours": 4.17,
                            "conversion_note": "250.0 minutes ÷ 60 = 4.17 hours"
                        },
                        "remaining_breakdown": {
                            "total_minutes": -50.0,
                            "total_hours": -0.83,
                            "computation": "3.33h (estimated) - 4.17h (spent) = -0.83h",
                            "interpretation": "Negative = over-time, Positive = time remaining"
                        }
                    },
                    "remaining_time_status": {
                        "is_over_time": True,
                        "over_time_hours": 0.83,
                        "computation": "3.33h (estimated) - 4.17h (spent) = -0.83h",
                        "note": "Negative value indicates time spent exceeds original estimate"
                    }
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
                    "username": "sarah",
                    "score": 20.0,
                    "status": "light"
                },
                "overloaded_members": [],
                "available_members": [
                    {"username": "sarah", "workload": {"status": "light", "active_tasks": 2, "workload_score": 20.0}},
                    {"username": "alex", "workload": {"status": "light", "active_tasks": 1, "workload_score": 35.0}}
                ],
                "transfer_suggestions": [
                    {
                        "from_member": "wiktor",
                        "to_member": "sarah", 
                        "task": {"name": "Database Schema"},
                        "reason": "Balance workload - wiktor is high (145.5 pts), sarah has light load (20.0 pts)"
                    }
                ]
            },
            "overview_stats": {
                "total_members": 3,
                "total_projects": 2,
                "total_active_tasks": 7,
                "avg_tasks_per_member": 2.3,
                "avg_workload_score": 66.8,
                "workload_distribution": {"high": 1, "light": 2},
                "health_score": 83,
                "health_computation": {
                    "formula": "100 - (overloaded_ratio * 50) - (high_ratio * 25)",
                    "breakdown": {
                        "base_score": "Starting score: 100",
                        "overloaded_penalty": "0/3 overloaded * 50 = -0.0",
                        "high_penalty": "1/3 high load * 25 = -8.3",
                        "status_distribution": {"high": 1, "light": 2}
                    },
                    "total_calculation": "100 - 0.0 - 8.3 = 92"
                }
            },
            "recommendations": [
                {
                    "type": "workload_warning",
                    "priority": "medium",
                    "member": "wiktor",
                    "message": "wiktor has high workload with 4 active tasks across 2 projects",
                    "action": "Monitor workload and consider task redistribution if new urgent tasks arise"
                },
                {
                    "type": "time_overrun",
                    "priority": "medium", 
                    "member": "alex",
                    "message": "alex has spent 50.0 hours more than estimated on current tasks",
                    "action": "Review time estimates and consider scope adjustments or additional resources"
                }
            ],
            "intelligent_summary": {
                "rule_based_analysis": {
                    "overall_assessment": "Generally balanced team workload",
                    "severity_level": "low",
                    "health_score_interpretation": "Good - Minor workload adjustments may be beneficial",
                    "key_concerns": [
                        "1 team member has time overrun issues (alex: 0.8h over)"
                    ],
                    "actionable_insights": [
                        "Team capacity appears underutilized - consider taking on additional work or projects",
                        "Time estimation accuracy needs improvement for alex's tasks"
                    ],
                    "priority_actions": [
                        "Continue monitoring current distribution"
                    ],
                    "workload_efficiency": {
                        "distribution_score": 88.3,
                        "utilization_rate": 83.5,
                        "balance_rating": "Good"
                    },
                    "team_metrics": {
                        "workload_variance": 125.5,
                        "average_utilization": "66.8 points",
                        "capacity_status": "Well-utilized"
                    }
                },
                "ai_enhanced_analysis": None,
                "generation_timestamp": datetime.now().isoformat(),
                "analysis_confidence": "medium"
            },
            "last_updated": datetime.now().isoformat(),
            "data_source": "demo_data"
        }
    
    def generate_comprehensive_fallback_analytics(self, member_workloads=None, project_analytics=None):
        """
        Generate comprehensive analytics without external APIs - excellent fallback when AI is unavailable
        """
        try:
            # If no data provided, use demo data as base
            if not member_workloads:
                demo_data = self._get_demo_data()
                member_workloads = demo_data.get('member_workloads', {})
                project_analytics = demo_data.get('project_analytics', {})
            
            # Advanced workload analysis
            workload_analysis = self._analyze_workload_patterns(member_workloads)
            
            # Project complexity scoring
            project_complexity = self._score_project_complexity(project_analytics)
            
            # Team efficiency metrics
            team_efficiency = self._calculate_team_efficiency_metrics(member_workloads)
            
            # Risk assessment
            risk_assessment = self._assess_project_risks(member_workloads, project_analytics)
            
            # Resource optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(member_workloads, project_analytics)
            
            return {
                "advanced_analytics": {
                    "workload_patterns": workload_analysis,
                    "project_complexity": project_complexity,
                    "team_efficiency": team_efficiency,
                    "risk_assessment": risk_assessment,
                    "optimization_suggestions": optimization_suggestions
                },
                "analysis_method": "comprehensive_rule_based",
                "confidence_level": "high",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error in fallback analytics: {e}")
            return {"error": str(e)}
    
    def _analyze_workload_patterns(self, member_workloads):
        """Analyze workload patterns and trends"""
        try:
            patterns = {}
            
            # Workload distribution analysis
            scores = [w.get('workload_score', 0) for w in member_workloads.values()]
            if scores:
                patterns['distribution'] = {
                    'mean': round(sum(scores) / len(scores), 2),
                    'median': sorted(scores)[len(scores)//2],
                    'std_dev': round((sum((x - sum(scores)/len(scores))**2 for x in scores) / len(scores))**0.5, 2),
                    'skewness': 'right' if max(scores) - sum(scores)/len(scores) > sum(scores)/len(scores) - min(scores) else 'left'
                }
            
            # Task type analysis
            total_urgent = sum(w.get('urgent_tasks', 0) for w in member_workloads.values())
            total_high_priority = sum(w.get('high_priority_tasks', 0) for w in member_workloads.values())
            total_due_soon = sum(w.get('due_soon_tasks', 0) for w in member_workloads.values())
            
            patterns['task_priorities'] = {
                'urgent': total_urgent,
                'high_priority': total_high_priority,
                'due_soon': total_due_soon,
                'priority_pressure': 'High' if total_urgent > 3 else 'Medium' if total_urgent > 1 else 'Low'
            }
            
            return patterns
            
        except Exception as e:
            print(f"Error analyzing workload patterns: {e}")
            return {}
    
    def _score_project_complexity(self, project_analytics):
        """Score project complexity based on multiple factors"""
        try:
            complexity_scores = {}
            
            for project_id, project in project_analytics.items():
                score = 0
                factors = []
                
                # Task count factor
                task_count = project.get('active_tasks', 0)
                if task_count > 20:
                    score += 3
                    factors.append(f"High task count ({task_count})")
                elif task_count > 10:
                    score += 2
                    factors.append(f"Medium task count ({task_count})")
                else:
                    score += 1
                    factors.append(f"Low task count ({task_count})")
                
                # Team size factor
                team_size = project.get('member_count', 0)
                if team_size > 5:
                    score += 2
                    factors.append(f"Large team ({team_size} members)")
                elif team_size > 2:
                    score += 1
                    factors.append(f"Medium team ({team_size} members)")
                else:
                    factors.append(f"Small team ({team_size} members)")
                
                # Time factor
                time_estimate = project.get('total_time_estimate', 0)
                if time_estimate > 2000:  # More than 33 hours
                    score += 2
                    factors.append("Long duration project")
                elif time_estimate > 1000:  # More than 16 hours
                    score += 1
                    factors.append("Medium duration project")
                else:
                    factors.append("Short duration project")
                
                complexity_scores[project_id] = {
                    'score': score,
                    'complexity_level': 'High' if score >= 5 else 'Medium' if score >= 3 else 'Low',
                    'factors': factors,
                    'project_name': project.get('name', 'Unknown')
                }
            
            return complexity_scores
            
        except Exception as e:
            print(f"Error scoring project complexity: {e}")
            return {}
    
    def _calculate_team_efficiency_metrics(self, member_workloads):
        """Calculate comprehensive team efficiency metrics"""
        try:
            metrics = {}
            
            # Utilization metrics
            active_members = len([w for w in member_workloads.values() if w.get('active_tasks', 0) > 0])
            total_members = len(member_workloads)
            
            metrics['utilization'] = {
                'active_members': active_members,
                'total_members': total_members,
                'utilization_rate': round((active_members / total_members) * 100, 1),
                'efficiency_score': 'High' if (active_members / total_members) > 0.8 else 'Medium' if (active_members / total_members) > 0.6 else 'Low'
            }
            
            # Workload balance metrics
            scores = [w.get('workload_score', 0) for w in member_workloads.values()]
            if scores:
                metrics['workload_balance'] = {
                    'variance': max(scores) - min(scores),
                    'balance_score': 'Balanced' if max(scores) - min(scores) < 50 else 'Moderate' if max(scores) - min(scores) < 100 else 'Imbalanced',
                    'recommendation': 'Monitor distribution' if max(scores) - min(scores) < 50 else 'Consider redistribution' if max(scores) - min(scores) < 100 else 'Immediate redistribution needed'
                }
            
            # Time management metrics
            time_overruns = [w for w in member_workloads.values() if w.get('remaining_time_status', {}).get('is_over_time', False)]
            metrics['time_management'] = {
                'members_with_overruns': len(time_overruns),
                'overrun_percentage': round((len(time_overruns) / total_members) * 100, 1),
                'estimation_accuracy': 'Accurate' if len(time_overruns) < total_members * 0.2 else 'Needs improvement' if len(time_overruns) < total_members * 0.5 else 'Poor'
            }
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating team efficiency: {e}")
            return {}
    
    def _assess_project_risks(self, member_workloads, project_analytics):
        """Assess project risks based on workload and project data"""
        try:
            risks = []
            
            # Overloaded member risks
            overloaded_members = [w for w in member_workloads.values() if w.get('status') == 'overloaded']
            if overloaded_members:
                risks.append({
                    'type': 'workload_risk',
                    'severity': 'High',
                    'description': f"{len(overloaded_members)} team member(s) are overloaded",
                    'impact': 'Project delays and quality issues',
                    'mitigation': 'Redistribute tasks or extend deadlines'
                })
            
            # Urgent task risks
            total_urgent = sum(w.get('urgent_tasks', 0) for w in member_workloads.values())
            if total_urgent > 5:
                risks.append({
                    'type': 'priority_risk',
                    'severity': 'Medium',
                    'description': f"High number of urgent tasks ({total_urgent})",
                    'impact': 'Resource contention and stress',
                    'mitigation': 'Review priorities and resource allocation'
                })
            
            # Time estimation risks
            time_overruns = [w for w in member_workloads.values() if w.get('remaining_time_status', {}).get('is_over_time', False)]
            if len(time_overruns) > len(member_workloads) * 0.3:
                risks.append({
                    'type': 'estimation_risk',
                    'severity': 'Medium',
                    'description': f"Time estimation accuracy issues ({len(time_overruns)} members)",
                    'impact': 'Schedule overruns and client dissatisfaction',
                    'mitigation': 'Improve estimation processes and training'
                })
            
            return risks
            
        except Exception as e:
            print(f"Error assessing project risks: {e}")
            return []
    
    def _generate_optimization_suggestions(self, member_workloads, project_analytics):
        """Generate actionable optimization suggestions"""
        try:
            suggestions = []
            
            # Workload optimization
            scores = [w.get('workload_score', 0) for w in member_workloads.values()]
            if scores and max(scores) - min(scores) > 100:
                suggestions.append({
                    'category': 'Workload Distribution',
                    'priority': 'High',
                    'suggestion': 'Redistribute tasks to balance workload across team',
                    'expected_impact': 'Improved team morale and project delivery',
                    'implementation': 'Review task assignments and move tasks from overloaded to underutilized members'
                })
            
            # Resource optimization
            underutilized_members = [w for w in member_workloads.values() if w.get('status') == 'light']
            if underutilized_members:
                suggestions.append({
                    'category': 'Resource Utilization',
                    'priority': 'Medium',
                    'suggestion': f'Utilize {len(underutilized_members)} underutilized team member(s)',
                    'expected_impact': 'Increased team productivity and capacity',
                    'implementation': 'Assign additional tasks or projects to underutilized members'
                })
            
            # Process optimization
            if len([w for w in member_workloads.values() if w.get('urgent_tasks', 0) > 0]) > 3:
                suggestions.append({
                    'category': 'Process Improvement',
                    'priority': 'Medium',
                    'suggestion': 'Review task prioritization and planning processes',
                    'expected_impact': 'Reduced urgent task pressure and better resource planning',
                    'implementation': 'Implement better sprint planning and priority management'
                })
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating optimization suggestions: {e}")
            return []

