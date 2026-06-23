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
Linux UCSI Backend
Handles Linux-specific UCSI operations via debugfs.
"""

import os
import sys
import subprocess
import glob
import getpass
from typing import Optional, Tuple, Dict, Any

# Debug flag
DEBUG = os.getenv('DEBUG', '0') == '1'

def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG mode is enabled."""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()


def get_sudo_credentials() -> Tuple[Optional[str], Optional[str]]:
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
            "This application requires administrator privileges for USB device access.\\n\\n"
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


def mount_debugfs(sudo_password: str) -> bool:
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


def check_ucsi_folder(sudo_password: str) -> Tuple[bool, str]:
    """
    Check if UCSI folder exists in /sys/kernel/debug/ and find device.
    
    Supports both old and new UCSI debugfs structures:
    - New: /sys/kernel/debug/usb/ucsi/USBC000:00 (kernel 5.x+)
    - Old: /sys/kernel/debug/ucsi/ppm0 (older kernels)
    
    Returns:
        (found, path_or_error): Boolean and either the path or error message
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
                    devices = [d for d in contents.split('\\n') if d.strip()]
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
                            continue
                    else:
                        debug_print(f"[WARN] No UCSI devices found in {ucsi_base_path}")
                        continue
                else:
                    debug_print(f"[WARN] Could not list UCSI folder contents")
                    continue
            else:
                debug_print(f"[WARN] UCSI folder not found at {ucsi_base_path}")
                continue
        
        # If we get here, none of the paths worked
        debug_print(f"[WARN] No valid UCSI path found in any location")
        return False, "UCSI folder not found in any expected location"
            
    except Exception as e:
        debug_print(f"[WARN] UCSI folder check error: {e}")
        return False, str(e)


def setup_serial_permissions(sudo_password: str) -> bool:
    """Set up serial port permissions for device access using sudo."""
    debug_print("Setting up serial port permissions...")
    
    try:
        # Find all serial ports
        serial_ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        if serial_ports:
            # Add current user to dialout group for serial port access
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


def setup_linux_permissions(sudo_password: str) -> bool:
    """Set up USB and serial permissions for device access using sudo."""
    debug_print("Setting up USB and serial device permissions...")
    
    # Set up serial port permissions first
    setup_serial_permissions(sudo_password)
    
    # Create udev rule for the supported external adapter (VID: 1679)
    udev_rule = 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1679", MODE="0666"\\n'
    rule_path = '/etc/udev/rules.d/99-aardvark.rules'
    
    try:
        # Write udev rule
        result = subprocess.run(
            ['sudo', '-S', 'tee', rule_path],
            input=(sudo_password + '\\n' + udev_rule).encode(),
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


def capture_linux_dmesg_logs() -> Optional[str]:
    """Capture recent dmesg logs related to UCSI for debugging."""
    try:
        result = subprocess.run(
            ['dmesg', '-T'],
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\\n')
            # Filter for UCSI-related messages (last 50)
            ucsi_lines = [line for line in lines if 'ucsi' in line.lower() or 'usb' in line.lower()]
            return '\\n'.join(ucsi_lines[-50:]) if ucsi_lines else "No UCSI-related messages found"
        else:
            return None
    except Exception:
        return None


def execute_ucsi_command_linux(command_hex: str, sudo_password: str, ucsi_path: str) -> Dict[str, Any]:
    """
    Execute UCSI command on Linux via debugfs.
    
    Args:
        command_hex: Hex string of the command (without 0x prefix)
        sudo_password: Sudo password for elevated access
        ucsi_path: Full path to UCSI device (e.g., /sys/kernel/debug/usb/ucsi/USBC000:00)
    
    Returns:
        Dictionary with 'success', 'response', 'dmesg_logs', and optionally 'error'
    """
    debug_print(f"[Linux] Executing UCSI command via sysfs: {command_hex}")
    
    command_file = f'{ucsi_path}/command'
    response_file = f'{ucsi_path}/response'
    
    # Verify files exist
    try:
        cmd_check = subprocess.run(
            ['sudo', '-S', 'test', '-f', command_file],
            input=sudo_password.encode() if isinstance(sudo_password, str) else sudo_password,
            capture_output=True,
            timeout=5
        )
        
        resp_check = subprocess.run(
            ['sudo', '-S', 'test', '-f', response_file],
            input=sudo_password.encode() if isinstance(sudo_password, str) else sudo_password,
            capture_output=True,
            timeout=5
        )
        
        if cmd_check.returncode != 0:
            return {'success': False, 'error': f"Command file not found: {command_file}"}
        
        if resp_check.returncode != 0:
            return {'success': False, 'error': f"Response file not found: {response_file}"}
            
    except Exception as e:
        return {'success': False, 'error': f"Failed to verify UCSI files: {str(e)}"}
    
    try:
        # Ensure password is a string
        sudo_password_str = sudo_password if isinstance(sudo_password, str) else sudo_password.decode()
        
        # Clear dmesg buffer before command
        debug_print(f"[Linux] Clearing dmesg buffer...")
        subprocess.run(
            ['sudo', '-S', 'dmesg', '-C'],
            input=sudo_password_str,
            capture_output=True,
            text=True
        )
        
        # Execute command - try multiple methods
        ucsi_dir = os.path.dirname(command_file)
        
        # Method 1: Standard echo redirection
        combined_cmd = f'cd {ucsi_dir} && echo 0x{command_hex} > command && cat response'
        debug_print(f"[Linux] Attempting Method 1: {combined_cmd}")
        
        result = subprocess.run(
            ['sudo', '-S', 'bash', '-c', combined_cmd],
            input=sudo_password_str,
            capture_output=True,
            timeout=5,
            text=True
        )
        
        if result.returncode != 0:
            debug_print(f"[Linux] Method 1 failed, trying Method 2...")
            combined_cmd = f'cd {ucsi_dir} && echo 0x{command_hex} | sudo tee command > /dev/null && cat response'
            result = subprocess.run(
                ['sudo', '-S', 'bash', '-c', combined_cmd],
                input=sudo_password_str,
                capture_output=True,
                timeout=5,
                text=True
            )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or 'Failed to execute UCSI command'
            debug_print(f"[Linux] Command execution failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'dmesg_logs': capture_linux_dmesg_logs()
            }
        
        hex_response = result.stdout.strip()
        debug_print(f"[Linux] Response (raw): {hex_response}")
        
        # Process response - remove 0x prefix and handle byte order
        if hex_response.startswith('0x') or hex_response.startswith('0X'):
            hex_clean = hex_response[2:]
        else:
            hex_clean = hex_response
        
        # Remove zero padding if present
        if hex_clean.startswith('00000000') and len(hex_clean) > 8:
            debug_print(f"[Linux] Removing zero padding prefix")
            hex_clean = hex_clean[8:]
        
        # Reverse bytes for little-endian format
        byte_pairs = [hex_clean[i:i+2] for i in range(0, len(hex_clean), 2)]
        byte_pairs.reverse()
        hex_response = '0x' + ''.join(byte_pairs)
        debug_print(f"[Linux] Response (byte-reversed): {hex_response}")
        
        return {
            'success': True,
            'response': hex_response,
            'dmesg_logs': capture_linux_dmesg_logs()
        }
        
    except subprocess.TimeoutExpired:
        debug_print("[Linux] Command timeout")
        return {'success': False, 'error': 'Command timeout', 'dmesg_logs': capture_linux_dmesg_logs()}
    except Exception as e:
        debug_print(f"[Linux] Exception: {e}")
        return {'success': False, 'error': str(e), 'dmesg_logs': capture_linux_dmesg_logs()}
