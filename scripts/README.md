# Scripts Directory

This directory contains utility scripts for building and running the UCSI Decoder Web Application.

## Files

- **build.bat** - Windows: Build standalone executable using PyInstaller
- **build.sh** - Linux/Mac: Build standalone executable using PyInstaller
- **run.bat** - Windows: Run web server (installs dependencies if needed)
- **run.sh** - Linux/Mac: Run web server (installs dependencies if needed)
- **UcsiControl.exe** - Windows UCSI control utility (required for command execution)

## Quick Start

### Windows

```bash
# Run the web application
.\run.bat

# Or build a standalone executable
.\build.bat
```

### Linux / Mac

```bash
# Make scripts executable (first time only)
chmod +x *.sh

# Run the web application
./run.sh

# Or build a standalone executable
./build.sh
```

## Usage

### Running the Web Application

Both `run.bat` and `run.sh` will:
1. Check for Python installation
2. Install dependencies from `requirements.txt` if needed
3. Start the Flask web server at `http://localhost:5000`

### Building the Executable

Both `build.bat` and `build.sh` will:
1. Clean previous builds
2. Build a standalone executable using PyInstaller
3. Create the executable in the `dist/` folder
4. Display the build status and next steps

## Requirements

- **Python 3.8+** (3.8 recommended for Aardvark I2C adapter compatibility)
- **PyInstaller** (for building executables)
- **Flask** and dependencies (installed via `run.bat/run.sh`)

## Platform Notes

- **Windows**: Use `.bat` scripts directly
- **Linux/Mac**: Make `.sh` scripts executable with `chmod +x *.sh` before running

All scripts automatically detect the project root directory and set working paths correctly.
