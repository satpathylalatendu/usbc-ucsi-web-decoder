@echo off
REM Build script for UCSI WebApp - Cross-Platform
REM Author: Lalatendu Satpathy

REM Navigate to project root (parent of scripts folder)
cd /d "%~dp0.." || exit /b 1

echo ============================================
echo UCSI WebApp - Cross-Platform Build
echo ============================================
echo.
echo NOTE: This requires Python 3.8 environment
echo Current Python version:
python --version
echo.

REM Check if we're using Python 3.8
python -c "import sys; exit(0 if sys.version_info[:2] == (3, 8) else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: Python 3.8 is recommended for Aardvark compatibility!
    echo Current Python may not work with Aardvark DLL.
    echo.
    choice /C YN /M "Continue anyway?"
    if errorlevel 2 exit /b 1
)

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo Building single-file executable...
echo.

python -m PyInstaller scripts\UCSIDecoder.spec --noconfirm

REM Check if the executable was actually created (more reliable than exit code)
if not exist "dist\UCSIDecoder.exe" (
    echo.
    echo ============================================
    echo BUILD FAILED!
    echo ============================================
    echo Executable was not created. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo ============================================
echo BUILD SUCCESSFUL!
echo ============================================
echo.
echo Executable location: dist\UCSIDecoder.exe
echo.
echo To run the application:
echo   cd dist
echo   UCSIDecoder.exe
echo.
echo Then open your browser to: http://127.0.0.1:5000
echo.

REM Optional: Clean build folder
echo.
choice /C YN /M "Do you want to clean the build folder (keeps only dist)?"
if errorlevel 2 goto :skip_clean
if errorlevel 1 goto :do_clean

:do_clean
echo Cleaning build folder...
rmdir /s /q build
echo Done!

:skip_clean
echo.
pause
