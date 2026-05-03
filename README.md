# Live Metrics App - Google Sheets Powered

A comprehensive metrics dashboard powered by Google Sheets with AI-powered analysis.

## Features

### Projects
- **Metrics**: Track KPIs and performance indicators
- **Experiments**: Monitor A/B tests and experiments
- **Insights**: AI-generated insights from data trends
- **Actions**: Actionable items based on anomalies and insights

### Agent: Analyst
An intelligent agent that:
- Explains trends in your data
- Detects anomalies automatically
- Suggests fixes and recommendations
- Answers questions via chat interface

### Workflows
1. **On Sheet Change**: Automatically sync rows into Metrics and flag anomalies
2. **Weekly Schedule**: Generate executive reports with charts and action items, then notify stakeholders

### UI Components
- **KPI Dashboard**: Real-time metrics overview with charts
- **Experiment Tracker**: Monitor all active and completed experiments
- **Insights Feed**: Browse AI-generated insights
- **Agent Chat**: Interactive chat with the Analyst agent

## Setup

### 1. Google Sheets Setup

Create a Google Sheet with the following worksheets:

#### Metrics Sheet
Columns: `Metric`, `Value`, `Timestamp`

#### Experiments Sheet
Columns: `Name`, `Status`, `Metric`, `Improvement`, `Start Date`

#### Reports Sheet (auto-populated)
Columns: `Generated At`, `Total Metrics`, `Anomalies`, `Actions`, `Status`

### 2. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API and Google Drive API
4. Create service account credentials
5. Download the JSON credentials file
6. Share your Google Sheet with the service account email

### 3. Installation

```bash
# Install dependencies
pip install flask gspread oauth2client pandas plotly schedule

# Set environment variables
export GOOGLE_CREDENTIALS_FILE=credentials.json
export GOOGLE_API_KEY=your_api_key  # Optional, for enhanced AI features
export PORT=5000

# Run the app
python app.py
```

### 4. Access the App

Open your browser and navigate to:
- Dashboard: `http://localhost:5000/`
- Experiments: `http://localhost:5000/experiments`
- Insights: `http://localhost:5000/insights`
- Actions: `http://localhost:5000/actions`
- Chat: `http://localhost:5000/chat`

## API Endpoints

- `POST /api/sync` - Manually trigger data sync from Google Sheets
- `POST /api/chat` - Chat with the Analyst agent
- `GET /api/metrics` - Get all metrics
- `GET /api/anomalies` - Get all detected anomalies
- `GET /api/insights` - Get all insights
- `GET/POST /api/actions` - Manage action items
- `PUT /api/actions/<id>` - Update an action
- `POST /api/report` - Generate weekly report on demand

## Configuration

The app is configured to use your Google Sheet:
- **Sheet ID**: `1UUE05iRRdXJQvQKSUf71ZpI4-S_-z1U6CxZ9eOZMG78`

To change the sheet, update the `SHEET_ID` variable in `app.py`.

## Scheduled Tasks

- **Weekly Report**: Every Monday at 9:00 AM, the system generates an executive report and notifies stakeholders

## Demo Mode

If no credentials are provided, the app runs in demo mode with sample data.

## Production Deployment

For production deployment:

1. Use a proper database instead of in-memory storage
2. Set up proper authentication
3. Use environment variables for sensitive data
4. Configure webhook triggers for real-time sheet updates
5. Deploy using the provided Procfile (Heroku compatible)

## License

MIT License
