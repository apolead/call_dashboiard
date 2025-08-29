"""
Railway-optimized Flask dashboard application for audio transcription automation system.
Uses your existing data and full functionality with persistent storage.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd

# Use Railway-specific config that maintains your existing data
from config_railway import config
from processor import AudioProcessor
from s3_manager import s3_manager
from analytics import analytics

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG_MODE

# Ensure directories exist
config.create_directories()

# Initialize processor with your existing functionality
processor = AudioProcessor()

@app.route('/')
def dashboard():
    """Main dashboard page with your existing stats."""
    try:
        stats = processor.get_processing_stats()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('dashboard.html', stats={})

@app.route('/api/data')
def api_data():
    """Get all transcription data as JSON - uses your existing CSV file."""
    try:
        if not config.CSV_FILE.exists():
            return jsonify({'data': [], 'total': 0})
        
        df = pd.read_csv(config.CSV_FILE)
        
        # Convert to records and format (same as your original app.py)
        records = []
        for _, row in df.iterrows():
            record = {
                'timestamp': row.get('timestamp', ''),
                'filename': row.get('filename', ''),
                'call_date': row.get('call_date', ''),
                'call_time': row.get('call_time', ''),
                'call_datetime': row.get('call_datetime', ''),
                'phone_number': row.get('phone_number', ''),
                'call_status': row.get('call_status', ''),
                'agent_name': row.get('agent_name', ''),
                'file_size': row.get('file_size', ''),
                'file_size_bytes': row.get('file_size_bytes', 0),
                'duration': row.get('duration', ''),
                'duration_seconds': row.get('duration_seconds', 0),
                'summary': row.get('summary', ''),
                'intent': row.get('intent', ''),
                'sub_intent': row.get('sub_intent', ''),
                'primary_disposition': row.get('primary_disposition', ''),
                'secondary_disposition': row.get('secondary_disposition', ''),
                'status': row.get('status', ''),
                'processing_time': row.get('processing_time', ''),
                'processing_time_seconds': row.get('processing_time_seconds', 0),
                'error_message': row.get('error_message', ''),
                'transcription': row.get('transcription', ''),
                'diarized_transcription': row.get('diarized_transcription', ''),
                'speaker_count': row.get('speaker_count', 1)
            }
            records.append(record)
        
        return jsonify({
            'data': records,
            'total': len(records),
            'recordsFiltered': len(records)
        })
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Get processing statistics."""
    try:
        stats = processor.get_processing_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

# All your existing analytics endpoints
@app.route('/api/analytics/intent-distribution')
def api_intent_distribution():
    """Get intent distribution analytics."""
    try:
        result = analytics.get_intent_distribution()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting intent distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/sub-intent-distribution')
def api_sub_intent_distribution():
    """Get sub-intent distribution analytics."""
    try:
        result = analytics.get_sub_intent_distribution()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting sub-intent distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/daily-trends')
def api_daily_trends():
    """Get daily trends analytics."""
    try:
        days = int(request.args.get('days', 30))
        result = analytics.get_daily_trends(days)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting daily trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/duration-distribution')
def api_duration_distribution():
    """Get call duration distribution analytics."""
    try:
        result = analytics.get_duration_distribution()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting duration distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/speaker-distribution')
def api_speaker_distribution():
    """Get speaker count distribution analytics."""
    try:
        result = analytics.get_speaker_distribution()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting speaker distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/drop-off-analysis')
def api_drop_off_analysis():
    """Get call drop-off analysis."""
    try:
        result = analytics.get_drop_off_analysis()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting drop-off analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-sub-intent-breakdown')
def api_intent_sub_intent_breakdown():
    """Get intent sub-intent breakdown analytics."""
    try:
        result = analytics.get_intent_sub_intent_breakdown()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting intent sub-intent breakdown: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/disposition-distribution')
def api_disposition_distribution():
    """Get disposition distribution analytics."""
    try:
        result = analytics.get_disposition_distribution()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting disposition distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classify-dispositions', methods=['POST'])
def api_classify_dispositions():
    """Classify dispositions using OpenAI."""
    try:
        # Use your existing classification logic
        result = processor.classify_dispositions()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error classifying dispositions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcription/<filename>')
def api_transcription(filename):
    """Get transcription for a specific file."""
    try:
        if not config.CSV_FILE.exists():
            return jsonify({'error': 'No data file found'}), 404
        
        df = pd.read_csv(config.CSV_FILE)
        file_data = df[df['filename'] == filename]
        
        if file_data.empty:
            return jsonify({'error': 'File not found'}), 404
        
        row = file_data.iloc[0]
        return jsonify({
            'transcription': row.get('transcription', ''),
            'diarized_transcription': row.get('diarized_transcription', ''),
            'summary': row.get('summary', ''),
            'intent': row.get('intent', ''),
            'sub_intent': row.get('sub_intent', ''),
            'speaker_count': row.get('speaker_count', 1),
            'primary_disposition': row.get('primary_disposition', ''),
            'secondary_disposition': row.get('secondary_disposition', '')
        })
        
    except Exception as e:
        logger.error(f"Error getting transcription for {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/start', methods=['POST'])
def api_start_processing():
    """Start batch processing."""
    try:
        result = processor.start_batch_processing()
        return jsonify({'message': 'Processing started successfully', 'success': True})
    except Exception as e:
        logger.error(f"Error starting processing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/stop', methods=['POST'])
def api_stop_processing():
    """Stop batch processing."""
    try:
        result = processor.stop_batch_processing()
        return jsonify({'message': 'Processing stopped successfully', 'success': True})
    except Exception as e:
        logger.error(f"Error stopping processing: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/status')
def api_processing_status():
    """Get processing status."""
    try:
        status = processor.get_processing_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Health check for Railway
@app.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'platform': 'railway',
        'data_file_exists': config.CSV_FILE.exists(),
        'total_records': len(pd.read_csv(config.CSV_FILE)) if config.CSV_FILE.exists() else 0
    })

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    # Railway deployment
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG_MODE)