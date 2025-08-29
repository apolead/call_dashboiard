"""
Configuration management for the audio transcription automation system.
Handles environment variables, default settings, and validation.
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """Centralized configuration management class."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        # Load environment variables from .env file
        load_dotenv()
        
        # API Configuration
        self.DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', '')
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # Directory Configuration
        self.AUDIO_FOLDER = Path(os.getenv('AUDIO_FOLDER', 'data/audio'))
        self.PROCESSED_FOLDER = Path(os.getenv('PROCESSED_FOLDER', 'data/processed'))
        self.CSV_FILE = Path(os.getenv('CSV_FILE', 'data/transcriptions.csv'))
        self.LOG_FOLDER = Path('logs')
        
        # Flask Configuration
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', 8080))
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
        
        # Processing Configuration
        self.SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        self.MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 100))
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', 60))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', 5))
        
        # Processing Window - Only process files from last 7 days
        self.PROCESSING_DAYS_LOOKBACK = int(os.getenv('PROCESSING_DAYS_LOOKBACK', 7))
        
        # Company Branding
        self.COMPANY_NAME = os.getenv('COMPANY_NAME', 'ApoLead')
        self.COMPANY_LOGO = os.getenv('COMPANY_LOGO', '/static/img/apolead-logo.png')
        self.PRIMARY_COLOR = os.getenv('PRIMARY_COLOR', '#1e40af')
        self.SECONDARY_COLOR = os.getenv('SECONDARY_COLOR', '#3b82f6')
        self.ACCENT_COLOR = os.getenv('ACCENT_COLOR', '#06b6d4')
        
        # OpenAI Prompt Configuration
        self.DEFAULT_OPENAI_PROMPT = os.getenv(
            'OPENAI_PROMPT',
            "Analyze the following call transcription and return ONLY valid JSON with exactly these fields:\n"
            "- summary: A brief 1-2 sentence summary of the call\n"
            "- intent: One of these categories: ROOFING, WINDOWS_DOORS, PLUMBING, ELECTRICAL, HVAC, FLOORING, SIDING_EXTERIOR, KITCHEN_BATH, GENERAL_CONTRACTOR, EMERGENCY_REPAIR, QUOTE_REQUEST, COMPLAINT, OTHER\n"
            "- sub_intent: A specific subcategory based on the intent:\n"
            "  * ROOFING: ROOF_REPAIR, ROOF_REPLACEMENT, ROOF_INSPECTION, ROOF_PURCHASE, GUTTER_CLEANING, GUTTER_REPAIR\n"
            "  * WINDOWS_DOORS: WINDOW_REPAIR, WINDOW_REPLACEMENT, DOOR_REPAIR, DOOR_INSTALLATION, SCREEN_REPAIR\n"
            "  * PLUMBING: LEAK_REPAIR, PIPE_REPAIR, DRAIN_CLEANING, TOILET_REPAIR, FAUCET_REPAIR, WATER_HEATER\n"
            "  * ELECTRICAL: WIRING_REPAIR, OUTLET_INSTALLATION, LIGHTING_REPAIR, ELECTRICAL_INSPECTION, PANEL_UPGRADE\n"
            "  * HVAC: AC_REPAIR, HEATING_REPAIR, DUCT_CLEANING, SYSTEM_INSTALLATION, MAINTENANCE_SERVICE\n"
            "  * KITCHEN_BATH: BATHROOM_REMODEL, KITCHEN_REMODEL, SHOWER_INSTALLATION, COUNTERTOP_REPAIR, TILE_WORK\n"
            "  * QUOTE_REQUEST: ESTIMATE_REQUEST, CONSULTATION, PRICE_INQUIRY, SERVICE_COMPARISON\n"
            "  * OTHER: GENERAL_INQUIRY, APPOINTMENT_SCHEDULING, COMPLAINT, TEST_CALL, WRONG_NUMBER\n\n"
            "Example response format:\n"
            '{{"summary": "Customer called about roof leak repair", "intent": "ROOFING", "sub_intent": "ROOF_REPAIR"}}\n\n'
            "Transcription: {transcription}\n\n"
            "Response (JSON only):"
        )
        
        # AWS S3 Configuration
        self.ENABLE_S3_SYNC = os.getenv('ENABLE_S3_SYNC', 'True').lower() == 'true'
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        self.AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'combined-client-data')
        self.AWS_PREFIX = os.getenv('AWS_PREFIX', 'c_30214/XC_Recordings/')
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # Dashboard Configuration
        self.DASHBOARD_REFRESH_INTERVAL = int(os.getenv('DASHBOARD_REFRESH_INTERVAL', 10))
        self.ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
        
        # Validate configuration
        self._validate_config()
        
        # Setup logging
        self._setup_logging()
    
    def _validate_config(self):
        """Validate required configuration settings."""
        errors = []
        
        if not self.DEEPGRAM_API_KEY:
            errors.append("DEEPGRAM_API_KEY is required")
        
        if not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if errors:
            print("Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            print("\nPlease check your .env file or environment variables.")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        self.LOG_FOLDER.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        log_file = self.LOG_FOLDER / 'app.log'
        
        logging.basicConfig(
            level=logging.DEBUG if self.DEBUG_MODE else logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Set external library log levels
        logging.getLogger('watchdog').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.AUDIO_FOLDER,
            self.PROCESSED_FOLDER,
            self.LOG_FOLDER,
            self.CSV_FILE.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Created directories: {', '.join(str(d) for d in directories)}")
    
    def get_csv_headers(self):
        """Get CSV headers for the transcriptions file."""
        return [
            'timestamp',
            'filename',
            'call_date',
            'call_time',
            'call_datetime',
            'phone_number',
            'call_status',
            'agent_name',
            'estimated_duration_seconds',
            'file_size',
            'duration',
            'transcription',
            'diarized_transcription',
            'speaker_count',
            'summary',
            'intent',
            'sub_intent',
            'status',
            'processing_time',
            'error_message'
        ]
    
    def is_supported_audio_file(self, filename):
        """Check if a file is a supported audio format."""
        return Path(filename).suffix.lower() in self.SUPPORTED_AUDIO_FORMATS
    
    def get_file_size_limit_bytes(self):
        """Get file size limit in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

# Global configuration instance
config = Config()