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

from ucsi_commands import *

# Constants for I2C setup
BUS_TIMEOUT = 150 #ms
BIT_RATE = 400

#UCSI ASCII constants
U = 0x55
C = 0x43
S = 0x53
I = 0x49

#CMD and DATA reg
COMMAND_REG = 0x8
DATA_REG = 0x9


INIT_ARRAY_BYTES = 16 #Number of bytes to initialize Array
NUM_BYTES_TRANSMITTED = 10 #Number of transmit data bytes
UCSI_CMD_BYTES = 4 #Number of UCSI command data bytes
DEFAULT_DATA_LENGTH = 0 #Default length is set to 00 in UCSI spec
READ_NUM_BYTES = 64 #Bytes read from PD

# 1: TCP0 ; 2:TCP1
TCPORT_0  = 1
TCPORT_1  = 2


HARD_RESET = 0 #DEFAULT
DATA_RESET = 1
ENABLE = 1
DISABLE = 0

# TI Standard task Response
TASK_COMPLETED_SUCCESSFUL = 0x0
TASK_TIMES_OUT = 0x1
TASK_REJECTED = 0x3
RX_BUFFER_LOCKED = 0x4

