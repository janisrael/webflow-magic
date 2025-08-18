#!/usr/bin/env python3
"""
ClickUp Pulse Integration
Modified from the original ClickUp analytics script for Pulse dashboard integration
"""

import requests
import time
from datetime import datetime, timedelta
import json
from collections import defaultdict

TEAM_MEMBERS = ['Jan', 'Tricia Kennedy', 'Arif', 'wiktor']

class ClickUpPulseIntegration:
    def __init__(self, api_token, space_id):
        self.api_token = 'pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K'
        self.team_id = '9013605091'
        self.space_id = '90132462540'
        self.headers = {'Authorization': api_token}
        self.base_url = 'https://api.clickup.com/api/v2'
        
        # Working hours configuration
        self.WORKDAY_START_HOUR = 9
        self.WORKDAY_END_HOUR = 17
        self.LUNCH_BREAK_START = 12
        self.LUNCH_BREAK_END = 12.5
        self.WORKING_HOURS_PER_DAY = 7.5
    
    def generate_pulse_analytics(self, target_date=None, debug=False):
        """
        Generate comprehensive pulse analytics from ClickUp data
        """
        try:
            print("🔍 Getting team information...")
            members = self._get_team_members()
            
            if debug:
                print(f"🐛 DEBUG: Found {len(members)} team members")
                for member in members[:3]:  # Show first 3 members for debugging
                    user = member.get('user', {})
                    print(f"🐛 DEBUG: Member - {user.get('username', 'Unknown')} (ID: {user.get('id', 'N/A')})")
            
            if not members:
                print("❌ No team members found! Check team_id and API key.")
                return None
            
            print(f"✅ Found {len(members)} team members")
            
            # Use provided date or default to today
            if target_date:
                analysis_date = target_date
            else:
                analysis_date = datetime.now().date()
            
            # Check if it's a weekend
            is_weekend = analysis_date.weekday() >= 5  # Saturday = 5, Sunday = 6
            
            if is_weekend and debug:
                print(f"🐛 DEBUG: {analysis_date} is a weekend day (weekday: {analysis_date.weekday()})")
                print(f"🐛 DEBUG: This might explain empty results if no weekend activity")
            
            # Get time range for the analysis date
            start_ts, current_ts, start_of_day, current_time = self._get_date_timestamps(analysis_date)
            print(f"⏰ Analysis period: {analysis_date} (Working hours: {self.WORKDAY_START_HOUR}:00-{self.WORKDAY_END_HOUR}:00)")
            
            # Analyze each member
            clickup_data = {
                'date': analysis_date.strftime('%Y-%m-%d'),
                'timestamp': datetime.now().isoformat(),
                'members_analyzed': 0,
                'detailed_data': {},
                'debug_info': {
                    'is_weekend': is_weekend,
                    'total_team_members': len(members),
                    'analysis_date': str(analysis_date)
                } if debug else {}
            }
            
            # More flexible member targeting - try all if no specific targets
            target_members = ['Jan', 'Tricia Kennedy', 'Arif', 'wiktor']  
            found_members = []
            
            for member in members:
                user = member.get('user', {})
                username = user.get('username', 'Unknown')
                user_id = user.get('id')
                
                if debug:
                    print(f"🐛 DEBUG: Checking member {username}")
                
                # Be more flexible - include if username contains any target name or if no targets specified
                should_analyze = False
                if not target_members:
                    should_analyze = True
                else:
                    for target in target_members:
                        if target.lower() in username.lower() or username.lower() in target.lower():
                            should_analyze = True
                            break
                
                if not should_analyze:
                    if debug:
                        print(f"🐛 DEBUG: Skipping {username} (not in target list)")
                    continue
                    
                found_members.append(username)
                print(f"\n👤 Analyzing {username} (ID: {user_id})...")
                
                # Get tasks for this member
                tasks = self._get_member_tasks(user_id, debug)
                print(f"   📋 Found {len(tasks)} open tasks")
                
                if debug and tasks:
                    print(f"🐛 DEBUG: Sample task: {tasks[0].get('name', 'Unknown')} (Status: {tasks[0].get('status', {}).get('status', 'Unknown')})")
                
                # Analyze activity
                task_periods, downtime_periods, task_details = self._analyze_task_activity(
                    tasks, start_ts, current_ts, start_of_day, current_time, debug
                )
                
                clickup_data['detailed_data'][username] = {
                    'task_periods': task_periods,
                    'downtime_periods': downtime_periods,
                    'task_details': task_details
                }
                
                clickup_data['members_analyzed'] += 1
                print(f"   ✅ Analysis complete - Tasks: {len(task_details)}, Periods: {len(task_periods)}, Downtime: {len(downtime_periods)}")
                
                # Rate limiting delay
                time.sleep(1)
            
            if debug:
                print(f"🐛 DEBUG: Found and analyzed members: {found_members}")
                print(f"🐛 DEBUG: Total analyzed: {clickup_data['members_analyzed']}")
            
            if clickup_data['members_analyzed'] == 0:
                print("❌ No members were analyzed! This could be due to:")
                print("   - Username mismatch in target_members list")
                print("   - Weekend/non-working day with no activity")
                print("   - API permissions issue")
                print("   - No open tasks for team members")
                
                if debug:
                    print(f"🐛 DEBUG: Available usernames: {[m.get('user', {}).get('username', 'Unknown') for m in members[:5]]}")
                
                return None
            
            # Transform ClickUp data to Pulse format
            pulse_data = self._transform_to_pulse_format(clickup_data)
            
            return pulse_data
            
        except Exception as e:
            print(f"❌ Error generating pulse analytics: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_team_members(self):
        """Get all team members"""
        try:
            resp = requests.get(f"{self.base_url}/team", headers=self.headers)
            resp.raise_for_status()
            teams = resp.json().get('teams', [])
            
            for team in teams:
                if team.get('id') == str(self.team_id):
                    return team.get('members', [])
            return []
        except Exception as e:
            print(f"Error getting team members: {e}")
            return []
    
    def _get_date_timestamps(self, target_date):
        """Get start and end timestamps for a specific date"""
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Create datetime objects for the target date
        start_of_day = datetime.combine(target_date, datetime.min.time())
        
        # If analyzing today, use current time; otherwise use end of day
        if target_date == datetime.now().date():
            current_time = datetime.now()
        else:
            current_time = datetime.combine(target_date, datetime.max.time().replace(microsecond=0))
        
        # Convert to ClickUp timestamps (milliseconds)
        start_ts = int(start_of_day.timestamp() * 1000)
        current_ts = int(current_time.timestamp() * 1000)
        
        return start_ts, current_ts, start_of_day, current_time
    
    def _get_member_tasks(self, member_id, debug=False, max_retries=3):
        """Get all open tasks for a team member"""
        for attempt in range(max_retries):
            try:
                # Get open tasks only
                url = f"{self.base_url}/team/{self.team_id}/task?assignees[]={member_id}&include_closed=false"
                
                if debug:
                    print(f"🐛 DEBUG: API URL: {url}")
                
                resp = requests.get(url, headers=self.headers)
                
                if resp.status_code == 429:  # Rate limited
                    wait_time = 60
                    print(f"    Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                
                if debug:
                    print(f"🐛 DEBUG: API Response status: {resp.status_code}")
                    
                resp.raise_for_status()
                data = resp.json()
                
                tasks = data.get('tasks', [])
                
                if debug and tasks:
                    print(f"🐛 DEBUG: Sample task data structure:")
                    sample_task = tasks[0]
                    print(f"🐛 DEBUG: Task keys: {list(sample_task.keys())}")
                    print(f"🐛 DEBUG: Task name: {sample_task.get('name', 'N/A')}")
                    print(f"🐛 DEBUG: Task status: {sample_task.get('status', 'N/A')}")
                    print(f"🐛 DEBUG: Task date_updated: {sample_task.get('date_updated', 'N/A')}")
                
                return tasks
                
            except requests.exceptions.RequestException as e:
                print(f"    Error getting tasks (attempt {attempt + 1}): {e}")
                if debug:
                    print(f"🐛 DEBUG: Request exception details: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(10)
        
        print("    Failed to fetch tasks after all retries")
        return []
    
    def _analyze_task_activity(self, tasks, start_ts, current_ts, start_of_day, current_time, debug=False):
        """Analyze task activity and identify downtime periods"""
        task_periods = []
        downtime_periods = []
        task_details = []
        
        # Working hours boundaries for the analysis date
        analysis_date = start_of_day.date()
        work_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_START_HOUR))
        lunch_start = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.LUNCH_BREAK_START))
        lunch_end = datetime.combine(analysis_date, datetime.min.time().replace(
            hour=int(self.LUNCH_BREAK_END), minute=int((self.LUNCH_BREAK_END % 1) * 60)))
        work_end = datetime.combine(analysis_date, datetime.min.time().replace(hour=self.WORKDAY_END_HOUR))
        
        if debug:
            print(f"🐛 DEBUG: Analysis date: {analysis_date}")
            print(f"🐛 DEBUG: Working hours: {work_start.strftime('%H:%M')} - {work_end.strftime('%H:%M')}")
            print(f"🐛 DEBUG: Is weekend: {analysis_date.weekday() >= 5}")
        
        print(f"    Working hours: {work_start.strftime('%H:%M')} - {work_end.strftime('%H:%M')}")
        
        # Track task activities
        activities = []
        
        for task in tasks:
            try:
                # Get task details
                task_name = task.get('name', 'Unknown Task')
                task_id = task.get('id', 'unknown')
                task_status = task.get('status', {}).get('status', 'unknown')
                priority = task.get('priority')
                due_date = task.get('due_date')
                
                # Store task details for dashboard
                task_details.append({
                    'name': task_name,
                    'id': task_id,
                    'status': task_status,
                    'due_date': due_date,
                    'priority': priority
                })
                
                # Check for time tracking or recent activity
                date_updated = task.get('date_updated')
                if date_updated:
                    updated_time = datetime.fromtimestamp(int(date_updated) / 1000)
                    
                    if debug:
                        print(f"🐛 DEBUG: Task '{task_name}' updated at: {updated_time}")
                        print(f"🐛 DEBUG: Analysis date: {analysis_date}, Task date: {updated_time.date()}")
                    
                    # Check if activity is on the analysis date and within working hours
                    if (updated_time.date() == analysis_date and
                        work_start <= updated_time <= work_end and
                        not (lunch_start <= updated_time <= lunch_end)):
                        
                        activities.append({
                            'time': updated_time,
                            'task_name': task_name,
                            'task_id': task_id,
                            'type': 'update'
                        })
                        
                        if debug:
                            print(f"🐛 DEBUG: Added activity: {task_name} at {updated_time}")
                    elif debug:
                        if updated_time.date() != analysis_date:
                            print(f"🐛 DEBUG: Skipped task (wrong date): {updated_time.date()} != {analysis_date}")
                        elif not (work_start <= updated_time <= work_end):
                            print(f"🐛 DEBUG: Skipped task (outside work hours): {updated_time.strftime('%H:%M')}")
                        elif lunch_start <= updated_time <= lunch_end:
                            print(f"🐛 DEBUG: Skipped task (during lunch): {updated_time.strftime('%H:%M')}")
                
            except Exception as e:
                print(f"    Error processing task {task.get('id', 'unknown')}: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
        
        # Sort activities by time
        activities.sort(key=lambda x: x['time'])
        
        print(f"    Found {len(activities)} activities in working hours")
        if debug:
            print(f"🐛 DEBUG: Activities: {[f\"{a['task_name']} at {a['time'].strftime('%H:%M')}\" for a in activities]}")
        
        # For weekends or days with no activity, create some task periods from task details
        # This helps show current workload even if no recent activity
        if not activities and task_details:
            if debug:
                print(f"🐛 DEBUG: No activities found, but {len(task_details)} tasks exist")
                print(f"🐛 DEBUG: Creating estimated task periods based on open tasks")
            
            # Create estimated periods for open tasks
            current_work_time = work_start
            for i, task in enumerate(task_details[:3]):  # Limit to first 3 tasks
                if current_work_time >= work_end:
                    break
                
                # Estimate 2-hour periods for tasks
                period_duration = 2.0
                period_end = min(current_work_time + timedelta(hours=period_duration), work_end)
                
                task_periods.append({
                    'start': current_work_time.isoformat(),
                    'end': period_end.isoformat(),
                    'task_name': task['name'],
                    'task_id': task['id'],
                    'duration_hours': round((period_end - current_work_time).total_seconds() / 3600, 2),
                    'status': 'estimated'  # Mark as estimated
                })
                
                current_work_time = period_end + timedelta(hours=0.5)  # Add break
        else:
            # Create task periods from actual activities
            for i, activity in enumerate(activities):
                start_time = activity['time']
                
                # Estimate task duration (1-2 hours by default, or until next activity)
                if i < len(activities) - 1:
                    next_time = activities[i + 1]['time']
                    duration = min((next_time - start_time).total_seconds() / 3600, 2.0)
                else:
                    # Last activity - assume 1 hour or until end of workday
                    time_to_end = (work_end - start_time).total_seconds() / 3600
                    duration = min(time_to_end, 1.0)
                
                end_time = start_time + timedelta(hours=duration)
                
                # Ensure we don't go past working hours
                if end_time > work_end:
                    end_time = work_end
                    duration = (end_time - start_time).total_seconds() / 3600
                
                if duration > 0:
                    task_periods.append({
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat(),
                        'task_name': activity['task_name'],
                        'task_id': activity['task_id'],
                        'duration_hours': round(duration, 2),
                        'status': 'active'
                    })
        
        # Calculate downtime periods (simplified for now)
        if not task_periods:
            # If analyzing today and it's current working hours, show some downtime
            if analysis_date == datetime.now().date() and work_start <= datetime.now() <= work_end:
                downtime_start = work_start
                downtime_end = min(datetime.now(), work_end)
                downtime_duration = (downtime_end - downtime_start).total_seconds() / 3600
                
                if downtime_duration > 0.25:  # More than 15 minutes
                    downtime_periods.append({
                        'start': downtime_start.isoformat(),
                        'end': downtime_end.isoformat(),
                        'duration_hours': round(downtime_duration, 2),
                        'reason': 'No activity detected today' if analysis_date == datetime.now().date() else 'No activity on this date'
                    })
        
        print(f"    Task periods: {len(task_periods)}")
        print(f"    Downtime periods: {len(downtime_periods)}")
        
        if debug:
            print(f"🐛 DEBUG: Task periods: {len(task_periods)}")
            for period in task_periods[:2]:  # Show first 2
                print(f"🐛 DEBUG: Period: {period['task_name']} ({period['duration_hours']}h)")
        
        return task_periods, downtime_periods, task_details
    
    def _transform_to_pulse_format(self, clickup_data):
        """
        Transform ClickUp data to Pulse dashboard format
        """
        try:
            # Initialize pulse data structure
            member_workloads = {}
            project_analytics = {}
            
            # Process each member's data
            for username, member_data in clickup_data['detailed_data'].items():
                # Calculate workload for this member
                workload = self._calculate_member_workload(username, member_data)
                member_workloads[username] = workload
                
                # Update project analytics
                self._update_project_analytics(project_analytics, member_data, username)
            
            # Generate additional analytics
            timeline_analysis = self._analyze_timeline(clickup_data)
            load_balance_insights = self._generate_load_balance_insights(member_workloads, timeline_analysis)
            recommendations = self._generate_recommendations(member_workloads, timeline_analysis)
            overview_stats = self._calculate_overview_stats(member_workloads, project_analytics)
            
            return {
                "member_workloads": member_workloads,
                "project_analytics": project_analytics,
                "timeline_analysis": timeline_analysis,
                "load_balance_insights": load_balance_insights,
                "recommendations": recommendations,
                "overview_stats": overview_stats,
                "last_updated": datetime.now().isoformat(),
                "data_source": "clickup_live",
                "analysis_date": clickup_data['date']
            }
            
        except Exception as e:
            print(f"Error transforming to pulse format: {e}")
            return None
    
    def _calculate_member_workload(self, username, member_data):
        """
        Calculate workload for a single member
        """
        # Count active tasks
        active_tasks = len(member_data.get('task_details', []))
        
        # Get projects from task details
        projects = {}
        for task in member_data.get('task_details', []):
            # In a real scenario, you'd get project info from task
            # For now, we'll use task status as a simple project grouping
            project_name = f"Project {task.get('status', 'unknown').title()}"
            if project_name not in projects:
                projects[project_name] = {
                    "name": project_name,
                    "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "status": "active",
                    "priority": "medium"
                }
        
        projects_list = list(projects.values())
        
        # Calculate time metrics
        total_time_estimate = sum(period.get('duration_hours', 0) * 60 
                                for period in member_data.get('task_periods', []))
        total_downtime = sum(period.get('duration_hours', 0) * 60 
                           for period in member_data.get('downtime_periods', []))
        
        # Count priority tasks
        urgent_tasks = 0
        high_priority_tasks = 0
        due_soon_tasks = 0
        
        for task in member_data.get('task_details', []):
            priority = task.get('priority', {})
            if isinstance(priority, dict):
                priority_level = priority.get('priority', 'medium')
            else:
                priority_level = str(priority) if priority else 'medium'
            
            if priority_level == 'urgent':
                urgent_tasks += 1
            elif priority_level == 'high':
                high_priority_tasks += 1
            
            # Check due date
            due_date = task.get('due_date')
            if due_date:
                try:
                    due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
                    days_until_due = (due_datetime - datetime.now()).days
                    if days_until_due <= 2:
                        due_soon_tasks += 1
                except:
                    pass
        
        # Calculate workload score
        workload_score = self._calculate_workload_score({
            "active_tasks": active_tasks,
            "urgent_tasks": urgent_tasks,
            "high_priority_tasks": high_priority_tasks,
            "due_soon_tasks": due_soon_tasks,
            "projects_count": len(projects_list),
            "remaining_time": total_time_estimate
        })
        
        # Determine status
        status = self._determine_workload_status(workload_score)
        
        return {
            "username": username,
            "active_tasks": active_tasks,
            "projects_count": len(projects_list),
            "projects": projects_list,
            "tasks": member_data.get('task_details', []),
            "total_time_estimate": total_time_estimate,
            "total_time_spent": 0,  # Would need time tracking data
            "urgent_tasks": urgent_tasks,
            "high_priority_tasks": high_priority_tasks,
            "due_soon_tasks": due_soon_tasks,
            "workload_score": workload_score,
            "status": status,
            "remaining_time": total_time_estimate,
            "downtime_hours": total_downtime / 60
        }
    
    def _calculate_workload_score(self, workload):
        """Calculate workload score based on multiple factors"""
        score = 0
        
        # Base score from active tasks
        score += workload.get("active_tasks", 0) * 10
        
        # Additional weight for urgent/high priority
        score += workload.get("urgent_tasks", 0) * 25
        score += workload.get("high_priority_tasks", 0) * 15
        
        # Weight for due soon tasks
        score += workload.get("due_soon_tasks", 0) * 20
        
        # Weight for time estimates (hours)
        remaining_hours = workload.get("remaining_time", 0) / 60
        score += remaining_hours * 2
        
        # Weight for number of projects
        score += workload.get("projects_count", 0) * 5
        
        return round(score, 1)
    
    def _determine_workload_status(self, score):
        """Determine workload status based on score"""
        if score >= 150:
            return "overloaded"
        elif score >= 100:
            return "high"
        elif score >= 50:
            return "balanced" 
        else:
            return "light"
    
    def _update_project_analytics(self, project_analytics, member_data, username):
        """Update project analytics with member data"""
        # This is simplified - in reality you'd group by actual project IDs
        for task in member_data.get('task_details', []):
            project_name = f"Project {task.get('status', 'unknown').title()}"
            
            if project_name not in project_analytics:
                project_analytics[project_name] = {
                    "name": project_name,
                    "active_tasks": 0,
                    "assigned_members": set(),
                    "total_time_estimate": 0,
                    "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "priority": "medium",
                    "status": "active"
                }
            
            project_analytics[project_name]["active_tasks"] += 1
            project_analytics[project_name]["assigned_members"].add(username)
        
        # Convert sets to lists for JSON serialization
        for project_id, project in project_analytics.items():
            if isinstance(project["assigned_members"], set):
                project["assigned_members"] = list(project["assigned_members"])
                project["member_count"] = len(project["assigned_members"])
    
    def _analyze_timeline(self, clickup_data):
        """Analyze timeline and deadlines"""
        analysis = {
            "urgent_deadlines": [],
            "upcoming_deadlines": [],
            "overdue_tasks": [],
            "high_priority_tasks": [],
            "deadline_pressure_by_member": defaultdict(int)
        }
        
        for username, member_data in clickup_data['detailed_data'].items():
            for task in member_data.get('task_details', []):
                # Priority analysis
                priority = task.get('priority', {})
                if isinstance(priority, dict):
                    priority_level = priority.get('priority', 'medium')
                else:
                    priority_level = str(priority) if priority else 'medium'
                
                if priority_level in ["urgent", "high"]:
                    analysis["high_priority_tasks"].append(task)
                
                # Deadline analysis
                due_date = task.get('due_date')
                if due_date:
                    try:
                        due_datetime = datetime.fromtimestamp(int(due_date) / 1000)
                        days_until_due = (due_datetime - datetime.now()).days
                        
                        if days_until_due < 0:
                            analysis["overdue_tasks"].append(task)
                        elif days_until_due <= 1:
                            analysis["urgent_deadlines"].append(task)
                            analysis["deadline_pressure_by_member"][username] += 3
                        elif days_until_due <= 7:
                            analysis["upcoming_deadlines"].append(task)
                            analysis["deadline_pressure_by_member"][username] += 1
                    except:
                        pass
        
        # Convert defaultdict to regular dict
        analysis["deadline_pressure_by_member"] = dict(analysis["deadline_pressure_by_member"])
        
        return analysis
    
    def _generate_load_balance_insights(self, workloads, timeline_analysis):
        """Generate load balancing insights"""
        insights = {
            "highest_workload": None,
            "lowest_workload": None,
            "overloaded_members": [],
            "available_members": [],
            "transfer_suggestions": []
        }
        
        if not workloads:
            return insights
        
        # Find highest and lowest workload
        sorted_workloads = sorted(workloads.items(), key=lambda x: x[1]["workload_score"], reverse=True)
        
        if sorted_workloads:
            insights["highest_workload"] = {
                "username": sorted_workloads[0][0],
                "score": sorted_workloads[0][1]["workload_score"],
                "status": sorted_workloads[0][1]["status"],
                "details": sorted_workloads[0][1]
            }
            
            insights["lowest_workload"] = {
                "username": sorted_workloads[-1][0],
                "score": sorted_workloads[-1][1]["workload_score"],
                "status": sorted_workloads[-1][1]["status"],
                "details": sorted_workloads[-1][1]
            }
        
        # Identify overloaded and available members
        for username, workload in workloads.items():
            if workload["status"] in ["overloaded", "high"]:
                insights["overloaded_members"].append({
                    "username": username,
                    "workload": workload
                })
            elif workload["status"] == "light":
                insights["available_members"].append({
                    "username": username,
                    "workload": workload
                })
        
        return insights
    
    def _generate_recommendations(self, workloads, timeline_analysis):
        """Generate recommendations based on workload analysis"""
        recommendations = []
        
        # Check for overloaded members
        overloaded = [w for w in workloads.values() if w["status"] in ["overloaded", "high"]]
        if overloaded:
            for member in overloaded:
                recommendations.append({
                    "type": "workload_warning",
                    "priority": "high",
                    "member": member["username"],
                    "message": f"{member['username']} has {member['status']} workload with {member['active_tasks']} active tasks across {member['projects_count']} projects",
                    "action": "Consider redistributing tasks or extending deadlines"
                })
        
        # Check for urgent deadlines
        if timeline_analysis["urgent_deadlines"]:
            recommendations.append({
                "type": "deadline_alert",
                "priority": "urgent",
                "message": f"{len(timeline_analysis['urgent_deadlines'])} tasks due within 24 hours",
                "action": "Review urgent tasks and allocate additional resources if needed"
            })
        
        return recommendations
    
    def _calculate_overview_stats(self, workloads, projects_data):
        """Calculate overview statistics"""
        total_members = len(workloads)
        total_projects = len(projects_data)
        total_active_tasks = sum(w["active_tasks"] for w in workloads.values())
        
        # Workload distribution
        status_counts = defaultdict(int)
        for workload in workloads.values():
            status_counts[workload["status"]] += 1
        
        avg_workload_score = sum(w["workload_score"] for w in workloads.values()) / total_members if total_members > 0 else 0
        
        return {
            "total_members": total_members,
            "total_projects": total_projects,
            "total_active_tasks": total_active_tasks,
            "avg_tasks_per_member": round(total_active_tasks / total_members, 1) if total_members > 0 else 0,
            "avg_workload_score": round(avg_workload_score, 1),
            "workload_distribution": dict(status_counts),
            "health_score": self._calculate_team_health_score(status_counts, total_members)
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