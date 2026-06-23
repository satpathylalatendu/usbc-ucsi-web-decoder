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
Aardvark Backend
Wraps the original aardvark_integration module.
"""

import sys
import os

# Add parent directory to path to import original aardvark_integration
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import from aardvark_integration module
try:
    from aardvark import aardvark_integration
    AARDVARK_AVAILABLE = aardvark_integration.AARDVARK_AVAILABLE
    
    # Re-export key functions
    detect_aardvark = aardvark_integration.detect_aardvark_device
    execute_command = aardvark_integration.execute_command_by_name
    scan_i2c_bus = aardvark_integration.scan_i2c_bus
    get_i2c_address_info = aardvark_integration.get_i2c_address_info
    set_ppm_address = aardvark_integration.set_ppm_address
    
except (ImportError, AttributeError) as e:
    AARDVARK_AVAILABLE = False
    
    def detect_aardvark():
        return {'found': False, 'error': 'Aardvark library not available'}
    
    def execute_command(*args, **kwargs):
        return {'ok': False, 'error': 'Aardvark library not available'}
    
    def scan_i2c_bus(*args, **kwargs):
        return {'success': False, 'error': 'Aardvark library not available'}
    
    def get_i2c_address_info():
        return {'error': 'Aardvark library not available'}
    
    def set_ppm_address(*args, **kwargs):
        pass


def execute_ucsi_command_aardvark(command_name: str, port: int = 1):
    """
    Execute UCSI command via Aardvark interface.
    
    Args:
        command_name: Name of the UCSI command (e.g., "GET_CAPABILITY")
        port: Port/connector number (1-4)
    
    Returns:
        Dictionary with 'ok', 'response', 'error_indicator', etc.
    """
    if not AARDVARK_AVAILABLE:
        return {'ok': False, 'error': 'Aardvark library not available'}
    
    return execute_command(command_name, port)


__all__ = [
    'AARDVARK_AVAILABLE',
    'detect_aardvark',
    'execute_command',
    'execute_ucsi_command_aardvark',
    'scan_i2c_bus',
    'get_i2c_address_info',
    'set_ppm_address',
]
