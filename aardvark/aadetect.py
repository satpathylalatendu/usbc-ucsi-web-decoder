#!/usr/bin/env python3
#==========================================================================
# (c) 2004-2019  Total Phase, Inc.
#--------------------------------------------------------------------------
# Project : Aardvark Sample Code
# File    : aadetect.py
#--------------------------------------------------------------------------
# Auto-detection test routine
#--------------------------------------------------------------------------
# Redistribution and use of this file in source and binary forms, with
# or without modification, are permitted.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#==========================================================================

#==========================================================================
# IMPORTS
#==========================================================================
from __future__ import division, with_statement, print_function
import os
import logging

try:
    from .log_utils import setup_file_logger
except ImportError:
    from log_utils import setup_file_logger

# Global debug flag from environment
DEBUG = os.getenv('DEBUG', '0') == '1'

logger = setup_file_logger('aadetect', 'aardvark')

def debug_print(*args, **kwargs):
    """Log debug message only if DEBUG mode is enabled."""
    if DEBUG:
        message = ' '.join(str(arg) for arg in args)
        logger.debug(message)

try:
    from .aardvark_py import *
except ImportError:
    from aardvark_py import *


#==========================================================================
# MAIN PROGRAM
#==========================================================================
def Detect_Device ():
    debug_print("Detecting Aardvark adapters...")
    
    # The functions are already imported at the top via "from .aardvark_py import *"
    # Just check if aa_find_devices_ext is available
    try:
        # Try calling aa_find_devices_ext - if it's not available, this will fail
        (num, ports, unique_ids) = aa_find_devices_ext(16, 16)
    except NameError:
        # Function not available - library not loaded
        return ("Not Detected", -1)
    except Exception as e:
        # Some other error during device detection
        debug_print(f"Error during device detection: {e}")
        return ("Not Detected", -1)

    if num > 0:
        debug_print("%d device(s) found:" % num)

        # Print the information on each device
        for i in range(num):
            port      = ports[i]
            unique_id = unique_ids[i]

            # Determine if the device is in-use
            inuse = "(avail)"
            if (port & AA_PORT_NOT_FREE):
                inuse = "(in-use)"
                port  = port & ~AA_PORT_NOT_FREE

            # Display device port number, in-use status, and serial number
            debug_print("    port = %d   %s  (%04d-%06d)" %
                (port, inuse, unique_id // 1000000, unique_id % 1000000))
            result = "Detected"
            return (result, port)

    else:
        result = "Not Detected"
        return (result, -1)
