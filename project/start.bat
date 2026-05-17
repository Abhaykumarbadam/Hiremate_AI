@echo off
echo ======================================
echo   HireMate AI - Startup Script
echo ======================================
echo.

if "%GEMINI_API_KEY%"=="" (
    echo WARNING: GEMINI_API_KEY environment variable is not set!
    echo Please set it before running:
    echo   set GEMINI_API_KEY=your-api-key-here
    echo.
    pause
)

echo Checking for backend.py...
if not exist backend.py (
    echo ERROR: backend.py not found in project root!
    echo Please place backend.py in the same directory as this script.
    pause
    exit /b 1
)

echo backend.py found
echo.

echo Starting Backend Server...
start "HireMate Backend" python backend.py

timeout /t 3 /nobreak > nul

echo.
echo Starting Frontend Dev Server...
start "HireMate Frontend" npm run dev

echo.
echo ======================================
echo   HireMate AI is starting up!
echo ======================================
echo.
echo Backend URL: http://localhost:8000
echo Frontend URL: http://localhost:5173
echo.
echo Two new windows have been opened.
echo Close those windows to stop the servers.
echo.
pause
