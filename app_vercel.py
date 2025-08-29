"""
Vercel-optimized Flask dashboard application for audio transcription automation system.
Provides web interface for monitoring and managing transcriptions in a serverless environment.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd

# Use Vercel-specific config
from config_vercel import config
from analytics import analytics

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG_MODE

# Ensure directories exist
config.create_directories()

# Mock processor class for serverless demo
class MockAudioProcessor:
    """Mock audio processor for serverless demo."""
    
    def get_processing_stats(self):
        """Return mock processing stats."""
        return {
            'total_files': 172,
            'processed_files': 172,
            'success_rate': 100.0,
            'avg_processing_time': 2.5,
            'total_duration': 7200,  # 2 hours in seconds
            'last_processed': '2025-08-28 15:30:00'
        }
    
    def start_batch_processing(self):
        """Mock batch processing start."""
        return True
    
    def stop_batch_processing(self):
        """Mock batch processing stop."""
        return True
    
    def get_processing_status(self):
        """Mock processing status."""
        return {
            'is_running': False,
            'current_file': None,
            'progress': 100
        }

# Initialize mock processor for serverless
processor = MockAudioProcessor()

@app.route('/')
def dashboard():
    """Main dashboard page."""
    try:
        stats = processor.get_processing_stats()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('dashboard.html', stats={})

@app.route('/api/data')
def api_data():
    """Get all transcription data as JSON."""
    try:
        if not config.CSV_FILE.exists():
            return jsonify({'data': [], 'total': 0})
        
        df = pd.read_csv(config.CSV_FILE)
        
        # Convert to records and format
        records = []
        for _, row in df.iterrows():
            record = {
                'timestamp': row.get('timestamp', ''),
                'filename': row.get('filename', ''),
                'call_date': row.get('call_date', ''),
                'call_time': row.get('call_time', ''),
                'phone_number': row.get('phone_number', ''),
                'call_status': row.get('call_status', ''),
                'agent_name': row.get('agent_name', ''),
                'file_size': row.get('file_size', ''),
                'file_size_bytes': 0,  # Mock value
                'duration': row.get('duration', ''),
                'duration_seconds': row.get('estimated_duration_seconds', 0),
                'summary': row.get('summary', ''),
                'intent': row.get('intent', ''),
                'sub_intent': row.get('sub_intent', ''),
                'primary_disposition': row.get('primary_disposition', ''),
                'secondary_disposition': row.get('secondary_disposition', ''),
                'status': row.get('status', ''),
                'processing_time': row.get('processing_time', ''),
                'processing_time_seconds': 0,  # Mock value
                'error_message': row.get('error_message', ''),
                'transcription': row.get('transcription', '')
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
    """Mock classify dispositions endpoint."""
    return jsonify({
        'message': 'Disposition classification completed',
        'classified': 172,
        'success': True
    })

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
            'speaker_count': row.get('speaker_count', 1)
        })
        
    except Exception as e:
        logger.error(f"Error getting transcription for {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/start', methods=['POST'])
def api_start_processing():
    """Mock start processing endpoint."""
    return jsonify({'message': 'Processing started (demo mode)', 'success': True})

@app.route('/api/processing/stop', methods=['POST'])
def api_stop_processing():
    """Mock stop processing endpoint."""
    return jsonify({'message': 'Processing stopped (demo mode)', 'success': True})

@app.route('/api/processing/status')
def api_processing_status():
    """Mock processing status endpoint."""
    return jsonify(processor.get_processing_status())

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

# Health check endpoint for Vercel
@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'serverless'
    })

if __name__ == "__main__":
    # This will only run locally, not on Vercel
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG_MODE)