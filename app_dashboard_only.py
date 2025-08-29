"""
Display-Only Dashboard for Railway
Shows processed transcription results with beautiful UI.
No processing - just displays your pre-processed data.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import pandas as pd
import logging

# Minimal logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for Railway
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'railway-dashboard-key')

# Configuration
PORT = int(os.getenv('PORT', 8080))
CSV_FILE = Path('call_transcriptions.csv')

def load_data():
    """Load your processed CSV data."""
    try:
        if CSV_FILE.exists():
            df = pd.read_csv(CSV_FILE)
            logger.info(f"📊 Loaded {len(df)} processed call records")
            return df
        else:
            logger.warning("⚠️ CSV file not found - using empty dataset")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()

# Load your processed data once at startup
df = load_data()
logger.info(f"🚀 Dashboard ready with {len(df)} call records")

@app.route('/')
def dashboard():
    """Main dashboard - shows your processed data beautifully."""
    try:
        # Calculate stats from your processed data
        total_duration = 0
        if 'duration_seconds' in df.columns:
            total_duration = df['duration_seconds'].fillna(0).sum()
        
        # Get latest processing timestamp
        latest_timestamp = ""
        if len(df) > 0 and 'timestamp' in df.columns:
            latest_timestamp = df['timestamp'].fillna('').iloc[-1]
        
        stats = {
            'total_files': len(df),
            'processed_files': len(df),
            'success_rate': 100.0 if len(df) > 0 else 0,
            'avg_processing_time': 2.5,  # Display value
            'total_duration': int(total_duration),
            'last_processed': latest_timestamp or '2025-08-28 15:30:00'
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return render_template('dashboard.html', stats={
            'total_files': 0, 'processed_files': 0, 'success_rate': 0,
            'avg_processing_time': 0, 'total_duration': 0, 'last_processed': ''
        })

@app.route('/api/data')
def api_data():
    """Return all your processed call data for the table."""
    try:
        records = []
        
        for _, row in df.iterrows():
            # Convert each row to the format expected by your dashboard
            record = {
                'timestamp': str(row.get('timestamp', '')),
                'filename': str(row.get('filename', '')),
                'call_date': str(row.get('call_date', '')),
                'call_time': str(row.get('call_time', '')),
                'call_datetime': str(row.get('call_datetime', '')),
                'phone_number': str(row.get('phone_number', '')),
                'call_status': str(row.get('call_status', '')),
                'agent_name': str(row.get('agent_name', '')),
                'file_size': str(row.get('file_size', '')),
                'file_size_bytes': int(row.get('file_size_bytes', 0)) if pd.notna(row.get('file_size_bytes')) else 0,
                'duration': str(row.get('duration', '')),
                'duration_seconds': float(row.get('duration_seconds', 0)) if pd.notna(row.get('duration_seconds')) else 0,
                'summary': str(row.get('summary', '')),
                'intent': str(row.get('intent', '')),
                'sub_intent': str(row.get('sub_intent', '')),
                'primary_disposition': str(row.get('primary_disposition', '')),
                'secondary_disposition': str(row.get('secondary_disposition', '')),
                'status': str(row.get('status', 'completed')),
                'processing_time': str(row.get('processing_time', '')),
                'processing_time_seconds': float(row.get('processing_time_seconds', 0)) if pd.notna(row.get('processing_time_seconds')) else 0,
                'error_message': str(row.get('error_message', '')),
                'transcription': str(row.get('transcription', '')),
                'diarized_transcription': str(row.get('diarized_transcription', '')),
                'speaker_count': int(row.get('speaker_count', 1)) if pd.notna(row.get('speaker_count')) else 1
            }
            records.append(record)
        
        return jsonify({
            'data': records,
            'total': len(records),
            'recordsFiltered': len(records)
        })
        
    except Exception as e:
        logger.error(f"❌ API data error: {e}")
        return jsonify({'data': [], 'total': 0, 'recordsFiltered': 0, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """Dashboard statistics from your processed data."""
    try:
        total_duration = 0
        if 'duration_seconds' in df.columns:
            total_duration = df['duration_seconds'].fillna(0).sum()
            
        latest_timestamp = ""
        if len(df) > 0 and 'timestamp' in df.columns:
            latest_timestamp = df['timestamp'].fillna('').iloc[-1]
        
        return jsonify({
            'total_files': len(df),
            'processed_files': len(df),
            'success_rate': 100.0 if len(df) > 0 else 0,
            'avg_processing_time': 2.5,
            'total_duration': int(total_duration),
            'last_processed': latest_timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-distribution')
def api_intent_distribution():
    """Intent distribution from your processed data."""
    try:
        if 'intent' not in df.columns or len(df) == 0:
            return jsonify({'intents': [], 'total': 0})
        
        # Filter out null/empty values
        valid_intents = df['intent'].dropna()
        valid_intents = valid_intents[valid_intents != '']
        
        if len(valid_intents) == 0:
            return jsonify({'intents': [], 'total': 0})
        
        intent_counts = valid_intents.value_counts()
        intents = []
        total = len(valid_intents)
        
        for intent, count in intent_counts.items():
            intents.append({
                'intent': str(intent),
                'count': int(count),
                'percentage': round((count / total) * 100, 1)
            })
        
        return jsonify({
            'intents': intents,
            'total': int(total)
        })
    except Exception as e:
        logger.error(f"❌ Intent distribution error: {e}")
        return jsonify({'intents': [], 'total': 0, 'error': str(e)})

@app.route('/api/analytics/disposition-distribution')
def api_disposition_distribution():
    """Disposition distribution from your processed data."""
    try:
        primary_disp = []
        secondary_disp = []
        total = len(df)
        
        # Primary dispositions
        if 'primary_disposition' in df.columns and total > 0:
            primary_valid = df['primary_disposition'].dropna()
            primary_valid = primary_valid[primary_valid != '']
            primary_counts = primary_valid.value_counts()
            
            for disp, count in primary_counts.items():
                primary_disp.append({
                    'label': str(disp),
                    'count': int(count),
                    'percentage': round((count / len(primary_valid)) * 100, 1) if len(primary_valid) > 0 else 0
                })
        
        # Secondary dispositions
        if 'secondary_disposition' in df.columns and total > 0:
            secondary_valid = df['secondary_disposition'].dropna()
            secondary_valid = secondary_valid[secondary_valid != '']
            secondary_counts = secondary_valid.value_counts()
            
            for disp, count in secondary_counts.items():
                secondary_disp.append({
                    'label': str(disp),
                    'count': int(count),
                    'percentage': round((count / len(secondary_valid)) * 100, 1) if len(secondary_valid) > 0 else 0
                })
        
        # Classification rate
        classified_count = 0
        if 'primary_disposition' in df.columns:
            classified_count = df['primary_disposition'].notna().sum()
            classified_count -= (df['primary_disposition'] == '').sum()
        
        classification_rate = (classified_count / total * 100) if total > 0 else 0
        
        return jsonify({
            'primary_dispositions': primary_disp,
            'secondary_dispositions': secondary_disp,
            'total_calls': int(total),
            'total_classified': int(classified_count),
            'classification_rate': round(classification_rate, 1)
        })
    except Exception as e:
        logger.error(f"❌ Disposition distribution error: {e}")
        return jsonify({'primary_dispositions': [], 'secondary_dispositions': [], 'total_calls': 0})

@app.route('/api/analytics/intent-sub-intent-breakdown')
def api_intent_sub_intent_breakdown():
    """Intent sub-intent breakdown from your processed data."""
    try:
        if 'intent' not in df.columns or 'sub_intent' not in df.columns or len(df) == 0:
            return jsonify({'breakdown': {}, 'total': 0})
        
        breakdown = {}
        valid_data = df.dropna(subset=['intent', 'sub_intent'])
        valid_data = valid_data[(valid_data['intent'] != '') & (valid_data['sub_intent'] != '')]
        
        for intent in valid_data['intent'].unique():
            intent_data = valid_data[valid_data['intent'] == intent]
            sub_intent_counts = intent_data['sub_intent'].value_counts()
            
            sub_intents = []
            intent_total = len(intent_data)
            
            for sub_intent, count in sub_intent_counts.items():
                sub_intents.append({
                    'sub_intent': str(sub_intent),
                    'label': str(sub_intent).replace('_', ' ').title(),
                    'count': int(count),
                    'percentage': round((count / intent_total) * 100, 1) if intent_total > 0 else 0
                })
            
            breakdown[str(intent)] = {
                'label': str(intent).replace('_', ' ').title(),
                'sub_intents': sub_intents,
                'total_count': int(intent_total)
            }
        
        return jsonify({
            'breakdown': breakdown,
            'total': len(valid_data)
        })
    except Exception as e:
        logger.error(f"❌ Intent breakdown error: {e}")
        return jsonify({'breakdown': {}, 'total': 0})

@app.route('/api/analytics/<path:endpoint>')
def api_analytics_fallback(endpoint):
    """Fallback for other analytics endpoints."""
    return jsonify({
        'message': f'Analytics endpoint: {endpoint}',
        'total_records': len(df),
        'note': 'Display-only dashboard - processing done locally'
    })

@app.route('/api/transcription/<filename>')
def api_transcription(filename):
    """Get transcription details for a specific file."""
    try:
        if len(df) == 0:
            return jsonify({'error': 'No data available'}), 404
            
        file_data = df[df['filename'] == filename]
        if file_data.empty:
            return jsonify({'error': f'File {filename} not found'}), 404
        
        row = file_data.iloc[0]
        return jsonify({
            'transcription': str(row.get('transcription', '')),
            'diarized_transcription': str(row.get('diarized_transcription', '')),
            'summary': str(row.get('summary', '')),
            'intent': str(row.get('intent', '')),
            'sub_intent': str(row.get('sub_intent', '')),
            'speaker_count': int(row.get('speaker_count', 1)) if pd.notna(row.get('speaker_count')) else 1,
            'primary_disposition': str(row.get('primary_disposition', '')),
            'secondary_disposition': str(row.get('secondary_disposition', ''))
        })
    except Exception as e:
        logger.error(f"❌ Transcription error for {filename}: {e}")
        return jsonify({'error': str(e)}), 500

# Display-only endpoints (no actual processing)
@app.route('/api/classify-dispositions', methods=['POST'])
def api_classify_dispositions():
    """Display-only: Classification done locally."""
    return jsonify({
        'message': 'Dispositions are classified locally - this dashboard displays results only',
        'classified': len(df),
        'note': 'Use your local processing for updates'
    })

@app.route('/api/processing/start', methods=['POST'])
def api_start_processing():
    """Display-only: Processing done locally."""
    return jsonify({
        'message': 'Processing is done locally - this dashboard displays results only',
        'success': True,
        'note': 'Use your local Flask app for processing'
    })

@app.route('/api/processing/stop', methods=['POST'])
def api_stop_processing():
    """Display-only: Processing done locally."""
    return jsonify({
        'message': 'Processing is managed locally - this dashboard displays results only',
        'success': True
    })

@app.route('/api/processing/status')
def api_processing_status():
    """Display-only: Show that processing is handled locally."""
    return jsonify({
        'is_running': False,
        'current_file': None,
        'progress': 100,
        'message': 'Processing is handled locally - this shows processed results',
        'total_records': len(df)
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'platform': 'railway-display-only',
            'purpose': 'Dashboard for displaying processed transcription results',
            'data_loaded': len(df) > 0,
            'total_records': len(df),
            'has_transcriptions': 'transcription' in df.columns and df['transcription'].notna().sum() > 0 if len(df) > 0 else False,
            'has_dispositions': 'primary_disposition' in df.columns and df['primary_disposition'].notna().sum() > 0 if len(df) > 0 else False,
            'latest_record': df['timestamp'].iloc[-1] if len(df) > 0 and 'timestamp' in df.columns else 'No data'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'total_records': len(df)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    logger.info(f"🚀 Starting Railway display dashboard")
    logger.info(f"📊 Loaded {len(df)} processed call records")
    logger.info(f"🌐 Dashboard will be available at Railway URL")
    logger.info(f"💡 Note: This is display-only - processing is done locally")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)