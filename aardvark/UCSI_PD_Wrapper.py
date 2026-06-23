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

#==========================================================================
# IMPORTS
#==========================================================================

from __future__ import division, with_statement, print_function
import sys
import os
import logging
from aardvark_py import *
from aadetect import *
from constants import *
from ucsi_commands import *
from aardvark_interface import *

try:
    from .log_utils import setup_file_logger
except ImportError:
    from log_utils import setup_file_logger

logger = setup_file_logger('ucsi_pd_wrapper', 'aardvark')



#UCSI command "Get capability" example"
#Write: 09 03 07 00 01
#Write: 08 04 55 43 53 49
#Read 08
#Read 09



def Write_UCSI_Data_PD(handle, PD_Address,Data):
    logger.info("Transmitted data is (Decimal Format) " + str(Data))
    aa_i2c_write(handle, PD_Address, AA_I2C_NO_FLAGS, Data)
    aa_sleep_ms(10)


def Write_UCSI_Commands_PD(handle, PD_Address):
    #write the address and data
    #
    data_Tx_ucsi = array('B', [ 0 for i in range(UCSI_CMD_BYTES+2) ])
    #data_out_ucsi = [COMMAND_REG, 4, U, C, S, I]
    data_Tx_ucsi[0] = COMMAND_REG
    data_Tx_ucsi[1] = UCSI_CMD_BYTES
    data_Tx_ucsi[2] = U
    data_Tx_ucsi[3] = C
    data_Tx_ucsi[4] = S
    data_Tx_ucsi[5] = I
    logger.info("UCSI data is (Decimal Format) " + str(data_Tx_ucsi))
    aa_i2c_write(handle, PD_Address, AA_I2C_NO_FLAGS, data_Tx_ucsi)
    aa_sleep_ms(10)


def Read_UCSI_Data_PD(handle, PD_Address, reg):
    # Write the address
    aa_i2c_write(handle, PD_Address, AA_I2C_NO_STOP, array('B', [reg]))
    length = READ_NUM_BYTES


    (count, data_Rx) = aa_i2c_read(handle, PD_Address, AA_I2C_NO_FLAGS, length)
    
    if (count < 0):
        logger.error("error: %s" % aa_status_string(count))
        return
    elif (count == 0):
        logger.error("error: no bytes read")
        logger.error("  are you sure you have the right slave address?")
        return
    elif (count != length):
        logger.warning("error: read %d bytes (expected %d)" % (count, length))

    if (reg == DATA_REG):
        logger.info("Length of Return Data bytes are " + str(count))
 
    # Dump the data to the screen
        data_hex = " ".join("%x" % data_Rx[i] for i in range(count) if reg == DATA_REG)
        logger.info("Data read from device (Hex Format): " + data_hex)
    return (data_Rx)














