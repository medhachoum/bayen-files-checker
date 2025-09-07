@echo off
title Missing Files Detector - Streamlit App
echo.
echo ===============================================
echo   Missing Files Detector - Streamlit App
echo   Now with Folder Selection Dialog!
echo ===============================================
echo.
echo Starting the application...
echo The app will open in your default web browser
echo Press Ctrl+C to stop the application
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first: https://python.org
    pause
    exit /b 1
)

REM Install requirements if needed
if exist requirements.txt (
    echo Installing/updating requirements...
    pip install -r requirements.txt >nul 2>&1
)

REM Run the Streamlit app
echo Starting Streamlit application...
echo.
streamlit run streamlit_missing_files_detector.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false

echo.
echo Application stopped.
pause