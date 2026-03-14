#!/bin/bash
# SocialFlow - Startup Script

set -e

echo "🚀 Starting SocialFlow..."
echo ""

# Check for .env
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your OpenAI/Claude API keys"
    echo ""
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r backend/requirements.txt

# Install Playwright browsers (first time only)
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "🌐 Installing browser (first time only)..."
    playwright install chromium
fi

# Load environment
export $(grep -v '^#' .env | xargs)

echo ""
echo "✅ Starting server..."
echo ""
echo "   🌐 Dashboard: http://localhost:8000"
echo "   📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

# Start backend (serves both API and frontend)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
