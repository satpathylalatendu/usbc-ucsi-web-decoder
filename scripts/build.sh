#!/bin/bash
# Build script for UCSI WebApp - Linux
# Author: Lalatendu Satpathy

# Navigate to project root (parent of scripts folder)
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "============================================"
echo "UCSI WebApp - Linux Build"
echo "============================================"
echo ""
echo "Working directory: $(pwd)"
echo ""
echo "NOTE: This requires Python 3.8+ environment"
echo "Current Python version:"
python3 --version
echo ""

# Check if we're in the correct directory
if [ ! -f "app.py" ]; then
    echo "ERROR: app.py not found. Please run this script from the project root directory."
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
fi

echo "Cleaning previous build..."
rm -rf build dist __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo ""
echo "Building single-file executable..."
echo ""

# Run PyInstaller with explicit working directory
python3 -m PyInstaller scripts/UCSIDecoder.spec --noconfirm

if [ $? -ne 0 ] || [ ! -f "dist/UCSIDecoder" ]; then
    echo ""
    echo "============================================"
    echo "BUILD FAILED!"
    echo "============================================"
    echo "Executable was not created. Check the output above for errors."
    exit 1
fi

echo ""
echo "============================================"
echo "BUILD SUCCESSFUL!"
echo "============================================"
echo ""
echo "Executable location: dist/UCSIDecoder"
echo ""
echo "To run the application:"
echo "  cd dist"
echo "  ./UCSIDecoder"
echo ""
echo "Then open your browser to: http://127.0.0.1:5000"
echo ""
