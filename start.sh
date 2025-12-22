#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

# Start Backend
echo "Starting Backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Start uvicorn in background
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start vite in background
npm run dev &
FRONTEND_PID=$!

echo "Servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
