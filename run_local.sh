#!/bin/bash

# ============================================
# Crew Scheduler - Local Development Script
# ============================================

set -e

echo "🚀 Starting Crew Scheduler (Local Mode)"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.11+ is required but not found."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "🔧 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Export environment variables
export DEBUG=true
export DATABASE_URL="sqlite:///./crew_scheduler.db"
export REDIS_URL=""  # Not needed for local dev with SQLite

echo ""
echo "✅ All setup complete!"
echo ""
echo "📊 Database: SQLite (local development)"
echo "🌐 Application running at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo ""
echo "💡 To stop the server, press Ctrl+C"
echo ""

# Run the application
echo "🎉 Starting FastAPI application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000