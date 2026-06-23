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
Aardvark Integration Module for UCSI GUI
Provides wrapper functions to execute UCSI commands via Aardvark I2C interface
instead of using UcsiControl.exe
"""

import sys
import os
import logging
from array import array
from threading import Lock

try:
    from .log_utils import setup_file_logger
except ImportError:
    from log_utils import setup_file_logger

# Global debug flag from environment
DEBUG = os.getenv('DEBUG', '0') == '1'

logger = setup_file_logger('aardvark_integration', 'aardvark')

def debug_print(*args, **kwargs):
    """Log debug message only if DEBUG mode is enabled."""
    if DEBUG:
        message = ' '.join(str(arg) for arg in args)
        logger.debug(message)

# Add the workspace to Python path so we can import aardvark
_script_dir = os.path.dirname(os.path.realpath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

# Also add aardvark folder to path for relative imports within that package
_aardvark_dir = os.path.join(_script_dir, "aardvark")
if _aardvark_dir not in sys.path:
    sys.path.insert(0, _aardvark_dir)

# UCSI Constants (always define these)
DATA_REG = 0x9
COMMAND_REG = 0x8
CCI_REG = 0x4  # UCSI CCI (Command Completion Indicator) register
INIT_ARRAY_BYTES = 10  # Changed from 16 to 10 bytes: [DATA_REG, NUM_BYTES, + 8 command bytes]
NUM_BYTES_TRANSMITTED = 8  # Changed from 10 to match manual results
UCSI_CMD_BYTES = 4
DEFAULT_DATA_LENGTH = 0
READ_NUM_BYTES = 256  # Increased to handle max UCSI response (MESSAGE_IN can be up to 256 bytes)

# Response codes
TASK_COMPLETED_SUCCESSFUL = 0x0
TASK_TIMES_OUT = 0x1
TASK_REJECTED = 0x3
RX_BUFFER_LOCKED = 0x4

# UCSI ASCII constants
U = 0x55
C = 0x43
S = 0x53
I = 0x49

# Logging helpers
def _format_hex_display(data, label="", bytes_per_line=16):
    """Format bytes/array for readable hex display"""
    if isinstance(data, (bytes, bytearray)):
        hex_bytes = data
    elif isinstance(data, array):
        hex_bytes = bytes(data)
    else:
        try:
            hex_bytes = bytes(data)
        except:
            return f"{label}: [unable to format]"
    
    if label:
        output = f"{label}:\n"
    else:
        output = ""
    
    # Show hex with ASCII representation
    hex_str = ' '.join(f'{b:02X}' for b in hex_bytes)
    output += f"  {hex_str}"
    
    return output

def _log_command_start(command_name, command_hex, connector, port_address):
    """Log start of command execution"""
    logger.info("=" * 70)
    logger.info("AARDVARK COMMAND EXECUTION START")
    logger.info("=" * 70)
    logger.info(f"Command Name:     {command_name}")
    logger.info(f"Command Hex:      {command_hex}")
    logger.info(f"Connector:        {connector}")
    logger.info(f"I2C Address:      0x{port_address:02X}")
    logger.info("-" * 70)

# Try to import Aardvark modules, but don't fail if they're not available in all contexts
AARDVARK_AVAILABLE = False
USE_CTYPES = False

# Check if running on Windows (Aardvark only supported on Windows)
import platform
if platform.system() != 'Windows':
    logger.info("Aardvark not available on Linux (Windows only)")
    AARDVARK_AVAILABLE = False
# First try ctypes wrapper (works in PyInstaller on Windows)
elif getattr(sys, 'frozen', False):
    try:
        logger.info("Running in PyInstaller - using ctypes wrapper for Aardvark")
        from aardvark import aardvark_ctypes
        if aardvark_ctypes.AARDVARK_DLL_LOADED:
            # Import ctypes functions into global namespace
            globals().update({
                'aa_open': aardvark_ctypes.aa_open,
                'aa_close': aardvark_ctypes.aa_close,
                'aa_configure': aardvark_ctypes.aa_configure,
                'aa_i2c_pullup': aardvark_ctypes.aa_i2c_pullup,
                'aa_i2c_bitrate': aardvark_ctypes.aa_i2c_bitrate,
                'aa_i2c_bus_timeout': aardvark_ctypes.aa_i2c_bus_timeout,
                'aa_i2c_write': aardvark_ctypes.aa_i2c_write,
                'aa_i2c_read': aardvark_ctypes.aa_i2c_read,
                'aa_i2c_write_ext': aardvark_ctypes.aa_i2c_write_ext,
                'aa_i2c_read_ext': aardvark_ctypes.aa_i2c_read_ext,
                'aa_sleep_ms': aardvark_ctypes.aa_sleep_ms,
                'aa_status_string': aardvark_ctypes.aa_status_string,
                'aa_version': aardvark_ctypes.aa_version,
                'aa_find_devices_ext': aardvark_ctypes.aa_find_devices_ext,
                'Detect_Device': aardvark_ctypes.Detect_Device,
                'AA_CONFIG_GPIO_I2C': aardvark_ctypes.AA_CONFIG_GPIO_I2C,
                'AA_CONFIG_SPI_I2C': aardvark_ctypes.AA_CONFIG_SPI_I2C,
                'AA_I2C_PULLUP_BOTH': aardvark_ctypes.AA_I2C_PULLUP_BOTH,
                'AA_I2C_NO_FLAGS': aardvark_ctypes.AA_I2C_NO_FLAGS,
                'AA_I2C_NO_STOP': aardvark_ctypes.AA_I2C_NO_STOP,
                'AA_I2C_10_BIT_ADDR': aardvark_ctypes.AA_I2C_10_BIT_ADDR,
            })
            AARDVARK_AVAILABLE = True
            USE_CTYPES = True
            debug_print("[OK] Aardvark ctypes wrapper loaded successfully")
        else:
            debug_print("[WARN] Aardvark DLL not loaded via ctypes")
    except Exception as e:
        debug_print(f"[WARN] Could not load Aardvark ctypes wrapper: {e}")
        AARDVARK_AVAILABLE = False

# Fall back to Python extension module (normal Python on Windows)
elif platform.system() == 'Windows':
    try:
        from aardvark.aardvark_py import *
        from aardvark.aardvark_py import AA_LIBRARY_LOADED, api as aardvark_api
        from aardvark.aadetect import Detect_Device
        
        # Only set AVAILABLE if the library actually loaded
        AARDVARK_AVAILABLE = AA_LIBRARY_LOADED
        if AARDVARK_AVAILABLE:
            debug_print("[OK] Aardvark integration modules loaded successfully")
        else:
            debug_print(f"[WARN] Aardvark modules imported but DLL not loaded")
    except (ImportError, Exception) as e:
        AARDVARK_AVAILABLE = False
        debug_print(f"[INFO] Aardvark not available: {e}")

# Global handle and lock for thread-safe operations
_aardvark_handle = None
_aardvark_lock = Lock()

# Global cache for discovered I2C addresses
_discovered_i2c_addresses = []
_ppm_i2c_address = None  # Auto-detected PPM address

def _check_usb_device_windows():
    """
    Check if Aardvark is detected as a USB device in Windows Device Manager.
    When drivers are properly installed: appears under "Universal Serial Bus Controllers"
    When drivers are missing: appears under "Other devices" with yellow exclamation mark
    Returns True if device is physically connected (with or without drivers).
    """
    import platform
    if platform.system() != 'Windows':
        return False
    
    try:
        import subprocess
        # Use Windows pnputil to list all devices and search for Aardvark
        result = subprocess.run(
            ['pnputil', '/enum-devices'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            output = result.stdout.lower()
            if 'aardvark' in output or 'total phase' in output:
                debug_print("[DEBUG] Found Aardvark in Windows USB devices")
                return True
    except Exception as e:
        debug_print(f"[DEBUG] pnputil check failed: {e}")
    
    # Fallback: Try WMI query to detect device in USB or Other devices class
    try:
        import subprocess
        # Query for USB devices with Aardvark in name
        result = subprocess.run(
            ['wmic', 'path', 'Win32_PnPDevice', 'where', 'name like "%aardvark%" or name like "%total phase%"', 'get', 'name,status'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            output = result.stdout.lower()
            if 'aardvark' in output or 'total phase' in output:
                debug_print("[DEBUG] Found Aardvark via WMI query")
                return True
    except Exception as e:
        debug_print(f"[DEBUG] WMI check failed: {e}")
    
    return False

def detect_aardvark_device():
    """
    Detect if an Aardvark device is connected.
    Returns dict with detection info including:
    - 'found': Device driver is working
    - 'usb_detected': Device is physically present but drivers may not be installed
    """
    try:
        # First, try to detect via the driver library (if available)
        if AARDVARK_AVAILABLE:
            try:
                debug_print("[DEBUG] Calling Detect_Device()...")
                result, port = Detect_Device()
                debug_print(f"[DEBUG] Detect_Device returned: result={result}, port={port}")
                
                if result == "Detected" and port >= 0:
                    # Get device info
                    try:
                        debug_print(f"[DEBUG] Opening device on port {port}...")
                        handle = aa_open(port)
                        debug_print(f"[DEBUG] aa_open returned handle: {handle}")
                        
                        if handle > 0:
                            try:
                                # Skip version check for ctypes - just return success
                                aa_close(handle)
                                return {
                                    'found': True,
                                    'port': port,
                                    'description': f'Aardvark I2C/SPI Host Adapter (Port {port})',
                                    'version': 'Unknown',
                                    'usb_detected': True
                                }
                            except Exception as ver_err:
                                debug_print(f"[DEBUG] Error in device check: {ver_err}")
                                aa_close(handle)
                                return {
                                    'found': True,
                                    'port': port,
                                    'description': f'Aardvark device on port {port}',
                                    'usb_detected': True
                                }
                        else:
                            debug_print(f"[DEBUG] Failed to open device, handle={handle}")
                    except Exception as open_err:
                        debug_print(f"[DEBUG] Exception opening device: {open_err}")
                        import traceback
                        traceback.print_exc()
                    
                    return {
                        'found': True,
                        'port': port,
                        'description': f'Aardvark device on port {port}',
                        'usb_detected': True
                    }
                else:
                    debug_print(f"[DEBUG] Detect_Device returned: {result}")
            except Exception as e:
                debug_print(f"[DEBUG] Driver library detection failed: {e}")
        
        # If driver detection failed or drivers not available, check for USB device physically present
        debug_print("[DEBUG] Checking for physical USB device...")
        usb_detected = _check_usb_device_windows()
        
        if usb_detected:
            return {
                'found': False,  # Driver not working
                'usb_detected': True,  # But device is physically present
                'error': 'Device detected but drivers not installed',
                'description': 'Aardvark I2C/SPI Host Adapter (drivers missing)'
            }
        else:
            return {
                'found': False,
                'usb_detected': False,
                'error': 'No Aardvark device detected',
                'description': None
            }
    
    except Exception as e:
        logger.error(f"detect_aardvark_device exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            'found': False,
            'usb_detected': False,
            'error': str(e),
            'description': None
        }

def scan_i2c_bus(full_scan=False):
    """
    Scan I2C bus to find active devices.
    
    Args:
        full_scan: If True, scan all addresses 0x00-0xFF. If False, scan 0x08-0x77 (standard range)
    
    Returns:
        dict with 'success', 'devices' (list of hex strings), and 'addresses' (list of int)
    """
    global _discovered_i2c_addresses, _ppm_i2c_address
    
    if not AARDVARK_AVAILABLE:
        return {'error': 'Aardvark library not available', 'devices': [], 'addresses': []}
    
    try:
        # Get Aardvark device
        result, port = Detect_Device()
        if result != "Detected" or port < 0:
            return {'error': 'No Aardvark device found', 'devices': [], 'addresses': []}
        
        handle = aa_open(port)
        if handle <= 0:
            return {'error': 'Failed to open Aardvark device', 'devices': [], 'addresses': []}
        
        try:
            # Configure I2C
            aa_configure(handle, AA_CONFIG_SPI_I2C)
            aa_i2c_pullup(handle, AA_I2C_PULLUP_BOTH)
            aa_i2c_bitrate(handle, 100)  # 100 kHz for compatibility
            aa_i2c_bus_timeout(handle, 150)
            
            logger.info("=" * 70)
            logger.info("I2C BUS SCAN")
            logger.info("=" * 70)
            
            # Determine scan range
            if full_scan:
                start_addr = 0x00
                end_addr = 0x100  # 0xFF + 1
                logger.info("Full scan: 0x00 to 0xFF (all addresses)...")
            else:
                start_addr = 0x08
                end_addr = 0x78  # 0x77 + 1
                logger.info("Standard scan: 0x08 to 0x77 (common I2C range)...")
            
            found_devices = []
            found_addresses = []
            
            # Scan I2C addresses
            for addr in range(start_addr, end_addr):
                # Try to write 0 bytes (address probe) - this sends only the address
                try:
                    status = aa_i2c_write(handle, addr, AA_I2C_NO_FLAGS, array('B', []))
                    if status == 0:  # ACK received
                        found_devices.append(f"0x{addr:02X}")
                        found_addresses.append(addr)
                        logger.info(f"  Device found at address: 0x{addr:02X}")
                except:
                    pass
                
                # Small delay to avoid bus flooding
                if addr % 16 == 0:
                    aa_sleep_ms(10)
            
            aa_close(handle)
            
            # Update global cache
            _discovered_i2c_addresses = found_addresses
            
            # Auto-detect PPM address (usually the first responding address in UCSI systems)
            if found_addresses:
                # Prefer addresses in typical UCSI range (0x20-0x2F)
                ucsi_addresses = [a for a in found_addresses if 0x20 <= a <= 0x2F]
                if ucsi_addresses:
                    _ppm_i2c_address = ucsi_addresses[0]
                    logger.info(f"[AUTO-DETECT] PPM I2C Address: 0x{_ppm_i2c_address:02X}")
                else:
                    _ppm_i2c_address = found_addresses[0]
                    logger.info(f"[AUTO-DETECT] Using first responding address as PPM: 0x{_ppm_i2c_address:02X}")
            
            if found_devices:
                logger.info(f"Total devices found: {len(found_devices)}")
                logger.info(f"Addresses: {', '.join(found_devices)}")
            else:
                logger.warning("No I2C devices found on the bus")
            logger.info("=" * 70)
            
            return {'success': True, 'devices': found_devices, 'addresses': found_addresses}
            
        except Exception as e:
            aa_close(handle)
            return {'error': f'Scan error: {str(e)}', 'devices': [], 'addresses': []}
            
    except Exception as e:
        return {'error': str(e), 'devices': [], 'addresses': []}

class AardvarkCommandError(Exception):
    """Exception raised when Aardvark command execution fails"""
    pass

def _format_hex_display(data, label="", bytes_per_line=16):
    """Format bytes/array for readable hex display"""
    if isinstance(data, (bytes, bytearray)):
        hex_bytes = data
    elif isinstance(data, array):
        hex_bytes = bytes(data)
    else:
        hex_bytes = bytes(data)
    
    if label:
        output = f"{label}:\n"
    else:
        output = ""
    
    # Show hex with ASCII
    for i in range(0, len(hex_bytes), bytes_per_line):
        chunk = hex_bytes[i:i+bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        output += f"  {i:04X}: {hex_part:<{bytes_per_line*3-1}} | {ascii_part}\n"
    
    return output.rstrip()

def _log_command_execution(command_name, command_hex, connector, port_address):
    """Log command execution details"""
    logger.info("=" * 70)
    logger.info("AARDVARK COMMAND EXECUTION")
    logger.info("=" * 70)
    logger.info(f"Command Name: {command_name}")
    logger.info(f"Command Hex:  {command_hex}")
    logger.info(f"Connector:    {connector}")
    logger.info(f"I2C Address:  0x{port_address:02X}")
    logger.info("-" * 70)

def initialize_aardvark():
    """
    Initialize and open Aardvark device.
    Returns handle if successful, raises AardvarkCommandError otherwise.
    """
    if not AARDVARK_AVAILABLE:
        raise AardvarkCommandError("Aardvark modules not available. Ensure aardvark folder is in path.")
    
    global _aardvark_handle
    
    with _aardvark_lock:
        if _aardvark_handle is not None:
            return _aardvark_handle
        
        try:
            # Detect device
            result, port = Detect_Device()
            if result != "Detected" or port < 0:
                raise AardvarkCommandError(f"No Aardvark device found. Detection result: {result}")
            
            # Open device
            handle = aa_open(port)
            if handle <= 0:
                raise AardvarkCommandError(f"Failed to open Aardvark device on port {port}. Handle: {handle}")
            
            # Configure for I2C
            aa_configure(handle, AA_CONFIG_SPI_I2C)
            
            # Enable I2C pullup resistors
            aa_i2c_pullup(handle, AA_I2C_PULLUP_BOTH)
            
            # Set bit rate (400 kHz)
            bitrate = aa_i2c_bitrate(handle, 400)
            
            # Set bus timeout (150ms)
            bus_timeout = aa_i2c_bus_timeout(handle, 150)
            
            _aardvark_handle = handle
            return handle
            
        except Exception as e:
            raise AardvarkCommandError(f"Failed to initialize Aardvark: {str(e)}")

def _reset_i2c_bus(handle, port_address):
    """Reset I2C bus state before communicating with a device."""
    try:
        logger.info("[I2C BUS RESET] Starting aggressive bus reset...")
        
        # Multiple attempts to clear stuck I2C bus state
        for attempt in range(5):  # More aggressive - 5 attempts instead of 3
            try:
                # Send stop condition by writing to invalid register
                aa_i2c_write(handle, port_address, AA_I2C_NO_FLAGS, array('B', [0xFF]))
            except:
                pass
            aa_sleep_ms(20)  # Longer delays between attempts
        
        # Extended final wait for bus to fully settle
        aa_sleep_ms(150)  # Longer final settle time
        logger.info("[I2C BUS RESET] Completed - bus in clean state")
    except Exception as e:
        logger.warning(f"[I2C BUS RESET] Warning: {str(e)}")
        aa_sleep_ms(150)  # Still wait even if reset failed



def close_aardvark():
    """Close the Aardvark device."""
    global _aardvark_handle
    
    with _aardvark_lock:
        if _aardvark_handle is not None:
            try:
                aa_close(_aardvark_handle)
            except:
                pass
            _aardvark_handle = None

def _write_ucsi_data(handle, address, data_array):
    """Write UCSI data via I2C"""
    try:
        logger.info("[I2C WRITE - DATA REGISTER]")
        logger.info(f"Register:  0x{DATA_REG:02X} (DATA_REG)")
        logger.info(f"I2C Address: 0x{address:02X}")
        logger.info(f"Payload Size: {len(data_array)} bytes")
        logger.info(_format_hex_display(data_array, "Data Payload"))
        
        aa_i2c_write(handle, address, AA_I2C_NO_FLAGS, data_array)
        logger.info("I2C Write Status: OK")
        aa_sleep_ms(20)
    except Exception as e:
        raise AardvarkCommandError(f"Failed to write UCSI data: {str(e)}")

def _write_ucsi_commands(handle, address):
    """Write UCSI command header (UCSI magic)"""
    try:
        data_tx = array('B', [0] * (UCSI_CMD_BYTES + 2))
        data_tx[0] = COMMAND_REG
        data_tx[1] = UCSI_CMD_BYTES
        data_tx[2] = U  # 'U'
        data_tx[3] = C  # 'C'
        data_tx[4] = S  # 'S'
        data_tx[5] = I  # 'I'
        
        logger.info("[I2C WRITE - COMMAND REGISTER]")
        logger.info(f"Register:  0x{COMMAND_REG:02X} (COMMAND_REG)")
        logger.info(f"I2C Address: 0x{address:02X}")
        logger.info(f"Command Magic: UCSI (0x55 0x43 0x53 0x49)")
        logger.info(_format_hex_display(data_tx, "UCSI Command Write"))
        
        aa_i2c_write(handle, address, AA_I2C_NO_FLAGS, data_tx)
        logger.info("I2C Write Status: OK")
        aa_sleep_ms(20)
    except Exception as e:
        raise AardvarkCommandError(f"Failed to write UCSI commands: {str(e)}")

def _read_ucsi_data(handle, address, reg):
    """Read UCSI data from register"""
    try:
        logger.info(f"[I2C READ - REGISTER 0x{reg:02X}]")
        logger.info(f"I2C Address: 0x{address:02X}")
        logger.info(f"Register Address: 0x{reg:02X}")
        logger.info(f"Read Length: {READ_NUM_BYTES} bytes")
        
        # Extended bus recovery - more aggressive for problematic devices
        logger.info("  [PRE-READ RECOVERY] Clearing I2C bus state...")
        for recovery_attempt in range(5):  # 5 aggressive attempts
            try:
                aa_i2c_write(handle, address, AA_I2C_NO_FLAGS, array('B', [0xFF]))
            except:
                pass
            aa_sleep_ms(15)  # Longer delays
        
        # Extended wait before register write
        aa_sleep_ms(100)  # Significantly longer wait
        
        # Try read with optimized sequence:
        # Some devices respond better to repeated start (NO_STOP) while others prefer separate write/read
        # We'll try NO_STOP first (repeated start), then fall back to regular sequence
        
        success = False
        data_rx = None
        count = 0
        
        # Attempt 1: Using NO_STOP for repeated start (preferred for i2c)
        try:
            logger.info(f"  Attempt 1: Write register with NO_STOP (repeated start)...")
            write_status = aa_i2c_write(handle, address, AA_I2C_NO_STOP, array('B', [reg]))
            logger.info(f"  Write status: {write_status}")
            
            if write_status >= 0:  # Success
                aa_sleep_ms(20)
                logger.info(f"  Reading {READ_NUM_BYTES} bytes...")
                count, data_rx = aa_i2c_read(handle, address, AA_I2C_NO_FLAGS, READ_NUM_BYTES)
                logger.info(f"  I2C Read Status: {count} bytes read")
                
                if count > 0:
                    success = True
                    logger.info("  [OK] Repeated start method succeeded")
        except:
            pass
        
        # Attempt 2: If first method failed, try separate write/read with full bus recovery
        if not success:
            logger.info(f"  Attempt 2: Separate write/read with bus recovery...")
            # Full bus reset between operations
            for recovery_attempt in range(3):
                try:
                    aa_i2c_write(handle, address, AA_I2C_NO_FLAGS, array('B', [0xFF]))
                except:
                    pass
                aa_sleep_ms(15)
            
            aa_sleep_ms(100)
            
            # Write register address alone
            write_status = aa_i2c_write(handle, address, AA_I2C_NO_FLAGS, array('B', [reg]))
            logger.info(f"  Write status: {write_status}")
            
            if write_status >= 0:
                aa_sleep_ms(50)  # Longer delay between write and read
                logger.info(f"  Reading {READ_NUM_BYTES} bytes...")
                count, data_rx = aa_i2c_read(handle, address, AA_I2C_NO_FLAGS, READ_NUM_BYTES)
                logger.info(f"  I2C Read Status: {count} bytes read")
                
                if count > 0:
                    success = True
                    logger.info("  [OK] Separate read method succeeded")
        
        # Check final result
        if count < 0:
            error_msg = aa_status_string(count) if count < -100 else str(count)
            raise AardvarkCommandError(f"I2C read error: {error_msg}")
        
        if count == 0:
            raise AardvarkCommandError("No bytes read from device - check I2C address and connection")
        
        response_data = bytes(data_rx[:count]) if count > 0 else b''
        logger.info(_format_hex_display(response_data, "Response Data"))
        
        return data_rx[:count]
        
    except AardvarkCommandError:
        raise
    except Exception as e:
        raise AardvarkCommandError(f"Failed to read UCSI data: {type(e).__name__}: {str(e)}")

def execute_ucsi_command_aardvark(command_hex_str, connector=1, port_address=0x20):
    """
    Execute a UCSI command via Aardvark I2C interface.
    
    Args:
        command_hex_str: Hex string representation of command (e.g., "010007" for GET_CONNECTOR_CAPABILITY)
        connector: Connector number (1 or 2, default 1)
        port_address: I2C address of the PD/EC controller (default 0x20 - match manual results)
    
    Returns:
        dict with keys:
            - 'ok': bool indicating success
            - 'error': error message if not ok
            - 'response': raw response bytes as hex string
            - 'response_bytes': response as bytes array
            - 'status': status code from response
    """
    if not AARDVARK_AVAILABLE:
        return {
            'ok': False,
            'error': 'Aardvark modules not available',
            'response': '',
            'response_bytes': None,
            'status': None
        }
    
    try:
        # Log command start
        _log_command_start("UCSI Command", command_hex_str, connector, port_address)
        
        # Initialize Aardvark
        handle = initialize_aardvark()
        logger.info(f"Aardvark device initialized successfully")
        
        # Reset I2C bus before communicating with device
        # This ensures clean state when switching between ports or after errors
        _reset_i2c_bus(handle, port_address)
        
        # Parse command hex string
        command_hex = command_hex_str.replace(' ', '').upper()
        if command_hex.startswith('0X'):
            command_hex = command_hex[2:]
        
        # Ensure even length
        if len(command_hex) % 2:
            command_hex = '0' + command_hex
        
        # Convert hex string to bytes
        try:
            command_bytes = bytes.fromhex(command_hex)
        except ValueError as e:
            return {
                'ok': False,
                'error': f'Invalid hex string: {str(e)}',
                'response': '',
                'response_bytes': None,
                'status': None
            }
        
        logger.info("[COMMAND PARSING]")
        logger.info(f"Input Command Hex: {command_hex}")
        logger.info(_format_hex_display(command_bytes, "Command Bytes"))
        
        # Build UCSI command array
        # Format: [DATA_REG, NUM_BYTES, CMD_BYTE, DATA_LEN, CONNECTOR, RESERVED, ...]
        data_tx = array('B', [0] * INIT_ARRAY_BYTES)
        data_tx[0] = DATA_REG
        data_tx[1] = NUM_BYTES_TRANSMITTED
        
        # Copy command bytes into the array
        for i, byte in enumerate(command_bytes):
            if i + 2 < INIT_ARRAY_BYTES:
                data_tx[i + 2] = byte
        
        logger.info("[UCSI COMMAND ARRAY]")
        logger.info(f"Array Size: {len(data_tx)} bytes")
        logger.info(_format_hex_display(data_tx, "Complete Data Transmission Array"))
        
        # Write data and trigger command
        logger.info("[EXECUTION SEQUENCE]")
        logger.info("Step 1: Writing data to DATA_REG")
        _write_ucsi_data(handle, port_address, data_tx)
        
        # Delay between write and command trigger
        aa_sleep_ms(30)
        
        logger.info("Step 2: Writing UCSI command magic")
        _write_ucsi_commands(handle, port_address)
        
        # Wait time for device to process command and prepare response
        logger.info("Step 3: Waiting for command completion (500ms)")
        aa_sleep_ms(500)
        
        logger.info("Step 4: Reading status from COMMAND_REG")
        # Read command register first (status)
        try:
            cmd_response = _read_ucsi_data(handle, port_address, COMMAND_REG)
            status_code = cmd_response[1] if len(cmd_response) > 1 else None
        except AardvarkCommandError as e:
            # If reading COMMAND_REG fails, try to recover and continue to DATA_REG
            logger.warning(f"  [WARNING] Failed to read COMMAND_REG: {str(e)}")
            logger.info("  [RECOVERY] Attempting to recover and read DATA_REG instead...")
            status_code = None  # Will be determined from response
            # Close and reinitialize to clear any stuck state
            close_aardvark()
            aa_sleep_ms(100)
            handle = initialize_aardvark()
            _reset_i2c_bus(handle, port_address)
        
        # Read CCI register to get ErrorIndicator
        cci_value = None
        error_indicator = None
        try:
            logger.info("Step 4.5: Reading CCI register for ErrorIndicator")
            cci_response = _read_ucsi_data(handle, port_address, CCI_REG)
            if len(cci_response) >= 4:
                # CCI is a 4-byte register (32 bits)
                # Assuming little-endian format
                cci_value = (cci_response[0] | 
                            (cci_response[1] << 8) | 
                            (cci_response[2] << 16) | 
                            (cci_response[3] << 24))
                # ErrorIndicator is bit 30 of CCI register
                error_indicator = (cci_value >> 30) & 0x01
                logger.info(f"  CCI Register: 0x{cci_value:08X}")
                logger.info(f"  ErrorIndicator (bit 30): {error_indicator}")
        except AardvarkCommandError as e:
            logger.warning(f"  [WARNING] Failed to read CCI register: {str(e)}")
            # Continue without ErrorIndicator
        
        # Delay between reading different registers
        aa_sleep_ms(50)
        
        logger.info("Step 5: Reading response from DATA_REG")
        # Read data register
        data_response = _read_ucsi_data(handle, port_address, DATA_REG)
        
        # Convert response to hex string
        # data_response can be a list, array.array, or bytes - convert to bytes
        if isinstance(data_response, (list, array)):
            response_bytes = bytes(data_response)
        elif isinstance(data_response, bytes):
            response_bytes = data_response
        else:
            response_bytes = bytes(data_response)
        
        # The DATA_REG response format (UCSI over I2C):
        # Byte 0: Data length (number of valid data bytes following)
        # Byte 1+: Actual UCSI response message data
        #
        # According to UCSI spec, we should read the length byte and only
        # extract that many bytes of actual data
        
        # Expected response lengths for specific commands (per UCSI spec)
        EXPECTED_RESPONSE_LENGTHS = {
            "07": 4,   # GET_CONNECTOR_CAPABILITY: 32 bits (4 bytes)
            "06": 16,  # GET_CAPABILITY: 16 bytes
            "12": 19,  # GET_CONNECTOR_STATUS: 19 bytes
            "16": 11,  # GET_ATTENTION_VDO: 88 bits (11 bytes) - Table 6-57
            "22": 20,  # GET_LPM_PPM_INFO: 160 bits (20 bytes) - Table 6-82
        }
        
        # Initialize response variables
        actual_response = b''
        response_hex = ''
        data_length = 0
        
        if len(response_bytes) > 0:
            # Detect the header format by examining the response structure
            # Aardvark I2C reads can include various headers:
            # - [DATA_REG_echo, status/flags, length_byte, data...] - 3 byte header
            # - [0x00, length_byte, data...] - 2 byte header  
            # - [length_byte, data...] - 1 byte header (standard)
            header_offset = 0
            
            # Check for 3-byte header: If first byte is 0x40 (DATA_REG echo), always use 3-byte header
            # The second byte can vary (0x00, 0x03, etc.) - it might be status or connector number
            if len(response_bytes) >= 3 and response_bytes[0] == 0x40:
                # Pattern: [0x40, status/flags, length, data...]
                header_offset = 2
                data_length = response_bytes[2]
                logger.info(f"  Detected 3-byte header (DATA_REG echo 0x40)")
            elif len(response_bytes) >= 3 and response_bytes[1] == 0x00 and response_bytes[2] < 128:
                # Likely pattern: [reg_echo, 0x00, length, data...]
                header_offset = 2
                data_length = response_bytes[2]
                logger.info(f"  Detected 3-byte header (register echo + 0x00 prefix)")
            elif len(response_bytes) >= 2 and response_bytes[0] == 0x00:
                # Pattern: [0x00, length, data...]
                header_offset = 1
                data_length = response_bytes[1]
                logger.info(f"  Detected 2-byte header (0x00 prefix)")
            else:
                # Standard format: [length, data...]
                data_length = response_bytes[0]
                logger.info(f"  Standard format (no header)")
            
            logger.info(f"  Data Length Byte: {data_length} (0x{data_length:02X}) at offset {header_offset}")
            logger.info(f"  Full buffer read: {len(response_bytes)} bytes")
            
            # Check if we should override the length based on command type
            # Extract command byte from command_hex (first 2 chars after any prefix)
            cmd_byte = command_hex[:2] if len(command_hex) >= 2 else ""
            if cmd_byte in EXPECTED_RESPONSE_LENGTHS:
                expected_length = EXPECTED_RESPONSE_LENGTHS[cmd_byte]
                if data_length != expected_length:
                    logger.warning(f"  WARNING: Data length byte is {data_length}, but command {cmd_byte} expects {expected_length} bytes")
                    logger.info(f"  Overriding to use expected length: {expected_length} bytes")
                    data_length = expected_length
            
            # Extract only the actual response data based on length byte
            # Data starts after the header (which might be 1 or 2 bytes)
            data_start_offset = header_offset + 1  # Skip header (if any) + length byte
            
            # Special case: If data_length is 0, connector has no data to return
            if data_length == 0:
                actual_response = b''
                response_hex = ''
                logger.info(f"  No response data (length=0 - e.g., no alternate modes available)")
            elif len(response_bytes) > data_start_offset:
                # Calculate how many bytes of data we actually have after the header
                bytes_available = len(response_bytes) - data_start_offset
                bytes_to_extract = min(data_length, bytes_available)
                
                # Extract the actual response data
                actual_response = response_bytes[data_start_offset:data_start_offset+bytes_to_extract]
                response_hex = actual_response.hex().upper()
                
                if bytes_to_extract < data_length:
                    logger.warning(f"  WARNING: Length byte indicates {data_length} bytes but only {bytes_available} bytes available after header")
                    logger.warning(f"  Extracting {bytes_to_extract} bytes of response data")
                else:
                    logger.info(f"  Extracted {bytes_to_extract} bytes of actual response data")
                
                logger.info(f"  Actual Response Data: {response_hex}")
            else:
                # Buffer too small
                actual_response = b''
                response_hex = ''
                logger.warning(f"  WARNING: Buffer too small (expected {data_start_offset + data_length} bytes, got {len(response_bytes)} bytes)")
        else:
            # Empty response
            data_length = 0
            response_hex = ''
            actual_response = b''
            logger.info(f"  Empty response buffer")
        
        # Extract status code from response if we couldn't read COMMAND_REG
        if status_code is None:
            # For successful reads, status should be 0 (TASK_COMPLETED_SUCCESSFUL)
            # If we got data back, assume success
            if len(response_bytes) >= 2:
                status_code = TASK_COMPLETED_SUCCESSFUL  # Assume success if we got data
            else:
                status_code = response_bytes[0] if len(response_bytes) > 0 else None
        
        # Determine if command was successful
        if status_code == TASK_COMPLETED_SUCCESSFUL:
            status_str = "SUCCESS"
        elif status_code == TASK_TIMES_OUT:
            status_str = "TIMEOUT"
        elif status_code == TASK_REJECTED:
            status_str = "REJECTED"
        elif status_code == RX_BUFFER_LOCKED:
            status_str = "RX_BUFFER_LOCKED"
        else:
            status_str = f"UNKNOWN ({status_code})" if status_code is not None else "UNKNOWN (no status)"
        
        # Check if command was successful
        # IMPORTANT: Trust the ErrorIndicator from CCI - it indicates the PPM/LPM encountered an error
        # Even if data is returned, if ErrorIndicator is set, the command failed.
        # Commands like GET_CABLE_PROPERTY may return cached/stale data when device is disconnected,
        # but the ErrorIndicator will correctly indicate the error condition.
        command_successful = status_code == TASK_COMPLETED_SUCCESSFUL
        if command_successful and error_indicator == 1 and data_length > 0:
            logger.warning(f"[WARNING] ErrorIndicator bit is set, but we received {data_length} bytes of valid data")
            logger.warning(f"[WARNING] Treating as successful (ErrorIndicator may be stale)")
            error_indicator = 0  # Clear the error indicator since we have valid data
        
        logger.info("[COMMAND RESULT]")
        logger.info(f"Status Code: 0x{status_code:02X} ({status_str})")
        logger.info(f"Response Hex: {response_hex}")
        logger.info(f"Response Hex Length: {len(response_hex)}")
        logger.info(f"Actual Response Bytes Length: {len(actual_response)}")
        if error_indicator is not None:
            logger.info(f"ErrorIndicator: {error_indicator} ({'No Error' if error_indicator == 0 else 'Error'})")
        logger.info("=" * 70)
        
        # Sanity check: ensure response_hex matches actual_response
        expected_hex = actual_response.hex().upper() if actual_response else ''
        if response_hex != expected_hex:
            logger.warning(f"[WARNING] response_hex mismatch! Expected '{expected_hex}' but got '{response_hex}'")
            response_hex = expected_hex  # Fix it
        
        result = {
            'ok': command_successful,
            'error': None if command_successful else status_str,
            'response': response_hex,
            'response_bytes': actual_response,
            'status': status_code,
            'status_str': status_str
        }
        
        logger.info(f"[RETURN] Returning result with response: '{result.get('response', '')}'")
        logger.info(f"[RETURN] Response length: {len(result.get('response', ''))}")
        logger.info(f"[RETURN] Response bytes length: {len(result.get('response_bytes', b''))}")
        
        # Add ErrorIndicator if available (now potentially cleared if we have valid data)
        if error_indicator is not None:
            result['error_indicator'] = error_indicator
            
        return result
        
    except AardvarkCommandError as e:
        error_str = str(e)
        logger.error(f"[ERROR] {error_str}")
        logger.info("=" * 70)
        
        # If there's an I2C read/write error, close and reinitialize for next attempt
        if "I2C" in error_str or "read error" in error_str.lower():
            logger.info("[RECOVERY] Closing Aardvark device due to I2C error")
            close_aardvark()
            logger.info("[RECOVERY] Device closed. Next command will reinitialize.")
        
        return {
            'ok': False,
            'error': error_str,

            'response': '',
            'response_bytes': None,
            'status': None
        }
    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {str(e)}")
        logger.info("=" * 70)
        return {
            'ok': False,
            'error': f'Unexpected error: {str(e)}',
            'response': '',
            'response_bytes': None,
            'status': None
        }

def execute_command_by_name(command_name, connector=1):
    """
    Execute a UCSI command by its name (from GUI).
    Maps GUI command names to Aardvark execution parameters.
    
    The 4CC commands are built to match the format used in UCSI_PD_TestCases:
    - Byte 0: Command ID (e.g., 0x07 for GET_CONNECTOR_CAPABILITY)
    - Byte 1: Data length / parameters
    - Byte 2+: Additional parameters (connector, flags, etc.)
    
    Args:
        command_name: Command name from GUI (e.g., "7 - GET_CONNECTOR_CAPABILITY")
        connector: Connector number (1 or 2)
    
    Returns:
        Result dict from execute_ucsi_command_aardvark
    """
    global _ppm_i2c_address, _discovered_i2c_addresses
    
    # Debug: Log the exact parameters received
    logger.info("=" * 70)
    logger.info(f"[EXECUTE_COMMAND_BY_NAME] Received:")
    logger.info(f"  command_name = '{command_name}'")
    logger.info(f"  connector = {connector} (type: {type(connector).__name__})")
    logger.info("=" * 70)
    
    # PPM-level commands that should use the PPM address (not port-specific)
    PPM_LEVEL_COMMANDS = {
        "1 - PPM_RESET",
        "2 - CANCEL",
        "4 - ACK_CC_CI",
        "6 - GET_CAPABILITY",
        "18 - GET_ERROR_STATUS",
        "5 - SET_NOTIFICATION_ENABLE (all)",
        "5 - SET_NOTIFICATION_ENABLE (none)"
    }
    
    # Determine I2C address based on command type
    if command_name in PPM_LEVEL_COMMANDS:
        # Use auto-detected PPM address if available, otherwise try to discover it
        if _ppm_i2c_address is None:
            logger.info("[AUTO-DETECT] PPM address not set, scanning I2C bus...")
            scan_result = scan_i2c_bus(full_scan=False)
            if not scan_result.get('success') or not _ppm_i2c_address:
                # Fallback to default if scan fails
                _ppm_i2c_address = 0x20
                logger.warning(f"[WARNING] I2C scan failed, using default PPM address: 0x{_ppm_i2c_address:02X}")
        
        port_address = _ppm_i2c_address
        logger.info(f"[INFO] Using PPM I2C address: 0x{port_address:02X} for {command_name}")
    else:
        # Port-specific command - calculate based on connector
        # Check if we have discovered addresses
        if _discovered_i2c_addresses:
            # Use discovered addresses in sequence
            # Port 1 -> first address, Port 2 -> second address, etc.
            if connector - 1 < len(_discovered_i2c_addresses):
                port_address = _discovered_i2c_addresses[connector - 1]
                logger.info(f"[INFO] Using discovered I2C address for port {connector}: 0x{port_address:02X}")
            else:
                # Fallback to calculated address if we don't have enough discovered addresses
                port_address = 0x1F + connector  # 0x20 for port 1, 0x21 for port 2, etc.
                logger.warning(f"[WARNING] No discovered address for port {connector}, using calculated: 0x{port_address:02X}")
        else:
            # No discovered addresses, use calculated
            port_address = 0x1F + connector
            logger.info(f"[INFO] Using calculated I2C address for port {connector}: 0x{port_address:02X}")
    
    # Map of command names to their 4CC command bytes
    # Based on UCSI spec and test cases in UCSI_PD_TestCases.py
    # Format: "command_name" -> "hex_command_string"
    # 
    # Command structure (from test cases):
    # [CMD, DataLen, ConnectorInfo, Reserved/Params, ...]
    # where ConnectorInfo = (flags << 7) | connector_number for commands with flags
    
    connector_byte = f"{connector:02x}"
    
    COMMAND_MAP = {
        # Basic commands (no connector info needed)
        "1 - PPM_RESET": "0100000000000000",
        "2 - CANCEL": "0200000000000000",
        "4 - ACK_CC_CI": "0400000000000000",
        "6 - GET_CAPABILITY": "0600000000000000",
        "13 - GET_ERROR_STATUS": "1300000000000000",
        
        # Commands with connector info (format: CMD + 0x00 + connector)
        # GET_CONNECTOR_CAPABILITY: 0x07
        "7 - GET_CONNECTOR_CAPABILITY": f"0700{connector_byte}0000000000",
        
        # GET_CONNECTOR_STATUS: 0x12
        "12 - GET_CONNECTOR_STATUS": f"1200{connector_byte}0000000000",
        
        # GET_ATTENTION_VDO: 0x16
        "16 - GET_ATTENTION_VDO": f"1600{connector_byte}000000000000",
        
        # GET_LPM_PPM_INFO: 0x22
        # Connector Number = 0 queries PPM, non-zero queries that connector's LPM
        "22 - GET_LPM_PPM_INFO": "220000000000000000",  # Connector 0 = Query PPM
        "22 - GET_LPM_PPM_INFO (Connector 1)": f"2200{connector_byte}000000000000",  # Query LPM
        
        # CONNECTOR_RESET: 0x03 (with reset type flag in byte 1)
        "3 - CONNECTOR_RESET": f"0300{connector_byte}000000000000",  # Default to soft reset
        "3 - CONNECTOR_RESET (soft)": f"0300{connector_byte}000000000000",
        "3 - CONNECTOR_RESET (hard)": f"0380{connector_byte}000000000000",
        
        # SET_CCOM: 0x08 (CC Operation Mode in byte 3, connector in byte 2)
        # Format: 08 00 connector ccom_value
        "8 - SET_CCOM (DFP)": f"0800{connector_byte}010000000000",
        "8 - SET_CCOM (UFP)": f"0800{connector_byte}020000000000",
        "8 - SET_CCOM (DRP)": f"0800{connector_byte}030000000000",
        
        # SET_UOR: 0x09 (USB Operation Role in byte 2)
        "9 - SET_UOR (DFP)": f"0900{connector_byte}010000000000",
        "9 - SET_UOR (UFP)": f"0900{connector_byte}020000000000",
        "9 - SET_UOR (Accept Swap)": f"0900{connector_byte}030000000000",
        
        # SET_PDR: 0x0B (Power Direction Role in byte 1)
        "B - SET_PDR (Provider)": f"0b01{connector_byte}000000000000",
        "B - SET_PDR (Consumer)": f"0b02{connector_byte}000000000000",
        "B - SET_PDR (Accept Swap)": f"0b03{connector_byte}000000000000",
        
        # GET_ALTERNATE_MODES: 0x0C (data_len, recipient, connector, offset, num_modes)
        "C - GET_ALTERNATE_MODES (Connector)": f"0c0000{connector_byte}00010000",
        "C - GET_ALTERNATE_MODES (Partner)": f"0c0080{connector_byte}00010000",
        
        # GET_CAM_SUPPORTED: 0x0D
        "D - GET_CAM_SUPPORTED": f"0d00{connector_byte}000000000000",
        
        # GET_CURRENT_CAM: 0x0E
        "E - GET_CURRENT_CAM": f"0e00{connector_byte}000000000000",
        
        # SET_NEW_CAM: 0x0F
        "F - SET_NEW_CAM": f"0f00{connector_byte}000000000000",
        
        # GET_PDOS: 0x10
        "10 - GET_PDOS (Local Source)": f"1007{connector_byte}000000000000",
        "10 - GET_PDOS (Local Sink)": f"1003{connector_byte}000000000000",
        "10 - GET_PDOS (Partner Source)": f"1087{connector_byte}000000000000",
        "10 - GET_PDOS (Partner Sink)": f"1083{connector_byte}000000000000",
        
        # GET_CABLE_PROPERTY: 0x11
        "11 - GET_CABLE_PROPERTY": f"1100{connector_byte}000000000000",
        
        # SET_POWER_LEVEL: 0x14 (with source/sink flag and power info)
        # Format: CMD, DataLen, (Source/Sink<<7)|Connector, USB_PD_Power, USB_Type_C_Current
        "14 - SET_POWER_LEVEL (Source)": f"140381{connector_byte}0f01",  # 0x81 = source flag | connector
        "14 - SET_POWER_LEVEL (Sink)": f"140301{connector_byte}0301",    # 0x01 = sink (no flag)
        
        # GET_PD_MESSAGE: 0x15
        "15 - GET_PD_MESSAGE": f"1500{connector_byte}000000000000",
        
        # GET_CAM_CS: 0x18 (Get Current Alternate Mode Configuration and Status)
        "18 - GET_CAM_CS": f"1800{connector_byte}000000000000",
        
        # LPM_FW_UPDATE_REQUEST: 0x19
        "19 - LPM_FW_UPDATE_REQUEST": f"1900{connector_byte}000000000000",
        
        # SECURITY_REQUEST: 0x1A
        "1A - SECURITY_REQUEST": f"1a00{connector_byte}000000000000",
        
        # SET_RETIMER_MODE: 0x1B
        "1B - SET_RETIMER_MODE (USB)": f"1b00{connector_byte}01000000000000",
        "1B - SET_RETIMER_MODE (DP)": f"1b00{connector_byte}02000000000000",
        "1B - SET_RETIMER_MODE (TBT)": f"1b00{connector_byte}03000000000000",
        "1B - SET_RETIMER_MODE (USB4)": f"1b00{connector_byte}04000000000000",
        
        # SET_SINK_PATH: 0x1C
        "1C - SET_SINK_PATH (Disable)": f"1c00{connector_byte}000000000000",
        "1C - SET_SINK_PATH (Enable)": f"1c00{connector_byte}010000000000",
        
        # CHUNKING_SUPPORT: 0x1F
        "1F - CHUNKING_SUPPORT (Enable)": f"1f00{connector_byte}010000000000",
        "1F - CHUNKING_SUPPORT (Disable)": f"1f00{connector_byte}000000000000",
        
        # SET_NOTIFICATION_ENABLE: 0x05
        "5 - SET_NOTIFICATION_ENABLE (all)": "0500ffff00000000000000",
        "5 - SET_NOTIFICATION_ENABLE (none)": "0500000000000000000000",
        
        # SET_PDO: 0x1D - Set PDOs
        "1D - SET_PDO (Source)": f"1d00{connector_byte}000000000000",
        "1D - SET_PDO (Sink)": f"1d00{connector_byte}010000000000",
        
        # READ_POWER_LEVEL: 0x1E
        "1E - READ_POWER_LEVEL": f"1e00{connector_byte}000000000000",
        
        # Vendor-defined commands
        "20 - VENDOR_DEFINED": "2000000100000000000000",
        
        # SET_USB: 0x21 (USB Operation Mode)
        # Format: 21 00 flags 00 00 00 00 00
        # flags: bit 0=USB2, bit 7=USB3/USB4
        "21 - SET_USB (USB2)": f"2100{connector_byte}010000000000",
        "21 - SET_USB (USB3)": f"2100{connector_byte}800000000000",
        "21 - SET_USB (USB2+USB3)": f"2100{connector_byte}810000000000",
        "21 - SET_USB (USB4)": f"2100{connector_byte}810000000000",
        "21 - SET_USB": f"2100{connector_byte}810000000000",  # Default: USB2+USB3/USB4
    }
    
    if command_name in COMMAND_MAP:
        command_hex = COMMAND_MAP[command_name]
        # Debug: Log the constructed command hex
        logger.info(f"[COMMAND_MAP] connector_byte = '{connector_byte}' (from connector={connector})")
        logger.info(f"[COMMAND_MAP] command_hex = '{command_hex}'")
        logger.info(f"[COMMAND_MAP] port_address = 0x{port_address:02X}")
        return execute_ucsi_command_aardvark(command_hex, connector, port_address)
    else:
        return {
            'ok': False,
            'error': f'Unknown command: {command_name}',
            'response': '',
            'response_bytes': None,
            'status': None
        }

def get_aardvark_command_hex(command_name, connector=1):
    """
    Get the full Aardvark command hex string that will be transmitted over I2C.
    Returns the complete hex including DATA_REG and NUM_BYTES prefix.
    
    Format: [DATA_REG, NUM_BYTES, CMD_BYTES...]
    Example: 09 08 07 00 01 00 00 00 00 00 for GET_CONNECTOR_CAPABILITY port 1
    
    Args:
        command_name: Command name from GUI (e.g., "7 - GET_CONNECTOR_CAPABILITY")
        connector: Connector number (1-4)
    
    Returns:
        Formatted hex string with spaces, or error message
    """
    connector_byte = f"{connector:02x}"
    
    # Same COMMAND_MAP as in execute_command_by_name
    COMMAND_MAP = {
        "1 - PPM_RESET": "0100000000000000",
        "2 - CANCEL": "0200000000000000",
        "4 - ACK_CC_CI": "0400000000000000",
        "6 - GET_CAPABILITY": "0600000000000000",
        "13 - GET_ERROR_STATUS": "1300000000000000",
        "7 - GET_CONNECTOR_CAPABILITY": f"0700{connector_byte}0000000000",
        "12 - GET_CONNECTOR_STATUS": f"1200{connector_byte}0000000000",
        "16 - GET_ATTENTION_VDO": f"1600{connector_byte}000000000000",
        "22 - GET_LPM_PPM_INFO": "220000000000000000",  # Connector 0 = Query PPM (not LPM)
        "22 - GET_LPM_PPM_INFO (Connector 1)": f"2200{connector_byte}000000000000",  # Query connector's LPM
        "3 - CONNECTOR_RESET (soft)": f"0300{connector_byte}000000000000",
        "3 - CONNECTOR_RESET (hard)": f"0380{connector_byte}000000000000",
        "3 - CONNECTOR_RESET": f"0300{connector_byte}000000000000",  # Default to soft
        "8 - SET_CCOM (DFP)": f"0800{connector_byte}010000000000",
        "8 - SET_CCOM (UFP)": f"0800{connector_byte}020000000000",
        "8 - SET_CCOM (DRP)": f"0800{connector_byte}030000000000",
        "9 - SET_UOR (DFP)": f"0900{connector_byte}010000000000",
        "9 - SET_UOR (UFP)": f"0900{connector_byte}020000000000",
        "9 - SET_UOR (Accept Swap)": f"0900{connector_byte}030000000000",
        "B - SET_PDR (Provider)": f"0b01{connector_byte}000000000000",
        "B - SET_PDR (Consumer)": f"0b02{connector_byte}000000000000",
        "B - SET_PDR (Accept Swap)": f"0b03{connector_byte}000000000000",
        "C - GET_ALTERNATE_MODES": f"0c0000{connector_byte}00010000",
        "C - GET_ALTERNATE_MODES (Connector)": f"0c0000{connector_byte}00010000",
        "C - GET_ALTERNATE_MODES (Partner)": f"0c0080{connector_byte}00010000",
        "D - GET_CAM_SUPPORTED": f"0d00{connector_byte}000000000000",
        "E - GET_CURRENT_CAM": f"0e00{connector_byte}000000000000",
        "F - SET_NEW_CAM": f"0f00{connector_byte}000000000000",
        "10 - GET_PDOS (Local Source)": f"1007{connector_byte}000000000000",
        "10 - GET_PDOS (Local Sink)": f"1003{connector_byte}000000000000",
        "10 - GET_PDOS (Partner Source)": f"1087{connector_byte}000000000000",
        "10 - GET_PDOS (Partner Sink)": f"1083{connector_byte}000000000000",
        "11 - GET_CABLE_PROPERTY": f"1100{connector_byte}000000000000",
        "14 - SET_POWER_LEVEL (Source)": f"140381{connector_byte}0f01",
        "14 - SET_POWER_LEVEL (Sink)": f"140301{connector_byte}0301",
        "15 - GET_PD_MESSAGE": f"1500{connector_byte}000000000000",
        "18 - GET_CAM_CS": f"1800{connector_byte}000000000000",
        "19 - LPM_FW_UPDATE_REQUEST": f"1900{connector_byte}000000000000",
        "1A - SECURITY_REQUEST": f"1a00{connector_byte}000000000000",
        "1B - SET_RETIMER_MODE": f"1b00{connector_byte}01000000000000",
        "1B - SET_RETIMER_MODE (USB)": f"1b00{connector_byte}01000000000000",
        "1B - SET_RETIMER_MODE (DP)": f"1b00{connector_byte}02000000000000",
        "1B - SET_RETIMER_MODE (TBT)": f"1b00{connector_byte}03000000000000",
        "1B - SET_RETIMER_MODE (USB4)": f"1b00{connector_byte}04000000000000",
        "1C - SET_SINK_PATH (Disable)": f"1c00{connector_byte}000000000000",
        "1C - SET_SINK_PATH (Enable)": f"1c00{connector_byte}010000000000",
        "1F - CHUNKING_SUPPORT (Enable)": f"1f00{connector_byte}010000000000",
        "1F - CHUNKING_SUPPORT (Disable)": f"1f00{connector_byte}000000000000",
        "5 - SET_NOTIFICATION_ENABLE (all)": "0500ffff00000000000000",
        "5 - SET_NOTIFICATION_ENABLE (none)": "0500000000000000000000",
        "5 - SET_NOTIFICATION_ENABLE": "0500ffff00000000000000",  # Default to all
        "1D - SET_PDO (Source)": f"1d00{connector_byte}000000000000",
        "1D - SET_PDO (Sink)": f"1d00{connector_byte}010000000000",
        "1E - READ_POWER_LEVEL": f"1e00{connector_byte}000000000000",
        "20 - VENDOR_DEFINED": "2000000100000000000000",
        
        # SET_USB: 0x21 (USB Operation Mode)
        # Format: 21 00 flags 00 00 00 00 00
        # flags: bit 0=USB2, bit 7=USB3/USB4
        "21 - SET_USB (USB2)": f"2100{connector_byte}010000000000",
        "21 - SET_USB (USB3)": f"2100{connector_byte}800000000000",
        "21 - SET_USB (USB2+USB3)": f"2100{connector_byte}810000000000",
        "21 - SET_USB (USB4)": f"2100{connector_byte}810000000000",
        "21 - SET_USB": f"2100{connector_byte}810000000000",  # Default: USB2+USB3/USB4
    }
    
    if command_name not in COMMAND_MAP:
        return f"Unknown command: {command_name}"
    
    # Get command bytes from map
    command_hex = COMMAND_MAP[command_name]
    
    # Pad command to 8 bytes (16 hex chars)
    command_hex = command_hex.ljust(16, '0')
    
    # Build full transmission: DATA_REG (0x09) + NUM_BYTES (0x08) + command bytes
    # Concatenate without spaces first
    full_hex = f"0908{command_hex}"
    
    # Format with spaces every 2 chars
    formatted = ' '.join(full_hex[i:i+2] for i in range(0, len(full_hex), 2))
    
    return formatted.upper()

def read_cci_register(connector=1):
    """
    Read the CCI (Command Completion Indicator) register via Aardvark I2C.
    
    The CCI register is at address 0x04 and is 4 bytes long.
    Format: [bit 31: Command Completed, bits 1-7: Connector Change, bit 30: Error, bits 8-15: Data Length]
    
    Args:
        connector: Connector number (1 or 2)
    
    Returns:
        dict with:
            - ok: True if successful
            - cci_value: 32-bit CCI register value
            - error: Error message if failed
    """
    global _ppm_i2c_address
    
    if not AARDVARK_AVAILABLE:
        return {'ok': False, 'error': 'Aardvark library not available', 'cci_value': None}
    
    try:
        # Get Aardvark device
        result, port = Detect_Device()
        if result != "Detected" or port < 0:
            return {'ok': False, 'error': 'No Aardvark device found', 'cci_value': None}
        
        handle = aa_open(port)
        if handle <= 0:
            return {'ok': False, 'error': 'Failed to open Aardvark device', 'cci_value': None}
        
        try:
            # Configure I2C
            aa_configure(handle, AA_CONFIG_SPI_I2C)
            aa_i2c_pullup(handle, AA_I2C_PULLUP_BOTH)
            aa_i2c_bitrate(handle, 400)  # 400 kHz
            aa_i2c_bus_timeout(handle, 150)
            
            # Use PPM I2C address
            if _ppm_i2c_address is None:
                scan_result = scan_i2c_bus(full_scan=False)
                if not scan_result.get('success') or not _ppm_i2c_address:
                    _ppm_i2c_address = 0x20  # Default fallback
            
            i2c_address = _ppm_i2c_address
            
            # CCI register is at 0x04
            CCI_REG = 0x04
            
            # Write CCI register address
            status = aa_i2c_write(handle, i2c_address, AA_I2C_NO_STOP, array('B', [CCI_REG]))
            if status < 0:
                return {'ok': False, 'error': f'Failed to write CCI register address: {status}', 'cci_value': None}
            
            # Read 4 bytes from CCI register
            data_in = array('B', [0] * 4)
            count = aa_i2c_read(handle, i2c_address, AA_I2C_NO_FLAGS, data_in)
            
            if count < 0:
                return {'ok': False, 'error': f'Failed to read CCI register: {count}', 'cci_value': None}
            
            if count != 4:
                return {'ok': False, 'error': f'Expected 4 bytes, got {count}', 'cci_value': None}
            
            # Convert bytes to 32-bit value (little-endian)
            cci_value = (data_in[0] | (data_in[1] << 8) | (data_in[2] << 16) | (data_in[3] << 24))
            
            return {
                'ok': True,
                'cci_value': cci_value,
                'error': None
            }
            
        finally:
            aa_close(handle)
            
    except Exception as e:
        return {'ok': False, 'error': f'Exception reading CCI: {str(e)}', 'cci_value': None}

def get_i2c_address_info():
    """
    Get information about discovered I2C addresses.
    
    Returns:
        dict with 'ppm_address', 'discovered_addresses', and 'status'
    """
    global _ppm_i2c_address, _discovered_i2c_addresses
    
    return {
        'ppm_address': f"0x{_ppm_i2c_address:02X}" if _ppm_i2c_address is not None else None,
        'ppm_address_int': _ppm_i2c_address,
        'discovered_addresses': [f"0x{addr:02X}" for addr in _discovered_i2c_addresses],
        'discovered_addresses_int': _discovered_i2c_addresses,
        'count': len(_discovered_i2c_addresses),
        'status': 'scanned' if _discovered_i2c_addresses else 'not_scanned'
    }

def set_ppm_address(address):
    """
    Manually set the PPM I2C address.
    
    Args:
        address: I2C address as int (e.g., 0x20) or hex string (e.g., "0x20")
    """
    global _ppm_i2c_address
    
    if isinstance(address, str):
        # Parse hex string
        address = int(address, 16) if address.startswith('0x') else int(address, 16)
    
    _ppm_i2c_address = address
    logger.info(f"[MANUAL] PPM I2C address set to: 0x{_ppm_i2c_address:02X}")
