"""
AWS S3 integration for downloading audio recordings.
Handles fetching recordings from the specified S3 bucket.
"""

import logging
import boto3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import os
from botocore.exceptions import ClientError, NoCredentialsError
from config import config

logger = logging.getLogger(__name__)

class S3AudioManager:
    """Manages S3 audio file operations."""
    
    def __init__(self):
        """Initialize S3 client with credentials."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            
            # Test connection
            self._test_connection()
            logger.info("S3 client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            self.s3_client = None
    
    def _test_connection(self):
        """Test S3 connection and credentials."""
        try:
            # Try to list objects with limit to test credentials
            self.s3_client.list_objects_v2(
                Bucket=config.AWS_BUCKET_NAME,
                Prefix=config.AWS_PREFIX,
                MaxKeys=1
            )
            logger.info("S3 connection test successful")
        except Exception as e:
            logger.warning(f"S3 connection test failed: {str(e)}")
            raise
    
    def list_recordings(self, limit: int = 100, since_hours: int = 168) -> List[Dict]:
        """
        List audio recordings from S3 bucket.
        
        Args:
            limit: Maximum number of files to return
            since_hours: Only return files modified in the last N hours
            
        Returns:
            List of dictionaries containing file information
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return []
        
        try:
            recordings = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=since_hours)
            
            for page in paginator.paginate(
                Bucket=config.AWS_BUCKET_NAME,
                Prefix=config.AWS_PREFIX
            ):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    # Check if file is recent enough
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Check if it's an audio file
                    file_key = obj['Key']
                    if not self._is_audio_file(file_key):
                        continue
                    
                    # Extract filename
                    filename = Path(file_key).name
                    
                    recording_info = {
                        'key': file_key,
                        'filename': filename,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'size_mb': round(obj['Size'] / 1024 / 1024, 2)
                    }
                    
                    recordings.append(recording_info)
                    
                    # Stop if we've reached the limit
                    if len(recordings) >= limit:
                        break
                
                if len(recordings) >= limit:
                    break
            
            # Sort by last modified (newest first)
            recordings.sort(key=lambda x: x['last_modified'], reverse=True)
            
            logger.info(f"Found {len(recordings)} audio recordings in S3")
            return recordings[:limit]
            
        except Exception as e:
            logger.error(f"Error listing S3 recordings: {str(e)}")
            return []
    
    def download_recording(self, s3_key: str, local_path: Optional[Path] = None) -> Optional[Path]:
        """
        Download a recording from S3 to local storage.
        
        Args:
            s3_key: S3 object key
            local_path: Optional local path, defaults to audio folder
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return None
        
        try:
            # Determine local path
            if local_path is None:
                filename = Path(s3_key).name
                local_path = config.AUDIO_FOLDER / filename
            
            # Create directory if it doesn't exist
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if local_path.exists():
                logger.info(f"File already exists locally: {local_path.name}")
                return local_path
            
            # Download file
            logger.info(f"Downloading {s3_key} to {local_path}")
            self.s3_client.download_file(
                config.AWS_BUCKET_NAME,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"Successfully downloaded: {local_path.name}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading {s3_key}: {str(e)}")
            return None
    
    def download_latest_recordings(self, count: int = 10, since_hours: int = 24) -> List[Path]:
        """
        Download the latest recordings from S3.
        
        Args:
            count: Number of latest recordings to download
            since_hours: Only download files modified in the last N hours
            
        Returns:
            List of local file paths that were downloaded
        """
        try:
            # Get list of recordings
            recordings = self.list_recordings(limit=count, since_hours=since_hours)
            
            if not recordings:
                logger.info("No new recordings found in S3")
                return []
            
            downloaded_files = []
            
            for recording in recordings:
                local_path = self.download_recording(recording['key'])
                if local_path:
                    downloaded_files.append(local_path)
            
            logger.info(f"Downloaded {len(downloaded_files)} recordings from S3")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading latest recordings: {str(e)}")
            return []
    
    def _is_audio_file(self, filename: str) -> bool:
        """Check if file is a supported audio format."""
        return config.is_supported_audio_file(filename)
    
    def get_bucket_stats(self) -> Dict:
        """Get statistics about the S3 bucket."""
        if not self.s3_client:
            return {'error': 'S3 client not initialized'}
        
        try:
            # Count audio files and total size
            paginator = self.s3_client.get_paginator('list_objects_v2')
            total_files = 0
            total_size = 0
            audio_files = 0
            
            for page in paginator.paginate(
                Bucket=config.AWS_BUCKET_NAME,
                Prefix=config.AWS_PREFIX
            ):
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    total_files += 1
                    total_size += obj['Size']
                    
                    if self._is_audio_file(obj['Key']):
                        audio_files += 1
            
            return {
                'total_files': total_files,
                'audio_files': audio_files,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'bucket': config.AWS_BUCKET_NAME,
                'prefix': config.AWS_PREFIX
            }
            
        except Exception as e:
            logger.error(f"Error getting bucket stats: {str(e)}")
            return {'error': str(e)}
    
    def sync_new_recordings(self) -> int:
        """
        Sync new recordings from S3 (download files not already processed).
        Only processes files from the last 7 days.
        
        Returns:
            Number of new files downloaded
        """
        try:
            logger.info("🔄 Starting S3 sync process...")
            
            # Get recordings from last 7 days only
            print(f"📡 Scanning S3 bucket for recordings (last {config.PROCESSING_DAYS_LOOKBACK} days)...")
            recordings = self.list_recordings(limit=1000, since_hours=config.PROCESSING_DAYS_LOOKBACK * 24)
            
            print(f"📊 Found {len(recordings)} total recordings in S3")
            if len(recordings) > 0:
                total_size_mb = sum(r['size_mb'] for r in recordings)
                print(f"📦 Total size: {total_size_mb:.2f} MB")
            
            # Check which files we haven't processed yet
            from processor import AudioProcessor
            processor = AudioProcessor()
            
            new_files = []
            for recording in recordings:
                if not processor.is_file_already_processed(recording['filename']):
                    new_files.append(recording)
            
            print(f"🆕 Found {len(new_files)} new files to download")
            
            if not new_files:
                logger.info("✅ No new recordings to sync from S3")
                return 0
            
            # Show download progress
            downloaded_count = 0
            total_download_mb = sum(f['size_mb'] for f in new_files)
            
            print(f"⬇️  Downloading {len(new_files)} files ({total_download_mb:.2f} MB)...")
            
            for i, recording in enumerate(new_files, 1):
                progress = f"[{i}/{len(new_files)}]"
                print(f"   {progress} {recording['filename']} ({recording['size_mb']:.2f} MB)")
                
                local_path = self.download_recording(recording['key'])
                if local_path:
                    downloaded_count += 1
                    print(f"   ✅ Downloaded: {recording['filename']}")
                else:
                    print(f"   ❌ Failed: {recording['filename']}")
            
            success_rate = (downloaded_count / len(new_files)) * 100 if new_files else 0
            print(f"📥 Download complete: {downloaded_count}/{len(new_files)} files ({success_rate:.1f}% success)")
            
            logger.info(f"Synced {downloaded_count} new recordings from S3")
            return downloaded_count
            
        except Exception as e:
            logger.error(f"Error syncing new recordings: {str(e)}")
            print(f"❌ S3 sync error: {str(e)}")
            return 0

# Global instance
s3_manager = S3AudioManager()