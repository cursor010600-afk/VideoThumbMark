# Digital Rename Bot - Local Run Script for PowerShell
# Make sure to set your environment variables before running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Digital Rename Bot - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (Test-Path .env) {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Yellow
    # Load .env file if python-dotenv is available
    python -c "from dotenv import load_dotenv; load_dotenv()" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: python-dotenv not installed. Install it with: pip install python-dotenv" -ForegroundColor Yellow
        Write-Host "Or set environment variables manually before running." -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Please create a .env file or set environment variables manually." -ForegroundColor Red
    Write-Host "See SETUP.md for instructions." -ForegroundColor Red
    Write-Host ""
}

Write-Host "Starting bot..." -ForegroundColor Green
python bot.py
