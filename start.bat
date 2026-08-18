@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Drug Info Q^&A Chatbot - launcher
echo ============================================

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend virtualenv not found.
    echo   Run:  cd backend
    echo         py -3.11 -m venv .venv
    echo         .venv\Scripts\activate
    echo         pip install -r requirements.txt
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed.
    echo   Run:  cd frontend
    echo         npm install
    pause
    exit /b 1
)

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

echo Starting backend on http://localhost:8000 ...
start "Drug Chatbot - Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 2 /nobreak >nul

echo Starting frontend on http://localhost:3000 ...
start "Drug Chatbot - Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev"

echo.
echo Both services starting.
echo   Backend API : http://localhost:8000/docs
echo   Web UI      : http://localhost:3000
echo.
echo Close each window to stop that service.
endlocal
