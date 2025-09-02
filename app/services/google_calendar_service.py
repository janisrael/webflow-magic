import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Try to load dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GoogleCalendarService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_CALENDAR_API_KEY', '')
        self.client_id = os.getenv('GOOGLE_CALENDAR_CLIENT_ID', '')
        self.client_secret = os.getenv('GOOGLE_CALENDAR_CLIENT_SECRET', '')
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.refresh_token = os.getenv('GOOGLE_CALENDAR_REFRESH_TOKEN', '')
        
        self.base_url = "https://www.googleapis.com/calendar/v3"
        self.access_token = None
        self.token_expiry = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Cache directory for calendar data
        self.cache_dir = "app/output/calendar"
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_access_token(self) -> Optional[str]:
        """Get a valid access token using refresh token"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            self.logger.error("Missing OAuth credentials")
            return None
            
        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            self.token_expiry = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            
            return self.access_token
            
        except Exception as e:
            self.logger.error(f"Error getting access token: {e}")
            return None

    def _is_token_valid(self) -> bool:
        """Check if current access token is still valid"""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry

    def _make_authenticated_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make an authenticated request to Google Calendar API"""
        if not self._is_token_valid():
            if not self._get_access_token():
                return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error making authenticated request: {e}")
            return None

    def _make_api_key_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request using API key (for public calendars)"""
        if not self.api_key:
            self.logger.error("No API key provided")
            return None
            
        try:
            url = f"{self.base_url}/{endpoint}"
            params = params or {}
            params['key'] = self.api_key
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Error making API key request: {e}")
            return None

    def get_calendar_events(self, days: int = 30, use_cache: bool = True) -> Dict:
        """Get calendar events for the specified number of days"""
        cache_file = f"{self.cache_dir}/calendar_events_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        # Check for recent cache
        if use_cache:
            cached_data = self._get_recent_cached_data()
            if cached_data:
                return cached_data

        # Calculate date range - include past events too
        now = datetime.utcnow()
        time_min = (now - timedelta(days=30)).isoformat() + 'Z'  # Include past 30 days
        time_max = (now + timedelta(days=days)).isoformat() + 'Z'
        
        params = {
            'timeMin': time_min,
            'timeMax': time_max,
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 100
        }
        
        # Try to get events using OAuth
        events_data = self._make_authenticated_request(f"calendars/{self.calendar_id}/events", params)
        
        if not events_data:
            return self._get_demo_calendar_data()
        
        # Process and format events
        processed_events = self._process_events(events_data.get('items', []))
        
        # Create response structure
        calendar_data = {
            'success': True,
            'calendar_id': self.calendar_id,
            'total_events': len(processed_events),
            'date_range': {
                'start': time_min,
                'end': time_max
            },
            'events': processed_events,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'cache_file': cache_file,
                'auth_method': 'oauth'
            }
        }
        
        # Cache the data
        self._cache_calendar_data(calendar_data, cache_file)
        
        return calendar_data

    def _process_events(self, events: List[Dict]) -> List[Dict]:
        """Process and format calendar events"""
        processed_events = []
        
        for event in events:
            # Extract event details
            event_id = event.get('id', '')
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Process start and end times
            start_data = event.get('start', {})
            end_data = event.get('end', {})
            
            start_time = start_data.get('dateTime') or start_data.get('date')
            end_time = end_data.get('dateTime') or end_data.get('date')
            
            # Process attendees
            attendees = []
            if 'attendees' in event:
                for attendee in event['attendees']:
                    attendees.append({
                        'email': attendee.get('email', ''),
                        'name': attendee.get('displayName', ''),
                        'response_status': attendee.get('responseStatus', 'needsAction')
                    })
            
            # Determine event type
            event_type = 'all_day' if 'date' in start_data else 'timed'
            
            # Calculate duration
            duration = None
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    duration = (end_dt - start_dt).total_seconds() / 3600  # hours
                except:
                    pass
            
            processed_event = {
                'id': event_id,
                'title': summary,
                'description': description,
                'location': location,
                'start_time': start_time,
                'end_time': end_time,
                'event_type': event_type,
                'duration_hours': duration,
                'attendees': attendees,
                'attendee_count': len(attendees),
                'organizer': event.get('organizer', {}).get('email', ''),
                'status': event.get('status', 'confirmed'),
                'created': event.get('created', ''),
                'updated': event.get('updated', ''),
                'html_link': event.get('htmlLink', ''),
                'color_id': event.get('colorId', ''),
                'recurring_event_id': event.get('recurringEventId', '')
            }
            
            processed_events.append(processed_event)
        
        return processed_events

    def _get_recent_cached_data(self) -> Optional[Dict]:
        """Get recent cached calendar data"""
        try:
            import glob
            cache_files = glob.glob(f"{self.cache_dir}/calendar_events_*.json")
            
            if not cache_files:
                return None
            
            # Get the most recent file
            latest_file = max(cache_files, key=os.path.getctime)
            
            # Check if file is from today and within 3 hours
            file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
            now = datetime.now()
            
            if (file_time.date() == now.date() and 
                (now - file_time).total_seconds() < 10800):  # 3 hours
                
                with open(latest_file, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Error reading cached data: {e}")
            
        return None

    def _cache_calendar_data(self, data: Dict, filename: str):
        """Cache calendar data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error caching calendar data: {e}")

    def _get_demo_calendar_data(self) -> Dict:
        """Return demo calendar data when API fails"""
        # Create sample events for demonstration
        demo_events = [
            {
                'id': 'demo_1',
                'title': 'Team Meeting',
                'description': 'Weekly team sync meeting',
                'location': 'Conference Room A',
                'start_time': (datetime.now() + timedelta(hours=2)).isoformat() + 'Z',
                'end_time': (datetime.now() + timedelta(hours=3)).isoformat() + 'Z',
                'event_type': 'timed',
                'duration_hours': 1.0,
                'attendees': [
                    {'email': 'jan@example.com', 'name': 'Jan', 'response_status': 'accepted'},
                    {'email': 'team@example.com', 'name': 'Team Member', 'response_status': 'accepted'}
                ],
                'attendee_count': 2,
                'organizer': 'jan@example.com',
                'status': 'confirmed',
                'created': datetime.now().isoformat() + 'Z',
                'updated': datetime.now().isoformat() + 'Z',
                'html_link': 'https://calendar.google.com/event?eid=demo_1',
                'color_id': '1',
                'recurring_event_id': ''
            },
            {
                'id': 'demo_2',
                'title': 'Project Review',
                'description': 'Review progress on current projects',
                'location': 'Virtual Meeting',
                'start_time': (datetime.now() + timedelta(days=1, hours=10)).isoformat() + 'Z',
                'end_time': (datetime.now() + timedelta(days=1, hours=11)).isoformat() + 'Z',
                'event_type': 'timed',
                'duration_hours': 1.0,
                'attendees': [
                    {'email': 'jan@example.com', 'name': 'Jan', 'response_status': 'accepted'},
                    {'email': 'client@example.com', 'name': 'Client', 'response_status': 'needsAction'}
                ],
                'attendee_count': 2,
                'organizer': 'jan@example.com',
                'status': 'confirmed',
                'created': datetime.now().isoformat() + 'Z',
                'updated': datetime.now().isoformat() + 'Z',
                'html_link': 'https://calendar.google.com/event?eid=demo_2',
                'color_id': '2',
                'recurring_event_id': ''
            },
            {
                'id': 'demo_3',
                'title': 'Holiday - Labor Day',
                'description': 'Office closed for Labor Day',
                'location': '',
                'start_time': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'end_time': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'event_type': 'all_day',
                'duration_hours': 24.0,
                'attendees': [],
                'attendee_count': 0,
                'organizer': 'system@example.com',
                'status': 'confirmed',
                'created': datetime.now().isoformat() + 'Z',
                'updated': datetime.now().isoformat() + 'Z',
                'html_link': 'https://calendar.google.com/event?eid=demo_3',
                'color_id': '3',
                'recurring_event_id': ''
            }
        ]
        
        return {
            'success': True,
            'calendar_id': self.calendar_id,
            'total_events': len(demo_events),
            'date_range': {
                'start': datetime.utcnow().isoformat() + 'Z',
                'end': (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
            },
            'events': demo_events,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'cache_file': None,
                'auth_method': 'demo',
                'note': 'Demo data - configure OAuth for real calendar access'
            }
        }

    def get_calendar_info(self) -> Dict:
        """Get calendar information and settings"""
        if self.access_token:
            calendar_info = self._make_authenticated_request(f"calendars/{self.calendar_id}")
        elif self.api_key:
            calendar_info = self._make_api_key_request(f"calendars/{self.calendar_id}")
        else:
            return {
                'success': False,
                'error': 'No authentication method available'
            }
        
        if not calendar_info:
            return {
                'success': False,
                'error': 'Failed to fetch calendar information'
            }
        
        return {
            'success': True,
            'calendar_id': calendar_info.get('id', ''),
            'summary': calendar_info.get('summary', ''),
            'description': calendar_info.get('description', ''),
            'time_zone': calendar_info.get('timeZone', ''),
            'access_role': calendar_info.get('accessRole', ''),
            'primary': calendar_info.get('primary', False),
            'selected': calendar_info.get('selected', False),
            'kind': calendar_info.get('kind', ''),
            'etag': calendar_info.get('etag', '')
        }

    def test_connection(self) -> Dict:
        """Test the calendar connection using OAuth"""
        # Test OAuth connection
        if self.refresh_token and self.client_id and self.client_secret:
            if self._get_access_token():
                test_result = self._make_authenticated_request(f"calendars/{self.calendar_id}")
                if test_result:
                    return {
                        'success': True,
                        'method': 'oauth',
                        'message': f'OAuth authentication successful with calendar: {self.calendar_id}'
                    }
        
        return {
            'success': False,
            'method': 'none',
            'message': 'Missing OAuth credentials (client_id, client_secret, refresh_token)'
        }
