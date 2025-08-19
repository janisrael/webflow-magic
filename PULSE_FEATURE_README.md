# Pulse Analytics Feature

## Overview
The Pulse tab provides comprehensive workload analytics and load balancing insights for your team using real ClickUp data.

## Features
- **Member Workload Analysis**: Individual cards showing tasks, projects, and workload status
- **Project Distribution**: How workload is spread across projects
- **Load Balancing Intelligence**: Identifies highest/lowest workload members
- **Transfer Suggestions**: Specific recommendations for task redistribution
- **Smart Recommendations**: Actionable insights for admins
- **3-Hour Caching**: Automatic data caching to reduce API calls

## Setup Instructions

### 1. Run Setup Script
```bash
python setup_pulse_directories.py
```

### 2. Update ClickUp API Key
Edit `services/pulse_service.py` and replace:
```python
self.clickup_api_key = "pk_126127973_ULPZ9TEC7TGPGAP3WVCA2KWOQQGV3Y4K"
```
With your actual ClickUp API key.

### 3. Configure Target Members
Edit `services/clickup_pulse_integration.py` line 55:
```python
target_members = ['Jan', 'Arif', 'wiktor', 'sarah', 'alex']  # Add your team member usernames
```

### 4. Add Route to wf.py
Add the provided route code to your main `wf.py` file.

### 5. Update index.html
Replace the navigation section and add the CSS/JS imports as provided.

### 6. Create Component Files
Create the following files:
- `static/components/pulse/pulse.css`
- `static/components/pulse/pulse.js`

## File Structure
```
app/
├── output/
│   └── pulse/                    # Generated JSON files stored here
│       └── pulse_YYYYMMDD_HHMM.json
├── services/
│   ├── __init__.py
│   ├── pulse_service.py          # Main pulse service
│   └── clickup_pulse_integration.py  # ClickUp API integration
├── static/
│   └── components/
│       └── pulse/
│           ├── pulse.css         # Pulse styling
│           └── pulse.js          # Pulse functionality
└── templates/
    └── index.html               # Updated with Pulse tab
```



app/
├── output/
│   └── pulse/                    # Generated JSON files stored here
│       └── pulse_YYYYMMDD_HHMM.json
    └── seo-reports/                   
│       └── themename_date
            SEO-OPTIMIZATION-REPORT.html
├── services/
│   ├── __init__.py
|   |── pulse
│   |  ├── pulse_service.py          # Main pulse service
│   |  └── clickup_pulse_integration.py  # ClickUp API integration
|   |__ tools
|   |   |── wf-wp-converter
|   |
|   |── Calendar
|   |
|   |── KPI (clickup analytics)
|   |── project tracker
|
|
├── static/
│   └── components/
│       └── pulse/
│           ├── pulse.css         # Pulse styling
│           └── pulse.js          # Pulse functionality
└── templates/
    └── index.html               # Updated with Pulse tab
main.py


## How It Works

### 1. **Data Caching (3-hour intervals)**
- Checks for existing `pulse_*.json` files in `output/pulse/`
- If a file exists that's less than 3 hours old, uses cached data
- Otherwise, generates fresh data from ClickUp API

### 2. **Real ClickUp Integration**
- Fetches team members and their open tasks
- Analyzes task activity within working hours (9 AM - 5 PM)
- Identifies task periods and downtime gaps
- Calculates workload scores based on multiple factors

### 3. **Workload Scoring Algorithm**
```
Score = (Active Tasks × 10) + 
        (Urgent Tasks × 25) + 
        (High Priority × 15) + 
        (Due Soon × 20) + 
        (Remaining Hours × 2) + 
        (Project Count × 5)
```

### 4. **Status Classification**
- **Light**: Score < 50
- **Balanced**: Score 50-99
- **High**: Score 100-149
- **Overloaded**: Score ≥ 150

## Example Output
The system will show insights like:
> "wiktor has high workload with 4 active tasks across 2 projects, one project due soon"

And provide transfer suggestions:
> "Transfer 'Database Schema' from wiktor to alex - Balance workload"

## Working Hours Configuration
Default working hours are configured in `clickup_pulse_integration.py`:
- **Work Start**: 9:00 AM
- **Work End**: 5:00 PM  
- **Lunch Break**: 12:00-12:30 PM
- **Working Hours Per Day**: 7.5 hours

## API Rate Limiting
- Built-in rate limiting with automatic retries
- 1-2 second delays between API calls
- Graceful handling of ClickUp API rate limits

## Troubleshooting

### Common Issues:
1. **Import Error**: Make sure `services/__init__.py` exists
2. **API Key Invalid**: Check your ClickUp API key
3. **No Team Members**: Verify team ID and member usernames
4. **Permission Error**: Ensure ClickUp API key has proper permissions

### Demo Data Fallback:
If real data can't be fetched, the system automatically falls back to demo data so the interface remains functional.

## Data Privacy
- All data is cached locally in JSON files
- No sensitive data is exposed in the frontend
- Old cache files are automatically cleaned up (keeps latest 10 files)