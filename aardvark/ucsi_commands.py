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

#UCSI commands Rev: 2.0

UCSI_SPEC_REVISION = 2.0

PPM_RESET = 0x1
CANCEL  = 0x2
CONNECTOR_RESET = 0x3
ACK_CC_CI = 0x4
SET_NOTIFICATION_ENABLE = 0x5
GET_CAPABILITY  = 0x6
GET_CONNECTOR_CAPABILITY = 0x7
SET_CCOM = 0x8
SET_UOR = 0x9
SET_PDM = 0xA  #obsolete
SET_PDR = 0xB
GET_ALTERNATE_MODES = 0xC
GET_CAM_SUPPORTED = 0xD
GET_CURRENT_CAM = 0xE
SET_NEW_CAM = 0xF
GET_PDOS = 0x10
GET_CABLE_PROPERTY = 0x11
GET_CONNECTOR_STATUS = 0x12
GET_ERROR_STATUS = 0x13
SET_POWER_LEVEL = 0x14
GET_PD_MESSAGE = 0x15
GET_ATTENTION_VDO = 0x16
Reserved_Command = 0x17
GET_CAM_CS = 0x18
LPM_FW_UPDATE_REQUEST = 0x19
SECURITY_REQUEST = 0x1A
SET_RETIMER_MODESET_RETIMER_MODE = 0x1B
SET_SINK_PATH = 0x1C
SET_PDOS = 0x1D
READ_POWER_LEVEL = 0x1E
CHUNKING_SUPPORT = 0x1F
