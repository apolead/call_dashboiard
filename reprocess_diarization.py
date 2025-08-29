#!/usr/bin/env python3
"""
Reprocess existing audio files to add diarized transcriptions.
This script will go through all existing audio files and reprocess them
with Deepgram's diarization feature to get speaker-separated transcripts.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from processor import AudioProcessor
from config import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reprocess_all_files():
    """Reprocess all audio files to add diarized transcriptions."""
    
    # Initialize the processor
    processor = AudioProcessor()
    
    # Check if CSV file exists
    if not config.CSV_FILE.exists():
        logger.error(f"CSV file not found: {config.CSV_FILE}")
        return
    
    # Load existing data
    logger.info("Loading existing CSV data...")
    df = pd.read_csv(config.CSV_FILE)
    logger.info(f"Found {len(df)} records in CSV")
    
    # Check which files need reprocessing (missing diarized_transcription)
    needs_reprocessing = df[df['diarized_transcription'].isna() | (df['diarized_transcription'] == '')]
    logger.info(f"Found {len(needs_reprocessing)} files that need diarized transcription")
    
    if len(needs_reprocessing) == 0:
        logger.info("All files already have diarized transcriptions!")
        return
    
    # Process each file
    processed_count = 0
    failed_count = 0
    
    for index, row in needs_reprocessing.iterrows():
        filename = row['filename']
        file_path = config.AUDIO_FOLDER / filename
        
        logger.info(f"Processing {filename} ({processed_count + failed_count + 1}/{len(needs_reprocessing)})")
        
        # Check if file exists
        if not file_path.exists():
            logger.warning(f"Audio file not found: {file_path}")
            failed_count += 1
            continue
        
        try:
            # Process the file with diarization directly
            logger.info(f"  - Transcribing with diarization...")
            transcription_data = processor._transcribe_with_deepgram(file_path)
            
            if transcription_data and 'diarized_transcript' in transcription_data and 'speaker_count' in transcription_data:
                # Update the CSV row
                df.loc[index, 'diarized_transcription'] = transcription_data['diarized_transcript']
                df.loc[index, 'speaker_count'] = transcription_data['speaker_count']
                
                logger.info(f"  ✅ Success! Found {transcription_data['speaker_count']} speakers")
                processed_count += 1
                
                # Save progress after each successful processing
                df.to_csv(config.CSV_FILE, index=False)
                logger.info(f"  - Progress saved to CSV")
                
            else:
                logger.error(f"  ❌ Failed to get diarized transcription")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"  ❌ Error processing {filename}: {str(e)}")
            failed_count += 1
            continue
    
    # Final save and summary
    df.to_csv(config.CSV_FILE, index=False)
    logger.info(f"\n=== REPROCESSING COMPLETE ===")
    logger.info(f"Successfully processed: {processed_count} files")
    logger.info(f"Failed: {failed_count} files")
    logger.info(f"Updated CSV saved to: {config.CSV_FILE}")

def check_audio_files():
    """Check which audio files exist in the upload folder."""
    
    if not config.CSV_FILE.exists():
        logger.error(f"CSV file not found: {config.CSV_FILE}")
        return
    
    df = pd.read_csv(config.CSV_FILE)
    logger.info(f"Checking audio files for {len(df)} records...")
    
    existing_files = []
    missing_files = []
    
    for _, row in df.iterrows():
        filename = row['filename']
        file_path = config.AUDIO_FOLDER / filename
        
        if file_path.exists():
            existing_files.append(filename)
        else:
            missing_files.append(filename)
    
    logger.info(f"Found {len(existing_files)} audio files")
    logger.info(f"Missing {len(missing_files)} audio files")
    
    if missing_files:
        logger.warning("Missing audio files:")
        for file in missing_files[:10]:  # Show first 10
            logger.warning(f"  - {file}")
        if len(missing_files) > 10:
            logger.warning(f"  ... and {len(missing_files) - 10} more")
    
    return existing_files, missing_files

if __name__ == "__main__":
    logger.info("=== AUDIO DIARIZATION REPROCESSING ===")
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--check-files":
        check_audio_files()
    else:
        # First check what files we have
        existing_files, missing_files = check_audio_files()
        
        if len(existing_files) == 0:
            logger.error("No audio files found to process!")
            sys.exit(1)
        
        # Ask for confirmation
        response = input(f"\nReady to reprocess {len(existing_files)} audio files with diarization. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            sys.exit(0)
        
        # Start reprocessing
        reprocess_all_files()