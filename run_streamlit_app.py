#!/usr/bin/env python3
"""
Startup script for Missing Files Detector Streamlit App

This script checks dependencies and launches the Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_streamlit():
    """Check if Streamlit is installed."""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def check_tkinter():
    """Check if tkinter is available for folder dialog."""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def install_requirements():
    """Install required packages."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        return False
    
    try:
        print("📦 Installing required packages...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def run_streamlit_app():
    """Run the Streamlit application."""
    app_file = Path(__file__).parent / "streamlit_missing_files_detector.py"
    
    if not app_file.exists():
        print("❌ Streamlit app file not found!")
        return False
    
    try:
        print("🚀 Starting Streamlit application...")
        print("📝 The app will open in your default web browser")
        print("🛑 Press Ctrl+C to stop the application")
        print("-" * 50)
        
        subprocess.run([
            "streamlit", "run", str(app_file),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n✅ Application stopped by user")
        return True
    except FileNotFoundError:
        print("❌ Streamlit command not found. Please install streamlit first:")
        print("   pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Error running application: {e}")
        return False

def main():
    """Main startup function."""
    print("🔍 Missing Files Detector - Streamlit App")
    print("=" * 50)
    
    # Check if Streamlit is installed
    if not check_streamlit():
        print("📦 Streamlit not found. Installing requirements...")
        if not install_requirements():
            print("❌ Failed to install requirements. Please install manually:")
            print("   pip install -r requirements.txt")
            return
    
    # Check tkinter availability
    if check_tkinter():
        print("✅ tkinter available - folder dialog will work")
    else:
        print("⚠️  tkinter not available - folder dialog disabled")
        print("   You can still enter folder paths manually")
    
    # Check if textData exists (optional warning)
    if Path("textData").exists():
        print("✅ textData folder found in current directory")
    else:
        print("⚠️  textData folder not found in current directory")
        print("   You can still scan other folders using the app")
    
    print()
    
    # Run the app
    run_streamlit_app()

if __name__ == "__main__":
    main()