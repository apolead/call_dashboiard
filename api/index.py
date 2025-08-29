"""
Vercel serverless entry point for the audio transcription dashboard.
This file adapts the Flask app for serverless deployment on Vercel.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Import the Vercel-optimized Flask app
from app_vercel import app

# Vercel expects the Flask app to be available as 'app'
# This is now using our serverless-optimized version

if __name__ == "__main__":
    app.run()