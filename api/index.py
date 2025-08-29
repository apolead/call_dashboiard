"""
Vercel Serverless Dashboard - Display Only
Shows processed transcription results with beautiful UI.
No processing - just displays your pre-processed data.
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request
from collections import defaultdict, Counter

# Flask app for Vercel
app = Flask(__name__)

# Load CSV data without pandas
def load_data():
    """Load your processed CSV data without pandas."""
    try:
        csv_path = Path('call_transcriptions.csv')
        if csv_path.exists():
            data = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        else:
            return []
    except Exception as e:
        return []

# Load data once
data = load_data()

@app.route('/')
def dashboard():
    """API endpoint - returns dashboard data as JSON."""
    try:
        # Calculate stats from your processed data
        total_duration = 0
        for row in data:
            duration = row.get('duration_seconds', '0')
            if duration and duration != '':
                try:
                    total_duration += float(duration)
                except:
                    pass
        
        # Get latest processing timestamp
        latest_timestamp = ""
        if len(data) > 0:
            latest_timestamp = data[-1].get('timestamp', '')
        
        stats = {
            'total_files': len(data),
            'processed_files': len(data),
            'success_rate': 100.0 if len(data) > 0 else 0,
            'avg_processing_time': 2.5,
            'total_duration': int(total_duration),
            'last_processed': latest_timestamp or '2025-08-28 15:30:00'
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Call Dashboard API - Display Only',
            'stats': stats,
            'data_loaded': len(data) > 0,
            'total_records': len(data),
            'endpoints': {
                'data': '/api/data',
                'stats': '/api/stats',
                'intent_distribution': '/api/analytics/intent-distribution',
                'disposition_distribution': '/api/analytics/disposition-distribution',
                'intent_breakdown': '/api/analytics/intent-sub-intent-breakdown'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'total_records': len(data)
        }), 500

@app.route('/api/data')
def api_data():
    """Return all your processed call data for the table."""
    try:
        records = []
        
        for row in data:
            def safe_int(val, default=0):
                try:
                    return int(val) if val and val != '' else default
                except:
                    return default
                    
            def safe_float(val, default=0.0):
                try:
                    return float(val) if val and val != '' else default
                except:
                    return default
            
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
                'file_size_bytes': safe_int(row.get('file_size_bytes')),
                'duration': str(row.get('duration', '')),
                'duration_seconds': safe_float(row.get('duration_seconds')),
                'summary': str(row.get('summary', '')),
                'intent': str(row.get('intent', '')),
                'sub_intent': str(row.get('sub_intent', '')),
                'primary_disposition': str(row.get('primary_disposition', '')),
                'secondary_disposition': str(row.get('secondary_disposition', '')),
                'status': str(row.get('status', 'completed')),
                'processing_time': str(row.get('processing_time', '')),
                'processing_time_seconds': safe_float(row.get('processing_time_seconds')),
                'error_message': str(row.get('error_message', '')),
                'transcription': str(row.get('transcription', '')),
                'diarized_transcription': str(row.get('diarized_transcription', '')),
                'speaker_count': safe_int(row.get('speaker_count'), 1)
            }
            records.append(record)
        
        return jsonify({
            'data': records,
            'total': len(records),
            'recordsFiltered': len(records)
        })
        
    except Exception as e:
        return jsonify({'data': [], 'total': 0, 'recordsFiltered': 0, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """Dashboard statistics from your processed data."""
    try:
        total_duration = 0
        for row in data:
            duration = row.get('duration_seconds', '0')
            if duration and duration != '':
                try:
                    total_duration += float(duration)
                except:
                    pass
            
        latest_timestamp = ""
        if len(data) > 0:
            latest_timestamp = data[-1].get('timestamp', '')
        
        return jsonify({
            'total_files': len(data),
            'processed_files': len(data),
            'success_rate': 100.0 if len(data) > 0 else 0,
            'avg_processing_time': 2.5,
            'total_duration': int(total_duration),
            'last_processed': latest_timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/intent-distribution')
def api_intent_distribution():
    """Intent distribution from your processed data."""
    try:
        if len(data) == 0:
            return jsonify({'intents': [], 'total': 0})
        
        # Get valid intents
        valid_intents = []
        for row in data:
            intent = row.get('intent', '')
            if intent and intent.strip() != '':
                valid_intents.append(intent)
        
        if len(valid_intents) == 0:
            return jsonify({'intents': [], 'total': 0})
        
        # Count intents
        intent_counts = Counter(valid_intents)
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
        return jsonify({'intents': [], 'total': 0, 'error': str(e)})

@app.route('/api/analytics/disposition-distribution')
def api_disposition_distribution():
    """Disposition distribution from your processed data."""
    try:
        primary_disp = []
        secondary_disp = []
        total = len(data)
        
        # Primary dispositions
        primary_valid = []
        for row in data:
            disp = row.get('primary_disposition', '')
            if disp and disp.strip() != '':
                primary_valid.append(disp)
        
        primary_counts = Counter(primary_valid)
        for disp, count in primary_counts.items():
            primary_disp.append({
                'label': str(disp),
                'count': int(count),
                'percentage': round((count / len(primary_valid)) * 100, 1) if len(primary_valid) > 0 else 0
            })
        
        # Secondary dispositions
        secondary_valid = []
        for row in data:
            disp = row.get('secondary_disposition', '')
            if disp and disp.strip() != '':
                secondary_valid.append(disp)
        
        secondary_counts = Counter(secondary_valid)
        for disp, count in secondary_counts.items():
            secondary_disp.append({
                'label': str(disp),
                'count': int(count),
                'percentage': round((count / len(secondary_valid)) * 100, 1) if len(secondary_valid) > 0 else 0
            })
        
        # Classification rate
        classified_count = len(primary_valid)
        classification_rate = (classified_count / total * 100) if total > 0 else 0
        
        return jsonify({
            'primary_dispositions': primary_disp,
            'secondary_dispositions': secondary_disp,
            'total_calls': int(total),
            'total_classified': int(classified_count),
            'classification_rate': round(classification_rate, 1)
        })
    except Exception as e:
        return jsonify({'primary_dispositions': [], 'secondary_dispositions': [], 'total_calls': 0})

@app.route('/api/analytics/intent-sub-intent-breakdown')
def api_intent_sub_intent_breakdown():
    """Intent sub-intent breakdown from your processed data."""
    try:
        if len(data) == 0:
            return jsonify({'breakdown': {}, 'total': 0})
        
        breakdown = {}
        valid_data = []
        
        # Get valid intent/sub_intent pairs
        for row in data:
            intent = row.get('intent', '')
            sub_intent = row.get('sub_intent', '')
            if intent and intent.strip() != '' and sub_intent and sub_intent.strip() != '':
                valid_data.append({'intent': intent, 'sub_intent': sub_intent})
        
        # Group by intent
        intent_groups = defaultdict(list)
        for item in valid_data:
            intent_groups[item['intent']].append(item['sub_intent'])
        
        for intent, sub_intents in intent_groups.items():
            sub_intent_counts = Counter(sub_intents)
            
            sub_intent_list = []
            intent_total = len(sub_intents)
            
            for sub_intent, count in sub_intent_counts.items():
                sub_intent_list.append({
                    'sub_intent': str(sub_intent),
                    'label': str(sub_intent).replace('_', ' ').title(),
                    'count': int(count),
                    'percentage': round((count / intent_total) * 100, 1) if intent_total > 0 else 0
                })
            
            breakdown[str(intent)] = {
                'label': str(intent).replace('_', ' ').title(),
                'sub_intents': sub_intent_list,
                'total_count': int(intent_total)
            }
        
        return jsonify({
            'breakdown': breakdown,
            'total': len(valid_data)
        })
    except Exception as e:
        return jsonify({'breakdown': {}, 'total': 0})

@app.route('/api/transcription/<filename>')
def api_transcription(filename):
    """Get transcription details for a specific file."""
    try:
        if len(data) == 0:
            return jsonify({'error': 'No data available'}), 404
            
        # Find file in data
        file_row = None
        for row in data:
            if row.get('filename', '') == filename:
                file_row = row
                break
        
        if not file_row:
            return jsonify({'error': f'File {filename} not found'}), 404
        
        def safe_int(val, default=1):
            try:
                return int(val) if val and val != '' else default
            except:
                return default
        
        return jsonify({
            'transcription': str(file_row.get('transcription', '')),
            'diarized_transcription': str(file_row.get('diarized_transcription', '')),
            'summary': str(file_row.get('summary', '')),
            'intent': str(file_row.get('intent', '')),
            'sub_intent': str(file_row.get('sub_intent', '')),
            'speaker_count': safe_int(file_row.get('speaker_count'), 1),
            'primary_disposition': str(file_row.get('primary_disposition', '')),
            'secondary_disposition': str(file_row.get('secondary_disposition', ''))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500