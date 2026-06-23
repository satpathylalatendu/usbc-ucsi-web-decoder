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

import os
import sys
import logging
from aardvark_py import *
from aadetect import *
from constants import *

try:
    from .log_utils import setup_file_logger
except ImportError:
    from log_utils import setup_file_logger

logger = setup_file_logger('aardvark_interface', 'aardvark')

#Aardvark interface function to detect and configure connected Aardvark device 
def aardvark_interface ():
   
    port = -1
    (result, port) = Detect_Device()
    logger.info("Port is " + str(port))
   
    if (result != "Detected"):
        logger.error("No Device Found: Please attach device")
        sys.exit()
        
      
    if(port >= 0):
        handle = aa_open(port)
    else :
        logger.error("Handle is N/A")
        logger.error("Unable to open Aardvark")
        sys.exit()
    
    #Ensure I2C is enabled
    aa_configure(handle, AA_CONFIG_SPI_I2C)

    # Enable the I2C bus pullup resistors (2.2k resistors).
    # This command is only effective on v2.0 hardware or greater.
    # The pullup resistors on the v1.02 hardware are enabled by default.
    aa_i2c_pullup(handle, AA_I2C_PULLUP_BOTH)

    #Target power??

    #Set Bit rate
    bitrate = aa_i2c_bitrate(handle, BIT_RATE)
    logger.info("bitrate set to %d kHz " % bitrate)


    # Set the bus lock timeout
    bus_timeout = aa_i2c_bus_timeout(handle, BUS_TIMEOUT)
    logger.info("Bus lock timeout set to %d ms" % bus_timeout)
    return (handle)

