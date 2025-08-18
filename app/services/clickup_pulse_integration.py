# #!/usr/bin/env python3
# """
# ClickUp Pulse Integration
# Modified from the original ClickUp analytics script for Pulse dashboard integration
# """

# import requests
# import time
# from datetime import datetime, timedelta
# import json
# from collections import defaultdict

# TEAM_MEMBERS = ['Jan', 'Tricia Kennedy', 'Arif', 'wiktor']

# class ClickUpPulseIntegration:
#     def __init__(self, api_token, team_id):
#         self.api_token = api_token
#         self.team_id = team_id
#         self.headers = {'Authorization': api_token}
#         self.base_url = 'https://api.clickup.com/api/v2'
        
#         # Working hours configuration
#         self.WORKDAY_START_HOUR = 9
#         self.WORKDAY_END_HOUR = 17
#         self.LUNCH_BREAK_START = 12
#         self.LUNCH_BREAK_END = 12.5
#         self.WORKING_HOURS_PER_DAY = 7.5
    
#     def generate_pulse_analytics(self, target_date=None, debug=False):
#         """
#         Generate comprehensive pulse analytics from ClickUp data
#         """
#         try:
#             print("🔍 Getting team information...")
#             members = self._get_team_members()
            
#             if debug:
#                 print("🐛 DEBUG: Found {} team members".format(len(members)))
#                 for member in members[:3]:  # Show first 3 members for debugging
#                     user = member.get('user', {})
#                     username = user.get('username', 'Unknown')
#                     user_id = user.get('id', 'N/A')
#                     print("🐛 DEBUG: Member - {} (ID: {})".format(username, user_id))
            
#             if not members:
#                 print("❌ No team members found! Check team_id and API key.")
#                 return None
            
#             print("✅ Found {} team members".format(len(members)))
            
#             # Use provided date or default to today
#             if target_date:
#                 analysis_date = target_date
#             else:
#                 analysis_date = datetime.now().date()
            
#             # Check if it's a weekend
#             is_weekend = analysis_date.weekday() >= 5  # Saturday = 5, Sunday = 6
            
#             if is_weekend and debug:
#                 weekday_num = analysis_date.weekday()
#                 print("🐛 DEBUG: {} is a weekend day (weekday: {})".format(analysis_date, weekday_num))
#                 print("🐛 DEBUG: This might explain empty results if no weekend activity")
            
#             # Get time range for the analysis date
#             start_ts, current_ts, start_of_day, current_time = self._get_date_timestamps(analysis_date)
#             work_hours = "{}:00-{}:00".format(self.WORKDAY_START_HOUR, self.WORKDAY_END_HOUR)
#             print("⏰ Analysis period: {} (Working hours: {})".format(analysis_date, work_hours))
            
#             # Analyze each member
#             clickup_data = {
#                 'date': analysis_date.strftime('%Y-%m-%d'),
#                 'timestamp': datetime.now().isoformat(),
#                 'members_analyzed': 0,
#                 'detailed_data': {},
#                 'debug_info': {
#                     'is_weekend': is_weekend,
#                     'total_team_members': len(members),
#                     'analysis_date': str(analysis_date)
#                 } if debug else {}
#             }
            
#             # More flexible member targeting - try all if no specific targets
#             target_members = TEAM_MEMBERS 
#             found_members = []
            
#             for member in members:
#                 user = member.get('user', {})
#                 username = user.get('username', 'Unknown')
#                 user_id = user.get('id')
                
#                 if debug:
#                     print("🐛 DEBUG: Checking member {}".format(username))
                
#                 # Be more flexible - include if username contains any target name or if no targets specified
#                 should_analyze = False
#                 if not target_members:
#                     should_analyze = True
#                 else:
#                     for target in target_members:
#                         if target.lower() in username.lower() or username.lower() in target.lower():
#                             should_analyze = True
#                             break
                
#                 if not should_analyze:
#                     if debug:
#                         print("🐛 DEBUG: Skipping {} (not in target list)".format(username))
#                     continue
                    
#                 found_members.append(username)
#                 print("\n👤 Analyzing {} (ID: {})...".format(username, user_id))
                
#                 # Get tasks for this member
#                 tasks = self._get_member_tasks(user_id, debug)
#                 print("   📋 Found {} open tasks".format(len(tasks)))
                
#                 if debug and tasks:
#                     sample_task = tasks[0]
#                     task_name = sample_task.get('name', 'Unknown')
#                     task_status = sample_task.get('status', {}).get('status', 'Unknown')
#                     print("🐛 DEBUG: Sample task: {} (Status: {})".format(task_name, task_status))
                
#                 # Analyze activity
#                 task_periods, downtime_periods, task_details = self._analyze_task_activity(
#                     tasks, start_ts, current_ts, start_of_day, current_time, debug
#                 )
                
#                 clickup_data['detailed_data'][username] = {
#                     'task_periods': task_periods,
#                     'downtime_periods': downtime_periods,
#                     'task_details': task_details
#                 }
                
#                 clickup_data['members_analyzed'] += 1
#                 periods_info = "Tasks: {}, Periods: {}, Downtime: {}".format(
#                     len(task_details), len(task_periods), len(downtime_periods)
#                 )
#                 print("   ✅ Analysis complete - {}".format(periods_info))
                
#                 # Rate limiting delay
#                 time.sleep(1)
            
#             if debug:
#                 print("🐛 DEBUG: Found and analyzed members: {}".format(found_members))
#                 print("🐛 DEBUG: Total analyzed: {}".format(clickup_data['members_analyzed']))
            
#             if clickup_data['members_analyzed'] == 0:
#                 print("❌ No members were analyzed! This could be due to:")
#                 print("   - Username mismatch in target_members list")
#                 print("   - Weekend/non-working day with no activity")
#                 print("   - API permissions issue")
#                 print("   - No open tasks for team members")
                
#                 if debug:
#                     available_names = [m.get('user', {}).get('username', 'Unknown') for m in members[:5]]
#                     print("🐛 DEBUG: Available usernames: {}".format(available_names))
                
#                 return None
            
#             # Transform ClickUp data to Pulse format
#             pulse_data = self._transform_to_pulse_format(clickup_data)
            
#             return pulse_data
            
#         except Exception as e:
#             print("❌ Error generating pulse analytics: {}".format(e))
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _get_team_members(self):
#         """Get all team members"""
#         try:
#             resp = requests.get("{}/team".format(self.base_url), headers=self.headers)
#             resp.raise_for_status()
#             teams = resp.json().get('teams', [])
            
#             for team in teams:
#                 if team.get('id') == str(self.team_id):
#                     return team.get('members', [])
#             return []
#         except Exception as e:
#             print("Error getting team members: {}".format(e))
#             return []
    
#     def _get_date_timestamps(self, target_date):
#         """Get start and end timestamps for a specific date"""
#         if isinstance(target_date, str):
#             target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
#         # Create datetime objects for the target date
#         start_of_day = datetime.combine(target_date, datetime.min.time())
        
#         # If analyzing today, use current time; otherwise use end of day
#         if target_date == datetime.now().date():
#             current_time = datetime.now()
#         else:
#             current_time = datetime.combine(target_date, datetime.max.time().replace(microsecond=0))
        
#         # Convert to ClickUp timestamps (milliseconds)
#         start_ts = int(start_of_day.timestamp() * 1000)
#         current_ts = int(current_time.timestamp() * 1000)
        
#         return start_ts, current_ts, start_of_day, current_time
    
#     def _get_member_tasks(self, member_id, debug=False, max_retries=3):
#         """Get all open tasks for a team member"""
#         for attempt in range(max_retries):
#             try:
#                 # Get open tasks only
#                 url = "{}/team/{}/task?assignees[]={}&include_closed=false".format(
#                     self.base_url, self.team_id, member_id
#                 )
                
#                 if debug:
#                     print("🐛 DEBUG: API URL: {}".format(url))
                
#                 resp = requests.get(url, headers=self.headers)
                
#                 if resp.status_code == 429:  # Rate limited
#                     wait_time = 60
#                     print("    Rate limited. Waiting {} seconds...".format(wait_time))
#                     time.sleep(wait_time)
#                     continue
                
#                 if debug:
#                     print("🐛 DEBUG: API Response status: {}".format(resp.status_code))
                    
#                 resp.raise_for_status()
#                 data = resp.json()
                
#                 tasks = data.get('tasks', [])
                
#                 if debug and tasks:
#                     print("🐛 DEBUG: Sample task data structure:")
#                     sample_task = tasks[0]
#                     print("🐛 DEBUG: Task keys: {}".format(list(sample_task.keys())))
#                     print("🐛 DEBUG: Task name: {}".format(sample_task.get('name', 'N/A')))
#                     print("🐛 DEBUG: Task status: {}".format(sample_task.get('status', 'N/A')))
#                     print("🐛 DEBUG: Task date_updated: {}".format(sample_task.get('date_updated', 'N/A')))
                
#                 return tasks
                
#             except requests.exceptions.RequestException as e:
#                 print("    Error getting tasks (attempt {}): {}".format(attempt + 1, e))
#                 if debug:
#                     print("🐛 DEBUG: Request exception details: {}".format(str(e)))
#                 if attempt < max_retries - 1:
#                     time.sleep(10)
        
#         print("    Failed to fetch tasks after all retries")
#         return []
    
#     def _analyze_task_activity(self, tasks, start_ts, current_ts, start_of_day, current_time, debug=False):
#         """Analyze task activity and identify downtime periods"""
#         task_periods = []
#         downtime_periods = []
#         task_details = []
        
#         # Working hours boundaries for the analysis date
#         analysis_date = start_of_day.date()
#         work_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_START_HOUR))
#         lunch_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.LUNCH_BREAK_START))
#         lunch_end = datetime.combine(analysis_date, datetime.min.time().replace(
#             hour=int(self.LUNCH_BREAK_END), minute=int((self.LUNCH_BREAK_END % 1) * 60)))
#         work_end = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_END_HOUR))
        
#         if debug:
#             print("🐛 DEBUG: Analysis date: {}".format(analysis_date))
#             print("🐛 DEBUG: Working hours: {} - {}".format(
#                 work_start.strftime('%H:%M'), work_end.strftime('%H:%M')
#             ))
#             print("🐛 DEBUG: Is weekend: {}".format(analysis_date.weekday() >= 5))
        
#         print("    Working hours: {} - {}".format(
#             work_start.strftime('%H:%M'), work_end.strftime('%H:%M')
#         ))
        
#         # Track task activities
#         activities = []
        
#         for task in tasks:
#             try:
#                 # Get task details
#                 task_name = task.get('name', 'Unknown Task')
#                 task_id = task.get('id', 'unknown')
#                 task_status = task.get('status', {}).get('status', 'unknown')
#                 priority = task.get('priority')
#                 due_date = task.get('due_date')
                
#                 # Store task details for dashboard
#                 task_details.append({
#                     'name': task_name,
#                     'id': task_id,
#                     'status': task_status,
#                     'due_date': due_date,
#                     'priority': priority
#                 })
                
#                 # Check for time tracking or recent activity
#                 date_updated = task.get('date_updated')
#                 if date_updated:
#                     updated_time = datetime.fromtimestamp(int(date_updated) / 1000)
                    
#                     if debug:
#                         print("🐛 DEBUG: Task '{}' updated at: {}".format(task_name, updated_time))
#                         print("🐛 DEBUG: Analysis date: {}, Task date: {}".format(
#                             analysis_date, updated_time.date()
#                         ))
                    
#                     # Check if activity is on the analysis date and within working hours
#                     if (updated_time.date() == analysis_date and
#                         work_start <= updated_time <= work_end and
#                         not (lunch_start <= updated_time <= lunch_end)):
                        
#                         activities.append({
#                             'time': updated_time,
#                             'task_name': task_name,
#                             'task_id': task_id,
#                             'type': 'update'
#                         })
                        
#                         if debug:
#                             print("🐛 DEBUG: Added activity: {} at {}".format(task_name, updated_time))
#                     elif debug:
#                         if updated_time.date() != analysis_date:
#                             print("🐛 DEBUG: Skipped task (wrong date): {} != {}".format(
#                                 updated_time.date(), analysis_date
#                             ))
#                         elif not (work_start <= updated_time <= work_end):
#                             print("🐛 DEBUG: Skipped task (outside work hours): {}".format(
#                                 updated_time.strftime('%H:%M')
#                             ))
#                         elif lunch_start <= updated_time <= lunch_end:
#                             print("🐛 DEBUG: Skipped task (during lunch): {}".format(
#                                 updated_time.strftime('%H:%M')
#                             ))
                
#             except Exception as e:
#                 print("    Error processing task {}: {}".format(task.get('id', 'unknown'), e))
#                 if debug:
#                     import traceback
#                     traceback.print_exc()
        
#         # Sort activities by time
#         activities.sort(key=lambda x: x['time'])
        
#         print("    Found {} activities in working hours".format(len(activities)))
#         if debug:
#             activity_list = []
#             for a in activities:
#                 activity_str = "{} at {}".format(a['task_name'], a['time'].strftime('%H:%M'))
#                 activity_list.append(activity_str)
#             print("🐛 DEBUG: Activities: {}".format(activity_list))
        
#         # For weekends or days with no activity, create some task periods from task details
#         # This helps show current workload even if no recent activity
#         if not activities and task_details:
#             if debug:
#                 print("🐛 DEBUG: No activities found, but {} tasks exist".format(len(task_details)))
#                 print("🐛 DEBUG: Creating estimated task periods based on open tasks")
            
#             # Create estimated periods for open tasks
#             current_work_time = work_start
#             for i, task in enumerate(task_details[:3]):  # Limit to first 3 tasks
#                 if current_work_time >= work_end:
#                     break
                
#                 # Estimate 2-hour periods for tasks
#                 period_duration = 2.0
#                 period_end = min(current_work_time + timedelta(hours=period_duration), work_end)
                
#                 task_periods.append({
#                     'start': current_work_time.isoformat(),
#                     'end': period_end.isoformat(),
#                     'task_name': task['name'],
#                     'task_id': task['id'],
#                     'duration_hours': round((period_end - current_work_time).total_seconds() / 3600, 2),
#                     'status': 'estimated'  # Mark as estimated
#                 })
                
#                 current_work_time = period_end + timedelta(hours=0.5)  # Add break
#         else:
#             # Create task periods from actual activities
#             for i, activity in enumerate(activities):
#                 start_time = activity['time']
                
#                 # Estimate task duration (1-2 hours by default, or until next activity)
#                 if i < len(activities) - 1:
#                     next_time = activities[i + 1]['time']
#                     duration = min((next_time - start_time).total_seconds() / 3600, 2.0)
#                 else:
#                     # Last activity - assume 1 hour or until end of workday
#                     time_to_end = (work_end - start_time).total_seconds() / 3600
#                     duration = min(time_to_end, 1.0)
                
#                 end_time = start_time + timedelta(hours=duration)
                
#                 # Ensure we don't go past working hours
#                 if end_time > work_end:
#                     end_time = work_end
#                     duration = (end_time - start_time).total_seconds() / 3600
                
#                 if duration > 0:
#                     task_periods.append({
#                         'start': start_time.isoformat(),
#                         'end': end_time.isoformat(),
#                         'task_name': activity['task_name'],
#                         'task_id': activity['task_id'],
#                         'duration_hours': round(duration, 2),
#                         'status': 'active'
#                     })
        
#         # Calculate downtime periods (simplified for now)
#         if not task_periods:
#             # If analyzing today and it's current working hours, show some downtime
#             if analysis_date == datetime.now().date() and work_start <= datetime.now() <= work_end:
#                 downtime_start = work_start
#                 downtime_end = min(datetime.now(), work_end)
#                 downtime_duration = (downtime_end - downtime_start).total_seconds() / 3600
                
#                 if downtime_duration > 0.25:  # More than 15 minutes
#                     reason = 'No activity detected today' if analysis_date == datetime.now().date() else 'No activity on this date'
#                     downtime_periods.append({
#                         'start': downtime_start.isoformat(),
#                         'end': downtime_end.isoformat(),
#                         'duration_hours': round(downtime_duration, 2),
#                         'reason': reason
#                     })
        
#         print("    Task periods: {}".format(len(task_periods)))
#         print("    Downtime periods: {}".format(len(downtime_periods)))
        
#         if debug:
#             print("🐛 DEBUG: Task periods: {}".format(len(task_periods)))
#             for period in task_periods[:2]:  # Show first 2
#                 print("🐛 DEBUG: Period: {} ({}h)".format(
#                     period['task_name'], period['duration_hours']
#                 ))
        
#         return task_periods, downtime_periods, task_details
    
#     def _transform_to_pulse_format(self, clickup_data):
#         """
#         Transform ClickUp data to Pulse dashboard format
#         """
#         try:
#             # Initialize pulse data structure
#             member_workloads = {}
#             project_analytics = {}
            
#             # Process each member's data
#             for username, member_data in clickup_data['detailed_data'].items():
#                 # Calculate workload for this member
#                 workload = self._calculate_member_workload(username, member_data)
#                 member_workloads[username] = workload
                
#                 # Update project analytics
#                 self._update_project_analytics(project_analytics, member_data, username)
            
#             # Convert sets to lists for JSON serialization (do this after all members processed)
#             for project_id, project in project_analytics.items():
#                 if isinstance(project["assigned_members"], set):
#                     project["assigned_members"] = list(project["assigned_members"])
#                     project["member_count"] = len(project["assigned_members"])
#                 elif isinstance(project["assigned_members"], list):
#                     project["member_count"] = len(project["assigned_members"])
            
#             # Generate additional analytics
#             timeline_analysis = self._analyze_timeline(clickup_data)
#             load_balance_insights = self._generate_load_balance_insights(member_workloads, timeline_analysis)
#             recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
#             overview_stats = self._calculate_overview_stats(member_workloads, project_analytics)
            
#             return {
#                 "member_workloads": member_workloads,
#                 "project_analytics": project_analytics,
#                 "timeline_analysis": timeline_analysis,
#                 "load_balance_insights": load_balance_insights,
#                 "recommendations": recommendations,
#                 "overview_stats": overview_stats,
#                 "last_updated": datetime.now().isoformat(),
#                 "data_source": "clickup_live",
#                 "analysis_date": clickup_data['date']
#             }
            
#         except Exception as e:
#             print("Error transforming to pulse format: {}".format(e))
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _calculate_member_workload(self, username, member_data):
#         """
#         Calculate workload for a single member
#         """
#         # Count active tasks
#         active_tasks = len(member_data.get('task_details', []))
        
#         # Get projects from task details
#         projects = {}
#         for task in member_data.get('task_details', []):
#             # In a real scenario, you'd get project info from task
#             # For now, we'll use task status as a simple project grouping
#             project_name = "Project {}".format(task.get('status', 'unknown').title())
#             if project_name not in projects:
#                 projects[project_name] = {
#                     "name": project_name,
#                     "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
#                     "status": "active",
#                     "priority": "medium"
#                 }
        
#         projects_list = list(projects.values())
        
#         # Calculate time metrics
#         total_time_estimate = sum(period.get('duration_hours', 0) * 60 
#                                 for period in member_data.get('task_periods', []))
#         total_downtime = sum(period.get('duration_hours', 0) * 60 
#                            for period in member_data.get('downtime_periods', []))
        
#         # Count priority tasks
#         urgent_tasks = 0
#         high_priority_tasks = 0
#         due_soon_tasks = 0
        
#         for task in member_data.get('task_details', []):
#             priority = task.get('priority', {})
#             if isinstance(priority, dict):
#                 priority_level = priority.get('priority', 'medium')
#             else:
#                 priority_level = str(priority) if priority else 'medium'
            
#             if priority_level == 'urgent':
#                 urgent_tasks += 1
#             elif priority_level == 'high':
#                 high_priority_tasks += 1
            
#             # Check due date
#             due_date = task.get('due_date')
#             if due_date:
#                 try:
#                     due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                     days_until_due = (due_datetime - datetime.now()).days
#                     if days_until_due <= 2:
#                         due_soon_tasks += 1
#                 except:
#                     pass
        
#         # Calculate workload score
#         workload_score = self._calculate_workload_score({
#             "active_tasks": active_tasks,
#             "urgent_tasks": urgent_tasks,
#             "high_priority_tasks": high_priority_tasks,
#             "due_soon_tasks": due_soon_tasks,
#             "projects_count": len(projects_list),
#             "remaining_time": total_time_estimate
#         })
        
#         # Determine status
#         status = self._determine_workload_status(workload_score)
        
#         return {
#             "username": username,
#             "active_tasks": active_tasks,
#             "projects_count": len(projects_list),
#             "projects": projects_list,
#             "tasks": member_data.get('task_details', []),
#             "total_time_estimate": total_time_estimate,
#             "total_time_spent": 0,  # Would need time tracking data
#             "urgent_tasks": urgent_tasks,
#             "high_priority_tasks": high_priority_tasks,
#             "due_soon_tasks": due_soon_tasks,
#             "workload_score": workload_score,
#             "status": status,
#             "remaining_time": total_time_estimate,
#             "downtime_hours": total_downtime / 60
#         }
    
#     def _calculate_workload_score(self, workload):
#         """Calculate workload score based on multiple factors"""
#         score = 0
        
#         # Base score from active tasks
#         score += workload.get("active_tasks", 0) * 10
        
#         # Additional weight for urgent/high priority
#         score += workload.get("urgent_tasks", 0) * 25
#         score += workload.get("high_priority_tasks", 0) * 15
        
#         # Weight for due soon tasks
#         score += workload.get("due_soon_tasks", 0) * 20
        
#         # Weight for time estimates (hours)
#         remaining_hours = workload.get("remaining_time", 0) / 60
#         score += remaining_hours * 2
        
#         # Weight for number of projects
#         score += workload.get("projects_count", 0) * 5
        
#         return round(score, 1)
    
#     def _determine_workload_status(self, score):
#         """Determine workload status based on score"""
#         if score >= 150:
#             return "overloaded"
#         elif score >= 100:
#             return "high"
#         elif score >= 50:
#             return "balanced" 
#         else:
#             return "light"
    
#     def _update_project_analytics(self, project_analytics, member_data, username):
#         """Update project analytics with member data"""
#         # This is simplified - in reality you'd group by actual project IDs
#         for task in member_data.get('task_details', []):
#             project_name = "Project {}".format(task.get('status', 'unknown').title())
            
#             if project_name not in project_analytics:
#                 project_analytics[project_name] = {
#                     "name": project_name,
#                     "active_tasks": 0,
#                     "assigned_members": set(),
#                     "total_time_estimate": 0,
#                     "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
#                     "priority": "medium",
#                     "status": "active"
#                 }
            
#             project_analytics[project_name]["active_tasks"] += 1
            
#             # Safely add to set (check if it's still a set)
#             if isinstance(project_analytics[project_name]["assigned_members"], set):
#                 project_analytics[project_name]["assigned_members"].add(username)
#             elif isinstance(project_analytics[project_name]["assigned_members"], list):
#                 if username not in project_analytics[project_name]["assigned_members"]:
#                     project_analytics[project_name]["assigned_members"].append(username)
    
#     def _analyze_timeline(self, clickup_data):
#         """Analyze timeline and deadlines"""
#         analysis = {
#             "urgent_deadlines": [],
#             "upcoming_deadlines": [],
#             "overdue_tasks": [],
#             "high_priority_tasks": [],
#             "deadline_pressure_by_member": defaultdict(int)
#         }
        
#         for username, member_data in clickup_data['detailed_data'].items():
#             for task in member_data.get('task_details', []):
#                 # Priority analysis
#                 priority = task.get('priority', {})
#                 if isinstance(priority, dict):
#                     priority_level = priority.get('priority', 'medium')
#                 else:
#                     priority_level = str(priority) if priority else 'medium'
                
#                 if priority_level in ["urgent", "high"]:
#                     analysis["high_priority_tasks"].append(task)
                
#                 # Deadline analysis
#                 due_date = task.get('due_date')
#                 if due_date:
#                     try:
#                         due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                         days_until_due = (due_datetime - datetime.now()).days
                        
#                         if days_until_due < 0:
#                             analysis["overdue_tasks"].append(task)
#                         elif days_until_due <= 1:
#                             analysis["urgent_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 3
#                         elif days_until_due <= 7:
#                             analysis["upcoming_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 1
#                     except:
#                         pass
        
#         # Convert defaultdict to regular dict
#         analysis["deadline_pressure_by_member"] = dict(analysis["deadline_pressure_by_member"])
        
#         return analysis
    
#     def _generate_load_balance_insights(self, workloads, timeline_analysis):
#         """Generate load balancing insights"""
#         insights = {
#             "highest_workload": None,
#             "lowest_workload": None,
#             "overloaded_members": [],
#             "available_members": [],
#             "transfer_suggestions": []
#         }
        
#         if not workloads:
#             return insights
        
#         # Find highest and lowest workload
#         sorted_workloads = sorted(workloads.items(), key=lambda x: x[1]["workload_score"], reverse=True)
        
#         if sorted_workloads:
#             insights["highest_workload"] = {
#                 "username": sorted_workloads[0][0],
#                 "score": sorted_workloads[0][1]["workload_score"],
#                 "status": sorted_workloads[0][1]["status"],
#                 "details": sorted_workloads[0][1]
#             }
            
#             insights["lowest_workload"] = {
#                 "username": sorted_workloads[-1][0],
#                 "score": sorted_workloads[-1][1]["workload_score"],
#                 "status": sorted_workloads[-1][1]["status"],
#                 "details": sorted_workloads[-1][1]
#             }
        
#         # Identify overloaded and available members
#         for username, workload in workloads.items():
#             if workload["status"] in ["overloaded", "high"]:
#                 insights["overloaded_members"].append({
#                     "username": username,
#                     "workload": workload
#                 })
#             elif workload["status"] == "light":
#                 insights["available_members"].append({
#                     "username": username,
#                     "workload": workload
#                 })
        
#         return insights
    
#     def _generate_recommendations(self, workloads, timeline_analysis):
#         """Generate recommendations based on workload analysis"""
#         recommendations = []
        
#         # Check for overloaded members
#         overloaded = [w for w in workloads.values() if w["status"] in ["overloaded", "high"]]
#         if overloaded:
#             for member in overloaded:
#                 message = "{} has {} workload with {} active tasks across {} projects".format(
#                     member["username"], member["status"], member["active_tasks"], member["projects_count"]
#                 )
#                 recommendations.append({
#                     "type": "workload_warning",
#                     "priority": "high",
#                     "member": member["username"],
#                     "message": message,
#                     "action": "Consider redistributing tasks or extending deadlines"
#                 })
        
#         # Check for urgent deadlines
#         if timeline_analysis["urgent_deadlines"]:
#             urgent_count = len(timeline_analysis["urgent_deadlines"])
#             recommendations.append({
#                 "type": "deadline_alert",
#                 "priority": "urgent",
#                 "message": "{} tasks due within 24 hours".format(urgent_count),
#                 "action": "Review urgent tasks and allocate additional resources if needed"
#             })
        
#         return recommendations
    
#     def _calculate_overview_stats(self, workloads, projects_data):
#         """Calculate overview statistics"""
#         total_members = len(workloads)
#         total_projects = len(projects_data)
#         total_active_tasks = sum(w["active_tasks"] for w in workloads.values())
        
#         # Workload distribution
#         status_counts = defaultdict(int)
#         for workload in workloads.values():
#             status_counts[workload["status"]] += 1
        
#         avg_workload_score = sum(w["workload_score"] for w in workloads.values()) / total_members if total_members > 0 else 0
        
#         return {
#             "total_members": total_members,
#             "total_projects": total_projects,
#             "total_active_tasks": total_active_tasks,
#             "avg_tasks_per_member": round(total_active_tasks / total_members, 1) if total_members > 0 else 0,
#             "avg_workload_score": round(avg_workload_score, 1),
#             "workload_distribution": dict(status_counts),
#             "health_score": self._calculate_team_health_score(status_counts, total_members)
#         }
    
#     def _calculate_team_health_score(self, status_counts, total_members):
#         """Calculate overall team health score (0-100)"""
#         if total_members == 0:
#             return 0
        
#         score = 100
        
#         overloaded_ratio = status_counts.get("overloaded", 0) / total_members
#         high_ratio = status_counts.get("high", 0) / total_members
        
#         # Penalize for overloaded members
#         score -= overloaded_ratio * 50
#         score -= high_ratio * 25
        
#         return max(0, round(score))


#!/usr/bin/env python3
# """
# ClickUp Pulse Integration - Updated to use Space ID for better project organization
# """

# import requests
# import time
# from datetime import datetime, timedelta
# import json
# from collections import defaultdict

# class ClickUpPulseIntegration:
#     def __init__(self, api_token, space_id):
#         self.api_token = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
#         self.space_id = '90132462540'  # Use your space ID here
#         # self.api_token = api_token
#         # self.space_id = space_id
#         self.headers = {'Authorization': api_token}
#         self.base_url = 'https://api.clickup.com/api/v2'
        
#         # Working hours configuration
#         self.WORKDAY_START_HOUR = 9
#         self.WORKDAY_END_HOUR = 17
#         self.LUNCH_BREAK_START = 12
#         self.LUNCH_BREAK_END = 12.5
#         self.WORKING_HOURS_PER_DAY = 7.5
    
#     def generate_pulse_analytics(self, target_date=None, debug=False, status_filters=None):
#         """
#         Generate comprehensive pulse analytics from ClickUp data with status filtering
#         """
#         try:
#             # Set default status filters if none provided
#             if status_filters is None:
#                 status_filters = ['to do', 'planning', 'in progress', 'bugs']
            
#             print(f"🎯 Using status filters: {status_filters}")
            
#             print("🔍 Getting space information...")
#             space_info = self._get_space_info()
            
#             if not space_info:
#                 print("❌ Could not fetch space information!")
#                 return None
            
#             print(f"✅ Found space: {space_info.get('name', 'Unknown')}")
            
#             # Get all lists (projects) in the space
#             print("📋 Getting lists/projects...")
#             lists = self._get_space_lists()
            
#             if not lists:
#                 print("❌ No lists found in this space!")
#                 return None
            
#             print(f"✅ Found {len(lists)} lists/projects")
            
#             # Use provided date or default to today
#             if target_date:
#                 analysis_date = target_date
#             else:
#                 analysis_date = datetime.now().date()
            
#             # Check if it's a weekend
#             is_weekend = analysis_date.weekday() >= 5
            
#             if is_weekend and debug:
#                 print(f"🐛 DEBUG: {analysis_date} is a weekend day")
            
#             # Get time range for the analysis date
#             start_ts, current_ts, start_of_day, current_time = self._get_date_timestamps(analysis_date)
#             print(f"⏰ Analysis period: {analysis_date}")
            
#             # Initialize data structure
#             clickup_data = {
#                 'date': analysis_date.strftime('%Y-%m-%d'),
#                 'timestamp': datetime.now().isoformat(),
#                 'space_name': space_info.get('name', 'Unknown'),
#                 'projects_analyzed': 0,
#                 'detailed_data': {},
#                 'project_data': {},
#                 'status_filters': status_filters,  # NEW: Store applied filters
#                 'debug_info': {
#                     'is_weekend': is_weekend,
#                     'total_lists': len(lists),
#                     'analysis_date': str(analysis_date),
#                     'status_filters_applied': status_filters
#                 } if debug else {}
#             }
            
#             # Analyze each list/project
#             for list_info in lists:
#                 list_id = list_info.get('id')
#                 list_name = list_info.get('name', 'Unknown Project')
                
#                 print(f"\n📋 Analyzing project: {list_name}")
                
#                 # Get tasks for this list with status filtering
#                 tasks = self._get_list_tasks(list_id, debug, status_filters)  # NEW: Pass filters
                
#                 # Filter tasks by status
#                 filtered_tasks = self._filter_tasks_by_status(tasks, status_filters)
                
#                 print(f"   📝 Found {len(tasks)} total tasks, {len(filtered_tasks)} matching status filters")
                
#                 if filtered_tasks:
#                     # Group tasks by assignee
#                     tasks_by_member = self._group_tasks_by_assignee(filtered_tasks)
                    
#                     # Store project data
#                     clickup_data['project_data'][list_name] = {
#                         'list_id': list_id,
#                         'list_name': list_name,
#                         'total_tasks': len(filtered_tasks),
#                         'tasks_by_member': tasks_by_member,
#                         'task_details': filtered_tasks
#                     }
                    
#                     # Analyze each member's tasks in this project
#                     for member_name, member_tasks in tasks_by_member.items():
#                         if member_name not in clickup_data['detailed_data']:
#                             clickup_data['detailed_data'][member_name] = {
#                                 'task_periods': [],
#                                 'downtime_periods': [],
#                                 'task_details': [],
#                                 'projects': []
#                             }
                        
#                         # Analyze activity for this member's tasks in this project
#                         task_periods, downtime_periods, task_details = self._analyze_task_activity(
#                             member_tasks, start_ts, current_ts, start_of_day, current_time, debug
#                         )
                        
#                         # Add to member's data
#                         clickup_data['detailed_data'][member_name]['task_periods'].extend(task_periods)
#                         clickup_data['detailed_data'][member_name]['downtime_periods'].extend(downtime_periods)
#                         clickup_data['detailed_data'][member_name]['task_details'].extend(task_details)
#                         clickup_data['detailed_data'][member_name]['projects'].append({
#                             'name': list_name,
#                             'task_count': len(member_tasks)
#                         })
                
#                 clickup_data['projects_analyzed'] += 1
#                 time.sleep(0.5)  # Rate limiting
            
#             print(f"\n✅ Analysis complete - {clickup_data['projects_analyzed']} projects analyzed")
#             print(f"🎯 Status filters applied: {status_filters}")
            
#             if clickup_data['projects_analyzed'] == 0:
#                 print("❌ No projects were analyzed!")
#                 return None
            
#             # Transform to Pulse format
#             pulse_data = self._transform_to_pulse_format(clickup_data)
            
#             return pulse_data
            
#         except Exception as e:
#             print(f"❌ Error generating pulse analytics: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _get_space_info(self):
#         """Get space information"""
#         try:
#             resp = requests.get(f"{self.base_url}/space/{self.space_id}", headers=self.headers)
#             resp.raise_for_status()
#             return resp.json()
#         except Exception as e:
#             print(f"Error getting space info: {e}")
#             return None
    
#     def _get_space_lists(self):
#         """Get all lists in the space"""
#         try:
#             resp = requests.get(f"{self.base_url}/space/{self.space_id}/list", headers=self.headers)
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('lists', [])
#         except Exception as e:
#             print(f"Error getting space lists: {e}")
#             return []
    
#     def _get_list_tasks(self, list_id, debug=False, status_filters=None):
#         """Get all tasks for a specific list"""
#         try:
#             # Get all tasks (not filtering by status at API level since ClickUp API doesn't support multiple status filters)
#             url = f"{self.base_url}/list/{list_id}/task?include_closed=false"
            
#             if debug:
#                 print(f"🐛 DEBUG: API URL: {url}")
            
#             resp = requests.get(url, headers=self.headers)
#             resp.raise_for_status()
#             data = resp.json()
            
#             return data.get('tasks', [])
            
#         except Exception as e:
#             print(f"Error getting list tasks: {e}")
#             return []
    
#     def _filter_tasks_by_status(self, tasks, status_filters):
#         """
#         Filter tasks by status on the client side
#         """
#         if not status_filters:
#             return tasks
        
#         # Normalize status filters for comparison
#         normalized_filters = [status.lower().strip() for status in status_filters]
        
#         filtered_tasks = []
#         for task in tasks:
#             task_status = task.get('status', {}).get('status', '').lower().strip()
            
#             if task_status in normalized_filters:
#                 filtered_tasks.append(task)
        
#         return filtered_tasks

#     def _group_tasks_by_assignee(self, tasks):
#         """Group tasks by assignee"""
#         tasks_by_member = defaultdict(list)
        
#         for task in tasks:
#             assignees = task.get('assignees', [])
            
#             if not assignees:
#                 # Unassigned task
#                 tasks_by_member['Unassigned'].append(task)
#             else:
#                 for assignee in assignees:
#                     username = assignee.get('username', 'Unknown')
#                     tasks_by_member[username].append(task)
        
#         return dict(tasks_by_member)
    
#     def _get_date_timestamps(self, target_date):
#         """Get start and end timestamps for a specific date"""
#         if isinstance(target_date, str):
#             target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
#         # Create datetime objects for the target date
#         start_of_day = datetime.combine(target_date, datetime.min.time())
        
#         # If analyzing today, use current time; otherwise use end of day
#         if target_date == datetime.now().date():
#             current_time = datetime.now()
#         else:
#             current_time = datetime.combine(target_date, datetime.max.time().replace(microsecond=0))
        
#         # Convert to ClickUp timestamps (milliseconds)
#         start_ts = int(start_of_day.timestamp() * 1000)
#         current_ts = int(current_time.timestamp() * 1000)
        
#         return start_ts, current_ts, start_of_day, current_time
    
#     def _analyze_task_activity(self, tasks, start_ts, current_ts, start_of_day, current_time, debug=False):
#         """Analyze task activity and identify downtime periods"""
#         task_periods = []
#         downtime_periods = []
#         task_details = []
        
#         # Working hours boundaries for the analysis date
#         analysis_date = start_of_day.date()
#         work_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_START_HOUR))
#         work_end = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_END_HOUR))
        
#         # Track task activities
#         activities = []
        
#         for task in tasks:
#             try:
#                 # Get task details
#                 task_name = task.get('name', 'Unknown Task')
#                 task_id = task.get('id', 'unknown')
#                 task_status = task.get('status', {}).get('status', 'unknown')
#                 priority = task.get('priority')
#                 due_date = task.get('due_date')
                
#                 # Get the list/project name from task
#                 list_info = task.get('list', {})
#                 project_name = list_info.get('name', 'Unknown Project')
                
#                 # Store task details for dashboard
#                 task_details.append({
#                     'name': task_name,
#                     'id': task_id,
#                     'status': task_status,
#                     'due_date': due_date,
#                     'priority': priority,
#                     'project_name': project_name,  # Now we have the actual project name!
#                     'list_id': list_info.get('id')
#                 })
                
#                 # Check for recent activity
#                 date_updated = task.get('date_updated')
#                 if date_updated:
#                     updated_time = datetime.fromtimestamp(int(date_updated) / 1000)
                    
#                     # Check if activity is on the analysis date and within working hours
#                     if (updated_time.date() == analysis_date and
#                         work_start <= updated_time <= work_end):
                        
#                         activities.append({
#                             'time': updated_time,
#                             'task_name': task_name,
#                             'task_id': task_id,
#                             'project_name': project_name,
#                             'type': 'update'
#                         })
                
#             except Exception as e:
#                 print(f"    Error processing task {task.get('id', 'unknown')}: {e}")
        
#         # Sort activities by time
#         activities.sort(key=lambda x: x['time'])
        
#         print(f"    Found {len(activities)} activities in working hours")
        
#         # Create task periods from activities or estimate from task details
#         if not activities and task_details:
#             # Create estimated periods for open tasks
#             current_work_time = work_start
#             for i, task in enumerate(task_details[:3]):  # Limit to first 3 tasks
#                 if current_work_time >= work_end:
#                     break
                
#                 # Estimate 2-hour periods for tasks
#                 period_duration = 2.0
#                 period_end = min(current_work_time + timedelta(hours=period_duration), work_end)
                
#                 task_periods.append({
#                     'start': current_work_time.isoformat(),
#                     'end': period_end.isoformat(),
#                     'task_name': task['name'],
#                     'task_id': task['id'],
#                     'project_name': task['project_name'],  # Include project name
#                     'duration_hours': round((period_end - current_work_time).total_seconds() / 3600, 2),
#                     'status': 'estimated'
#                 })
                
#                 current_work_time = period_end + timedelta(hours=0.5)
#         else:
#             # Create task periods from actual activities
#             for i, activity in enumerate(activities):
#                 start_time = activity['time']
                
#                 # Estimate task duration
#                 if i < len(activities) - 1:
#                     next_time = activities[i + 1]['time']
#                     duration = min((next_time - start_time).total_seconds() / 3600, 2.0)
#                 else:
#                     duration = 1.0
                
#                 end_time = start_time + timedelta(hours=duration)
                
#                 if end_time > work_end:
#                     end_time = work_end
#                     duration = (end_time - start_time).total_seconds() / 3600
                
#                 if duration > 0:
#                     task_periods.append({
#                         'start': start_time.isoformat(),
#                         'end': end_time.isoformat(),
#                         'task_name': activity['task_name'],
#                         'task_id': activity['task_id'],
#                         'project_name': activity['project_name'],  # Include project name
#                         'duration_hours': round(duration, 2),
#                         'status': 'active'
#                     })
        
#         return task_periods, downtime_periods, task_details
    
#     def _transform_to_pulse_format(self, clickup_data):
#         """Transform ClickUp data to Pulse dashboard format with enhanced error handling"""
#         try:
#             member_workloads = {}
#             project_analytics = {}
            
#             print("🔄 Starting transform to pulse format...")
            
#             # Debug: Check the structure of clickup_data
#             print(f"🐛 DEBUG: clickup_data keys: {list(clickup_data.keys())}")
#             print(f"🐛 DEBUG: project_data type: {type(clickup_data.get('project_data', {}))}")
#             print(f"🐛 DEBUG: detailed_data type: {type(clickup_data.get('detailed_data', {}))}")
            
#             # Process project data first - with error handling
#             project_data = clickup_data.get('project_data', {})
#             if isinstance(project_data, dict):
#                 for project_name, project_info in project_data.items():
#                     try:
#                         print(f"🔄 Processing project: {project_name}")
#                         print(f"🐛 DEBUG: project_info type: {type(project_info)}")
                        
#                         # Ensure project_info is a dictionary
#                         if not isinstance(project_info, dict):
#                             print(f"⚠️ WARNING: project_info for {project_name} is not a dict: {type(project_info)}")
#                             continue
                        
#                         # Safely extract project data
#                         list_id = project_info.get('list_id', 'unknown')
#                         total_tasks = project_info.get('total_tasks', 0)
#                         tasks_by_member = project_info.get('tasks_by_member', {})
                        
#                         # Ensure tasks_by_member is a dictionary
#                         if not isinstance(tasks_by_member, dict):
#                             print(f"⚠️ WARNING: tasks_by_member for {project_name} is not a dict: {type(tasks_by_member)}")
#                             tasks_by_member = {}
                        
#                         project_analytics[project_name] = {
#                             "name": project_name,
#                             "list_id": list_id,
#                             "active_tasks": total_tasks,
#                             "assigned_members": list(tasks_by_member.keys()),
#                             "member_count": len(tasks_by_member),
#                             "tasks_by_member": tasks_by_member,
#                             "status": "active",
#                             "priority": "medium"
#                         }
#                         print(f"✅ Successfully processed project: {project_name}")
                        
#                     except Exception as e:
#                         print(f"❌ Error processing project {project_name}: {e}")
#                         print(f"🐛 DEBUG: project_info content: {project_info}")
#                         continue
#             else:
#                 print(f"⚠️ WARNING: project_data is not a dictionary: {type(project_data)}")
            
#             # Process each member's data - with error handling
#             detailed_data = clickup_data.get('detailed_data', {})
#             if isinstance(detailed_data, dict):
#                 for username, member_data in detailed_data.items():
#                     try:
#                         print(f"🔄 Processing member: {username}")
#                         print(f"🐛 DEBUG: member_data type: {type(member_data)}")
                        
#                         # Ensure member_data is a dictionary
#                         if not isinstance(member_data, dict):
#                             print(f"⚠️ WARNING: member_data for {username} is not a dict: {type(member_data)}")
#                             continue
                        
#                         workload = self._calculate_member_workload(username, member_data)
#                         member_workloads[username] = workload
#                         print(f"✅ Successfully processed member: {username}")
                        
#                     except Exception as e:
#                         print(f"❌ Error processing member {username}: {e}")
#                         print(f"🐛 DEBUG: member_data content: {member_data}")
#                         continue
#             else:
#                 print(f"⚠️ WARNING: detailed_data is not a dictionary: {type(detailed_data)}")
            
#             print(f"✅ Processed {len(member_workloads)} members and {len(project_analytics)} projects")
            
#             # Generate additional analytics with error handling
#             try:
#                 timeline_analysis = self._analyze_timeline(clickup_data)
#             except Exception as e:
#                 print(f"❌ Error in timeline analysis: {e}")
#                 timeline_analysis = {
#                     "urgent_deadlines": [],
#                     "upcoming_deadlines": [],
#                     "overdue_tasks": [],
#                     "high_priority_tasks": [],
#                     "deadline_pressure_by_member": {}
#                 }
            
#             try:
#                 load_balance_insights = self._generate_load_balance_insights(member_workloads, timeline_analysis)
#             except Exception as e:
#                 print(f"❌ Error in load balance insights: {e}")
#                 load_balance_insights = {
#                     "highest_workload": None,
#                     "lowest_workload": None,
#                     "overloaded_members": [],
#                     "available_members": [],
#                     "transfer_suggestions": []
#                 }
            
#             try:
#                 recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
#             except Exception as e:
#                 print(f"❌ Error in recommendations: {e}")
#                 recommendations = []
            
#             try:
#                 overview_stats = self._calculate_overview_stats(member_workloads, project_analytics)
#             except Exception as e:
#                 print(f"❌ Error in overview stats: {e}")
#                 overview_stats = {
#                     "total_members": len(member_workloads),
#                     "total_projects": len(project_analytics),
#                     "total_active_tasks": 0,
#                     "avg_tasks_per_member": 0,
#                     "avg_workload_score": 0,
#                     "health_score": 50
#                 }
            
#             final_data = {
#                 "member_workloads": member_workloads,
#                 "project_analytics": project_analytics,
#                 "timeline_analysis": timeline_analysis,
#                 "load_balance_insights": load_balance_insights,
#                 "recommendations": recommendations,
#                 "overview_stats": overview_stats,
#                 "last_updated": datetime.now().isoformat(),
#                 "data_source": "clickup_space",
#                 "analysis_date": clickup_data.get('date', 'unknown'),
#                 "space_name": clickup_data.get('space_name', 'Unknown'),
#                 "status_filters": clickup_data.get('status_filters', [])
#             }
            
#             print("✅ Transform to pulse format completed successfully")
#             return final_data
            
#         except Exception as e:
#             print(f"❌ Critical error in transform to pulse format: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
        
  
#     def _calculate_member_workload(self, username, member_data):
#         """Calculate workload for a single member with enhanced error handling"""
#         try:
#             print(f"🔄 Calculating workload for {username}")
            
#             # Safely get task details
#             task_details = member_data.get('task_details', [])
#             if not isinstance(task_details, list):
#                 print(f"⚠️ WARNING: task_details for {username} is not a list: {type(task_details)}")
#                 task_details = []
            
#             all_tasks = task_details
#             active_tasks_count = len(all_tasks)
            
#             print(f"🐛 DEBUG: {username} has {active_tasks_count} tasks")
            
#             urgent_tasks = 0
#             high_priority_tasks = 0
#             due_soon_tasks = 0
            
#             # Process each task with error handling
#             for i, task in enumerate(all_tasks):
#                 try:
#                     if not isinstance(task, dict):
#                         print(f"⚠️ WARNING: Task {i} for {username} is not a dict: {type(task)}")
#                         continue
                    
#                     # Safely handle priority
#                     priority = task.get('priority', {})
#                     if priority is None:
#                         priority_level = 'medium'
#                     elif isinstance(priority, dict):
#                         priority_level = priority.get('priority', 'medium')
#                     elif isinstance(priority, str):
#                         priority_level = priority
#                     else:
#                         priority_level = str(priority) if priority else 'medium'
                    
#                     if priority_level == 'urgent':
#                         urgent_tasks += 1
#                     elif priority_level == 'high':
#                         high_priority_tasks += 1
                    
#                     # Safely handle due date
#                     due_date = task.get('due_date')
#                     if due_date:
#                         try:
#                             if isinstance(due_date, str) and due_date.isdigit():
#                                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                             elif isinstance(due_date, (int, float)):
#                                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                             else:
#                                 continue  # Skip invalid due dates
                            
#                             days_until_due = (due_datetime - datetime.now()).days
#                             if days_until_due <= 2:
#                                 due_soon_tasks += 1
#                         except (ValueError, TypeError, OSError) as e:
#                             print(f"⚠️ WARNING: Invalid due_date for task: {due_date}")
#                             continue
                            
#                 except Exception as e:
#                     print(f"❌ Error processing task {i} for {username}: {e}")
#                     continue
            
#             # Safely get projects
#             projects_list = member_data.get('projects', [])
#             if not isinstance(projects_list, list):
#                 print(f"⚠️ WARNING: projects for {username} is not a list: {type(projects_list)}")
#                 projects_list = []
            
#             # Safely calculate time estimate
#             task_periods = member_data.get('task_periods', [])
#             if not isinstance(task_periods, list):
#                 print(f"⚠️ WARNING: task_periods for {username} is not a list: {type(task_periods)}")
#                 task_periods = []
            
#             total_time_estimate = 0
#             for period in task_periods:
#                 if isinstance(period, dict):
#                     duration = period.get('duration_hours', 0)
#                     if isinstance(duration, (int, float)):
#                         total_time_estimate += duration * 60
            
#             # Calculate workload score
#             workload_score = self._calculate_workload_score({
#                 "active_tasks": active_tasks_count,
#                 "urgent_tasks": urgent_tasks,
#                 "high_priority_tasks": high_priority_tasks,
#                 "due_soon_tasks": due_soon_tasks,
#                 "projects_count": len(projects_list),
#                 "remaining_time": total_time_estimate
#             })
            
#             # Get task breakdown
#             task_breakdown = self._get_task_breakdown(all_tasks)
            
#             result = {
#                 "username": username,
#                 "active_tasks": active_tasks_count,
#                 "projects_count": len(projects_list),
#                 "projects": projects_list,
#                 "tasks": all_tasks,
#                 "urgent_tasks": urgent_tasks,
#                 "high_priority_tasks": high_priority_tasks,
#                 "due_soon_tasks": due_soon_tasks,
#                 "workload_score": workload_score,
#                 "status": self._determine_workload_status(workload_score),
#                 "remaining_time": total_time_estimate,
#                 "task_breakdown": task_breakdown
#             }
            
#             print(f"✅ Workload calculated for {username}: {active_tasks_count} tasks, score: {workload_score}")
#             return result
            
#         except Exception as e:
#             print(f"❌ Error calculating workload for {username}: {e}")
#             import traceback
#             traceback.print_exc()
            
#             # Return a safe default
#             return {
#                 "username": username,
#                 "active_tasks": 0,
#                 "projects_count": 0,
#                 "projects": [],
#                 "tasks": [],
#                 "urgent_tasks": 0,
#                 "high_priority_tasks": 0,
#                 "due_soon_tasks": 0,
#                 "workload_score": 0,
#                 "status": "light",
#                 "remaining_time": 0,
#                 "task_breakdown": {}
#             }

#     def _get_task_breakdown(self, tasks):
#         """Get breakdown of tasks by status with error handling"""
#         try:
#             breakdown = {
#                 "in_progress": 0,
#                 "to_do": 0,
#                 "bugs": 0,
#                 "planning": 0,
#                 "for_qa": 0,
#                 "for_viewing": 0,
#                 "grammar": 0
#             }
            
#             if not isinstance(tasks, list):
#                 return breakdown
            
#             for task in tasks:
#                 try:
#                     if not isinstance(task, dict):
#                         continue
                    
#                     # Safely get status
#                     status_obj = task.get('status', {})
#                     if isinstance(status_obj, dict):
#                         status = status_obj.get('status', '').lower().strip()
#                     elif isinstance(status_obj, str):
#                         status = status_obj.lower().strip()
#                     else:
#                         continue
                    
#                     if status in breakdown:
#                         breakdown[status] += 1
                        
#                 except Exception as e:
#                     print(f"⚠️ Warning: Error processing task status: {e}")
#                     continue
            
#             return breakdown
            
#         except Exception as e:
#             print(f"❌ Error in get_task_breakdown: {e}")
#             return {
#                 "in_progress": 0,
#                 "to_do": 0,
#                 "bugs": 0,
#                 "planning": 0,
#                 "for_qa": 0,
#                 "for_viewing": 0,
#                 "grammar": 0
#             }
        
#     def _calculate_workload_score(self, workload):
#         """Calculate workload score based on multiple factors"""
#         score = 0
#         score += workload.get("active_tasks", 0) * 10
#         score += workload.get("urgent_tasks", 0) * 25
#         score += workload.get("high_priority_tasks", 0) * 15
#         score += workload.get("due_soon_tasks", 0) * 20
#         remaining_hours = workload.get("remaining_time", 0) / 60
#         score += remaining_hours * 2
#         score += workload.get("projects_count", 0) * 5
#         return round(score, 1)
    
#     def _determine_workload_status(self, score):
#         """Determine workload status based on score"""
#         if score >= 150:
#             return "overloaded"
#         elif score >= 100:
#             return "high"
#         elif score >= 50:
#             return "balanced" 
#         else:
#             return "light"
    
#     def _update_project_analytics(self, project_analytics, member_data, username):  
#         """Update project analytics with member data"""
#         # This is simplified - in reality you'd group by actual project IDs
#         for task in member_data.get('task_details', []):
#             project_name = f"Project {task.get('status', 'unknown').title()}"
            
#             if project_name not in project_analytics:
#                 project_analytics[project_name] = {
#                     "name": project_name,
#                     "active_tasks": 0,
#                     "assigned_members": set(),
#                     "total_time_estimate": 0,
#                     "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
#                     "priority": "medium",
#                     "status": "active"
#                 }
            
#             project_analytics[project_name]["active_tasks"] += 1
#             project_analytics[project_name]["assigned_members"].add(username)
        
#         # Convert sets to lists for JSON serialization
#         for project_id, project in project_analytics.items():
#             if isinstance(project["assigned_members"], set):
#                 project["assigned_members"] = list(project["assigned_members"])
#                 project["member_count"] = len(project["assigned_members"])
    
#     def _analyze_timeline(self, clickup_data):
#         """Analyze timeline and deadlines"""
#         analysis = {
#             "urgent_deadlines": [],
#             "upcoming_deadlines": [],
#             "overdue_tasks": [],
#             "high_priority_tasks": [],
#             "deadline_pressure_by_member": defaultdict(int)
#         }
        
#         for username, member_data in clickup_data['detailed_data'].items():
#             for task in member_data.get('task_details', []):
#                 # Priority analysis
#                 priority = task.get('priority', {})
#                 if isinstance(priority, dict):
#                     priority_level = priority.get('priority', 'medium')
#                 else:
#                     priority_level = str(priority) if priority else 'medium'
                
#                 if priority_level in ["urgent", "high"]:
#                     analysis["high_priority_tasks"].append(task)
                
#                 # Deadline analysis
#                 due_date = task.get('due_date')
#                 if due_date:
#                     try:
#                         due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                         days_until_due = (due_datetime - datetime.now()).days
                        
#                         if days_until_due < 0:
#                             analysis["overdue_tasks"].append(task)
#                         elif days_until_due <= 1:
#                             analysis["urgent_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 3
#                         elif days_until_due <= 7:
#                             analysis["upcoming_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 1
#                     except:
#                         pass
        
#         # Convert defaultdict to regular dict
#         analysis["deadline_pressure_by_member"] = dict(analysis["deadline_pressure_by_member"])
        
#         return analysis
    
#     def _generate_load_balance_insights(self, workloads, timeline_analysis):
#         """Generate load balancing insights with transfer suggestions"""
#         insights = {
#             "highest_workload": None,
#             "lowest_workload": None,
#             "overloaded_members": [],
#             "available_members": [],
#             "transfer_suggestions": []
#         }
        
#         if not workloads:
#             return insights
        
#         # Find highest and lowest workload
#         sorted_workloads = sorted(workloads.items(), key=lambda x: x[1]["workload_score"], reverse=True)
        
#         if sorted_workloads:
#             insights["highest_workload"] = {
#                 "username": sorted_workloads[0][0],
#                 "score": sorted_workloads[0][1]["workload_score"],
#                 "status": sorted_workloads[0][1]["status"],
#                 "details": sorted_workloads[0][1]
#             }
            
#             insights["lowest_workload"] = {
#                 "username": sorted_workloads[-1][0],
#                 "score": sorted_workloads[-1][1]["workload_score"],
#                 "status": sorted_workloads[-1][1]["status"],
#                 "details": sorted_workloads[-1][1]
#             }
        
#         # Identify overloaded and available members
#         overloaded_members = []
#         available_members = []
        
#         for username, workload in workloads.items():
#             if workload["status"] in ["overloaded", "high"]:
#                 overloaded_members.append({
#                     "username": username,
#                     "workload": workload
#                 })
#             elif workload["status"] == "light":
#                 available_members.append({
#                     "username": username,
#                     "workload": workload
#                 })
        
#         insights["overloaded_members"] = overloaded_members
#         insights["available_members"] = available_members
        
#         # Generate transfer suggestions
#         insights["transfer_suggestions"] = self._generate_transfer_suggestions(
#             overloaded_members, available_members, workloads
#         )
        
#         return insights

#     def _generate_transfer_suggestions(self, overloaded_members, available_members, all_workloads):
#         """
#         Generate specific task transfer suggestions between team members
#         """
#         suggestions = []
        
#         if not overloaded_members or not available_members:
#             return suggestions
        
#         # Sort overloaded by severity, available by capacity
#         overloaded_sorted = sorted(
#             overloaded_members, 
#             key=lambda x: x["workload"]["workload_score"], 
#             reverse=True
#         )
        
#         available_sorted = sorted(
#             available_members, 
#             key=lambda x: x["workload"]["workload_score"]
#         )
        
#         for overloaded_member in overloaded_sorted[:3]:  # Top 3 overloaded
#             overloaded_username = overloaded_member["username"]
#             overloaded_workload = overloaded_member["workload"]
            
#             # Get transferable tasks (non-urgent, not due soon)
#             transferable_tasks = self._get_transferable_tasks(overloaded_workload)
            
#             if not transferable_tasks:
#                 continue
                
#             for available_member in available_sorted[:2]:  # Top 2 available
#                 available_username = available_member["username"]
#                 available_workload = available_member["workload"]
                
#                 # Check if this member can take more work
#                 if available_workload["workload_score"] >= 80:  # Don't overload available members
#                     continue
                
#                 # Find best task to transfer
#                 best_task = self._find_best_transfer_task(
#                     transferable_tasks, 
#                     overloaded_workload, 
#                     available_workload
#                 )
                
#                 if best_task:
#                     # Calculate impact
#                     score_reduction = self._estimate_score_reduction(best_task, overloaded_workload)
#                     score_increase = self._estimate_score_increase(best_task, available_workload)
                    
#                     # Only suggest if it significantly helps and doesn't hurt too much
#                     if score_reduction >= 15 and score_increase <= 25:
#                         suggestion = {
#                             "from_member": overloaded_username,
#                             "to_member": available_username,
#                             "task": {
#                                 "id": best_task["id"],
#                                 "name": best_task["name"],
#                                 "project_name": best_task.get("project_name", "Unknown"),
#                                 "status": best_task["status"],
#                                 "priority": best_task.get("priority", {}).get("priority", "normal") if best_task.get("priority") else "normal"
#                             },
#                             "reason": self._generate_transfer_reason(
#                                 overloaded_username, 
#                                 available_username, 
#                                 best_task, 
#                                 score_reduction, 
#                                 score_increase
#                             ),
#                             "impact": {
#                                 "from_score_reduction": score_reduction,
#                                 "to_score_increase": score_increase,
#                                 "net_improvement": score_reduction - score_increase
#                             }
#                         }
                        
#                         suggestions.append(suggestion)
                        
#                         # Remove this task from transferable list to avoid duplicate suggestions
#                         transferable_tasks.remove(best_task)
                        
#                         # Limit suggestions per overloaded member
#                         if len([s for s in suggestions if s["from_member"] == overloaded_username]) >= 2:
#                             break
        
#         # Sort suggestions by net improvement (highest impact first)
#         suggestions.sort(key=lambda x: x["impact"]["net_improvement"], reverse=True)
        
#         # Return top 5 suggestions
#         return suggestions[:5]

#     def _estimate_score_increase(self, task, to_workload):
#         """
#         Estimate how much the workload score would increase by receiving this task
#         """
#         base_increase = 10  # Base increase for any task
        
#         # Add increase based on priority
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         if priority_level == "high":
#             base_increase += 15
#         elif priority_level == "normal":
#             base_increase += 10
#         elif priority_level == "low":
#             base_increase += 5
        
#         # Reduce increase if member is already on the project
#         task_project = task.get("project_name", "")
#         to_member_projects = [p.get("name", "") for p in to_workload.get("projects", [])]
        
#         if task_project in to_member_projects:
#             base_increase -= 5  # Easier to take on task in familiar project
        
#         return base_increase


#     def _estimate_score_reduction(self, task, from_workload):
#         """
#         Estimate how much the workload score would reduce by transferring this task
#         """
#         base_reduction = 10  # Base reduction for any task
        
#         # Add reduction based on priority
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         if priority_level == "high":
#             base_reduction += 15
#         elif priority_level == "normal":
#             base_reduction += 10
#         elif priority_level == "low":
#             base_reduction += 5
        
#         # Add reduction based on due date pressure
#         due_date = task.get("due_date")
#         if due_date:
#             try:
#                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                 days_until_due = (due_datetime - datetime.now()).days
#                 if days_until_due <= 7:
#                     base_reduction += 20
#                 elif days_until_due <= 14:
#                     base_reduction += 10
#             except:
#                 pass
        
#         return base_reduction

#     def _find_best_transfer_task(self, transferable_tasks, from_workload, to_workload):
#         """
#         Find the best task to transfer based on multiple criteria
#         """
#         if not transferable_tasks:
#             return None
        
#         # Score each task for transfer suitability
#         scored_tasks = []
        
#         for task in transferable_tasks:
#             score = 0
            
#             # Prefer tasks that are not started yet
#             if task.get("status") == "to do":
#                 score += 20
#             elif task.get("status") == "planning":
#                 score += 15
#             elif task.get("status") == "in progress":
#                 score += 5  # Less preferred
            
#             # Prefer normal priority tasks
#             priority = task.get("priority", {})
#             if isinstance(priority, dict):
#                 priority_level = priority.get("priority", "normal")
#             else:
#                 priority_level = str(priority) if priority else "normal"
            
#             if priority_level == "normal":
#                 score += 15
#             elif priority_level == "low":
#                 score += 10
#             elif priority_level == "high":
#                 score += 5  # Can transfer but less preferred
            
#             # Prefer tasks with longer deadlines
#             due_date = task.get("due_date")
#             if due_date:
#                 try:
#                     due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                     days_until_due = (due_datetime - datetime.now()).days
#                     if days_until_due > 14:
#                         score += 15
#                     elif days_until_due > 7:
#                         score += 10
#                     elif days_until_due > 3:
#                         score += 5
#                 except:
#                     score += 10  # No penalty for invalid dates
#             else:
#                 score += 10  # No deadline is good for transfer
            
#             # Check if the receiving member is already on this project
#             task_project = task.get("project_name", "")
#             to_member_projects = [p.get("name", "") for p in to_workload.get("projects", [])]
            
#             if task_project in to_member_projects:
#                 score += 25  # Big bonus for same project
            
#             scored_tasks.append((task, score))
        
#         # Return the highest scored task
#         if scored_tasks:
#             scored_tasks.sort(key=lambda x: x[1], reverse=True)
#             return scored_tasks[0][0]
        
#         return None

#     def _generate_transfer_reason(self, from_member, to_member, task, score_reduction, score_increase):
#         """
#         Generate a human-readable reason for the transfer suggestion
#         """
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         # Base reason
#         reason = f"Transfer '{task['name']}' to help reduce {from_member}'s workload"
        
#         # Add specific reasons
#         reasons = []
        
#         if score_reduction >= 20:
#             reasons.append("high impact task")
        
#         if priority_level == "normal" or priority_level == "low":
#             reasons.append("non-critical priority")
        
#         if task.get("status") in ["to do", "planning"]:
#             reasons.append("not yet started")
        
#         # Check project familiarity
#         task_project = task.get("project_name", "")
#         if task_project:
#             reasons.append(f"within {task_project} project")
        
#         if score_increase <= 15:
#             reasons.append(f"minimal impact on {to_member}")
        
#         if reasons:
#             reason += f" ({', '.join(reasons)})"
        
#         # Add impact summary
#         net_improvement = score_reduction - score_increase
#         reason += f". Net workload improvement: {net_improvement} points."
        
#         return reason

#     def _get_transferable_tasks(self, workload):
#         """
#         Get tasks that can be safely transferred (not urgent or due soon)
#         """
#         transferable = []
        
#         for task in workload.get("tasks", []):
#             # Skip urgent tasks
#             priority = task.get("priority", {})
#             if isinstance(priority, dict):
#                 priority_level = priority.get("priority", "normal")
#             else:
#                 priority_level = str(priority) if priority else "normal"
            
#             if priority_level == "urgent":
#                 continue
            
#             # Skip tasks due soon
#             due_date = task.get("due_date")
#             if due_date:
#                 try:
#                     due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                     days_until_due = (due_datetime - datetime.now()).days
#                     if days_until_due <= 3:  # Due within 3 days
#                         continue
#                 except:
#                     pass
            
#             # Skip tasks in final stages
#             if task.get("status") in ["review", "testing", "staging"]:
#                 continue
            
#             # Only transfer tasks that are in early stages
#             if task.get("status") in ["to do", "planning", "in progress"]:
#                 transferable.append(task)
        
#         return transferable

        
#     def _generate_recommendations(self, workloads, timeline_analysis):
#         """Generate recommendations based on workload analysis"""
#         recommendations = []
        
#         # Check for overloaded members
#         overloaded = [w for w in workloads.values() if w["status"] in ["overloaded", "high"]]
#         if overloaded:
#             for member in overloaded:
#                 recommendations.append({
#                     "type": "workload_warning",
#                     "priority": "high",
#                     "member": member["username"],
#                     "message": f"{member['username']} has {member['status']} workload with {member['active_tasks']} active tasks across {member['projects_count']} projects",
#                     "action": "Consider redistributing tasks or extending deadlines"
#                 })
        
#         # Check for urgent deadlines
#         if timeline_analysis["urgent_deadlines"]:
#             recommendations.append({
#                 "type": "deadline_alert",
#                 "priority": "urgent",
#                 "message": f"{len(timeline_analysis['urgent_deadlines'])} tasks due within 24 hours",
#                 "action": "Review urgent tasks and allocate additional resources if needed"
#             })
        
#         return recommendations
    
#     def _calculate_overview_stats(self, workloads, projects_data):
#         """Calculate overview statistics"""
#         total_members = len(workloads)
#         total_projects = len(projects_data)
#         total_active_tasks = sum(w["active_tasks"] for w in workloads.values())
        
#         # Workload distribution
#         status_counts = defaultdict(int)
#         for workload in workloads.values():
#             status_counts[workload["status"]] += 1
        
#         avg_workload_score = sum(w["workload_score"] for w in workloads.values()) / total_members if total_members > 0 else 0
        
#         return {
#             "total_members": total_members,
#             "total_projects": total_projects,
#             "total_active_tasks": total_active_tasks,
#             "avg_tasks_per_member": round(total_active_tasks / total_members, 1) if total_members > 0 else 0,
#             "avg_workload_score": round(avg_workload_score, 1),
#             "workload_distribution": dict(status_counts),
#             "health_score": self._calculate_team_health_score(status_counts, total_members)
#         }
    
#     def _calculate_team_health_score(self, status_counts, total_members):
#         """Calculate overall team health score (0-100)"""
#         if total_members == 0:
#             return 0
        
#         score = 100
        
#         overloaded_ratio = status_counts.get("overloaded", 0) / total_members
#         high_ratio = status_counts.get("high", 0) / total_members
        
#         # Penalize for overloaded members
#         score -= overloaded_ratio * 50
#         score -= high_ratio * 25
        
#         return max(0, round(score))# """
# ClickUp Pulse Integration - Updated to use Space ID for better project organization
# """

# import requests
# import time
# from datetime import datetime, timedelta
# import json
# from collections import defaultdict

# class ClickUpPulseIntegration:
#     def __init__(self, api_token, space_id):
#         self.api_token = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
#         self.space_id = '90132462540'  # Use your space ID here
#         # self.api_token = api_token
#         # self.space_id = space_id
#         self.headers = {'Authorization': api_token}
#         self.base_url = 'https://api.clickup.com/api/v2'
        
#         # Working hours configuration
#         self.WORKDAY_START_HOUR = 9
#         self.WORKDAY_END_HOUR = 17
#         self.LUNCH_BREAK_START = 12
#         self.LUNCH_BREAK_END = 12.5
#         self.WORKING_HOURS_PER_DAY = 7.5
    
#     def generate_pulse_analytics(self, target_date=None, debug=False, status_filters=None):
#         """
#         Generate comprehensive pulse analytics from ClickUp data with status filtering
#         """
#         try:
#             # Set default status filters if none provided
#             if status_filters is None:
#                 status_filters = ['to do', 'planning', 'in progress', 'bugs']
            
#             print(f"🎯 Using status filters: {status_filters}")
            
#             print("🔍 Getting space information...")
#             space_info = self._get_space_info()
            
#             if not space_info:
#                 print("❌ Could not fetch space information!")
#                 return None
            
#             print(f"✅ Found space: {space_info.get('name', 'Unknown')}")
            
#             # Get all lists (projects) in the space
#             print("📋 Getting lists/projects...")
#             lists = self._get_space_lists()
            
#             if not lists:
#                 print("❌ No lists found in this space!")
#                 return None
            
#             print(f"✅ Found {len(lists)} lists/projects")
            
#             # Use provided date or default to today
#             if target_date:
#                 analysis_date = target_date
#             else:
#                 analysis_date = datetime.now().date()
            
#             # Check if it's a weekend
#             is_weekend = analysis_date.weekday() >= 5
            
#             if is_weekend and debug:
#                 print(f"🐛 DEBUG: {analysis_date} is a weekend day")
            
#             # Get time range for the analysis date
#             start_ts, current_ts, start_of_day, current_time = self._get_date_timestamps(analysis_date)
#             print(f"⏰ Analysis period: {analysis_date}")
            
#             # Initialize data structure
#             clickup_data = {
#                 'date': analysis_date.strftime('%Y-%m-%d'),
#                 'timestamp': datetime.now().isoformat(),
#                 'space_name': space_info.get('name', 'Unknown'),
#                 'projects_analyzed': 0,
#                 'detailed_data': {},
#                 'project_data': {},
#                 'status_filters': status_filters,  # NEW: Store applied filters
#                 'debug_info': {
#                     'is_weekend': is_weekend,
#                     'total_lists': len(lists),
#                     'analysis_date': str(analysis_date),
#                     'status_filters_applied': status_filters
#                 } if debug else {}
#             }
            
#             # Analyze each list/project
#             for list_info in lists:
#                 list_id = list_info.get('id')
#                 list_name = list_info.get('name', 'Unknown Project')
                
#                 print(f"\n📋 Analyzing project: {list_name}")
                
#                 # Get tasks for this list with status filtering
#                 tasks = self._get_list_tasks(list_id, debug, status_filters)  # NEW: Pass filters
                
#                 # Filter tasks by status
#                 filtered_tasks = self._filter_tasks_by_status(tasks, status_filters)
                
#                 print(f"   📝 Found {len(tasks)} total tasks, {len(filtered_tasks)} matching status filters")
                
#                 if filtered_tasks:
#                     # Group tasks by assignee
#                     tasks_by_member = self._group_tasks_by_assignee(filtered_tasks)
                    
#                     # Store project data
#                     clickup_data['project_data'][list_name] = {
#                         'list_id': list_id,
#                         'list_name': list_name,
#                         'total_tasks': len(filtered_tasks),
#                         'tasks_by_member': tasks_by_member,
#                         'task_details': filtered_tasks
#                     }
                    
#                     # Analyze each member's tasks in this project
#                     for member_name, member_tasks in tasks_by_member.items():
#                         if member_name not in clickup_data['detailed_data']:
#                             clickup_data['detailed_data'][member_name] = {
#                                 'task_periods': [],
#                                 'downtime_periods': [],
#                                 'task_details': [],
#                                 'projects': []
#                             }
                        
#                         # Analyze activity for this member's tasks in this project
#                         task_periods, downtime_periods, task_details = self._analyze_task_activity(
#                             member_tasks, start_ts, current_ts, start_of_day, current_time, debug
#                         )
                        
#                         # Add to member's data
#                         clickup_data['detailed_data'][member_name]['task_periods'].extend(task_periods)
#                         clickup_data['detailed_data'][member_name]['downtime_periods'].extend(downtime_periods)
#                         clickup_data['detailed_data'][member_name]['task_details'].extend(task_details)
#                         clickup_data['detailed_data'][member_name]['projects'].append({
#                             'name': list_name,
#                             'task_count': len(member_tasks)
#                         })
                
#                 clickup_data['projects_analyzed'] += 1
#                 time.sleep(0.5)  # Rate limiting
            
#             print(f"\n✅ Analysis complete - {clickup_data['projects_analyzed']} projects analyzed")
#             print(f"🎯 Status filters applied: {status_filters}")
            
#             if clickup_data['projects_analyzed'] == 0:
#                 print("❌ No projects were analyzed!")
#                 return None
            
#             # Transform to Pulse format
#             pulse_data = self._transform_to_pulse_format(clickup_data)
            
#             return pulse_data
            
#         except Exception as e:
#             print(f"❌ Error generating pulse analytics: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def _get_space_info(self):
#         """Get space information"""
#         try:
#             resp = requests.get(f"{self.base_url}/space/{self.space_id}", headers=self.headers)
#             resp.raise_for_status()
#             return resp.json()
#         except Exception as e:
#             print(f"Error getting space info: {e}")
#             return None
    
#     def _get_space_lists(self):
#         """Get all lists in the space"""
#         try:
#             resp = requests.get(f"{self.base_url}/space/{self.space_id}/list", headers=self.headers)
#             resp.raise_for_status()
#             data = resp.json()
#             return data.get('lists', [])
#         except Exception as e:
#             print(f"Error getting space lists: {e}")
#             return []
    
#     def _get_list_tasks(self, list_id, debug=False, status_filters=None):
#         """Get all tasks for a specific list"""
#         try:
#             # Get all tasks (not filtering by status at API level since ClickUp API doesn't support multiple status filters)
#             url = f"{self.base_url}/list/{list_id}/task?include_closed=false"
            
#             if debug:
#                 print(f"🐛 DEBUG: API URL: {url}")
            
#             resp = requests.get(url, headers=self.headers)
#             resp.raise_for_status()
#             data = resp.json()
            
#             return data.get('tasks', [])
            
#         except Exception as e:
#             print(f"Error getting list tasks: {e}")
#             return []
    
#     def _filter_tasks_by_status(self, tasks, status_filters):
#         """
#         Filter tasks by status on the client side
#         """
#         if not status_filters:
#             return tasks
        
#         # Normalize status filters for comparison
#         normalized_filters = [status.lower().strip() for status in status_filters]
        
#         filtered_tasks = []
#         for task in tasks:
#             task_status = task.get('status', {}).get('status', '').lower().strip()
            
#             if task_status in normalized_filters:
#                 filtered_tasks.append(task)
        
#         return filtered_tasks

#     def _group_tasks_by_assignee(self, tasks):
#         """Group tasks by assignee"""
#         tasks_by_member = defaultdict(list)
        
#         for task in tasks:
#             assignees = task.get('assignees', [])
            
#             if not assignees:
#                 # Unassigned task
#                 tasks_by_member['Unassigned'].append(task)
#             else:
#                 for assignee in assignees:
#                     username = assignee.get('username', 'Unknown')
#                     tasks_by_member[username].append(task)
        
#         return dict(tasks_by_member)
    
#     def _get_date_timestamps(self, target_date):
#         """Get start and end timestamps for a specific date"""
#         if isinstance(target_date, str):
#             target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
#         # Create datetime objects for the target date
#         start_of_day = datetime.combine(target_date, datetime.min.time())
        
#         # If analyzing today, use current time; otherwise use end of day
#         if target_date == datetime.now().date():
#             current_time = datetime.now()
#         else:
#             current_time = datetime.combine(target_date, datetime.max.time().replace(microsecond=0))
        
#         # Convert to ClickUp timestamps (milliseconds)
#         start_ts = int(start_of_day.timestamp() * 1000)
#         current_ts = int(current_time.timestamp() * 1000)
        
#         return start_ts, current_ts, start_of_day, current_time
    
#     def _analyze_task_activity(self, tasks, start_ts, current_ts, start_of_day, current_time, debug=False):
#         """Analyze task activity and identify downtime periods"""
#         task_periods = []
#         downtime_periods = []
#         task_details = []
        
#         # Working hours boundaries for the analysis date
#         analysis_date = start_of_day.date()
#         work_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_START_HOUR))
#         work_end = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_END_HOUR))
        
#         # Track task activities
#         activities = []
        
#         for task in tasks:
#             try:
#                 # Get task details
#                 task_name = task.get('name', 'Unknown Task')
#                 task_id = task.get('id', 'unknown')
#                 task_status = task.get('status', {}).get('status', 'unknown')
#                 priority = task.get('priority')
#                 due_date = task.get('due_date')
                
#                 # Get the list/project name from task
#                 list_info = task.get('list', {})
#                 project_name = list_info.get('name', 'Unknown Project')
                
#                 # Store task details for dashboard
#                 task_details.append({
#                     'name': task_name,
#                     'id': task_id,
#                     'status': task_status,
#                     'due_date': due_date,
#                     'priority': priority,
#                     'project_name': project_name,  # Now we have the actual project name!
#                     'list_id': list_info.get('id')
#                 })
                
#                 # Check for recent activity
#                 date_updated = task.get('date_updated')
#                 if date_updated:
#                     updated_time = datetime.fromtimestamp(int(date_updated) / 1000)
                    
#                     # Check if activity is on the analysis date and within working hours
#                     if (updated_time.date() == analysis_date and
#                         work_start <= updated_time <= work_end):
                        
#                         activities.append({
#                             'time': updated_time,
#                             'task_name': task_name,
#                             'task_id': task_id,
#                             'project_name': project_name,
#                             'type': 'update'
#                         })
                
#             except Exception as e:
#                 print(f"    Error processing task {task.get('id', 'unknown')}: {e}")
        
#         # Sort activities by time
#         activities.sort(key=lambda x: x['time'])
        
#         print(f"    Found {len(activities)} activities in working hours")
        
#         # Create task periods from activities or estimate from task details
#         if not activities and task_details:
#             # Create estimated periods for open tasks
#             current_work_time = work_start
#             for i, task in enumerate(task_details[:3]):  # Limit to first 3 tasks
#                 if current_work_time >= work_end:
#                     break
                
#                 # Estimate 2-hour periods for tasks
#                 period_duration = 2.0
#                 period_end = min(current_work_time + timedelta(hours=period_duration), work_end)
                
#                 task_periods.append({
#                     'start': current_work_time.isoformat(),
#                     'end': period_end.isoformat(),
#                     'task_name': task['name'],
#                     'task_id': task['id'],
#                     'project_name': task['project_name'],  # Include project name
#                     'duration_hours': round((period_end - current_work_time).total_seconds() / 3600, 2),
#                     'status': 'estimated'
#                 })
                
#                 current_work_time = period_end + timedelta(hours=0.5)
#         else:
#             # Create task periods from actual activities
#             for i, activity in enumerate(activities):
#                 start_time = activity['time']
                
#                 # Estimate task duration
#                 if i < len(activities) - 1:
#                     next_time = activities[i + 1]['time']
#                     duration = min((next_time - start_time).total_seconds() / 3600, 2.0)
#                 else:
#                     duration = 1.0
                
#                 end_time = start_time + timedelta(hours=duration)
                
#                 if end_time > work_end:
#                     end_time = work_end
#                     duration = (end_time - start_time).total_seconds() / 3600
                
#                 if duration > 0:
#                     task_periods.append({
#                         'start': start_time.isoformat(),
#                         'end': end_time.isoformat(),
#                         'task_name': activity['task_name'],
#                         'task_id': activity['task_id'],
#                         'project_name': activity['project_name'],  # Include project name
#                         'duration_hours': round(duration, 2),
#                         'status': 'active'
#                     })
        
#         return task_periods, downtime_periods, task_details
    
#     def _transform_to_pulse_format(self, clickup_data):
#         """Transform ClickUp data to Pulse dashboard format with enhanced error handling"""
#         try:
#             member_workloads = {}
#             project_analytics = {}
            
#             print("🔄 Starting transform to pulse format...")
            
#             # Debug: Check the structure of clickup_data
#             print(f"🐛 DEBUG: clickup_data keys: {list(clickup_data.keys())}")
#             print(f"🐛 DEBUG: project_data type: {type(clickup_data.get('project_data', {}))}")
#             print(f"🐛 DEBUG: detailed_data type: {type(clickup_data.get('detailed_data', {}))}")
            
#             # Process project data first - with error handling
#             project_data = clickup_data.get('project_data', {})
#             if isinstance(project_data, dict):
#                 for project_name, project_info in project_data.items():
#                     try:
#                         print(f"🔄 Processing project: {project_name}")
#                         print(f"🐛 DEBUG: project_info type: {type(project_info)}")
                        
#                         # Ensure project_info is a dictionary
#                         if not isinstance(project_info, dict):
#                             print(f"⚠️ WARNING: project_info for {project_name} is not a dict: {type(project_info)}")
#                             continue
                        
#                         # Safely extract project data
#                         list_id = project_info.get('list_id', 'unknown')
#                         total_tasks = project_info.get('total_tasks', 0)
#                         tasks_by_member = project_info.get('tasks_by_member', {})
                        
#                         # Ensure tasks_by_member is a dictionary
#                         if not isinstance(tasks_by_member, dict):
#                             print(f"⚠️ WARNING: tasks_by_member for {project_name} is not a dict: {type(tasks_by_member)}")
#                             tasks_by_member = {}
                        
#                         project_analytics[project_name] = {
#                             "name": project_name,
#                             "list_id": list_id,
#                             "active_tasks": total_tasks,
#                             "assigned_members": list(tasks_by_member.keys()),
#                             "member_count": len(tasks_by_member),
#                             "tasks_by_member": tasks_by_member,
#                             "status": "active",
#                             "priority": "medium"
#                         }
#                         print(f"✅ Successfully processed project: {project_name}")
                        
#                     except Exception as e:
#                         print(f"❌ Error processing project {project_name}: {e}")
#                         print(f"🐛 DEBUG: project_info content: {project_info}")
#                         continue
#             else:
#                 print(f"⚠️ WARNING: project_data is not a dictionary: {type(project_data)}")
            
#             # Process each member's data - with error handling
#             detailed_data = clickup_data.get('detailed_data', {})
#             if isinstance(detailed_data, dict):
#                 for username, member_data in detailed_data.items():
#                     try:
#                         print(f"🔄 Processing member: {username}")
#                         print(f"🐛 DEBUG: member_data type: {type(member_data)}")
                        
#                         # Ensure member_data is a dictionary
#                         if not isinstance(member_data, dict):
#                             print(f"⚠️ WARNING: member_data for {username} is not a dict: {type(member_data)}")
#                             continue
                        
#                         workload = self._calculate_member_workload(username, member_data)
#                         member_workloads[username] = workload
#                         print(f"✅ Successfully processed member: {username}")
                        
#                     except Exception as e:
#                         print(f"❌ Error processing member {username}: {e}")
#                         print(f"🐛 DEBUG: member_data content: {member_data}")
#                         continue
#             else:
#                 print(f"⚠️ WARNING: detailed_data is not a dictionary: {type(detailed_data)}")
            
#             print(f"✅ Processed {len(member_workloads)} members and {len(project_analytics)} projects")
            
#             # Generate additional analytics with error handling
#             try:
#                 timeline_analysis = self._analyze_timeline(clickup_data)
#             except Exception as e:
#                 print(f"❌ Error in timeline analysis: {e}")
#                 timeline_analysis = {
#                     "urgent_deadlines": [],
#                     "upcoming_deadlines": [],
#                     "overdue_tasks": [],
#                     "high_priority_tasks": [],
#                     "deadline_pressure_by_member": {}
#                 }
            
#             try:
#                 load_balance_insights = self._generate_load_balance_insights(member_workloads, timeline_analysis)
#             except Exception as e:
#                 print(f"❌ Error in load balance insights: {e}")
#                 load_balance_insights = {
#                     "highest_workload": None,
#                     "lowest_workload": None,
#                     "overloaded_members": [],
#                     "available_members": [],
#                     "transfer_suggestions": []
#                 }
            
#             try:
#                 recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
#             except Exception as e:
#                 print(f"❌ Error in recommendations: {e}")
#                 recommendations = []
            
#             try:
#                 overview_stats = self._calculate_overview_stats(member_workloads, project_analytics)
#             except Exception as e:
#                 print(f"❌ Error in overview stats: {e}")
#                 overview_stats = {
#                     "total_members": len(member_workloads),
#                     "total_projects": len(project_analytics),
#                     "total_active_tasks": 0,
#                     "avg_tasks_per_member": 0,
#                     "avg_workload_score": 0,
#                     "health_score": 50
#                 }
            
#             final_data = {
#                 "member_workloads": member_workloads,
#                 "project_analytics": project_analytics,
#                 "timeline_analysis": timeline_analysis,
#                 "load_balance_insights": load_balance_insights,
#                 "recommendations": recommendations,
#                 "overview_stats": overview_stats,
#                 "last_updated": datetime.now().isoformat(),
#                 "data_source": "clickup_space",
#                 "analysis_date": clickup_data.get('date', 'unknown'),
#                 "space_name": clickup_data.get('space_name', 'Unknown'),
#                 "status_filters": clickup_data.get('status_filters', [])
#             }
            
#             print("✅ Transform to pulse format completed successfully")
#             return final_data
            
#         except Exception as e:
#             print(f"❌ Critical error in transform to pulse format: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
        
  
#     def _calculate_member_workload(self, username, member_data):
#         """Calculate workload for a single member with enhanced error handling"""
#         try:
#             print(f"🔄 Calculating workload for {username}")
            
#             # Safely get task details
#             task_details = member_data.get('task_details', [])
#             if not isinstance(task_details, list):
#                 print(f"⚠️ WARNING: task_details for {username} is not a list: {type(task_details)}")
#                 task_details = []
            
#             all_tasks = task_details
#             active_tasks_count = len(all_tasks)
            
#             print(f"🐛 DEBUG: {username} has {active_tasks_count} tasks")
            
#             urgent_tasks = 0
#             high_priority_tasks = 0
#             due_soon_tasks = 0
            
#             # Process each task with error handling
#             for i, task in enumerate(all_tasks):
#                 try:
#                     if not isinstance(task, dict):
#                         print(f"⚠️ WARNING: Task {i} for {username} is not a dict: {type(task)}")
#                         continue
                    
#                     # Safely handle priority
#                     priority = task.get('priority', {})
#                     if priority is None:
#                         priority_level = 'medium'
#                     elif isinstance(priority, dict):
#                         priority_level = priority.get('priority', 'medium')
#                     elif isinstance(priority, str):
#                         priority_level = priority
#                     else:
#                         priority_level = str(priority) if priority else 'medium'
                    
#                     if priority_level == 'urgent':
#                         urgent_tasks += 1
#                     elif priority_level == 'high':
#                         high_priority_tasks += 1
                    
#                     # Safely handle due date
#                     due_date = task.get('due_date')
#                     if due_date:
#                         try:
#                             if isinstance(due_date, str) and due_date.isdigit():
#                                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                             elif isinstance(due_date, (int, float)):
#                                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                             else:
#                                 continue  # Skip invalid due dates
                            
#                             days_until_due = (due_datetime - datetime.now()).days
#                             if days_until_due <= 2:
#                                 due_soon_tasks += 1
#                         except (ValueError, TypeError, OSError) as e:
#                             print(f"⚠️ WARNING: Invalid due_date for task: {due_date}")
#                             continue
                            
#                 except Exception as e:
#                     print(f"❌ Error processing task {i} for {username}: {e}")
#                     continue
            
#             # Safely get projects
#             projects_list = member_data.get('projects', [])
#             if not isinstance(projects_list, list):
#                 print(f"⚠️ WARNING: projects for {username} is not a list: {type(projects_list)}")
#                 projects_list = []
            
#             # Safely calculate time estimate
#             task_periods = member_data.get('task_periods', [])
#             if not isinstance(task_periods, list):
#                 print(f"⚠️ WARNING: task_periods for {username} is not a list: {type(task_periods)}")
#                 task_periods = []
            
#             total_time_estimate = 0
#             for period in task_periods:
#                 if isinstance(period, dict):
#                     duration = period.get('duration_hours', 0)
#                     if isinstance(duration, (int, float)):
#                         total_time_estimate += duration * 60
            
#             # Calculate workload score
#             workload_score = self._calculate_workload_score({
#                 "active_tasks": active_tasks_count,
#                 "urgent_tasks": urgent_tasks,
#                 "high_priority_tasks": high_priority_tasks,
#                 "due_soon_tasks": due_soon_tasks,
#                 "projects_count": len(projects_list),
#                 "remaining_time": total_time_estimate
#             })
            
#             # Get task breakdown
#             task_breakdown = self._get_task_breakdown(all_tasks)
            
#             result = {
#                 "username": username,
#                 "active_tasks": active_tasks_count,
#                 "projects_count": len(projects_list),
#                 "projects": projects_list,
#                 "tasks": all_tasks,
#                 "urgent_tasks": urgent_tasks,
#                 "high_priority_tasks": high_priority_tasks,
#                 "due_soon_tasks": due_soon_tasks,
#                 "workload_score": workload_score,
#                 "status": self._determine_workload_status(workload_score),
#                 "remaining_time": total_time_estimate,
#                 "task_breakdown": task_breakdown
#             }
            
#             print(f"✅ Workload calculated for {username}: {active_tasks_count} tasks, score: {workload_score}")
#             return result
            
#         except Exception as e:
#             print(f"❌ Error calculating workload for {username}: {e}")
#             import traceback
#             traceback.print_exc()
            
#             # Return a safe default
#             return {
#                 "username": username,
#                 "active_tasks": 0,
#                 "projects_count": 0,
#                 "projects": [],
#                 "tasks": [],
#                 "urgent_tasks": 0,
#                 "high_priority_tasks": 0,
#                 "due_soon_tasks": 0,
#                 "workload_score": 0,
#                 "status": "light",
#                 "remaining_time": 0,
#                 "task_breakdown": {}
#             }

#     def _get_task_breakdown(self, tasks):
#         """Get breakdown of tasks by status with error handling"""
#         try:
#             breakdown = {
#                 "in_progress": 0,
#                 "to_do": 0,
#                 "bugs": 0,
#                 "planning": 0,
#                 "for_qa": 0,
#                 "for_viewing": 0,
#                 "grammar": 0
#             }
            
#             if not isinstance(tasks, list):
#                 return breakdown
            
#             for task in tasks:
#                 try:
#                     if not isinstance(task, dict):
#                         continue
                    
#                     # Safely get status
#                     status_obj = task.get('status', {})
#                     if isinstance(status_obj, dict):
#                         status = status_obj.get('status', '').lower().strip()
#                     elif isinstance(status_obj, str):
#                         status = status_obj.lower().strip()
#                     else:
#                         continue
                    
#                     if status in breakdown:
#                         breakdown[status] += 1
                        
#                 except Exception as e:
#                     print(f"⚠️ Warning: Error processing task status: {e}")
#                     continue
            
#             return breakdown
            
#         except Exception as e:
#             print(f"❌ Error in get_task_breakdown: {e}")
#             return {
#                 "in_progress": 0,
#                 "to_do": 0,
#                 "bugs": 0,
#                 "planning": 0,
#                 "for_qa": 0,
#                 "for_viewing": 0,
#                 "grammar": 0
#             }
        
#     def _calculate_workload_score(self, workload):
#         """Calculate workload score based on multiple factors"""
#         score = 0
#         score += workload.get("active_tasks", 0) * 10
#         score += workload.get("urgent_tasks", 0) * 25
#         score += workload.get("high_priority_tasks", 0) * 15
#         score += workload.get("due_soon_tasks", 0) * 20
#         remaining_hours = workload.get("remaining_time", 0) / 60
#         score += remaining_hours * 2
#         score += workload.get("projects_count", 0) * 5
#         return round(score, 1)
    
#     def _determine_workload_status(self, score):
#         """Determine workload status based on score"""
#         if score >= 150:
#             return "overloaded"
#         elif score >= 100:
#             return "high"
#         elif score >= 50:
#             return "balanced" 
#         else:
#             return "light"
    
#     def _update_project_analytics(self, project_analytics, member_data, username):  
#         """Update project analytics with member data"""
#         # This is simplified - in reality you'd group by actual project IDs
#         for task in member_data.get('task_details', []):
#             project_name = f"Project {task.get('status', 'unknown').title()}"
            
#             if project_name not in project_analytics:
#                 project_analytics[project_name] = {
#                     "name": project_name,
#                     "active_tasks": 0,
#                     "assigned_members": set(),
#                     "total_time_estimate": 0,
#                     "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
#                     "priority": "medium",
#                     "status": "active"
#                 }
            
#             project_analytics[project_name]["active_tasks"] += 1
#             project_analytics[project_name]["assigned_members"].add(username)
        
#         # Convert sets to lists for JSON serialization
#         for project_id, project in project_analytics.items():
#             if isinstance(project["assigned_members"], set):
#                 project["assigned_members"] = list(project["assigned_members"])
#                 project["member_count"] = len(project["assigned_members"])
    
#     def _analyze_timeline(self, clickup_data):
#         """Analyze timeline and deadlines"""
#         analysis = {
#             "urgent_deadlines": [],
#             "upcoming_deadlines": [],
#             "overdue_tasks": [],
#             "high_priority_tasks": [],
#             "deadline_pressure_by_member": defaultdict(int)
#         }
        
#         for username, member_data in clickup_data['detailed_data'].items():
#             for task in member_data.get('task_details', []):
#                 # Priority analysis
#                 priority = task.get('priority', {})
#                 if isinstance(priority, dict):
#                     priority_level = priority.get('priority', 'medium')
#                 else:
#                     priority_level = str(priority) if priority else 'medium'
                
#                 if priority_level in ["urgent", "high"]:
#                     analysis["high_priority_tasks"].append(task)
                
#                 # Deadline analysis
#                 due_date = task.get('due_date')
#                 if due_date:
#                     try:
#                         due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                         days_until_due = (due_datetime - datetime.now()).days
                        
#                         if days_until_due < 0:
#                             analysis["overdue_tasks"].append(task)
#                         elif days_until_due <= 1:
#                             analysis["urgent_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 3
#                         elif days_until_due <= 7:
#                             analysis["upcoming_deadlines"].append(task)
#                             analysis["deadline_pressure_by_member"][username] += 1
#                     except:
#                         pass
        
#         # Convert defaultdict to regular dict
#         analysis["deadline_pressure_by_member"] = dict(analysis["deadline_pressure_by_member"])
        
#         return analysis
    
#     def _generate_load_balance_insights(self, workloads, timeline_analysis):
#         """Generate load balancing insights with transfer suggestions"""
#         insights = {
#             "highest_workload": None,
#             "lowest_workload": None,
#             "overloaded_members": [],
#             "available_members": [],
#             "transfer_suggestions": []
#         }
        
#         if not workloads:
#             return insights
        
#         # Find highest and lowest workload
#         sorted_workloads = sorted(workloads.items(), key=lambda x: x[1]["workload_score"], reverse=True)
        
#         if sorted_workloads:
#             insights["highest_workload"] = {
#                 "username": sorted_workloads[0][0],
#                 "score": sorted_workloads[0][1]["workload_score"],
#                 "status": sorted_workloads[0][1]["status"],
#                 "details": sorted_workloads[0][1]
#             }
            
#             insights["lowest_workload"] = {
#                 "username": sorted_workloads[-1][0],
#                 "score": sorted_workloads[-1][1]["workload_score"],
#                 "status": sorted_workloads[-1][1]["status"],
#                 "details": sorted_workloads[-1][1]
#             }
        
#         # Identify overloaded and available members
#         overloaded_members = []
#         available_members = []
        
#         for username, workload in workloads.items():
#             if workload["status"] in ["overloaded", "high"]:
#                 overloaded_members.append({
#                     "username": username,
#                     "workload": workload
#                 })
#             elif workload["status"] == "light":
#                 available_members.append({
#                     "username": username,
#                     "workload": workload
#                 })
        
#         insights["overloaded_members"] = overloaded_members
#         insights["available_members"] = available_members
        
#         # Generate transfer suggestions
#         insights["transfer_suggestions"] = self._generate_transfer_suggestions(
#             overloaded_members, available_members, workloads
#         )
        
#         return insights

#     def _generate_transfer_suggestions(self, overloaded_members, available_members, all_workloads):
#         """
#         Generate specific task transfer suggestions between team members
#         """
#         suggestions = []
        
#         if not overloaded_members or not available_members:
#             return suggestions
        
#         # Sort overloaded by severity, available by capacity
#         overloaded_sorted = sorted(
#             overloaded_members, 
#             key=lambda x: x["workload"]["workload_score"], 
#             reverse=True
#         )
        
#         available_sorted = sorted(
#             available_members, 
#             key=lambda x: x["workload"]["workload_score"]
#         )
        
#         for overloaded_member in overloaded_sorted[:3]:  # Top 3 overloaded
#             overloaded_username = overloaded_member["username"]
#             overloaded_workload = overloaded_member["workload"]
            
#             # Get transferable tasks (non-urgent, not due soon)
#             transferable_tasks = self._get_transferable_tasks(overloaded_workload)
            
#             if not transferable_tasks:
#                 continue
                
#             for available_member in available_sorted[:2]:  # Top 2 available
#                 available_username = available_member["username"]
#                 available_workload = available_member["workload"]
                
#                 # Check if this member can take more work
#                 if available_workload["workload_score"] >= 80:  # Don't overload available members
#                     continue
                
#                 # Find best task to transfer
#                 best_task = self._find_best_transfer_task(
#                     transferable_tasks, 
#                     overloaded_workload, 
#                     available_workload
#                 )
                
#                 if best_task:
#                     # Calculate impact
#                     score_reduction = self._estimate_score_reduction(best_task, overloaded_workload)
#                     score_increase = self._estimate_score_increase(best_task, available_workload)
                    
#                     # Only suggest if it significantly helps and doesn't hurt too much
#                     if score_reduction >= 15 and score_increase <= 25:
#                         suggestion = {
#                             "from_member": overloaded_username,
#                             "to_member": available_username,
#                             "task": {
#                                 "id": best_task["id"],
#                                 "name": best_task["name"],
#                                 "project_name": best_task.get("project_name", "Unknown"),
#                                 "status": best_task["status"],
#                                 "priority": best_task.get("priority", {}).get("priority", "normal") if best_task.get("priority") else "normal"
#                             },
#                             "reason": self._generate_transfer_reason(
#                                 overloaded_username, 
#                                 available_username, 
#                                 best_task, 
#                                 score_reduction, 
#                                 score_increase
#                             ),
#                             "impact": {
#                                 "from_score_reduction": score_reduction,
#                                 "to_score_increase": score_increase,
#                                 "net_improvement": score_reduction - score_increase
#                             }
#                         }
                        
#                         suggestions.append(suggestion)
                        
#                         # Remove this task from transferable list to avoid duplicate suggestions
#                         transferable_tasks.remove(best_task)
                        
#                         # Limit suggestions per overloaded member
#                         if len([s for s in suggestions if s["from_member"] == overloaded_username]) >= 2:
#                             break
        
#         # Sort suggestions by net improvement (highest impact first)
#         suggestions.sort(key=lambda x: x["impact"]["net_improvement"], reverse=True)
        
#         # Return top 5 suggestions
#         return suggestions[:5]

#     def _estimate_score_increase(self, task, to_workload):
#         """
#         Estimate how much the workload score would increase by receiving this task
#         """
#         base_increase = 10  # Base increase for any task
        
#         # Add increase based on priority
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         if priority_level == "high":
#             base_increase += 15
#         elif priority_level == "normal":
#             base_increase += 10
#         elif priority_level == "low":
#             base_increase += 5
        
#         # Reduce increase if member is already on the project
#         task_project = task.get("project_name", "")
#         to_member_projects = [p.get("name", "") for p in to_workload.get("projects", [])]
        
#         if task_project in to_member_projects:
#             base_increase -= 5  # Easier to take on task in familiar project
        
#         return base_increase


#     def _estimate_score_reduction(self, task, from_workload):
#         """
#         Estimate how much the workload score would reduce by transferring this task
#         """
#         base_reduction = 10  # Base reduction for any task
        
#         # Add reduction based on priority
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         if priority_level == "high":
#             base_reduction += 15
#         elif priority_level == "normal":
#             base_reduction += 10
#         elif priority_level == "low":
#             base_reduction += 5
        
#         # Add reduction based on due date pressure
#         due_date = task.get("due_date")
#         if due_date:
#             try:
#                 due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                 days_until_due = (due_datetime - datetime.now()).days
#                 if days_until_due <= 7:
#                     base_reduction += 20
#                 elif days_until_due <= 14:
#                     base_reduction += 10
#             except:
#                 pass
        
#         return base_reduction

#     def _find_best_transfer_task(self, transferable_tasks, from_workload, to_workload):
#         """
#         Find the best task to transfer based on multiple criteria
#         """
#         if not transferable_tasks:
#             return None
        
#         # Score each task for transfer suitability
#         scored_tasks = []
        
#         for task in transferable_tasks:
#             score = 0
            
#             # Prefer tasks that are not started yet
#             if task.get("status") == "to do":
#                 score += 20
#             elif task.get("status") == "planning":
#                 score += 15
#             elif task.get("status") == "in progress":
#                 score += 5  # Less preferred
            
#             # Prefer normal priority tasks
#             priority = task.get("priority", {})
#             if isinstance(priority, dict):
#                 priority_level = priority.get("priority", "normal")
#             else:
#                 priority_level = str(priority) if priority else "normal"
            
#             if priority_level == "normal":
#                 score += 15
#             elif priority_level == "low":
#                 score += 10
#             elif priority_level == "high":
#                 score += 5  # Can transfer but less preferred
            
#             # Prefer tasks with longer deadlines
#             due_date = task.get("due_date")
#             if due_date:
#                 try:
#                     due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                     days_until_due = (due_datetime - datetime.now()).days
#                     if days_until_due > 14:
#                         score += 15
#                     elif days_until_due > 7:
#                         score += 10
#                     elif days_until_due > 3:
#                         score += 5
#                 except:
#                     score += 10  # No penalty for invalid dates
#             else:
#                 score += 10  # No deadline is good for transfer
            
#             # Check if the receiving member is already on this project
#             task_project = task.get("project_name", "")
#             to_member_projects = [p.get("name", "") for p in to_workload.get("projects", [])]
            
#             if task_project in to_member_projects:
#                 score += 25  # Big bonus for same project
            
#             scored_tasks.append((task, score))
        
#         # Return the highest scored task
#         if scored_tasks:
#             scored_tasks.sort(key=lambda x: x[1], reverse=True)
#             return scored_tasks[0][0]
        
#         return None

#     def _generate_transfer_reason(self, from_member, to_member, task, score_reduction, score_increase):
#         """
#         Generate a human-readable reason for the transfer suggestion
#         """
#         priority = task.get("priority", {})
#         if isinstance(priority, dict):
#             priority_level = priority.get("priority", "normal")
#         else:
#             priority_level = str(priority) if priority else "normal"
        
#         # Base reason
#         reason = f"Transfer '{task['name']}' to help reduce {from_member}'s workload"
        
#         # Add specific reasons
#         reasons = []
        
#         if score_reduction >= 20:
#             reasons.append("high impact task")
        
#         if priority_level == "normal" or priority_level == "low":
#             reasons.append("non-critical priority")
        
#         if task.get("status") in ["to do", "planning"]:
#             reasons.append("not yet started")
        
#         # Check project familiarity
#         task_project = task.get("project_name", "")
#         if task_project:
#             reasons.append(f"within {task_project} project")
        
#         if score_increase <= 15:
#             reasons.append(f"minimal impact on {to_member}")
        
#         if reasons:
#             reason += f" ({', '.join(reasons)})"
        
#         # Add impact summary
#         net_improvement = score_reduction - score_increase
#         reason += f". Net workload improvement: {net_improvement} points."
        
#         return reason

#     def _get_transferable_tasks(self, workload):
#         """
#         Get tasks that can be safely transferred (not urgent or due soon)
#         """
#         transferable = []
        
#         for task in workload.get("tasks", []):
#             # Skip urgent tasks
#             priority = task.get("priority", {})
#             if isinstance(priority, dict):
#                 priority_level = priority.get("priority", "normal")
#             else:
#                 priority_level = str(priority) if priority else "normal"
            
#             if priority_level == "urgent":
#                 continue
            
#             # Skip tasks due soon
#             due_date = task.get("due_date")
#             if due_date:
#                 try:
#                     due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
#                     days_until_due = (due_datetime - datetime.now()).days
#                     if days_until_due <= 3:  # Due within 3 days
#                         continue
#                 except:
#                     pass
            
#             # Skip tasks in final stages
#             if task.get("status") in ["review", "testing", "staging"]:
#                 continue
            
#             # Only transfer tasks that are in early stages
#             if task.get("status") in ["to do", "planning", "in progress"]:
#                 transferable.append(task)
        
#         return transferable

        
#     def _generate_recommendations(self, workloads, timeline_analysis):
#         """Generate recommendations based on workload analysis"""
#         recommendations = []
        
#         # Check for overloaded members
#         overloaded = [w for w in workloads.values() if w["status"] in ["overloaded", "high"]]
#         if overloaded:
#             for member in overloaded:
#                 recommendations.append({
#                     "type": "workload_warning",
#                     "priority": "high",
#                     "member": member["username"],
#                     "message": f"{member['username']} has {member['status']} workload with {member['active_tasks']} active tasks across {member['projects_count']} projects",
#                     "action": "Consider redistributing tasks or extending deadlines"
#                 })
        
#         # Check for urgent deadlines
#         if timeline_analysis["urgent_deadlines"]:
#             recommendations.append({
#                 "type": "deadline_alert",
#                 "priority": "urgent",
#                 "message": f"{len(timeline_analysis['urgent_deadlines'])} tasks due within 24 hours",
#                 "action": "Review urgent tasks and allocate additional resources if needed"
#             })
        
#         return recommendations
    
#     def _calculate_overview_stats(self, workloads, projects_data):
#         """Calculate overview statistics"""
#         total_members = len(workloads)
#         total_projects = len(projects_data)
#         total_active_tasks = sum(w["active_tasks"] for w in workloads.values())
        
#         # Workload distribution
#         status_counts = defaultdict(int)
#         for workload in workloads.values():
#             status_counts[workload["status"]] += 1
        
#         avg_workload_score = sum(w["workload_score"] for w in workloads.values()) / total_members if total_members > 0 else 0
        
#         return {
#             "total_members": total_members,
#             "total_projects": total_projects,
#             "total_active_tasks": total_active_tasks,
#             "avg_tasks_per_member": round(total_active_tasks / total_members, 1) if total_members > 0 else 0,
#             "avg_workload_score": round(avg_workload_score, 1),
#             "workload_distribution": dict(status_counts),
#             "health_score": self._calculate_team_health_score(status_counts, total_members)
#         }
    
#     def _calculate_team_health_score(self, status_counts, total_members):
#         """Calculate overall team health score (0-100)"""
#         if total_members == 0:
#             return 0
        
#         score = 100
        
#         overloaded_ratio = status_counts.get("overloaded", 0) / total_members
#         high_ratio = status_counts.get("high", 0) / total_members
        
#         # Penalize for overloaded members
#         score -= overloaded_ratio * 50
#         score -= high_ratio * 25
        
#         return max(0, round(score))




#!/usr/bin/env python3
"""
ClickUp Pulse Integration - Enhanced with JSON File Caching
Modified from the original ClickUp analytics script for Pulse dashboard integration
"""

import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict
import os
import glob

class ClickUpPulseIntegration:
    def __init__(self, api_token, space_id):
        self.api_token = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
        self.space_id = space_id  # Use your space ID here
        self.headers = {'Authorization': api_token}
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
    
    def get_all_available_spaces(self):
        """Get all spaces available to the user"""
        try:
            # First get all teams
            resp = requests.get(f"{self.base_url}/team", headers=self.headers)
            resp.raise_for_status()
            teams = resp.json().get('teams', [])
            
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
            
            return all_spaces
            
        except Exception as e:
            print(f"Error getting available spaces: {e}")
            return {}


    def generate_pulse_analytics(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None):
        """
        Generate comprehensive pulse analytics from ClickUp data with JSON caching
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

            if space_filters and len(space_filters) > 1:
                return self._generate_multi_space_pulse_data(target_date, debug, status_filters, member_filters, space_filters)
            else:
                # Single space - use existing logic
                self.space_id = space_filters[0] if space_filters else '90132462540'
                return self._generate_fresh_pulse_data(target_date, debug, status_filters, member_filters)
            
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
            
            # Generate fresh data using ClickUp API
            # fresh_data = self._generate_fresh_pulse_data(target_date, debug, status_filters)
            # fresh_data = self._generate_fresh_pulse_data(target_date, debug, status_filters, member_filters)
            fresh_data = self._generate_multi_space_pulse_data(target_date, debug, status_filters, member_filters, space_filters)
            print(f"fresssshhhh {fresh_data}")
            if fresh_data and fresh_data.get('member_workloads'):
                print(f'thus is fresh data')
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
            print(f"❌ Error generating pulse analytics: {e}")
            import traceback
            traceback.print_exc()
            return self._get_demo_data()
    
    def _generate_fresh_pulse_data(self, target_date=None, debug=False, status_filters=None, member_filters=None):
        """
        Generate fresh pulse data using ClickUp integration (original logic)
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
                # for task in tasks:
                #     self._process_task_for_member_workload(task, member_workloads, timeline_analysis)
                for task in tasks:
                    self._process_task_for_member_workload(task, member_workloads, timeline_analysis, member_filters)
            
            if total_tasks == 0:
                print("❌ No tasks found matching the status filters!")
                return None
            
            print(f"✅ Total tasks processed: {total_tasks}")
            print(f"✅ Members with workload: {len(member_workloads)}")
            
            # Generate load balance insights
            load_balance_insights = self._generate_load_balance_insights(member_workloads)
            
            # Generate overview stats
            overview_stats = self._generate_overview_stats(member_workloads, project_analytics, total_tasks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
            
            # Compile final analytics
            analytics_data = {
                "member_workloads": member_workloads,
                "project_analytics": project_analytics,
                "timeline_analysis": timeline_analysis,
                "load_balance_insights": load_balance_insights,
                "overview_stats": overview_stats,
                "recommendations": recommendations,
                "last_updated": datetime.now().isoformat(),
                "data_source": "clickup_api",
                "cache_info": {
                    "generated_fresh": True,
                    "status_filters_used": status_filters,
                    "analysis_date": str(target_date)
                }
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
            return None

    def _generate_multi_space_pulse_data(self, target_date=None, debug=False, status_filters=None, member_filters=None, space_filters=None):
        """
        Generate pulse data by combining multiple spaces
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
            for space_id in space_filters:
                print(f"📋 Processing space: {space_id}")
                
                # Temporarily set space_id for this iteration
                self.space_id = space_id
                
                # Get data for this space
                space_data = self._generate_fresh_pulse_data(target_date, debug, status_filters, member_filters)
                
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
            
            # Recalculate workload scores for combined data
            for username, workload in combined_member_workloads.items():
                score = (
                    workload["active_tasks"] * 10 +
                    workload["urgent_tasks"] * 25 +
                    workload["high_priority_tasks"] * 15 +
                    workload["due_soon_tasks"] * 10
                )
                workload["workload_score"] = round(score, 1)
                workload["remaining_time"] = workload["total_time_estimate"] - workload["total_time_spent"]
                
                # Determine status based on new score
                if score >= 150:
                    workload["status"] = "overloaded"
                elif score >= 100:
                    workload["status"] = "high"
                elif score >= 50:
                    workload["status"] = "balanced"
                else:
                    workload["status"] = "light"
            
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
            return None


    # JSON Caching Methods (from PulseService)
    def _save_pulse_data(self, data):
        """
        Save pulse data to JSON file with timestamp
        """
        try:
            print(f"💾 Saved pSavedSavedSavedSavedSavedulse data to:")
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

    # Original ClickUp API Methods (existing functionality)
    def _get_space_info(self):
        """Get space information"""
        try:
            resp = requests.get(f"{self.base_url}/space/{self.space_id}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error getting space info: {e}")
            return None
    
    def _get_space_lists(self):
        """Get all lists in the space, including those inside folders"""
        try:
            all_lists = []
            
            # 1. Get lists directly in the space (not in folders)
            print("🔍 Getting lists directly in space...")
            resp = requests.get(f"{self.base_url}/space/{self.space_id}/list", headers=self.headers)
            resp.raise_for_status()
            direct_lists = resp.json().get('lists', [])
            all_lists.extend(direct_lists)
            print(f"   ✅ Found {len(direct_lists)} direct lists in space")
            
            # 2. Get all folders in the space
            print("📁 Getting folders in space...")
            resp = requests.get(f"{self.base_url}/space/{self.space_id}/folder", headers=self.headers)
            resp.raise_for_status()
            folders = resp.json().get('folders', [])
            print(f"   ✅ Found {len(folders)} folders in space")
            
            # 3. Get lists from each folder
            for folder in folders:
                folder_id = folder.get('id')
                folder_name = folder.get('name', 'Unknown Folder')
                
                print(f"📂 Getting lists from folder: {folder_name}")
                try:
                    resp = requests.get(f"{self.base_url}/folder/{folder_id}/list", headers=self.headers)
                    resp.raise_for_status()
                    folder_lists = resp.json().get('lists', [])
                    
                    # Add folder info to each list for context
                    for list_item in folder_lists:
                        list_item['folder_info'] = {
                            'folder_id': folder_id,
                            'folder_name': folder_name
                        }
                    
                    all_lists.extend(folder_lists)
                    print(f"   ✅ Found {len(folder_lists)} lists in folder '{folder_name}'")
                    
                except Exception as e:
                    print(f"   ❌ Error getting lists from folder '{folder_name}': {e}")
                    continue
            
            print(f"✅ Total lists found: {len(all_lists)} (direct: {len(direct_lists)}, in folders: {len(all_lists) - len(direct_lists)})")
            return all_lists
            
        except Exception as e:
            print(f"❌ Error getting space lists and folders: {e}")
            import traceback
            traceback.print_exc()
            return []


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

    def _get_list_tasks_with_status_filter(self, list_id, status_filters, debug=False):
        """Get tasks from a list with status filtering"""
        try:
            resp = requests.get(f"{self.base_url}/list/{list_id}/task", headers=self.headers)
            resp.raise_for_status()
            all_tasks = resp.json().get('tasks', [])
            
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
        """Analyze a single project/list - Enhanced with folder support"""
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
            folder_info = list_item.get('folder_info')
            if folder_info:
                project_display_name = f"{folder_info['folder_name']} / {project_name}"
            else:
                project_display_name = project_name
            
            project_data = {
                "name": project_display_name,  # Include folder in display name
                "original_name": project_name,  # Keep original name
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
                "high_priority_tasks": high_priority_tasks
            }
            
            print(f"📊 Project '{project_display_name}': {len(tasks)} tasks, {len(assignees)} members, {round(total_time, 1)}min estimated")
            return project_data
            
        except Exception as e:
            print(f"❌ Error analyzing project {list_item.get('name', 'Unknown')}: {e}")
            return {
                "name": list_item.get('name', 'Unknown Project'),
                "original_name": list_item.get('name', 'Unknown Project'),
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
                "high_priority_tasks": 0
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
    
    def _process_task_for_member_workload(self, task, member_workloads, timeline_analysis, member_filters=None):
        """Process a task for member workload analysis - Enhanced with folder support"""
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
                        "workload_score": 0,
                        "status": "light",
                        "total_time_estimate": 0,
                        "total_time_spent": 0,
                        "remaining_time": 0,
                        "tasks": []  # Store actual task objects for frontend
                    }
                
                # Update task counts
                member_workloads[username]["active_tasks"] += 1
                
                # Get project/list information with folder context
                list_info = task.get('list', {})
                project_name = list_info.get('name', 'Unknown Project')
                
                # Try to get folder info from the list if available
                # Note: Individual tasks might not have folder info, so we'll use the project name as-is
                
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
                
                # Update time estimates (ClickUp uses milliseconds)
                time_estimate = task.get('time_estimate')
                if time_estimate:
                    # Convert from milliseconds to minutes
                    estimate_minutes = int(time_estimate) / 1000 / 60
                    member_workloads[username]["total_time_estimate"] += estimate_minutes
                
                # Update time spent
                time_spent = task.get('time_spent')
                if time_spent:
                    # Convert from milliseconds to minutes  
                    spent_minutes = int(time_spent) / 1000 / 60
                    member_workloads[username]["total_time_spent"] += spent_minutes
                
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
        """Generate load balancing insights"""
        try:
            if not member_workloads:
                return {
                    "highest_workload": None,
                    "lowest_workload": None,
                    "overloaded_members": [],
                    "available_members": [],
                    "transfer_suggestions": []
                }
            
            # Calculate workload scores and determine status for each member
            for username, workload in member_workloads.items():
                score = (
                    workload["active_tasks"] * 10 +
                    workload["urgent_tasks"] * 25 +
                    workload["high_priority_tasks"] * 15 +
                    workload["due_soon_tasks"] * 10
                )
                workload["workload_score"] = round(score, 1)
                workload["remaining_time"] = workload["total_time_estimate"] - workload["total_time_spent"]
                
                # Determine status based on score
                if score >= 150:
                    workload["status"] = "overloaded"
                elif score >= 100:
                    workload["status"] = "high"
                elif score >= 50:
                    workload["status"] = "balanced"
                else:
                    workload["status"] = "light"
                
                print(f"📊 {username}: Score={score}, Status={workload['status']}")
            
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
        """Generate overview statistics"""
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
                status = workload.get("status", "unknown")
                status_counts[status] += 1
            
            # Calculate team health score (0-100)
            health_score = self._calculate_team_health_score(status_counts, total_members)
            
            overview = {
                "total_members": total_members,
                "total_projects": total_projects,
                "total_active_tasks": total_tasks,
                "avg_tasks_per_member": round(avg_tasks_per_member, 1),
                "avg_workload_score": round(avg_workload_score, 1),
                "workload_distribution": dict(status_counts),
                "health_score": health_score
            }
            
            print(f"✅ Overview stats: {total_members} members, {total_projects} projects, {total_tasks} tasks, health: {health_score}")
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
                "health_score": 0
            }
    
    def _calculate_team_health_score(self, status_counts, total_members):
        """Calculate overall team health score (0-100)"""
        if total_members == 0:
            return 0
        
        score = 100
        
        overloaded_ratio = status_counts.get("overloaded", 0) / total_members
        high_ratio = status_counts.get("high", 0) / total_members
        
        # Penalize for overloaded members
        score -= overloaded_ratio * 50
        score -= high_ratio * 25
        
        return max(0, round(score))
    
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