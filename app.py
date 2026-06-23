"""
Copyright (c) 2026 Lalatendu Satpathy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
UCSI Decoder Web Application
A Flask-based web interface for decoding USB Type-C Connector System Software Interface (UCSI) data.

Author: Lalatendu Satpathy
Version: 3.3
"""

import sys
import os
import platform
import subprocess
import socket
import threading
import time
import tempfile

# Application version - single source of truth
APP_VERSION = "1.0.0"
APP_AUTHOR = "Lalatendu Satpathy"

STARTUP_LOG_PATH = os.path.join(tempfile.gettempdir(), 'ucsi_decoder_startup.log')


def get_app_base_dir():
    """Return the directory that contains bundled app resources."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


class SafeConsoleStream:
    """Fallback stream for windowed EXE mode without a console."""

    def write(self, message):
        try:
            text = '' if message is None else str(message)
            if text:
                with open(STARTUP_LOG_PATH, 'a', encoding='utf-8') as handle:
                    handle.write(text)
            return len(text)
        except Exception:
            return 0

    def flush(self):
        return None

    def isatty(self):
        return False


def ensure_console_streams():
    """Guarantee stdout/stderr exist, even in windowed PyInstaller mode."""
    if sys.stdout is None:
        sys.stdout = SafeConsoleStream()
    if sys.stderr is None:
        sys.stderr = SafeConsoleStream()

    try:
        if hasattr(sys.stdout, 'fileno') and not isinstance(sys.stdout, SafeConsoleStream):
            sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
    except Exception:
        pass


ensure_console_streams()

# Global debug flag - set via environment variable DEBUG=1
DEBUG = os.getenv('DEBUG', '0') == '1'

def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG mode is enabled."""
    if DEBUG:
        print(*args, **kwargs)
        if sys.stdout is not None and hasattr(sys.stdout, 'flush'):
            sys.stdout.flush()


def has_interactive_console():
    """Return True if stdin is interactive; False for windowed EXE mode."""
    try:
        return sys.stdin is not None and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()
    except Exception:
        return False


def pause_before_exit():
    """Pause for user input only when a console is attached."""
    if has_interactive_console():
        try:
            input("Press Enter to exit...")
        except Exception:
            pass

def get_sudo_credentials():
    """Show GUI dialog to get sudo credentials on Linux."""
    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog
        
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front
        
        # Show info message
        messagebox.showinfo(
            "UCSI Decoder - Administrator Access",
            "This application requires administrator privileges for USB device access.\n\n"
            "Please enter your sudo password."
        )
        
        # Get password
        password = simpledialog.askstring(
            "Sudo Password",
            "Enter sudo password:",
            show='*',
            parent=root
        )
        
        root.destroy()
        
        if password is None:
            return None, "User cancelled"
        
        # Verify password by running a simple sudo command
        try:
            result = subprocess.run(
                ['sudo', '-S', 'echo', 'test'],
                input=password.encode(),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return password, None
            else:
                error_msg = result.stderr.decode().strip() or "Invalid password"
                return None, error_msg
        except subprocess.TimeoutExpired:
            return None, "Authentication timeout"
        except Exception as e:
            return None, f"Verification failed: {str(e)}"
            
    except ImportError:
        return None, "tkinter not available"
    except Exception as e:
        return None, f"Dialog error: {str(e)}"

def mount_debugfs(sudo_password):
    """Mount debugfs if not already mounted."""
    debugfs_path = '/sys/kernel/debug'
    
    try:
        # Check if debugfs is already mounted
        result = subprocess.run(
            ['mount'],
            capture_output=True,
            timeout=5
        )
        
        if b'debugfs' in result.stdout and debugfs_path.encode() in result.stdout:
            debug_print(f"[OK] debugfs already mounted at {debugfs_path}")
            return True
        
        # Try to mount debugfs
        debug_print(f"Mounting debugfs at {debugfs_path}...")
        result = subprocess.run(
            ['sudo', '-S', 'mount', '-t', 'debugfs', 'none', debugfs_path],
            input=sudo_password.encode(),
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            debug_print(f"[OK] debugfs mounted successfully")
            return True
        else:
            error_msg = result.stderr.decode().strip()
            debug_print(f"[WARN] Failed to mount debugfs: {error_msg}")
            return False
            
    except Exception as e:
        debug_print(f"[WARN] debugfs mount error: {e}")
        return False

def check_ucsi_folder(sudo_password):
    """Check if UCSI folder exists in /sys/kernel/debug/ and find device.
    
    Supports both old and new UCSI debugfs structures:
    - New: /sys/kernel/debug/usb/ucsi/USBC000:00 (kernel 5.x+)
    - Old: /sys/kernel/debug/ucsi/ppm0 (older kernels)
    """
    # Try new path first (most common)
    ucsi_paths_to_try = [
        '/sys/kernel/debug/usb/ucsi',  # New structure (kernel 5.x+)
        '/sys/kernel/debug/ucsi'        # Old structure (kernel 4.x)
    ]
    
    try:
        # First ensure debugfs is mounted
        if not mount_debugfs(sudo_password):
            return False, "debugfs not mounted"
        
        for ucsi_base_path in ucsi_paths_to_try:
            debug_print(f"Checking for UCSI folder at {ucsi_base_path}...")
            
            # Use sudo to check since debugfs may require elevated permissions
            result = subprocess.run(
                ['sudo', '-S', 'test', '-d', ucsi_base_path],
                input=sudo_password.encode(),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                debug_print(f"[OK] UCSI base folder found at {ucsi_base_path}")
                
                # List contents to find UCSI device (e.g., USBC000:00 or ppm0)
                result = subprocess.run(
                    ['sudo', '-S', 'ls', ucsi_base_path],
                    input=sudo_password.encode(),
                    capture_output=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    contents = result.stdout.decode().strip()
                    debug_print(f"UCSI devices found: {contents}")
                    
                    # Find first UCSI device directory (usually USBC000:00 or ppm0)
                    devices = [d for d in contents.split('\n') if d.strip()]
                    if devices:
                        device_name = devices[0].strip()
                        full_ucsi_path = f"{ucsi_base_path}/{device_name}"
                        
                        # Verify command and response files exist
                        cmd_file = f"{full_ucsi_path}/command"
                        resp_file = f"{full_ucsi_path}/response"
                        
                        cmd_check = subprocess.run(
                            ['sudo', '-S', 'test', '-f', cmd_file],
                            input=sudo_password.encode(),
                            capture_output=True,
                            timeout=5
                        )
                        
                        resp_check = subprocess.run(
                            ['sudo', '-S', 'test', '-f', resp_file],
                            input=sudo_password.encode(),
                            capture_output=True,
                            timeout=5
                        )
                        
                        if cmd_check.returncode == 0 and resp_check.returncode == 0:
                            debug_print(f"[OK] UCSI device ready at {full_ucsi_path}")
                            return True, full_ucsi_path
                        else:
                            debug_print(f"[WARN] Command/response files not found in {full_ucsi_path}")
                            # Try next path if files not found
                            continue
                    else:
                        debug_print(f"[WARN] No UCSI devices found in {ucsi_base_path}")
                        # Try next path
                        continue
                else:
                    debug_print(f"[WARN] Could not list UCSI folder contents")
                    # Try next path
                    continue
            else:
                debug_print(f"[WARN] UCSI folder not found at {ucsi_base_path}")
                # Try next path
                continue
        
        # If we get here, none of the paths worked
        debug_print(f"[WARN] No valid UCSI path found in any location")
        return False, "UCSI folder not found in any expected location"
            
    except Exception as e:
        debug_print(f"[WARN] UCSI folder check error: {e}")
        return False, str(e)

def setup_serial_permissions(sudo_password):
    """Set up serial port permissions for device access using sudo."""
    debug_print("Setting up serial port permissions...")
    
    try:
        import glob
        
        # Find all serial ports
        serial_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        if serial_ports:
            # Add current user to dialout group for serial port access
            import getpass
            current_user = getpass.getuser()
            
            debug_print(f"Adding user '{current_user}' to 'dialout' group...")
            result = subprocess.run(
                ['sudo', '-S', 'usermod', '-a', '-G', 'dialout', current_user],
                input=sudo_password.encode(),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                debug_print(f"[OK] User added to dialout group (may require re-login)")
            
            # Set immediate permissions on existing serial ports
            for port in serial_ports:
                debug_print(f"Setting permissions for {port}...")
                subprocess.run(
                    ['sudo', '-S', 'chmod', '666', port],
                    input=sudo_password.encode(),
                    capture_output=True,
                    timeout=5
                )
            
            debug_print(f"[OK] Serial port permissions configured for {len(serial_ports)} port(s)")
            return True
        else:
            debug_print("[INFO] No serial ports found to configure")
            return True
            
    except Exception as e:
        debug_print(f"[WARN] Serial permission setup error: {e}")
        return False

def setup_linux_permissions(sudo_password):
    """Set up USB and serial permissions for device access using sudo."""
    debug_print("Setting up USB and serial device permissions...")
    
    # Set up serial port permissions first
    setup_serial_permissions(sudo_password)
    
    # Create udev rule for the supported external adapter (VID: 1679)
    udev_rule = 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1679", MODE="0666"\n'
    rule_path = '/etc/udev/rules.d/99-aardvark.rules'
    
    try:
        # Write udev rule
        write_cmd = f'echo \'{udev_rule}\' | sudo -S tee {rule_path}'
        result = subprocess.run(
            ['sudo', '-S', 'tee', rule_path],
            input=(sudo_password + '\n' + udev_rule).encode(),
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            debug_print(f"[OK] Created udev rule: {rule_path}")
            
            # Reload udev rules
            subprocess.run(
                ['sudo', '-S', 'udevadm', 'control', '--reload-rules'],
                input=sudo_password.encode(),
                capture_output=True,
                timeout=5
            )
            
            subprocess.run(
                ['sudo', '-S', 'udevadm', 'trigger'],
                input=sudo_password.encode(),
                capture_output=True,
                timeout=5
            )
            
            debug_print("[OK] USB permissions configured successfully")
            return True
        else:
            debug_print(f"[WARN] Failed to set up permissions: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        debug_print(f"[WARN] Permission setup error: {e}")
        return False

# Global flag to track if system setup has been done
SYSTEM_SETUP_DONE = False
SUDO_PASSWORD = None  # Store sudo password for Linux operations
UCSI_STATUS = {'checked': False, 'found': False, 'location': '', 'error': ''}

# Browser session tracking for windowed EXE mode.
BROWSER_LAST_HEARTBEAT = 0.0
BROWSER_CLOSE_REQUESTED = False
BROWSER_MONITOR_STARTED = False
BROWSER_SHUTDOWN_TIMEOUT_SECONDS = 45


def is_frozen_exe():
    """Return True when running as a packaged executable."""
    return getattr(sys, 'frozen', False)


def browser_session_monitor():
    """Exit EXE when browser is closed or heartbeat stops."""
    global BROWSER_LAST_HEARTBEAT, BROWSER_CLOSE_REQUESTED

    while True:
        time.sleep(2)

        if not is_frozen_exe():
            return

        if BROWSER_LAST_HEARTBEAT <= 0:
            continue

        elapsed = time.time() - BROWSER_LAST_HEARTBEAT

        # Fast shutdown when browser explicitly notifies on close.
        if BROWSER_CLOSE_REQUESTED and elapsed >= 5:
            os._exit(0)

        # Fallback shutdown when browser disappears unexpectedly.
        if elapsed >= BROWSER_SHUTDOWN_TIMEOUT_SECONDS:
            os._exit(0)


def start_browser_monitor_if_needed():
    """Start session monitor thread once in packaged mode."""
    global BROWSER_MONITOR_STARTED

    if not is_frozen_exe() or BROWSER_MONITOR_STARTED:
        return

    thread = threading.Thread(target=browser_session_monitor, daemon=True)
    thread.start()
    BROWSER_MONITOR_STARTED = True

def check_windows_ucsi():
    """Check for UCSI device in Windows Device Manager."""
    try:
        debug_print("[Windows] Checking for UCSI device in Device Manager...")
        
        # Use PowerShell to query device manager via PnP devices
        ps_script = '''
$ucsiDevice = Get-PnpDevice | Where-Object { 
    $_.FriendlyName -like "*UCM-UCSI*" -or 
    $_.FriendlyName -like "*UCSI*" -or
    $_.InstanceId -like "*USBC*"
}

if ($ucsiDevice) {
    $device = $ucsiDevice | Select-Object -First 1
    Write-Output "FOUND:$($device.FriendlyName)"
    Write-Output "STATUS:$($device.Status)"
} else {
    Write-Output "FOUND:False"
}
'''
        
        # Run PowerShell command (hide window on Windows)
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        
        result = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            capture_output=True,
            timeout=10,
            text=True,
            creationflags=creationflags
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            debug_print(f"[DEBUG] PowerShell output: {output}")
            
            # Parse output
            device_name = None
            device_status = None
            
            for line in output.split('\n'):
                line = line.strip()
                if line.startswith('FOUND:'):
                    device_name = line.split(':', 1)[1]
                elif line.startswith('STATUS:'):
                    device_status = line.split(':', 1)[1]
            
            if device_name and device_name != 'False':
                debug_print(f"[OK] UCSI device found: {device_name} (Status: {device_status})")
                return True, device_name
            else:
                debug_print("[WARN] No UCSI device found in Device Manager")
                return False, "No UCSI device found in Device Manager"
        else:
            error_msg = result.stderr.strip() if result.stderr else "PowerShell command failed"
            debug_print(f"[WARN] PowerShell error: {error_msg}")
            return False, error_msg
        
    except subprocess.TimeoutExpired:
        debug_print("[WARN] Device Manager check timeout")
        return False, "Device check timeout"
    except Exception as e:
        debug_print(f"[WARN] Device Manager check error: {e}")
        return False, str(e)

def perform_system_setup():
    """Perform platform-specific system setup and UCSI checks."""
    global SYSTEM_SETUP_DONE, UCSI_STATUS, SUDO_PASSWORD
    
    if SYSTEM_SETUP_DONE:
        return UCSI_STATUS
    
    system = platform.system()
    
    if system == 'Linux':
        # Linux: Wait for web-based sudo authentication
        # Don't show tkinter dialog - use web modal instead
        debug_print("\n[Linux] Waiting for sudo authentication via web interface...")
        
        if SUDO_PASSWORD:
            # If password already provided (via web auth), perform setup
            debug_print("[OK] Credentials already provided, setting up USB permissions...")
            setup_linux_permissions(SUDO_PASSWORD)
            
            # Check for UCSI folder
            debug_print("\n[Linux] Checking for UCSI support in debugfs...")
            ucsi_found, ucsi_info = check_ucsi_folder(SUDO_PASSWORD)
            
            UCSI_STATUS = {
                'checked': True,
                'found': ucsi_found,
                'location': 'debugfs' if ucsi_found else '',
                'error': ucsi_info if not ucsi_found else '',
                'message': f"UCSI is {'enabled' if ucsi_found else 'not found'} in debugfs",
                'internal_path': ucsi_info if ucsi_found else ''  # Store real path internally
            }
            
            if ucsi_found:
                debug_print(f"[OK] UCSI is enabled in debugfs")
            else:
                debug_print(f"[WARN] UCSI is not enabled in debugfs: {ucsi_info}")
        else:
            # No password yet - setup will be done after web authentication
            debug_print("[INFO] Sudo authentication pending - user will be prompted in browser")
            UCSI_STATUS = {
                'checked': False,
                'found': False,
                'location': '',
                'error': 'Sudo authentication required',
                'message': 'Waiting for sudo authentication'
            }
    
    elif system == 'Windows':
        # Windows: Check Device Manager
        debug_print("\n[Windows] Checking for UCSI device in Device Manager...")
        ucsi_found, ucsi_info = check_windows_ucsi()
        
        if ucsi_found:
            UCSI_STATUS = {
                'checked': True,
                'found': True,
                'location': ucsi_info,
                'error': '',
                'message': f"UCSI device found in Device Manager: {ucsi_info}"
            }
            debug_print(f"[OK] UCSI device found: {ucsi_info}")
        else:
            UCSI_STATUS = {
                'checked': True,
                'found': False,
                'location': '',
                'error': ucsi_info,
                'message': "UCSI device not found in Device Manager"
            }
            debug_print(f"[WARN] UCSI device not found: {ucsi_info}")
    
    else:
        UCSI_STATUS = {
            'checked': True,
            'found': False,
            'location': '',
            'error': f"Platform {system} not supported",
            'message': f"UCSI check not available on {system}"
        }
    
    SYSTEM_SETUP_DONE = True
    return UCSI_STATUS

if DEBUG:
    print("=" * 70)
    print("UCSI WebApp Starting...")
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    if hasattr(sys, '_MEIPASS'):
        print(f"PyInstaller temp folder: {sys._MEIPASS}")
    print("=" * 70)
else:
    print(f"UCSI Decoder v{APP_VERSION} - Starting server...")

# Declare module-level variables for integrations
AARDVARK_AVAILABLE = False
AARDVARK_DEVICE_DETECTED = False
aardvark_integration = None


def ensure_aardvark_integration(detect_device=False):
    """Load the optional Aardvark integration only when it is actually needed."""
    global aardvark_integration, AARDVARK_AVAILABLE, AARDVARK_DEVICE_DETECTED

    if aardvark_integration is None:
        try:
            debug_print("Importing Aardvark integration on demand...")
            from aardvark import aardvark_integration as loaded_integration
            aardvark_integration = loaded_integration
            AARDVARK_AVAILABLE = getattr(aardvark_integration, 'AARDVARK_AVAILABLE', False)
            debug_print(f"[OK] Aardvark available: {AARDVARK_AVAILABLE}")
        except ImportError as e:
            debug_print(f"[WARN] Aardvark integration ImportError: {e}")
            aardvark_integration = None
            AARDVARK_AVAILABLE = False
            AARDVARK_DEVICE_DETECTED = False
            return None
        except Exception as e:
            debug_print(f"[WARN] Error loading Aardvark integration: {type(e).__name__}: {e}")
            aardvark_integration = None
            AARDVARK_AVAILABLE = False
            AARDVARK_DEVICE_DETECTED = False
            return None

    if detect_device and aardvark_integration is not None and AARDVARK_AVAILABLE:
        try:
            detection_result = aardvark_integration.detect_aardvark_device()
            AARDVARK_DEVICE_DETECTED = detection_result.get('found', False)
        except Exception:
            AARDVARK_DEVICE_DETECTED = False

    return aardvark_integration


try:
    debug_print("Importing Flask...")
    from flask import Flask, render_template, request, jsonify
    debug_print("[OK] Flask imported")
    
    debug_print("Importing standard libraries...")
    import json
    import struct
    from datetime import datetime
    debug_print("[OK] Standard libraries imported")
    
    debug_print("Importing decoders...")
    from decoders import ucsi_decoders
    debug_print("[OK] Decoders imported")

    debug_print("Creating Flask app...")
    sys.stdout.flush()
    app_base_dir = get_app_base_dir()
    app = Flask(__name__,
                template_folder=os.path.join(app_base_dir, 'app', 'templates'),
                static_folder=os.path.join(app_base_dir, 'app', 'static'))
    app.config['SECRET_KEY'] = 'ucsi-decoder-secret-key-2026'
    debug_print("[OK] Flask app created")
    
    # Suppress Flask/Werkzeug HTTP request logging unless DEBUG mode is enabled
    # Keep startup info and warnings visible
    if not DEBUG:
        import logging
        
        class RequestFilter(logging.Filter):
            """Filter out HTTP request logs but keep startup messages."""
            def filter(self, record):
                # Allow WARNING and ERROR level messages
                if record.levelno >= logging.WARNING:
                    return True
                # Filter out HTTP request logs (they contain HTTP method and status code)
                message = record.getMessage()
                if '" 200 -' in message or '" 304 -' in message or '" 404 -' in message or '" 500 -' in message:
                    return False
                # Allow other INFO messages (like startup messages)
                return True
        
        log = logging.getLogger('werkzeug')
        log.addFilter(RequestFilter())
    
    sys.stdout.flush()

except Exception as e:
    print(f"FATAL ERROR during import: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    pause_before_exit()
    sys.exit(1)

# Application metadata (APP_VERSION and APP_AUTHOR defined at top of file)

# UCSI 3.0 Commands Configuration
COMMANDS = [
    # 1 - PPM_RESET (0x01)
    {"id": 1, "key": "1 - PPM_RESET", "cmd_hex": "00000001", "category": "Basic Control"},
    
    # 2 - CANCEL (0x02)
    {"id": 2, "key": "2 - CANCEL", "cmd_hex": "00000002", "category": "Basic Control"},
    
    # 3 - CONNECTOR_RESET (0x03)
    {"id": 3, "key": "3 - CONNECTOR_RESET", "cmd_hex": "00010003", "category": "Basic Control"},
    
    # 4 - ACK_CC_CI (0x04)
    # Format per Table 6-7: Bit 16=Connector Change Ack, Bit 17=Command Completed Ack
    # Setting both: byte2=0x03 (bits 16-17 set)
    {"id": 4, "key": "4 - ACK_CC_CI", "cmd_hex": "00030004", "category": "Basic Control"},
    
    # 5 - SET_NOTIFICATION_ENABLE (0x05)
    {"id": 5, "key": "5 - SET_NOTIFICATION_ENABLE", "cmd_hex": "0000000000010005", "category": "Basic Control"},
    
    # 6 - GET_CAPABILITY (0x06)
    {"id": 6, "key": "6 - GET_CAPABILITY", "cmd_hex": "00000006", "category": "Capability & Status"},
    
    # 7 - GET_CONNECTOR_CAPABILITY (0x07)
    {"id": 7, "key": "7 - GET_CONNECTOR_CAPABILITY", "cmd_hex": "010007", "category": "Capability & Status"},
    
    # 8 - SET_UOM (0x08) - USB Operation Mode
    {"id": 8, "key": "8 - SET_CCOM (DFP)", "cmd_hex": "810008", "category": "USB Configuration"},
    {"id": 9, "key": "8 - SET_CCOM (UFP)", "cmd_hex": "1010008", "category": "USB Configuration"},
    {"id": 10, "key": "8 - SET_CCOM (DRP)", "cmd_hex": "2010008", "category": "USB Configuration"},
    
    # 9 - SET_UOR (0x09) - USB Operation Role
    # Format: byte2 = connector | (bit0 << 7), byte3 = (bit1 | bit2 << 1)
    {"id": 11, "key": "9 - SET_UOR (Swap to DFP)", "cmd_hex": "810009", "category": "USB Configuration"},  # bit 0 set
    {"id": 12, "key": "9 - SET_UOR (Swap to UFP)", "cmd_hex": "1010009", "category": "USB Configuration"},  # bit 1 set
    {"id": 13, "key": "9 - SET_UOR (Accept Swap)", "cmd_hex": "2010009", "category": "USB Configuration"},  # bit 2 set

    # 10 - SET_PDR (0x0B) - Set Power Direction Role
    # Format: byte2 = connector | (bit0 << 7), byte3 = (bit1 | bit2 << 1)
    {"id": 14, "key": "B - SET_PDR (Swap to Provider)", "cmd_hex": "81000B", "category": "Power Management"},  # bit 0 set (Source)
    {"id": 15, "key": "B - SET_PDR (Swap to Consumer)", "cmd_hex": "101000B", "category": "Power Management"},  # bit 1 set (Sink)
    {"id": 16, "key": "B - SET_PDR (Accept Swap)", "cmd_hex": "201000B", "category": "Power Management"},  # bit 2 set
    # 11 - GET_ALTERNATE_MODES (0x0C)
    {"id": 17, "key": "C - GET_ALTERNATE_MODES", "cmd_hex": "01000C", "category": "Alternate Modes"},
    
    # 12 - GET_CAM_SUPPORTED (0x0D)
    {"id": 18, "key": "D - GET_CAM_SUPPORTED", "cmd_hex": "10030D", "category": "Alternate Modes"},
    
    # 13 - GET_CURRENT_CAM (0x0E)
    {"id": 19, "key": "E - GET_CURRENT_CAM", "cmd_hex": "01000E", "category": "Alternate Modes"},
    
    # 14 - SET_NEW_CAM (0x0F)
    {"id": 20, "key": "F - SET_NEW_CAM", "cmd_hex": "01000F", "category": "Alternate Modes"},
    
    # 15 - GET_PDOS (0x10)
    {"id": 21, "key": "10 - GET_PDOS (Local Source)", "cmd_hex": "010710", "category": "Power Management"},
    {"id": 22, "key": "10 - GET_PDOS (Local Sink)", "cmd_hex": "010310", "category": "Power Management"},
    {"id": 23, "key": "10 - GET_PDOS (Partner Source)", "cmd_hex": "010710", "category": "Power Management"},
    {"id": 24, "key": "10 - GET_PDOS (Partner Sink)", "cmd_hex": "010310", "category": "Power Management"},
    
    # 16 - GET_CABLE_PROPERTY (0x11)
    {"id": 25, "key": "11 - GET_CABLE_PROPERTY", "cmd_hex": "010011", "category": "Capability & Status"},
    
    # 17 - GET_CONNECTOR_STATUS (0x12)
    {"id": 26, "key": "12 - GET_CONNECTOR_STATUS", "cmd_hex": "010012", "category": "Capability & Status"},
    
    # 18 - GET_ERROR_STATUS (0x13)
    {"id": 27, "key": "13 - GET_ERROR_STATUS", "cmd_hex": "00000013", "category": "Capability & Status"},
    
    # 19 - SET_POWER_LEVEL (0x14)
    {"id": 28, "key": "14 - SET_POWER_LEVEL (Source)", "cmd_hex": "03810014", "category": "Power Management"},
    {"id": 29, "key": "14 - SET_POWER_LEVEL (Sink)", "cmd_hex": "03010014", "category": "Power Management"},
    
    # 20 - GET_PD_MESSAGE (0x15)
    {"id": 30, "key": "15 - GET_PD_MESSAGE", "cmd_hex": "010015", "category": "PD Messages"},
    
    # 21 - GET_ATTENTION_VDO (0x16)
    {"id": 31, "key": "16 - GET_ATTENTION_VDO", "cmd_hex": "010016", "category": "PD Messages"},
    
    # 22 - GET_CAM_CS (0x18)
    {"id": 32, "key": "18 - GET_CAM_CS", "cmd_hex": "010018", "category": "Alternate Modes"},

    # 23 - LPM_FW_UPDATE_REQUEST (0x19)
    {"id": 33, "key": "19 - LPM_FW_UPDATE_REQUEST", "cmd_hex": "010019", "category": "Advanced Features"},
    
    # 24 - SECURITY_REQUEST (0x1A)
    {"id": 34, "key": "1A - SECURITY_REQUEST", "cmd_hex": "01001A", "category": "Advanced Features"},
    
    # 25 - SET_RETIMER_MODE (0x1B)
    {"id": 35, "key": "1B - SET_RETIMER_MODE", "cmd_hex": "01001B", "category": "Advanced Features"},
    
    # 26 - SET_SINK_PATH (0x1C)
    {"id": 36, "key": "1C - SET_SINK_PATH (Disable)", "cmd_hex": "0000001C", "category": "Power Management"},
    {"id": 37, "key": "1C - SET_SINK_PATH (Enable)", "cmd_hex": "0001001C", "category": "Power Management"},
    
    # 27 - SET_PDO (0x1D)
    {"id": 40, "key": "1D - SET_PDO (Source)", "cmd_hex": "1401081D", "category": "Power Management"},
    {"id": 41, "key": "1D - SET_PDO (Sink)", "cmd_hex": "1001081D", "category": "Power Management"},
    
    # 28 - READ_POWER_LEVEL (0x1E)
    # Format: Connector 1, Time to Read = 1 (200ms), Time Interval = 1 (10ms)
    {"id": 45, "key": "1E - READ_POWER_LEVEL", "cmd_hex": "8081001E", "category": "Power Management"},

    # 29 - CHUNKING_SUPPORT (0x1F)
    {"id": 38, "key": "1F - CHUNKING_SUPPORT (Enable)", "cmd_hex": "0001001F", "category": "Advanced Features"},
    {"id": 39, "key": "1F - CHUNKING_SUPPORT (Disable)", "cmd_hex": "0000001F", "category": "Advanced Features"},

    # 29 - VENDOR_DEFINED (0x20)
    {"id": 42, "key": "20 - VENDOR_DEFINED", "cmd_hex": "010020", "category": "Advanced Features"},

    # 31 - SET_USB (0x21) - Default to Enable USB4 for connector 1
    {"id": 44, "key": "21 - SET_USB", "cmd_hex": "0000000001012100", "category": "USB Configuration"},

    # 30 - GET_LPM_PPM_INFO (0x22) - Connector 0 queries PPM/LPM info (not a specific connector)
    {"id": 43, "key": "22 - GET_LPM_PPM_INFO", "cmd_hex": "00000022", "category": "Advanced Features"},
]

# Command categories
COMMAND_CATEGORIES = {
    "Basic Control": [
        "1 - PPM_RESET",
        "2 - CANCEL",
        "3 - CONNECTOR_RESET",
        "4 - ACK_CC_CI",
        "5 - SET_NOTIFICATION_ENABLE"
    ],
    "Capability & Status": [
        "6 - GET_CAPABILITY",
        "7 - GET_CONNECTOR_CAPABILITY",
        "11 - GET_CABLE_PROPERTY",
        "12 - GET_CONNECTOR_STATUS",
        "13 - GET_ERROR_STATUS"
    ],
    "USB Configuration": [
        "8 - SET_CCOM (DFP)",
        "8 - SET_CCOM (UFP)",
        "8 - SET_CCOM (DRP)",
        "9 - SET_UOR (Swap to DFP)",
        "9 - SET_UOR (Swap to UFP)",
        "9 - SET_UOR (Accept Swap)",
        "21 - SET_USB"
    ],
    "Power Management": [
        "B - SET_PDR (Swap to Provider)",
        "B - SET_PDR (Swap to Consumer)",
        "B - SET_PDR (Accept Swap)",
        "10 - GET_PDOS (Local Source)",
        "10 - GET_PDOS (Local Sink)",
        "10 - GET_PDOS (Partner Source)",
        "10 - GET_PDOS (Partner Sink)",
        "14 - SET_POWER_LEVEL (Source)",
        "14 - SET_POWER_LEVEL (Sink)",
        "1C - SET_SINK_PATH (Disable)",
        "1C - SET_SINK_PATH (Enable)",
        "1D - SET_PDO (Source)",
        "1D - SET_PDO (Sink)",
        "1E - READ_POWER_LEVEL"
    ],
    "Alternate Modes": [
        "C - GET_ALTERNATE_MODES",
        "D - GET_CAM_SUPPORTED",
        "E - GET_CURRENT_CAM",
        "F - SET_NEW_CAM",
        "18 - GET_CAM_CS"
    ],
    "PD Messages": [
        "15 - GET_PD_MESSAGE",
        "16 - GET_ATTENTION_VDO"
    ],
    "Advanced Features": [
        "19 - LPM_FW_UPDATE_REQUEST",
        "1A - SECURITY_REQUEST",
        "1B - SET_RETIMER_MODE",
        "1F - CHUNKING_SUPPORT (Enable)",
        "1F - CHUNKING_SUPPORT (Disable)",
        "20 - VENDOR_DEFINED",
        "22 - GET_LPM_PPM_INFO"
    ]
}

def format_hex_response(hex_string):
    """Format hex string with spaces and line breaks (8 bytes per line)."""
    # Remove any existing spaces and formatting
    clean_hex = ''.join(hex_string.split())
    
    # Insert space after every 2 characters (1 byte)
    spaced = ' '.join(clean_hex[i:i+2] for i in range(0, len(clean_hex), 2))
    
    # Split into lines of 8 bytes (24 chars + 7 spaces)
    bytes_list = spaced.split(' ')
    lines = []
    for i in range(0, len(bytes_list), 8):
        lines.append(' '.join(bytes_list[i:i+8]))
    
    return '\n'.join(lines)

@app.route('/')
def index():
    """Render main page."""
    # Perform system setup on first access
    global SYSTEM_SETUP_DONE
    if not SYSTEM_SETUP_DONE:
        debug_print("\n[INFO] First browser access detected - performing system setup...")
        perform_system_setup()
        
        # Show UCSI status dialog on Linux
        if platform.system() == 'Linux' and UCSI_STATUS['checked']:
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                
                if UCSI_STATUS['found']:
                    messagebox.showinfo(
                        "UCSI Decoder - System Check",
                        f"UCSI Support: FOUND\n\n"
                        f"Location: {UCSI_STATUS['location']}\n\n"
                        f"Your system has UCSI (USB Type-C Connector System Software Interface) support.\n\n"
                        f"UCSI is enabled in debugfs.\n\n"
                        f"You can use the UCSI decoder features in this application."
                    )
                else:
                    messagebox.showwarning(
                        "UCSI Decoder - System Check",
                        f"UCSI Support: NOT FOUND\n\n"
                        f"Reason: {UCSI_STATUS['error']}\n\n"
                        f"Your system may not have UCSI support, or the UCSI driver is not loaded.\n\n"
                        f"To check manually, run:\n"
                        f"  sudo mount -t debugfs none /sys/kernel/debug\n"
                        f"  sudo ls -la /sys/kernel/debug/usb/ucsi"
                    )
                
                root.destroy()
            except Exception as e:
                debug_print(f"[WARN] Could not show UCSI status dialog: {e}")
    
    # Determine UCSI path if available (platform-specific)
    ucsi_path = ''
    if UCSI_STATUS.get('location'):
        ucsi_path = UCSI_STATUS['location']
    
    # Add timestamp for cache busting (used for JS/CSS files only)
    import time
    cache_bust = str(int(time.time()))
    
    return render_template('index.html', 
                         commands=COMMANDS,
                         categories=COMMAND_CATEGORIES,
                         version=APP_VERSION,  # Display version without timestamp
                         cache_version=cache_bust,  # Separate cache busting variable
                         author=APP_AUTHOR,
                         ucsi_status=UCSI_STATUS,
                         platform=platform.system(),
                         ucsi_path=ucsi_path)

@app.route('/api/decode', methods=['POST'])
def decode():
    """Decode UCSI command response."""
    try:
        data = request.get_json()
        hex_response = data.get('hex_response', '').strip()
        command_key = data.get('command_key', '')
        ucsi_version = data.get('ucsi_version', '3.0')
        port = data.get('port', 1)
        
        if not hex_response:
            return jsonify({'error': 'No hex response provided'}), 400
        
        # Decode the hex string
        resp_bytes = ucsi_decoders.decode_hex_string(hex_response)
        
        if resp_bytes is None:
            return jsonify({'error': 'Invalid hex string format'}), 400
        
        # Get the decoder function for this command
        decoder_func = ucsi_decoders.get_decoder(command_key)
        
        if decoder_func:
            decoded_data = decoder_func(resp_bytes, ucsi_version)
        else:
            # Generic decode if no specific decoder
            decoded_data = ucsi_decoders.decode_generic(resp_bytes, ucsi_version)
        
        # Add metadata
        decoded_data['command'] = command_key
        decoded_data['timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'decoded': decoded_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/platform-info', methods=['GET'])
def get_platform_info():
    """Get platform-specific information for command display."""
    current_platform = platform.system()
    ucsi_path = ''
    
    if current_platform == 'Linux':
        # Don't expose internal kernel paths to UI
        ucsi_path = 'debugfs' if UCSI_STATUS.get('found') else ''
    elif current_platform == 'Windows':
        # Windows doesn't use file paths for UCSI access
        if UCSI_STATUS.get('location'):
            ucsi_path = UCSI_STATUS['location']  # Device name from Device Manager
    
    return jsonify({
        'success': True,
        'platform': current_platform,
        'ucsi_path': ucsi_path,
        'is_linux': current_platform == 'Linux',
        'is_windows': current_platform == 'Windows',
        'needs_sudo_auth': current_platform == 'Linux' and not SUDO_PASSWORD,
        'aardvark_available': AARDVARK_AVAILABLE,
        'aardvark_detected': AARDVARK_DEVICE_DETECTED
    })


@app.route('/api/browser-heartbeat', methods=['POST'])
def browser_heartbeat():
    """Keep-alive signal from browser so EXE can exit after browser closes."""
    global BROWSER_LAST_HEARTBEAT, BROWSER_CLOSE_REQUESTED

    BROWSER_LAST_HEARTBEAT = time.time()
    BROWSER_CLOSE_REQUESTED = False
    return jsonify({'success': True})


@app.route('/api/browser-close', methods=['POST'])
def browser_close():
    """Signal that browser window/tab is closing."""
    global BROWSER_CLOSE_REQUESTED

    BROWSER_CLOSE_REQUESTED = True
    return jsonify({'success': True})

@app.route('/api/sudo-auth', methods=['POST'])
def sudo_authenticate():
    """Authenticate sudo password via web dialog."""
    global SUDO_PASSWORD, UCSI_STATUS
    
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Verify password by running a simple sudo command
        try:
            result = subprocess.run(
                ['sudo', '-S', 'echo', 'test'],
                input=password.encode(),
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Store password globally
                SUDO_PASSWORD = password
                
                # Perform Linux setup now that we have credentials
                setup_linux_permissions(password)
                
                # Check for UCSI folder
                ucsi_found, ucsi_info = check_ucsi_folder(password)
                
                UCSI_STATUS = {
                    'checked': True,
                    'found': ucsi_found,
                    'location': 'debugfs' if ucsi_found else '',
                    'error': ucsi_info if not ucsi_found else '',
                    'message': f"UCSI is {'enabled' if ucsi_found else 'not found'} in debugfs",
                    'internal_path': ucsi_info if ucsi_found else ''  # Store real path internally
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Authentication successful',
                    'ucsi_status': UCSI_STATUS
                })
            else:
                error_msg = result.stderr.decode().strip() or "Invalid password"
                return jsonify({'success': False, 'error': error_msg}), 401
                
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Authentication timeout'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'Verification failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ucsi-status', methods=['GET'])
def get_ucsi_status():
    """Get UCSI system status."""
    global SYSTEM_SETUP_DONE
    if not SYSTEM_SETUP_DONE:
        perform_system_setup()
    
    return jsonify({
        'success': True,
        'ucsi_status': UCSI_STATUS,
        'platform': platform.system()
    })

@app.route('/api/commands', methods=['GET'])
def get_commands():
    """Get list of all UCSI commands."""
    return jsonify({
        'success': True,
        'commands': COMMANDS,
        'categories': COMMAND_CATEGORIES
    })

@app.route('/api/command/<int:cmd_id>', methods=['GET'])
def get_command(cmd_id):
    """Get specific command details."""
    cmd = next((c for c in COMMANDS if c['id'] == cmd_id), None)
    if cmd:
        return jsonify({'success': True, 'command': cmd})
    else:
        return jsonify({'error': 'Command not found'}), 404

@app.route('/api/format_command', methods=['POST'])
def format_command():
    """Format command hex with port number - platform aware."""
    try:
        data = request.get_json()
        command_key = data.get('command_key', '')
        port = data.get('port', 1)
        aardvark_mode = data.get('aardvark_mode', False)
        
        cmd = next((c for c in COMMANDS if c['key'] == command_key), None)
        if not cmd:
            return jsonify({'error': 'Command not found'}), 404
        
        cmd_hex = cmd['cmd_hex']
        formatted_hex = update_port_in_hex(cmd_hex, port)
        
        # Determine Linux UCSI path
        linux_ucsi_path = ''
        if platform.system() == 'Linux':
            # Use internal_path for actual operations (don't expose to user)
            if UCSI_STATUS.get('internal_path'):
                linux_ucsi_path = UCSI_STATUS['internal_path']
            else:
                linux_ucsi_path = '/sys/kernel/debug/usb/ucsi/USBC000:00'
        
        # Platform and mode specific command format
        aardvark_module = ensure_aardvark_integration() if aardvark_mode else None
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            # Aardvark mode - show the hex command
            try:
                aardvark_hex = aardvark_module.get_aardvark_command_hex(command_key, port)
                full_command = aardvark_hex
            except Exception:
                full_command = f'{command_key}'
        elif platform.system() == 'Linux':
            # Linux sysfs mode - just show the hex value
            full_command = f'0x{formatted_hex}'
        else:
            # Windows UcsiControl.exe mode
            if len(formatted_hex) == 16:
                high_dw = formatted_hex[0:8]
                low_dw = formatted_hex[8:16]
                full_command = f'UcsiControl.exe send {high_dw} {low_dw}'
            else:
                full_command = f'UcsiControl.exe send 0 {formatted_hex}'
        
        return jsonify({
            'success': True,
            'ucsi_command': formatted_hex,
            'full_command': full_command,
            'aardvark_mode': aardvark_mode,
            'platform': platform.system(),
            'linux_read_command': 'cat response' if platform.system() == 'Linux' else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def capture_linux_dmesg_logs():
    """Capture UCSI-related dmesg logs on Linux."""
    if platform.system() != 'Linux' or not SUDO_PASSWORD:
        return None
    
    try:
        sudo_password_str = SUDO_PASSWORD if isinstance(SUDO_PASSWORD, str) else SUDO_PASSWORD.decode()
        debug_print(f"[Linux] Capturing dmesg logs for UCSI...")
        dmesg_result = subprocess.run(
            ['sudo', '-S', 'dmesg', '--color=never'],
            input=sudo_password_str,
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if dmesg_result.returncode == 0:
            # Filter for UCSI-related messages and get last 30 lines
            all_lines = dmesg_result.stdout.strip().split('\n')
            ucsi_lines = [line for line in all_lines if 'ucsi' in line.lower() or 'typec' in line.lower()]
            dmesg_logs = '\n'.join(ucsi_lines[-30:]) if ucsi_lines else "No UCSI-related dmesg logs found"
            debug_print(f"[Linux] Captured {len(ucsi_lines)} UCSI-related dmesg lines")
            return dmesg_logs
        else:
            debug_print(f"[Linux] dmesg capture failed: {dmesg_result.stderr}")
            return "Failed to capture dmesg logs"
    except Exception as e:
        debug_print(f"[Linux] dmesg capture exception: {e}")
        return f"Error capturing dmesg: {str(e)}"

def handle_set_power_level_workflow(aardvark_mode, port, power_level_hex, ucsi_version):
    """
    Handle SET_POWER_LEVEL command with automatic before/after comparison.
    
    This function automatically:
    1. Reads GET_CONNECTOR_STATUS (before)
    2. Executes SET_POWER_LEVEL command
    3. Reads GET_CONNECTOR_STATUS (after)
    4. Compares and highlights differences
    
    Args:
        aardvark_mode: Whether using Aardvark I2C mode
        port: UCSI port number
        power_level_hex: The SET_POWER_LEVEL command hex
        ucsi_version: UCSI specification version
        
    Returns:
        Flask JSON response with workflow results and comparison
    """
    workflow_log = []
    workflow_log.append("=== SET_POWER_LEVEL Automatic Workflow ===")
    workflow_log.append("Step 1: Reading GET_CONNECTOR_STATUS (before)...")
    aardvark_module = ensure_aardvark_integration() if aardvark_mode else None
    
    try:
        # Step 1: Get connector status BEFORE
        # Build GET_CONNECTOR_STATUS command hex
        # Format: port number (1 byte) + 0x00 (data length) + 0x12 (command)
        connector_status_hex = f"{port:02X}0012"
        
        status_before = None
        status_before_raw = None
        
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            result = aardvark_module.execute_command_by_name("12 - GET_CONNECTOR_STATUS", port)
            if result.get('ok'):
                status_before = result.get('decoded', {})
                status_before_raw = result.get('hex_response', '')
                workflow_log.append(f"Step 1 SUCCESS: Connector status captured (before)")
            else:
                workflow_log.append(f"Step 1 WARNING: Could not read status before: {result.get('error', 'Unknown')}")
                
        elif platform.system() == 'Windows':
            ucsi_path = get_ucsi_executable()
            if ucsi_path:
                args = ['send', '0', connector_status_hex]
                result = run_ucsi_control(ucsi_path, args)
                if result.get('ok'):
                    hex_resp = result.get('hex_response', '')
                    status_before_raw = hex_resp
                    # Decode the response
                    resp_bytes = bytes.fromhex(hex_resp) if hex_resp else b''
                    status_before = ucsi_decoders.decode_connector_status(resp_bytes, ucsi_version)
                    workflow_log.append(f"Step 1 SUCCESS: Connector status captured (before)")
                else:
                    workflow_log.append(f"Step 1 WARNING: Could not read status before")
        
        # Step 2: Execute SET_POWER_LEVEL
        workflow_log.append("Step 2: Executing SET_POWER_LEVEL command...")
        
        power_result = None
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            result = aardvark_module.send_command(power_level_hex, port)
            if result.get('ok'):
                workflow_log.append(f"Step 2 SUCCESS: SET_POWER_LEVEL executed")
                power_result = result
            else:
                workflow_log.append(f"Step 2 FAILED: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'error': 'SET_POWER_LEVEL workflow failed at Step 2',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': result.get('error', 'Command execution failed')
                }), 400
                
        elif platform.system() == 'Windows':
            ucsi_path = get_ucsi_executable()
            if not ucsi_path:
                return jsonify({'error': 'UcsiControl.exe not found'}), 400
            
            args = ['send', '0', power_level_hex]
            result = run_ucsi_control(ucsi_path, args)
            if result.get('ok'):
                workflow_log.append(f"Step 2 SUCCESS: SET_POWER_LEVEL executed")
                power_result = result
            else:
                workflow_log.append(f"Step 2 FAILED: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'error': 'SET_POWER_LEVEL workflow failed at Step 2',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': result.get('error', 'Command execution failed')
                }), 400
        
        # Small delay to allow status to update
        import time
        time.sleep(0.2)
        
        # Step 3: Get connector status AFTER
        workflow_log.append("Step 3: Reading GET_CONNECTOR_STATUS (after)...")
        
        status_after = None
        status_after_raw = None
        
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            result = aardvark_module.execute_command_by_name("12 - GET_CONNECTOR_STATUS", port)
            if result.get('ok'):
                status_after = result.get('decoded', {})
                status_after_raw = result.get('hex_response', '')
                workflow_log.append(f"Step 3 SUCCESS: Connector status captured (after)")
            else:
                workflow_log.append(f"Step 3 WARNING: Could not read status after")
                
        elif platform.system() == 'Windows':
            if ucsi_path:
                args = ['send', '0', connector_status_hex]
                result = run_ucsi_control(ucsi_path, args)
                if result.get('ok'):
                    hex_resp = result.get('hex_response', '')
                    status_after_raw = hex_resp
                    resp_bytes = bytes.fromhex(hex_resp) if hex_resp else b''
                    status_after = ucsi_decoders.decode_connector_status(resp_bytes, ucsi_version)
                    workflow_log.append(f"Step 3 SUCCESS: Connector status captured (after)")
                else:
                    workflow_log.append(f"Step 3 WARNING: Could not read status after")
        
        # Step 4: Compare and identify changes
        workflow_log.append("Step 4: Comparing before/after status...")
        
        changes = {}
        if status_before and status_after:
            # Compare all fields
            all_keys = set(list(status_before.keys()) + list(status_after.keys()))
            for key in all_keys:
                if key in ['command', 'timestamp', 'raw_len', 'raw_hex']:
                    continue  # Skip metadata
                
                val_before = status_before.get(key)
                val_after = status_after.get(key)
                
                if val_before != val_after:
                    changes[key] = {
                        'before': val_before,
                        'after': val_after,
                        'changed': True
                    }
                    workflow_log.append(f"  CHANGED: {key}")
                    workflow_log.append(f"    Before: {val_before}")
                    workflow_log.append(f"    After:  {val_after}")
        
        if changes:
            workflow_log.append(f"Step 4 COMPLETE: Found {len(changes)} changed field(s)")
        else:
            workflow_log.append("Step 4 COMPLETE: No changes detected")
        
        workflow_log.append("=== SET_POWER_LEVEL Workflow COMPLETED ===")
        
        # Determine command type (Source or Sink) from the hex command
        # Byte 2 has the type flag: 0x81 = Source, 0x01 = Sink
        command_type = "14 - SET_POWER_LEVEL"
        try:
            # Convert hex string to bytes to check the flag
            hex_bytes = bytes.fromhex(power_level_hex)
            if len(hex_bytes) >= 3:
                type_flag = hex_bytes[2]  # Byte 2 in little-endian
                if type_flag == 0x81:
                    command_type = "14 - SET_POWER_LEVEL (Source)"
                elif type_flag == 0x01:
                    command_type = "14 - SET_POWER_LEVEL (Sink)"
        except:
            pass  # Use default if parsing fails
        
        # Get proper decoded information from decoder
        decoded_result = ucsi_decoders.get_decoder(command_type)
        if decoded_result:
            # Call the decoder with empty bytes (SET commands return empty response)
            decoded_result = decoded_result(b'', ucsi_version)
        else:
            # Fallback if decoder not found
            decoded_result = ucsi_decoders.decode_generic(b'', ucsi_version)
        
        # Add workflow-specific data to the decoded result
        decoded_result['command'] = command_type
        decoded_result['timestamp'] = datetime.now().isoformat()
        decoded_result['workflow_comparison'] = {
            'changes_detected': len(changes) > 0,
            'changed_fields': list(changes.keys()),
            'details': changes
        }
        decoded_result['connector_status_before'] = status_before
        decoded_result['connector_status_after'] = status_after
        
        return jsonify({
            'success': True,
            'hex_response': power_result.get('hex_response', '') if power_result else 'Command executed',
            'decoded': decoded_result,
            'workflow_log': '\n'.join(workflow_log),
            'raw_output': power_result.get('stdout', '') if power_result else ''
        })
        
    except Exception as e:
        workflow_log.append(f"EXCEPTION: {str(e)}")
        import traceback
        workflow_log.append(traceback.format_exc())
        
        return jsonify({
            'error': f'SET_POWER_LEVEL workflow failed: {str(e)}',
            'workflow_log': '\n'.join(workflow_log)
        }), 500

def handle_ack_cc_ci_workflow(aardvark_mode, port, ack_command_hex, ucsi_version):
    """
    Handle ACK_CC_CI command with automatic prerequisite workflow.
    
    ACK_CC_CI requires a pending notification (Command Completed or Connector Change).
    This function automatically:
    1. Sends a test command (GET_CAPABILITY) to generate a completion notification
    2. Reads and verifies the CCI register has pending indicators
    3. Executes the ACK_CC_CI command
    4. Reports success or failure
    
    Args:
        aardvark_mode: Whether using Aardvark I2C mode
        port: UCSI port number
        ack_command_hex: The ACK_CC_CI command hex
        ucsi_version: UCSI specification version
        
    Returns:
        Flask JSON response with workflow results
    """
    workflow_log = []
    workflow_log.append("=== ACK_CC_CI Automatic Workflow ===")
    workflow_log.append("Step 1: Sending test command (GET_CAPABILITY) to generate completion notification...")
    aardvark_module = ensure_aardvark_integration() if aardvark_mode else None
    
    try:
        # Step 1: Send GET_CAPABILITY command to generate a completion notification
        # GET_CAPABILITY is command 0x06 with no parameters
        test_command_hex = "00000006"  # GET_CAPABILITY (correct 8-character format)
        
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            # Use Aardvark
            result = aardvark_module.execute_command_by_name("6 - GET_CAPABILITY", port)
            if not result.get('ok'):
                workflow_log.append(f"Step 1 FAILED: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'error': 'ACK_CC_CI workflow failed at Step 1 (test command)',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': result.get('error', 'Test command execution failed')
                }), 400
            workflow_log.append(f"Step 1 SUCCESS: Test command completed")
            
        elif platform.system() == 'Windows':
            # Use Windows UcsiControl.exe
            ucsi_path = get_ucsi_executable()
            if not ucsi_path:
                workflow_log.append("Step 1 FAILED: UcsiControl.exe not found")
                return jsonify({
                    'error': 'ACK_CC_CI workflow failed - UcsiControl.exe not found',
                    'workflow_log': '\n'.join(workflow_log)
                }), 400
            
            args = ['send', '0', test_command_hex]
            result = run_ucsi_control(ucsi_path, args)
            if not result.get('ok'):
                workflow_log.append(f"Step 1 FAILED: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'error': 'ACK_CC_CI workflow failed at Step 1 (test command)',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': result.get('error', 'Test command execution failed')
                }), 400
            workflow_log.append(f"Step 1 SUCCESS: Test command completed")
            
        else:
            # Linux - not fully implemented for ACK workflow
            workflow_log.append("Step 1 SKIPPED: Linux ACK_CC_CI workflow not yet implemented")
            workflow_log.append("Note: For Linux, please manually check CCI before ACK_CC_CI")
        
        # Step 2: Read CCI register to verify pending notification
        workflow_log.append("Step 2: Reading CCI register to verify notification pending...")
        
        cci_value = None
        command_completed = False
        connector_change = False
        
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            # Read CCI via Aardvark
            cci_result = aardvark_module.read_cci_register(port)
            if cci_result.get('ok'):
                cci_value = cci_result.get('cci_value')
                workflow_log.append(f"Step 2 SUCCESS: CCI = 0x{cci_value:08X}")
                
                # Check bit 31 (Command Completed) and bits 1-7 (Connector Change Indicator)
                command_completed = (cci_value & 0x80000000) != 0
                connector_change_bits = (cci_value >> 1) & 0x7F
                connector_change = connector_change_bits != 0
                
                workflow_log.append(f"  - Command Completed (bit 31): {command_completed}")
                workflow_log.append(f"  - Connector Change (bits 1-7): {connector_change} (0x{connector_change_bits:02X})")
            else:
                workflow_log.append(f"Step 2 WARNING: Could not read CCI - {cci_result.get('error', 'Unknown')}")
                
        elif platform.system() == 'Windows':
            # Read CCI via UcsiControl.exe
            ucsi_path = get_ucsi_executable()
            args = ['read', '0', 'cci']
            result = run_ucsi_control(ucsi_path, args)
            if result.get('ok'):
                stdout = result.get('stdout', '')
                workflow_log.append(f"  CCI read output: {stdout[:200]}")  # Log first 200 chars for debugging
                
                # Parse CCI from output: "CCI: 0x80000302" or similar formats
                import re
                match = re.search(r'CCI[:\s]+0x([0-9A-Fa-f]+)', stdout, re.IGNORECASE)
                if match:
                    cci_value = int(match.group(1), 16)
                    workflow_log.append(f"Step 2 SUCCESS: CCI = 0x{cci_value:08X}")
                    
                    # Check bits
                    command_completed = (cci_value & 0x80000000) != 0
                    connector_change_bits = (cci_value >> 1) & 0x7F
                    connector_change = connector_change_bits != 0
                    
                    workflow_log.append(f"  - Command Completed (bit 31): {command_completed}")
                    workflow_log.append(f"  - Connector Change (bits 1-7): {connector_change} (0x{connector_change_bits:02X})")
                else:
                    workflow_log.append(f"Step 2 WARNING: Could not parse CCI from output")
                    workflow_log.append(f"  Full output: {stdout}")
            else:
                workflow_log.append(f"Step 2 WARNING: Could not read CCI - {result.get('error', 'Unknown')}")
        
        # Verify we have a pending notification (if CCI was read successfully)
        if cci_value is not None:
            if not command_completed and not connector_change:
                workflow_log.append("Step 2 WARNING: No pending notification found in CCI")
                workflow_log.append("  CCI indicates no Command Completed or Connector Change pending")
                workflow_log.append("  Proceeding anyway - ACK command may timeout if no notifications exist")
        else:
            workflow_log.append("Step 2 NOTE: CCI could not be verified, proceeding with ACK command")
            workflow_log.append("  If ACK fails, it means no notification was pending")
        
        # Step 3: Execute ACK_CC_CI command
        workflow_log.append("Step 3: Executing ACK_CC_CI command...")
        
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            # Determine which ACK variant to use based on CCI
            ack_command_key = "4 - ACK_CC_CI"
            result = aardvark_module.execute_command_by_name(ack_command_key, port)
            if not result.get('ok'):
                workflow_log.append(f"Step 3 FAILED: {result.get('error', 'Unknown error')}")
                return jsonify({
                    'error': 'ACK_CC_CI execution failed',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': result.get('error', 'ACK command execution failed')
                }), 400
            
            workflow_log.append(f"Step 3 SUCCESS: ACK_CC_CI completed")
            hex_response = result.get('response', '')
            
        elif platform.system() == 'Windows':
            ucsi_path = get_ucsi_executable()
            
            # Use the correct ACK_CC_CI command hex (always 00030004)
            # This acknowledges both Command Completed (bit 0) and Connector Change (bit 1)
            correct_ack_hex = "00030004"
            
            # For 8-character hex, UcsiControl.exe expects single argument
            args = ['send', '0', correct_ack_hex]
            
            # Increase timeout for ACK command (may take longer if waiting for notification)
            result = run_ucsi_control(ucsi_path, args, timeout=15)
            if not result.get('ok'):
                error_detail = result.get('error', 'Unknown error')
                workflow_log.append(f"Step 3 FAILED: {error_detail}")
                workflow_log.append("  This typically means: No UCSI notification was pending")
                workflow_log.append("  Or: The test command in Step 1 did not complete successfully")
                return jsonify({
                    'error': 'ACK_CC_CI execution failed',
                    'workflow_log': '\n'.join(workflow_log),
                    'details': error_detail,
                    'hint': 'ACK_CC_CI requires a pending notification. Try running another command first (like GET_CAPABILITY), then manually send ACK_CC_CI.'
                }), 400
            
            workflow_log.append(f"Step 3 SUCCESS: ACK_CC_CI completed")
            stdout = result.get('stdout', '')
            hex_response = extract_hex_from_ucsi_output(stdout)
        
        # Step 4: Verify acknowledgment
        workflow_log.append("Step 4: Verifying acknowledgment...")
        
        # Read CCI again to verify notification was cleared
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            cci_result_after = aardvark_module.read_cci_register(port)
            if cci_result_after.get('ok'):
                cci_after = cci_result_after.get('cci_value')
                workflow_log.append(f"Step 4 SUCCESS: CCI after ACK = 0x{cci_after:08X}")
                
                # Check if notification was cleared
                cmd_complete_after = (cci_after & 0x80000000) != 0
                conn_change_after = ((cci_after >> 1) & 0x7F) != 0
                
                if cmd_complete_after or conn_change_after:
                    workflow_log.append("  NOTE: Some notifications still pending (this is normal if multiple events occurred)")
                else:
                    workflow_log.append("  All notifications cleared successfully")
        
        elif platform.system() == 'Windows':
            args = ['read', '0', 'cci']
            result_after = run_ucsi_control(ucsi_path, args)
            if result_after.get('ok'):
                stdout_after = result_after.get('stdout', '')
                import re
                match_after = re.search(r'CCI:\s*0x([0-9A-Fa-f]+)', stdout_after)
                if match_after:
                    cci_after = int(match_after.group(1), 16)
                    workflow_log.append(f"Step 4 SUCCESS: CCI after ACK = 0x{cci_after:08X}")
                    
                    cmd_complete_after = (cci_after & 0x80000000) != 0
                    conn_change_after = ((cci_after >> 1) & 0x7F) != 0
                    
                    if cmd_complete_after or conn_change_after:
                        workflow_log.append("  NOTE: Some notifications still pending (this is normal if multiple events occurred)")
                    else:
                        workflow_log.append("  All notifications cleared successfully")
        
        workflow_log.append("=== ACK_CC_CI Workflow COMPLETED Successfully ===")
        
        # Build response
        decoded_result = {
            'command': '4 - ACK_CC_CI',
            'timestamp': datetime.now().isoformat(),
            'status': 'ACK_CC_CI workflow completed successfully',
            'workflow_summary': {
                'step_1': 'Test command sent (GET_CAPABILITY)',
                'step_2': f'CCI verified (Command Completed: {command_completed}, Connector Change: {connector_change})',
                'step_3': 'ACK_CC_CI executed',
                'step_4': 'Acknowledgment verified'
            },
            'cci_before': f"0x{cci_value:08X}" if cci_value is not None else "Not read"
        }
        
        return jsonify({
            'success': True,
            'hex_response': hex_response if 'hex_response' in locals() else 'ACK command (no response expected)',
            'decoded': decoded_result,
            'workflow_log': '\n'.join(workflow_log),
            'raw_output': result.get('stdout', '') if 'result' in locals() else ''
        })
        
    except Exception as e:
        workflow_log.append(f"EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'ACK_CC_CI workflow exception',
            'workflow_log': '\n'.join(workflow_log),
            'details': str(e)
        }), 500

@app.route('/api/execute_command', methods=['POST'])
def execute_command():
    """Execute a UCSI command via UcsiControl.exe (Windows), sysfs (Linux), or Aardvark."""
    try:
        data = request.get_json()
        debug_print(f"Execute command request: {data}")
        
        command_key = data.get('command_key', '')
        command_hex = data.get('command_hex', '')
        port = data.get('port', 1)
        ucsi_version = data.get('ucsi_version', '3.0')
        aardvark_mode = data.get('aardvark_mode', False)
        
        debug_print(f"[DEBUG] Command: {command_key}, Hex: {command_hex}, Port: {port}")
        debug_print(f"[DEBUG] Platform: {platform.system()}, Aardvark mode: {aardvark_mode}")
        
        if not command_hex:
            debug_print("[ERROR] No command hex provided")
            return jsonify({'error': 'No command hex provided'}), 400
        
        # Special handling for ACK_CC_CI - automatically setup the acknowledgment context
        if 'ACK_CC_CI' in command_key:
            debug_print("[ACK_CC_CI] Detected ACK_CC_CI command - setting up prerequisite workflow")
            return handle_ack_cc_ci_workflow(aardvark_mode, port, command_hex, ucsi_version)
        
        # Special handling for SET_POWER_LEVEL - automatically compare before/after connector status
        if 'SET_POWER_LEVEL' in command_key:
            debug_print("[SET_POWER_LEVEL] Detected SET_POWER_LEVEL command - setting up comparison workflow")
            return handle_set_power_level_workflow(aardvark_mode, port, command_hex, ucsi_version)
        
        # Clean hex string - remove any formatting if present
        clean_hex = command_hex.strip()
        
        # If hex contains formatting (Linux or Windows), extract just the hex
        if 'echo 0x' in clean_hex or '> command' in clean_hex:
            # Linux format: "echo 0x00000006 > command"
            import re
            match = re.search(r'0x([0-9a-fA-F]+)', clean_hex)
            if match:
                clean_hex = match.group(1)
                debug_print(f"[DEBUG] Extracted hex from Linux format: {clean_hex}")
            else:
                debug_print(f"[WARNING] Could not extract hex from Linux format: {clean_hex}")
        elif 'UcsiControl.exe' in clean_hex:
            # Windows format: "UcsiControl.exe send 0 00000006"
            parts = clean_hex.split()
            if len(parts) > 0:
                clean_hex = parts[-1]
                debug_print(f"[DEBUG] Extracted hex from Windows format: {clean_hex}")
        else:
            # Already clean hex - remove 0x prefix if present
            if clean_hex.startswith('0x') or clean_hex.startswith('0X'):
                clean_hex = clean_hex[2:]
            debug_print(f"[DEBUG] Using hex as-is: {clean_hex}")
        
        debug_print(f"[DEBUG] Clean hex for execution: {clean_hex}")
        debug_print(f"[DEBUG] About to check execution path - Platform: {platform.system()}")
        
        # Variable to hold ErrorIndicator from Aardvark (if available)
        aardvark_error_indicator = None
        aardvark_module = ensure_aardvark_integration() if aardvark_mode else None
        
        # Execute via Aardvark, Linux sysfs, or Windows UcsiControl.exe
        if aardvark_mode and aardvark_module and AARDVARK_AVAILABLE:
            # Use Aardvark - execute by command name
            try:
                debug_print(f"[AARDVARK] Calling execute_command_by_name('{command_key}', port={port})")
                debug_print(f"[AARDVARK] port type: {type(port)}")
                result = aardvark_module.execute_command_by_name(command_key, port)
                if not result.get('ok'):
                    error_msg = result.get('error', 'Aardvark execution failed')
                    output_msg = result.get('status_str', '')
                    return jsonify({
                        'error': error_msg,
                        'output': f"Aardvark execution failed: {error_msg}\\nStatus: {output_msg}"
                    }), 400
                hex_response =result.get('response', '')
                stdout = f"Aardvark response: {hex_response}"
                
                debug_print(f"[DEBUG] Aardvark result keys: {result.keys()}")
                debug_print(f"[DEBUG] Aardvark hex_response type: {type(hex_response)}")
                debug_print(f"[DEBUG] Aardvark hex_response: '{hex_response}'")
                debug_print(f"[DEBUG] Aardvark hex_response length: {len(hex_response)}")
                debug_print(f"[DEBUG] Aardvark hex_response == '': {hex_response == ''}")
                debug_print(f"[DEBUG] Aardvark hex_response is None: {hex_response is None}")
                debug_print(f"[DEBUG] Aardvark hex_response is empty: {not hex_response}")
                
                # Extract ErrorIndicator from Aardvark result if available
                aardvark_error_indicator = result.get('error_indicator')
                
                # Handle empty response (e.g., no alternate modes on this port)
                # Check multiple conditions to be absolutely sure
                if hex_response is None or hex_response == '' or len(str(hex_response)) == 0:
                    debug_print(f"[DEBUG] *** EMPTY RESPONSE DETECTED *** - returning friendly message")
                    decoded_result = {
                        'command': command_key,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'Command completed successfully',
                        'message': 'No data returned (e.g., no alternate modes available on this connector)'
                    }
                    if aardvark_error_indicator is not None:
                        decoded_result['ErrorIndicator'] = aardvark_error_indicator
                    return jsonify({
                        'success': True,
                        'hex_response': '',
                        'decoded': decoded_result
                    })
                
                debug_print(f"[DEBUG] Response is NOT empty, proceeding with decoding...")
            except Exception as e:
                return jsonify({'error': f'Aardvark error: {str(e)}'}), 500
                
        elif platform.system() == 'Linux':
            # Use Linux sysfs interface
            debug_print("[Linux] Executing UCSI command via sysfs")
            
            # Check if we have sudo credentials
            if not SUDO_PASSWORD:
                error_msg = "Sudo credentials not available. Please refresh the page to enter sudo password."
                debug_print(f"[Linux] ERROR: {error_msg}")
                return jsonify({'error': error_msg}), 400
            
            # Determine UCSI path - use internal_path for actual operations
            linux_ucsi_path = ''
            if UCSI_STATUS.get('internal_path'):
                linux_ucsi_path = UCSI_STATUS['internal_path']
            else:
                linux_ucsi_path = '/sys/kernel/debug/usb/ucsi/USBC000:00'
                debug_print(f"[Linux] No UCSI_STATUS internal_path, using default: {linux_ucsi_path}")
            
            debug_print(f"[Linux] UCSI path to use: {linux_ucsi_path}")
            
            # Check if UCSI device path exists using sudo (debugfs requires elevated permissions)
            try:
                check_result = subprocess.run(
                    ['sudo', '-S', 'test', '-d', linux_ucsi_path],
                    input=SUDO_PASSWORD.encode() if isinstance(SUDO_PASSWORD, str) else SUDO_PASSWORD,
                    capture_output=True,
                    timeout=5
                )
                
                if check_result.returncode != 0:
                    error_msg = f"UCSI device path not found: {linux_ucsi_path}. Please ensure debugfs is mounted and UCSI driver is loaded."
                    debug_print(f"[Linux] ERROR: {error_msg}")
                    return jsonify({'error': error_msg, 'dmesg_logs': capture_linux_dmesg_logs()}), 400
            except Exception as e:
                error_msg = f"Failed to check UCSI path: {str(e)}"
                debug_print(f"[Linux] ERROR: {error_msg}")
                return jsonify({'error': error_msg, 'dmesg_logs': capture_linux_dmesg_logs()}), 400
            
            command_file = f'{linux_ucsi_path}/command'
            response_file = f'{linux_ucsi_path}/response'
            
            # Verify command and response files exist using sudo
            try:
                cmd_check = subprocess.run(
                    ['sudo', '-S', 'test', '-f', command_file],
                    input=SUDO_PASSWORD.encode() if isinstance(SUDO_PASSWORD, str) else SUDO_PASSWORD,
                    capture_output=True,
                    timeout=5
                )
                
                resp_check = subprocess.run(
                    ['sudo', '-S', 'test', '-f', response_file],
                    input=SUDO_PASSWORD.encode() if isinstance(SUDO_PASSWORD, str) else SUDO_PASSWORD,
                    capture_output=True,
                    timeout=5
                )
                
                if cmd_check.returncode != 0:
                    error_msg = f"Command file not found: {command_file}"
                    debug_print(f"[Linux] ERROR: {error_msg}")
                    return jsonify({'error': error_msg, 'dmesg_logs': capture_linux_dmesg_logs()}), 400
                
                if resp_check.returncode != 0:
                    error_msg = f"Response file not found: {response_file}"
                    debug_print(f"[Linux] ERROR: {error_msg}")
                    return jsonify({'error': error_msg, 'dmesg_logs': capture_linux_dmesg_logs()}), 400
                    
            except Exception as e:
                error_msg = f"Failed to verify UCSI files: {str(e)}"
                debug_print(f"[Linux] ERROR: {error_msg}")
                return jsonify({'error': error_msg, 'dmesg_logs': capture_linux_dmesg_logs()}), 400
            
            try:
                # Import time for delay
                import time
                
                # Ensure password is a string (text=True requires string input, not bytes)
                sudo_password_str = SUDO_PASSWORD if isinstance(SUDO_PASSWORD, str) else SUDO_PASSWORD.decode()
                
                # Use longer timeout for commands that may take extra time
                # SET_NEW_CAM (0x0F) exit modes can take longer to process
                cmd_timeout = 20 if 'SET_NEW_CAM' in command_key else 5
                debug_print(f"[Linux] Using timeout: {cmd_timeout} seconds for {command_key}")
                
                # Step 1: Clear the dmesg buffer
                debug_print(f"[Linux] Clearing dmesg buffer before command execution...")
                subprocess.run(
                    ['sudo', '-S', 'dmesg', '-C'],
                    input=sudo_password_str,
                    capture_output=True,
                    text=True
                )
                
                # Execute both write and read commands in the UCSI directory
                # This matches the manual approach: cd to directory, echo command, cat response
                ucsi_dir = os.path.dirname(command_file)
                
                # Try multiple write methods for debugfs compatibility
                # Method 1: Standard echo redirection
                combined_cmd = f'cd {ucsi_dir} && echo 0x{clean_hex} > command && cat response'
                debug_print(f"[Linux] Attempting Method 1 (echo redirect): {combined_cmd}")
                
                result = subprocess.run(
                    ['sudo', '-S', 'bash', '-c', combined_cmd],
                    input=sudo_password_str,
                    capture_output=True,
                    timeout=cmd_timeout,
                    text=True
                )
                
                # If Method 1 fails, try Method 2: Using tee for writing
                if result.returncode != 0:
                    debug_print(f"[Linux] Method 1 failed: {result.stderr.strip()}")
                    debug_print(f"[Linux] Attempting Method 2 (echo + tee)...")
                    
                    # Method 2: echo piped to tee (works better with some debugfs files)
                    combined_cmd = f'cd {ucsi_dir} && echo 0x{clean_hex} | sudo tee command > /dev/null && cat response'
                    
                    result = subprocess.run(
                        ['sudo', '-S', 'bash', '-c', combined_cmd],
                        input=sudo_password_str,
                        capture_output=True,
                        timeout=cmd_timeout,
                        text=True
                    )
                
                # If Method 2 also fails, try Method 3: Absolute path
                if result.returncode != 0:
                    debug_print(f"[Linux] Method 2 failed: {result.stderr.strip()}")
                    debug_print(f"[Linux] Attempting Method 3 (absolute path)...")
                    
                    # Method 3: Use absolute path for command file
                    combined_cmd = f'echo 0x{clean_hex} > {command_file} && cat {response_file}'
                    
                    result = subprocess.run(
                        ['sudo', '-S', 'bash', '-c', combined_cmd],
                        input=sudo_password_str,
                        capture_output=True,
                        timeout=cmd_timeout,
                        text=True
                    )
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or 'Failed to execute UCSI command'
                    debug_print(f"[Linux] All write methods failed. Last error: {error_msg}")
                    
                    # Gather diagnostic information
                    diag_info = []
                    try:
                        # Check file permissions
                        ls_result = subprocess.run(
                            ['sudo', '-S', 'ls', '-la', command_file],
                            input=sudo_password_str,
                            capture_output=True,
                            timeout=5,
                            text=True
                        )
                        if ls_result.returncode == 0:
                            diag_info.append(f"Permissions: {ls_result.stdout.strip()}")
                        
                        # Check if file is writable
                        test_result = subprocess.run(
                            ['sudo', '-S', 'test', '-w', command_file],
                            input=sudo_password_str,
                            capture_output=True,
                            timeout=5,
                            text=True
                        )
                        diag_info.append(f"Writable: {'Yes' if test_result.returncode == 0 else 'No'}")
                        
                    except Exception as diag_e:
                        diag_info.append(f"Diagnostic error: {str(diag_e)}")
                    
                    return jsonify({
                        'error': f'Linux UCSI command failed: {error_msg}',
                        'hint': 'The command file may not support write operations. Check: 1) debugfs is mounted, 2) UCSI driver is loaded, 3) file permissions are correct.',
                        'diagnostics': ' | '.join(diag_info) if diag_info else 'No diagnostics available',
                        'dmesg_logs': capture_linux_dmesg_logs()
                    }), 400
                
                hex_response = result.stdout.strip()
                debug_print(f"[Linux] Response (raw): {hex_response}")
                
                # Linux sysfs returns bytes in big-endian format (MSB first)
                # Need to reverse byte order for little-endian UCSI format
                # Example: 0x02000320000000020008a20200004147 -> reverse bytes -> 0x4741000002a20800020000000003000002
                if hex_response.startswith('0x') or hex_response.startswith('0X'):
                    hex_clean = hex_response[2:]
                else:
                    hex_clean = hex_response
                
                # Linux UCSI debugfs sometimes adds 4 bytes of zero padding at the beginning
                # Check if response starts with 00000000 and remove it if present
                # Example: 0x0000000040001c46ff01000000018087 -> 40001c46ff01000000018087
                if hex_clean.startswith('00000000') and len(hex_clean) > 8:
                    debug_print(f"[Linux] Response has zero padding prefix, removing first 4 bytes")
                    hex_clean = hex_clean[8:]  # Remove first 8 hex chars (4 bytes of 0x00000000)
                    debug_print(f"[Linux] Response after removing padding: 0x{hex_clean}")
                
                # Split into byte pairs and reverse
                byte_pairs = [hex_clean[i:i+2] for i in range(0, len(hex_clean), 2)]
                byte_pairs.reverse()
                hex_response = '0x' + ''.join(byte_pairs)
                debug_print(f"[Linux] Response (byte-reversed for little-endian): {hex_response}")
                
                # Build stdout for compatibility
                stdout = f"Linux sysfs execution:\n"
                stdout += f"Command: echo 0x{clean_hex} > {command_file}\n"
                stdout += f"Response: {hex_response}\n"
                
                # Capture dmesg logs for UCSI (Linux only)
                dmesg_logs = capture_linux_dmesg_logs()
                
                # Create a result dict compatible with Windows path
                result = {
                    'ok': True,
                    'stdout': stdout,
                    'dmesg_logs': dmesg_logs
                }
                
            except subprocess.TimeoutExpired:
                debug_print("[Linux] ERROR: subprocess timeout")
                return jsonify({'error': 'Linux sysfs command timeout', 'dmesg_logs': capture_linux_dmesg_logs()}), 500
            except Exception as e:
                debug_print(f"[Linux] ERROR: Exception occurred: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Linux execution error: {str(e)}', 'dmesg_logs': capture_linux_dmesg_logs()}), 500
        
        else:
            # Use Windows UcsiControl.exe
            debug_print(f"[Windows] Entered Windows execution path")
            debug_print(f"[Windows] Platform detected: {platform.system()}")
            ucsi_path = get_ucsi_executable()
            if not ucsi_path:
                return jsonify({'error': 'UcsiControl.exe not found. Please ensure it is in the PATH or same directory.'}), 400
            
            # Format command: UcsiControl.exe send <HighDW> <LowDW>
            # For 16-character hex (two DWORDs), split into two 8-character arguments
            # Hex string is big-endian: first 8 chars = HighDW, last 8 chars = LowDW
            if len(clean_hex) == 16:
                high_dw = clean_hex[0:8]
                low_dw = clean_hex[8:16]
                args = ['send', high_dw, low_dw]
                debug_print(f"[Windows] Using DWORD format: send {high_dw} {low_dw}")
            else:
                args = ['send', '0', clean_hex]
            
            # Use longer timeout for commands that may take extra time
            # SET_NEW_CAM (0x0F) exit modes can take longer to process
            timeout = 20 if 'SET_NEW_CAM' in command_key else 8
            debug_print(f"[Windows] Using timeout: {timeout} seconds for {command_key}")
            
            result = run_ucsi_control(ucsi_path, args, timeout=timeout)
            
            if not result.get('ok'):
                return jsonify({'error': result.get('error', 'Command execution failed')}), 400
            
            stdout = result.get('stdout', '')
            if 'No UCSI controllers found' in stdout:
                return jsonify({'error': 'No UCSI controllers found'}), 400
            
            # Extract hex response from output
            hex_response = extract_hex_from_ucsi_output(stdout)
            
            # Check if MESSAGE_IN is empty (command completed but no data)
            # Handle various ways UcsiControl reports empty MESSAGE_IN
            message_in_empty = (
                'MESSAGE_IN is empty' in stdout or 
                'MESSAGE_IN:' in stdout and not hex_response
            )
            
            if not hex_response and message_in_empty:
                # Extract UCSI sections for display
                ucsi_sections = extract_ucsi_sections(stdout)
                
                # Command completed successfully but MESSAGE_IN is empty
                decoded_result = {
                    'command': command_key,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'Command completed successfully',
                    'message': 'MESSAGE_IN is empty - No data returned for this command'
                }
                
                # Add UCSI sections to decoded result
                if ucsi_sections.get('ucsi_control'):
                    decoded_result['UCSI_CONTROL'] = ucsi_sections['ucsi_control']
                if ucsi_sections.get('ucsi_version'):
                    decoded_result['UCSI_VERSION'] = ucsi_sections['ucsi_version']
                if ucsi_sections.get('ucsi_cci'):
                    decoded_result['UCSI_CCI'] = ucsi_sections['ucsi_cci']
                    # Parse CCI to extract ErrorIndicator
                    error_indicator = parse_cci_register(ucsi_sections['ucsi_cci'])
                    if error_indicator is not None:
                        decoded_result['ErrorIndicator'] = error_indicator
                        if error_indicator == 1:
                            decoded_result['message'] = 'Command returned ErrorIndicator=1 (PPM reports an error condition)'
                
                return jsonify({
                    'success': True,
                    'hex_response': 'MESSAGE_IN is empty.',
                    'decoded': decoded_result,
                    'raw_output': stdout
                })
            
            if not hex_response:
                return jsonify({'error': 'No hex response in command output', 'output': stdout}), 400
        
        # Decode the response
        resp_bytes = ucsi_decoders.decode_hex_string(hex_response)
        if resp_bytes is None:
            return jsonify({'error': 'Invalid hex response format'}), 400
        
        debug_print(f"[DECODE] Command: '{command_key}'")
        debug_print(f"[DECODE] Hex response: {hex_response}")
        debug_print(f"[DECODE] Response bytes length: {len(resp_bytes) if resp_bytes else 0}")
        
        # Get the decoder function
        decoder_func = ucsi_decoders.get_decoder(command_key)
        debug_print(f"[DECODE] Decoder function found: {decoder_func is not None}")
        if decoder_func:
            debug_print(f"[DECODE] Using decoder: {decoder_func.__name__}")
        else:
            debug_print(f"[DECODE] No decoder found for '{command_key}' - using generic decoder")
            # List available decoders for debugging
            from decoders import ucsi_decoders as decoder_module
            alternate_mode_decoders = [k for k in decoder_module.DECODER_MAP.keys() if 'ALTERNATE' in k]
            debug_print(f"[DECODE] Available ALTERNATE_MODES decoders: {alternate_mode_decoders}")
        
        if decoder_func:
            decoded_data = decoder_func(resp_bytes, ucsi_version)
        else:
            decoded_data = ucsi_decoders.decode_generic(resp_bytes, ucsi_version)
        
        decoded_data['command'] = command_key
        decoded_data['timestamp'] = datetime.now().isoformat()
        
        # Extract UCSI sections for all commands (if UcsiControl.exe was used)
        if not aardvark_mode and result.get('stdout'):
            ucsi_sections = extract_ucsi_sections(result.get('stdout', ''))
            if ucsi_sections.get('ucsi_control'):
                decoded_data['UCSI_CONTROL'] = ucsi_sections['ucsi_control']
            if ucsi_sections.get('ucsi_version'):
                decoded_data['UCSI_VERSION'] = ucsi_sections['ucsi_version']
            if ucsi_sections.get('ucsi_cci'):
                decoded_data['UCSI_CCI'] = ucsi_sections['ucsi_cci']
                # Parse CCI to extract ErrorIndicator
                error_indicator = parse_cci_register(ucsi_sections['ucsi_cci'])
                if error_indicator is not None:
                    decoded_data['ErrorIndicator'] = error_indicator
                    # If ErrorIndicator is set, the command failed (device may be disconnected)
                    if error_indicator == 1:
                        decoded_data['error'] = 'ErrorIndicator set - Command failed (device may be disconnected or not responding)'
                        decoded_data['warning'] = 'Data returned may be cached/stale from previous connection'
        elif aardvark_mode and aardvark_error_indicator is not None:
            # Add ErrorIndicator from Aardvark CCI register read
            decoded_data['ErrorIndicator'] = aardvark_error_indicator
        
        return jsonify({
            'success': True,
            'hex_response': format_hex_response(hex_response),
            'decoded': decoded_data,
            'raw_output': result.get('stdout', '') if not aardvark_mode else '',
            'dmesg_logs': result.get('dmesg_logs', None)  # Include dmesg logs if available (Linux only)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check_device', methods=['GET'])
def check_device():
    """Check UCSI device status - platform aware (Device Manager on Windows, debugfs on Linux)."""
    global SYSTEM_SETUP_DONE
    
    # Ensure system setup has been performed
    if not SYSTEM_SETUP_DONE:
        perform_system_setup()
    
    # Return UCSI status if available
    if UCSI_STATUS['checked']:
        result = {
            'has_error': not UCSI_STATUS['found'],
            'firmware_version': 'N/A',
            'device_found': UCSI_STATUS['found'],
            'error': UCSI_STATUS['error'] if not UCSI_STATUS['found'] else None,
            'os': platform.system(),
            'ucsi_message': UCSI_STATUS['message'],  # Add the formatted message
            'ucsi_location': UCSI_STATUS['location']  # Shows 'debugfs' on Linux, device name on Windows
        }
        return jsonify({
            'success': True,
            'device_status': result
        })
    
    # Fallback to old Device Manager check for Windows
    result = check_ucsi_device_manager()
    return jsonify({
        'success': True,
        'device_status': result
    })

@app.route('/api/check_aardvark', methods=['GET'])
def check_aardvark():
    """Check if Aardvark device is connected and drivers are installed."""
    result = {
        'driver_installed': False,
        'device_connected': False,
        'available': False,
        'connected': False,
        'error': None,
        'message': '',
        'status': 'unknown',  # 'driver_not_installed', 'device_not_connected', 'device_present_no_drivers', 'ready'
        'debug_info': {}
    }
    
    aardvark_module = ensure_aardvark_integration(detect_device=False)
    
    # Add debug information
    result['debug_info']['AARDVARK_AVAILABLE'] = AARDVARK_AVAILABLE
    result['debug_info']['AARDVARK_DEVICE_DETECTED'] = AARDVARK_DEVICE_DETECTED
    result['debug_info']['platform'] = platform.system()
    result['debug_info']['frozen'] = getattr(sys, 'frozen', False)
    
    # Step 1: Check if drivers/library is installed
    if not AARDVARK_AVAILABLE or aardvark_module is None:
        result['driver_installed'] = False
        result['status'] = 'driver_not_installed'
        result['error'] = 'Aardvark library/drivers not installed'
        
        # Add additional debug info if available
        if aardvark_module is not None:
            try:
                result['debug_info']['integration_available'] = aardvark_module.AARDVARK_AVAILABLE
                if hasattr(aardvark_module, 'USE_CTYPES'):
                    result['debug_info']['USE_CTYPES'] = aardvark_module.USE_CTYPES
            except Exception as e:
                result['debug_info']['import_error'] = str(e)
        
        # Don't return yet - check if device is physically present
    else:
        result['driver_installed'] = True
    
    # Step 2: Check for device (both via driver API and USB detection)
    try:
        device_info = aardvark_module.detect_aardvark_device() if aardvark_module else {'found': False, 'usb_detected': False}
        result['debug_info']['detection_result'] = device_info
        
        if device_info and device_info.get('found'):
            # Device is connected and drivers are installed
            result['device_connected'] = True
            result['available'] = True
            result['connected'] = True
            result['status'] = 'ready'
            result['message'] = f"✓ Aardvark Ready: {device_info.get('description', 'Device connected')}"
            result['port'] = device_info.get('port', -1)
            result['description'] = device_info.get('description', '')
            return jsonify(result)
        
        # Check if device is physically present but drivers missing
        if device_info and device_info.get('usb_detected'):
            result['device_connected'] = False  # Connected via USB but not accessible via driver
            result['status'] = 'device_present_no_drivers'
            result['error'] = 'Device detected but drivers not installed'
            result['message'] = (
                '⚠️ Aardvark Adapter Detected (Drivers Missing)\n\n'
                'Your Aardvark I2C/SPI adapter is physically connected and visible in Device Manager '
                'under "Other devices" with a yellow exclamation mark.\n\n'
                'To enable Aardvark mode:\n'
                '1. Download Aardvark drivers from Total Phase website\n'
                '2. Install the drivers for your operating system\n'
                '3. After installation, the device will appear under "Universal Serial Bus Controllers" without the yellow mark\n'
                '4. Run: pip install pyaardvark\n'
                '5. Restart the application'
            )
            return jsonify(result)
        
        # Device not found at all
        if not result['driver_installed']:
            result['message'] = (
                '❌ Aardvark Drivers Not Installed\n\n'
                'The Aardvark Python library and drivers are not installed on this system.\n\n'
                'To use Aardvark mode:\n'
                '1. Download Aardvark drivers from Total Phase\n'
                '2. Install the drivers for your operating system\n'
                '3. Run: pip install pyaardvark\n'
                '4. Reconnect your Aardvark adapter and restart the application'
            )
        else:
            result['device_connected'] = False
            result['status'] = 'device_not_connected'
            result['error'] = device_info.get('error', 'No Aardvark device found')
            result['message'] = (
                '⚠️ Aardvark Device Not Connected\n\n'
                'Drivers are installed, but the Aardvark I2C/SPI adapter is not detected.\n\n'
                'Please:\n'
                '1. Connect your Aardvark I2C/SPI Host Adapter to a USB port\n'
                '2. Wait for drivers to load (usually 2-3 seconds)\n'
                '3. Try again'
            )
    
    except Exception as e:
        result['device_connected'] = False
        result['status'] = 'error'
        result['error'] = str(e)
        result['message'] = f'Error checking Aardvark device: {str(e)}'
        result['debug_info']['exception'] = str(e)
        import traceback
        result['debug_info']['traceback'] = traceback.format_exc()
    
    return jsonify(result)

@app.route('/api/scan_i2c_bus', methods=['GET'])
def scan_i2c_bus():
    """Scan I2C bus to discover all responding devices."""
    aardvark_module = ensure_aardvark_integration()
    if not AARDVARK_AVAILABLE or aardvark_module is None:
        return jsonify({
            'success': False,
            'error': 'Aardvark library not available',
            'devices': [],
            'addresses': []
        }), 400
    
    try:
        # Get full_scan parameter (default to False for faster scan)
        full_scan = request.args.get('full_scan', 'false').lower() == 'true'
        
        # Run the scan
        result = aardvark_module.scan_i2c_bus(full_scan=full_scan)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'devices': [],
            'addresses': []
        }), 500

@app.route('/api/i2c_address_info', methods=['GET'])
def get_i2c_address_info():
    """Get information about discovered I2C addresses."""
    aardvark_module = ensure_aardvark_integration()
    if not AARDVARK_AVAILABLE or aardvark_module is None:
        return jsonify({
            'success': False,
            'error': 'Aardvark library not available'
        }), 400
    
    try:
        info = aardvark_module.get_i2c_address_info()
        return jsonify({
            'success': True,
            **info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/set_ppm_address', methods=['POST'])
def set_ppm_address():
    """Manually set the PPM I2C address."""
    aardvark_module = ensure_aardvark_integration()
    if not AARDVARK_AVAILABLE or aardvark_module is None:
        return jsonify({
            'success': False,
            'error': 'Aardvark library not available'
        }), 400
    
    try:
        data = request.get_json()
        address = data.get('address')
        
        if address is None:
            return jsonify({
                'success': False,
                'error': 'No address provided'
            }), 400
        
        aardvark_module.set_ppm_address(address)
        
        return jsonify({
            'success': True,
            'message': f'PPM address set to {address}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/vdc_loopback_test', methods=['POST'])
def vdc_loopback_test():
    """
    Run a 255-byte UCSI Vendor Defined Command (VDC) loopback test.
    Sends a fixed 255-byte incrementing payload via UcsiControl.exe and
    checks the EC echo response for correctness.
    Windows only (requires UcsiControl.exe).
    """
    if platform.system() != 'Windows':
        return jsonify({'success': False, 'error': 'VDC loopback test only supported on Windows'}), 400

    ucsi_path = get_ucsi_executable()
    if not ucsi_path:
        return jsonify({'success': False, 'error': 'UcsiControl.exe not found. Place it in the same directory or in PATH.'}), 400

    # Fixed 255-byte incrementing payload (matches the batch file exactly)
    args = [
        'Send',
        '00018087', '1080FF20',
        '03020100', '07060504', '0B0A0908', '0F0E0D0C',
        '13121110', '17161514', '1B1A1918', '1F1E1D1C',
        '23222120', '27262524', '2B2A2928', '2F2E2D2C',
        '33323130', '37363534', '3B3A3938', '3F3E3D3C',
        '43424140', '47464544', '4B4A4948', '4F4E4D4C',
        '53525150', '57565554', '5B5A5958', '5F5E5D5C',
        '63626160', '67666564', '6B6A6968', '6F6E6D6C',
        '73727170', '77767574', '7B7A7978', '7F7E7D7C',
        '83828180', '87868584', '8B8A8988', '8F8E8D8C',
        '93929190', '97969594', '9B9A9998', '9F9E9D9C',
        'A3A2A1A0', 'A7A6A5A4', 'ABAAA9A8', 'AFAEADAC',
        'B3B2B1B0', 'B7B6B5B4', 'BBBAB9B8', 'BFBEBDBC',
        'C3C2C1C0', 'C7C6C5C4', 'CBCAC9C8', 'CFCECDCC',
        'D3D2D1D0', 'D7D6D5D4', 'DBDAD9D8', 'DFDEDDDC',
        'E3E2E1E0', 'E7E6E5E4', 'EBEAE9E8', 'EFEEEDEC',
        'F3F2F1F0', 'F7F6F5F4', 'FBFAF9F8', '00FEFDFC',
    ]

    result = run_ucsi_control(ucsi_path, args, timeout=30)
    raw_output = result.get('stdout', '') + result.get('stderr', '')

    if not result.get('ok'):
        return jsonify({
            'success': False,
            'error': result.get('error', 'UcsiControl.exe failed'),
            'raw_output': raw_output
        }), 400

    output = raw_output.lower()

    ok_cmd  = 'command completed successfully.' in output
    ok_msg  = '87 80 01 00 00 0a'             in output
    ok_sum  = '81 7e 00 00'                   in output
    bad_err = 'errorindicator: 1'             in output

    passed = ok_cmd and ok_msg and ok_sum and not bad_err

    # Extract MESSAGE_IN hex bytes from UcsiControl output
    # Look for hex patterns in output (e.g., "87 80 01 00" or "87800100")
    import re as _re
    hex_response = ''
    
    # Try multiple extraction strategies
    # Strategy 1: Look for "MESSAGE_IN:" followed by hex
    msg_in_match = _re.search(r'message[_\s]*in[:\s]+([0-9a-f\s]+)', raw_output, _re.IGNORECASE)
    if msg_in_match:
        hex_bytes = msg_in_match.group(1).strip().split()
        hex_response = ' '.join(h.upper().zfill(2) for h in hex_bytes if len(h) <= 2)
    
    # Strategy 2: Look for hex lines with the known header/checksum (VDC specific)
    if not hex_response:
        # Extract all lines that look like hex output (8 hex bytes per line typical format)
        hex_lines = []
        for line in raw_output.split('\n'):
            # Look for lines with multiple hex bytes (space-separated or concatenated)
            if _re.search(r'([0-9a-f]{2}\s+){2,}', line, _re.IGNORECASE):
                # Extract the hex part from the line
                hex_part = _re.findall(r'([0-9a-f]{2})\s+', line, _re.IGNORECASE)
                if hex_part:
                    hex_lines.extend(hex_part)
        
        if hex_lines:
            hex_response = ' '.join(h.upper() for h in hex_lines)
    
    # Strategy 3: If test passed, construct response from known values
    # For VDC loopback: MESSAGE_IN contains header + echo + checksum
    if not hex_response and passed:
        # Known values from the test
        # We validate "87 80 01 00 00 0a" (success header) and "81 7e 00 00" (checksum)
        # Construct minimal MESSAGE_IN showing these key parts
        hex_response = '87 80 01 00 00 0a 81 7e 00 00'

    # Extract UCSI_CONTROL block from output if present
    ucsi_control = ''
    ctrl_match = _re.search(r'(UCSI_CONTROL[^\n]*(?:\n(?:[ \t]+[^\n]+))*)', raw_output)
    if ctrl_match:
        ucsi_control = ctrl_match.group(1).strip()

    # Format raw_hex like other commands: 8 bytes per line
    raw_hex_formatted = ''
    if hex_response:
        hex_list = hex_response.split()
        lines = [' '.join(hex_list[i:i+8]) for i in range(0, len(hex_list), 8)]
        raw_hex_formatted = '\n'.join(lines)

    decoded = {
        'command': '20 - VENDOR_DEFINED (VDC Loopback Test)',
        'timestamp': datetime.now().isoformat(),
        'raw_hex': raw_hex_formatted if hex_response else None,
        'raw_len': len(hex_response.split()) if hex_response else 0,
        'status': 'PASS – 255-byte VDC loopback verified' if passed else None,
        'error':  'FAIL – EC response did not match expected values' if not passed else None,
        'VDC_Checks': (
            f"Command completed: {'YES' if ok_cmd else 'NO'}\n"
            f"Success header (87 80 01 00 00 0a): {'YES' if ok_msg else 'NO'}\n"
            f"Checksum match (81 7e 00 00): {'YES' if ok_sum else 'NO'}\n"
            f"Error indicator: {'YES (BAD)' if bad_err else 'NO (GOOD)'}"
        ),
    }
    if ucsi_control:
        decoded['UCSI_CONTROL'] = ucsi_control

    return jsonify({
        'success': passed,
        'hex_response': hex_response,
        'decoded': decoded,
        'checks': {
            'command_completed': ok_cmd,
            'success_header':    ok_msg,
            'checksum_match':    ok_sum,
            'error_indicator':   bad_err,
        },
        'raw_output': raw_output,
        'summary': (
            'PASS \u2013 255-byte VDC loopback verified: all bytes received, checksum correct.'
            if passed else
            'FAIL \u2013 EC response did not match expected values. See raw output for details.'
        )
    })


@app.route('/api/cleanup_logs', methods=['POST'])
def cleanup_logs():
    """Remove Aardvark log files older than a specified number of days."""
    try:
        days = request.json.get('days', 7) if request.json else 7
        days = max(1, int(days))
        
        from aardvark.log_utils import cleanup_old_logs
        result = cleanup_old_logs(days=days)
        
        if result['error']:
            return jsonify({
                'success': False,
                'message': f"Cleanup failed: {result['error']}"
            }), 500
        
        return jsonify({
            'success': True,
            'message': f"Cleaned {result['cleaned']} log file(s) older than {days} days"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error during cleanup: {str(e)}"
        }), 500


@app.route('/save_test_results', methods=['POST'])
def save_test_results():
    """Save test results to a file in the executable directory."""
    try:
        data = request.get_json()
        filename = data.get('filename', 'test_results.txt')
        content = data.get('content', '')
        
        # Get the directory where the executable/script is running
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            app_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join(app_dir, 'test_results')
        os.makedirs(results_dir, exist_ok=True)
        
        # Full path to the file
        filepath = os.path.join(results_dir, filename)
        
        # Write the content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'filepath': filepath,
            'message': f'Results saved to {filepath}'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Failed to save results: {str(e)}'
        })


def check_ucsi_device_manager():
    """
    Check Device Manager for UCSI device status (Windows only).
    Returns dict with device information.
    """
    result = {
        'has_error': False,
        'has_warning': False,
        'yellow_bang': False,
        'problem_code': None,
        'status_text': 'Unknown',
        'firmware_version': 'Unknown',
        'device_found': False,
        'device_name': 'Unknown',
        'error': None,
        'os': platform.system()
    }
    
    # Only run on Windows
    if platform.system() != 'Windows':
        result['error'] = 'Device Manager check only available on Windows'
        return result
    
    try:
        # Use PowerShell to query device manager via PnP devices
        ps_script = '''
$ucsiDevice = Get-PnpDevice | Where-Object { 
    $_.FriendlyName -like "*UCM-UCSI*" -or 
    $_.FriendlyName -like "*UCSI*" -or
    $_.InstanceId -like "*USBC*"
}

if ($ucsiDevice) {
    $device = $ucsiDevice | Select-Object -First 1
    $status = $device.Status
    $problemCode = $device.ProblemCode
    $instanceId = $device.InstanceId
    $friendlyName = $device.FriendlyName
    
    # Get device properties including firmware version
    $props = Get-PnpDeviceProperty -InstanceId $instanceId
    $fwVersion = ($props | Where-Object { $_.KeyName -eq "DEVPKEY_Device_FirmwareVersion" }).Data
    
    # If firmware version not found, try alternative property names
    if (-not $fwVersion) {
        $fwVersion = ($props | Where-Object { $_.KeyName -like "*Firmware*" }).Data | Select-Object -First 1
    }
    
    # Output in parseable format
    Write-Output "DEVICE_FOUND:True"
    Write-Output "STATUS:$status"
    Write-Output "PROBLEM_CODE:$problemCode"
    Write-Output "FRIENDLY_NAME:$friendlyName"
    Write-Output "INSTANCE_ID:$instanceId"
    if ($fwVersion) {
        Write-Output "FW_VERSION:$fwVersion"
    } else {
        Write-Output "FW_VERSION:Not Available"
    }
} else {
    Write-Output "DEVICE_FOUND:False"
}
'''
        
        # Run PowerShell command (hide window on Windows)
        creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        
        process = subprocess.Popen(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
        
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode != 0:
            result['error'] = f"PowerShell error: {stderr}"
            return result
        
        # Parse output
        lines = stdout.strip().split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'DEVICE_FOUND':
                    result['device_found'] = value.lower() == 'true'
                elif key == 'STATUS':
                    # Status can be: OK, Error, Degraded, Unknown
                    result['status_text'] = value
                    result['has_error'] = value.lower() in ['error', 'degraded']
                elif key == 'PROBLEM_CODE':
                    # Problem codes indicate yellow bang (warning/error)
                    # Common Windows Device Manager Problem Codes:
                    # 0  = No problem (device working properly)
                    # 1  = Device not configured correctly
                    # 10 = Device cannot start
                    # 12 = Not enough free resources
                    # 18 = Device needs to be reinstalled
                    # 19 = Registry returned unknown result
                    # 22 = Device is disabled
                    # 28 = Drivers for this device are not installed
                    # 31 = Device is not working properly
                    # 43 = Windows has stopped this device (Code 43)
                    # 52 = Windows cannot verify digital signature
                    try:
                        problem_code = int(value) if value and value.isdigit() else 0
                        result['problem_code'] = problem_code
                        result['yellow_bang'] = problem_code > 0
                        result['has_warning'] = problem_code > 0
                        if problem_code > 0:
                            result['has_error'] = True
                    except (ValueError, TypeError):
                        result['problem_code'] = None
                elif key == 'FRIENDLY_NAME':
                    result['device_name'] = value
                elif key == 'FW_VERSION':
                    result['firmware_version'] = value
        
        return result
        
    except subprocess.TimeoutExpired:
        result['error'] = "PowerShell command timed out"
        return result
    except Exception as e:
        result['error'] = str(e)
        return result

        
        # Format as UcsiControl.exe command
        if len(formatted_hex) == 16:
            high_dw = formatted_hex[0:8]
            low_dw = formatted_hex[8:16]
            ucsi_command = f"UcsiControl.exe Send {high_dw} {low_dw}"
        else:
            ucsi_command = f"UcsiControl.exe Send 0 {formatted_hex}"
        
        return jsonify({
            'success': True,
            'original_hex': cmd_hex,
            'formatted_hex': formatted_hex,
            'ucsi_command': ucsi_command,
            'port': port
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_port_in_hex(cmd_hex, port):
    """Update port number in command hex."""
    if len(cmd_hex) < 6:
        return cmd_hex
    
    try:
        # Pad to even length so bytes.fromhex works on odd-length strings
        padded_hex = cmd_hex if len(cmd_hex) % 2 == 0 else '0' + cmd_hex
        cmd_bytes = bytes.fromhex(padded_hex)
        if len(cmd_bytes) < 3:
            return cmd_hex
        
        # Check command code (last byte)
        cmd_code = cmd_bytes[-1]
        
        # Commands without connector numbers or with custom formatting
        # Added 0x0C (GET_ALTERNATE_MODES) - already formatted correctly by frontend
        NON_CONNECTOR_COMMANDS = {0x01, 0x02, 0x04, 0x05, 0x06, 0x0C, 0x13, 0x1C, 0x1F}
        if cmd_code in NON_CONNECTOR_COMMANDS:
            return cmd_hex
        
        # Special handling for GET_LPM_PPM_INFO (0x22)
        # Format: [Connector Number 2 bytes][Data Length 1 byte][Command 1 byte]
        # Port 0 (PPM): 00000022, Port 1: 00010022, Port 2: 00020022
        if cmd_code == 0x22:
            # Connector number is in bytes 0-1 (little endian, but as a 16-bit value it's just the port number)
            port_hex = f"{int(port):04x}".upper()
            return f"{port_hex}0022"
        
        # Connector number is in bits [22:16] of the UCSI CONTROL value,
        # which is the 3rd byte from the end in the hex string (byte index -3).
        connector_idx = len(cmd_bytes) - 3
        connector_byte = cmd_bytes[connector_idx]
        upper_bit = connector_byte & 0x80  # Preserve bit 7 (role bit)
        new_connector_byte = upper_bit | (int(port) & 0x7F)
        
        # Rebuild
        new_cmd_bytes = bytearray(cmd_bytes)
        new_cmd_bytes[connector_idx] = new_connector_byte
        
        return new_cmd_bytes.hex().upper()
    except:
        return cmd_hex

def get_ucsi_executable():
    """Find UcsiControl.exe in PATH, bundled resources, current directory, scripts folder, or parent directory."""
    import os
    import shutil
    
    # Check if in PATH
    ucsi_path = shutil.which('UcsiControl.exe')
    if ucsi_path:
        return ucsi_path

    # Check bundled PyInstaller location first when running as a one-file EXE
    bundle_dir = get_app_base_dir()
    bundled_path = os.path.join(bundle_dir, 'UcsiControl.exe')
    if os.path.exists(bundled_path):
        return bundled_path
    
    # Check in current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(current_dir, 'UcsiControl.exe')
    if os.path.exists(local_path):
        return local_path
    
    # Check in scripts/ subfolder
    scripts_path = os.path.join(current_dir, 'scripts', 'UcsiControl.exe')
    if os.path.exists(scripts_path):
        return scripts_path
    
    # Check parent directory
    parent_dir = os.path.dirname(current_dir)
    parent_path = os.path.join(parent_dir, 'UcsiControl.exe')
    if os.path.exists(parent_path):
        return parent_path
    
    return None

def run_ucsi_control(path_to_ucsi, args_list, timeout=8):
    """Execute UcsiControl.exe with given arguments."""
    import os
    
    full_cmd = [path_to_ucsi] + args_list
    try:
        # Hide console window on Windows
        si = None
        creationflags = 0
        if platform.system() == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW
        
        p = subprocess.run(
            full_cmd, 
            capture_output=True, 
            timeout=timeout, 
            check=False, 
            text=True, 
            shell=False, 
            startupinfo=si,
            creationflags=creationflags
        )
        
        stdout = p.stdout.strip()
        stderr = p.stderr.strip()
        code = p.returncode
        
        return {"ok": True, "stdout": stdout, "stderr": stderr, "returncode": code}
    except FileNotFoundError:
        return {"ok": False, "error": f"UcsiControl not found at: {path_to_ucsi}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "UcsiControl timed out"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def parse_cci_register(cci_text):
    """Parse CCI register value and extract ErrorIndicator."""
    try:
        import re
        # First try to find the explicit ErrorIndicator line (most reliable)
        error_line_match = re.search(r'ErrorIndicator:\s*(\d+)', cci_text)
        if error_line_match:
            return int(error_line_match.group(1))
        
        # Fallback: Extract from AsUInt32/AsUInt64 value and calculate bit 30
        # Look for hex value in CCI text (format: "0xXXXXXXXX" or "XXXXXXXX")
        # Accept 1-8 hex digits to handle values like 0x8000000 (7 digits)
        hex_match = re.search(r'AsUInt(?:32|64):\s*(?:0x)?([0-9A-Fa-f]{1,16})', cci_text)
        if hex_match:
            cci_value = int(hex_match.group(1), 16)
            # Bit 30 is Error Indicator (per UCSI spec Table 6-2)
            error_indicator = (cci_value >> 30) & 0x01
            return error_indicator
    except:
        pass
    return None

def extract_ucsi_sections(output):
    """Extract UCSI_CONTROL, UCSI VERSION, and UCSI_CCI sections from output."""
    lines = output.split('\n')
    sections = {
        'ucsi_control': [],
        'ucsi_version': [],
        'ucsi_cci': []
    }
    
    current_section = None
    
    for line in lines:
        stripped = line.strip()
        
        # Detect section headers
        if 'UCSI_CONTROL:' in line:
            current_section = 'ucsi_control'
            sections['ucsi_control'].append('UCSI_CONTROL:')
            continue
        elif 'UCSI VERSION:' in line:
            current_section = 'ucsi_version'
            sections['ucsi_version'].append('UCSI VERSION:')
            continue
        elif 'UCSI_CCI:' in line:
            current_section = 'ucsi_cci'
            sections['ucsi_cci'].append('UCSI_CCI:')
            continue
        
        # Stop collecting if we hit MESSAGE_IN
        if 'MESSAGE_IN' in stripped:
            current_section = None
            continue
        
        # Skip separator lines (===, ---, etc.) and empty lines
        if current_section is not None and stripped and not all(c in '=-_' for c in stripped):
            # Add the stripped line to preserve consistent formatting
            sections[current_section].append(stripped)
    
    # Convert lists to strings with proper line breaks
    result = {}
    for key, section_lines in sections.items():
        if section_lines:
            # Join with newlines to create multi-line text
            result[key] = '\n'.join(section_lines)
    
    return result

def extract_hex_from_ucsi_output(output):
    """Extract hex response from UcsiControl.exe output."""
    lines = output.split('\n')
    hex_lines = []
    in_message_in_section = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're entering MESSAGE_IN section
        if 'MESSAGE_IN:' in line or 'UCSI MESSAGE_IN:' in line:
            in_message_in_section = True
            continue
        
        # Check if we're leaving MESSAGE_IN section (next section starts)
        if in_message_in_section and line and ':' in line and '=' in line:
            in_message_in_section = False
        
        # If in MESSAGE_IN section, collect hex lines
        if in_message_in_section and line:
            # Check if line looks like hex (only contains hex chars and spaces)
            cleaned = line.replace(' ', '').replace('\t', '')
            if cleaned and all(c in '0123456789ABCDEFabcdef' for c in cleaned):
                hex_lines.append(cleaned)
    
    # If we found hex in MESSAGE_IN section, return it
    if hex_lines:
        return ''.join(hex_lines)
    
    # Fallback: look for any line with hex (old behavior)
    for line in lines:
        line = line.strip()
        if line and not any(skip in line.lower() for skip in ['ucsi', 'command', 'response:', 'controller']):
            cleaned = line.replace(' ', '').replace('\t', '')
            if cleaned and all(c in '0123456789ABCDEFabcdef' for c in cleaned):
                return cleaned
    
    return ''


if __name__ == '__main__':
    try:
        def is_port_available(host, port):
            """Return True if host:port can be bound, else False."""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return True
            except OSError:
                return False
            finally:
                sock.close()

        def show_startup_popup(title, message, is_error=True):
            """Show a GUI popup with robust Windows fallback for windowed EXE mode."""
            if platform.system() == 'Windows':
                try:
                    import ctypes

                    mb_icon = 0x10 if is_error else 0x40
                    mb_topmost = 0x00040000
                    ctypes.windll.user32.MessageBoxW(0, str(message), str(title), mb_icon | mb_topmost)
                    return
                except Exception:
                    pass

            try:
                import tkinter as tk
                from tkinter import messagebox

                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                if is_error:
                    messagebox.showerror(title, message, parent=root)
                else:
                    messagebox.showinfo(title, message, parent=root)
                root.destroy()
            except Exception:
                # Console fallback keeps behavior safe for headless sessions.
                print(f"{title}: {message}")

        debug_print("Starting UCSI WebApp...")
        import flask
        try:
            from importlib.metadata import version
            flask_version = version('flask')
        except Exception:
            flask_version = "unknown"
        debug_print(f"Flask version: {flask_version}")
        debug_print("Attempting to bind to 0.0.0.0:5000...")

        host = '0.0.0.0'
        port = 5000

        start_browser_monitor_if_needed()

        if not is_port_available(host, port):
            error_message = (
                f"Port {port} is already in use.\n\n"
                "Close the application using that port and try again."
            )
            print(f"ERROR: {error_message}")
            show_startup_popup("UCSI Decoder Startup Error", error_message, is_error=True)
            raise SystemExit(1)
        
        if not DEBUG:
            print(f"Server starting on http://{host}:{port}")

        import webbrowser

        def wait_for_server_ready(check_port, timeout_seconds=12):
            """Wait until localhost:port accepts connections."""
            deadline = time.time() + timeout_seconds
            while time.time() < deadline:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(0.3)
                try:
                    if test_sock.connect_ex(('127.0.0.1', check_port)) == 0:
                        return True
                except Exception:
                    pass
                finally:
                    test_sock.close()
                time.sleep(0.25)
            return False

        def open_browser_url(url):
            """Open browser with fallback methods for windowed EXE environments."""
            if platform.system() == 'Windows':
                try:
                    os.startfile(url)  # type: ignore[attr-defined]
                    return True
                except Exception:
                    pass

                try:
                    creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    subprocess.Popen(
                        ['cmd', '/c', 'start', '', url],
                        creationflags=creationflags
                    )
                    return True
                except Exception:
                    pass

            try:
                if webbrowser.open_new(url):
                    return True
            except Exception:
                pass

            return False

        def open_browser():
            url = f"http://localhost:{port}"
            # Give Flask a moment and then wait for actual socket readiness.
            time.sleep(0.8)
            if not wait_for_server_ready(port, timeout_seconds=10):
                show_startup_popup(
                    "UCSI Decoder",
                    f"Server did not become ready on time.\n\nTry opening manually: {url}",
                    is_error=True
                )
                return

            opened = False
            for _ in range(8):
                if open_browser_url(url):
                    opened = True
                    break
                time.sleep(0.7)

            if not opened:
                show_startup_popup(
                    "UCSI Decoder",
                    f"Server started, but browser could not be opened automatically.\n\nPlease open: {url}",
                    is_error=True
                )

        threading.Thread(target=open_browser, daemon=True).start()

        app.run(debug=False, host=host, port=port, use_reloader=False)
    except Exception as e:
        print(f"ERROR: Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        try:
            show_startup_popup("UCSI Decoder Startup Error", f"Failed to start application:\n{e}", is_error=True)
        except Exception:
            pass
        pause_before_exit()





