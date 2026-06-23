#!/bin/bash
# UCSI Decoder Web Application Launcher for Linux/Mac

# Navigate to project root (parent of scripts folder)
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "========================================"
echo "  UCSI Decoder Web Application"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "Starting UCSI Decoder Web Server..."
echo ""
echo "========================================"
echo "Open your browser and go to:"
echo "  http://localhost:5000"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
