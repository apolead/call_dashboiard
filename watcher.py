"""
File monitoring system for audio transcription automation.
Watches for new audio files and triggers processing.
"""

import logging
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import config
from processor import AudioProcessor
from s3_manager import s3_manager

logger = logging.getLogger(__name__)

class AudioFileHandler(FileSystemEventHandler):
    """Handler for audio file system events."""
    
    def __init__(self, processor):
        """Initialize with audio processor instance."""
        super().__init__()
        self.processor = processor
        self.processed_files = set()
        self._lock = threading.Lock()
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file is supported audio format
        if not config.is_supported_audio_file(file_path.name):
            logger.debug(f"Skipping non-audio file: {file_path.name}")
            return
        
        # Wait for file to be completely written
        self._wait_for_file_stable(file_path)
        
        # Check if already processed
        with self._lock:
            if str(file_path) in self.processed_files:
                logger.debug(f"File already processed: {file_path.name}")
                return
            self.processed_files.add(str(file_path))
        
        print(f"NEW: New audio file detected: {file_path.name}")
        logger.info(f"New audio file detected: {file_path.name}")
        
        # Process the file in a separate thread
        processing_thread = threading.Thread(
            target=self._process_file_safely,
            args=(file_path,),
            daemon=True
        )
        processing_thread.start()
    
    def _wait_for_file_stable(self, file_path, max_wait=30):
        """Wait for file to be completely written."""
        stable_time = 2  # seconds
        last_size = 0
        stable_count = 0
        wait_time = 0
        
        while wait_time < max_wait:
            try:
                current_size = file_path.stat().st_size
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    if stable_count >= stable_time:
                        break
                else:
                    stable_count = 0
                    last_size = current_size
                
                time.sleep(1)
                wait_time += 1
                
            except (OSError, FileNotFoundError):
                # File might be in use, wait a bit more
                time.sleep(1)
                wait_time += 1
                continue
        
        if wait_time >= max_wait:
            logger.warning(f"File may not be stable after {max_wait}s: {file_path.name}")
    
    def _process_file_safely(self, file_path):
        """Process file with error handling."""
        try:
            # Validate file size
            file_size = file_path.stat().st_size
            if file_size > config.get_file_size_limit_bytes():
                logger.error(f"File too large: {file_path.name} ({file_size / 1024 / 1024:.1f}MB)")
                return
            
            if file_size == 0:
                logger.error(f"Empty file: {file_path.name}")
                return
            
            # Process the audio file
            self.processor.process_audio_file(file_path)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {str(e)}")
        finally:
            # Remove from processed set if processing failed
            # This allows retry on next detection
            with self._lock:
                if str(file_path) in self.processed_files:
                    # Only remove if file still exists and wasn't moved
                    if file_path.exists():
                        self.processed_files.discard(str(file_path))

class AudioWatcher:
    """Main file watcher class."""
    
    def __init__(self):
        """Initialize the audio file watcher."""
        self.processor = AudioProcessor()
        self.observer = Observer()
        self.event_handler = AudioFileHandler(self.processor)
        self._running = False
        self._s3_sync_thread = None
        
        # Ensure directories exist
        config.create_directories()
        
        logger.info(f"Audio watcher initialized. Monitoring: {config.AUDIO_FOLDER}")
    
    def start(self):
        """Start the file watcher."""
        if self._running:
            logger.warning("Watcher is already running")
            return
        
        try:
            # Setup observer
            self.observer.schedule(
                self.event_handler,
                str(config.AUDIO_FOLDER),
                recursive=False
            )
            
            # Start observer
            self.observer.start()
            self._running = True
            
            logger.info("Audio file watcher started")
            
            # Process existing files
            self._process_existing_files()
            
            # Start S3 sync background thread (only if enabled)
            if config.ENABLE_S3_SYNC:
                self._start_s3_sync()
            else:
                print("STOP: S3 sync disabled - using local files only")
            
            # Keep the watcher running
            try:
                while self._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
                self.stop()
            
        except Exception as e:
            logger.error(f"Error starting watcher: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the file watcher."""
        if not self._running:
            return
        
        logger.info("Stopping audio file watcher...")
        self._running = False
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=5)
        
        logger.info("Audio file watcher stopped")
    
    def _process_existing_files(self):
        """Process any existing audio files in the folder."""
        try:
            audio_files = [
                f for f in config.AUDIO_FOLDER.rglob("*")
                if f.is_file() and config.is_supported_audio_file(f.name)
            ]
            
            if audio_files:
                print(f"FOLDER: Found {len(audio_files)} existing audio files")
                logger.info(f"Found {len(audio_files)} existing audio files to process")
                
                unprocessed_files = []
                for audio_file in audio_files:
                    # Check if already processed by looking in CSV
                    if not self.processor.is_file_already_processed(audio_file.name):
                        unprocessed_files.append(audio_file)
                
                if unprocessed_files:
                    print(f"REFRESH: Processing {len(unprocessed_files)} unprocessed files...")
                    
                    for i, audio_file in enumerate(unprocessed_files, 1):
                        print(f"   [{i}/{len(unprocessed_files)}] Queuing: {audio_file.name}")
                        logger.info(f"Processing existing file: {audio_file.name}")
                        
                        # Process in separate thread
                        processing_thread = threading.Thread(
                            target=self.event_handler._process_file_safely,
                            args=(audio_file,),
                            daemon=True
                        )
                        processing_thread.start()
                        
                        # Small delay to prevent overwhelming APIs
                        time.sleep(2)
                else:
                    print("SUCCESS: All existing files already processed")
            else:
                print("FOLDER: No existing audio files found in folder")
                logger.info("No existing audio files found")
                
        except Exception as e:
            print(f"ERROR: Error processing existing files: {str(e)}")
            logger.error(f"Error processing existing files: {str(e)}")
    
    def _start_s3_sync(self):
        """Start background S3 sync thread."""
        try:
            self._s3_sync_thread = threading.Thread(
                target=self._s3_sync_worker,
                daemon=True
            )
            self._s3_sync_thread.start()
            logger.info("S3 sync background thread started")
        except Exception as e:
            logger.error(f"Failed to start S3 sync thread: {str(e)}")
    
    def _s3_sync_worker(self):
        """Background worker for S3 sync."""
        sync_interval = 300  # 5 minutes
        
        print("WAVE: S3 sync worker started (checking every 5 minutes)")
        
        while self._running:
            try:
                # Sync new recordings from S3
                count = s3_manager.sync_new_recordings()
                if count > 0:
                    print(f"REFRESH: S3 sync complete: Downloaded {count} new recordings")
                    logger.info(f"S3 sync: Downloaded {count} new recordings")
                
            except Exception as e:
                print(f"ERROR: S3 sync error: {str(e)}")
                logger.error(f"S3 sync error: {str(e)}")
            
            # Wait for next sync
            for _ in range(sync_interval):
                if not self._running:
                    break
                time.sleep(1)
        
        print("WAVE: S3 sync worker stopped")
        logger.info("S3 sync worker stopped")
    
    def get_status(self):
        """Get current watcher status."""
        return {
            'running': self._running,
            'observer_alive': self.observer.is_alive() if self.observer else False,
            'monitored_folder': str(config.AUDIO_FOLDER),
            'processed_count': len(self.event_handler.processed_files)
        }

def main():
    """Main function to run the watcher."""
    logger.info("Starting Audio Transcription Watcher")
    
    try:
        watcher = AudioWatcher()
        watcher.start()
    except KeyboardInterrupt:
        logger.info("Watcher stopped by user")
    except Exception as e:
        logger.error(f"Watcher error: {str(e)}")
    finally:
        logger.info("Audio Transcription Watcher shutdown complete")

if __name__ == "__main__":
    main()