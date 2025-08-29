"""
Vercel-specific configuration management for the audio transcription automation system.
Handles serverless environment setup with in-memory storage for CSV data.
"""

import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import pandas as pd

class VercelConfig:
    """Vercel-optimized configuration management class."""
    
    def __init__(self):
        """Initialize configuration with environment variables and serverless defaults."""
        # Load environment variables from .env file
        load_dotenv()
        
        # API Configuration
        self.DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', '')
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
        # Serverless Directory Configuration - Use temp directories
        temp_dir = Path(tempfile.gettempdir())
        self.AUDIO_FOLDER = temp_dir / 'audio'
        self.PROCESSED_FOLDER = temp_dir / 'processed' 
        self.CSV_FILE = temp_dir / 'call_transcriptions.csv'
        self.LOG_FOLDER = temp_dir / 'logs'
        
        # Flask Configuration
        self.FLASK_PORT = int(os.getenv('PORT', 8080))  # Vercel uses PORT
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
        self.SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
        
        # Processing Configuration
        self.SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg']
        self.MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 25))  # Smaller for serverless
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', 30))  # Shorter for serverless
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', 2))
        self.RETRY_DELAY = int(os.getenv('RETRY_DELAY', 3))
        
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
        
        # AWS S3 Configuration (Primary data source for serverless)
        self.ENABLE_S3_SYNC = os.getenv('ENABLE_S3_SYNC', 'True').lower() == 'true'
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        self.AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'combined-client-data')
        self.AWS_PREFIX = os.getenv('AWS_PREFIX', 'c_30214/XC_Recordings/')
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
        
        # Dashboard Configuration
        self.DASHBOARD_REFRESH_INTERVAL = int(os.getenv('DASHBOARD_REFRESH_INTERVAL', 30))
        self.ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 50))
        
        # Validate configuration
        self._validate_config()
        
        # Setup logging for serverless
        self._setup_serverless_logging()
        
        # Initialize in-memory CSV data
        self._initialize_csv_data()
    
    def _validate_config(self):
        """Validate required configuration settings."""
        # For demo purposes, allow missing API keys in development
        if not self.DEEPGRAM_API_KEY and os.getenv('VERCEL_ENV') == 'production':
            logging.warning("DEEPGRAM_API_KEY is missing - some features may not work")
        
        if not self.OPENAI_API_KEY and os.getenv('VERCEL_ENV') == 'production':
            logging.warning("OPENAI_API_KEY is missing - some features may not work")
    
    def _setup_serverless_logging(self):
        """Setup logging configuration for serverless environment."""
        # Configure logging for serverless - use console output
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        logging.basicConfig(
            level=logging.INFO,  # Use INFO for serverless to reduce noise
            format=log_format,
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        
        # Set external library log levels
        logging.getLogger('watchdog').setLevel(logging.ERROR)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('boto3').setLevel(logging.WARNING)
    
    def _initialize_csv_data(self):
        """Initialize in-memory CSV data with sample data for demo."""
        # Create sample data for demo purposes
        sample_data = {
            'timestamp': ['2025-08-28 10:30:00', '2025-08-28 11:15:00', '2025-08-28 12:00:00'],
            'filename': ['sample_call_1.mp3', 'sample_call_2.mp3', 'sample_call_3.mp3'],
            'call_date': ['2025-08-28', '2025-08-28', '2025-08-28'],
            'call_time': ['10:30', '11:15', '12:00'],
            'call_datetime': ['2025-08-28 10:30:00', '2025-08-28 11:15:00', '2025-08-28 12:00:00'],
            'phone_number': ['555-0001', '555-0002', '555-0003'],
            'call_status': ['answered', 'answered', 'voicemail'],
            'agent_name': ['Demo Agent', 'Demo Agent', 'Demo Agent'],
            'estimated_duration_seconds': [120, 89, 45],
            'file_size': ['1.2 MB', '890 KB', '450 KB'],
            'duration': '2m 0s,1m 29s,45s'.split(','),
            'transcription': [
                'Customer called about roof repair services',
                'Inquiry about window replacement quote',
                'Left voicemail about kitchen remodeling'
            ],
            'diarized_transcription': [
                'Speaker 1: Hello, I need roof repair. Speaker 2: We can help with that.',
                'Speaker 1: Looking for window quotes. Speaker 2: Let me get you pricing.',
                'Speaker 1: Please call back about kitchen work.'
            ],
            'speaker_count': [2, 2, 1],
            'summary': [
                'Customer needs roof repair after storm damage',
                'Homeowner requesting window replacement quotes',
                'Kitchen remodeling inquiry left on voicemail'
            ],
            'intent': ['ROOFING', 'WINDOWS_DOORS', 'KITCHEN_BATH'],
            'sub_intent': ['ROOF_REPAIR', 'WINDOW_REPLACEMENT', 'KITCHEN_REMODEL'],
            'status': ['completed', 'completed', 'completed'],
            'processing_time': ['3.2s', '2.8s', '1.5s'],
            'error_message': ['', '', ''],
            'primary_disposition': ['QUALIFIED_LEAD', 'APPOINTMENT_SET', 'CALLBACK_REQUESTED'],
            'secondary_disposition': ['IMMEDIATE', 'FUTURE', 'FOLLOW_UP_REQUIRED']
        }
        
        # Create DataFrame and save to temp CSV
        df = pd.DataFrame(sample_data)
        df.to_csv(self.CSV_FILE, index=False)
        logging.info(f"Initialized sample CSV data at {self.CSV_FILE}")
    
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
        
        logging.info(f"Created temp directories for serverless deployment")
    
    def get_csv_headers(self):
        """Get CSV headers for the transcriptions file."""
        return [
            'timestamp', 'filename', 'call_date', 'call_time', 'call_datetime',
            'phone_number', 'call_status', 'agent_name', 'estimated_duration_seconds',
            'file_size', 'duration', 'transcription', 'diarized_transcription',
            'speaker_count', 'summary', 'intent', 'sub_intent', 'status',
            'processing_time', 'error_message', 'primary_disposition', 'secondary_disposition'
        ]
    
    def is_supported_audio_file(self, filename):
        """Check if a file is a supported audio format."""
        return Path(filename).suffix.lower() in self.SUPPORTED_AUDIO_FORMATS
    
    def get_file_size_limit_bytes(self):
        """Get file size limit in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

# Global configuration instance for Vercel
config = VercelConfig()