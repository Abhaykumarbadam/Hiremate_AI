#!/bin/bash

echo "======================================"
echo "  HireMate AI - Startup Script"
echo "======================================"
echo ""

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY environment variable is not set!"
    echo "Please set it before running:"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Checking for backend.py..."
if [ ! -f "backend.py" ]; then
    echo "❌ backend.py not found in project root!"
    echo "Please place backend.py in the same directory as this script."
    exit 1
fi

echo "✅ backend.py found"
echo ""

echo "Starting Backend Server..."
python3 backend.py &
BACKEND_PID=$!

sleep 3

echo ""
echo "Starting Frontend Dev Server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "  HireMate AI is starting up!"
echo "======================================"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Backend URL: http://localhost:8000"
echo "Frontend URL: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

wait
