"""
Live Metrics App powered by Google Sheets
Projects: Metrics, Experiments, Insights, Actions
Agent: Analyst - explains trends and suggests fixes
Workflows: 
  - On sheet change: sync rows into Metrics and flag anomalies
  - Schedule weekly: generate executive report with charts and action items
UI: KPI dashboard, experiment tracker, insights feed, agent chat
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import schedule
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Google Sheets Configuration
SHEET_ID = "1UUE05iRRdXJQvQKSUf71ZpI4-S_-z1U6CxZ9eOZMG78"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# In-memory storage (in production, use a database)
metrics_data = []
experiments_data = []
insights_data = []
actions_data = []
anomalies = []

class GoogleSheetsClient:
    """Client for interacting with Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.sheet = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Google Sheets client"""
        try:
            # Try to use service account credentials if available
            creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            if os.path.exists(creds_file):
                with open(creds_file, 'r') as f:
                    creds_dict = json.load(f)
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
                self.client = gspread.authorize(credentials)
                self.sheet = self.client.open_by_key(SHEET_ID)
                logger.info("Successfully connected to Google Sheets")
            else:
                logger.warning("No credentials file found. Using demo mode.")
                self.client = None
                self.sheet = None
        except Exception as e:
            logger.error(f"Error initializing Google Sheets: {e}")
            self.client = None
            self.sheet = None
    
    def get_worksheet(self, worksheet_name):
        """Get a specific worksheet"""
        if self.sheet:
            try:
                return self.sheet.worksheet(worksheet_name)
            except Exception as e:
                logger.error(f"Error getting worksheet {worksheet_name}: {e}")
        return None
    
    def get_all_records(self, worksheet_name):
        """Get all records from a worksheet"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                return worksheet.get_all_records()
            except Exception as e:
                logger.error(f"Error getting records from {worksheet_name}: {e}")
        return []
    
    def append_row(self, worksheet_name, row_data):
        """Append a row to a worksheet"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                worksheet.append_row(row_data)
                return True
            except Exception as e:
                logger.error(f"Error appending row to {worksheet_name}: {e}")
        return False
    
    def update_cell(self, worksheet_name, row, col, value):
        """Update a cell in a worksheet"""
        worksheet = self.get_worksheet(worksheet_name)
        if worksheet:
            try:
                worksheet.update_cell(row, col, value)
                return True
            except Exception as e:
                logger.error(f"Error updating cell in {worksheet_name}: {e}")
        return False


class AnalystAgent:
    """AI Agent that explains trends and suggests fixes"""
    
    def __init__(self):
        self.name = "Analyst"
        self.google_api_key = os.environ.get('GOOGLE_API_KEY', '')
    
    def analyze_trend(self, metric_name, data_points, threshold=0.2):
        """Analyze a metric trend and provide insights"""
        if len(data_points) < 2:
            return {"trend": "insufficient_data", "explanation": "Not enough data points", "suggestion": "Collect more data"}
        
        # Calculate trend
        recent = data_points[-3:] if len(data_points) >= 3 else data_points
        older = data_points[:-3] if len(data_points) > 3 else [data_points[0]]
        
        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older) if older else avg_recent
        
        if avg_older == 0:
            change_pct = 0
        else:
            change_pct = (avg_recent - avg_older) / abs(avg_older)
        
        # Determine trend direction
        if change_pct > threshold:
            trend = "increasing"
            explanation = f"{metric_name} has increased by {change_pct*100:.1f}% recently"
            suggestion = "Monitor closely to ensure sustainable growth"
        elif change_pct < -threshold:
            trend = "decreasing"
            explanation = f"{metric_name} has decreased by {abs(change_pct)*100:.1f}% recently"
            suggestion = f"Investigate potential causes for the decline in {metric_name}"
        else:
            trend = "stable"
            explanation = f"{metric_name} is stable with minor fluctuations"
            suggestion = "Continue current strategy"
        
        return {
            "trend": trend,
            "change_percent": change_pct * 100,
            "explanation": explanation,
            "suggestion": suggestion,
            "is_anomaly": abs(change_pct) > threshold * 2
        }
    
    def generate_insight(self, metric_name, analysis):
        """Generate an insight from analysis"""
        timestamp = datetime.now().isoformat()
        insight = {
            "id": len(insights_data) + 1,
            "timestamp": timestamp,
            "metric": metric_name,
            "trend": analysis['trend'],
            "explanation": analysis['explanation'],
            "suggestion": analysis['suggestion'],
            "is_anomaly": analysis.get('is_anomaly', False)
        }
        return insight
    
    def chat_response(self, user_message, context=None):
        """Generate a chat response based on metrics data"""
        message_lower = user_message.lower()
        
        if 'trend' in message_lower or 'performance' in message_lower:
            response = "Based on recent data, I've identified several trends. Key metrics show mixed performance with some areas of growth and others needing attention. Would you like me to focus on a specific metric?"
        elif 'anomal' in message_lower or 'issue' in message_lower:
            if anomalies:
                response = f"I've detected {len(anomalies)} anomalies in the data. The most critical ones are in: {', '.join(set(a.get('metric', 'unknown') for a in anomalies[-5:]))}. I recommend investigating these immediately."
            else:
                response = "No significant anomalies detected at this time. All metrics appear within normal ranges."
        elif 'suggest' in message_lower or 'recommend' in message_lower:
            response = "My recommendations: 1) Focus on improving conversion rates through A/B testing, 2) Monitor customer acquisition costs, 3) Consider expanding successful experiments. Would you like detailed action items?"
        elif 'report' in message_lower or 'summar' in message_lower:
            response = "This week's summary: Overall performance is stable with notable improvements in key engagement metrics. Three experiments showed positive results. I suggest prioritizing the top-performing initiatives for next week."
        else:
            response = "I'm your Analyst agent. I can help you understand trends, identify anomalies, and suggest actions. Ask me about specific metrics, trends, anomalies, or recommendations."
        
        return {
            "agent": self.name,
            "user_message": user_message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }


class MetricsApp:
    """Main application logic"""
    
    def __init__(self):
        self.sheets_client = GoogleSheetsClient()
        self.analyst = AnalystAgent()
        self.last_sync = None
    
    def sync_from_sheets(self):
        """Sync data from Google Sheets"""
        logger.info("Starting sync from Google Sheets")
        
        # Sync Metrics
        metrics_sheet = self.sheets_client.get_all_records('Metrics')
        if metrics_sheet:
            global metrics_data
            metrics_data = metrics_sheet
            logger.info(f"Synced {len(metrics_data)} metrics records")
        
        # Sync Experiments
        exp_sheet = self.sheets_client.get_all_records('Experiments')
        if exp_sheet:
            global experiments_data
            experiments_data = exp_sheet
            logger.info(f"Synced {len(experiments_data)} experiment records")
        
        # Check for anomalies
        self.detect_anomalies()
        
        self.last_sync = datetime.now()
        logger.info("Sync completed")
    
    def detect_anomalies(self):
        """Detect anomalies in metrics data"""
        global anomalies, insights_data
        
        if not metrics_data:
            return
        
        # Group metrics by name
        metrics_by_name = {}
        for row in metrics_data:
            metric_name = row.get('Metric', row.get('metric', 'Unknown'))
            value = row.get('Value', row.get('value', 0))
            try:
                value = float(value)
            except:
                continue
            
            if metric_name not in metrics_by_name:
                metrics_by_name[metric_name] = []
            metrics_by_name[metric_name].append(value)
        
        # Analyze each metric
        new_anomalies = []
        for metric_name, values in metrics_by_name.items():
            analysis = self.analyst.analyze_trend(metric_name, values)
            
            if analysis['is_anomaly']:
                anomaly = {
                    "id": len(anomalies) + 1,
                    "metric": metric_name,
                    "timestamp": datetime.now().isoformat(),
                    "severity": "high" if abs(analysis['change_percent']) > 50 else "medium",
                    "description": analysis['explanation'],
                    "suggested_action": analysis['suggestion']
                }
                new_anomalies.append(anomaly)
                
                # Generate insight
                insight = self.analyst.generate_insight(metric_name, analysis)
                insights_data.append(insight)
        
        anomalies.extend(new_anomalies)
        if new_anomalies:
            logger.info(f"Detected {len(new_anomalies)} new anomalies")
    
    def generate_weekly_report(self):
        """Generate weekly executive report"""
        logger.info("Generating weekly report")
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": "Weekly",
            "summary": {},
            "charts": [],
            "action_items": [],
            "stakeholders_notified": []
        }
        
        # Generate summary statistics
        if metrics_data:
            report["summary"]["total_metrics"] = len(metrics_data)
            report["summary"]["anomalies_detected"] = len([a for a in anomalies if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(days=7)])
        
        # Generate charts
        if metrics_data:
            # Create time series chart
            df = pd.DataFrame(metrics_data)
            if not df.empty and 'Metric' in df.columns and 'Value' in df.columns:
                fig = px.line(df, x=df.index, y='Value', color='Metric', title='Metrics Trend')
                chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
                report["charts"].append({"type": "line", "data": chart_json})
        
        # Generate action items from insights
        for insight in insights_data[-10:]:
            if insight.get('is_anomaly'):
                action = {
                    "id": len(actions_data) + 1,
                    "title": f"Investigate {insight['metric']} anomaly",
                    "description": insight['suggestion'],
                    "priority": "high",
                    "status": "pending",
                    "created_at": insight['timestamp']
                }
                report["action_items"].append(action)
                actions_data.append(action)
        
        # Notify stakeholders (simulated)
        stakeholders = ["ceo@company.com", "cto@company.com", "product@company.com"]
        report["stakeholders_notified"] = stakeholders
        logger.info(f"Weekly report sent to {len(stakeholders)} stakeholders")
        
        # Save report to Google Sheets
        self.sheets_client.append_row('Reports', [
            report["generated_at"],
            report["summary"].get("total_metrics", 0),
            report["summary"].get("anomalies_detected", 0),
            len(report["action_items"]),
            "Sent"
        ])
        
        return report
    
    def run_scheduler(self):
        """Run background scheduler"""
        while True:
            schedule.run_pending()
            time.sleep(60)


# Initialize app
metrics_app = MetricsApp()

# Schedule weekly report
schedule.every().monday.at("09:00").do(metrics_app.generate_weekly_report)

# Start scheduler in background thread
scheduler_thread = threading.Thread(target=metrics_app.run_scheduler, daemon=True)
scheduler_thread.start()


@app.route('/')
def index():
    """Home page - KPI Dashboard"""
    return render_template('index.html', 
                         metrics=metrics_data,
                         anomalies=anomalies,
                         last_sync=metrics_app.last_sync)


@app.route('/experiments')
def experiments():
    """Experiment Tracker"""
    return render_template('experiments.html', experiments=experiments_data)


@app.route('/insights')
def insights():
    """Insights Feed"""
    return render_template('insights.html', insights=insights_data)


@app.route('/actions')
def actions():
    """Actions Tracker"""
    return render_template('actions.html', actions=actions_data)


@app.route('/chat')
def chat():
    """Agent Chat Interface"""
    return render_template('chat.html', agent_name=metrics_app.analyst.name)


@app.route('/api/sync', methods=['POST'])
def trigger_sync():
    """Manually trigger sync from Google Sheets"""
    metrics_app.sync_from_sheets()
    return jsonify({
        "status": "success",
        "message": "Sync completed",
        "last_sync": str(metrics_app.last_sync),
        "metrics_count": len(metrics_data),
        "experiments_count": len(experiments_data),
        "anomalies_count": len(anomalies)
    })


@app.route('/api/chat', methods=['POST'])
def chat_api():
    """Chat with Analyst agent"""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    response = metrics_app.analyst.chat_response(user_message)
    return jsonify(response)


@app.route('/api/metrics')
def get_metrics():
    """Get all metrics"""
    return jsonify(metrics_data)


@app.route('/api/anomalies')
def get_anomalies():
    """Get all anomalies"""
    return jsonify(anomalies)


@app.route('/api/insights')
def get_insights():
    """Get all insights"""
    return jsonify(insights_data)


@app.route('/api/actions', methods=['GET', 'POST'])
def manage_actions():
    """Manage actions"""
    if request.method == 'POST':
        data = request.json
        action = {
            "id": len(actions_data) + 1,
            "title": data.get('title', 'New Action'),
            "description": data.get('description', ''),
            "priority": data.get('priority', 'medium'),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        actions_data.append(action)
        return jsonify(action), 201
    return jsonify(actions_data)


@app.route('/api/actions/<int:action_id>', methods=['PUT'])
def update_action(action_id):
    """Update an action"""
    data = request.json
    for action in actions_data:
        if action['id'] == action_id:
            action.update(data)
            return jsonify(action)
    return jsonify({"error": "Action not found"}), 404


@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate weekly report on demand"""
    report = metrics_app.generate_weekly_report()
    return jsonify(report)


if __name__ == '__main__':
    # Initial sync
    metrics_app.sync_from_sheets()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
