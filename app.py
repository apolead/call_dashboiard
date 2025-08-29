"""
Flask dashboard application for audio transcription automation system.
Provides web interface for monitoring and managing transcriptions.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import pandas as pd
from config import config
from processor import AudioProcessor
from s3_manager import s3_manager
from analytics import analytics

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config['DEBUG'] = config.DEBUG_MODE

# Initialize processor
processor = AudioProcessor()

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
                'timestamp': row['timestamp'],
                'filename': row['filename'],
                'file_size': format_file_size(row['file_size']),
                'file_size_bytes': row['file_size'],
                'duration': format_duration(row['duration']),
                'duration_seconds': row['duration'],
                'transcription': row['transcription'] if pd.notna(row['transcription']) else 'No transcription available',
                'summary': row['summary'] if pd.notna(row['summary']) else '',
                'intent': row['intent'] if pd.notna(row['intent']) else 'OTHER',
                'sub_intent': row['sub_intent'] if pd.notna(row['sub_intent']) else 'GENERAL_INQUIRY',
                'primary_disposition': row['primary_disposition'] if pd.notna(row['primary_disposition']) else '',
                'secondary_disposition': row['secondary_disposition'] if pd.notna(row['secondary_disposition']) else '',
                'status': row['status'],
                'processing_time': f"{row['processing_time']:.2f}s",
                'processing_time_seconds': row['processing_time'],
                'error_message': row['error_message'] if pd.notna(row['error_message']) else ''
            }
            records.append(record)
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'data': records,
            'total': len(records)
        })
        
    except Exception as e:
        logger.error(f"Error getting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest/<int:count>')
def api_latest(count):
    """Get latest N records."""
    try:
        if not config.CSV_FILE.exists():
            return jsonify({'data': []})
        
        df = pd.read_csv(config.CSV_FILE)
        
        # Sort by timestamp and get latest
        df = df.sort_values('timestamp', ascending=False).head(count)
        
        records = []
        for _, row in df.iterrows():
            record = {
                'timestamp': row['timestamp'],
                'filename': row['filename'],
                'file_size': format_file_size(row['file_size']),
                'duration': format_duration(row['duration']),
                'status': row['status'],
                'processing_time': f"{row['processing_time']:.2f}s"
            }
            records.append(record)
        
        return jsonify({'data': records})
        
    except Exception as e:
        logger.error(f"Error getting latest data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Get processing statistics."""
    try:
        stats = processor.get_processing_stats()
        
        # Add formatted versions
        stats['avg_processing_time_formatted'] = f"{stats['avg_processing_time']:.2f}s"
        stats['total_duration_formatted'] = format_duration(stats['total_duration'])
        stats['success_rate_formatted'] = f"{stats['success_rate']:.1f}%"
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing/status')
def api_processing_status():
    """Get real-time processing status and queue information."""
    try:
        # Get current processing statistics
        stats = processor.get_processing_stats()
        
        # Get files waiting to be processed
        pending_files = []
        if config.AUDIO_FOLDER.exists():
            audio_files = [
                f for f in config.AUDIO_FOLDER.rglob("*") 
                if f.is_file() and config.is_supported_audio_file(f.name)
            ]
            
            for audio_file in audio_files:
                if not processor.is_file_already_processed(audio_file.name):
                    file_size = audio_file.stat().st_size / 1024 / 1024  # MB
                    pending_files.append({
                        'filename': audio_file.name,
                        'size_mb': round(file_size, 2),
                        'path': str(audio_file)
                    })
        
        processing_status = {
            'total_files_found': len(audio_files) if 'audio_files' in locals() else 0,
            'files_processed': stats['successful'],
            'files_failed': stats['failed'], 
            'files_pending': len(pending_files),
            'pending_files': pending_files[:10],  # Show first 10 pending files
            'processing_complete': len(pending_files) == 0,
            'success_rate': stats['success_rate'],
            'avg_processing_time': stats['avg_processing_time'],
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(processing_status)
        
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def api_search():
    """Search transcriptions."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'data': [], 'total': 0})
        
        if not config.CSV_FILE.exists():
            return jsonify({'data': [], 'total': 0})
        
        df = pd.read_csv(config.CSV_FILE)
        
        # Search in transcription, summary, intent, and filename columns
        mask = (
            df['transcription'].str.contains(query, case=False, na=False) |
            df['summary'].str.contains(query, case=False, na=False) |
            df['intent'].str.contains(query, case=False, na=False) |
            df['filename'].str.contains(query, case=False, na=False)
        )
        
        filtered_df = df[mask]
        
        records = []
        for _, row in filtered_df.iterrows():
            record = {
                'timestamp': row['timestamp'],
                'filename': row['filename'],
                'file_size': format_file_size(row['file_size']),
                'duration': format_duration(row['duration']),
                'transcription': row['transcription'] if pd.notna(row['transcription']) else 'No transcription available',
                'summary': row['summary'] if pd.notna(row['summary']) else '',
                'intent': row['intent'] if pd.notna(row['intent']) else 'OTHER',
                'sub_intent': row['sub_intent'] if pd.notna(row['sub_intent']) else 'GENERAL_INQUIRY',
                'primary_disposition': row['primary_disposition'] if pd.notna(row['primary_disposition']) else '',
                'secondary_disposition': row['secondary_disposition'] if pd.notna(row['secondary_disposition']) else '',
                'status': row['status'],
                'processing_time': f"{row['processing_time']:.2f}s",
                'error_message': row['error_message'] if pd.notna(row['error_message']) else ''
            }
            records.append(record)
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'data': records,
            'total': len(records),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<filename>', methods=['DELETE'])
def api_delete(filename):
    """Delete specific record."""
    try:
        success = processor.delete_record(filename)
        
        if success:
            return jsonify({'success': True, 'message': f'Record for {filename} deleted'})
        else:
            return jsonify({'success': False, 'message': f'Record for {filename} not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting record: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reprocess/<filename>', methods=['POST'])
def api_reprocess(filename):
    """Reprocess specific file."""
    try:
        success = processor.reprocess_file(filename)
        
        if success:
            return jsonify({'success': True, 'message': f'File {filename} reprocessed successfully'})
        else:
            return jsonify({'success': False, 'message': f'Failed to reprocess {filename}'}), 400
            
    except Exception as e:
        logger.error(f"Error reprocessing file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>')
def api_file_details(filename):
    """Get detailed information for a specific file."""
    try:
        if not config.CSV_FILE.exists():
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.read_csv(config.CSV_FILE)
        
        # Find the record
        record = df[df['filename'] == filename]
        
        if record.empty:
            return jsonify({'error': 'File not found'}), 404
        
        row = record.iloc[0]
        
        details = {
            'timestamp': row['timestamp'],
            'filename': row['filename'],
            'file_size': format_file_size(row['file_size']),
            'file_size_bytes': int(row['file_size']) if pd.notna(row['file_size']) else 0,
            'duration': format_duration(row['duration']),
            'duration_seconds': float(row['duration']) if pd.notna(row['duration']) else 0.0,
            'transcription': row['transcription'] if pd.notna(row['transcription']) else 'No transcription available',
            'summary': row['summary'] if pd.notna(row['summary']) else '',
            'intent': row['intent'] if pd.notna(row['intent']) else 'OTHER',
            'sub_intent': row['sub_intent'] if pd.notna(row['sub_intent']) else 'GENERAL_INQUIRY',
            'primary_disposition': row['primary_disposition'] if pd.notna(row['primary_disposition']) else '',
            'secondary_disposition': row['secondary_disposition'] if pd.notna(row['secondary_disposition']) else '',
            'status': row['status'],
            'processing_time': f"{float(row['processing_time']):.2f}s" if pd.notna(row['processing_time']) else "0.00s",
            'processing_time_seconds': float(row['processing_time']) if pd.notna(row['processing_time']) else 0.0,
            'error_message': row['error_message'] if pd.notna(row['error_message']) else '',
            'diarized_transcription': row['diarized_transcription'] if pd.notna(row['diarized_transcription']) else '',
            'speaker_count': int(row['speaker_count']) if pd.notna(row['speaker_count']) else 1
        }
        
        return jsonify(details)
        
    except Exception as e:
        logger.error(f"Error getting file details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def api_export():
    """Export data as CSV or JSON."""
    try:
        format_type = request.args.get('format', 'csv').lower()
        
        if not config.CSV_FILE.exists():
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.read_csv(config.CSV_FILE)
        
        if format_type == 'json':
            # Convert to JSON
            records = df.to_dict('records')
            return jsonify({'data': records, 'count': len(records)})
        else:
            # Return CSV content
            csv_content = df.to_csv(index=False)
            
            from flask import Response
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=transcriptions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
            )
        
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'components': {
                'csv_file': config.CSV_FILE.exists(),
                'audio_folder': config.AUDIO_FOLDER.exists(),
                'processed_folder': config.PROCESSED_FOLDER.exists(),
                'deepgram_api': bool(config.DEEPGRAM_API_KEY),
                'openai_api': bool(config.OPENAI_API_KEY)
            }
        }
        
        # Check if all components are healthy
        all_healthy = all(health_status['components'].values())
        health_status['status'] = 'healthy' if all_healthy else 'degraded'
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Handle single or multiple file uploads."""
    try:
        files = request.files.getlist('files')
        
        if not files or (len(files) == 1 and files[0].filename == ''):
            return jsonify({'error': 'No files provided'}), 400
        
        results = []
        total_uploaded = 0
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not config.is_supported_audio_file(file.filename):
                errors.append(f'{file.filename}: Unsupported file format')
                continue
            
            # Check if file is already processed (duplicate)
            if processor.is_file_already_processed(file.filename):
                errors.append(f'{file.filename}: File already processed (duplicate)')
                continue
            
            # Save file to audio folder
            file_path = config.AUDIO_FOLDER / file.filename
            
            # Handle filename conflicts (different from duplicates)
            counter = 1
            original_path = file_path
            original_filename = file.filename
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = config.AUDIO_FOLDER / f"{stem}_{counter}{suffix}"
                counter += 1
            
            try:
                file.save(str(file_path))
                results.append({
                    'original_filename': original_filename,
                    'saved_filename': file_path.name,
                    'success': True
                })
                total_uploaded += 1
            except Exception as e:
                errors.append(f'{file.filename}: Failed to save - {str(e)}')
        
        return jsonify({
            'success': total_uploaded > 0,
            'message': f'Successfully uploaded {total_uploaded} file(s)',
            'uploaded_count': total_uploaded,
            'results': results,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/s3/recordings')
def api_s3_recordings():
    """Get list of recordings from S3."""
    try:
        limit = int(request.args.get('limit', 50))
        since_hours = int(request.args.get('since_hours', 24))
        
        recordings = s3_manager.list_recordings(limit=limit, since_hours=since_hours)
        
        # Format the recordings for display
        formatted_recordings = []
        for recording in recordings:
            formatted_recordings.append({
                'key': recording['key'],
                'filename': recording['filename'],
                'size': format_file_size(recording['size']),
                'size_bytes': recording['size'],
                'last_modified': recording['last_modified'].isoformat(),
                'last_modified_formatted': recording['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'recordings': formatted_recordings,
            'count': len(formatted_recordings)
        })
        
    except Exception as e:
        logger.error(f"Error getting S3 recordings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/s3/download/<path:s3_key>', methods=['POST'])
def api_s3_download(s3_key):
    """Download a specific recording from S3."""
    try:
        local_path = s3_manager.download_recording(s3_key)
        
        if local_path:
            return jsonify({
                'success': True,
                'message': f'Downloaded {local_path.name} successfully',
                'filename': local_path.name,
                'local_path': str(local_path)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to download file'
            }), 400
            
    except Exception as e:
        logger.error(f"Error downloading from S3: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/s3/sync', methods=['POST'])
def api_s3_sync():
    """Sync new recordings from S3."""
    try:
        count = s3_manager.sync_new_recordings()
        
        return jsonify({
            'success': True,
            'message': f'Synced {count} new recordings from S3',
            'downloaded_count': count
        })
        
    except Exception as e:
        logger.error(f"Error syncing S3 recordings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/s3/stats')
def api_s3_stats():
    """Get S3 bucket statistics."""
    try:
        stats = s3_manager.get_bucket_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting S3 stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/overview')
def api_analytics_overview():
    """Get overview analytics."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        stats = analytics.get_overview_stats(start_date, end_date)
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intents')
def api_analytics_intents():
    """Get intent distribution."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        intent_data = analytics.get_intent_distribution(start_date, end_date)
        return jsonify(intent_data)
        
    except Exception as e:
        logger.error(f"Error getting intent analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/trends')
def api_analytics_trends():
    """Get daily trends."""
    try:
        days = int(request.args.get('days', 30))
        
        trends = analytics.get_daily_trends(days)
        return jsonify(trends)
        
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/hourly')
def api_analytics_hourly():
    """Get hourly distribution."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        hourly_data = analytics.get_hourly_distribution(start_date, end_date)
        return jsonify(hourly_data)
        
    except Exception as e:
        logger.error(f"Error getting hourly analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/performance')
def api_analytics_performance():
    """Get performance metrics."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        performance = analytics.get_performance_metrics(start_date, end_date)
        return jsonify(performance)
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/insights')
def api_analytics_insights():
    """Get top insights."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        insights = analytics.get_top_insights(start_date, end_date)
        return jsonify({'insights': insights})
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-trends')
def api_analytics_intent_trends():
    """Get intent trends over time."""
    try:
        days = int(request.args.get('days', 7))
        
        intent_trends = analytics.get_intent_trends(days)
        return jsonify(intent_trends)
        
    except Exception as e:
        logger.error(f"Error getting intent trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/sub-intents')
def api_analytics_sub_intents():
    """Get sub-intent distribution."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        sub_intent_data = analytics.get_sub_intent_distribution(start_date, end_date)
        return jsonify(sub_intent_data)
        
    except Exception as e:
        logger.error(f"Error getting sub-intent analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-matrix')
def api_analytics_intent_matrix():
    """Get intent vs sub-intent matrix."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        matrix_data = analytics.get_intent_sub_intent_matrix(start_date, end_date)
        return jsonify(matrix_data)
        
    except Exception as e:
        logger.error(f"Error getting intent matrix: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/duration-distribution')
def api_analytics_duration_distribution():
    """Get call duration distribution."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        duration_data = analytics.get_duration_distribution(start_date, end_date)
        return jsonify(duration_data)
        
    except Exception as e:
        logger.error(f"Error getting duration distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/speaker-distribution')
def api_analytics_speaker_distribution():
    """Get speaker count distribution."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        speaker_data = analytics.get_speaker_distribution(start_date, end_date)
        return jsonify(speaker_data)
        
    except Exception as e:
        logger.error(f"Error getting speaker distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/drop-off-analysis')
def api_analytics_drop_off_analysis():
    """Get call drop-off analysis."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        dropoff_data = analytics.get_drop_off_analysis(start_date, end_date)
        return jsonify(dropoff_data)
        
    except Exception as e:
        logger.error(f"Error getting drop-off analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-sub-intent-breakdown')
def api_intent_sub_intent_breakdown():
    """Get sub-intent distribution within main intents."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        breakdown = analytics.get_intent_sub_intent_breakdown(start_date, end_date)
        return jsonify(breakdown)
        
    except Exception as e:
        logger.error(f"Error getting intent sub-intent breakdown: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/disposition-distribution')
def api_disposition_distribution():
    """Get disposition distribution analytics."""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        distribution = analytics.get_disposition_distribution(start_date, end_date)
        return jsonify(distribution)
        
    except Exception as e:
        logger.error(f"Error getting disposition distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classify-dispositions', methods=['POST'])
def api_classify_dispositions():
    """Batch classify dispositions for calls."""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        processed_count = analytics.batch_classify_dispositions(start_date, end_date)
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'message': f'Successfully classified dispositions for {processed_count} calls'
        })
        
    except Exception as e:
        logger.error(f"Error classifying dispositions: {str(e)}")
        return jsonify({'error': str(e)}), 500

def format_file_size(size_bytes):
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds):
    """Format duration in human readable format."""
    if seconds == 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Ensure directories exist
    config.create_directories()
    
    logger.info(f"Starting Flask dashboard on port {config.FLASK_PORT}")
    
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.DEBUG_MODE,
        threaded=True
    )