@echo off
chcp 65001 >nul
title Crew Scheduler - Local Development

echo ============================================
echo    Crew Scheduler - Local Mode Setup
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11+ is required but not found.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists.
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file...
    copy .env.example .env >nul
)

echo.
echo ============================================
echo  Setup Complete!
echo ============================================
echo.
echo Database: SQLite (local development)
echo Application running at: http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

:: Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000