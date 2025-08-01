#!/usr/bin/env python3
"""
Simple script to run the Streamlit audio transcription app
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit app"""
    try:
        # Check if streamlit is installed
        import streamlit
    except ImportError:
        print("❌ Streamlit is not installed. Please run: pip install -r requirements.txt")
        return 1
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app_path = os.path.join(script_dir, "streamlit_app.py")
    
    if not os.path.exists(streamlit_app_path):
        print(f"❌ Streamlit app not found at: {streamlit_app_path}")
        return 1
    
    print("🚀 Starting Streamlit Audio Transcription & Redaction App...")
    print("📱 The app will open in your default web browser")
    print("⏹️  Press Ctrl+C to stop the app")
    print()
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            streamlit_app_path,
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running app: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())