@echo off
echo ========================================
echo SolarSnap Backend - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
echo.

REM Check if requirements are installed
if not exist "venv\Lib\site-packages\flask\" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Check if database exists
if not exist "solarsnap.db" (
    echo Initializing database...
    python init_db.py
    echo.
)

REM Start server
echo Starting server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop
echo.
python run.py
