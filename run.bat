@echo off
REM Digital Rename Bot - Local Run Script for Windows
REM Make sure to set your environment variables before running

echo ========================================
echo Digital Rename Bot - Starting...
echo ========================================
echo.

REM Check if .env file exists
if exist .env (
    echo Loading environment variables from .env file...
    REM Note: This script requires python-dotenv to load .env files
    REM Install it with: pip install python-dotenv
    python -c "from dotenv import load_dotenv; load_dotenv()" 2>nul
    if errorlevel 1 (
        echo WARNING: python-dotenv not installed. Install it with: pip install python-dotenv
        echo Or set environment variables manually in PowerShell before running.
        echo.
    )
) else (
    echo WARNING: .env file not found!
    echo Please create a .env file or set environment variables manually.
    echo See SETUP.md for instructions.
    echo.
)

echo Starting bot...
python bot.py

pause
