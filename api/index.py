"""
Vercel serverless entry point for the audio transcription dashboard.
This file adapts the Flask app for serverless deployment on Vercel.
"""

# Import the minimal Flask app directly
from app import app

# Vercel expects the Flask app to be available as 'app'
# This is now using our minimal serverless version

if __name__ == "__main__":
    app.run()