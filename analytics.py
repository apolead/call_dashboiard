"""
Analytics engine for ApoLead call transcription system.
Provides comprehensive metrics, aggregations, and insights.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import os
import openai
from config import config

logger = logging.getLogger(__name__)

class CallAnalytics:
    """Advanced analytics for call transcription data."""
    
    def __init__(self):
        """Initialize analytics engine."""
        self.csv_file = config.CSV_FILE
    
    def get_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """Load and filter data based on date range."""
        try:
            if not self.csv_file.exists():
                return pd.DataFrame()
            
            df = pd.read_csv(self.csv_file)
            
            if df.empty:
                return df
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            
            # Filter by date range
            if start_date:
                start_dt = pd.to_datetime(start_date)
                df = df[df['timestamp'] >= start_dt]
            
            if end_date:
                end_dt = pd.to_datetime(end_date) + timedelta(days=1)
                df = df[df['timestamp'] < end_dt]
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading analytics data: {str(e)}")
            return pd.DataFrame()
    
    def get_overview_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive overview statistics."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return self._empty_stats()
        
        completed_calls = df[df['status'] == 'completed']
        
        # Basic stats
        stats = {
            'total_calls': len(df),
            'completed_calls': len(completed_calls),
            'failed_calls': len(df[df['status'] == 'failed']),
            'processing_calls': len(df[df['status'] == 'processing']),
            'success_rate': round(len(completed_calls) / len(df) * 100, 1) if len(df) > 0 else 0,
            
            # Duration metrics
            'total_duration_hours': round(completed_calls['duration'].sum() / 3600, 2),
            'avg_duration_minutes': round(completed_calls['duration'].mean() / 60, 1) if len(completed_calls) > 0 else 0,
            'max_duration_minutes': round(completed_calls['duration'].max() / 60, 1) if len(completed_calls) > 0 else 0,
            
            # Processing metrics
            'avg_processing_time': round(completed_calls['processing_time'].mean(), 2) if len(completed_calls) > 0 else 0,
            'total_processing_time': round(df['processing_time'].sum(), 2),
            
            # File size metrics
            'total_size_mb': round(df['file_size'].sum() / 1024 / 1024, 2),
            'avg_size_mb': round(df['file_size'].mean() / 1024 / 1024, 2) if len(df) > 0 else 0,
            
            # Recent activity
            'calls_today': len(df[df['date'] == datetime.now().date()]),
            'calls_yesterday': len(df[df['date'] == (datetime.now().date() - timedelta(days=1))]),
            'calls_this_week': len(df[df['timestamp'] >= (datetime.now() - timedelta(days=7))]),
        }
        
        # Enhanced metrics with filename metadata
        if not completed_calls.empty:
            # Agent performance
            if 'agent_name' in completed_calls.columns:
                agent_counts = completed_calls['agent_name'].value_counts()
                if len(agent_counts) > 0:
                    stats['top_agent'] = agent_counts.index[0] if len(agent_counts.index) > 0 else 'Unknown'
                    stats['total_agents'] = len(agent_counts)
            
            # Call status distribution
            if 'call_status' in completed_calls.columns:
                status_counts = completed_calls['call_status'].value_counts()
                stats['call_statuses'] = status_counts.to_dict()
                if len(status_counts) > 0:
                    stats['most_common_status'] = status_counts.index[0] if len(status_counts.index) > 0 else 'Unknown'
            
            # Phone number insights
            if 'phone_number' in completed_calls.columns:
                unique_numbers = completed_calls['phone_number'].nunique()
                stats['unique_phone_numbers'] = unique_numbers
                stats['avg_calls_per_number'] = round(len(completed_calls) / unique_numbers, 1) if unique_numbers > 0 else 0
        
        return stats
    
    def get_intent_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get intent distribution with counts and percentages."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return {'intents': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'intents': [], 'total': 0}
        
        intent_counts = completed_calls['intent'].value_counts()
        total = len(completed_calls)
        
        intents = []
        for intent, count in intent_counts.items():
            intents.append({
                'intent': intent,
                'count': int(count),
                'percentage': round(count / total * 100, 1),
                'label': intent.replace('_', ' ').title()
            })
        
        return {
            'intents': intents,
            'total': total,
            'unique_intents': len(intent_counts)
        }
    
    def get_sub_intent_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get sub-intent distribution with counts and percentages."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'sub_intent' not in df.columns:
            return {'sub_intents': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'sub_intents': [], 'total': 0}
        
        # Filter out null/empty sub_intents
        completed_calls = completed_calls[completed_calls['sub_intent'].notna()]
        completed_calls = completed_calls[completed_calls['sub_intent'] != '']
        
        if completed_calls.empty:
            return {'sub_intents': [], 'total': 0}
        
        sub_intent_counts = completed_calls['sub_intent'].value_counts()
        total = len(completed_calls)
        
        sub_intents = []
        for sub_intent, count in sub_intent_counts.items():
            sub_intents.append({
                'sub_intent': sub_intent,
                'count': int(count),
                'percentage': round(count / total * 100, 1),
                'label': sub_intent.replace('_', ' ').title()
            })
        
        return {
            'sub_intents': sub_intents,
            'total': total,
            'unique_sub_intents': len(sub_intent_counts)
        }
    
    def get_intent_sub_intent_breakdown(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get sub-intent distributions within each main intent category."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'sub_intent' not in df.columns or 'intent' not in df.columns:
            return {'intent_breakdowns': {}, 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'intent_breakdowns': {}, 'total': 0}
        
        # Filter out null/empty values
        valid_calls = completed_calls[
            (completed_calls['intent'].notna()) & 
            (completed_calls['sub_intent'].notna()) &
            (completed_calls['intent'] != '') &
            (completed_calls['sub_intent'] != '')
        ]
        
        if valid_calls.empty:
            return {'intent_breakdowns': {}, 'total': 0}
        
        intent_breakdowns = {}
        
        # Get top 5 most common intents
        top_intents = valid_calls['intent'].value_counts().head(5).index.tolist()
        
        for intent in top_intents:
            intent_data = valid_calls[valid_calls['intent'] == intent]
            sub_intent_counts = intent_data['sub_intent'].value_counts()
            intent_total = len(intent_data)
            
            sub_intents = []
            for sub_intent, count in sub_intent_counts.items():
                sub_intents.append({
                    'sub_intent': sub_intent,
                    'count': int(count),
                    'percentage': round(count / intent_total * 100, 1),
                    'label': sub_intent.replace('_', ' ').title()
                })
            
            intent_breakdowns[intent] = {
                'sub_intents': sub_intents,
                'total_count': intent_total,
                'label': intent.replace('_', ' ').title()
            }
        
        return {
            'breakdown': intent_breakdowns,
            'total': len(valid_calls)
        }
    
    def get_intent_sub_intent_matrix(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get intent vs sub-intent correlation matrix."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'sub_intent' not in df.columns:
            return {'matrix': {}, 'intents': [], 'sub_intents': []}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'matrix': {}, 'intents': [], 'sub_intents': []}
        
        # Filter out null/empty values
        matrix_data = completed_calls[
            (completed_calls['intent'].notna()) & 
            (completed_calls['sub_intent'].notna()) &
            (completed_calls['intent'] != '') &
            (completed_calls['sub_intent'] != '')
        ]
        
        if matrix_data.empty:
            return {'matrix': {}, 'intents': [], 'sub_intents': []}
        
        # Create cross-tabulation
        crosstab = pd.crosstab(matrix_data['intent'], matrix_data['sub_intent'])
        
        # Convert to nested dictionary for easier frontend handling
        matrix = {}
        for intent in crosstab.index:
            matrix[intent] = {}
            for sub_intent in crosstab.columns:
                count = crosstab.loc[intent, sub_intent]
                if count > 0:  # Only include non-zero values
                    matrix[intent][sub_intent] = int(count)
        
        return {
            'matrix': matrix,
            'intents': [intent.replace('_', ' ').title() for intent in crosstab.index.tolist()],
            'sub_intents': [sub_intent.replace('_', ' ').title() for sub_intent in crosstab.columns.tolist()],
            'total_combinations': len([v for intent_data in matrix.values() for v in intent_data.values() if v > 0])
        }
    
    def get_duration_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get call duration distribution in meaningful ranges."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return {'duration_ranges': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'duration_ranges': [], 'total': 0}
        
        # Define duration ranges in seconds
        ranges = [
            (0, 30, "Under 30 seconds"),
            (30, 60, "30s - 1 minute"),
            (60, 120, "1 - 2 minutes"),
            (120, 240, "2 - 4 minutes"),
            (240, 360, "4 - 6 minutes"),
            (360, float('inf'), "Over 6 minutes")
        ]
        
        duration_data = []
        total_calls = len(completed_calls)
        
        for min_dur, max_dur, label in ranges:
            if max_dur == float('inf'):
                count = len(completed_calls[completed_calls['duration'] >= min_dur])
            else:
                count = len(completed_calls[
                    (completed_calls['duration'] >= min_dur) & 
                    (completed_calls['duration'] < max_dur)
                ])
            
            percentage = round(count / total_calls * 100, 1) if total_calls > 0 else 0
            
            duration_data.append({
                'range': label,
                'count': int(count),
                'percentage': percentage,
                'min_seconds': min_dur,
                'max_seconds': max_dur if max_dur != float('inf') else None
            })
        
        return {
            'duration_ranges': duration_data,
            'total': total_calls,
            'avg_duration_minutes': round(completed_calls['duration'].mean() / 60, 1) if total_calls > 0 else 0
        }
    
    def get_speaker_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get speaker count distribution."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'speaker_count' not in df.columns:
            return {'speaker_counts': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'speaker_counts': [], 'total': 0}
        
        # Clean speaker count data
        completed_calls = completed_calls[completed_calls['speaker_count'].notna()]
        
        if completed_calls.empty:
            return {'speaker_counts': [], 'total': 0}
        
        speaker_counts = completed_calls['speaker_count'].value_counts().sort_index()
        total = len(completed_calls)
        
        speaker_data = []
        for count, calls in speaker_counts.items():
            percentage = round(calls / total * 100, 1) if total > 0 else 0
            
            if count == 1:
                label = "1 Speaker (Agent Only)"
                description = "Calls where only the agent spoke - likely drop-offs"
            elif count == 2:
                label = "2 Speakers (Normal)"
                description = "Standard agent-customer conversations"
            else:
                label = f"{count} Speakers"
                description = "Multi-party conversations"
            
            speaker_data.append({
                'speaker_count': int(count),
                'label': label,
                'description': description,
                'calls': int(calls),
                'percentage': percentage
            })
        
        return {
            'speaker_counts': speaker_data,
            'total': total,
            'drop_off_rate': round(speaker_counts.get(1, 0) / total * 100, 1) if total > 0 else 0
        }
    
    def get_drop_off_analysis(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Analyze call drop-offs and short calls."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return {'drop_offs': 0, 'total_calls': 0, 'analysis': []}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'drop_offs': 0, 'total_calls': 0, 'analysis': []}
        
        total_calls = len(completed_calls)
        
        # Analyze different types of drop-offs
        analysis = []
        
        # 1. Single speaker calls (agent only)
        if 'speaker_count' in completed_calls.columns:
            single_speaker = len(completed_calls[completed_calls['speaker_count'] == 1])
            single_speaker_pct = round(single_speaker / total_calls * 100, 1) if total_calls > 0 else 0
            
            analysis.append({
                'type': 'Single Speaker',
                'count': single_speaker,
                'percentage': single_speaker_pct,
                'description': 'Calls with only agent speaking (likely immediate hang-ups)'
            })
        
        # 2. Very short calls (under 30 seconds)
        very_short = len(completed_calls[completed_calls['duration'] < 30])
        very_short_pct = round(very_short / total_calls * 100, 1) if total_calls > 0 else 0
        
        analysis.append({
            'type': 'Very Short Calls',
            'count': very_short,
            'percentage': very_short_pct,
            'description': 'Calls under 30 seconds (quick hang-ups)'
        })
        
        # 3. Short calls (30-60 seconds)
        short_calls = len(completed_calls[
            (completed_calls['duration'] >= 30) & 
            (completed_calls['duration'] < 60)
        ])
        short_calls_pct = round(short_calls / total_calls * 100, 1) if total_calls > 0 else 0
        
        analysis.append({
            'type': 'Short Calls',
            'count': short_calls,
            'percentage': short_calls_pct,
            'description': 'Calls 30-60 seconds (early disconnects)'
        })
        
        # 4. Call status analysis
        hang_ups = len(df[df['call_status'].str.contains('HangUp', na=False)])
        hang_up_pct = round(hang_ups / len(df) * 100, 1) if len(df) > 0 else 0
        
        analysis.append({
            'type': 'Hang Ups',
            'count': hang_ups,
            'percentage': hang_up_pct,
            'description': 'Calls marked as hang-ups in filename'
        })
        
        # Calculate overall drop-off rate (combining single speaker + very short)
        total_drop_offs = single_speaker + very_short - len(completed_calls[
            (completed_calls['speaker_count'] == 1) & 
            (completed_calls['duration'] < 30)
        ]) if 'speaker_count' in completed_calls.columns else very_short
        
        drop_off_rate = round(total_drop_offs / total_calls * 100, 1) if total_calls > 0 else 0
        
        return {
            'drop_offs': total_drop_offs,
            'total_calls': total_calls,
            'drop_off_rate': drop_off_rate,
            'analysis': analysis
        }
    
    def get_daily_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get daily call trends for the specified number of days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = self.get_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            return {'dates': [], 'calls': [], 'completed': [], 'failed': []}
        
        # Create daily aggregations
        daily_stats = df.groupby('date').agg({
            'filename': 'count',
            'status': lambda x: (x == 'completed').sum(),
            'processing_time': 'mean',
            'duration': 'sum'
        }).rename(columns={
            'filename': 'total_calls',
            'status': 'completed_calls'
        })
        
        daily_stats['failed_calls'] = df.groupby('date')['status'].apply(lambda x: (x == 'failed').sum())
        daily_stats['avg_processing_time'] = daily_stats['processing_time'].round(2)
        daily_stats['total_duration_hours'] = (daily_stats['duration'] / 3600).round(2)
        
        # Fill missing dates with zeros
        date_range = pd.date_range(start=start_date.date(), end=end_date.date())
        daily_stats = daily_stats.reindex(date_range, fill_value=0)
        
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in daily_stats.index],
            'total_calls': daily_stats['total_calls'].tolist(),
            'completed_calls': daily_stats['completed_calls'].tolist(),
            'failed_calls': daily_stats['failed_calls'].tolist(),
            'avg_processing_time': daily_stats['avg_processing_time'].tolist(),
            'total_duration_hours': daily_stats['total_duration_hours'].tolist()
        }
    
    def get_hourly_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get hourly call distribution."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return {'hours': [], 'calls': []}
        
        hourly_counts = df.groupby('hour').size()
        
        # Ensure all hours 0-23 are represented
        all_hours = pd.Series(0, index=range(24))
        hourly_counts = all_hours.add(hourly_counts, fill_value=0)
        
        return {
            'hours': [f"{h:02d}:00" for h in range(24)],
            'calls': hourly_counts.tolist()
        }
    
    def get_performance_metrics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return self._empty_performance_metrics()
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return self._empty_performance_metrics()
        
        # Processing time percentiles
        processing_times = completed_calls['processing_time']
        duration_times = completed_calls['duration']
        
        return {
            'processing_time': {
                'mean': round(processing_times.mean(), 2),
                'median': round(processing_times.median(), 2),
                'p95': round(processing_times.quantile(0.95), 2),
                'p99': round(processing_times.quantile(0.99), 2),
                'min': round(processing_times.min(), 2),
                'max': round(processing_times.max(), 2)
            },
            'call_duration': {
                'mean_minutes': round(duration_times.mean() / 60, 2),
                'median_minutes': round(duration_times.median() / 60, 2),
                'total_hours': round(duration_times.sum() / 3600, 2),
                'shortest_seconds': round(duration_times.min(), 2),
                'longest_minutes': round(duration_times.max() / 60, 2)
            },
            'throughput': {
                'calls_per_hour': round(len(completed_calls) / ((completed_calls['timestamp'].max() - completed_calls['timestamp'].min()).total_seconds() / 3600), 2) if len(completed_calls) > 1 else 0,
                'processing_efficiency': round(completed_calls['duration'].sum() / completed_calls['processing_time'].sum(), 2) if completed_calls['processing_time'].sum() > 0 else 0
            }
        }
    
    def get_intent_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get intent trends over time."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        df = self.get_data(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            return {'dates': [], 'intent_data': {}}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'dates': [], 'intent_data': {}}
        
        # Get daily intent counts
        daily_intents = completed_calls.groupby(['date', 'intent']).size().unstack(fill_value=0)
        
        # Fill missing dates
        date_range = pd.date_range(start=start_date.date(), end=end_date.date())
        daily_intents = daily_intents.reindex(date_range, fill_value=0)
        
        # Prepare data for charts
        dates = [d.strftime('%Y-%m-%d') for d in daily_intents.index]
        intent_data = {}
        
        for intent in daily_intents.columns:
            intent_data[intent] = {
                'label': intent.replace('_', ' ').title(),
                'data': daily_intents[intent].tolist(),
                'total': daily_intents[intent].sum()
            }
        
        return {
            'dates': dates,
            'intent_data': intent_data
        }
    
    def get_top_insights(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get top insights and recommendations."""
        df = self.get_data(start_date, end_date)
        
        if df.empty:
            return []
        
        insights = []
        completed_calls = df[df['status'] == 'completed']
        
        # Peak hour analysis
        if not df.empty:
            peak_hour = df.groupby('hour').size().idxmax()
            peak_count = df.groupby('hour').size().max()
            insights.append({
                'type': 'peak_time',
                'title': 'Peak Call Hour',
                'description': f"Most calls ({peak_count}) occur at {peak_hour:02d}:00",
                'value': f"{peak_hour:02d}:00",
                'icon': 'clock'
            })
        
        # Top intent
        if not completed_calls.empty and 'intent' in completed_calls.columns:
            top_intent = completed_calls['intent'].mode().iloc[0]
            intent_count = completed_calls['intent'].value_counts().iloc[0]
            intent_pct = round(intent_count / len(completed_calls) * 100, 1)
            insights.append({
                'type': 'top_intent',
                'title': 'Most Common Intent',
                'description': f"{top_intent.replace('_', ' ').title()} ({intent_pct}% of calls)",
                'value': f"{intent_count} calls",
                'icon': 'bullseye'
            })
        
        # Processing efficiency
        if not completed_calls.empty:
            avg_processing = completed_calls['processing_time'].mean()
            if avg_processing < 30:
                insights.append({
                    'type': 'efficiency',
                    'title': 'High Processing Efficiency',
                    'description': f"Average processing time: {avg_processing:.1f}s",
                    'value': 'Excellent',
                    'icon': 'lightning'
                })
        
        # Success rate
        if not df.empty:
            success_rate = len(completed_calls) / len(df) * 100
            if success_rate > 95:
                insights.append({
                    'type': 'reliability',
                    'title': 'High Success Rate',
                    'description': f"{success_rate:.1f}% of calls processed successfully",
                    'value': f"{success_rate:.1f}%",
                    'icon': 'check-circle'
                })
        
        return insights
    
    def get_agent_performance(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get agent performance metrics."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'agent_name' not in df.columns:
            return {'agents': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'agents': [], 'total': 0}
        
        # Group by agent
        agent_stats = []
        for agent in completed_calls['agent_name'].unique():
            if pd.isna(agent):
                continue
                
            agent_calls = completed_calls[completed_calls['agent_name'] == agent]
            
            agent_data = {
                'agent': agent,
                'total_calls': len(agent_calls),
                'avg_duration_minutes': round(agent_calls['duration'].mean() / 60, 1),
                'total_duration_hours': round(agent_calls['duration'].sum() / 3600, 2),
                'success_rate': 100.0,  # All these are completed calls
                'most_common_status': agent_calls['call_status'].mode().iloc[0] if 'call_status' in agent_calls.columns and not agent_calls['call_status'].empty else 'Unknown'
            }
            
            agent_stats.append(agent_data)
        
        # Sort by total calls
        agent_stats.sort(key=lambda x: x['total_calls'], reverse=True)
        
        return {
            'agents': agent_stats,
            'total': len(agent_stats)
        }
    
    def get_call_status_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get call status distribution."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'call_status' not in df.columns:
            return {'statuses': [], 'total': 0}
        
        completed_calls = df[df['status'] == 'completed']
        
        if completed_calls.empty:
            return {'statuses': [], 'total': 0}
        
        status_counts = completed_calls['call_status'].value_counts()
        total = len(completed_calls)
        
        statuses = []
        for status, count in status_counts.items():
            if pd.isna(status):
                continue
                
            statuses.append({
                'status': status,
                'count': int(count),
                'percentage': round(count / total * 100, 1),
                'label': status.replace('_', ' ').title()
            })
        
        return {
            'statuses': statuses,
            'total': total,
            'unique_statuses': len(status_counts)
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure."""
        return {
            'total_calls': 0,
            'completed_calls': 0,
            'failed_calls': 0,
            'processing_calls': 0,
            'success_rate': 0,
            'total_duration_hours': 0,
            'avg_duration_minutes': 0,
            'max_duration_minutes': 0,
            'avg_processing_time': 0,
            'total_processing_time': 0,
            'total_size_mb': 0,
            'avg_size_mb': 0,
            'calls_today': 0,
            'calls_yesterday': 0,
            'calls_this_week': 0
        }
    
    def _empty_performance_metrics(self) -> Dict[str, Any]:
        """Return empty performance metrics."""
        return {
            'processing_time': {
                'mean': 0, 'median': 0, 'p95': 0, 'p99': 0, 'min': 0, 'max': 0
            },
            'call_duration': {
                'mean_minutes': 0, 'median_minutes': 0, 'total_hours': 0,
                'shortest_seconds': 0, 'longest_minutes': 0
            },
            'throughput': {
                'calls_per_hour': 0, 'processing_efficiency': 0
            }
        }
    
    def classify_disposition(self, transcription: str, summary: str = "") -> Dict[str, str]:
        """
        Classify call disposition using OpenAI API based on transcription content.
        Returns primary and secondary disposition categories.
        """
        try:
            # Check if OpenAI API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OpenAI API key not found. Skipping disposition classification.")
                return {'primary_disposition': 'UNKNOWN', 'secondary_disposition': 'NO_API_KEY'}
            
            # Initialize OpenAI client
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Prepare context for classification
            context = f"Transcription: {transcription}\n\nSummary: {summary}".strip()
            
            # Define disposition categories based on user requirements
            disposition_prompt = f"""
            Based on the call transcription, classify this call with a PRIMARY and SECONDARY disposition.

            PRIMARY DISPOSITIONS:
            - APPOINTMENT_SET: Lead scheduled an appointment
            - QUALIFIED_LEAD: Lead is interested and qualified but no appointment yet
            - NOT_QUALIFIED: Lead doesn't meet qualification criteria
            - NOT_INTERESTED: Lead explicitly not interested
            - CALLBACK_REQUESTED: Lead asked to be called back later
            - WRONG_NUMBER: Incorrect phone number or person
            - NO_ANSWER: Call went unanswered
            - HANG_UP: Lead hung up during call
            - VOICEMAIL: Left voicemail message
            - TECHNICAL_ISSUE: Call had technical problems
            - OTHER: Doesn't fit other categories

            SECONDARY DISPOSITIONS:
            - IMMEDIATE: Ready to proceed now
            - FUTURE: Interested but timing not right
            - PRICE_OBJECTION: Concerned about pricing
            - TRUST_OBJECTION: Skeptical about company/service
            - DECISION_MAKER: Not the decision maker
            - RESEARCH_NEEDED: Wants to research more
            - COMPETITOR: Already working with competitor
            - SEASONAL: Waiting for right season/timing
            - BUDGET_CONSTRAINTS: Financial limitations
            - PROPERTY_ISSUE: Property-specific concerns
            - REFERRAL_NEEDED: Asking for referrals
            - FOLLOW_UP_REQUIRED: Needs additional follow-up
            - OTHER: Doesn't fit other categories

            Respond with only: PRIMARY_DISPOSITION|SECONDARY_DISPOSITION

            Call Content:
            {context}
            """
            
            # Make API call to OpenAI using new client format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a call disposition classifier for home improvement leads."},
                    {"role": "user", "content": disposition_prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            # Parse response
            result = response.choices[0].message.content.strip()
            if '|' in result:
                primary, secondary = result.split('|', 1)
                return {
                    'primary_disposition': primary.strip(),
                    'secondary_disposition': secondary.strip()
                }
            else:
                logger.warning(f"Unexpected OpenAI response format: {result}")
                return {'primary_disposition': 'OTHER', 'secondary_disposition': 'CLASSIFICATION_ERROR'}
                
        except Exception as e:
            logger.error(f"Error classifying disposition: {str(e)}")
            return {'primary_disposition': 'ERROR', 'secondary_disposition': 'API_ERROR'}
    
    def batch_classify_dispositions(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> int:
        """
        Classify dispositions for calls that don't have them yet.
        Returns the number of calls processed.
        """
        try:
            # Load data
            if not config.CSV_FILE.exists():
                logger.error("CSV file not found for disposition classification")
                return 0
            
            df = pd.read_csv(config.CSV_FILE)
            
            # Filter by date range if provided
            if start_date and end_date:
                df = df[
                    (df['timestamp'] >= start_date) & 
                    (df['timestamp'] <= end_date)
                ]
            
            # Find calls without disposition classifications
            needs_classification = df[
                (df['primary_disposition'].isna()) | 
                (df['primary_disposition'] == '') |
                (df['secondary_disposition'].isna()) | 
                (df['secondary_disposition'] == '')
            ]
            
            if needs_classification.empty:
                logger.info("No calls need disposition classification")
                return 0
            
            logger.info(f"Classifying dispositions for {len(needs_classification)} calls...")
            processed_count = 0
            
            # Process each call
            for index, row in needs_classification.iterrows():
                transcription = row.get('transcription', '')
                summary = row.get('summary', '')
                
                if not transcription or transcription == 'No transcription available':
                    continue
                
                # Classify disposition
                disposition = self.classify_disposition(transcription, summary)
                
                # Update the dataframe
                df.loc[index, 'primary_disposition'] = disposition['primary_disposition']
                df.loc[index, 'secondary_disposition'] = disposition['secondary_disposition']
                
                processed_count += 1
                
                # Save progress every 10 classifications
                if processed_count % 10 == 0:
                    df.to_csv(config.CSV_FILE, index=False)
                    logger.info(f"Processed {processed_count}/{len(needs_classification)} disposition classifications")
            
            # Final save
            df.to_csv(config.CSV_FILE, index=False)
            logger.info(f"Completed disposition classification for {processed_count} calls")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in batch disposition classification: {str(e)}")
            return 0
    
    def get_disposition_distribution(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get disposition distribution analytics."""
        df = self.get_data(start_date, end_date)
        
        if df.empty or 'primary_disposition' not in df.columns:
            return {
                'primary_dispositions': [],
                'secondary_dispositions': [],
                'total_classified': 0,
                'classification_rate': 0
            }
        
        # Filter out unclassified calls
        classified_calls = df[
            (df['primary_disposition'].notna()) & 
            (df['primary_disposition'] != '') &
            (df['primary_disposition'] != 'UNKNOWN')
        ]
        
        total_calls = len(df)
        classified_count = len(classified_calls)
        classification_rate = round(classified_count / total_calls * 100, 1) if total_calls > 0 else 0
        
        # Primary disposition distribution
        primary_counts = classified_calls['primary_disposition'].value_counts()
        primary_dispositions = [
            {
                'label': disposition,
                'count': count,
                'percentage': round(count / classified_count * 100, 1) if classified_count > 0 else 0
            }
            for disposition, count in primary_counts.items()
        ]
        
        # Secondary disposition distribution
        secondary_classified = classified_calls[
            (classified_calls['secondary_disposition'].notna()) & 
            (classified_calls['secondary_disposition'] != '')
        ]
        
        secondary_counts = secondary_classified['secondary_disposition'].value_counts()
        secondary_dispositions = [
            {
                'label': disposition,
                'count': count,
                'percentage': round(count / len(secondary_classified) * 100, 1) if len(secondary_classified) > 0 else 0
            }
            for disposition, count in secondary_counts.items()
        ]
        
        return {
            'primary_dispositions': primary_dispositions,
            'secondary_dispositions': secondary_dispositions,
            'total_classified': classified_count,
            'total_calls': total_calls,
            'classification_rate': classification_rate
        }

# Global analytics instance
analytics = CallAnalytics()