@echo off
title SocialFlow
echo.
echo  ========================================
echo   SocialFlow - AI Social Media Automation
echo  ========================================
echo.

:: Check for .env
if not exist ".env" (
    echo [*] Creating .env from template...
    copy .env.example .env
    echo.
    echo [!] Please edit .env with your API keys before continuing!
    echo.
    pause
)

:: Create venv if needed
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
)

:: Activate
call venv\Scripts\activate.bat

:: Install dependencies
echo [*] Installing dependencies...
pip install -q -r backend\requirements.txt

:: Install Playwright browsers
echo [*] Checking browser installation...
playwright install chromium

:: Load env vars
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set "%%a=%%b"
)

echo.
echo  ========================================
echo   Server starting...
echo  ========================================
echo.
echo   Dashboard: http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop
echo.

cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
