#!/usr/bin/env python3
"""
Quick fix script for .env file issues
This will help resolve the dotenv parsing errors
"""

import os
from pathlib import Path

def fix_env_file():
    """Fix common .env file issues"""
    print("🔧 Fixing .env file issues...")
    
    env_file = Path(".env")
    env_clean = Path(".env.clean")
    env_backup = Path(".env.backup")
    
    # Backup existing .env if it exists
    if env_file.exists():
        print("📄 Backing up existing .env file...")
        with open(env_file, 'r') as f:
            content = f.read()
        with open(env_backup, 'w') as f:
            f.write(content)
        print(f"✅ Backup saved as .env.backup")
    
    # Check if clean template exists
    if not env_clean.exists():
        print("❌ .env.clean template not found!")
        return False
    
    # Copy clean template to .env
    print("📋 Creating clean .env file from template...")
    with open(env_clean, 'r') as f:
        clean_content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(clean_content)
    
    print("✅ Clean .env file created!")
    print("\n⚠️  IMPORTANT: You now need to edit .env and add your actual credentials:")
    print("   1. DEEPGRAM_API_KEY=your_actual_deepgram_key")
    print("   2. OPENAI_API_KEY=your_actual_openai_key")
    print("   3. AWS_ACCESS_KEY_ID=your_actual_aws_key")
    print("   4. AWS_SECRET_ACCESS_KEY=your_actual_aws_secret")
    print("   5. S3_BUCKET_NAME=your_actual_bucket_name")
    print("\nEdit the .env file with your real credentials, then run python start.py again")
    
    return True

if __name__ == "__main__":
    print("🎯 ApoLead Call Analytics - .env Fix Tool")
    print("=" * 50)
    fix_env_file()