@echo off
REM Email Triage Agent Startup Script for Windows

echo Starting Email Triage Agent...

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if OPENAI_API_KEY is set
if "%OPENAI_API_KEY%"=="" (
    echo Warning: OPENAI_API_KEY environment variable is not set.
    echo Please set it before running the application:
    echo set OPENAI_API_KEY=your_api_key_here
    echo.
    echo Or create a .env file with your configuration.
)

REM Start the server
echo Starting FastAPI server...
python main.py

pause
