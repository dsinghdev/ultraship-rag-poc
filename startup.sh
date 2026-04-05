#!/bin/bash

# Start FastAPI in background
echo "🚀 Starting FastAPI API on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
sleep 3

# Start Streamlit
echo "🎨 Starting Streamlit UI on port 8510..."
streamlit run app/streamlit_app.py --server.port=8510 --server.address=0.0.0.0 --server.headless=true &
STREAMLIT_PID=$!

echo "✅ Both services started!"
echo "📡 API: http://localhost:8000"
echo "🎨 UI: http://localhost:8510"

# Wait for both processes
wait $API_PID $STREAMLIT_PID
