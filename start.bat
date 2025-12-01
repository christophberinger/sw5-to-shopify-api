@echo off
echo Starting SW5 to Shopify API...
echo.

REM Check if .env exists
if not exist "app\.env" (
    echo WARNING: .env file not found in app\ directory
    echo Creating .env from .env.example...
    copy app\.env.example app\.env
    echo .env file created. Please edit app\.env with your API credentials.
    echo.
    pause
)

REM Start backend
echo Starting Backend (FastAPI)...
cd app
start "Backend" cmd /k "python -m uvicorn main:app --reload --port 8000"
cd ..

REM Wait for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo Starting Frontend (React + Vite)...
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

start "Frontend" cmd /k "npm run dev"
cd ..

echo.
echo Application started successfully!
echo.
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit (this will NOT stop the servers)
pause > nul
