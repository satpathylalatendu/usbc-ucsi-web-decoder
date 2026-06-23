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
Windows UCSI Backend
Handles Windows-specific UCSI operations via UcsiControl.exe and Device Manager.
"""

import os
import sys
import platform
import subprocess
import shutil
from typing import Dict, Any, Optional, Tuple

# Debug flag
DEBUG = os.getenv('DEBUG', '0') == '1'

def debug_print(*args, **kwargs):
    """Print debug message only if DEBUG mode is enabled."""
    if DEBUG:
        print(*args, **kwargs)
        sys.stdout.flush()


def check_windows_ucsi() -> Tuple[bool, str]:
    """
    Check for UCSI device in Windows Device Manager.
    
    Returns:
        (found, info): Boolean indicating if device was found, and device name or error message
    """
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
            
            for line in output.split('\\n'):
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


def get_ucsi_executable() -> Optional[str]:
    """Find UcsiControl.exe in PATH or current directory."""
    # Check if in PATH
    ucsi_path = shutil.which('UcsiControl.exe')
    if ucsi_path:
        return ucsi_path
    
    # Check in current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(current_dir, 'UcsiControl.exe')
    if os.path.exists(local_path):
        return local_path
    
    # Check parent directory
    parent_dir = os.path.dirname(current_dir)
    parent_path = os.path.join(parent_dir, 'UcsiControl.exe')
    if os.path.exists(parent_path):
        return parent_path
    
    # Check workspace root (two levels up from app/backend/)
    root_dir = os.path.dirname(parent_dir)
    root_path = os.path.join(root_dir, 'UcsiControl.exe')
    if os.path.exists(root_path):
        return root_path
    
    return None


def run_ucsi_control(path_to_ucsi: str, args_list: list, timeout: int = 8) -> Dict[str, Any]:
    """Execute UcsiControl.exe with given arguments."""
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


def execute_ucsi_command_windows(command_hex: str) -> Dict[str, Any]:
    """
    Execute UCSI command on Windows via UcsiControl.exe.
    
    Args:
        command_hex: Hex string of the command (without 0x prefix)
    
    Returns:
        Dictionary with 'success', 'response', 'stdout', and optionally 'error'
    """
    debug_print(f"[Windows] Executing UCSI command: {command_hex}")
    
    ucsi_path = get_ucsi_executable()
    if not ucsi_path:
        return {'success': False, 'error': 'UcsiControl.exe not found. Please ensure it is in the PATH or same directory.'}
    
    # Format command: UcsiControl.exe send 0 <hex>
    # For 16-character hex (two DWORDs), split into two 8-character arguments
    if len(command_hex) == 16:
        # Split into LowDW (first 8 chars) and HighDW (last 8 chars)
        low_dw = command_hex[0:8]
        high_dw = command_hex[8:16]
        args = ['send', '0', low_dw, high_dw]
        debug_print(f"[Windows] Using DWORD format: send 0 {low_dw} {high_dw}")
    else:
        args = ['send', '0', command_hex]
    
    result = run_ucsi_control(ucsi_path, args)
    
    if not result.get('ok'):
        return {'success': False, 'error': result.get('error', 'Command execution failed')}
    
    stdout = result.get('stdout', '')
    if 'No UCSI controllers found' in stdout:
        return {'success': False, 'error': 'No UCSI controllers found'}
    
    return {
        'success': True,
        'stdout': stdout,
        'response': extract_hex_from_output(stdout)
    }


def extract_hex_from_output(output: str) -> str:
    """Extract hex response from UcsiControl.exe output."""
    lines = output.split('\\n')
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
            cleaned = line.replace(' ', '').replace('\\t', '')
            if cleaned and all(c in '0123456789ABCDEFabcdef' for c in cleaned):
                hex_lines.append(cleaned)
    
    # If we found hex in MESSAGE_IN section, return it
    if hex_lines:
        return ''.join(hex_lines)
    
    # Fallback: look for any line with hex (old behavior)
    for line in lines:
        line = line.strip()
        if line and not any(skip in line.lower() for skip in ['ucsi', 'command', 'response:', 'controller']):
            cleaned = line.replace(' ', '').replace('\\t', '')
            if cleaned and all(c in '0123456789ABCDEFabcdef' for c in cleaned):
                return cleaned
    
    return ''


def parse_cci_register(cci_text: str) -> Optional[int]:
    """Parse CCI register value and extract ErrorIndicator."""
    try:
        import re
        # First try to find the explicit ErrorIndicator line (most reliable)
        error_line_match = re.search(r'ErrorIndicator:\\s*(\\d+)', cci_text)
        if error_line_match:
            return int(error_line_match.group(1))
        
        # Fallback: Extract from AsUInt32/AsUInt64 value and calculate bit 30
        hex_match = re.search(r'AsUInt(?:32|64):\\s*(?:0x)?([0-9A-Fa-f]{1,16})', cci_text)
        if hex_match:
            cci_value = int(hex_match.group(1), 16)
            # Bit 30 is Error Indicator (per UCSI spec Table 6-2)
            error_indicator = (cci_value >> 30) & 0x01
            return error_indicator
    except:
        pass
    return None


def extract_ucsi_sections(output: str) -> Dict[str, str]:
    """Extract UCSI_CONTROL, UCSI VERSION, and UCSI_CCI sections from output."""
    lines = output.split('\\n')
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
        
        # Skip separator lines and empty lines
        if current_section is not None and stripped and not all(c in '=-_' for c in stripped):
            sections[current_section].append(stripped)
    
    # Convert lists to strings
    result = {}
    for key, section_lines in sections.items():
        if section_lines:
            result[key] = '\\n'.join(section_lines)
    
    return result
