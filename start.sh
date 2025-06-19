#!/bin/bash

# Text-to-SQL RAG System Startup Script
echo "🚀 Starting Text-to-SQL RAG System..."

# Set OpenAI API Key (set this in your environment or uncomment and add your key)
# export OPENAI_API_KEY="your-openai-api-key-here"
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set."
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
    echo "   Or uncomment and edit the line in this script."
fi

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Kill any existing backend processes
pkill -f "python.*main.py" 2>/dev/null
sleep 2

# Start backend
echo "📦 Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend server..."
npm start &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 5

# Open localhost in default browser
echo "🌍 Opening application in browser..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open http://localhost:3000
elif command -v start >/dev/null 2>&1; then
    # Windows
    start http://localhost:3000
else
    echo "Please open http://localhost:3000 in your browser"
fi

echo "✅ Services started successfully!"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for background processes
wait