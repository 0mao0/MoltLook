@echo off
chcp 65001 >nul
echo ===================================================
echo       MoltLook Community Observer - One-Key Start
echo ===================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add to PATH.
    pause
    exit /b
)

REM Check Node/pnpm
call pnpm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pnpm not found. Please install Node.js and pnpm.
    pause
    exit /b
)

echo [1/3] Starting Backend API...
start "MoltLook API" cmd /k "cd backend && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/3] Starting Data Collector...
start "MoltLook Collector" cmd /k "cd backend && (if exist venv\Scripts\activate.bat call venv\Scripts\activate.bat) && python collector.py"

echo [3/3] Starting Frontend Service...
start "MoltLook Frontend" cmd /k "cd frontend && pnpm run serve"

echo.
echo All services started!
echo - Frontend: http://localhost:5173
echo - Backend API: http://localhost:8000/docs
echo.
echo Do not close the popped up terminal windows.
echo.
pause
