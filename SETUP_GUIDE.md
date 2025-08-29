# 🎯 ApoLead Call Analytics System - Complete Setup Guide

Welcome to the ApoLead Call Analytics System! This guide will walk you through the complete setup process with comprehensive progress tracking and monitoring.

## 📋 What You'll Need

Before starting, gather these credentials:

### Required API Keys
- **Deepgram API Key** - For audio transcription ([Sign up here](https://deepgram.com/))
- **OpenAI API Key** - For AI analysis ([Get yours here](https://openai.com/))

### Optional but Recommended
- **AWS S3 Credentials** - For automatic recording downloads
  - AWS Access Key ID
  - AWS Secret Access Key  
  - S3 Bucket Name
  - AWS Region (usually `us-east-1`)

## 🚀 Setup Methods

### Method 1: Automated Setup (Recommended)

The automated setup provides a step-by-step wizard with validation:

```bash
cd audio-transcription-app
python setup.py
```

**What the automated setup does:**
- ✅ **Environment Configuration** - Guides you through API key setup
- ✅ **Dependency Installation** - Automatically installs all Python packages
- ✅ **Directory Creation** - Creates all necessary folders
- ✅ **Configuration Validation** - Tests your API keys and settings
- ✅ **Next Steps** - Shows you exactly what to do next

### Method 2: Manual Setup

If you prefer manual control:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start the system:**
   ```bash
   python start.py
   ```

## 🖥️ What You'll See When Starting

When you run `python start.py`, you'll see comprehensive progress tracking:

### System Validation Phase
```
🎯 SYSTEM VALIDATION
================================================================================
[1/6] Checking environment configuration...
✅ .env file found and loaded

[2/6] Validating API keys...
✅ DEEPGRAM_API_KEY configured
✅ OPENAI_API_KEY configured

[3/6] Validating AWS S3 configuration...
✅ AWS_ACCESS_KEY_ID configured
✅ AWS_SECRET_ACCESS_KEY configured
✅ S3_BUCKET_NAME configured

[4/6] Creating necessary directories...
✅ Directory ready: data/audio
✅ Directory ready: data/processed
✅ Directory ready: logs

[5/6] Checking Python dependencies...
✅ flask installed
✅ watchdog installed
✅ deepgram installed
✅ openai installed
✅ pandas installed
✅ boto3 installed

[6/6] Testing API connectivity...
✅ OpenAI API key format valid
✅ Deepgram API key format valid

🎉 All validation checks passed!
```

### System Startup Phase
```
🎯 STARTING SYSTEM COMPONENTS
================================================================================
[1/2] Initializing File Watcher & S3 Sync...
ℹ️  Starting File Watcher...
✅ File Watcher started (PID: 12345)

[2/2] Initializing Flask Dashboard...
ℹ️  Starting Flask Dashboard...
✅ Flask Dashboard started (PID: 12346)
```

### System Ready
```
🎯 SYSTEM READY
================================================================================
🚀 ApoLead Call Analytics System is now running!

📊 Dashboard Access:
   🌐 Web Interface: http://localhost:8080

📁 File Locations:
   📥 Drop audio files: data/audio/
   📄 Results saved to: data/call_transcriptions.csv
   📋 Logs saved to: logs/

🔄 Active Monitoring:
   • File system monitoring for new audio files
   • AWS S3 automatic sync every 5 minutes
   • Real-time transcription processing
   • Live analytics dashboard updates

⌨️  Commands:
   • Press Ctrl+C to stop the system
   • Check logs/ directory for detailed information
```

## 📊 Live Monitoring

After startup, you'll see real-time system monitoring:

### S3 Sync Progress
```
🌊 S3 sync worker started (checking every 5 minutes)
📡 Scanning S3 bucket for recordings (last 7 days)...
📊 Found 25 total recordings in S3
📦 Total size: 487.3 MB
🆕 Found 3 new files to download
⬇️  Downloading 3 files (45.2 MB)...
   [1/3] call_recording_001.wav (15.8 MB)
   ✅ Downloaded: call_recording_001.wav
   [2/3] call_recording_002.wav (18.1 MB)
   ✅ Downloaded: call_recording_002.wav
   [3/3] call_recording_003.wav (11.3 MB)
   ✅ Downloaded: call_recording_003.wav
📥 Download complete: 3/3 files (100.0% success)
```

### File Processing Progress
```
🆕 New audio file detected: call_recording_001.wav

🎵 Processing: call_recording_001.wav
   📁 File size: 15.8 MB
   🎤 [1/3] Transcribing with Deepgram...
   ✅ Transcription complete: 8.3m audio, 2,847 chars
   🤖 [2/3] Analyzing with OpenAI...
   ✅ AI analysis complete: Intent = ROOFING
   💾 [3/3] Saving results...
   🎉 Processing complete! (2.1m total)
```

### Existing Files Check
```
📂 Found 5 existing audio files
🔄 Processing 2 unprocessed files...
   [1/2] Queuing: old_call_001.wav
   [2/2] Queuing: old_call_002.wav
```

## 🌐 Accessing the Dashboard

1. **Open your browser** to `http://localhost:8080`
2. **View real-time analytics** with charts and metrics
3. **Monitor processing status** with live updates
4. **Browse all transcriptions** with search and filtering

### Dashboard Features You'll See:
- **📊 Analytics Cards** - Total calls, success rate, processing metrics
- **📈 Interactive Charts** - Intent distribution, daily trends, hourly patterns
- **📋 Call Table** - All transcriptions with detailed view
- **🔍 Advanced Search** - Filter by text, intent, date, status
- **⚙️ Settings Panel** - Theme toggle, refresh intervals, S3 sync controls

## 🔧 Terminal Commands

### View Live Logs
```bash
# Watch application logs in real-time
tail -f logs/app.log

# View just error messages
grep ERROR logs/app.log

# Check system status
python -c "from config import config; print('System OK')"
```

### Manual Operations
```bash
# Process specific file manually
python processor.py path/to/audio.wav

# Check S3 connection
python -c "from s3_manager import s3_manager; print(s3_manager.get_bucket_stats())"

# View current configuration
python -c "from config import config; print(f'Audio folder: {config.AUDIO_FOLDER}')"
```

## 📁 File Organization

After setup, your directory structure will look like:

```
audio-transcription-app/
├── 📄 .env                      # Your API keys and settings
├── 📄 .env.example              # Template for configuration
├── 📄 start.py                  # Enhanced startup script with progress tracking
├── 📄 setup.py                  # Automated setup wizard
├── 📂 data/
│   ├── 📂 audio/                # 📥 Drop audio files here
│   ├── 📂 processed/            # ✅ Completed files moved here
│   └── 📄 call_transcriptions.csv # 📊 All results stored here
├── 📂 logs/                     # 📋 System logs and debugging info
├── 📂 static/                   # 🎨 Dashboard styling and scripts
└── 📂 templates/                # 🌐 Dashboard HTML templates
```

## 🚨 Troubleshooting

### Common Startup Issues

**❌ API Key Errors**
```
[ERROR] DEEPGRAM_API_KEY not configured properly
```
**Solution:** Check your `.env` file and ensure API keys are correctly entered without quotes.

**❌ Dependency Issues**
```
[ERROR] flask not installed
```
**Solution:** Run `pip install -r requirements.txt` or use the automated setup.

**❌ Port Already in Use**
```
[ERROR] Port 5000 is already in use
```
**Solution:** Either stop the conflicting service or change the port in your `.env` file.

### Monitoring System Health

The system provides comprehensive monitoring:

- **✅ Real-time status updates** every 30 seconds
- **📊 Component health checks** for File Watcher and Dashboard
- **🔄 Automatic restart** detection for failed components
- **📋 Detailed logging** in the `logs/` directory

### Getting Help

1. **Check the live monitoring output** - Most issues are shown in real-time
2. **Review the logs** - `tail -f logs/app.log` shows detailed information
3. **Verify configuration** - The startup validation catches most configuration issues
4. **Test individual components** - Use the manual commands above to isolate problems

## ✅ Success Indicators

You'll know the system is working correctly when you see:

1. **All validation checks pass** during startup
2. **Both components start successfully** (File Watcher and Dashboard)
3. **Dashboard loads** at `http://localhost:8080`
4. **S3 sync completes** without errors (if configured)
5. **Test file processing** works end-to-end

## 🎉 You're Ready!

Once you see the "SYSTEM READY" message and can access the dashboard, your ApoLead Call Analytics System is fully operational!

- **Drop audio files** into `data/audio/` or let S3 sync handle it automatically
- **Monitor progress** in real-time through the terminal output
- **View results** on the beautiful analytics dashboard
- **Track performance** with comprehensive metrics and charts

Enjoy your new AI-powered call analytics system! 🚀