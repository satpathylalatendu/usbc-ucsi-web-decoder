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
Ctypes-based wrapper for aardvark.dll
This works in PyInstaller frozen executables (Windows only)
"""

import sys
import os
import ctypes
import platform
import logging
from ctypes import c_int, c_uint8, c_uint16, c_uint32, POINTER, byref

try:
    from .log_utils import setup_file_logger
except ImportError:
    from log_utils import setup_file_logger

logger = setup_file_logger('aardvark_ctypes', 'aardvark')

# Only load on Windows
if platform.system() != 'Windows':
    AARDVARK_DLL_LOADED = False
    logger.info("Aardvark ctypes wrapper skipped on Linux")
else:
    # Load the DLL
    def load_aardvark_dll():
        """Load aardvark.dll using ctypes (works in PyInstaller)"""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            dll_dir = os.path.join(sys._MEIPASS, 'aardvark')
        else:
            dll_dir = os.path.dirname(os.path.abspath(__file__))
        
        dll_path = os.path.join(dll_dir, 'aardvark.dll')
        
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"aardvark.dll not found at {dll_path}")
        
        return ctypes.CDLL(dll_path)

    # Initialize DLL
    try:
        _aa = load_aardvark_dll()
        AARDVARK_DLL_LOADED = True
    except Exception as e:
        logger.warning(f"Could not load aardvark.dll via ctypes: {e}")
        _aa = None
        AARDVARK_DLL_LOADED = False

# Define Aardvark API functions with ctypes
if AARDVARK_DLL_LOADED:
    # aa_find_devices_ext(int num_devices, u16* devices, int* unique_ids)
    _aa.c_aa_find_devices_ext.argtypes = [c_int, POINTER(c_uint16), POINTER(c_uint32)]
    _aa.c_aa_find_devices_ext.restype = c_int
    
    # aa_open(int port)
    _aa.c_aa_open.argtypes = [c_int]
    _aa.c_aa_open.restype = c_int
    
    # aa_close(Aardvark aardvark)
    _aa.c_aa_close.argtypes = [c_int]
    _aa.c_aa_close.restype = c_int
    
    # aa_configure(Aardvark aardvark, AardvarkConfig config)
    _aa.c_aa_configure.argtypes = [c_int, c_int]
    _aa.c_aa_configure.restype = c_int
    
    # aa_i2c_pullup(Aardvark aardvark, u08 pullup_mask)
    _aa.c_aa_i2c_pullup.argtypes = [c_int, c_int]
    _aa.c_aa_i2c_pullup.restype = c_int
    
    # aa_i2c_bitrate(Aardvark aardvark, int bitrate_khz)
    _aa.c_aa_i2c_bitrate.argtypes = [c_int, c_int]
    _aa.c_aa_i2c_bitrate.restype = c_int
    
    # aa_i2c_bus_timeout(Aardvark aardvark, u16 timeout_ms)
    _aa.c_aa_i2c_bus_timeout.argtypes = [c_int, c_uint16]
    _aa.c_aa_i2c_bus_timeout.restype = c_int
    
    # aa_i2c_write(Aardvark aardvark, u16 slave_addr, AardvarkI2cFlags flags, u16 num_bytes, u08* data_out)
    _aa.c_aa_i2c_write.argtypes = [c_int, c_uint16, c_int, c_uint16, POINTER(c_uint8)]
    _aa.c_aa_i2c_write.restype = c_int
    
    # aa_i2c_read(Aardvark aardvark, u16 slave_addr, AardvarkI2cFlags flags, u16 num_bytes, u08* data_in)
    _aa.c_aa_i2c_read.argtypes = [c_int, c_uint16, c_int, c_uint16, POINTER(c_uint8)]
    _aa.c_aa_i2c_read.restype = c_int
    
    # aa_sleep_ms(u32 milliseconds)
    _aa.c_aa_sleep_ms.argtypes = [c_uint32]
    _aa.c_aa_sleep_ms.restype = c_uint32
    
    # aa_status_string(int status)
    _aa.c_aa_status_string.argtypes = [c_int]
    _aa.c_aa_status_string.restype = ctypes.c_char_p
    
    # aa_i2c_write_ext(Aardvark aardvark, u16 slave_addr, AardvarkI2cFlags flags, u16 num_bytes, u08* data_out, u16* num_written)
    _aa.c_aa_i2c_write_ext.argtypes = [c_int, c_uint16, c_int, c_uint16, POINTER(c_uint8), POINTER(c_uint16)]
    _aa.c_aa_i2c_write_ext.restype = c_int
    
    # aa_i2c_read_ext(Aardvark aardvark, u16 slave_addr, AardvarkI2cFlags flags, u16 num_bytes, u08* data_in, u16* num_read)
    _aa.c_aa_i2c_read_ext.argtypes = [c_int, c_uint16, c_int, c_uint16, POINTER(c_uint8), POINTER(c_uint16)]
    _aa.c_aa_i2c_read_ext.restype = c_int
    
    # aa_version(Aardvark aardvark, AardvarkVersion* version)
    _aa.c_aa_version.argtypes = [c_int, c_int]
    _aa.c_aa_version.restype = c_int

# Python wrapper functions
def aa_find_devices_ext(max_devices=16):
    """Find connected Aardvark devices"""
    if not AARDVARK_DLL_LOADED:
        return []
    
    devices = (c_uint16 * max_devices)()
    unique_ids = (c_uint32 * max_devices)()
    
    num_found = _aa.c_aa_find_devices_ext(max_devices, devices, unique_ids)
    
    if num_found < 0:
        return []
    
    return [(devices[i], unique_ids[i]) for i in range(num_found)]

def aa_open(port):
    """Open Aardvark device on specified port"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_open(port)

def aa_close(handle):
    """Close Aardvark device"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_close(handle)

def aa_configure(handle, config):
    """Configure Aardvark device"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_configure(handle, config)

def aa_i2c_pullup(handle, pullup_mask):
    """Set I2C pullup resistors"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_i2c_pullup(handle, pullup_mask)

def aa_i2c_bitrate(handle, bitrate_khz):
    """Set I2C bitrate"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_i2c_bitrate(handle, bitrate_khz)

def aa_i2c_bus_timeout(handle, timeout_ms):
    """Set I2C bus timeout"""
    if not AARDVARK_DLL_LOADED:
        return -1
    return _aa.c_aa_i2c_bus_timeout(handle, timeout_ms)

def aa_i2c_write(handle, slave_addr, flags, data):
    """Write data to I2C slave (simplified version)"""
    if not AARDVARK_DLL_LOADED:
        return -1
    
    num_bytes = len(data)
    data_array = (c_uint8 * num_bytes)(*data)
    
    result = _aa.c_aa_i2c_write(handle, slave_addr, flags, num_bytes, data_array)
    return result

def aa_i2c_read(handle, slave_addr, flags, num_bytes):
    """Read data from I2C slave (simplified version)"""
    if not AARDVARK_DLL_LOADED:
        return -1, []
    
    data_array = (c_uint8 * num_bytes)()
    result = _aa.c_aa_i2c_read(handle, slave_addr, flags, num_bytes, data_array)
    
    data = [data_array[i] for i in range(num_bytes)] if result >= 0 else []
    return result, data

def aa_sleep_ms(milliseconds):
    """Sleep for specified milliseconds"""
    if not AARDVARK_DLL_LOADED:
        import time
        time.sleep(milliseconds / 1000.0)
        return milliseconds
    return _aa.c_aa_sleep_ms(milliseconds)

def aa_status_string(status):
    """Get status string for error code"""
    if not AARDVARK_DLL_LOADED:
        return f"Error code: {status}"
    try:
        result = _aa.c_aa_status_string(status)
        return result.decode('utf-8') if result else f"Error code: {status}"
    except:
        return f"Error code: {status}"

def aa_i2c_write_ext(handle, slave_addr, flags, data):
    """Write data to I2C slave"""
    if not AARDVARK_DLL_LOADED:
        return -1
    
    num_bytes = len(data)
    data_array = (c_uint8 * num_bytes)(*data)
    num_written = c_uint16()
    
    result = _aa.c_aa_i2c_write_ext(handle, slave_addr, flags, num_bytes, data_array, byref(num_written))
    return result, num_written.value

def aa_i2c_read_ext(handle, slave_addr, flags, num_bytes):
    """Read data from I2C slave"""
    if not AARDVARK_DLL_LOADED:
        return -1, []
    
    data_array = (c_uint8 * num_bytes)()
    num_read = c_uint16()
    
    result = _aa.c_aa_i2c_read_ext(handle, slave_addr, flags, num_bytes, data_array, byref(num_read))
    
    data = [data_array[i] for i in range(num_read.value)]
    return result, data

def aa_version(handle, pullup):
    """Get Aardvark version"""
    if not AARDVARK_DLL_LOADED:
        return 0
    return _aa.c_aa_version(handle, pullup)

# Constants (from aardvark.h)
AA_CONFIG_GPIO_ONLY = 0x00
AA_CONFIG_SPI_GPIO = 0x01
AA_CONFIG_GPIO_I2C = 0x02
AA_CONFIG_SPI_I2C = 0x03
AA_CONFIG_QUERY = 0x80

AA_I2C_NO_FLAGS = 0x00
AA_I2C_10_BIT_ADDR = 0x01
AA_I2C_COMBINED_FMT = 0x02
AA_I2C_NO_STOP = 0x04
AA_I2C_SIZED_READ = 0x10
AA_I2C_SIZED_READ_EXTRA1 = 0x20

AA_I2C_PULLUP_NONE = 0x00
AA_I2C_PULLUP_BOTH = 0x03
AA_I2C_PULLUP_QUERY = 0x80

# Detect_Device function (compatible with aadetect.py)
def Detect_Device():
    """
    Detect Aardvark device (compatible with aadetect.Detect_Device)
    Returns: ("Detected", port) or ("Not detected", -1)
    """
    devices = aa_find_devices_ext()
    
    if not devices:
        logger.info("No Aardvark adapters found.")
        return ("Not detected", -1)
    
    logger.info(f"{len(devices)} device(s) found:")
    for port, unique_id in devices:
        port_value = port & 0xFF
        if port & 0x8000:  # In use
            status = "in-use"
        else:
            status = "avail"
        
        # Format unique ID
        unique_str = f"{(unique_id >> 16) & 0xFFFF:04d}-{unique_id & 0xFFFF:06d}"
        logger.info(f"    port = {port_value}   ({status})  ({unique_str})")
    
    # Return first available port
    for port, unique_id in devices:
        if not (port & 0x8000):  # Not in use
            return ("Detected", port & 0xFF)
    
    # All in use, return first one anyway
    return ("Detected", devices[0][0] & 0xFF)
