#!/bin/bash

# SW5 to Shopify API Startup Script

echo "🚀 Starting SW5 to Shopify API..."
echo ""

# Check if .env exists
if [ ! -f "app/.env" ]; then
    echo "⚠️  .env file not found in app/ directory"
    echo "📝 Creating .env from .env.example..."
    cp app/.env.example app/.env
    echo "✅ .env file created. Please edit app/.env with your API credentials."
    echo ""
    echo "Press Enter to continue after you've configured your .env file..."
    read
fi

# Start backend
echo "🐍 Starting Backend (FastAPI)..."
cd app
python3 -m uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Start frontend
echo "⚛️  Starting Frontend (React + Vite)..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Application started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
