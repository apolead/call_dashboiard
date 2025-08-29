#!/usr/bin/env python3
"""
Enhanced Startup script for ApoLead Call Analytics System
Includes setup validation, progress tracking, and comprehensive status monitoring
"""

import subprocess
import sys
import time
import signal
import os
import threading
import queue
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(text, color=Colors.ENDC):
    """Print colored text to terminal."""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    """Print a header with styling."""
    print("\n" + "=" * 80)
    print_colored(f"TARGET {text}", Colors.BOLD + Colors.HEADER)
    print("=" * 80)

def print_step(step_num, total_steps, description):
    """Print a step with progress indicator."""
    progress = f"[{step_num}/{total_steps}]"
    print_colored(f"{progress} {description}...", Colors.OKBLUE)

def print_success(message):
    """Print success message."""
    print_colored(f"SUCCESS: {message}", Colors.OKGREEN)

def print_warning(message):
    """Print warning message."""
    print_colored(f"WARNING: {message}", Colors.WARNING)

def print_error(message):
    """Print error message."""
    print_colored(f"ERROR: {message}", Colors.FAIL)

def print_info(message):
    """Print info message."""
    print_colored(f"INFO: {message}", Colors.OKCYAN)

def validate_environment():
    """Validate environment setup and configuration."""
    print_header("SYSTEM VALIDATION")
    
    validation_passed = True
    
    # Step 1: Check .env file
    print_step(1, 6, "Checking environment configuration")
    env_file = Path(".env")
    if not env_file.exists():
        print_error(".env file not found!")
        print_info("Please copy .env.example to .env and configure your settings")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Step 2: Check required API keys
    print_step(2, 6, "Validating API keys")
    required_keys = ["DEEPGRAM_API_KEY", "OPENAI_API_KEY"]
    
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower()}_here":
            print_error(f"{key} not configured properly")
            validation_passed = False
        else:
            print_success(f"{key} configured")
    
    # Step 3: Check AWS credentials (only if S3 sync is enabled)
    print_step(3, 6, "Validating AWS S3 configuration")
    s3_enabled = os.getenv('ENABLE_S3_SYNC', 'True').lower() == 'true'
    
    if s3_enabled:
        aws_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
        
        for key in aws_keys:
            value = os.getenv(key)
            if not value or value.startswith("your_"):
                print_error(f"{key} not configured properly")
                validation_passed = False
            else:
                print_success(f"{key} configured")
    else:
        print_success("S3 sync disabled - skipping S3 configuration check")
    
    # Step 4: Create necessary directories
    print_step(4, 6, "Creating necessary directories")
    directories = [
        Path("data/audio"),
        Path("data/processed"),
        Path("logs")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print_success(f"Directory ready: {directory}")
    
    # Step 5: Check dependencies
    print_step(5, 6, "Checking Python dependencies")
    required_packages = ["flask", "watchdog", "deepgram", "openai", "pandas", "boto3"]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} not installed")
            validation_passed = False
    
    # Step 6: Test API connectivity
    print_step(6, 6, "Testing API connectivity")
    
    # Test OpenAI API
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Just validate the key format, don't make actual API call during setup
        if os.getenv('OPENAI_API_KEY', '').startswith('sk-'):
            print_success("OpenAI API key format valid")
        else:
            print_warning("OpenAI API key format may be invalid")
    except Exception as e:
        print_warning(f"OpenAI API test inconclusive: {str(e)}")
    
    # Test Deepgram API
    try:
        deepgram_key = os.getenv('DEEPGRAM_API_KEY')
        if deepgram_key and len(deepgram_key) > 20:
            print_success("Deepgram API key format valid")
        else:
            print_warning("Deepgram API key format may be invalid")
    except Exception as e:
        print_warning(f"Deepgram API test inconclusive: {str(e)}")
    
    print("\n" + "-" * 80)
    if validation_passed:
        print_success("PARTY All validation checks passed!")
        return True
    else:
        print_error("ERROR: Some validation checks failed. Please fix the issues above.")
        return False

def stream_output(process, name, output_queue):
    """Stream output from a subprocess to a queue."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                timestamp = datetime.now().strftime('%H:%M:%S')
                output_queue.put(f"[{timestamp}] {name}: {line.strip()}")
        process.stdout.close()
    except Exception as e:
        output_queue.put(f"[ERROR] {name}: {str(e)}")

def start_component_with_monitoring(script_name, component_name, output_queue):
    """Start a component with output monitoring."""
    try:
        print_info(f"Starting {component_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Start output streaming thread
        output_thread = threading.Thread(
            target=stream_output, 
            args=(process, component_name, output_queue),
            daemon=True
        )
        output_thread.start()
        
        print_success(f"{component_name} started (PID: {process.pid})")
        return process, output_thread
    except Exception as e:
        print_error(f"Failed to start {component_name}: {str(e)}")
        return None, None

def print_system_status():
    """Print system status and instructions."""
    print_header("SYSTEM READY")
    print_colored("ROCKET ApoLead Call Analytics System is now running!", Colors.BOLD + Colors.OKGREEN)
    print()
    print_colored("CHART Dashboard Access:", Colors.BOLD)
    print_colored("   WEB Web Interface: http://localhost:8080", Colors.OKCYAN)
    print()
    print_colored("FOLDER File Locations:", Colors.BOLD)
    print_colored("   INBOX Drop audio files: data/audio/", Colors.OKCYAN)
    print_colored("   FILE Results saved to: data/call_transcriptions.csv", Colors.OKCYAN)
    print_colored("   LOGS Logs saved to: logs/", Colors.OKCYAN)
    print()
    print_colored("REFRESH Active Monitoring:", Colors.BOLD)
    print_colored("   • File system monitoring for new audio files", Colors.OKCYAN)
    print_colored("   • AWS S3 automatic sync every 5 minutes", Colors.OKCYAN)
    print_colored("   • Real-time transcription processing", Colors.OKCYAN)
    print_colored("   • Live analytics dashboard updates", Colors.OKCYAN)
    print()
    print_colored("KEYBOARD Commands:", Colors.BOLD)
    print_colored("   • Press Ctrl+C to stop the system", Colors.WARNING)
    print_colored("   • Check logs/ directory for detailed information", Colors.OKCYAN)
    print("=" * 80)

def main():
    """Main startup function with enhanced monitoring."""
    print_colored("MUSIC ApoLead Call Analytics System", Colors.BOLD + Colors.HEADER)
    print_colored("   Advanced Audio Transcription & Analytics Platform", Colors.HEADER)
    print_colored(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.OKCYAN)
    
    # Validate environment
    if not validate_environment():
        print_error("Setup validation failed. Please fix the issues and try again.")
        sys.exit(1)
    
    print_header("STARTING SYSTEM COMPONENTS")
    
    processes = []
    output_queue = queue.Queue()
    
    try:
        # Start file watcher with monitoring
        print_step(1, 2, "Initializing File Watcher & S3 Sync")
        watcher_process, watcher_thread = start_component_with_monitoring(
            "watcher.py", "File Watcher", output_queue
        )
        if watcher_process:
            processes.append(("File Watcher", watcher_process, watcher_thread))
        
        # Brief delay for watcher to initialize
        time.sleep(3)
        
        # Start Flask dashboard
        print_step(2, 2, "Initializing Flask Dashboard")
        dashboard_process, dashboard_thread = start_component_with_monitoring(
            "app.py", "Flask Dashboard", output_queue
        )
        if dashboard_process:
            processes.append(("Flask Dashboard", dashboard_process, dashboard_thread))
        
        if not processes:
            print_error("Failed to start any components")
            return
        
        # Wait a moment for services to fully initialize
        print_info("Waiting for services to initialize...")
        time.sleep(5)
        
        # Print system status
        print_system_status()
        
        # Start monitoring loop
        print_header("LIVE SYSTEM MONITORING")
        print_colored("TV Real-time component output:", Colors.BOLD)
        print("-" * 80)
        
        last_status_check = time.time()
        
        while True:
            # Display queued output
            try:
                while True:
                    message = output_queue.get_nowait()
                    print(message)
            except queue.Empty:
                pass
            
            # Periodic status check
            current_time = time.time()
            if current_time - last_status_check > 30:  # Every 30 seconds
                last_status_check = current_time
                
                active_count = 0
                for name, process, thread in processes:
                    if process.poll() is None:
                        active_count += 1
                    else:
                        print_warning(f"{name} has stopped unexpectedly")
                
                if active_count == len(processes):
                    print_colored(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: All {active_count} components running normally", Colors.OKGREEN)
                
            # Check if all processes are still running
            if all(process.poll() is None for _, process, _ in processes):
                time.sleep(1)
                continue
            else:
                print_error("One or more components have stopped")
                break
    
    except KeyboardInterrupt:
        print_colored("\n\nSTOP Shutdown requested by user...", Colors.WARNING)
    
    except Exception as e:
        print_error(f"System error: {str(e)}")
    
    finally:
        # Clean shutdown
        print_header("SYSTEM SHUTDOWN")
        print_info("Stopping all components gracefully...")
        
        for name, process, thread in processes:
            if process.poll() is None:
                print_info(f"Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=10)
                    print_success(f"{name} stopped")
                except subprocess.TimeoutExpired:
                    print_warning(f"Force killing {name}...")
                    process.kill()
                    print_success(f"{name} force stopped")
                except Exception as e:
                    print_error(f"Error stopping {name}: {str(e)}")
        
        print_success("All components stopped")
        print_colored("WAVE ApoLead Call Analytics System shutdown complete", Colors.BOLD + Colors.OKCYAN)

if __name__ == "__main__":
    main()