# UCSI 3.0 Decoder Web App

**Cross-Platform (Windows & Linux)** — UCSI 3.0 Decoder Web App is a Flask-based workspace for decoding, executing, and reviewing USB Type-C Connector System Software Interface commands and responses. It is built around the UCSI 3.0 command model and supports both manual decode workflows and live platform-backed command execution.

This repository is intended for firmware engineers, validation teams, platform integrators, and anyone debugging UCSI behavior across connector state, role swaps, power data, alternate modes, and PD messaging.

## Highlights

- UCSI 3.0 focused command library with categorized commands and per-port formatting
- Manual response decoding for pasted hex data
- Live command execution from the web UI
- Platform-aware backend support for Windows and Linux
- Optional external I2C adapter workflow for hardware-backed execution
- Decoding for capability, connector, cable, PDO, alternate mode, PD message, attention, error, and power-level responses
- Batch workflows in the UI, including run-all, selected runs, sequential runs, and concurrent runs
- Result history, summary export, and PDF/text save options
- Linux kernel log capture during command execution for debugfs-backed workflows

## What The Application Does

The active application entrypoint is the root-level [app.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app.py). From that server, the web app provides:

- A browsable command catalog grouped into core control, capability/status, USB configuration, power management, alternate modes, PD messages, and advanced operations
- Automatic command formatting for connector-specific requests
- Command execution through Windows via `UcsiControl.exe`
- Command execution through Linux UCSI debugfs command and response files
- Command execution through an optional external adapter integration path
- Response decoding into structured fields instead of raw hex only
- Device and platform checks before execution
- I2C bus scan and address selection endpoints for adapter-backed operation
- A Windows-only vendor-defined command loopback route for stress and echo validation

## Supported Command Families

The command set currently includes these major groups:

- Basic control: reset, cancel, acknowledgment, notification enable
- Capability and status: platform capability, connector capability, cable property, connector status, error status
- USB configuration: connector operation mode, role swaps, USB configuration updates
- Power management: power-direction role swaps, PDO reads, power-level reads, sink path control, PDO programming
- Alternate modes: alternate mode discovery, current mode inspection, CAM operations
- PD messaging: PD message retrieval and attention VDO retrieval
- Advanced operations: firmware update request, security request, retimer mode, chunking support, vendor-defined command handling, LPM/PPM info

## Runtime Model

There are two Python application layouts in the repository:

- [app.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app.py): the working application entrypoint and the one you should run today
- [app/main.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app/main.py): an in-progress package refactor scaffold that is not yet the primary runtime path

If you are using or evaluating the project, run the root application.

## Repository Layout

- [app.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app.py): active Flask server and API routes
- [decoders/ucsi_decoders.py](/c:/lalat/persional/opensource/ucsi-decoder-webapp/decoders/ucsi_decoders.py): command and response decode logic
- [app/templates/index.html](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app/templates/index.html): main UI shell
- [app/static/js/app.js](/c:/lalat/persional/opensource/ucsi-decoder-webapp/app/static/js/app.js): browser-side interaction logic
- [aardvark/](/c:/lalat/persional/opensource/ucsi-decoder-webapp/aardvark): external adapter integration and legacy automation utilities
- [scripts/](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts): helper scripts for running and packaging

## Requirements

### Python

- Python 3.8 or newer is the safest target for this codebase
- `pip` for dependency installation

### Python Packages

Install from [requirements.txt](/c:/lalat/persional/opensource/ucsi-decoder-webapp/requirements.txt):

```bash
pip install -r requirements.txt
```

### Platform Requirements

Windows:
- Python installed and available in `PATH`
- `UcsiControl.exe` available either beside the app or in `PATH`
- A detectable UCSI-capable device if you want live execution instead of manual decode only

Linux:
- Python installed and available in `PATH`
- `sudo` access for debugfs and device permission setup
- Kernel UCSI debugfs support exposed under `/sys/kernel/debug/usb/ucsi` or `/sys/kernel/debug/ucsi`

Optional external adapter mode:
- The bundled adapter integration dependencies available on the host
- Hardware connected and visible to the adapter detection path

## Quick Start

### 1. Clone The Repository

```bash
git clone <your-repo-url>
cd ucsi-decoder-webapp
```

### 2. Create A Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run The Active Application

Windows:

```bash
python app.py
```

Linux:

```bash
python3 app.py
```

The server starts on `http://127.0.0.1:5000` or `http://localhost:5000`.

## Alternate Run Helpers

You can also use the helper scripts in [scripts/](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts):

Windows:

```bash
scripts\run.bat
```

Linux:

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

## Building for Linux

You can package the web application as a standalone executable for Linux using PyInstaller:

### Prerequisites

```bash
pip install -r requirements.txt
```

PyInstaller will be installed if not already present.

### Build Steps

```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

The build process will:
1. Clean any previous builds
2. Compile the application using PyInstaller and [scripts/UCSIDecoder.spec](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts/UCSIDecoder.spec)
3. Create a standalone single-file executable in `dist/UCSIDecoder.exe`

### Running The Executable

After a successful build:

```bash
cd dist
./UCSIDecoder
```

Then open your browser to `http://127.0.0.1:5000`.

The executable bundles Flask, all dependencies, and the web application into a single self-contained binary. It requires Python to be installed on the build machine but can run on other Linux systems with compatible architecture and glibc.

### Troubleshooting

- If the build fails, ensure Python 3.8+ and pip are installed
- Check that the project root contains `app.py` before running the script
- Review build output for any missing dependencies

## How To Use The Web App

### Manual Decode

1. Open the web UI.
2. Select a command from the command library.
3. Paste the raw hex response into the response box.
4. Click `Decode Manual Input`.
5. Review the structured fields in the decoded results pane.

### Live Execution

1. Open the web UI.
2. Select the active connector port.
3. Select a command.
4. Use the generated command hex for the current port.
5. Click `Run Command`.
6. Inspect the decoded response, raw output, and any captured diagnostics.

### Linux Execution Notes

On Linux, the app requests administrator access through the browser and then:

- validates debugfs access
- checks for UCSI device folders
- verifies command and response files
- captures filtered `dmesg` output during command execution

### Windows Execution Notes

On Windows, the app:

- checks for a detectable UCSI device
- formats commands for `UcsiControl.exe`
- extracts response payloads and CCI-related output from the command-line result

### External Adapter Mode

The UI exposes an adapter mode toggle for hardware-backed execution. In that mode the app can:

- detect whether the adapter library is available
- check whether a supported device is connected
- scan the I2C bus
- show discovered addresses
- let you set the active PPM I2C address

## API Surface

The server exposes JSON endpoints used by the UI, including:

- `POST /api/decode`
- `POST /api/execute_command`
- `GET /api/platform-info`
- `GET /api/ucsi-status`
- `GET /api/commands`
- `POST /api/format_command`
- `GET /api/check_device`
- `GET /api/check_aardvark`
- `GET /api/scan_i2c_bus`
- `GET /api/i2c_address_info`
- `POST /api/set_ppm_address`
- `POST /api/vdc_loopback_test`

## Packaging

The repository includes PyInstaller support for packaging:

- [scripts/build.bat](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts/build.bat)
- [scripts/build.sh](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts/build.sh)
- [scripts/UCSIDecoder.spec](/c:/lalat/persional/opensource/ucsi-decoder-webapp/scripts/UCSIDecoder.spec)

Generated output directories such as `build/` and `dist/` should not be treated as source.

## Troubleshooting

- If the web server exits immediately, first verify that port `5000` is free.
- If Linux execution fails, verify debugfs is mounted and that a UCSI device folder exists.
- If Windows execution fails, verify `UcsiControl.exe` is available and the system exposes a UCSI-capable device.
- If adapter mode is unavailable, verify the adapter library and hardware connection before using I2C-backed operations.
- If a command returns no payload, check the decoded result metadata and raw output before assuming the decode failed.

## Open-Source Readiness Notes

This repository already includes an Apache 2.0 license. For public hosting, the important repository-facing files are:

- [README.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/README.md)
- [LICENSE](/c:/lalat/persional/opensource/ucsi-decoder-webapp/LICENSE)
- [CONTRIBUTING.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/CONTRIBUTING.md)
- [SECURITY.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/SECURITY.md)
- [.gitignore](/c:/lalat/persional/opensource/ucsi-decoder-webapp/.gitignore)

Before publishing, it is also worth reviewing generated output folders and excluding any local tools, binaries, logs, or device-specific captures that should not live in source control.

## Specification Alignment

The command catalog and decode workflows in this repository are written around the UCSI 3.0 specification and the associated command-response structure used by platform policy managers and connector managers.

## Contributing And Security

Contribution guidance is in [CONTRIBUTING.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/CONTRIBUTING.md).

Security reporting guidance is in [SECURITY.md](/c:/lalat/persional/opensource/ucsi-decoder-webapp/SECURITY.md).

## License

This project is licensed under the Apache License 2.0. See [LICENSE](/c:/lalat/persional/opensource/ucsi-decoder-webapp/LICENSE).

