"""
Minimal Vercel-optimized Flask app for audio transcription dashboard.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('SECRET_KEY', 'vercel-demo-key')

# Sample data for demo
SAMPLE_DATA = [
    {
        'timestamp': '2025-08-28 10:30:00',
        'filename': 'sample_call_1.mp3',
        'call_date': '2025-08-28',
        'call_time': '10:30',
        'phone_number': '555-0001',
        'call_status': 'answered',
        'agent_name': 'Demo Agent',
        'file_size': '1.2 MB',
        'duration': '2m 0s',
        'duration_seconds': 120,
        'transcription': 'Customer called about roof repair services',
        'summary': 'Customer needs roof repair after storm damage',
        'intent': 'ROOFING',
        'sub_intent': 'ROOF_REPAIR',
        'status': 'completed',
        'processing_time': '3.2s',
        'primary_disposition': 'QUALIFIED_LEAD',
        'secondary_disposition': 'IMMEDIATE'
    },
    {
        'timestamp': '2025-08-28 11:15:00',
        'filename': 'sample_call_2.mp3',
        'call_date': '2025-08-28',
        'call_time': '11:15',
        'phone_number': '555-0002',
        'call_status': 'answered',
        'agent_name': 'Demo Agent',
        'file_size': '890 KB',
        'duration': '1m 29s',
        'duration_seconds': 89,
        'transcription': 'Inquiry about window replacement quote',
        'summary': 'Homeowner requesting window replacement quotes',
        'intent': 'WINDOWS_DOORS',
        'sub_intent': 'WINDOW_REPLACEMENT',
        'status': 'completed',
        'processing_time': '2.8s',
        'primary_disposition': 'APPOINTMENT_SET',
        'secondary_disposition': 'FUTURE'
    },
    {
        'timestamp': '2025-08-28 12:00:00',
        'filename': 'sample_call_3.mp3',
        'call_date': '2025-08-28',
        'call_time': '12:00',
        'phone_number': '555-0003',
        'call_status': 'voicemail',
        'agent_name': 'Demo Agent',
        'file_size': '450 KB',
        'duration': '45s',
        'duration_seconds': 45,
        'transcription': 'Left voicemail about kitchen remodeling',
        'summary': 'Kitchen remodeling inquiry left on voicemail',
        'intent': 'KITCHEN_BATH',
        'sub_intent': 'KITCHEN_REMODEL',
        'status': 'completed',
        'processing_time': '1.5s',
        'primary_disposition': 'CALLBACK_REQUESTED',
        'secondary_disposition': 'FOLLOW_UP_REQUIRED'
    }
]

@app.route('/')
def dashboard():
    """Main dashboard page."""
    stats = {
        'total_files': 172,
        'processed_files': 172,
        'success_rate': 100.0,
        'avg_processing_time': 2.5,
        'total_duration': 7200,
        'last_processed': '2025-08-28 15:30:00'
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/api/data')
def api_data():
    """Get sample data."""
    return jsonify({
        'data': SAMPLE_DATA,
        'total': len(SAMPLE_DATA),
        'recordsFiltered': len(SAMPLE_DATA)
    })

@app.route('/api/stats')
def api_stats():
    """Get stats."""
    return jsonify({
        'total_files': 172,
        'processed_files': 172,
        'success_rate': 100.0,
        'avg_processing_time': 2.5,
        'total_duration': 7200
    })

@app.route('/api/analytics/intent-distribution')
def api_intent_distribution():
    """Get intent distribution."""
    return jsonify({
        'intents': [
            {'intent': 'ROOFING', 'count': 49, 'percentage': 28.5},
            {'intent': 'OTHER', 'count': 92, 'percentage': 53.5},
            {'intent': 'WINDOWS_DOORS', 'count': 15, 'percentage': 8.7},
            {'intent': 'KITCHEN_BATH', 'count': 7, 'percentage': 4.1},
            {'intent': 'QUOTE_REQUEST', 'count': 12, 'percentage': 7.0}
        ],
        'total': 172
    })

@app.route('/api/analytics/disposition-distribution')
def api_disposition_distribution():
    """Get disposition distribution."""
    return jsonify({
        'classification_rate': 100.0,
        'primary_dispositions': [
            {'count': 20, 'label': 'APPOINTMENT_SET', 'percentage': 11.6},
            {'count': 19, 'label': 'CALLBACK_REQUESTED', 'percentage': 11.0},
            {'count': 19, 'label': 'OTHER', 'percentage': 11.0},
            {'count': 15, 'label': 'QUALIFIED_LEAD', 'percentage': 8.7}
        ],
        'secondary_dispositions': [
            {'count': 23, 'label': 'OTHER', 'percentage': 13.4},
            {'count': 19, 'label': 'IMMEDIATE', 'percentage': 11.0},
            {'count': 17, 'label': 'TRUST_OBJECTION', 'percentage': 9.9}
        ],
        'total_calls': 172
    })

@app.route('/api/analytics/intent-sub-intent-breakdown')
def api_intent_sub_intent_breakdown():
    """Get intent breakdown."""
    return jsonify({
        'breakdown': {
            'ROOFING': {
                'label': 'Roofing',
                'sub_intents': [
                    {'count': 33, 'label': 'Roof Repair', 'percentage': 67.3, 'sub_intent': 'ROOF_REPAIR'},
                    {'count': 12, 'label': 'Roof Replacement', 'percentage': 24.5, 'sub_intent': 'ROOF_REPLACEMENT'}
                ],
                'total_count': 49
            },
            'OTHER': {
                'label': 'Other',
                'sub_intents': [
                    {'count': 69, 'label': 'General Inquiry', 'percentage': 75.0, 'sub_intent': 'GENERAL_INQUIRY'},
                    {'count': 8, 'label': 'Test Call', 'percentage': 8.7, 'sub_intent': 'TEST_CALL'}
                ],
                'total_count': 92
            }
        },
        'total': 172
    })

@app.route('/api/health')
def health_check():
    """Health check."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

# Catch all other analytics endpoints
@app.route('/api/analytics/<path:endpoint>')
def api_analytics_fallback(endpoint):
    """Fallback for other analytics endpoints."""
    return jsonify({'message': f'Analytics endpoint {endpoint} - demo data', 'data': []})

if __name__ == "__main__":
    app.run(debug=True)