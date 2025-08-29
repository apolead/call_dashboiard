"""
Audio processing engine for transcription and AI analysis.
Handles Deepgram API integration, OpenAI processing, and data management.
"""

import logging
import time
import csv
import json
import shutil
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
import pandas as pd
import requests
from openai import OpenAI
from deepgram import DeepgramClient, PrerecordedOptions
from tqdm import tqdm
from config import config

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Main audio processing class."""
    
    def __init__(self):
        """Initialize the audio processor."""
        # Initialize APIs
        self.deepgram = DeepgramClient(config.DEEPGRAM_API_KEY)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Initialize CSV file
        self._initialize_csv()
        
        logger.info("Audio processor initialized")
    
    def _extract_filename_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from filename pattern: YYYYMMDD_HHMMSSXXmXXs_PHONE_STATUS_AGENT.mp3
        
        Args:
            filename: The audio filename
            
        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {
            'call_date': None,
            'call_time': None,
            'call_datetime': None,
            'phone_number': None,
            'call_status': None,
            'agent_name': None,
            'estimated_duration_seconds': 0
        }
        
        try:
            # Pattern: YYYYMMDD_HHMMSSXXmXXs_PHONE_STATUS_AGENT.mp3
            pattern = r'(\d{8})_(\d{6})(\d+)m(\d+)s_([^_]+)_([^_]+)_(.+)\.'
            match = re.match(pattern, filename)
            
            if match:
                date_str, time_str, duration_min, duration_sec, phone, status, agent = match.groups()
                
                # Parse date and time
                call_date = datetime.strptime(date_str, '%Y%m%d').date()
                call_time_obj = datetime.strptime(time_str, '%H%M%S').time()
                call_datetime = datetime.combine(call_date, call_time_obj)
                
                # Calculate estimated duration
                estimated_duration = int(duration_min) * 60 + int(duration_sec)
                
                metadata.update({
                    'call_date': call_date.isoformat(),
                    'call_time': call_time_obj.isoformat(),
                    'call_datetime': call_datetime.isoformat(),
                    'phone_number': phone,
                    'call_status': status,
                    'agent_name': agent,
                    'estimated_duration_seconds': estimated_duration
                })
                
                print(f"   DATE: Call Date: {call_date.strftime('%Y-%m-%d')}")
                print(f"   TIME: Call Time: {call_time_obj.strftime('%H:%M:%S')}")
                print(f"   PHONE: Phone: {phone}")
                print(f"   AGENT: Agent: {agent}")
                print(f"   STATUS: Status: {status}")
                print(f"   DURATION: Estimated Duration: {duration_min}m {duration_sec}s")
                
            else:
                print(f"   WARNING: Could not parse filename pattern: {filename}")
                
        except Exception as e:
            print(f"   ERROR: Error extracting metadata: {str(e)}")
            logger.error(f"Error extracting filename metadata: {str(e)}")
        
        return metadata
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not config.CSV_FILE.exists():
            config.CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config.CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(config.get_csv_headers())
            
            logger.info(f"Created CSV file: {config.CSV_FILE}")
    
    def process_audio_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Process an audio file through the complete pipeline.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing processing results
        """
        start_time = time.time()
        filename = file_path.name
        
        # Check if already processed to avoid duplicates
        if self.is_file_already_processed(filename):
            print(f"\nSKIP: {filename} (already processed)")
            logger.info(f"Skipping {filename} - already processed")
            return {'status': 'skipped', 'filename': filename, 'message': 'Already processed'}
        
        print(f"\n" + "="*80)
        print(f"MUSIC PROCESSING: {filename}")
        print(f"CALENDAR Started: {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        logger.info(f"Starting processing for: {filename}")
        
        # Create a progress bar for the overall process
        with tqdm(total=3, desc="Processing Steps", leave=False, bar_format='{l_bar}{bar:20}{r_bar}{bar:-20b}') as main_pbar:
            # Extract metadata from filename
            main_pbar.set_description("📋 Extracting metadata")
            filename_metadata = self._extract_filename_metadata(filename)
            main_pbar.update(0.3)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'call_date': filename_metadata.get('call_date'),
            'call_time': filename_metadata.get('call_time'),
            'call_datetime': filename_metadata.get('call_datetime'),
            'phone_number': filename_metadata.get('phone_number'),
            'call_status': filename_metadata.get('call_status'),
            'agent_name': filename_metadata.get('agent_name'),
            'estimated_duration_seconds': filename_metadata.get('estimated_duration_seconds', 0),
            'file_size': 0,
            'duration': 0,
            'transcription': '',
            'diarized_transcription': '',
            'speaker_count': 0,
            'summary': '',
            'intent': '',
            'status': 'processing',
            'processing_time': 0,
            'error_message': ''
        }
        
        try:
            # Get file metadata
            file_size = file_path.stat().st_size
            result['file_size'] = file_size
            size_mb = file_size / 1024 / 1024
            
            print(f"FOLDER File size: {size_mb:.2f} MB")
            logger.info(f"File size: {size_mb:.2f}MB")
            
            # Create processing pipeline with progress tracking
            with tqdm(total=100, desc="MIC Transcription", leave=True, 
                     bar_format='{desc:20} |{bar:30}| {percentage:3.0f}% {elapsed}') as pbar:
                
                # Step 1: Transcribe with Deepgram
                pbar.set_description("MIC Starting Deepgram...")
                pbar.update(10)
                
                transcription_data = self._transcribe_with_deepgram(file_path)
                pbar.update(70)
                
                if not transcription_data:
                    raise Exception("Failed to get transcription from Deepgram")
                
                result['transcription'] = transcription_data['transcript']
                result['diarized_transcription'] = transcription_data.get('diarized_transcript', '')
                result['speaker_count'] = transcription_data.get('speaker_count', 1)
                result['duration'] = transcription_data.get('duration', 0)
                
                duration_mins = result['duration'] / 60
                transcript_length = len(result['transcription'])
                
                pbar.set_description("MIC Transcription complete")
                pbar.update(20)
                
                print(f"   SUCCESS Audio: {duration_mins:.1f}m | Text: {transcript_length:,} chars")
                logger.info(f"Transcription completed. Duration: {result['duration']:.2f}s")
            
            # Step 2: AI Analysis with progress
            with tqdm(total=100, desc="ROBOT AI Analysis", leave=True,
                     bar_format='{desc:20} |{bar:30}| {percentage:3.0f}% {elapsed}') as pbar:
                
                if result['transcription'].strip():
                    pbar.set_description("ROBOT Sending to OpenAI...")
                    pbar.update(20)
                    
                    analysis_result = self._analyze_with_openai(result['transcription'])
                    pbar.update(60)
                    
                    if analysis_result:
                        result['summary'] = analysis_result.get('summary', 'Analysis failed')
                        result['intent'] = analysis_result.get('intent', 'OTHER')
                        result['sub_intent'] = analysis_result.get('sub_intent', 'GENERAL_INQUIRY')
                        pbar.set_description("ROBOT Analysis complete")
                        pbar.update(20)
                        print(f"   SUCCESS Intent: {result['intent']}")
                        logger.info("AI analysis completed")
                    else:
                        result['summary'] = "AI analysis failed"
                        result['intent'] = "OTHER"
                        result['sub_intent'] = "GENERAL_INQUIRY"
                        pbar.set_description("ROBOT Analysis failed")
                        pbar.update(20)
                        print("   WARNING AI analysis failed")
                        logger.warning("AI analysis failed")
                else:
                    result['summary'] = "No transcription available for analysis"
                    result['intent'] = "OTHER"
                    result['sub_intent'] = "GENERAL_INQUIRY"
                    pbar.set_description("ROBOT Empty transcription")
                    pbar.update(100)
                    print("   WARNING Empty transcription, skipping AI analysis")
                    logger.warning("Empty transcription, skipping AI analysis")
            
            # Step 3: Save results with progress
            with tqdm(total=100, desc="DISK Saving", leave=True,
                     bar_format='{desc:20} |{bar:30}| {percentage:3.0f}% {elapsed}') as pbar:
                
                pbar.set_description("DISK Moving file...")
                result['status'] = 'completed'
                result['processing_time'] = time.time() - start_time
                pbar.update(30)
                
                # Move file to processed folder
                self._move_to_processed(file_path)
                pbar.update(40)
                
                # Save to CSV
                pbar.set_description("DISK Saving to CSV...")
                pbar.update(30)
                
                processing_mins = result['processing_time'] / 60
                pbar.set_description("DISK Save complete")
                print(f"   PARTY COMPLETED in {processing_mins:.1f}m | {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 80)
            logger.info(f"Processing completed for {filename} in {result['processing_time']:.2f}s")
            
        except Exception as e:
            error_msg = str(e)
            result['status'] = 'failed'
            result['error_message'] = error_msg
            result['processing_time'] = time.time() - start_time
            
            print(f"   ❌ Processing failed: {error_msg}")
            logger.error(f"Processing failed for {filename}: {error_msg}")
        
        finally:
            # Save to CSV
            self._save_to_csv(result)
        
        return result
    
    def _transcribe_with_deepgram(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Deepgram API.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription data
        """
        for attempt in range(config.MAX_RETRIES):
            try:
                logger.info(f"Transcribing with Deepgram (attempt {attempt + 1})")
                
                # Prepare transcription options using new v3 API
                options = PrerecordedOptions(
                    punctuate=True,
                    language='en-US',
                    model='nova',
                    smart_format=True,
                    diarize=True,  # Speaker diarization
                    utterances=True,
                    paragraphs=True
                )
                
                # Read audio file
                with open(file_path, 'rb') as audio_file:
                    audio_data = audio_file.read()
                
                # Transcribe using new v3 API
                response = self.deepgram.listen.prerecorded.v('1').transcribe_file(
                    {'buffer': audio_data}, 
                    options
                )
                
                # Extract results using new v3 response format
                if response and hasattr(response, 'results'):
                    channels = response.results.channels
                    if channels and len(channels) > 0:
                        alternatives = channels[0].alternatives
                        if alternatives and len(alternatives) > 0:
                            transcript = alternatives[0].transcript
                            
                            # Get metadata
                            duration = 0
                            
                            # Try to get duration from metadata
                            if hasattr(response, 'metadata') and response.metadata:
                                duration = response.metadata.duration
                            
                            # Extract diarized transcription and speaker count
                            diarized_transcript = self._extract_diarized_transcript(response)
                            speaker_count = self._count_speakers(response)
                            
                            return {
                                'transcript': transcript.strip(),
                                'diarized_transcript': diarized_transcript,
                                'speaker_count': speaker_count,
                                'duration': duration,
                                'confidence': alternatives[0].confidence if hasattr(alternatives[0], 'confidence') else 0
                            }
                
                raise Exception("No transcription results in response")
                
            except Exception as e:
                logger.warning(f"Deepgram attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY * (attempt + 1))
                else:
                    raise Exception(f"Deepgram transcription failed after {config.MAX_RETRIES} attempts: {str(e)}")
        
        return None
    
    def _extract_diarized_transcript(self, response) -> str:
        """Extract speaker-diarized transcript from Deepgram response."""
        try:
            result_data = response.results
            channels = result_data.channels
            
            if not channels or len(channels) == 0:
                return ""
            
            # Get utterances if available (these contain speaker info)
            channel = channels[0]
            if hasattr(channel, 'alternatives') and channel.alternatives:
                alternative = channel.alternatives[0]
                
                # Try to get utterances first (best for diarization)
                if hasattr(alternative, 'utterances') and alternative.utterances:
                    diarized_lines = []
                    for utterance in alternative.utterances:
                        speaker_id = getattr(utterance, 'speaker', 0)
                        text = getattr(utterance, 'transcript', '')
                        if text.strip():
                            diarized_lines.append(f"Speaker {speaker_id + 1}: {text.strip()}")
                    return '\n'.join(diarized_lines)
                
                # Fallback to words with speaker info
                elif hasattr(alternative, 'words') and alternative.words:
                    current_speaker = None
                    current_text = []
                    diarized_lines = []
                    
                    for word_data in alternative.words:
                        speaker_id = getattr(word_data, 'speaker', 0)
                        word_text = getattr(word_data, 'word', '')
                        
                        if current_speaker != speaker_id:
                            if current_text:
                                diarized_lines.append(f"Speaker {current_speaker + 1}: {' '.join(current_text)}")
                            current_speaker = speaker_id
                            current_text = [word_text]
                        else:
                            current_text.append(word_text)
                    
                    # Add the last speaker's text
                    if current_text:
                        diarized_lines.append(f"Speaker {current_speaker + 1}: {' '.join(current_text)}")
                    
                    return '\n'.join(diarized_lines)
            
            return ""
            
        except Exception as e:
            logger.warning(f"Failed to extract diarized transcript: {str(e)}")
            return ""
    
    def _count_speakers(self, response) -> int:
        """Count unique speakers from Deepgram response."""
        try:
            speakers = set()
            result_data = response.results
            channels = result_data.channels
            
            if not channels or len(channels) == 0:
                return 1
            
            channel = channels[0]
            if hasattr(channel, 'alternatives') and channel.alternatives:
                alternative = channel.alternatives[0]
                
                # Try utterances first
                if hasattr(alternative, 'utterances') and alternative.utterances:
                    for utterance in alternative.utterances:
                        speaker_id = getattr(utterance, 'speaker', 0)
                        speakers.add(speaker_id)
                
                # Fallback to words
                elif hasattr(alternative, 'words') and alternative.words:
                    for word_data in alternative.words:
                        speaker_id = getattr(word_data, 'speaker', 0)
                        speakers.add(speaker_id)
            
            return max(len(speakers), 1)  # At least 1 speaker
            
        except Exception as e:
            logger.warning(f"Failed to count speakers: {str(e)}")
            return 1
    
    def _get_mimetype(self, file_path: Path) -> str:
        """Get MIME type for audio file."""
        extension = file_path.suffix.lower()
        mime_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.ogg': 'audio/ogg'
        }
        return mime_types.get(extension, 'audio/mpeg')
    
    def _analyze_with_openai(self, transcription: str) -> Optional[Dict[str, str]]:
        """
        Analyze transcription using OpenAI API for home improvement calls.
        
        Args:
            transcription: The transcribed text
            
        Returns:
            Dictionary with summary and intent, or None if failed
        """
        for attempt in range(config.MAX_RETRIES):
            try:
                logger.info(f"Analyzing with OpenAI (attempt {attempt + 1})")
                
                # Prepare prompt
                prompt = config.DEFAULT_OPENAI_PROMPT.format(transcription=transcription)
                
                # Truncate if too long (approximate token limit for gpt-4o-mini)
                max_chars = 15000  # More generous for newer model
                if len(prompt) > max_chars:
                    truncated_transcription = transcription[:max_chars - len(config.DEFAULT_OPENAI_PROMPT) + 50]
                    prompt = config.DEFAULT_OPENAI_PROMPT.format(transcription=truncated_transcription + "... [truncated]")
                    logger.info("Truncated long transcription for OpenAI")
                
                # Make API call with updated client
                response = self.openai_client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing home improvement customer service calls. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,  # Reduced since we only need summary and intent
                    temperature=0.1,  # Lower temperature for consistent classification
                    timeout=config.API_TIMEOUT
                )
                
                # Extract and parse response
                if response and response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content.strip()
                    
                    try:
                        # Try to extract JSON from the response (in case there's extra text)
                        json_str = content
                        
                        # Look for JSON content between brackets
                        start = content.find('{')
                        end = content.rfind('}')
                        
                        if start != -1 and end != -1 and end > start:
                            json_str = content[start:end + 1]
                        else:
                            logger.warning(f"No JSON brackets found in response, using full content")
                        
                        # Parse JSON response
                        result = json.loads(json_str)
                        
                        # Validate required fields
                        if 'summary' in result and 'intent' in result:
                            # Validate intent is one of our allowed categories
                            valid_intents = [
                                'ROOFING', 'WINDOWS_DOORS', 'PLUMBING', 'ELECTRICAL', 
                                'HVAC', 'FLOORING', 'SIDING_EXTERIOR', 'KITCHEN_BATH',
                                'GENERAL_CONTRACTOR', 'EMERGENCY_REPAIR', 'QUOTE_REQUEST', 
                                'COMPLAINT', 'OTHER'
                            ]
                            
                            if result['intent'] not in valid_intents:
                                result['intent'] = 'OTHER'
                            
                            # Ensure summary is a string and not too long
                            result['summary'] = str(result['summary'])[:500]
                            
                            # Handle sub_intent - use keyword classification if not provided by AI
                            if 'sub_intent' not in result or not result['sub_intent'] or result['sub_intent'] in ['GENERAL_INQUIRY', 'GENERAL']:
                                result['sub_intent'] = self._classify_sub_intent_keywords(result['intent'], result['summary'])
                            else:
                                result['sub_intent'] = str(result['sub_intent']).upper()
                            
                            logger.info(f"OpenAI analysis successful - Intent: {result['intent']}, Sub-intent: {result['sub_intent']}")
                            return result
                        else:
                            logger.warning("Missing required fields in OpenAI response")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON response: {str(e)}")
                        
                        # Fallback: try to extract from non-JSON response
                        return self._extract_from_text_response(content)
                else:
                    logger.error("No response content from OpenAI")
                
                raise Exception("No valid response from OpenAI")
                
            except Exception as e:
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"All OpenAI attempts failed: {str(e)}")
                    return None
        
        return None
    
    def _extract_from_text_response(self, content: str) -> Dict[str, str]:
        """Extract summary, intent, and sub_intent from non-JSON response as fallback."""
        try:
            # Simple text parsing fallback
            lines = content.strip().split('\n')
            summary = "Call analysis completed"
            intent = "OTHER"
            sub_intent = "GENERAL_INQUIRY"
            
            # Try multiple parsing approaches
            for line in lines:
                line = line.strip()
                line_lower = line.lower()
                
                # Look for summary
                if 'summary' in line_lower and ':' in line:
                    summary = line.split(':', 1)[1].strip().strip('"\'').strip()
                    if len(summary) > 500:
                        summary = summary[:500] + "..."
                
                # Look for intent
                elif 'intent' in line_lower and ':' in line and 'sub' not in line_lower:
                    intent_text = line.split(':', 1)[1].strip().strip('"\'').upper()
                    valid_intents = [
                        'ROOFING', 'WINDOWS_DOORS', 'PLUMBING', 'ELECTRICAL', 
                        'HVAC', 'FLOORING', 'SIDING_EXTERIOR', 'KITCHEN_BATH',
                        'GENERAL_CONTRACTOR', 'EMERGENCY_REPAIR', 'QUOTE_REQUEST', 
                        'COMPLAINT', 'OTHER'
                    ]
                    if intent_text in valid_intents:
                        intent = intent_text
                
                # Look for sub_intent
                elif 'sub_intent' in line_lower and ':' in line:
                    sub_intent = line.split(':', 1)[1].strip().strip('"\'').upper()
            
            # If we didn't find structured data, create a basic summary
            if summary == "Call analysis completed" and content:
                # Use first sentence or first 200 characters as summary
                sentences = content.split('. ')
                if sentences:
                    summary = sentences[0].strip()
                    if not summary.endswith('.'):
                        summary += '.'
                    summary = summary[:200]
            
            # Ensure we have valid data
            if not summary or summary.strip() == "":
                summary = "Call transcribed successfully"
            
            # Use keyword classification for sub-intent if it's generic
            if sub_intent in ['GENERAL_INQUIRY', 'GENERAL']:
                sub_intent = self._classify_sub_intent_keywords(intent, summary)
            
            return {'summary': summary[:500], 'intent': intent, 'sub_intent': sub_intent}
            
        except Exception as e:
            logger.error(f"Failed to extract from text response: {str(e)}")
            return {'summary': 'Analysis parsing failed', 'intent': 'OTHER', 'sub_intent': 'GENERAL_INQUIRY'}
    
    def _classify_sub_intent_keywords(self, intent: str, summary: str) -> str:
        """Classify sub-intent based on keywords in the summary."""
        
        # Sub-intent patterns based on keywords
        patterns = {
            'ROOFING': {
                'ROOF_PURCHASE': ['purchase', 'buy', 'material', 'gauge', 'buying', 'advertised', 'facebook'],
                'ROOF_REPAIR': ['repair', 'leak', 'fix', 'damage', 'broken', 'leaking'],
                'ROOF_REPLACEMENT': ['replacement', 'replace', 'new roof', 'install'],
                'ROOF_INSPECTION': ['inspection', 'inspect', 'check', 'assessment'],
                'GUTTER_CLEANING': ['gutter clean', 'cleaning gutters', 'gutter maintenance'],
                'GUTTER_REPAIR': ['gutter repair', 'gutter fix', 'gutter damage']
            },
            'WINDOWS_DOORS': {
                'WINDOW_REPAIR': ['window repair', 'broken window', 'window fix', 'upstairs window'],
                'WINDOW_REPLACEMENT': ['window replacement', 'new window', 'replace window', 'glass block windows'],
                'DOOR_REPAIR': ['door repair', 'broken door', 'door fix'],
                'DOOR_INSTALLATION': ['door install', 'new door', 'door replacement'],
                'SCREEN_REPAIR': ['screen repair', 'screen replacement', 'screen fix']
            },
            'PLUMBING': {
                'LEAK_REPAIR': ['leak', 'leaking', 'water damage', 'pipe leak'],
                'PIPE_REPAIR': ['pipe repair', 'broken pipe', 'pipe fix'],
                'DRAIN_CLEANING': ['drain clean', 'clogged drain', 'drain maintenance'],
                'TOILET_REPAIR': ['toilet repair', 'toilet fix', 'toilet problem'],
                'FAUCET_REPAIR': ['faucet repair', 'faucet fix', 'tap repair'],
                'WATER_HEATER': ['water heater', 'hot water', 'heater repair']
            },
            'ELECTRICAL': {
                'WIRING_REPAIR': ['wiring', 'electrical problem', 'wire repair'],
                'OUTLET_INSTALLATION': ['outlet', 'electrical outlet', 'socket install'],
                'LIGHTING_REPAIR': ['lighting', 'light repair', 'light fix'],
                'ELECTRICAL_INSPECTION': ['electrical inspect', 'electrical check'],
                'PANEL_UPGRADE': ['electrical panel', 'panel upgrade', 'breaker box']
            },
            'HVAC': {
                'AC_REPAIR': ['ac repair', 'air conditioning', 'ac fix', 'cooling'],
                'HEATING_REPAIR': ['heating repair', 'heater', 'heat pump', 'furnace'],
                'DUCT_CLEANING': ['duct clean', 'air duct', 'ductwork'],
                'SYSTEM_INSTALLATION': ['hvac install', 'system install', 'new hvac'],
                'MAINTENANCE_SERVICE': ['hvac maintenance', 'service call', 'tune up']
            },
            'KITCHEN_BATH': {
                'BATHROOM_REMODEL': ['bathroom remodel', 'bath renovation', 'bathroom renovation'],
                'KITCHEN_REMODEL': ['kitchen remodel', 'kitchen renovation', 'kitchen upgrade'],
                'SHOWER_INSTALLATION': ['shower install', 'new shower', 'shower replacement'],
                'COUNTERTOP_REPAIR': ['countertop', 'counter repair', 'counter replacement'],
                'TILE_WORK': ['tile work', 'tile repair', 'tile installation']
            },
            'QUOTE_REQUEST': {
                'ESTIMATE_REQUEST': ['estimate', 'quote', 'pricing', 'cost', 'looking for a quote'],
                'CONSULTATION': ['consultation', 'consult', 'discuss', 'advice', 'listing', 'website'],
                'PRICE_INQUIRY': ['price', 'how much', 'cost inquiry'],
                'SERVICE_COMPARISON': ['compare', 'comparison', 'options']
            },
            'EMERGENCY_REPAIR': {
                'EMERGENCY_REPAIR': ['emergency', 'urgent', 'asap', 'immediately']
            },
            'COMPLAINT': {
                'COMPLAINT': ['complaint', 'issue', 'problem', 'unhappy', 'dissatisfied']
            },
            'GENERAL_CONTRACTOR': {
                'GENERAL_INQUIRY': ['general', 'contractor', 'multiple', 'various']
            },
            'OTHER': {
                'TEST_CALL': ['test call', 'testing', 'test', 'prepare for incoming leads', 'be ready'],
                'WRONG_NUMBER': ['wrong number', 'mistake', 'misdialed', 'not relevant', 'at&t', 'internet service', 'business internet'],
                'APPOINTMENT_SCHEDULING': ['appointment', 'schedule', 'booking'],
                'COMPLAINT': ['complaint', 'issue', 'problem', 'unhappy'],
                'GENERAL_INQUIRY': ['greeting', 'audio clarity', 'confirming', 'brief', 'no specific inquiry', 'information']
            }
        }
        
        if not intent or intent not in patterns:
            return 'GENERAL_INQUIRY'
        
        summary_lower = summary.lower()
        intent_patterns = patterns[intent]
        
        # Score each sub-intent based on keyword matches
        scores = {}
        for sub_intent, keywords in intent_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in summary_lower:
                    score += len(keyword)  # Longer keywords get higher scores
            scores[sub_intent] = score
        
        # Return the sub-intent with the highest score
        if scores and max(scores.values()) > 0:
            best_sub_intent = max(scores, key=scores.get)
            return best_sub_intent
        
        # Default based on intent
        defaults = {
            'ROOFING': 'ROOF_REPAIR',
            'WINDOWS_DOORS': 'WINDOW_REPAIR', 
            'PLUMBING': 'LEAK_REPAIR',
            'ELECTRICAL': 'WIRING_REPAIR',
            'HVAC': 'AC_REPAIR',
            'KITCHEN_BATH': 'BATHROOM_REMODEL',
            'QUOTE_REQUEST': 'ESTIMATE_REQUEST',
            'EMERGENCY_REPAIR': 'EMERGENCY_REPAIR',
            'COMPLAINT': 'COMPLAINT',
            'GENERAL_CONTRACTOR': 'GENERAL_INQUIRY',
            'OTHER': 'GENERAL_INQUIRY'
        }
        
        return defaults.get(intent, 'GENERAL_INQUIRY')
    
    def _move_to_processed(self, file_path: Path):
        """Move processed file to the processed folder."""
        try:
            processed_path = config.PROCESSED_FOLDER / file_path.name
            
            # Handle duplicate names
            counter = 1
            original_processed_path = processed_path
            while processed_path.exists():
                stem = original_processed_path.stem
                suffix = original_processed_path.suffix
                processed_path = config.PROCESSED_FOLDER / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(file_path), str(processed_path))
            logger.info(f"Moved {file_path.name} to {processed_path}")
            
        except Exception as e:
            logger.error(f"Failed to move file {file_path.name}: {str(e)}")
    
    def _save_to_csv(self, result: Dict[str, Any]):
        """Save processing result to CSV file."""
        try:
            # Prepare row data matching CSV headers exactly
            row = [
                result['timestamp'],
                result['filename'],
                result['call_date'],
                result['call_time'], 
                result['call_datetime'],
                result['phone_number'],
                result['call_status'],
                result['agent_name'],
                result['estimated_duration_seconds'],
                result['file_size'],
                result['duration'],
                result['transcription'],
                result['diarized_transcription'],
                result['speaker_count'],
                result['summary'],
                result['intent'],
                result['sub_intent'],
                result['status'],
                result['processing_time'],
                result['error_message']
            ]
            
            # Append to CSV
            with open(config.CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row)
            
            logger.info(f"Saved results to CSV for {result['filename']}")
            
        except Exception as e:
            logger.error(f"Failed to save to CSV: {str(e)}")
    
    def is_file_already_processed(self, filename: str) -> bool:
        """Check if a file has already been processed."""
        try:
            if not config.CSV_FILE.exists():
                return False
            
            df = pd.read_csv(config.CSV_FILE)
            return filename in df['filename'].values
            
        except Exception as e:
            logger.warning(f"Error checking processed files: {str(e)}")
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        try:
            if not config.CSV_FILE.exists():
                return {
                    'total_files': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0,
                    'avg_processing_time': 0,
                    'total_duration': 0
                }
            
            df = pd.read_csv(config.CSV_FILE)
            
            total_files = len(df)
            successful = len(df[df['status'] == 'completed'])
            failed = len(df[df['status'] == 'failed'])
            success_rate = (successful / total_files * 100) if total_files > 0 else 0
            
            # Calculate averages for successful processes only
            successful_df = df[df['status'] == 'completed']
            avg_processing_time = successful_df['processing_time'].mean() if len(successful_df) > 0 else 0
            total_duration = successful_df['duration'].sum() if len(successful_df) > 0 else 0
            
            return {
                'total_files': total_files,
                'successful': successful,
                'failed': failed,
                'success_rate': round(success_rate, 2),
                'avg_processing_time': round(avg_processing_time, 2),
                'total_duration': round(total_duration, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0,
                'avg_processing_time': 0,
                'total_duration': 0
            }
    
    def reprocess_file(self, filename: str) -> bool:
        """Reprocess a file that's in the processed folder."""
        try:
            processed_file = config.PROCESSED_FOLDER / filename
            
            if not processed_file.exists():
                logger.error(f"File not found in processed folder: {filename}")
                return False
            
            # Move back to audio folder temporarily
            temp_file = config.AUDIO_FOLDER / filename
            shutil.copy2(str(processed_file), str(temp_file))
            
            # Process the file
            result = self.process_audio_file(temp_file)
            
            return result['status'] == 'completed'
            
        except Exception as e:
            logger.error(f"Error reprocessing file {filename}: {str(e)}")
            return False
    
    def delete_record(self, filename: str) -> bool:
        """Delete a record from the CSV file."""
        try:
            if not config.CSV_FILE.exists():
                return False
            
            df = pd.read_csv(config.CSV_FILE)
            original_length = len(df)
            
            # Remove rows with matching filename
            df = df[df['filename'] != filename]
            
            if len(df) < original_length:
                # Save updated CSV
                df.to_csv(config.CSV_FILE, index=False)
                logger.info(f"Deleted record for {filename}")
                return True
            else:
                logger.warning(f"No record found for {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting record for {filename}: {str(e)}")
            return False