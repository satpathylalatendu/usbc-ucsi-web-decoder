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

from constants import *

######################################################################################
##                                                                                  ##
##                                                                                  ##
##         USER CAN UPDATE BELOW VALUES AS PER REQUIREMENT                          ##
##                                                                                  ##
##                                                                                  ##
##                                                                                  ##
######################################################################################

#PD-EC port address
PORT0_PD_EC_ADDRESS = 0x20
PORT1_PD_EC_ADDRESS = 0x21 


PORT_PD_EC_ADDRESS = PORT1_PD_EC_ADDRESS
TYPE_C_CONNECTOR_NUMBER = TCPORT_1 & 0x7F # Don't change 0x7F part


#User defined inputs for Test cases
RESET_TYPE = HARD_RESET  # or DATA_RESET# TestCase_CONNECTOR_RESET : num of BITS: 1

SINK_PATH = DISABLE#ENABLE # or DISABLE #TestCase_SET_SINK_PATH_user_input :  num of BITS: 1

CC_OPERATION_MODE = 0 # TestCase_SET_CCOM_user_input : num of BITS: 3

USB_OPERATION_ROLE = 0 # TestCase_SET_UOR_user_input : num of BITS: 3

POWER_DIRECTION_ROLE = 0 # TestCase_SET_PDR_user_input : : num of BITS: 3


MESSAGE_OFFSET = 0 # TestCase_GET_PD_MESSAGE_user_input: num of BITS: 8
NUMBER_OF_BYTES = 0 #TestCase_GET_PD_MESSAGE_user_input : num of BITS: 8
RESPONSE_MESSAGE_TYPE = 0 #TestCase_GET_PD_MESSAGE_user_input : num of BITS: 6

RECIPIENT = 00 # TestCase_GET_ALTERNATE_MODES_user_input AND TestCase_GET_PD_MESSAGE_user_input : num of BITS: 3
ALT_MODE_OFFSET = 0 # TestCase_GET_ALTERNATE_MODES_user_input : num of BITS: 8
NUM_ALT_MODE = 0 # TestCase_GET_ALTERNATE_MODES_user_input : num of BITS: 2

ENTER_OR_EXIT = 0 # TestCase_SET_NEW_CAM_user_input : Num of bit:1
NEW_CAM = 0 # TestCase_SET_NEW_CAM_user_input : Num of bits:8
AM_SPECIFIC = 0 # TestCase_SET_NEW_CAM_user_input : Num of bits:32

PARTNER_PDO = 0 # TestCase_GET_PDOS_user_input : nUM OF BIT : 1
PDO_OFFSET = 0 # TestCase_GET_PDOS_user_input : nUM OF BIT : 8
NUMBER_PDOs = 0 # TestCase_GET_PDOS_user_input : nUM OF BITs : 2
SOURCE_OR_SINK_PDOs = 0 # TestCase_GET_PDOS_user_input : nUM OF BIT : 1
SOURCE_CAP_TYPES = 0 # TestCase_GET_PDOS_user_input : nUM OF BIT : 2

NOTIFICATION_ENABLE_BYTE_0 = 0 # TestCase_SET_NOTIFICATION_ENABLE_user_input : 8 bits
NOTIFICATION_ENABLE_BYTE_1 = 0 # TestCase_SET_NOTIFICATION_ENABLE_user_input : 8 bits
NOTIFICATION_ENABLE_BYTE_2 = 0  # TestCase_SET_NOTIFICATION_ENABLE_user_input : 1 bit

SOURCE_or_SINK = 0  #TestCase_SET_POWER_LEVEL_user_input : 1 bit
USB_PD_MAX_POWER = 0  #TestCase_SET_POWER_LEVEL_user_input : 8 bitS
USB_Type_C_CURRENT = 0  #TestCase_SET_POWER_LEVEL_user_input : 3 bitS

RETIMER_NUMBER = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input  : Num of BITS-2
STATE = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input : Num of BITS-3
FUNCTIONAL_MODE = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input: Num of BITS-4
DP_SOURCE_SINK = 0 # TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input: Num of BITS-1
GAIN = 0 # TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input: Num of BITS-8
ORIENTATION = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input : Num of BITS-1
RESERVED_BITS = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input : Num of BITS-4


END_OF_MESSAGE = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input AND TestCase_SECURITY_REQUEST_user_input AND TestCase_LPM_FW_UPDATE_REQUEST_user_input : Num of BITS-1
DATA_INDEX = 0 #TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input AND TestCase_SECURITY_REQUEST_user_input AND TestCase_LPM_FW_UPDATE_REQUEST_user_input: Num of BITS-7
DIRECTION = 0#TestCase_SECURITY_REQUEST_user_input AND TestCase_LPM_FW_UPDATE_REQUEST_user_input : num of BITS : 2


SECURITY_REQUEST_bits = 0 # #TestCase_SECURITY_REQUEST_user_input : num of BITS : 1
AUTH_PROTOCOL_REVISION = 0 #TestCase_SECURITY_REQUEST_user_input : num of BITS : 8
AUTHENTICATION_MESSAGE = 0 #TestCase_SECURITY_REQUEST_user_input : num of BITS : 8


FW_UPDATE_REQUEST = 0 # TestCase_LPM_FW_UPDATE_REQUEST_user_input : num of BITS : 8


CURRENT_ALT_MODE = 0 #TestCase_GET_CAM_CS_user_input: : num of BITS: 8