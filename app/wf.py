from flask import Flask, request, jsonify, send_file, render_template,make_response
import os, re
import tempfile
import zipfile
import shutil
from bs4 import BeautifulSoup
import re

from services.clickup_pulse_integration import ClickUpPulseIntegration
import json
import requests
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from services.seo_service import SEOService
import time
app = Flask(__name__)

# Static config
# BASE_DIR = '/home/jan-israel/dev/webflow_magic/app'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
seo_report_url = ''
print(f"BASE_DIR: {BASE_DIR}")
SEO_FOLDER = os.path.join(BASE_DIR, 'seo_reports')
STARTER_THEME = os.path.join(BASE_DIR, 'WebflowStarter')
ASSET_FOLDERS = ['css', 'js', 'images', 'videos', 'fonts', 'media', 'documents', 'cms']

@app.route('/')
def index():
    return render_template('index.html')


# Add this route to your existing wf.py file

@app.route('/api/pulse-data')
def get_pulse_data():
    try:
        target_date = request.args.get('date')
        debug_mode = request.args.get('debug', 'false').lower() == 'true'
        
        # Get status filters
        status_filters = request.args.getlist('status_filter')
        if not status_filters:
            status_filters = ['to do', 'planning', 'in progress', 'bugs']
        
        # Get member filters
        member_filters = request.args.getlist('member_filter')
        if not member_filters:
            member_filters = ['Arif', 'Jan', 'wiktor', 'Kendra', 'Calum', 'Tricia', 'Rick']
        
        # NEW: Get space filters
        space_filters = request.args.getlist('space_filter')
        if not space_filters:
            # Default: main workspace only
            filters =  ["90132462540", "90134767504", "90138214659", "90138873649"]
            space_filters = filters
            
        if debug_mode:
            print(f"🔍 DEBUG: Status filters: {status_filters}")
            print(f"👥 DEBUG: Member filters: {member_filters}")
            print(f"🏢 DEBUG: Space filters: {space_filters}")
        
        clickup_integration = ClickUpPulseIntegration(
            api_token='pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K',
            space_id=None  # We'll pass space_filters instead
        )
        
        # Pass all filters including spaces
        pulse_data = clickup_integration.generate_pulse_analytics(
            target_date=target_date,
            debug=debug_mode,
            status_filters=status_filters,
            member_filters=member_filters,
            space_filters=space_filters  # NEW
        )
        
        if pulse_data is None:
            return jsonify({"error": "No pulse data available"}), 404
        
        # Add filter info to response
        pulse_data["filter_info"] = {
            "status_filters_applied": status_filters,
            "member_filters_applied": member_filters,
            "space_filters_applied": space_filters,  # NEW
            "total_statuses_available": ['to do', 'planning', 'in progress', 'bugs', 'for qa', 'for viewing', 'grammar'],
            "total_members_available": ['Arif', 'Jan', 'wiktor', 'Kendra', 'Calum', 'Tricia', 'Rick'],
            "total_spaces_available": space_filters,  # You can get this from ClickUp API
            "filter_count": len(status_filters),
            "member_filter_count": len(member_filters),
            "space_filter_count": len(space_filters)  # NEW
        }
        
        return jsonify(pulse_data)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/api/available-spaces')
def get_available_spaces():
    try:
        clickup_integration = ClickUpPulseIntegration(
            api_token='pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K',
            space_id=None
        )
        
        spaces = clickup_integration.get_all_available_spaces()
        return jsonify({"spaces": spaces})
        
    except Exception as e:
        return jsonify({"error": f"Error fetching spaces: {str(e)}"}), 500

        
@app.route('/api/calendar-data')
def get_calendar_data():
    """
    Get unified calendar data including ClickUp tasks and Google Calendar events
    """
    try:
        # Get existing ClickUp project data (reuse from your existing structure)
        clickup_data = get_clickup_project_data()
        
        # Sample Google Calendar events (replace with real Google Calendar API integration)
        google_events = get_sample_google_events()
        
        # Process ClickUp tasks to extract calendar events
        calendar_tasks = process_clickup_tasks_for_calendar(clickup_data)
        
        # Combine and format all calendar data
        calendar_data = {
            "clickup_tasks": calendar_tasks,
            "google_events": google_events,
            "summary": generate_calendar_summary(calendar_tasks),
            "integration_status": {
                "clickup": "connected",
                "google_calendar": "demo"  # Change to "connected" when real API is integrated
            }
        }
        
        return jsonify(calendar_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_clickup_project_data():
    """
    Get ClickUp project data - reuses your existing data structure
    """
    # This reuses the same data structure from your projects_tracker.js
    return {
        "90132462540": {
            "name": "Web Design and App Development",
            "folders": [
                {
                    "id": "901310157028",
                    "name": "TheSantris",
                    "lists": [
                        {
                            "id": "901310471238",
                            "name": "Lotto (P1)",
                            "status": {
                                "status": "red",
                                "color": "#d33d44",
                                "hide_label": True,
                            },
                            "tasks": [
                                {
                                    "id": "86aanbgch",
                                    "name": "Email updates bug - not receiving win notifications",
                                    "status": "complete",
                                    "assignees": [
                                        {
                                            "id": 99989505,
                                            "username": "Tricia Kennedy",
                                            "email": "triciais@sourceselect.ca",
                                        },
                                        {
                                            "id": 126127973,
                                            "username": "Jan",
                                            "email": "janisatssm@gmail.com",
                                        },
                                    ],
                                    "due_date": str(int((datetime.now() + timedelta(days=0)).timestamp() * 1000)),  # Today
                                    "start_date": None,
                                    "priority": {
                                        "color": "#f50000",
                                        "id": "1",
                                        "orderindex": "1",
                                        "priority": "urgent",
                                    },
                                },
                                {
                                    "id": "86aanbe1d",
                                    "name": "Photo acceptance issues for tickets",
                                    "status": "in progress",
                                    "assignees": [
                                        {
                                            "id": 99989505,
                                            "username": "Tricia Kennedy",
                                            "email": "triciais@sourceselect.ca",
                                        },
                                        {
                                            "id": 126127973,
                                            "username": "Jan",
                                            "email": "janisatssm@gmail.com",
                                        },
                                    ],
                                    "due_date": str(int((datetime.now() + timedelta(days=1)).timestamp() * 1000)),  # Tomorrow
                                    "start_date": str(int((datetime.now() - timedelta(days=2)).timestamp() * 1000)),
                                    "priority": {
                                        "color": "#f50000",
                                        "id": "1",
                                        "orderindex": "1",
                                        "priority": "urgent",
                                    },
                                },
                                {
                                    "id": "86aanbd0q",
                                    "name": "App incorrectly showing no winners",
                                    "status": "bugs",
                                    "assignees": [
                                        {
                                            "id": 126127973,
                                            "username": "Jan",
                                            "email": "janisatssm@gmail.com",
                                        },
                                    ],
                                    "due_date": str(int((datetime.now() + timedelta(days=2)).timestamp() * 1000)),  # Day after tomorrow
                                    "start_date": None,
                                    "priority": {
                                        "color": "#f50000",
                                        "id": "1",
                                        "orderindex": "1",
                                        "priority": "urgent",
                                    },
                                },
                                {
                                    "id": "86aa4x0kp",
                                    "name": "Email notification design",
                                    "status": "to do",
                                    "assignees": [
                                        {
                                            "id": 126127973,
                                            "username": "Jan",
                                            "email": "janisatssm@gmail.com",
                                        },
                                    ],
                                    "due_date": str(int((datetime.now() + timedelta(days=5)).timestamp() * 1000)),  # 5 days from now
                                    "start_date": None,
                                    "priority": {
                                        "color": "#6fddff",
                                        "id": "3",
                                        "orderindex": "3",
                                        "priority": "normal",
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        "90134767504": {
            "name": "Design & Creative Services",
            "folders": [
                {
                    "id": "901310136443",
                    "name": "Design & Media",
                    "lists": [
                        {
                            "id": "901309584374",
                            "name": "The Cardboard Casket",
                            "tasks": [
                                {
                                    "id": "86aa5fjp3",
                                    "name": "Vinyl for Cardboard Casket and Retro Classics",
                                    "status": "on hold",
                                    "assignees": [
                                        {
                                            "id": 93916583,
                                            "username": "Calum",
                                            "email": "calumis@sourceselect.ca",
                                        },
                                    ],
                                    "due_date": str(int((datetime.now() + timedelta(days=3)).timestamp() * 1000)),  # 3 days from now
                                    "start_date": str(int((datetime.now() - timedelta(days=1)).timestamp() * 1000)),
                                    "priority": {
                                        "color": "#f8ae00",
                                        "id": "2",
                                        "orderindex": "2",
                                        "priority": "high",
                                    },
                                },
                                {
                                    "id": "86a7pyf7m",
                                    "name": "Create arrows colour proposal",
                                    "status": "complete",
                                    "assignees": [],
                                    "due_date": str(int((datetime.now() + timedelta(days=7)).timestamp() * 1000)),  # Next week
                                    "start_date": None,
                                    "priority": {
                                        "color": "#6fddff",
                                        "id": "3",
                                        "orderindex": "3",
                                        "priority": "normal",
                                    },
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    }


def get_sample_google_events():
    """
    Sample Google Calendar events - replace with real Google Calendar API integration
    """
    today = datetime.now()
    
    return [
        {
            "id": "gc1",
            "title": "Team Standup",
            "start": (today.replace(hour=9, minute=0, second=0, microsecond=0)).isoformat(),
            "end": (today.replace(hour=9, minute=30, second=0, microsecond=0)).isoformat(),
            "type": "meeting",
            "source": "google",
            "description": "Daily team standup meeting",
            "attendees": ["team@sourceselect.ca"]
        },
        {
            "id": "gc2",
            "title": "Client Review Call",
            "start": ((today + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)).isoformat(),
            "end": ((today + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)).isoformat(),
            "type": "meeting",
            "source": "google",
            "description": "Review progress with client",
            "attendees": ["client@example.com", "team@sourceselect.ca"]
        },
        {
            "id": "gc3",
            "title": "Sprint Planning",
            "start": ((today + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)).isoformat(),
            "end": ((today + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)).isoformat(),
            "type": "planning",
            "source": "google",
            "description": "Plan next sprint objectives",
            "attendees": ["dev-team@sourceselect.ca"]
        },
        {
            "id": "gc4",
            "title": "Design System Review",
            "start": ((today + timedelta(days=4)).replace(hour=15, minute=30, second=0, microsecond=0)).isoformat(),
            "end": ((today + timedelta(days=4)).replace(hour=16, minute=30, second=0, microsecond=0)).isoformat(),
            "type": "review",
            "source": "google",
            "description": "Review and update design system components",
            "attendees": ["design-team@sourceselect.ca"]
        }
    ]


def process_clickup_tasks_for_calendar(clickup_data):
    """
    Process ClickUp tasks and extract those with due dates for calendar display
    """
    calendar_tasks = []
    
    for project_id, project in clickup_data.items():
        for folder in project.get("folders", []):
            for list_item in folder.get("lists", []):
                for task in list_item.get("tasks", []):
                    if task.get("due_date"):  # Only include tasks with due dates
                        calendar_task = {
                            "id": task["id"],
                            "name": task["name"],
                            "status": task["status"],
                            "due_date": task["due_date"],
                            "start_date": task.get("start_date"),
                            "priority": task.get("priority", {"priority": "normal", "color": "#6fddff"}),
                            "assignees": task.get("assignees", []),
                            "project": project["name"],
                            "list": list_item["name"],
                            "source": "clickup"
                        }
                        calendar_tasks.append(calendar_task)
    
    return calendar_tasks


def generate_calendar_summary(calendar_tasks):
    """
    Generate summary statistics for calendar data
    """
    today = datetime.now().date()
    week_from_now = today + timedelta(days=7)
    
    due_today = 0
    due_this_week = 0
    overdue = 0
    in_progress = 0
    
    for task in calendar_tasks:
        if task.get("due_date"):
            due_date = datetime.fromtimestamp(int(task["due_date"]) / 1000).date()
            
            if due_date == today:
                due_today += 1
            elif today < due_date <= week_from_now:
                due_this_week += 1
            elif due_date < today:
                overdue += 1
                
            if task["status"] == "in progress":
                in_progress += 1
    
    return {
        "due_today": due_today,
        "due_this_week": due_this_week,
        "overdue": overdue,
        "in_progress": in_progress,
        "total_tasks": len(calendar_tasks)
    }


@app.route('/api/calendar-data/<date>')
def get_calendar_data_for_date(date):
    """
    Get calendar data for a specific date
    """
    try:
        # Parse the date
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Get all calendar data
        all_data = get_calendar_data().get_json()
        
        # Filter tasks and events for the specific date
        date_tasks = []
        date_events = []
        
        # Filter ClickUp tasks
        for task in all_data["clickup_tasks"]:
            if task.get("due_date"):
                task_date = datetime.fromtimestamp(int(task["due_date"]) / 1000).date()
                if task_date == target_date:
                    date_tasks.append(task)
        
        # Filter Google events
        for event in all_data["google_events"]:
            event_date = datetime.fromisoformat(event["start"]).date()
            if event_date == target_date:
                date_events.append(event)
        
        return jsonify({
            "date": date,
            "tasks": date_tasks,
            "events": date_events,
            "total_items": len(date_tasks) + len(date_events)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/calendar-sync', methods=['POST'])
def sync_calendar_data():
    """
    Endpoint to trigger calendar data synchronization
    This would integrate with real ClickUp and Google Calendar APIs
    """
    try:
        # In a real implementation, this would:
        # 1. Fetch latest data from ClickUp API
        # 2. Fetch latest data from Google Calendar API
        # 3. Update cached data
        # 4. Return synchronization status
        
        sync_result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "clickup_tasks_synced": 6,
            "google_events_synced": 4,
            "last_sync": datetime.now().isoformat()
        }
        
        return jsonify(sync_result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Optional: Add Google Calendar OAuth integration
@app.route('/api/google-calendar/auth')
def google_calendar_auth():
    """
    Initiate Google Calendar OAuth flow
    """
    # This would implement the Google OAuth2 flow
    # For now, return demo response
    return jsonify({
        "auth_url": "https://accounts.google.com/oauth2/auth?...",
        "status": "demo_mode"
    })


@app.route('/api/google-calendar/callback')
def google_calendar_callback():
    """
    Handle Google Calendar OAuth callback
    """
    # This would handle the OAuth callback and store tokens
    # For now, return demo response
    return jsonify({
        "status": "connected",
        "message": "Google Calendar integration successful"
    })


# Add this to your existing route to include calendar data in dashboard data
@app.route('/api/dashboard-data')
def get_dashboard_data():
    """
    Enhanced dashboard data endpoint that includes calendar information
    """
    try:
        # Get your existing dashboard data
        dashboard_data = {
            "projects": get_clickup_project_data(),
            "analytics": {
                "total_tasks": 12,
                "completed_today": 3,
                "in_progress": 5,
                "overdue": 2
            }
        }
        
        # Add calendar data
        calendar_data = get_calendar_data().get_json()
        dashboard_data["calendar"] = calendar_data
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        

@app.route('/seo-report/<folder_name>')
def serve_seo_report(folder_name):
    try:
        report_path = os.path.join(SEO_FOLDER, folder_name, 'SEO-OPTIMIZATION-REPORT.html')
        print(f"Looking for SEO report at: {report_path}")  # Debug line
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}  # Fix: Set proper content type
        else:
            print(f"File not found: {report_path}")  # Debug line
            return "<h1>SEO Report Not Found</h1><p>File does not exist at expected location.</p>", 404
    except Exception as e:
        print(f"Error serving SEO report: {str(e)}")  # Debug line
        return f"<h1>Error Loading Report</h1><p>{str(e)}</p>", 500


def fetch_webflow_cms(api_token, site_id):
    """Fetch all CMS collections and items from Webflow API"""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "accept": "application/json", 
        "accept-version": "2.0.0"
    }
    
    
    try:
        # 1. Get all collections
        collections_url = f"https://api.webflow.com/v2/sites/{site_id}/collections"
        collections_res = requests.get(collections_url, headers=headers)
        collections_res.raise_for_status()
        collections = collections_res.json().get("collections", [])
        
        if not collections:
            print("No collections found in this site")
            return None
            
        # 2. Fetch items for each collection
        def fetch_collection_items(collection):
            items_url = f"https://api.webflow.com/v2/collections/{collection['id']}/items"
            items_res = requests.get(items_url, headers=headers)
            items_res.raise_for_status()
            
            return {
                "id": collection["id"],
                "name": collection["displayName"],
                "slug": collection["slug"],
                "fields": [
                    {
                        "id": field["id"],
                        "name": field["displayName"],
                        "slug": field["slug"],
                        "type": field["type"]
                    } 
                    for field in collection.get("fieldDefinitions", [])  # Changed from 'fields'
                ],
                "items": items_res.json().get("items", [])
            }
        
        # 3. Process collections
        cms_data = []
        for collection in collections:
            try:
                cms_data.append(fetch_collection_items(collection))
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Failed to fetch {collection['displayName']}: {str(e)}")
            
        return cms_data
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error fetching CMS data: {str(e)}")
    
    return None


def process_html_files_safe(temp_dir, output_theme):
    """
    Safely process HTML files to avoid PHP syntax errors
    """
    processed_files = []
    
    for filename in os.listdir(temp_dir):
        if not filename.endswith('.html'):
            continue

        try:
            filepath = os.path.join(temp_dir, filename)
            print(f"Processing: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Remove problematic scripts and links that might cause PHP conflicts
            for tag in soup.find_all(['script', 'link']):
                src_or_href = tag.get('src') or tag.get('href') or ''
                if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                    tag.decompose()

            # Clean up any potentially problematic content
            clean_html_content(soup)

            # Add CDN resources
            head = soup.find('head')
            if head:
                cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
                splide_css = soup.new_tag('link', rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
                splide_js = soup.new_tag('script', src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')
                head.insert(0, cdn_jquery)
                head.append(splide_css)
                head.append(splide_js)

            # Add WordPress PHP includes
            body = soup.find('body')
            if body:
                original = list(body.contents)
                body.clear()
                body.append(BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
                for item in original:
                    body.append(item)
                body.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))
            else:
                soup.insert(0, BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
                soup.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))

            # Convert to string and fix asset paths
            html_str = str(soup)
            html_str = fix_asset_paths_safe(html_str)

            # Generate safe output filename
            out_filename = generate_safe_filename(filename)
            out_path = os.path.join(output_theme, out_filename)

            # Write the file safely
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html_str)
            
            processed_files.append({
                'original': filename,
                'output': out_filename,
                'path': out_path
            })
            
            print(f"Created: {out_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            # Create a basic fallback file
            create_fallback_page(filename, output_theme)
            continue
    
    return processed_files


def process_html_files_with_seo(temp_dir, output_theme, seo_enabled=False, 
                               business_type="", target_location="", 
                               openai_api_key="", serp_api_key=""):
    """
    Process HTML files with optional SEO optimization
    """
    processed_files = []
    seo_reports = {}
    
    # Initialize SEO service if enabled
    seo_service = None
    if seo_enabled:
        try:
            seo_service = SEOService(openai_api_key, serp_api_key)
            print("🚀 SEO Service initialized successfully")
        except Exception as e:
            print(f"⚠️ SEO Service initialization failed: {e}")
            seo_service = None
    
    for filename in os.listdir(temp_dir):
        if not filename.endswith('.html'):
            continue

        try:
            filepath = os.path.join(temp_dir, filename)
            print(f"Processing: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Remove problematic scripts and links that might cause PHP conflicts
            for tag in soup.find_all(['script', 'link']):
                src_or_href = tag.get('src') or tag.get('href') or ''
                if any(lib in src_or_href.lower() for lib in ['jquery', 'splide']):
                    tag.decompose()

            # Clean up any potentially problematic content
            clean_html_content(soup)

            # Add CDN resources
            head = soup.find('head')
            if head:
                cdn_jquery = soup.new_tag('script', src='https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js')
                splide_css = soup.new_tag('link', rel='stylesheet', href='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css')
                splide_js = soup.new_tag('script', src='https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js')
                head.insert(0, cdn_jquery)
                head.append(splide_css)
                head.append(splide_js)

            # SEO OPTIMIZATION
            if seo_enabled and seo_service:
                try:
                    print(f"🔍 Running SEO optimization for {filename}")
                    
                    # Extract page title from filename or title tag
                    page_title = soup.find('title')
                    if page_title and page_title.string:
                        page_title = page_title.string.strip()
                    else:
                        page_title = os.path.splitext(filename)[0].replace('-', ' ').title()
                    
                    # Run SEO optimization
                    seo_result = seo_service.analyze_and_optimize_page(
                        str(soup), 
                        page_title, 
                        business_type, 
                        target_location
                    )
                    
                    # Update soup with optimized HTML
                    soup = BeautifulSoup(seo_result['optimized_html'], 'html.parser')
                    
                    # Store SEO report
                    seo_reports[filename] = {
                        'page_title': page_title,
                        'seo_score': seo_result['seo_score'],
                        'trending_keywords': seo_result['trending_keywords'],
                        'seo_data': seo_result['seo_data'],
                        'recommendations': seo_result['recommendations']
                    }
                    
                    print(f"✅ SEO optimization completed for {filename} - Score: {seo_result['seo_score']['score']}/100")
                    
                except Exception as e:
                    print(f"⚠️ SEO optimization failed for {filename}: {e}")

            # Add WordPress PHP includes
            body = soup.find('body')
            if body:
                original = list(body.contents)
                body.clear()
                body.append(BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
                for item in original:
                    body.append(item)
                body.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))
            else:
                soup.insert(0, BeautifulSoup('<?php get_header(); ?>', 'html.parser'))
                soup.append(BeautifulSoup('<?php get_footer(); ?>', 'html.parser'))

            # Convert to string and fix asset paths
            html_str = str(soup)
            html_str = fix_asset_paths_safe(html_str)

            # Generate safe output filename
            out_filename = generate_safe_filename(filename)
            out_path = os.path.join(output_theme, out_filename)

            # Write the file safely
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html_str)
            
            processed_files.append({
                'original': filename,
                'output': out_filename,
                'path': out_path
            })
            
            print(f"Created: {out_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            # Create a basic fallback file
            create_fallback_page(filename, output_theme)
            continue
    
    # Generate SEO report if SEO was enabled
    seo_report_url = None
    if seo_enabled and seo_reports:
        # Create unique folder name
        import datetime
        folder_name = f"{output_theme}-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"


        folder_name = generate_seo_report(output_theme, seo_reports)
        # report_folder = os.path.join(SEO_FOLDER, folder_name)
        # os.makedirs(report_folder, exist_ok=True)
        
        # # Save the file in the subfolder
        # seo_reports_file = os.path.join(report_folder, 'SEO-OPTIMIZATION-REPORT.html')  
        # with open(seo_reports_file, 'w', encoding='utf-8') as f:
        #     f.write(report_html)
        
        # Create the URL
        seo_report_url = f"/seo-report/{folder_name}"
    
    return processed_files, seo_reports, seo_report_url



def generate_seo_report(output_theme, seo_reports):
    """Generate comprehensive SEO report"""
    
    # Calculate overall SEO stats
    total_pages = len(seo_reports)
    total_score = sum(report['seo_score']['score'] for report in seo_reports.values())
    average_score = round(total_score / total_pages) if total_pages > 0 else 0
    
    # Count pages by score range
    excellent_pages = sum(1 for report in seo_reports.values() if report['seo_score']['score'] >= 80)
    good_pages = sum(1 for report in seo_reports.values() if 60 <= report['seo_score']['score'] < 80)
    fair_pages = sum(1 for report in seo_reports.values() if 40 <= report['seo_score']['score'] < 60)
    poor_pages = sum(1 for report in seo_reports.values() if report['seo_score']['score'] < 40)
    
    # Collect all trending keywords
    all_keywords = []
    for report in seo_reports.values():
        all_keywords.extend(report.get('trending_keywords', []))
    
    # Count keyword frequency
    keyword_freq = {}
    for keyword in all_keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Generate HTML report
    report_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Optimization Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f8fafc;
            color: #1e293b;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5rem; }}
        .header p {{ margin: 10px 0 0; opacity: 0.9; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{ color: #64748b; font-weight: 500; }}
        .excellent {{ color: #22c55e; }}
        .good {{ color: #3b82f6; }}
        .fair {{ color: #f59e0b; }}
        .poor {{ color: #ef4444; }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #1e293b;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .page-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: all 0.2s;
        }}
        .page-card:hover {{ box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }}
        .page-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .score-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            color: white;
            margin-bottom: 15px;
        }}
        .recommendations {{
            background: #f1f5f9;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .recommendations ul {{ margin: 0; padding-left: 20px; }}
        .recommendations li {{ margin-bottom: 5px; }}
        .keywords-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .keyword-item {{
            background: #f1f5f9;
            padding: 10px 15px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .keyword-badge {{
            background: #6366f1;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
        }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> SEO Optimization Report</h1>
            <p>AI-Powered SEO Analysis with Trending Keywords Integration</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number excellent">{average_score}</div>
                <div class="stat-label">Average SEO Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_pages}</div>
                <div class="stat-label">Pages Optimized</div>
            </div>
            <div class="stat-card">
                <div class="stat-number excellent">{excellent_pages}</div>
                <div class="stat-label">Excellent Pages (80+)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number good">{good_pages}</div>
                <div class="stat-label">Good Pages (60-79)</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Score Distribution</h2>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
                <div style="text-align: center;">
                    <div class="excellent" style="font-size: 2rem; font-weight: bold;">{excellent_pages}</div>
                    <div>Excellent (80-100)</div>
                    <div class="progress-bar">
                        <div class="progress-fill excellent" style="width: {(excellent_pages/total_pages)*100 if total_pages > 0 else 0}%; background: #22c55e;"></div>
                    </div>
                </div>
                <div style="text-align: center;">
                    <div class="good" style="font-size: 2rem; font-weight: bold;">{good_pages}</div>
                    <div>Good (60-79)</div>
                    <div class="progress-bar">
                        <div class="progress-fill good" style="width: {(good_pages/total_pages)*100 if total_pages > 0 else 0}%; background: #3b82f6;"></div>
                    </div>
                </div>
                <div style="text-align: center;">
                    <div class="fair" style="font-size: 2rem; font-weight: bold;">{fair_pages}</div>
                    <div>Fair (40-59)</div>
                    <div class="progress-bar">
                        <div class="progress-fill fair" style="width: {(fair_pages/total_pages)*100 if total_pages > 0 else 0}%; background: #f59e0b;"></div>
                    </div>
                </div>
                <div style="text-align: center;">
                    <div class="poor" style="font-size: 2rem; font-weight: bold;">{poor_pages}</div>
                    <div>Poor (0-39)</div>
                    <div class="progress-bar">
                        <div class="progress-fill poor" style="width: {(poor_pages/total_pages)*100 if total_pages > 0 else 0}%; background: #ef4444;"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Top Trending Keywords Integrated</h2>
            <div class="keywords-grid">
"""
    
    for keyword, count in top_keywords:
        report_html += f"""
                <div class="keyword-item">
                    <span>{keyword}</span>
                    <span class="keyword-badge">{count}</span>
                </div>
"""
    
    report_html += """
            </div>
        </div>
        
        <div class="section">
            <h2>📄 Individual Page Reports</h2>
"""
    
    # Sort pages by score (highest first)
    sorted_pages = sorted(seo_reports.items(), key=lambda x: x[1]['seo_score']['score'], reverse=True)
    
    for filename, report in sorted_pages:
        score = report['seo_score']['score']
        status = report['seo_score']['status']
        color = report['seo_score']['color']
        
        report_html += f"""
            <div class="page-card">
                <div class="page-title">{report['page_title']}</div>
                <span class="score-badge" style="background-color: {color};">{score}/100 - {status}</span>
                
                <div style="margin: 15px 0;">
                    <strong>Focus Keywords:</strong> {', '.join(report['seo_data'].get('focus_keywords', []))}
                </div>
                
                <div style="margin: 15px 0;">
                    <strong>Trending Keywords Used:</strong> {', '.join(report['trending_keywords'][:5])}
                </div>
                
                <div class="recommendations">
                    <strong>SEO Recommendations:</strong>
                    <ul>
"""
        
        for recommendation in report['recommendations'][:3]:
            report_html += f"<li>{recommendation}</li>"
        
        report_html += """
                    </ul>
                </div>
            </div>
"""
    
    report_html += """
        </div>
        
        <div class="section">
            <h2> Optimization Summary</h2>
            <p><strong> SEO Elements Added:</strong></p>
            <ul>
                <li>AI-generated meta titles and descriptions optimized for trending keywords</li>
                <li>Schema.org JSON-LD structured data markup</li>
                <li>Open Graph and Twitter Card meta tags for social sharing</li>
                <li>Keyword-optimized alt text for images</li>
                <li>Mobile-friendly viewport configuration</li>
                <li>Search engine crawler optimization (robots, googlebot, bingbot)</li>
                <li>Performance and accessibility enhancements</li>
            </ul>
            
            <p><strong> Next Steps:</strong></p>
            <ul>
                <li>Monitor search rankings for targeted keywords</li>
                <li>Set up Google Search Console and Analytics</li>
                <li>Create quality backlinks to improve domain authority</li>
                <li>Regularly update content with fresh trending keywords</li>
                <li>Optimize page loading speed and Core Web Vitals</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    import datetime
    import os

    # Make sure the output_theme directory exists
    os.makedirs(output_theme, exist_ok=True)

    # Save SEO report
    report_path = os.path.join(output_theme, 'SEO-OPTIMIZATION-REPORT.html')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)

    folder_name = f"{output_theme}-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Also save JSON data for programmatic access
    json_path = os.path.join(output_theme, 'seo-data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_path, f, indent=2, ensure_ascii=False)

    print(f" SEO Report generated: {report_path}")
    return report_html


def clean_html_content(soup):
    """
    Clean HTML content to prevent PHP syntax errors including XML version declarations
    """
    # Remove or escape potentially problematic content
    for tag in soup.find_all():
        # Clean attributes that might cause issues
        if tag.attrs:
            for attr_name, attr_value in list(tag.attrs.items()):
                if isinstance(attr_value, str):
                    # Remove or escape problematic characters including XML declarations
                    attr_value = attr_value.replace('<?xml', '&lt;?xml')
                    attr_value = attr_value.replace('<?', '&lt;?')
                    attr_value = attr_value.replace('?>', '?&gt;')
                    tag.attrs[attr_name] = attr_value
        
        # Clean text content
        if tag.string:
            text = str(tag.string)
            # Escape XML declarations and PHP tags in content
            text = text.replace('<?xml', '&lt;?xml')
            text = text.replace('<?', '&lt;?')
            text = text.replace('?>', '?&gt;')
            tag.string.replace_with(text)
    
    # Remove XML processing instructions that might cause issues
    for pi in soup.find_all(string=re.compile(r'<\?xml.*?\?>')):
        pi.extract()


def generate_safe_filename(filename):
    """
    Generate safe PHP filename from HTML filename
    """
    base_name = os.path.splitext(filename)[0]
    
    # Clean the filename
    safe_name = base_name.lower()
    safe_name = re.sub(r'[^a-z0-9\-_]', '-', safe_name)  # Replace special chars with hyphens
    safe_name = re.sub(r'-+', '-', safe_name)  # Remove multiple hyphens
    safe_name = safe_name.strip('-')  # Remove leading/trailing hyphens
    
    # Generate PHP filename
    if filename.lower() == 'index.html':
        return 'index.php'
    else:
        return f"page-{safe_name}.php"


def create_fallback_page(original_filename, output_theme):
    """
    Create a basic fallback page if processing fails
    """
    try:
        base_name = os.path.splitext(original_filename)[0]
        safe_filename = generate_safe_filename(original_filename)
        
        fallback_content = f"""<?php get_header(); ?>

<main id="main" class="site-main">
    <div class="container">
        <div class="error-notice">
            <h1>Page Processing Error</h1>
            <p>There was an issue processing the original Webflow page: <strong>{original_filename}</strong></p>
            <p>This is a fallback page. Please check the original HTML file for syntax issues.</p>
            <p><a href="<?php echo home_url(); ?>">Back to Home</a></p>
        </div>
    </div>
</main>

<style>
.error-notice {{
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 20px;
    margin: 20px 0;
}}
.error-notice h1 {{
    color: #856404;
    margin-top: 0;
}}
</style>

<?php get_footer(); ?>"""
        
        fallback_path = os.path.join(output_theme, safe_filename)
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(fallback_content)
        
        print(f"Created fallback for {original_filename} to {safe_filename}")
        
    except Exception as e:
        print(f"Failed to create fallback for {original_filename}: {e}")


def fix_asset_paths_safe(html):
    """
    CORRECTED: Safer version of fix_asset_paths that avoids PHP syntax errors
    """
    try:
        # First, remove any XML declarations that might cause issues
        html = re.sub(r'<\?xml[^>]*\?>', '', html)
        
        # Fix asset folder paths
        pattern = re.compile(r'(src|href)="[^"]*((?:' + '|'.join(ASSET_FOLDERS) + r')/([^"/\?#]+))(\?[^\"]*)?"')

        def replacer(match):
            try:
                attr, folder_path, raw_filename = match.group(1), match.group(2), match.group(3)
                folder = folder_path.split('/')[0]
                parts = raw_filename.split('.')
                if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
                    raw_filename = '.'.join(parts[:-2] + parts[-1:])
                
                # FIXED: Proper PHP syntax with escaped quotes
                return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'
            except Exception:
                return match.group(0)  # Return original if replacement fails

        html = pattern.sub(replacer, html)

        # Fix srcset attributes
        def srcset_replacer(match):
            try:
                parts = [p.strip() for p in match.group(1).split(',')]
                new_parts = []
                for part in parts:
                    url, size = part.rsplit(' ', 1) if ' ' in part else (part, '')
                    folder = url.split('/')[0]
                    filename = os.path.basename(url)
                    segments = filename.split('.')
                    if len(segments) > 2 and re.fullmatch(r'[a-f0-9]{8,}', segments[-2]):
                        filename = '.'.join(segments[:-2] + segments[-1:])
                    if folder in ASSET_FOLDERS:
                        new_url = f'<?php echo get_template_directory_uri(); ?>/{folder}/{filename}'
                        new_parts.append(f'{new_url} {size}'.strip())
                    else:
                        new_parts.append(part)
                return f'srcset="{", ".join(new_parts)}"'
            except Exception:
                return match.group(0)

        html = re.sub(r'srcset="([^"]+)"', srcset_replacer, html)

        # Fix custom data attributes
        def custom_data_attr_replacer(match):
            try:
                attr, path = match.groups()
                folder = path.split('/')[0]
                filename = os.path.basename(path)
                if folder in ASSET_FOLDERS:
                    return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{filename}"'
                return match.group(0)
            except Exception:
                return match.group(0)

        html = re.sub(r'(data-poster-url|data-video-urls)="([^"]+)"', custom_data_attr_replacer, html)

        # FIXED: Internal page links with proper escaping
        def internal_link_replacer(match):
            try:
                href_value = match.group(1)
                if href_value.lower() == 'index.html':
                    return 'href="<?php echo home_url(\'/\'); ?>"'
                else:
                    page_slug = os.path.splitext(os.path.basename(href_value))[0]
                    # Clean the slug safely
                    page_slug = re.sub(r'[^a-z0-9\-_]', '-', page_slug.lower())
                    page_slug = re.sub(r'-+', '-', page_slug).strip('-')
                    return f'href="<?php echo home_url(\'/{page_slug}/\'); ?>"'
            except Exception:
                return match.group(0)

        html = re.sub(r'href="([^"]+\.html)"', internal_link_replacer, html)

        # FIXED: CSS url() references with proper escaping
        def style_url_replacer(match):
            try:
                path = match.group(1)
                folder = path.split('/')[0]
                filename = os.path.basename(path)
                if folder in ASSET_FOLDERS:
                    return f'url(<?php echo get_template_directory_uri(); ?>/{folder}/{filename})'
                return match.group(0)
            except Exception:
                return match.group(0)

        html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)

        # Replace CDN links (these are safe)
        html = re.sub(r'<link href="[^"]*splide.min.css[^"]*"[^>]*>',
                      '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
        html = re.sub(r'<script src="[^"]*splide.min.js[^"]*"></script>',
                      '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

        return html

    except Exception as e:
        print(f"Error in fix_asset_paths_safe: {e}")
        return html  # Return original HTML if processing fails


def extract_webflow_pages(webflow_temp_dir):
    """
    Extract all pages from Webflow export and prepare data for WordPress page creation
    """
    pages_data = []
    
    for filename in os.listdir(webflow_temp_dir):
        if not filename.endswith('.html'):
            continue
            
        filepath = os.path.join(webflow_temp_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            # Extract page information
            page_title = ""
            page_slug = ""
            meta_description = ""
            
            # Get title from <title> tag or <h1>
            title_tag = soup.find('title')
            if title_tag:
                page_title = title_tag.get_text().strip()
            else:
                h1_tag = soup.find('h1')
                if h1_tag:
                    page_title = h1_tag.get_text().strip()
                else:
                    page_title = os.path.splitext(filename)[0].replace('-', ' ').title()
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                meta_description = meta_desc.get('content', '')
            
            # Generate slug from filename
            base_name = os.path.splitext(filename)[0].lower().replace(' ', '-')
            page_slug = base_name if base_name != 'index' else 'home'
            
            # Determine template file name
            template_name = 'index.php' if filename == 'index.html' else f"page-{base_name}.php"
            
            # Check if this should be the front page
            is_front_page = filename.lower() == 'index.html'
            
            pages_data.append({
                'filename': filename,
                'title': page_title,
                'slug': page_slug,
                'template': template_name,
                'meta_description': meta_description,
                'is_front_page': is_front_page,
                'content': f'<!-- Content will be loaded from {template_name} -->'
            })
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    return pages_data


def generate_page_creator_plugin_from_template(pages_data, theme_name):
    """
    Generate page creator plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-page-creator.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        print("Please create templates/webflow-page-creator.php")
        return None
    
    # Prepare the JSON data with safe escaping
    pages_json = json.dumps(pages_data, ensure_ascii=True, separators=(',', ':'))
    pages_json = pages_json.replace('\\', '\\\\').replace("'", "\\'")
    
    # Replace placeholders in template
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Auto Page Creator')
    plugin_code = plugin_code.replace('{{PAGES_JSON}}', pages_json)
    
    return plugin_code


def create_page_creator_plugin_files_template(output_theme, theme_name, pages_data):
    """
    Create the auto-page creator plugin files using template approach
    """
    # Create plugin directory
    plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-page-creator')
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Debug pages data before processing
    print(f"Processing {len(pages_data)} pages for creation:")
    for i, page in enumerate(pages_data[:3]):  # Show first 3 for debugging
        print(f"   {i+1}. {page.get('title', 'No title')} ({page.get('slug', 'No slug')})")
    if len(pages_data) > 3:
        print(f"   ... and {len(pages_data) - 3} more pages")
    
    # Generate plugin code from template
    plugin_code = generate_page_creator_plugin_from_template(pages_data, theme_name)
    
    if not plugin_code:
        print("Failed to generate page creator plugin from template")
        return None
    
    # Save the main plugin file
    plugin_file_path = os.path.join(plugin_dir, 'webflow-page-creator.php')
    with open(plugin_file_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    # Create plugin readme
    readme_content = f"""=== {theme_name} Auto Page Creator ===
Contributors: webflow-converter
Tags: pages, auto-create, webflow, automation
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Automatically creates WordPress pages for all your converted Webflow pages.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
Pages are created automatically on theme activation.
Check Tools > Webflow Pages for status.

== Changelog ==
= 1.0.0 =
* Initial release"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    page_creator_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-page-creator.zip')
    
    with zipfile.ZipFile(page_creator_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-page-creator/webflow-page-creator.php')
        zipf.write(readme_path, 'webflow-page-creator/readme.txt')
    
    print(f"Created Page Creator plugin from template: {page_creator_zip_path}")
    
    # Debug output for pages
    print(f"Pages to be created:")
    for page in pages_data:
        print(f"   - {page['title']} ({page['slug']}) -> {page.get('template', 'default template')}")
    
    return page_creator_zip_path


@app.route('/convert', methods=['POST'])
def convert():

    import os

    theme_name = request.form.get('theme_name', 'converted-theme')
    webflow_zip = request.files.get('webflow_zip')
    screenshot_file = request.files.get("screenshot")
    include_cms = True
    api_token = request.form.get('api_token', 'a0c4e41f662c0fa945996569e7e9ded64e0c6fd66bca66176e020e2df3910a6a')
    site_id = request.form.get('site_id')
    
    print(f"tokennnn {include_cms} {api_token} {site_id}")
    print(f"Received screenshot_file: {screenshot_file}")
    if not webflow_zip:
        return jsonify({"error": "Missing Webflow ZIP"}), 400


    # SEO-related parameters
    enable_seo = request.form.get('enable_seo') == 'on'
    business_type = request.form.get('business_type', '')
    target_location = request.form.get('target_location', '')
    openai_api_key = request.form.get('openai_api_key', '')
    serp_api_key = request.form.get('serp_api_key', '')

    print(f"🚀 Conversion started - SEO: {enable_seo}, Business: {business_type}, Location: {target_location}")

    theme_name = secure_filename(theme_name)
    temp_base = tempfile.mkdtemp()
    zip_path = os.path.join(temp_base, theme_name + ".zip")
    temp_dir = os.path.join(temp_base, 'webflow-temp')
    output_theme = os.path.join(temp_base, theme_name)

    if os.path.exists(output_theme):
        shutil.rmtree(output_theme)

    os.makedirs(output_theme, exist_ok=True)

    # FIRST: Copy the starter theme
    shutil.copytree(STARTER_THEME, output_theme, dirs_exist_ok=True)
    
    # THEN: Handle screenshot upload (this will overwrite any existing screenshot from starter theme)
    screenshot_dest = os.path.join(output_theme, "screenshot.png")  
    
    if screenshot_file and screenshot_file.filename != "":
        if os.path.exists(screenshot_dest):
            os.remove(screenshot_dest)
        screenshot_file.save(screenshot_dest)
        print(f"Custom screenshot uploaded and saved at: {screenshot_dest}")
        print(f"Screenshot file size: {os.path.getsize(screenshot_dest)} bytes")
    else:
        if not os.path.exists(screenshot_dest):
            default_thumbnail = os.path.join(BASE_DIR, "assets", "screenshot.png")
            if os.path.exists(default_thumbnail):
                print(f"Using default thumbnail: {default_thumbnail}")
                shutil.copy2(default_thumbnail, screenshot_dest)
                print(f"Default thumbnail saved at: {screenshot_dest}")
            else:
                print("Default thumbnail not found!")
        else:
            print("Using screenshot from starter theme")

    # Process Webflow ZIP
    zip_path = os.path.join(temp_base, secure_filename(webflow_zip.filename))
    webflow_zip.save(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Extract Webflow pages data for auto-creation
    pages_data = extract_webflow_pages(temp_dir)
    print(f"Detected {len(pages_data)} pages for auto-creation: {[p['title'] for p in pages_data]}")
    
    # Copy assets
    for folder in ASSET_FOLDERS:
        src = os.path.join(temp_dir, folder)
        dest = os.path.join(output_theme, folder)
        if os.path.exists(src):
            shutil.copytree(src, dest, dirs_exist_ok=True)
    
    # SAFE HTML PROCESSING (prevents PHP syntax errors)
    # processed_files = process_html_files_safe(temp_dir, output_theme)

    # SAFE HTML PROCESSING WITH SEO OPTIMIZATION
    processed_files, seo_reports, seo_report_url = process_html_files_with_seo(
        temp_dir, 
        output_theme, 
        enable_seo, 
        business_type, 
        target_location, 
        openai_api_key, 
        serp_api_key
    )

    print(f"Processed {len(processed_files)} HTML files successfully")
    if enable_seo:
        print(f"📊 SEO optimization completed for {len(seo_reports)} pages")
        

    
    # Update pages_data to include only successfully processed files
    if processed_files:
        processed_filenames = [f['original'] for f in processed_files]
        pages_data = [page for page in pages_data if page.get('filename') in processed_filenames]
        print(f"{len(pages_data)} pages ready for WordPress creation")

    components_css_path = os.path.join(output_theme, 'css', 'components.css')
    override_css = '\n.w-section {\n  display: none !important;\n}\n'
    if os.path.exists(components_css_path):
        with open(components_css_path, 'r+', encoding='utf-8') as f:
            existing_css = f.read()
            if '.w-section' not in existing_css:
                f.write(override_css)
    else:
        os.makedirs(os.path.dirname(components_css_path), exist_ok=True)
        with open(components_css_path, 'w', encoding='utf-8') as f:
            f.write(override_css)

    update_style_css_with_theme_name(output_theme, theme_name)

    # Process CMS if requested
    cms_data = None

    if include_cms and api_token and site_id:
        cms_data = fetch_webflow_cms(api_token, site_id)
    else:
        cms_data = extract_webflow_collections(temp_dir)

    # CREATE CMS IMPORTER PLUGIN (if CMS data exists)
    if cms_data:
        # Save raw CMS data
        cms_dir = os.path.join(output_theme, 'cms-data')
        os.makedirs(cms_dir, exist_ok=True)
        with open(os.path.join(cms_dir, 'collections.json'), 'w') as f:
            json.dump(cms_data, f, indent=2)
        
        # Create plugin directories
        plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer')
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Generate plugin files
        plugin_code = generate_plugin_from_template(cms_data, theme_name)
        
        # 1. Save the main plugin file
        plugin_file_path = os.path.join(plugin_dir, 'webflow-importer.php')
        with open(plugin_file_path, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
        
        # 2. Create readme.txt
        readme_content = f"""=== {theme_name} CMS Importer ===
Contributors: webflow-to-wp
Tags: webflow, import, cms, migration, auto-import
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Automatically imports Webflow CMS content into WordPress.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
CMS import runs automatically on plugin activation.

== Requirements ==
* Advanced Custom Fields (recommended)
* WordPress 5.0 or newer
* PHP 7.4 or newer

== Changelog ==
= 1.0.0 =
* Initial release"""
        
        readme_path = os.path.join(plugin_dir, 'readme.txt')
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # 3. Create the ZIP archive
        importer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-importer.zip')
        
        with zipfile.ZipFile(importer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(plugin_file_path, 'webflow-importer/webflow-importer.php')
            zipf.write(readme_path, 'webflow-importer/readme.txt')
        
        print(f"Created CMS importer: {importer_zip_path}")
        
        # Verify collections data for debugging
        print(f"CMS Collections to import: {len(cms_data)}")
        for collection in cms_data:
            collection_name = collection.get('name', collection.get('slug', 'Unknown'))
            item_count = len(collection.get('items', []))
            print(f"   - {collection_name}: {item_count} items")
    else:
        print("No CMS data found - skipping CMS importer creation")

    # CREATE AUTO PAGE CREATOR PLUGIN (Template-based)
    if pages_data:
        page_creator_zip = create_page_creator_plugin_files_template(output_theme, theme_name, pages_data)
        if page_creator_zip:
            print(f"Created Template-based Page Creator plugin: {page_creator_zip}")
        else:
            print("Failed to create Page Creator plugin - check template file exists")
    else:
        print("No pages data found - skipping Page Creator plugin")
    
    # CREATE AUTO-RESPONSE EMAIL PLUGIN (Always create, auto-installs)
    auto_response_zip = create_auto_response_plugin_files(output_theme, theme_name)
    if auto_response_zip:
        print(f"Created Auto-Response Email plugin: {auto_response_zip}")
    else:
        print("Failed to create Auto-Response Email plugin")


    # CREATE CONTACT FORM HANDLER PLUGIN (Always create, auto-installs)
    contact_form_zip = create_contact_form_plugin_files(output_theme, theme_name)
    if contact_form_zip:
        print(f"Created Contact Form Handler plugin: {contact_form_zip}")
    else:
        print("Failed to create Contact Form Handler plugin")
        
    
    # UPDATE FUNCTIONS.PHP FOR AUTO-INSTALLATION (Updated to include page creator)
    update_functions_php_for_auto_plugin_install_with_contact_forms(
        output_theme, 
        theme_name, 
        cms_data is not None, 
        len(pages_data) > 0 if pages_data else False
    )

    # Create installation guides with SEO information
    # create_plugin_installation_guide_auto_install_with_seo(
    #     output_theme, 
    #     theme_name, 
    #     cms_data is not None, 
    #     len(pages_data) > 0 if pages_data else False,
    #     enable_seo,
    #     seo_reports if enable_seo else {}
    # )

    create_plugin_installation_guide_auto_install_with_contact_forms(
        output_theme, 
        theme_name, 
        cms_data is not None, 
        len(pages_data) > 0 if pages_data else False
    )

    # Final theme packaging
    final_zip_path = os.path.join(temp_base, theme_name + ".zip")
    shutil.make_archive(final_zip_path.replace(".zip", ""), "zip", output_theme)

    response = make_response(send_file(
        final_zip_path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=theme_name + ".zip"
    ))
    response.headers["X-Temp-Zip-Path"] = final_zip_path

    # Create a unique folder name
    if seo_report_url:
        import os
        from datetime import datetime
        
        folder_name = f"{theme_name}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_folder = os.path.join(SEO_FOLDER, folder_name)
        os.makedirs(report_folder, exist_ok=True)
        
        # Generate your HTML content (you'll need to create this)
        report_html= generate_seo_report(theme_name, seo_reports)
    
        
        # Save the HTML file
        report_file_path = os.path.join(report_folder, 'SEO-OPTIMIZATION-REPORT.html')
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        # Create the URL that matches your Flask route
        seo_report_url = f"/seo-report/{folder_name}"
        response.headers["X-SEO-Report-URL"] = seo_report_url

    return response

def create_plugin_installation_guide_auto_install_with_contact_forms(output_theme, theme_name, has_cms, has_pages):
    """
    Create updated installation guide for auto-installing plugins including contact form handler
    """
    
    installation_guide = f"""
# {theme_name} - AUTO-INSTALL Setup Guide

## AUTOMATIC PLUGIN INSTALLATION + COMPLETE CONTACT MANAGEMENT

Your theme includes 4 AUTO-INSTALLING PLUGINS that set up everything automatically when you activate the theme!

### What Happens Automatically:

1. Theme Activation - All plugins install automatically
2. WordPress Pages - Created automatically from Webflow pages  
3. Auto-Response Mailer - Starts working immediately  
4. Contact Form Handler - Monitors all contact forms automatically
5. CMS Content - Imported automatically (if applicable)
6. Email Templates - Pre-configured and ready
7. Form Detection - All contact forms work instantly with dual handling

## Included Auto-Installing Plugins

### Auto Page Creator (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & CREATES PAGES
Purpose: Automatically creates WordPress pages for all Webflow pages

What You Get:
- All Webflow pages become WordPress pages instantly
- Correct page templates assigned automatically
- Front page (index.html) set up automatically
- SEO-friendly URLs and meta descriptions
- Zero manual page creation needed

### Auto-Response Email Mailer (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & ACTIVATES
Purpose: Sends beautiful response emails to ALL contact form submissions

What You Get:
- Instant auto-response emails (no setup needed)
- Professional email templates  
- Works with ANY contact form automatically
- Visual email designer for customization
- Logo and branding support

Customization: Go to Settings > Auto-Response Mailer (optional)

### Contact Form Handler (ALWAYS INCLUDED) - NEW!
Status: AUTO-INSTALLS & MONITORS CONTACT PAGES
Purpose: Universal contact form processor with complete admin management

What You Get:
- Automatic detection of contact pages (contact, contact-us, etc.)
- Handles ANY HTML form with email field
- Saves all submissions to WordPress admin ("Contact Forms" menu)
- Email notifications for new submissions  
- No configuration needed - works immediately
- AJAX form submission (no page reload)
- Complete admin interface to view and manage submissions
- One-click reply to form submitters
- Search and filter submissions

Customization: Go to Contact Forms > Settings (optional)

"""

    if has_cms:
        installation_guide += f"""### {theme_name} CMS Importer (CMS THEMES)
Status: AUTO-INSTALLS & RUNS IMPORT
Purpose: Imports all Webflow CMS content automatically

What You Get:
- All CMS collections imported as custom post types
- Dynamic content replaces static Webflow content  
- Advanced Custom Fields integration
- Progress tracking and error reporting

Requirement: Advanced Custom Fields plugin (install first)

"""

    installation_guide += """
## SUPER QUICK SETUP (2 Minutes)

### Step 1: Upload & Activate Theme (30 seconds)
Appearance > Themes > Add New > Upload Theme
Upload your theme ZIP
Click "Activate"

### Step 2: Everything Auto-Installs (60 seconds)  
Auto Page Creator - Creates all WordPress pages automatically
Auto-Response Mailer - Installs automatically
Contact Form Handler - Installs automatically
CMS Importer - Installs automatically (if CMS theme)
Success notice appears in admin

### Step 3: Verify Pages Created (30 seconds)
Go to Pages > All Pages
See all your Webflow pages now in WordPress!
Check Tools > Webflow Pages for status

### Step 4: Test Contact Forms (30 seconds)
Visit any contact page
Fill out and submit a contact form
Check "Contact Forms > All Submissions" in admin
Check your email for notification!

### Step 5: Test Auto-Response (30 seconds)
Go to Settings > Auto-Response Mailer
Click "Send Test Email"  
Enter your email
Check your inbox!

### Step 6: Done!
Your complete WordPress site is ready with:
- All pages created automatically
- Contact forms with dual processing (admin storage + email)
- Professional auto-response emails
- Complete form submission management system
- CMS content imported (if applicable)

## ZERO-CONFIGURATION FEATURES

### Automatic Page Creation
WordPress pages created automatically:
- index.html - Home page (set as front page)
- about.html - About page (/about/)
- contact.html - Contact page (/contact/)
- services.html - Services page (/services/)
- Any-page.html - WordPress page (/any-page/)

### Smart Contact Form Detection
Automatically handles forms on pages containing:
- "contact" (contact.html, contact-us.html)
- "contact-us" 
- "get-in-touch"
- "reach-out"
- Custom keywords (configurable)

### Universal Form Compatibility
Works automatically with:
- HTML contact forms - No setup needed
- Contact Form 7 - Enhanced with dual processing
- Gravity Forms - Enhanced with dual processing  
- Formidable Forms - Enhanced with dual processing
- Any form with email field - No setup needed

### Triple Form Processing System
Every contact form submission gets:
1. **Admin Storage**: Saved to "Contact Forms > All Submissions"
2. **Email Notification**: Instant alert to site administrator  
3. **Auto-Response**: Professional reply to form submitter
4. **No Duplicates**: Smart handling prevents double-processing

### Complete Admin Management
- View all form submissions in organized list
- See submission details, page source, timestamp
- Reply directly to submitters via email
- Search and filter submissions
- Export submission data
- Track form conversion rates

### SEO Preservation
- Page titles preserved from Webflow
- Meta descriptions maintained
- Clean, SEO-friendly URLs

## You're All Set!

Your Webflow theme is now a complete WordPress website with:
- All pages created automatically - No manual page creation needed
- Universal contact form handling with complete admin management
- Instant auto-response emails for ALL contact forms
- Professional email templates with your branding  
- Complete form submission tracking and management system
- Zero configuration - works immediately
- CMS content imported (if applicable)
- WordPress best practices implemented

Result: A fully functional WordPress website that mirrors your Webflow design with professional contact form management, complete admin interface, and enhanced email handling!

## Admin Menu Locations:

After theme activation, find these in WordPress admin:
- **Contact Forms** - Main menu (view all submissions)
- **Contact Forms > All Submissions** - Form submission manager
- **Contact Forms > Settings** - Configure form handling
- **Settings > Auto-Response Mailer** - Email template designer
- **Tools > Webflow Pages** - Page creation status (if applicable)

Theme converted by Webflow to WordPress Converter with Complete Contact Management System
"""

    # Save the updated installation guide
    guide_path = os.path.join(output_theme, 'AUTO-INSTALL-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Create simple setup card
    setup_card = f"""
{theme_name} - INSTANT SETUP WITH COMPLETE CONTACT MANAGEMENT
============================================================

STEP 1: Activate Theme (30 sec)
   Upload ZIP - Activate - Done!

STEP 2: Everything Auto-Installs (60 sec)  
   WordPress pages created automatically
   Auto-Response Mailer installed
   Contact Form Handler installed (NEW!)
   CMS Importer installed (if CMS)

STEP 3: Verify Everything Works (60 sec)
   Pages > All Pages - See all your pages!
   Contact Forms > All Submissions - Form management
   Settings > Auto-Response Mailer - Test email

STEP 4: Test Contact System (30 sec)
   Visit contact page - Submit form
   Check "Contact Forms" menu for submission
   Check email for notifications
   Check submitter email for auto-response

RESULT: Complete WordPress site with professional contact management!

TOTAL TIME: 3 MINUTES
New Feature: Complete contact form admin system!

For details, see AUTO-INSTALL-GUIDE.md
"""
    
    setup_card_path = os.path.join(output_theme, 'INSTANT-SETUP.txt')
    with open(setup_card_path, 'w', encoding='utf-8') as f:
        f.write(setup_card)
    
    print(f"Created auto-install guides (with contact form handler):")
    print(f"  - {guide_path}")
    print(f"  - {setup_card_path}")
    
    return guide_path

def create_plugin_installation_guide_auto_install_with_seo(output_theme, theme_name, has_cms, has_pages, has_seo, seo_reports):
    """
    Create updated installation guide including SEO optimization information
    """
    
    seo_summary = ""
    if has_seo and seo_reports:
        total_pages = len(seo_reports)
        avg_score = sum(report['seo_score']['score'] for report in seo_reports.values()) / total_pages if total_pages > 0 else 0
        excellent_pages = sum(1 for report in seo_reports.values() if report['seo_score']['score'] >= 80)
        
        seo_summary = f"""
### 🚀 SEO OPTIMIZATION RESULTS

Your theme has been optimized with AI-powered SEO:

- **{total_pages} pages optimized** with trending keywords
- **Average SEO Score: {avg_score:.0f}/100**
- **{excellent_pages} pages** achieved excellent scores (80+)
- **Trending keywords integrated** from Google Trends and AI analysis
- **Schema markup, Open Graph, and Twitter Cards** added automatically
- **Mobile optimization** and search engine crawler configuration
- **Detailed SEO report** included: `SEO-OPTIMIZATION-REPORT.html`

"""
    
    installation_guide = f"""
# {theme_name} - AUTO-INSTALL Setup Guide {' + AI SEO OPTIMIZATION' if has_seo else ''}

## AUTOMATIC PLUGIN INSTALLATION + PAGE CREATION{' + SEO OPTIMIZATION' if has_seo else ''}

Your theme includes {'4' if has_seo else '3'} AUTO-INSTALLING PLUGINS that set up everything automatically when you activate the theme!

{seo_summary}

### What Happens Automatically:

1. **Theme Activation** - All plugins install automatically
2. **WordPress Pages** - Created automatically from Webflow pages  
3. **Auto-Response Mailer** - Starts working immediately  
{'4. **SEO Optimization** - AI-powered SEO with trending keywords applied' if has_seo else ''}
{'5. **CMS Content** - Imported automatically (if applicable)' if has_cms else '4. **CMS Content** - Imported automatically (if applicable)' if has_cms else ''}
{'6. **Email Templates** - Pre-configured and ready' if has_seo else '5. **Email Templates** - Pre-configured and ready'}
{'7. **Form Detection** - All contact forms work instantly' if has_seo else '6. **Form Detection** - All contact forms work instantly'}

## Included Auto-Installing Plugins

### Auto Page Creator (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & CREATES PAGES
Purpose: Automatically creates WordPress pages for all Webflow pages

What You Get:
- All Webflow pages become WordPress pages instantly
- Correct page templates assigned automatically
- Front page (index.html) set up automatically
- SEO-friendly URLs and meta descriptions
- Zero manual page creation needed
{f'- **AI-optimized SEO** for each page with trending keywords' if has_seo else ''}

### Auto-Response Email Mailer (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & ACTIVATES
Purpose: Sends beautiful response emails to ALL contact form submissions

What You Get:
- Instant auto-response emails (no setup needed)
- Professional email templates  
- Works with ANY contact form automatically
- Visual email designer for customization
- Logo and branding support

Customization: Go to Settings > Auto-Response Mailer (optional)

"""

    if has_seo:
        installation_guide += f"""### 🚀 AI-Powered SEO Optimization (ENABLED)
Status: APPLIED TO ALL PAGES
Purpose: Maximizes search engine visibility with trending keywords

What You Get:
- **AI-generated meta titles and descriptions** optimized for current trends
- **Google Trends keyword integration** for maximum relevance
- **Schema.org structured data** for rich search results
- **Open Graph and Twitter Cards** for social media optimization
- **Image alt text optimization** for accessibility and SEO
- **Mobile-first optimization** with responsive design
- **Page speed optimization** recommendations
- **Detailed SEO scoring** with improvement suggestions

SEO Report: Open `SEO-OPTIMIZATION-REPORT.html` in your theme folder

"""

    if has_cms:
        installation_guide += f"""### {theme_name} CMS Importer (CMS THEMES)
Status: AUTO-INSTALLS & RUNS IMPORT
Purpose: Imports all Webflow CMS content automatically

What You Get:
- All CMS collections imported as custom post types
- Dynamic content replaces static Webflow content  
- Advanced Custom Fields integration
- Progress tracking and error reporting

Requirement: Advanced Custom Fields plugin (install first)

"""

    # Continue with the rest of the installation guide...
    installation_guide += f"""
## SUPER QUICK SETUP ({'2.5' if has_seo else '2'} Minutes)

### Step 1: Upload & Activate Theme (30 seconds)
Appearance > Themes > Add New > Upload Theme
Upload your theme ZIP
Click "Activate"

### Step 2: Everything Auto-Installs (60 seconds)  
Auto Page Creator - Creates all WordPress pages automatically
Auto-Response Mailer - Installs automatically
{'AI SEO Optimization - Applied to all pages automatically' if has_seo else ''}
CMS Importer - Installs automatically (if CMS theme)
Success notice appears in admin

### Step 3: Verify Pages Created (30 seconds)
Go to Pages > All Pages
See all your Webflow pages now in WordPress!
Check Tools > Webflow Pages for status

### Step 4: Test Auto-Response (30 seconds)
Go to Settings > Auto-Response Mailer
Click "Send Test Email"  
Enter your email
Check your inbox!

{f'''### Step 5: Review SEO Report (30 seconds)
Open `SEO-OPTIMIZATION-REPORT.html` from your theme folder
Review individual page SEO scores
Check trending keywords integration
Follow improvement recommendations''' if has_seo else ''}

### Step {'6' if has_seo else '5'}: Done!
Your complete WordPress site is ready with:
- All pages created automatically
- Contact forms sending professional auto-responses
{f'- AI-optimized SEO with trending keywords integrated' if has_seo else ''}
- CMS content imported (if applicable)

## You're All Set!

Your Webflow theme is now a complete WordPress website with:
- All pages created automatically - No manual page creation needed
- Instant auto-response emails for ALL contact forms
- Professional email templates with your branding  
{f'- AI-optimized SEO with trending keywords for maximum visibility' if has_seo else ''}
- Zero configuration - works immediately
- CMS content imported (if applicable)
- WordPress best practices implemented

{f'**SEO Bonus**: Your site is optimized with current trending keywords and AI-generated content for maximum search engine visibility!' if has_seo else ''}

Result: A fully functional WordPress website that mirrors your Webflow design with enhanced functionality{' and SEO optimization' if has_seo else ''}!

Theme converted by Webflow to WordPress Converter with Auto Page Creation{' + AI SEO Optimization' if has_seo else ''}
"""

    # Save the updated installation guide
    guide_path = os.path.join(output_theme, 'AUTO-INSTALL-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Create simple setup card
    setup_card = f"""
{theme_name} - INSTANT SETUP{' + AI SEO' if has_seo else ''}
===============================

STEP 1: Activate Theme (30 sec)
   Upload ZIP - Activate - Done!

STEP 2: Everything Auto-Installs (60 sec)  
   WordPress pages created automatically
   Auto-Response Mailer installed
   {'AI SEO optimization applied to all pages' if has_seo else ''}
   CMS Importer installed (if CMS)

STEP 3: Verify (30 sec)
   Pages > All Pages - See all your pages!
   Settings > Auto-Response Mailer - Test email
   {'SEO-OPTIMIZATION-REPORT.html - View SEO scores' if has_seo else ''}

RESULT: Complete WordPress site ready{' with AI-optimized SEO' if has_seo else ''}!

TOTAL TIME: {'2.5' if has_seo else '2'} MINUTES

For details, see AUTO-INSTALL-GUIDE.md
"""
    
    setup_card_path = os.path.join(output_theme, 'INSTANT-SETUP.txt')
    with open(setup_card_path, 'w', encoding='utf-8') as f:
        f.write(setup_card)
    
    print(f"Created auto-install guides (with {'SEO optimization' if has_seo else 'standard features'}):")
    print(f"  - {guide_path}")
    print(f"  - {setup_card_path}")
    if has_seo:
        print(f"  - SEO-OPTIMIZATION-REPORT.html")
    
    return guide_path

    
# Updated installation guide to include auto page creation
def create_plugin_installation_guide_auto_install_with_pages(output_theme, theme_name, has_cms, has_pages):
    """
    Create updated installation guide for auto-installing plugins including page creator
    """
    
    installation_guide = f"""
# {theme_name} - AUTO-INSTALL Setup Guide

## AUTOMATIC PLUGIN INSTALLATION + PAGE CREATION

Your theme includes 3 AUTO-INSTALLING PLUGINS that set up everything automatically when you activate the theme!

### What Happens Automatically:

1. Theme Activation - All plugins install automatically
2. WordPress Pages - Created automatically from Webflow pages  
3. Auto-Response Mailer - Starts working immediately  
4. CMS Content - Imported automatically (if applicable)
5. Email Templates - Pre-configured and ready
6. Form Detection - All contact forms work instantly

## Included Auto-Installing Plugins

### Auto Page Creator (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & CREATES PAGES
Purpose: Automatically creates WordPress pages for all Webflow pages

What You Get:
- All Webflow pages become WordPress pages instantly
- Correct page templates assigned automatically
- Front page (index.html) set up automatically
- SEO-friendly URLs and meta descriptions
- Zero manual page creation needed

### Auto-Response Email Mailer (ALWAYS INCLUDED)
Status: AUTO-INSTALLS & ACTIVATES
Purpose: Sends beautiful response emails to ALL contact form submissions

What You Get:
- Instant auto-response emails (no setup needed)
- Professional email templates  
- Works with ANY contact form automatically
- Visual email designer for customization
- Logo and branding support

Customization: Go to Settings > Auto-Response Mailer (optional)

"""

    if has_cms:
        installation_guide += f"""### {theme_name} CMS Importer (CMS THEMES)
Status: AUTO-INSTALLS & RUNS IMPORT
Purpose: Imports all Webflow CMS content automatically

What You Get:
- All CMS collections imported as custom post types
- Dynamic content replaces static Webflow content  
- Advanced Custom Fields integration
- Progress tracking and error reporting

Requirement: Advanced Custom Fields plugin (install first)

"""

    installation_guide += """
## SUPER QUICK SETUP (2 Minutes)

### Step 1: Upload & Activate Theme (30 seconds)
Appearance > Themes > Add New > Upload Theme
Upload your theme ZIP
Click "Activate"

### Step 2: Everything Auto-Installs (60 seconds)  
Auto Page Creator - Creates all WordPress pages automatically
Auto-Response Mailer - Installs automatically
CMS Importer - Installs automatically (if CMS theme)
Success notice appears in admin

### Step 3: Verify Pages Created (30 seconds)
Go to Pages > All Pages
See all your Webflow pages now in WordPress!
Check Tools > Webflow Pages for status

### Step 4: Test Auto-Response (30 seconds)
Go to Settings > Auto-Response Mailer
Click "Send Test Email"  
Enter your email
Check your inbox!

### Step 5: Done!
Your complete WordPress site is ready with:
- All pages created automatically
- Contact forms sending professional auto-responses
- CMS content imported (if applicable)

## ZERO-CONFIGURATION FEATURES

### Automatic Page Creation
WordPress pages created automatically:
- index.html - Home page (set as front page)
- about.html - About page (/about/)
- contact.html - Contact page (/contact/)
- services.html - Services page (/services/)
- Any-page.html - WordPress page (/any-page/)

### Smart Template Assignment
- about.html uses page-about.php template
- contact.html uses page-contact.php template  
- Automatic template matching for all pages

### SEO Preservation
- Page titles preserved from Webflow
- Meta descriptions maintained
- Clean, SEO-friendly URLs

### Contact Form Auto-Detection
Works automatically with:
- Contact Form 7 - No setup needed
- Gravity Forms - No setup needed  
- Formidable Forms - No setup needed
- Custom HTML Forms - No setup needed
- Any form with email field - No setup needed

## You're All Set!

Your Webflow theme is now a complete WordPress website with:
- All pages created automatically - No manual page creation needed
- Instant auto-response emails for ALL contact forms
- Professional email templates with your branding  
- Zero configuration - works immediately
- CMS content imported (if applicable)
- WordPress best practices implemented

Result: A fully functional WordPress website that mirrors your Webflow design with enhanced functionality!

Theme converted by Webflow to WordPress Converter with Auto Page Creation
"""

    # Save the updated installation guide
    guide_path = os.path.join(output_theme, 'AUTO-INSTALL-GUIDE.md')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(installation_guide)
    
    # Create simple setup card
    setup_card = f"""
{theme_name} - INSTANT SETUP
===============================

STEP 1: Activate Theme (30 sec)
   Upload ZIP - Activate - Done!

STEP 2: Everything Auto-Installs (60 sec)  
   WordPress pages created automatically
   Auto-Response Mailer installed
   CMS Importer installed (if CMS)

STEP 3: Verify (30 sec)
   Pages > All Pages - See all your pages!
   Settings > Auto-Response Mailer - Test email

RESULT: Complete WordPress site ready!

TOTAL TIME: 2 MINUTES

For details, see AUTO-INSTALL-GUIDE.md
"""
    
    setup_card_path = os.path.join(output_theme, 'INSTANT-SETUP.txt')
    with open(setup_card_path, 'w', encoding='utf-8') as f:
        f.write(setup_card)
    
    print(f"Created auto-install guides (with page creation):")
    print(f"  - {guide_path}")
    print(f"  - {setup_card_path}")
    
    return guide_path


def generate_plugin_from_template(collections, theme_name):
    """Generates the importer plugin from template file with progress tracking"""
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-importer.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        return generate_basic_cms_plugin(collections, theme_name)
    
    # Prepare the JSON data with proper escaping
    collections_json = json.dumps(collections, ensure_ascii=False)
    collections_json = collections_json.replace('\\', '\\\\')
    collections_json = collections_json.replace("'", "\\'")
    collections_json = collections_json.replace('"', '\\"')
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} CMS Importer')
    plugin_code = plugin_code.replace('{{COLLECTIONS_JSON}}', collections_json)
    
    return plugin_code


def generate_basic_cms_plugin(collections, theme_name):
    """
    Fallback: Generate basic CMS plugin if template doesn't exist
    """
    collections_json = json.dumps(collections, ensure_ascii=True, separators=(',', ':'))
    collections_json = collections_json.replace('\\', '\\\\').replace("'", "\\'")
    
    # Basic plugin without template - minimal working version
    plugin_code = f"""<?php
/**
 * Plugin Name: {theme_name} CMS Importer
 * Description: Imports Webflow CMS content into WordPress
 * Version: 1.0.0
 */

if (!defined('ABSPATH')) exit;

class WebflowCMSImporter {{
    private $collections_data;
    
    public function __construct() {{
        $this->collections_data = json_decode('{collections_json}', true);
        add_action('admin_menu', array($this, 'add_admin_menu'));
        register_activation_hook(__FILE__, array($this, 'activate_plugin'));
    }}
    
    public function activate_plugin() {{
        update_option('webflow_cms_auto_import_needed', true);
        update_option('webflow_cms_collections_data', $this->collections_data);
    }}
    
    public function add_admin_menu() {{
        add_management_page('Webflow Import', 'Webflow Import', 'manage_options', 'webflow-import', array($this, 'admin_page'));
    }}
    
    public function admin_page() {{
        echo '<div class="wrap"><h1>Webflow CMS Importer</h1>';
        echo '<p>CMS collections ready for import.</p>';
        echo '<button onclick="alert(\'Import functionality needs full template\')">Import Now</button>';
        echo '</div>';
    }}
}}

new WebflowCMSImporter();
?>"""
    
    return plugin_code


def extract_webflow_collections(webflow_dir):
    """Extracts collection data from Webflow export"""
    collections = []
    cms_dir = os.path.join(webflow_dir, 'cms')
    
    if os.path.exists(cms_dir):
        for collection_file in os.listdir(cms_dir):
            if collection_file.endswith('.json'):
                with open(os.path.join(cms_dir, collection_file), 'r') as f:
                    try:
                        data = json.load(f)
                        collections.append({
                            'name': data.get('name', 'Unnamed'),
                            'slug': data.get('slug', 'unnamed'),
                            'fields': extract_fields(data)
                        })
                    except json.JSONDecodeError:
                        continue
    return collections


def generate_auto_response_plugin_from_template(theme_name):
    """
    Generate auto-response email plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-auto-mailer.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        print("Please create templates/webflow-auto-mailer.php")
        return None
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Auto-Response Mailer')
    
    return plugin_code


def create_auto_response_plugin_files(output_theme, theme_name):
    """
    Create the auto-response email plugin files using template
    """
    # Create plugin directory
    plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-auto-mailer')
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Generate plugin code from template
    plugin_code = generate_auto_response_plugin_from_template(theme_name)
    
    if not plugin_code:
        print("Failed to generate auto-response plugin")
        return None
    
    # Save the main plugin file
    plugin_file_path = os.path.join(plugin_dir, 'webflow-auto-mailer.php')
    with open(plugin_file_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    # Create plugin readme
    readme_content = f"""=== {theme_name} Auto-Response Mailer ===
Contributors: webflow-converter
Tags: email, auto-response, contact-form, mailer, automatic
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Sends beautiful, customizable response emails to contact form submissions.

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
Configure through Settings > Auto-Response Mailer.

== Changelog ==
= 1.0.0 =
* Initial release"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    mailer_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-auto-mailer.zip')
    
    with zipfile.ZipFile(mailer_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-auto-mailer/webflow-auto-mailer.php')
        zipf.write(readme_path, 'webflow-auto-mailer/readme.txt')
    
    print(f"Created Auto-Response Email plugin from template: {mailer_zip_path}")
    return mailer_zip_path



def update_functions_php_for_auto_plugin_install_with_contact_forms(output_theme, theme_name, has_cms=False, has_pages=True):
    """
    Updated version that includes contact form handler plugin
    """
    functions_php_path = os.path.join(output_theme, 'functions.php')
    
    theme_slug = theme_name.lower().replace(' ', '_').replace('-', '_')
    
    # Add auto-plugin installation code to functions.php
    auto_install_code = f"""

// Auto-install theme plugins on activation
function {theme_slug}_auto_install_plugins() {{
    // Check if plugins are already installed
    $auto_mailer_installed = is_plugin_active('webflow-auto-mailer/webflow-auto-mailer.php');
    $cms_importer_installed = is_plugin_active('webflow-importer/webflow-importer.php');
    $page_creator_installed = is_plugin_active('webflow-page-creator/webflow-page-creator.php');
    $contact_handler_installed = is_plugin_active('webflow-contact-handler/webflow-contact-handler.php');
    
    $plugins_to_install = array();
    
    // Auto-Response Mailer (always install)
    if (!$auto_mailer_installed) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} Auto-Response Mailer',
            'zip' => get_template_directory() . '/includes/plugins/webflow-auto-mailer.zip',
            'folder' => 'webflow-auto-mailer',
            'main_file' => 'webflow-auto-mailer/webflow-auto-mailer.php'
        );
    }}
    
    // Contact Form Handler (always install)
    if (!$contact_handler_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-contact-handler.zip')) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} Contact Form Handler',
            'zip' => get_template_directory() . '/includes/plugins/webflow-contact-handler.zip',
            'folder' => 'webflow-contact-handler',
            'main_file' => 'webflow-contact-handler/webflow-contact-handler.php'
        );
    }}
    
    {f'''// Auto Page Creator (if pages exist)
    if (!$page_creator_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-page-creator.zip')) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} Page Creator',
            'zip' => get_template_directory() . '/includes/plugins/webflow-page-creator.zip',
            'folder' => 'webflow-page-creator',
            'main_file' => 'webflow-page-creator/webflow-page-creator.php'
        );
    }}''' if has_pages else '// No page creator needed'}
    
    {f'''// CMS Importer (if CMS theme)
    if (!$cms_importer_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-importer.zip')) {{
        $plugins_to_install[] = array(
            'name' => '{theme_name} CMS Importer',
            'zip' => get_template_directory() . '/includes/plugins/webflow-importer.zip',
            'folder' => 'webflow-importer',
            'main_file' => 'webflow-importer/webflow-importer.php'
        );
    }}''' if has_cms else '// No CMS plugin needed'}
    
    // Install plugins
    if (!empty($plugins_to_install)) {{
        require_once ABSPATH . 'wp-admin/includes/file.php';
        require_once ABSPATH . 'wp-admin/includes/misc.php';
        require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
        
        foreach ($plugins_to_install as $plugin) {{
            if (file_exists($plugin['zip'])) {{
                // Install plugin
                $upgrader = new Plugin_Upgrader();
                $result = $upgrader->install($plugin['zip']);
                
                if (!is_wp_error($result)) {{
                    // Activate plugin
                    activate_plugin($plugin['main_file']);
                    
                    // Add success notice
                    set_transient('theme_plugins_installed', true, 60);
                }}
            }}
        }}
    }}
}}

// Auto-install on theme activation
add_action('after_switch_theme', '{theme_slug}_auto_install_plugins');

// Show installation notice
add_action('admin_notices', function() {{
    if (get_transient('theme_plugins_installed')) {{
        echo '<div class="notice notice-success is-dismissible">';
        echo '<p><strong>🎉 Theme Activated Successfully!</strong></p>';
        echo '<p>✅ Auto-Response Email plugin installed and activated</p>';
        echo '<p>✅ Contact Form Handler plugin installed and activated</p>';
        {f"echo '<p>✅ Auto Page Creator plugin installed and activated</p>';" if has_pages else ''}
        {f"echo '<p>✅ CMS Importer plugin installed and activated</p>';" if has_cms else ''}
        echo '<p><strong>Quick Actions:</strong></p>';
        echo '<p><a href=\"' . admin_url('options-general.php?page=webflow-auto-mailer') . '\" class=\"button button-primary\">📧 Configure Auto-Response Emails</a></p>';
        echo '<p><a href=\"' . admin_url('edit.php?post_type=webflow_contact_forms&page=webflow-contact-settings') . '\" class=\"button\">📝 Configure Contact Forms</a></p>';
        {f"echo '<p><a href=\"' . admin_url('tools.php?page=webflow-pages') . '\" class=\"button\">📄 View Created Pages</a></p>';" if has_pages else ''}
        echo '</div>';
        delete_transient('theme_plugins_installed');
    }}
}});"""
    
    # Append to existing functions.php
    if os.path.exists(functions_php_path):
        with open(functions_php_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Remove the closing ?> if it exists and add our code
        if existing_content.strip().endswith('?>'):
            existing_content = existing_content.strip()[:-2]
        
        updated_content = existing_content + auto_install_code + "\n?>"
        
        with open(functions_php_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Updated functions.php with auto-plugin installation (including contact form handler)")
    
    return True


# def update_functions_php_for_auto_plugin_install_with_pages(output_theme, theme_name, has_cms=False, has_pages=True):
#     """
#     Updated version that includes auto page creator plugin
#     """
#     functions_php_path = os.path.join(output_theme, 'functions.php')
    
#     theme_slug = theme_name.lower().replace(' ', '_').replace('-', '_')
    
#     # Add auto-plugin installation code to functions.php
#     auto_install_code = f"""

# // Auto-install theme plugins on activation
# function {theme_slug}_auto_install_plugins() {{
#     // Check if plugins are already installed
#     $auto_mailer_installed = is_plugin_active('webflow-auto-mailer/webflow-auto-mailer.php');
#     $cms_importer_installed = is_plugin_active('webflow-importer/webflow-importer.php');
#     $page_creator_installed = is_plugin_active('webflow-page-creator/webflow-page-creator.php');
    
#     $plugins_to_install = array();
    
#     // Auto-Response Mailer (always install)
#     if (!$auto_mailer_installed) {{
#         $plugins_to_install[] = array(
#             'name' => '{theme_name} Auto-Response Mailer',
#             'zip' => get_template_directory() . '/includes/plugins/webflow-auto-mailer.zip',
#             'folder' => 'webflow-auto-mailer',
#             'main_file' => 'webflow-auto-mailer/webflow-auto-mailer.php'
#         );
#     }}
    
#     {f'''// Auto Page Creator (always install)
#     if (!$page_creator_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-page-creator.zip')) {{
#         $plugins_to_install[] = array(
#             'name' => '{theme_name} Page Creator',
#             'zip' => get_template_directory() . '/includes/plugins/webflow-page-creator.zip',
#             'folder' => 'webflow-page-creator',
#             'main_file' => 'webflow-page-creator/webflow-page-creator.php'
#         );
#     }}''' if has_pages else '// No page creator needed'}
    
#     {f'''// CMS Importer (if CMS theme)
#     if (!$cms_importer_installed && file_exists(get_template_directory() . '/includes/plugins/webflow-importer.zip')) {{
#         $plugins_to_install[] = array(
#             'name' => '{theme_name} CMS Importer',
#             'zip' => get_template_directory() . '/includes/plugins/webflow-importer.zip',
#             'folder' => 'webflow-importer',
#             'main_file' => 'webflow-importer/webflow-importer.php'
#         );
#     }}''' if has_cms else '// No CMS plugin needed'}
    
#     // Install plugins
#     if (!empty($plugins_to_install)) {{
#         require_once ABSPATH . 'wp-admin/includes/file.php';
#         require_once ABSPATH . 'wp-admin/includes/misc.php';
#         require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';
        
#         foreach ($plugins_to_install as $plugin) {{
#             if (file_exists($plugin['zip'])) {{
#                 // Install plugin
#                 $upgrader = new Plugin_Upgrader();
#                 $result = $upgrader->install($plugin['zip']);
                
#                 if (!is_wp_error($result)) {{
#                     // Activate plugin
#                     activate_plugin($plugin['main_file']);
                    
#                     // Add success notice
#                     set_transient('theme_plugins_installed', true, 60);
#                 }}
#             }}
#         }}
#     }}
# }}

# // Auto-install on theme activation
# add_action('after_switch_theme', '{theme_slug}_auto_install_plugins');

# // Show installation notice
# add_action('admin_notices', function() {{
#     if (get_transient('theme_plugins_installed')) {{
#         echo '<div class="notice notice-success is-dismissible">';
#         echo '<p><strong>Theme Activated Successfully!</strong></p>';
#         echo '<p>Auto-Response Email plugin installed and activated</p>';
#         {f"echo '<p>Auto Page Creator plugin installed and activated</p>';" if has_pages else ''}
#         {f"echo '<p>CMS Importer plugin installed and activated</p>';" if has_cms else ''}
#         echo '<p><a href="' . admin_url('options-general.php?page=webflow-auto-mailer') . '" class="button button-primary">Configure Auto-Response Emails</a></p>';
#         {f"echo '<p><a href=\"' . admin_url('tools.php?page=webflow-pages') . '\" class=\"button\">View Created Pages</a></p>';" if has_pages else ''}
#         echo '</div>';
#         delete_transient('theme_plugins_installed');
#     }}
# }});"""
    
#     # Append to existing functions.php
#     if os.path.exists(functions_php_path):
#         with open(functions_php_path, 'r', encoding='utf-8') as f:
#             existing_content = f.read()
        
#         # Remove the closing ?> if it exists and add our code
#         if existing_content.strip().endswith('?>'):
#             existing_content = existing_content.strip()[:-2]
        
#         updated_content = existing_content + auto_install_code + "\n?>"
        
#         with open(functions_php_path, 'w', encoding='utf-8') as f:
#             f.write(updated_content)
        
#         print("Updated functions.php with auto-plugin installation (including page creator)")
    
#     return True


def extract_fields(collection_data):
    """Extracts field definitions from collection data"""
    fields = []
    for field in collection_data.get('fields', []):
        fields.append({
            'name': field.get('name', 'Unnamed'),
            'slug': field.get('slug', 'unnamed'),
            'type': map_field_type(field.get('type', 'text'))
        })
    return fields


def map_field_type(webflow_type):
    """Maps Webflow field types to ACF field types"""
    mapping = {
        'text': 'text',
        'textarea': 'textarea',
        'richtext': 'wysiwyg',
        'image': 'image',
        'file': 'file',
        'number': 'number',
        'date': 'date_picker',
        'switch': 'true_false',
        'option': 'select'
    }
    return mapping.get(webflow_type, 'text')


def update_style_css_with_theme_name(output_theme, theme_name):
    """
    Update style.css with proper WordPress theme header and make it deletable
    """
    style_css_path = os.path.join(output_theme, 'style.css')
    
    # Create proper WordPress theme header
    wordpress_theme_header = f"""/*
Theme Name: {theme_name}
Description: Converted from Webflow to WordPress theme with CMS integration and AI-powered SEO optimization
Version: 1.0.0
Author: Webflow to WP Converter
Author URI: https://yoursite.com
License: GPL v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: {theme_name.lower().replace(' ', '-')}
Tags: webflow, responsive, cms, custom-post-types, seo-optimized, ai-powered
Requires at least: 5.0
Tested up to: 6.4
Requires PHP: 7.4

This theme was automatically converted from Webflow.
Includes CMS content and Advanced Custom Fields integration.
*/

"""

    if os.path.exists(style_css_path):
        with open(style_css_path, 'r', encoding='utf-8') as f:
            existing_css = f.read()

        # Remove old theme header if exists
        updated_css_content = re.sub(
            r'\/\*[\s\S]*?\*\/',
            '',
            existing_css,
            count=1  # Only remove the first comment block
        ).strip()

        # Add new WordPress theme header
        final_css_content = wordpress_theme_header + "\n" + updated_css_content

        with open(style_css_path, 'w', encoding='utf-8') as f:
            f.write(final_css_content)
        print("style.css updated with proper WordPress theme header.")

    else:
        # Create style.css if it doesn't exist
        with open(style_css_path, 'w', encoding='utf-8') as f:
            f.write(wordpress_theme_header)
        print(f"Created style.css with WordPress theme header at {style_css_path}")

    # Create additional files needed for theme deletion
    create_theme_management_files(output_theme, theme_name)


def create_theme_management_files(output_theme, theme_name):
    """
    Create additional files needed for proper WordPress theme management
    """
    
    # 1. Create functions.php if it doesn't exist
    functions_php_path = os.path.join(output_theme, 'functions.php')
    if not os.path.exists(functions_php_path):
        functions_content = f"""<?php
/**
 * {theme_name} Functions and Definitions
 */

// Prevent direct access
if (!defined('ABSPATH')) exit;

// Theme setup
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_setup() {{
    // Add theme support for various features
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    add_theme_support('html5', array('search-form', 'comment-form', 'comment-list', 'gallery', 'caption'));
    add_theme_support('custom-logo');
    
    // Register navigation menus
    register_nav_menus(array(
        'primary' => __('Primary Menu', '{theme_name.lower().replace(' ', '-')}'),
        'footer' => __('Footer Menu', '{theme_name.lower().replace(' ', '-')}'),
    ));
}}
add_action('after_setup_theme', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_setup');

// Enqueue styles and scripts
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_scripts() {{
    // Main stylesheet
    wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-style', get_stylesheet_uri(), array(), '1.0.0');
    
    // Webflow CSS files
    if (file_exists(get_template_directory() . '/css/normalize.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-normalize', get_template_directory_uri() . '/css/normalize.css', array(), '1.0.0');
    }}
    if (file_exists(get_template_directory() . '/css/webflow.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-webflow', get_template_directory_uri() . '/css/webflow.css', array(), '1.0.0');
    }}
    if (file_exists(get_template_directory() . '/css/components.css')) {{
        wp_enqueue_style('{theme_name.lower().replace(' ', '-')}-components', get_template_directory_uri() . '/css/components.css', array(), '1.0.0');
    }}
    
    // Webflow JS files
    if (file_exists(get_template_directory() . '/js/webflow.js')) {{
        wp_enqueue_script('{theme_name.lower().replace(' ', '-')}-webflow-js', get_template_directory_uri() . '/js/webflow.js', array('jquery'), '1.0.0', true);
    }}
}}
add_action('wp_enqueue_scripts', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_scripts');

// Widget areas
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_widgets_init() {{
    register_sidebar(array(
        'name'          => __('Sidebar', '{theme_name.lower().replace(' ', '-')}'),
        'id'            => 'sidebar-1',
        'description'   => __('Add widgets here.', '{theme_name.lower().replace(' ', '-')}'),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h2 class="widget-title">',
        'after_title'   => '</h2>',
    ));
}}
add_action('widgets_init', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_widgets_init');

// Theme cleanup on switch
function {theme_name.lower().replace(' ', '_').replace('-', '_')}_cleanup() {{
    // Clean up any theme-specific options or data
    delete_option('{theme_name.lower().replace(' ', '-')}_settings');
    
    // Flush rewrite rules
    flush_rewrite_rules();
}}
add_action('switch_theme', '{theme_name.lower().replace(' ', '_').replace('-', '_')}_cleanup');
?>"""
        
        with open(functions_php_path, 'w', encoding='utf-8') as f:
            f.write(functions_content)
        print("Created functions.php for proper theme functionality")

    # 2. Create index.php fallback if it doesn't exist
    index_php_path = os.path.join(output_theme, 'index.php')
    if not os.path.exists(index_php_path):
        index_content = f"""<?php
/**
 * The main template file for {theme_name}
 */

get_header(); ?>

<main id="main" class="site-main">
    <div class="container">
        <?php if (have_posts()) : ?>
            <?php while (have_posts()) : the_post(); ?>
                <article id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
                    <header class="entry-header">
                        <h1 class="entry-title"><?php the_title(); ?></h1>
                    </header>
                    
                    <div class="entry-content">
                        <?php the_content(); ?>
                    </div>
                </article>
            <?php endwhile; ?>
        <?php else : ?>
            <p><?php _e('No content found.', '{theme_name.lower().replace(' ', '-')}'); ?></p>
        <?php endif; ?>
    </div>
</main>

<?php get_footer(); ?>"""
        
        with open(index_php_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print("Created index.php fallback template")

    # 3. Create header.php if it doesn't exist
    header_php_path = os.path.join(output_theme, 'header.php')
    if not os.path.exists(header_php_path):
        header_content = f"""<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="profile" href="https://gmpg.org/xfn/11">
    <?php wp_head(); ?>
</head>

<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<div id="page" class="site">
    <header id="masthead" class="site-header">
        <div class="site-branding">
            <?php
            if (has_custom_logo()) {{
                the_custom_logo();
            }} else {{
                ?>
                <h1 class="site-title"><a href="<?php echo esc_url(home_url('/')); ?>" rel="home"><?php bloginfo('name'); ?></a></h1>
                <?php
            }}
            ?>
        </div>
        
        <nav id="site-navigation" class="main-navigation">
            <?php
            wp_nav_menu(array(
                'theme_location' => 'primary',
                'menu_id'        => 'primary-menu',
                'fallback_cb'    => false,
            ));
            ?>
        </nav>
    </header>"""
        
        with open(header_php_path, 'w', encoding='utf-8') as f:
            f.write(header_content)
        print("Created header.php template")

    # 4. Create footer.php if it doesn't exist
    footer_php_path = os.path.join(output_theme, 'footer.php')
    if not os.path.exists(footer_php_path):
        footer_content = f"""    <footer id="colophon" class="site-footer">
        <div class="site-info">
            <p>&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. <?php _e('Converted from Webflow.', '{theme_name.lower().replace(' ', '-')}'); ?></p>
        </div>
    </footer>
</div><!-- #page -->

<?php wp_footer(); ?>
</body>
</html>"""
        
        with open(footer_php_path, 'w', encoding='utf-8') as f:
            f.write(footer_content)
        print("Created footer.php template")


# ======= contact form


def generate_contact_form_plugin_from_template(theme_name):
    """
    Generate contact form handler plugin from template file
    """
    template_path = os.path.join(BASE_DIR, 'templates', 'webflow-contact-handler.php')
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        print("Please create templates/webflow-contact-handler.php")
        return None
    
    # Replace placeholders
    plugin_code = template.replace('{{PLUGIN_NAME}}', f'{theme_name} Contact Form Handler')
    
    return plugin_code



def create_contact_form_plugin_files(output_theme, theme_name):
    """
    Create the contact form handler plugin files using template
    """
    # Create plugin directory
    plugin_dir = os.path.join(output_theme, 'includes', 'plugins', 'webflow-contact-handler')
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Generate plugin code from template
    plugin_code = generate_contact_form_plugin_from_template(theme_name)
    
    if not plugin_code:
        print("Failed to generate contact form plugin")
        return None
    
    # Save the main plugin file
    plugin_file_path = os.path.join(plugin_dir, 'webflow-contact-handler.php')
    with open(plugin_file_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    # Create plugin readme
    readme_content = f"""=== {theme_name} Contact Form Handler ===
Contributors: webflow-converter
Tags: contact-form, form-handler, automatic, ajax, universal
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0

== Description ==
Universal contact form handler that automatically processes any contact form on pages containing contact-related keywords.

== Features ==
* Auto-detects contact pages by URL keywords
* Handles any HTML form with email field
* Saves submissions to WordPress admin
* Sends email notifications
* Works without configuration
* AJAX form submission
* Admin management interface

== Installation ==
Auto-installs when you activate your theme.

== Usage ==
Configure through Contact Forms > Settings in WordPress admin.

== Changelog ==
= 1.0.0 =
* Initial release with universal form detection
* Auto-install capability
* Admin interface for form management"""

    readme_path = os.path.join(plugin_dir, 'readme.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # Create the ZIP archive
    contact_zip_path = os.path.join(output_theme, 'includes', 'plugins', 'webflow-contact-handler.zip')
    
    with zipfile.ZipFile(contact_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(plugin_file_path, 'webflow-contact-handler/webflow-contact-handler.php')
        zipf.write(readme_path, 'webflow-contact-handler/readme.txt')
    
    print(f"Created Contact Form Handler plugin from template: {contact_zip_path}")
    return contact_zip_path



@app.route("/delete_temp_zip", methods=["POST"])
def delete_temp_zip():
    data = request.get_json()
    zip_path = data.get("zip_path")
    if zip_path and os.path.exists(zip_path):
        os.remove(zip_path)
        return jsonify({"message": "Temporary ZIP deleted."})
    return jsonify({"error": "ZIP file not found."}), 404


def fix_asset_paths(html):
    pattern = re.compile(r'(src|href)="[^"]*((?:' + '|'.join(ASSET_FOLDERS) + r')/([^"/\?#]+))(\?[^\"]*)?"')

    def replacer(match):
        attr, folder_path, raw_filename = match.group(1), match.group(2), match.group(3)
        folder = folder_path.split('/')[0]
        parts = raw_filename.split('.')
        if len(parts) > 2 and re.fullmatch(r'[a-f0-9]{8,}', parts[-2]):
            raw_filename = '.'.join(parts[:-2] + parts[-1:])
        return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{raw_filename}"'

    html = pattern.sub(replacer, html)

    def srcset_replacer(match):
        parts = [p.strip() for p in match.group(1).split(',')]
        new_parts = []
        for part in parts:
            url, size = part.rsplit(' ', 1) if ' ' in part else (part, '')
            folder = url.split('/')[0]
            filename = os.path.basename(url)
            segments = filename.split('.')
            if len(segments) > 2 and re.fullmatch(r'[a-f0-9]{8,}', segments[-2]):
                filename = '.'.join(segments[:-2] + segments[-1:])
            if folder in ASSET_FOLDERS:
                new_url = f'<?php echo get_template_directory_uri(); ?>/{folder}/{filename}'
                new_parts.append(f'{new_url} {size}'.strip())
            else:
                new_parts.append(part)
        return f'srcset="{", ".join(new_parts)}"'

    html = re.sub(r'srcset="([^"]+)"', srcset_replacer, html)

    def custom_data_attr_replacer(match):
        attr, path = match.groups()
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'{attr}="<?php echo get_template_directory_uri(); ?>/{folder}/{filename}"'
        return match.group(0)

    html = re.sub(r'(data-poster-url|data-video-urls)="([^"]+)"', custom_data_attr_replacer, html)

    def style_url_replacer(match):
        path = match.group(1)
        folder = path.split('/')[0]
        filename = os.path.basename(path)
        if folder in ASSET_FOLDERS:
            return f'url(<?php echo get_template_directory_uri(); ?>/{folder}/{filename})'
        return match.group(0)

    html = re.sub(
        r'href="([^"]+\.html)"',
        lambda m: 'href="<?php echo site_url(\'/\'); ?>"' if os.path.basename(m.group(1)).lower() == 'index.html'
        else f'href="<?php echo site_url(\'/{os.path.splitext(os.path.basename(m.group(1)))[0]}\'); ?>"',
        html
    )

    html = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', style_url_replacer, html)

    html = re.sub(r'<link href="[^"]*splide.min.css[^"]*"[^>]*>',
                  '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/css/splide.min.css">', html)
    html = re.sub(r'<script src="[^"]*splide.min.js[^"]*"></script>',
                  '<script src="https://cdn.jsdelivr.net/npm/@splidejs/splide@4.1.4/dist/js/splide.min.js"></script>', html)

    return html


if __name__ == '__main__':

    # Create services directory if it doesn't exist
    services_dir = os.path.join(BASE_DIR, 'services')
    os.makedirs(services_dir, exist_ok=True)
    
    # Create __init__.py in services directory
    init_file = os.path.join(services_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Services package\n')

    app.run(host='0.0.0.0', port=5022, debug=True)