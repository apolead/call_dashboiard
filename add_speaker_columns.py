"""
Add speaker-related columns to existing CSV data.
"""

import pandas as pd
import json
import re
from config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def estimate_speaker_count(transcription: str) -> int:
    """Estimate speaker count based on transcription patterns."""
    if not transcription or pd.isna(transcription):
        return 1
    
    # Look for conversation patterns that indicate multiple speakers
    patterns = [
        r'\?.*\.',  # Question followed by answer
        r'Hello.*Hi',  # Greetings from different people
        r'Yes.*No',  # Agreement/disagreement patterns
        r'Thank you.*You\'re welcome',  # Polite exchanges
    ]
    
    conversation_indicators = 0
    for pattern in patterns:
        if re.search(pattern, transcription, re.IGNORECASE):
            conversation_indicators += 1
    
    # Simple heuristic: look for back-and-forth conversation
    sentences = re.split(r'[.!?]+', transcription)
    if len(sentences) > 10:  # Longer calls likely have 2 speakers
        return 2
    elif len(sentences) > 5 and conversation_indicators > 0:
        return 2
    else:
        return 1

def create_simple_diarization(transcription: str, speaker_count: int) -> str:
    """Create a simple speaker-separated version."""
    if not transcription or pd.isna(transcription) or speaker_count <= 1:
        return f"Speaker 1: {transcription}" if transcription else ""
    
    # Split into sentences and alternate speakers
    sentences = re.split(r'([.!?]+)', transcription)
    result = []
    current_speaker = 1
    
    for i, sentence in enumerate(sentences):
        if sentence.strip() and not re.match(r'^[.!?]+$', sentence):
            result.append(f"Speaker {current_speaker}: {sentence.strip()}")
            # Switch speakers occasionally for realistic diarization
            if len(sentence.strip()) > 20:  # Switch after longer statements
                current_speaker = 2 if current_speaker == 1 else 1
    
    return '\n'.join(result)

def main():
    """Add speaker columns to existing data."""
    logger.info(f"Loading data from {config.CSV_FILE}")
    df = pd.read_csv(config.CSV_FILE)
    
    logger.info(f"Found {len(df)} records to update")
    
    # Add new columns if they don't exist
    if 'diarized_transcription' not in df.columns:
        df['diarized_transcription'] = ''
    
    if 'speaker_count' not in df.columns:
        df['speaker_count'] = 1
    
    updated_count = 0
    
    for index, row in df.iterrows():
        transcription = row.get('transcription', '')
        
        # Estimate speaker count
        speaker_count = estimate_speaker_count(transcription)
        df.at[index, 'speaker_count'] = speaker_count
        
        # Create simple diarization
        if pd.isna(row.get('diarized_transcription')) or row.get('diarized_transcription') == '':
            diarized = create_simple_diarization(transcription, speaker_count)
            df.at[index, 'diarized_transcription'] = diarized
        
        updated_count += 1
        
        if updated_count % 20 == 0:
            logger.info(f"Updated {updated_count} records...")
    
    # Save the updated data
    logger.info(f"Saving updated data with speaker information")
    df.to_csv(config.CSV_FILE, index=False)
    
    # Print summary
    speaker_counts = df['speaker_count'].value_counts().sort_index()
    logger.info("Speaker count distribution:")
    for count, num_calls in speaker_counts.items():
        logger.info(f"  {count} speaker(s): {num_calls} calls")
    
    logger.info("Speaker column addition complete!")

if __name__ == "__main__":
    main()