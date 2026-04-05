#!/bin/bash

# Ultra Doc-Intelligence - Local Development Script

echo "🚢 Ultra Doc-Intelligence - Starting Local Development"
echo "======================================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env and add your GOOGLE_API_KEY before continuing."
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Check if GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_gemini_api_key_here" ]; then
    echo "❌ GOOGLE_API_KEY is not set in .env file"
    echo "📝 Please add your Google Gemini API key to .env file"
    exit 1
fi

echo "✅ Environment loaded"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# Create uploads directory
mkdir -p uploads

# Start FastAPI API in background
echo "🚀 Starting FastAPI API on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for API to start
sleep 3

# Start Streamlit
echo "🎨 Starting Streamlit UI on port 8510..."
streamlit run app/streamlit_app.py --server.port=8510 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

echo ""
echo "✅ Application started!"
echo "📡 API: http://localhost:8000"
echo "🎨 UI: http://localhost:8510"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

# Wait for processes
wait $API_PID $STREAMLIT_PID
