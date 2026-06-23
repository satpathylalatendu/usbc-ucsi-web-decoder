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

from UCSI_PD_TestCases import *
from History import *
from colorama import Fore, Back, Style
from ucsi_commands import *

######################################################################################
##                                                                                  ##
##                                                                                  ##
##                           MAIN PROGRAM                                           ##
##                                                                                  ##
##                                                                                  ##
##                                                                                  ##
######################################################################################


SW_Version = Get_SW_Version()
print("Framework version is ",SW_Version)
print("UCSI Spec Version is ", UCSI_SPEC_REVISION)

print("Type-C_0 port address is %x" %PORT0_PD_EC_ADDRESS)
print("Type-C_1 port address is %x" %PORT1_PD_EC_ADDRESS)

print("Slave Address is %x" %PORT_PD_EC_ADDRESS)


print("\nStart of Test cases execution\n")

#TestCase_PPM_RESET()
#TestCase_CANCEL()
#TestCase_CONNECTOR_RESET()
#TestCase_ACK_CC_CI() # Need to look into this
#TestCase_SET_NOTIFICATION_ENABLE()
TestCase_GET_CAPABILITY()
#TestCase_GET_CONNECTOR_CAPABILITY()
#TestCase_SET_CCOM()
#TestCase_SET_UOR()
#TestCase_SET_PDR()
#TestCase_GET_ALTERNATE_MODES()
#TestCase_GET_CAM_SUPPORTED()
#TestCase_GET_CURRENT_CAM()
#TestCase_SET_NEW_CAM()
#TestCase_GET_PDOS()
#TestCase_GET_CABLE_PROPERTY()
TestCase_GET_CONNECTOR_STATUS()
#TestCase_GET_ERROR_STATUS()
#TestCase_SET_POWER_LEVEL()
#TestCase_GET_PD_MESSAGE()
#TestCase_GET_ATTENTION_VDO()
#TestCase_GET_CAM_CS()
#TestCase_LPM_FW_UPDATE_REQUEST()
#TestCase_SECURITY_REQUEST()
#TestCase_SET_RETIMER_MODESET_RETIMER_MODE()
TestCase_SET_SINK_PATH()

print("End of Test cases execution\n")