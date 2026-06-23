@echo off
REM UCSI Decoder Web Application Launcher for Windows

REM Navigate to project root (parent of scripts folder)
cd /d "%~dp0.." || exit /b 1

echo ========================================
echo   UCSI Decoder Web Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt 

    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Starting UCSI Decoder Web Server...
echo.
echo ========================================
echo Open your browser and go to:
echo   http://localhost:5000
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
