# 🎵 ApoLead Call Analytics System

**Advanced Audio Transcription & Analytics Platform**

A complete enterprise-grade audio transcription automation system with AWS S3 integration, real-time monitoring, and comprehensive analytics dashboard. Built specifically for home improvement call centers with intelligent intent classification and beautiful data visualization.

## Features

### 🎵 Audio Processing
- **Automatic monitoring** of local folder for new audio files
- **Multiple format support**: MP3, WAV, M4A, FLAC, OGG
- **Deepgram integration** for high-quality transcription with speaker diarization
- **OpenAI integration** for intelligent analysis with standardized intent classification
- **AWS S3 integration** for automatic recording downloads from cloud storage
- **Automatic file management** with processed file organization

### 📊 Live Dashboard
- **Real-time updates** without page refresh
- **Comprehensive statistics** and metrics
- **Advanced search** across transcriptions and AI analysis
- **Export functionality** (CSV, JSON)
- **File upload** with drag-and-drop interface
- **AWS S3 browser** for cloud recording management
- **Automatic S3 sync** every 5 minutes in background
- **Dark/light theme** support
- **Responsive design** for mobile and desktop

### 🔧 System Features
- **Robust error handling** and retry mechanisms
- **Comprehensive logging** with file and console output
- **Health monitoring** and status indicators
- **Configurable processing** options
- **Security best practices** with input validation

## 🚀 Quick Setup

### Method 1: Automated Setup (Recommended)

1. **Navigate to the project directory**:
   ```bash
   cd audio-transcription-app
   ```

2. **Run the automated setup**:
   ```bash
   python setup.py
   ```
   
   The setup wizard will:
   - ✅ Guide you through API key configuration
   - ✅ Install all required dependencies
   - ✅ Create necessary directories
   - ✅ Validate your configuration
   - ✅ Provide next steps

3. **Start the system**:
   ```bash
   python start.py
   ```

### Method 2: Manual Setup

#### Prerequisites
- Python 3.8 or higher
- Deepgram API key ([Get one here](https://deepgram.com/))
- OpenAI API key ([Get one here](https://openai.com/))
- AWS S3 credentials (optional but recommended)

#### Step-by-Step Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your actual credentials
   notepad .env  # Windows
   # or
   nano .env     # Linux/Mac
   ```

3. **Update .env file**:
   ```bash
   # Required API Keys
   DEEPGRAM_API_KEY=your_actual_deepgram_api_key
   OPENAI_API_KEY=your_actual_openai_api_key
   
   # AWS S3 Configuration (Optional but recommended)
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   S3_BUCKET_NAME=your_bucket_name
   S3_REGION=us-east-1
   
   # Optional customization
   COMPANY_NAME=ApoLead
   PRIMARY_COLOR=#1e40af
   PROCESSING_DAYS_LOOKBACK=7
   FLASK_PORT=8080
   ```

## Usage

### Starting the System

#### Option 1: Single Command Startup (Recommended)
```bash
python start.py
```
This starts both the file watcher and dashboard automatically.

#### Option 2: Manual Startup
Run these two commands in separate terminals:

1. **File Watcher** (Monitors for new audio files)
```bash
python watcher.py
```

2. **Dashboard** (Web interface)
```bash
python app.py
```

### Accessing the Dashboard

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. The dashboard will show real-time processing status and results

### Processing Audio Files

#### Method 1: AWS S3 Integration (Recommended)
1. **Automatic Sync**: System automatically downloads new recordings every 5 minutes
2. **Manual Sync**: Click "Sync S3" button for immediate download
3. **Browse S3**: Use "Browse S3" to view and selectively download recordings
4. Files are automatically processed after download

#### Method 2: Local File Drop
1. Drop audio files into the `data/audio/` folder
2. The system will automatically detect and process them
3. View results in real-time on the dashboard

#### Method 3: Web Upload
1. Use the "Upload Audio" button in the dashboard
2. Select your audio file
3. The file will be automatically processed

### Supported File Formats
- **MP3** - Most common format
- **WAV** - Uncompressed audio
- **M4A** - Apple audio format
- **FLAC** - Lossless compression
- **OGG** - Open source format

### File Size Limits
- Maximum file size: 100MB (configurable)
- Processing time varies based on file duration and complexity

## Dashboard Features

### 📈 Statistics Overview
- **Total Files Processed**: Count of all processed audio files
- **Success Rate**: Percentage of successfully processed files
- **Average Processing Time**: Mean time per successful transcription
- **Total Audio Duration**: Sum of all processed audio duration

### 🔍 Search and Filter
- **Text Search**: Search across transcriptions and AI analysis
- **Status Filter**: Filter by completed, failed, or processing status
- **Real-time Results**: Instant search results as you type

### 📋 Data Management
- **View Details**: Click eye icon to see full transcription, summary, and intent
- **Intent Classification**: Automatic categorization of home improvement calls
- **Reprocess Files**: Re-run failed or outdated transcriptions
- **Delete Records**: Remove unwanted entries
- **Export Data**: Download results as CSV or JSON

### 🏠 Home Improvement Intent Classification

The system automatically classifies calls into standardized categories:

- **ROOFING**: Roof repairs, replacement, leaks, gutters
- **WINDOWS_DOORS**: Window/door installation, repair, replacement
- **PLUMBING**: Pipes, fixtures, water issues, bathroom work
- **ELECTRICAL**: Wiring, outlets, electrical repairs/installation
- **HVAC**: Heating, cooling, air conditioning, ventilation
- **FLOORING**: Carpet, hardwood, tile installation/repair
- **SIDING_EXTERIOR**: Siding, exterior painting, deck work
- **KITCHEN_BATH**: Kitchen/bathroom renovation, cabinets
- **GENERAL_CONTRACTOR**: Multi-trade projects, general construction
- **EMERGENCY_REPAIR**: Urgent repairs needed immediately
- **QUOTE_REQUEST**: Customer requesting price estimates
- **COMPLAINT**: Service complaints, billing issues
- **OTHER**: Anything not fitting above categories

### ⚙️ Settings
- **Auto-refresh**: Configure dashboard refresh intervals (5s, 10s, 30s, or manual)
- **Theme Toggle**: Switch between light and dark themes
- **Status Monitoring**: Real-time system health indicators

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPGRAM_API_KEY` | Required | Your Deepgram API key |
| `OPENAI_API_KEY` | Required | Your OpenAI API key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model to use |
| `FLASK_PORT` | `5000` | Dashboard port |
| `DEBUG_MODE` | `True` | Enable debug logging |
| `MAX_FILE_SIZE_MB` | `100` | Maximum file size limit |
| `API_TIMEOUT` | `60` | API request timeout (seconds) |
| `MAX_RETRIES` | `3` | Number of retry attempts |
| `RETRY_DELAY` | `5` | Delay between retries (seconds) |

### Custom OpenAI Prompts

You can customize the AI analysis by setting the `OPENAI_PROMPT` environment variable:

```bash
OPENAI_PROMPT="Provide a detailed analysis of this conversation including: 1) Summary, 2) Key participants, 3) Main topics, 4) Action items, 5) Sentiment. Transcription: {transcription}"
```

## API Endpoints

The system provides a RESTful API for integration:

### Data Endpoints
- `GET /api/data` - Get all transcription records
- `GET /api/latest/{count}` - Get latest N records
- `GET /api/stats` - Get processing statistics
- `GET /api/search?q={query}` - Search transcriptions
- `GET /api/file/{filename}` - Get detailed file information

### Management Endpoints
- `POST /api/upload` - Upload audio file
- `POST /api/reprocess/{filename}` - Reprocess specific file
- `DELETE /api/delete/{filename}` - Delete record
- `GET /api/export?format={csv|json}` - Export data
- `GET /api/health` - System health check

## Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Configuration Errors:
  - DEEPGRAM_API_KEY is required
  - OPENAI_API_KEY is required
```
**Solution**: Ensure your `.env` file contains valid API keys.

#### 2. File Processing Failures
**Symptoms**: Files appear in the folder but aren't processed
**Solutions**:
- Check file format is supported
- Verify file size is under limit
- Check logs for specific error messages
- Ensure API keys have sufficient credits

#### 3. Dashboard Not Loading
**Symptoms**: Browser shows connection refused
**Solutions**:
- Ensure Flask app is running (`python app.py`)
- Check if port 5000 is available
- Try accessing `http://127.0.0.1:5000` instead

#### 4. Transcription Quality Issues
**Solutions**:
- Ensure audio quality is good (clear speech, minimal background noise)
- Check if the audio language is supported by Deepgram
- Consider preprocessing audio files for better quality

### Log Files

Check the `logs/app.log` file for detailed error information:
```bash
tail -f logs/app.log
```

### Health Check

Monitor system health via:
- Dashboard status indicator
- API endpoint: `http://localhost:5000/api/health`
- Log file monitoring

## Development

### Project Structure
```
audio-transcription-app/
├── app.py                 # Flask dashboard application
├── processor.py           # Audio processing engine
├── watcher.py            # File monitoring service
├── config.py             # Configuration management
├── requirements.txt      # Dependencies
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
├── data/
│   ├── audio/            # Input folder
│   ├── processed/        # Processed files
│   └── transcriptions.csv # Results database
├── templates/            # HTML templates
├── static/              # CSS/JS assets
└── logs/                # Application logs
```

### Adding New Features

1. **Custom Processing Logic**: Modify `processor.py`
2. **Dashboard Enhancements**: Update templates and static files
3. **API Extensions**: Add routes to `app.py`
4. **Configuration Options**: Extend `config.py`

### Testing

Run basic functionality tests:
```bash
# Test configuration
python -c "from config import config; print('Config loaded successfully')"

# Test API connectivity
python -c "from processor import AudioProcessor; p = AudioProcessor(); print('APIs initialized')"
```

## Security Considerations

### API Key Protection
- Never commit API keys to version control
- Use environment variables for sensitive data
- Rotate API keys regularly

### File Validation
- File type validation prevents malicious uploads
- File size limits prevent resource exhaustion
- Input sanitization prevents injection attacks

### Network Security
- Dashboard runs on localhost by default
- Consider VPN or authentication for remote access
- Use HTTPS in production environments

## Performance Optimization

### Processing Performance
- Adjust `MAX_RETRIES` and `RETRY_DELAY` based on your network
- Monitor API rate limits and usage
- Consider upgrading to faster OpenAI models for better performance

### Dashboard Performance
- Adjust auto-refresh intervals based on usage patterns
- Use search and filters to manage large datasets
- Consider pagination for very large result sets

### Resource Management
- Monitor disk space in `data/` directories
- Regularly archive old transcription files
- Clean up log files periodically

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with Deepgram and OpenAI terms of service when using their APIs.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review log files for detailed error information
3. Verify API key validity and credit availability
4. Ensure all dependencies are properly installed

## Version History

- **v1.0.0** - Initial release with complete functionality
  - Real-time audio file monitoring
  - Deepgram and OpenAI integration
  - Web dashboard with live updates
  - Export and management features
  - Comprehensive error handling and logging