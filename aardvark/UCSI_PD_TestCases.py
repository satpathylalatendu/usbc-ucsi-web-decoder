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

from aardvark_py import *
from aadetect import *
from constants import *
from User_Inputs import *
from ucsi_commands import *
from aardvark_interface import *
from UCSI_PD_Wrapper import *



#Add test case functions for execution
def TestCase_PPM_RESET():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = PPM_RESET #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    
    print("End of TestCase_PPM_RESET")
    print("\n")
    
    # Close the device
    aa_close(handle)

def TestCase_CANCEL():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = CANCEL #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_CANCEL") 
    print("\n")       
    # Close the device
    aa_close(handle)

def TestCase_CONNECTOR_RESET():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = CONNECTOR_RESET #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = (RESET_TYPE << 7) | TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_CONNECTOR_RESET")  
    print("\n")
    # Close the device
    aa_close(handle)   

#TODO: OPM will set bit in this command? Do we need it for PD? If yes, what would be the value?
def TestCase_ACK_CC_CI():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = ACK_CC_CI #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)

    print("End of TestCase_ACK_CC_CI_user_input") 
    print("\n") 
    # Close the device
    aa_close(handle)   


def TestCase_SET_NOTIFICATION_ENABLE():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_NOTIFICATION_ENABLE #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = NOTIFICATION_ENABLE_BYTE_0 & 0xFF #Notification enable : 8 bits (17 bits total)
    data_Tx[5] = NOTIFICATION_ENABLE_BYTE_1 & 0xFF #Notification enable : 8 bits(17 bits)
    data_Tx[6] = NOTIFICATION_ENABLE_BYTE_2 & 0x01 #Notification enable : 1bit (17 bits total) + reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_SET_NOTIFICATION_ENABLE_user_input")  
    print("\n")        
    # Close the device
    aa_close(handle)   

def TestCase_GET_CAPABILITY():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CAPABILITY #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            Disabled_State_Support = 0
            Battery_Charging = 0
            USB_PD = 0
            USB_Type_C_Current = 0
        class Byte_3:
            #bmPowerSource = 0
            AC_Supply = 0
            Other = 0
            Uses_VBUS = 0
        class Byte_6:
            bNumConnectors = 0
        class Byte_7:
            SET_CCOM_Supported = 0
            SET_POWER_LEVEL_Supported = 0
            Alt_Mode_Details_Supported = 0
            Alt_Mode_Override_Supported = 0
            PDO_Details_Supported = 0
            Cable_Details_Supported = 0
            External_Supply_notification_Supported = 0
            PD_Reset_notification_Supported = 0

        class Byte_10:
            bNumAltModes = 0
         
        class Byte_12_13:
            bcdBCVersion = 0
        class Byte_14_15:
            bcPDVersion = 0            
        class Byte_16_17:
            bcdTypeCVersion = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F

    Output_DATAx.Byte_2.Disabled_State_Support = RetVal[2] & 0x01
    Output_DATAx.Byte_2.Battery_Charging = (RetVal[2] & 0x02) >>1
    Output_DATAx.Byte_2.USB_PD = (RetVal[2] & 0x04) >> 2
    Output_DATAx.Byte_2.USB_Type_C_Current = (RetVal[2] & 0x40) >> 6

    #Output_DATAx.Byte_3.bmPowerSource = RetVal[3]
    Output_DATAx.Byte_3.AC_Supply = RetVal[3] & 0x01
    Output_DATAx.Byte_3.Other = (RetVal[3] >> 2) & 0x01
    Output_DATAx.Byte_3.Uses_VBUS = (RetVal[3] >> 6) & 0x01


    Output_DATAx.Byte_6.bNumConnectors = RetVal[6] & 0x7F

    Output_DATAx.Byte_7.SET_CCOM_Supported = RetVal[7] & 0x01
    Output_DATAx.Byte_7.SET_POWER_LEVEL_Supported = (RetVal[7] & 0x02) >> 1
    Output_DATAx.Byte_7.Alt_Mode_Details_Supported = (RetVal[7] & 0x04) >> 2
    Output_DATAx.Byte_7.Alt_Mode_Override_Supported = (RetVal[7] & 0x08) >> 3
    Output_DATAx.Byte_7.PDO_Details_Supported = (RetVal[7] & 0x10) >> 4
    Output_DATAx.Byte_7.Cable_Details_Supported = (RetVal[7] & 0x20) >> 5
    Output_DATAx.Byte_7.External_Supply_notification_Supported = (RetVal[7] & 0x40) >> 6
    Output_DATAx.Byte_7.PD_Reset_notification_Supported = (RetVal[7] & 0x80) >> 7

    Output_DATAx.Byte_10.bNumAltModes = RetVal[10]

    Output_DATAx.Byte_12_13.bcdBCVersion = RetVal[12]  | (RetVal[13] << 8)

    Output_DATAx.Byte_14_15.bcPDVersion = RetVal[14]  | (RetVal[15] << 8)
    Output_DATAx.Byte_16_17.bcdTypeCVersion = RetVal[16] | (RetVal[17] << 8)

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Disabled_State_Support: %x" %Output_DATAx.Byte_2.Disabled_State_Support)
    print("Battery_Charging: %x" %Output_DATAx.Byte_2.Battery_Charging)
    print("USB_PD: %x" %Output_DATAx.Byte_2.USB_PD)
    print("USB_Type_C_Current: %x" %Output_DATAx.Byte_2.USB_Type_C_Current)

    print("AC_Supply: %x" %Output_DATAx.Byte_3.AC_Supply)
    print("Other: %x" %Output_DATAx.Byte_3.Other)
    print("Uses_VBUS: %x" %Output_DATAx.Byte_3.Uses_VBUS)

    print("bNumConnectors: %x" %Output_DATAx.Byte_6.bNumConnectors)

    print("SET_CCOM_Supported: %x" %Output_DATAx.Byte_7.SET_CCOM_Supported)
    print("SET_POWER_LEVEL_Supported: %x" %Output_DATAx.Byte_7.SET_POWER_LEVEL_Supported)
    print("Alt_Mode_Details_Supported: %x" %Output_DATAx.Byte_7.Alt_Mode_Details_Supported)
    print("Alt_Mode_Override_Supported: %x" %Output_DATAx.Byte_7.Alt_Mode_Override_Supported)
    print("PDO_Details_Supported: %x" %Output_DATAx.Byte_7.PDO_Details_Supported)
    print("Cable_Details_Supported: %x" %Output_DATAx.Byte_7.Cable_Details_Supported)
    print("External_Supply_notification_Supported: %x" %Output_DATAx.Byte_7.External_Supply_notification_Supported)
    print("PD_Reset_notification_Supported: %x" %Output_DATAx.Byte_7.PD_Reset_notification_Supported)

    print("bNumAltModes: %x" %Output_DATAx.Byte_10.bNumAltModes)

    print("bcdBCVersion: %x" %Output_DATAx.Byte_12_13.bcdBCVersion)

    print("bcPDVersion: %x" %Output_DATAx.Byte_14_15.bcPDVersion)
    print("bcdTypeCVersion: %x" %Output_DATAx.Byte_16_17.bcdTypeCVersion)


    print("End of TestCase_GET_CAPABILITY")  
    print("\n")
    # Close the device
    aa_close(handle)

def TestCase_GET_CONNECTOR_CAPABILITY():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CONNECTOR_CAPABILITY #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER#connector number
    data_Tx[5] = 0#reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            #Operation_Mode = 0
            Rp_Only = 0
            Rd_Only = 0
            DRP = 0
            Analog_Audio_Accessory_Mode = 0
            Debug_Accessory_Mode = 0
            USB2 = 0
            USB3 = 0
            Alternate_Mode = 0
        class Byte_3:
            Provider = 0
            Consumer = 0
            Swap_to_DFP = 0
            Swap_to_UFP = 0
            Swap_to_SRC = 0
            Swap_to_SINK = 0
        class Byte_3_4:
            Extended_Operation_Mode = 0xFF
        class Byte_4_5:
            Miscellaneous_Capabilities = 0x0F
        class Byte_5:
            Reverse_Current_Protection_Support = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    
    #Output_DATAx.Byte_2.Operation_Mode = RetVal[2]
    Output_DATAx.Byte_2.Rp_Only = RetVal[2] & 0x01
    Output_DATAx.Byte_2.Rd_Only = (RetVal[2] >> 1) & 0x01
    Output_DATAx.Byte_2.DRP = (RetVal[2] >> 2) & 0x01
    Output_DATAx.Byte_2.Analog_Audio_Accessory_Mode = (RetVal[2] >> 3)& 0x01
    Output_DATAx.Byte_2.Debug_Accessory_Mode = (RetVal[2] >> 4) & 0x01
    Output_DATAx.Byte_2.USB2 = (RetVal[2] >> 5) & 0x01
    Output_DATAx.Byte_2.USB3 = (RetVal[2] >> 6) & 0x01
    Output_DATAx.Byte_2.Alternate_Mode = (RetVal[2] >> 7) & 0x01

    Output_DATAx.Byte_3.Provider = RetVal[3] & 0x01
    Output_DATAx.Byte_3.Consumer = (RetVal[3] & 0x02) >>1
    Output_DATAx.Byte_3.Swap_to_DFP = (RetVal[3] & 0x04) >>2
    Output_DATAx.Byte_3.Swap_to_UFP = (RetVal[3]& 0x08) >>3
    Output_DATAx.Byte_3.Swap_to_SRC = (RetVal[3] & 0x10) >>4
    Output_DATAx.Byte_3.Swap_to_SINK = (RetVal[3] & 0x20) >>5

    Output_DATAx.Byte_3_4.Extended_Operation_Mode = (RetVal[3] & 0x40) >> 6

    Output_DATAx.Byte_4_5.Miscellaneous_Capabilities = ((RetVal[4] & 0xC0) >> 6)| ((RetVal[5] & 0x3) << 2)

    Output_DATAx.Byte_5.Reverse_Current_Protection_Support = (RetVal[5] & 0x04) >> 2

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Rp_Only: %x" %Output_DATAx.Byte_2.Rp_Only)
    print("Rd_Only: %x" %Output_DATAx.Byte_2.Rd_Only)  
    print("DRP: %x" %Output_DATAx.Byte_2.DRP)  
    print("Analog_Audio_Accessory_Mode: %x" %Output_DATAx.Byte_2.Analog_Audio_Accessory_Mode)  
    print("Debug_Accessory_Mode: %x" %Output_DATAx.Byte_2.Debug_Accessory_Mode)  
    print("USB2: %x" %Output_DATAx.Byte_2.USB2)  
    print("USB3: %x" %Output_DATAx.Byte_2.USB3)  
    print("Alternate_Mode: %x" %Output_DATAx.Byte_2.Alternate_Mode)     

    print("Provider: %x" %Output_DATAx.Byte_3.Provider) 
    print("Consumer: %x" %Output_DATAx.Byte_3.Consumer) 
    print("Swap_to_DFP: %x" %Output_DATAx.Byte_3.Swap_to_DFP) 
    print("Swap_to_UFP: %x" %Output_DATAx.Byte_3.Swap_to_UFP) 
    print("Swap_to_SRC: %x" %Output_DATAx.Byte_3.Swap_to_SRC) 
    print("Swap_to_SINK: %x " %Output_DATAx.Byte_3.Swap_to_SINK) 

    print("Extended_Operation_Mode: %x" %Output_DATAx.Byte_3_4.Extended_Operation_Mode) 
    print("Miscellaneous_Capabilities: %x" %Output_DATAx.Byte_4_5.Miscellaneous_Capabilities) 

    print("Reverse_Current_Protection_Support: %x" %Output_DATAx.Byte_5.Reverse_Current_Protection_Support) 

    print("End of TestCase_GET_CONNECTOR_CAPABILITY")
    print("\n")
    # Close the device
    aa_close(handle)


def TestCase_SET_CCOM():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_CCOM #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((CC_OPERATION_MODE & 0x01 ) << 7) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + 1 bit for Cc Operation mode
    data_Tx[5] = (CC_OPERATION_MODE & 0x06) >> 1  #CC operation bits : 2 bits + reserved
 

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_SET_CCOM_user_input")  
    print("\n")      
    # Close the device
    aa_close(handle)   


def TestCase_SET_UOR():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_UOR #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((USB_OPERATION_ROLE & 0x01 )  << 7)| TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + USB ope role: 1bit
    data_Tx[5] = (USB_OPERATION_ROLE & 0X06) >> 1 #USB operation role bits : 2 bits + reserved
 

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")


    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")   

    print("End of TestCase_SET_UOR_user_input")  
    print("\n")
    # Close the device
    aa_close(handle)   


def TestCase_SET_PDR():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_PDR #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((POWER_DIRECTION_ROLE & 0x01) << 7) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + Power Direction role: 1bit
    data_Tx[5] = (POWER_DIRECTION_ROLE & 0X06) >> 1 #Power Direction role bits : 2 bits + reserved
 

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1] == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1] == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1] == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n") 

    print("End of TestCase_SET_PDR_user_input")  
    print("\n")
    # Close the device
    aa_close(handle)   


def TestCase_GET_ALTERNATE_MODES():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_ALTERNATE_MODES #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = RECIPIENT & 0x07 #Recipient 3 bits + reserved 5 bits = 8bits
    data_Tx[5] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[6] = ALT_MODE_OFFSET #Alternate mode offset: 8bits
    data_Tx[7] = NUM_ALT_MODE & 0x03 #Number of Alternate mode : 2bits + reserved
 

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte2_3:
            SVID_0 : 0
        class Byte_4_5_6_7:
            MID_0 = 0
        class Byte_8_9:
            SVID_1 = 0
        class Byte_10_11_12_13:
            MID_1 = 0
    
    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
 
    Output_DATAx.Byte2_3.SVID_0 = (RetVal[3] << 8) | RetVal[2] 
    Output_DATAx.Byte_4_5_6_7.MID_0 = (RetVal[7] << 24) | (RetVal[6] << 16) | (RetVal[5] << 8) | RetVal[4] 
    Output_DATAx.Byte_8_9.SVID_1 = (RetVal[9] << 8) | RetVal[8] 
    Output_DATAx.Byte_10_11_12_13.MID_1 = (RetVal[13] << 24) | (RetVal[12] << 16) | (RetVal[11] << 8) | RetVal[10] 

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("SVID_0: %x" %Output_DATAx.Byte2_3.SVID_0)
    print("MID_0: %x" %Output_DATAx.Byte_4_5_6_7.MID_0)
    print("SVID_1: %x" %Output_DATAx.Byte_8_9.SVID_1)
    print("MID_1: %x" %Output_DATAx.Byte_10_11_12_13.MID_1)

    print("End of TestCase_GET_ALTERNATE_MODES_user_input")  
    print("\n")
    # Close the device
    aa_close(handle)   

def TestCase_GET_CAM_SUPPORTED():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CAM_SUPPORTED #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved

 

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            bmAltModeSupported = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.bmAltModeSupported = RetVal[2]


    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("bmAltModeSupported: %x" %Output_DATAx.Byte_2.bmAltModeSupported)

    print("End of TestCase_GET_CAM_SUPPORTED")  
    print("\n")
    # Close the device
    aa_close(handle)   

def TestCase_GET_CURRENT_CAM():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CURRENT_CAM #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            CurrentAlternateMode_1 = 0
        class Byte_3:
            CurrentAlternateMode_2 = 0
        class Byte_4_64:
            CurrentAlternateMode_N = 0


    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.CurrentAlternateMode_1 = RetVal[2]
    Output_DATAx.Byte_3.CurrentAlternateMode_2 = RetVal[3]


    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("CurrentAlternateMode_1: %x" %Output_DATAx.Byte_2.CurrentAlternateMode_1)
    print("CurrentAlternateMode_2: %x" %Output_DATAx.Byte_3.CurrentAlternateMode_2)
    print("Do need to print CurrentAlternateMode_N ?")

    print("End of TestCase_GET_CURRENT_CAM")
    print("\n")  
    # Close the device
    aa_close(handle)   


def TestCase_SET_NEW_CAM():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_NEW_CAM #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((ENTER_OR_EXIT & 0x01) << 7) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + 1 bit EnterorExit = 8bits
    data_Tx[5] = NEW_CAM #New CAM: 8 bits
    data_Tx[6] =  AM_SPECIFIC & 0x000000FF #AM Specific: 8 bits (Total= 32 bits)
    data_Tx[7] = (AM_SPECIFIC & 0x0000FF00 >> 8) #AM Specific: 8 bits (Total= 32 bits)
    data_Tx[8] = (AM_SPECIFIC & 0x00FF0000 >> 16) #AM Specific: 8 bits (Total= 32 bits)
    data_Tx[9] = (AM_SPECIFIC & 0xFF000000 >> 24) #AM Specific: 8 bits (Total= 32 bits)

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1]  == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1]  == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1]  == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_SET_NEW_CAM_user_input")  
    print("\n")

    # Close the device
    aa_close(handle)   


def TestCase_GET_PDOS():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_PDOS #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((PARTNER_PDO  & 0x01)<< 7) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + 1 bit Partner PDO = 8bits
    data_Tx[5] = PDO_OFFSET #PDO Offset: 8 bits
    data_Tx[6] = ((SOURCE_CAP_TYPES & 0x3) << 3) | ((SOURCE_OR_SINK_PDOs & 0x1) << 2) | (NUMBER_PDOs & 0x3) # Number of Source Capability: 2 bits + Source-Sink PDOs: 1bit + PDOs:2bits = total 5 bits
    data_Tx[7] = 0 #Reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")


    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            Num_of_PDOs = 0
        class Byte_3_4_5_6:
            PDO_1 = 0
        class Byte_7_8_9_10:
            PDO_2 = 0
        class Byte_11_12_13_14:
            PDO_3 = 0    
        class Byte_15_16_17_18:
            PDO_4 = 0  

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.Num_of_PDOs = RetVal[2]
    Output_DATAx.Byte_3_4_5_6.PDO_1 = (RetVal[6] << 24) | (RetVal[5] << 16) | (RetVal[4] << 8) | RetVal[3] 
    Output_DATAx.Byte_7_8_9_10.PDO_2 = (RetVal[10] << 24) | (RetVal[9] << 16) | (RetVal[8] << 8) | RetVal[7] 
    Output_DATAx.Byte_11_12_13_14.PDO_3 = (RetVal[14] << 24) | (RetVal[13] << 16) | (RetVal[12] << 8) | RetVal[11]  
    Output_DATAx.Byte_15_16_17_18.PDO_4 = (RetVal[18] << 24) | (RetVal[17] << 16) | (RetVal[16] << 8) | RetVal[15] 

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Num_of_PDOs: %x" %Output_DATAx.Byte_2.Num_of_PDOs)
    print("PDO_1: %x" %Output_DATAx.Byte_3_4_5_6.PDO_1)
    print("PDO_2: %x" %Output_DATAx.Byte_7_8_9_10.PDO_2)
    print("PDO_3: %x" %Output_DATAx.Byte_11_12_13_14.PDO_3)
    print("PDO_4: %x" %Output_DATAx.Byte_15_16_17_18.PDO_4)

    print("End of TestCase_GET_PDOS_user_input")  
    print("\n")
    # Close the device
    aa_close(handle)   

def TestCase_GET_CABLE_PROPERTY():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CABLE_PROPERTY #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2_3:
            bmSpeedSuppoted = 0
        class Byte_4:
            bCurrentCapability = 0
        class Byte_5:
            VBUSInCable = 0
            CableType = 0
            Directionality = 0
            Plug_End_Type = 0
            Mode_Support = 0
        class Byte_6:
            Latency = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2_3.bmSpeedSuppoted = (RetVal[3] << 8) | RetVal[2]
    Output_DATAx.Byte_4.bCurrentCapability = RetVal[4]
    Output_DATAx.Byte_5.VBUSInCable = RetVal[5] & 0x01 #bit-0
    Output_DATAx.Byte_5.CableType = (RetVal[5] >> 1) & 0x01 #bit-1
    Output_DATAx.Byte_5.Directionality = (RetVal[5] >> 2) & 0x01 #bit-2
    Output_DATAx.Byte_5.Plug_End_Type = (RetVal[5] >> 3) & 0x03 #bit-3-4
    Output_DATAx.Byte_5.Mode_Support = (RetVal[5] >> 5) & 0x01 #bit-5
    Output_DATAx.Byte_6.Latency = RetVal[6] & 0x0F #bit-0-3


    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("bmSpeedSuppoted: %x" %Output_DATAx.Byte_2_3.bmSpeedSuppoted)
    print("bCurrentCapability: %x" %Output_DATAx.Byte_4.bCurrentCapability)
    print("VBUSInCable: %x" %Output_DATAx.Byte_5.VBUSInCable)
    print("CableType: %x" %Output_DATAx.Byte_5.CableType)
    print("Directionality: %x" %Output_DATAx.Byte_5.Directionality)
    print("Plug_End_Type: %x" %Output_DATAx.Byte_5.Plug_End_Type)
    print("Mode_Support: %x" %Output_DATAx.Byte_5.Mode_Support)
    print("Latency: %x" %Output_DATAx.Byte_6.Latency)


    print("End of TestCase_GET_CABLE_PROPERTY")  
    print("\n")
    # Close the device
    aa_close(handle)   

def TestCase_GET_CONNECTOR_STATUS():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CONNECTOR_STATUS #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2_3:
            Connector_Status_Change = 0
        class Byte_4_5:
            Power_Operation_Mode = 0
            Connector_Status = 0
            Power_Direction = 0
            Connector_Partner_Flag = 0
            Connector_Partner_Type = 0
        class Byte_6_7_8_9:
            Request_Data_Object = 0
        class Byte_10_11_12:
            Battery_Charging_Capability_Status = 0
            Provider_Capabilities_Limited_Reason = 0
            bcd_PDVersion_Opearion_Mode = 0
            Orientaion = 0
            Sink_Path_Status = 0
        class Byte_13:
            Reverse_Current_Protection_Status = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2_3.Connector_Status_Change = (RetVal[3] << 8) | RetVal[2]

    Output_DATAx.Byte_4_5.Power_Operation_Mode = RetVal[4] & 0x07 # bit0-2
    Output_DATAx.Byte_4_5.Connector_Status = (RetVal[4] >> 3) & 0x01 # bit-3
    Output_DATAx.Byte_4_5.Power_Direction = (RetVal[4] >> 4) & 0x01 # bit-4
    Output_DATAx.Byte_4_5.Connector_Partner_Flag =  ((RetVal[5] << 3 ) & 0xF8) | ((RetVal[4] > 5 ) & 0x07)
    Output_DATAx.Byte_4_5.Connector_Partner_Type = (RetVal[5] >> 5) & 0x07

    Output_DATAx.Byte_6_7_8_9.Request_Data_Object = (RetVal[9] << 24) | (RetVal[8] << 16) | (RetVal[7] << 8) | RetVal[6]

    Output_DATAx.Byte_10_11_12.Battery_Charging_Capability_Status = RetVal[10] & 0x03
    Output_DATAx.Byte_10_11_12.bcd_PDVersion_Opearion_Mode = ((((RetVal[12] << 2) & 0xFC) | (RetVal[11] >> 6 & 0x03)) << 8) | (((RetVal[11] << 2) & 0xFC) | RetVal[10] >> 6 & 0x03)
    Output_DATAx.Byte_10_11_12.Orientaion = (RetVal[12] >> 6) & 0x01
    Output_DATAx.Byte_10_11_12.Sink_Path_Status = (RetVal[12] >> 7) & 0x01

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")       

    print("Connector_Status_Change: %x" %Output_DATAx.Byte_2_3.Connector_Status_Change)
    print("Power_Operation_Mode: %x" %Output_DATAx.Byte_4_5.Power_Operation_Mode)
    print("Connector_Status: %x" %Output_DATAx.Byte_4_5.Connector_Status)
    print("Power_Direction: %x" %Output_DATAx.Byte_4_5.Power_Direction)
    print("Connector_Partner_Flag: %x" %Output_DATAx.Byte_4_5.Connector_Partner_Flag)
    print("Connector_Partner_Type: %x" %Output_DATAx.Byte_4_5.Connector_Partner_Type)
    print("Request_Data_Object: %x" %Output_DATAx.Byte_6_7_8_9.Request_Data_Object)
    print("Battery_Charging_Capability_Status: %x" %Output_DATAx.Byte_10_11_12.Battery_Charging_Capability_Status)
    print("bcd_PDVersion_Opearion_Mode: %x" %Output_DATAx.Byte_10_11_12.bcd_PDVersion_Opearion_Mode)
    print("Orientaion: %x" %Output_DATAx.Byte_10_11_12.Orientaion)
    print("Sink_Path_Status: %x" %Output_DATAx.Byte_10_11_12.Sink_Path_Status)

    print("End of TestCase_GET_CONNECTOR_STATUS")
    print("\n")
    # Close the device
    aa_close(handle)   

def TestCase_GET_ERROR_STATUS():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_ERROR_STATUS #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2_3:
            Unrecognized_Command = 0
            Non_Existent_Connector_number = 0
            Invalid_Command_SPecific_Parameters = 0
            Incompatible_connector_partner = 0
            CC_communication_error = 0
            Command_unsuccessful_due_to_dead_battery_condition = 0
            Contract_negotiation_failure = 0
            Overcurrent = 0
            Undefined = 0
            Port_partner_rejected_swap = 0
            Hard_Reset = 0
            PPM_Policy_Conflict = 0
            Swap_Rejected = 0
            Reverse_Current_Protection = 0
            Set_Sink_Path_Rejected = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F

    Output_DATAx.Byte_2_3.Unrecognized_Command = RetVal[2] & 0x01 #bit-0
    Output_DATAx.Byte_2_3.Non_Existent_Connector_number = (RetVal[2] >> 1) & 0x01 #bit-1
    Output_DATAx.Byte_2_3.Invalid_Command_SPecific_Parameters = (RetVal[2] >> 2) & 0x01 #bit-2
    Output_DATAx.Byte_2_3.Incompatible_connector_partner = (RetVal[2] >> 3) & 0x01 #bit-3
    Output_DATAx.Byte_2_3.CC_communication_error = (RetVal[2] >> 4) & 0x01 #bit-4
    Output_DATAx.Byte_2_3.Command_unsuccessful_due_to_dead_battery_condition = (RetVal[2] >> 5) & 0x01 #bit-5
    Output_DATAx.Byte_2_3.Contract_negotiation_failure = (RetVal[2] >> 6) & 0x01 #bit-6
    Output_DATAx.Byte_2_3.Overcurrent = (RetVal[2] >> 7) & 0x01 #bit-7

    Output_DATAx.Byte_2_3.Undefined = RetVal[3] & 0x01 #bit-0
    Output_DATAx.Byte_2_3.Port_partner_rejected_swap = (RetVal[3] >> 1) & 0x01 #bit-1
    Output_DATAx.Byte_2_3.Hard_Reset = (RetVal[3] >> 2) & 0x01 #bit-2
    Output_DATAx.Byte_2_3.PPM_Policy_Conflict = (RetVal[3] >> 3) & 0x01 #bit-3
    Output_DATAx.Byte_2_3.Swap_Rejected = (RetVal[3] >> 4) & 0x01 #bit-4
    Output_DATAx.Byte_2_3.Reverse_Current_Protection = (RetVal[3] >> 5) & 0x01 #bit-5
    Output_DATAx.Byte_2_3.Set_Sink_Path_Rejected = (RetVal[3] >> 6) & 0x01 #bit-6

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Unrecognized_Command: %x" %Output_DATAx.Byte_2_3.Unrecognized_Command)
    print("Non_Existent_Connector_number: %x" %Output_DATAx.Byte_2_3.Non_Existent_Connector_number)
    print("Invalid_Command_SPecific_Parameters: %x" %Output_DATAx.Byte_2_3.Invalid_Command_SPecific_Parameters)
    print("Incompatible_connector_partner: %x" %Output_DATAx.Byte_2_3.Incompatible_connector_partner)
    print("CC_communication_error: %x" %Output_DATAx.Byte_2_3.CC_communication_error)
    print("Command_unsuccessful_due_to_dead_battery_condition: %x" %Output_DATAx.Byte_2_3.Command_unsuccessful_due_to_dead_battery_condition)
    print("Contract_negotiation_failure: %x" %Output_DATAx.Byte_2_3.Contract_negotiation_failure)
    print("Overcurrent: %x" %Output_DATAx.Byte_2_3.Overcurrent)

    print("Undefined: %x" %Output_DATAx.Byte_2_3.Undefined)
    print("Port_partner_rejected_swap: %x" %Output_DATAx.Byte_2_3.Port_partner_rejected_swap)
    print("Hard_Reset: %x" %Output_DATAx.Byte_2_3.Hard_Reset)
    print("PPM_Policy_Conflict: %x" %Output_DATAx.Byte_2_3.PPM_Policy_Conflict)
    print("Swap_Rejected: %x" %Output_DATAx.Byte_2_3.Swap_Rejected)
    print("Reverse_Current_Protection: %x" %Output_DATAx.Byte_2_3.Reverse_Current_Protection)
    print("Set_Sink_Path_Rejected: %x" %Output_DATAx.Byte_2_3.Set_Sink_Path_Rejected)

    print("End of TestCase_GET_ERROR_STATUS")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_SET_POWER_LEVEL():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_POWER_LEVEL #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((SOURCE_or_SINK & 0x01) << 7) |TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + SourceorSink:1bit = 8bits total
    data_Tx[5] = USB_PD_MAX_POWER #USB PD MAx power : 8 bits
    data_Tx[6] = USB_Type_C_CURRENT & 0x07 #USB Type-C current : 3 bits


    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1]  == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1]  == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1]  == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

  
    print("End of TestCase_SET_POWER_LEVEL_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_GET_PD_MESSAGE():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_PD_MESSAGE #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((RECIPIENT & 0x01) << 7 ) | TYPE_C_CONNECTOR_NUMBER #connector: 7 bits + recipient : 1 bit (lsb)
    data_Tx[5] = ((MESSAGE_OFFSET & 0x3F) << 2) | ((RECIPIENT & 0x06) >> 2)# recipient : 2 bit + message offset : 6 bits
    data_Tx[6] = ((NUMBER_OF_BYTES & 0x3F) << 2) | ((MESSAGE_OFFSET & 0xC0) >> 6) # message offset : 2 bits + number of bytes : 6 bits
    data_Tx[7] = ((RESPONSE_MESSAGE_TYPE & 0x3F) << 2)| ((NUMBER_OF_BYTES & 0xC0) >> 6) # number of bytes : 2 bits + response message type : 6 bits


    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2_3:
            VID = 0
        class Byte_4_5:
            PID = 0
        class Byte_6_7_8_9:
            XID = 0
        class Byte_10:
            FW_Version = 0
        class Byte_11:
            HW_Version = 0
        class Byte_12:
            SKEDB_Version = 0
        class Byte_13:
            Load_Step = 0
        class Byte_14_15:
            Sink_Load_Characteristics = 0
        class Byte_16:
            Compliance = 0
        class Byte_17:
            Touch_Temp = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2_3.VID = (RetVal[3] << 8) | RetVal[2]
    Output_DATAx.Byte_4_5.PID = (RetVal[5] << 8) | RetVal[4]
    Output_DATAx.Byte_6_7_8_9.XID = (RetVal[9] << 24) | (RetVal[8] << 16) | (RetVal[7] << 8) | RetVal[6]
    Output_DATAx.Byte_10.FW_Version = RetVal[10]
    Output_DATAx.Byte_11.HW_Version = RetVal[11]
    Output_DATAx.Byte_12.SKEDB_Version = RetVal[12]
    Output_DATAx.Byte_13.Load_Step = RetVal[13]
    Output_DATAx.Byte_14_15.Sink_Load_Characteristics = (RetVal[15] << 8) | RetVal[14]
    Output_DATAx.Byte_16.Compliance = RetVal[16]
    Output_DATAx.Byte_17.Touch_Temp = RetVal[17]


    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("VID: %x"  %Output_DATAx.Byte_2_3.VID)
    print("PID: %x"  %Output_DATAx.Byte_4_5.PID)
    print("XID: %x"  %Output_DATAx.Byte_6_7_8_9.XID)
    print("FW_Version: %x"  %Output_DATAx.Byte_10.FW_Version)
    print("HW_Version: %x"  %Output_DATAx.Byte_11.HW_Version)
    print("SKEDB_Version: %x"  %Output_DATAx.Byte_12.SKEDB_Version)
    print("Load_Step: %x"  %Output_DATAx.Byte_13.Load_Step)
    print("Sink_Load_Characteristics: %x"  %Output_DATAx.Byte_14_15.Sink_Load_Characteristics)
    print("Compliance: %x"  %Output_DATAx.Byte_16.Compliance)
    print("Touch_Temp: %x"  %Output_DATAx.Byte_17.Touch_Temp)


    print("End of TestCase_GET_PD_MESSAGE_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 

def TestCase_GET_ATTENTION_VDO():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_ATTENTION_VDO #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits
    data_Tx[5] = 0 #Reserved



    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")


    class Output_DATAx:
        class Byte_1:
           ReturnCode = 0xFF
        class Byte_2_3:
            Alt_Mode_Index = 0
        class Byte_4:
            Number_Of_VDOs = 0
            Sequence_Number = 0
        class Byte_5_6_7_8:
            VDM_Header = 0
        class Byte_9_10_11_12:
            VDO = 0

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2_3.Alt_Mode_Index = (RetVal[3] << 8) | RetVal[2]
    Output_DATAx.Byte_4.Number_Of_VDOs = RetVal[4] & 0x07
    Output_DATAx.Byte_4.Sequence_Number = (RetVal[4] & 0xE0) >> 5

    Output_DATAx.Byte_5_6_7_8.VDM_Header = (RetVal[8] << 24) | (RetVal[7] << 16) | (RetVal[6] << 8) | RetVal[5] 
    Output_DATAx.Byte_9_10_11_12.VDO = (RetVal[12] << 24) | (RetVal[11] << 16) | (RetVal[10] << 8) | RetVal[9] 

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Alt_Mode_Index: %x" %Output_DATAx.Byte_2_3.Alt_Mode_Index)
    print("Number_Of_VDOs: %x" %Output_DATAx.Byte_4.Number_Of_VDOs)
    print("Sequence_Number: %x" %Output_DATAx.Byte_4.Sequence_Number)
    print("VDM_Header: %x" %Output_DATAx.Byte_5_6_7_8.VDM_Header)
    print("VDO: %x" %Output_DATAx.Byte_9_10_11_12.VDO)


    print("End of TestCase_GET_ATTENTION_VDO")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_GET_CAM_CS():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = GET_CAM_CS #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + Reserved: 1 bit
    data_Tx[5] = CURRENT_ALT_MODE # Current Alt Mode: 8 bits

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            Current_Alternate_Mode = 0
        class Byte_3:
            Status_Byte_1 = 0    
        class Byte_4:
            Status_Byte_2 = 0 
        class Byte_5:
            Status_Byte_3 = 0 
        class Byte_6:
            Status_Byte_4 = 0          
        class Byte_7:
            Number_Of_VDOs = 0                

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.Current_Alternate_Mode = RetVal[2]
    Output_DATAx.Byte_3.Status_Byte_1 = RetVal[3]
    Output_DATAx.Byte_4.Status_Byte_2 = RetVal[4]
    Output_DATAx.Byte_5.Status_Byte_3 = RetVal[5]
    Output_DATAx.Byte_6.Status_Byte_4 = RetVal[6]
    Output_DATAx.Byte_7.Number_Of_VDOs = RetVal[7]

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("Current_Alternate_Mode: %x" %Output_DATAx.Byte_2.Current_Alternate_Mode)
    print("Status_Byte_1: %x" %Output_DATAx.Byte_3.Status_Byte_1)
    print("Status_Byte_2: %x" %Output_DATAx.Byte_4.Status_Byte_2)
    print("Status_Byte_3: %x" %Output_DATAx.Byte_5.Status_Byte_3)
    print("Status_Byte_4: %x" %Output_DATAx.Byte_6.Status_Byte_4)
    print("Number_Of_VDOs: %x" %Output_DATAx.Byte_7.Number_Of_VDOs)

    print("End of TestCase_GET_CAM_CS_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_LPM_FW_UPDATE_REQUEST():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = LPM_FW_UPDATE_REQUEST #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((DIRECTION & 0X01)<< 7 ) & TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + DIRECTION lsb bit: 1 bit
    data_Tx[5] = ((FW_UPDATE_REQUEST & 0x7F) << 1)  | ((DIRECTION >> 1 )& 0x01) #FW_UPDATE_REQUEST: 7bits + DIRECTION msb bit: 1 bit
    data_Tx[6] = ((DATA_INDEX & 0x7F) << 2) | ((FW_UPDATE_REQUEST & 0x80) >> 7) #FW_UPDATE_REQUEST: 1bit + DATA_INDEX : 6 bits + reserved: 1bit
    data_Tx[7] = ((END_OF_MESSAGE & 0x01) << 1)| ((DATA_INDEX & 0x7F) >> 6) # DATA_INDEX : 1 bits + END_OF_MESSAGE: 1 bit


    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            DataPayload_Byte1 = 0
        class Byte_3:
            DataPayload_Byte2 = 0    
        class Byte_4:
            DataPayload_Byte3 = 0  
        class Byte_5:
            DataPayload_Byte4 = 0  
        class Byte_6:
            DataPayload_Byte5 = 0  
        class Byte_7:
            DataPayload_Byte6 = 0  
        class Byte_8:
            DataPayload_Byte7 = 0  
        class Byte_9:
            DataPayload_Byte8 = 0  

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.DataPayload_Byte1 = RetVal[2]
    Output_DATAx.Byte_3.DataPayload_Byte2 = RetVal[3]
    Output_DATAx.Byte_4.DataPayload_Byte3 = RetVal[4]
    Output_DATAx.Byte_5.DataPayload_Byte4 = RetVal[5]
    Output_DATAx.Byte_6.DataPayload_Byte5 = RetVal[6]
    Output_DATAx.Byte_7.DataPayload_Byte6 = RetVal[7]
    Output_DATAx.Byte_8.DataPayload_Byte7 = RetVal[8]
    Output_DATAx.Byte_9.DataPayload_Byte8 = RetVal[9]

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("DataPayload_Byte1: %x" %Output_DATAx.Byte_2.DataPayload_Byte1)
    print("DataPayload_Byte2: %x" %Output_DATAx.Byte_3.DataPayload_Byte2)
    print("DataPayload_Byte3: %x" %Output_DATAx.Byte_4.DataPayload_Byte3)
    print("DataPayload_Byte4: %x" %Output_DATAx.Byte_5.DataPayload_Byte4)
    print("DataPayload_Byte5: %x" %Output_DATAx.Byte_6.DataPayload_Byte5)
    print("DataPayload_Byte6: %x" %Output_DATAx.Byte_7.DataPayload_Byte6)
    print("DataPayload_Byte7: %x" %Output_DATAx.Byte_8.DataPayload_Byte7)
    print("DataPayload_Byte8: %x" %Output_DATAx.Byte_9.DataPayload_Byte8)


    print("End of TestCase_LPM_FW_UPDATE_REQUEST_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_SECURITY_REQUEST():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SECURITY_REQUEST #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((DIRECTION & 0X01)<< 7 ) & TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + DIRECTION lsb bit: 1 bit
    data_Tx[5] = ((AUTH_PROTOCOL_REVISION & 0x3F) << 2)| ((SECURITY_REQUEST_bits & 0x01) << 1)| ((DIRECTION >> 1 )& 0x01) #   AUTH_PROTOCOL_REVISION : 6 bits + SECURITY_REQUEST_bits : 2 + DIRECTION msb bit: 1 bit
    data_Tx[6] = ((AUTHENTICATION_MESSAGE & 0x3F) << 2) | ((AUTH_PROTOCOL_REVISION & 0xC0) >> 6) #  AUTHENTICATION_MESSAGE :6 bits   + AUTH_PROTOCOL_REVISION : 2 bits
    data_Tx[7] = ((DATA_INDEX & 0x7F) << 2) | ((AUTHENTICATION_MESSAGE & 0xC0) >> 6) #  DATA_INDEX : 6 bits  + AUTHENTICATION_MESSAGE :2 bits 
    data_Tx[8] = ((END_OF_MESSAGE & 0x01) << 3)| ((DATA_INDEX >> 6) & 0x01) # DATA_INDEX : 1 bit at b0 and END_OF_MESSAGE : 1 bit at bit-3


    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    class Output_DATAx:
        class Byte_1:
            ReturnCode = 0xFF
        class Byte_2:
            DataPayload_Byte1 = 0
        class Byte_3:
            DataPayload_Byte2 = 0    
        class Byte_4:
            DataPayload_Byte3 = 0  
        class Byte_5:
            DataPayload_Byte4 = 0  
        class Byte_6:
            DataPayload_Byte5 = 0  
        class Byte_7:
            DataPayload_Byte6 = 0  
        class Byte_8:
            DataPayload_Byte7 = 0  
        class Byte_9:
            DataPayload_Byte8 = 0  

    Output_DATAx.Byte_1.ReturnCode = RetVal[1] & 0x0F
    Output_DATAx.Byte_2.DataPayload_Byte1 = RetVal[2]
    Output_DATAx.Byte_3.DataPayload_Byte2 = RetVal[3]
    Output_DATAx.Byte_4.DataPayload_Byte3 = RetVal[4]
    Output_DATAx.Byte_5.DataPayload_Byte4 = RetVal[5]
    Output_DATAx.Byte_6.DataPayload_Byte5 = RetVal[6]
    Output_DATAx.Byte_7.DataPayload_Byte6 = RetVal[7]
    Output_DATAx.Byte_8.DataPayload_Byte7 = RetVal[8]
    Output_DATAx.Byte_9.DataPayload_Byte8 = RetVal[9]

    if(Output_DATAx.Byte_1.ReturnCode == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(Output_DATAx.Byte_1.ReturnCode == TASK_REJECTED):
        print("Task Rejected\n")
    elif(Output_DATAx.Byte_1.ReturnCode == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("DataPayload_Byte1: %x" %Output_DATAx.Byte_2.DataPayload_Byte1)
    print("DataPayload_Byte2: %x" %Output_DATAx.Byte_3.DataPayload_Byte2)
    print("DataPayload_Byte3: %x" %Output_DATAx.Byte_4.DataPayload_Byte3)
    print("DataPayload_Byte4: %x" %Output_DATAx.Byte_5.DataPayload_Byte4)
    print("DataPayload_Byte5: %x" %Output_DATAx.Byte_6.DataPayload_Byte5)
    print("DataPayload_Byte6: %x" %Output_DATAx.Byte_7.DataPayload_Byte6)
    print("DataPayload_Byte7: %x" %Output_DATAx.Byte_8.DataPayload_Byte7)
    print("DataPayload_Byte8: %x" %Output_DATAx.Byte_9.DataPayload_Byte8)


    print("End of TestCase_SECURITY_REQUEST_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 


def TestCase_SET_RETIMER_MODESET_RETIMER_MODE():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_RETIMER_MODESET_RETIMER_MODE #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = ((RETIMER_NUMBER << 7) & 0x80) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + Retimer Number's lsb : 1 bit
    data_Tx[5] =  ((FUNCTIONAL_MODE << 4)& 0xF0)| ((STATE << 1) & 0x0E)| ((RETIMER_NUMBER >> 1) & 0x01) #  Retimer Number's msb  bit: 1 bit + State: 3 bits + Functional mode :  4bits
    data_Tx[6] =  ((GAIN << 1) & 0xFE) | (DP_SOURCE_SINK & 0x01) # dp source-sink : 1 bit + gain : 7 bits
    data_Tx[7] =  ((DATA_INDEX & 0x03) << 6) | RESERVED_BITS | ((ORIENTATION & 0x01) << 1)| ((GAIN >> 7) & 0x01) # gain's msb : 1 bit + Orientation: 1 bit + RESERVED : 4 bits + DataIndex's first two bits: 2 bits
    data_Tx[8] =  ((END_OF_MESSAGE & 0x01) << 5) | ((DATA_INDEX & 0x7C) >> 2) # Data Index: remaining 5 bits : 5 bits + End of message :  1 bit

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1]  == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1]  == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1]  == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")
		

    print("End of TestCase_SET_RETIMER_MODESET_RETIMER_MODE_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 

def TestCase_SET_SINK_PATH():
    handle = aardvark_interface()
    print("\n")
    #Write data
    #write the address and data
    #data_out = array('B', [ 0 for i in range(1+5) ])
    #print("data exp is", data_out)
    data_Tx = array('B', [ 0 for i in range(INIT_ARRAY_BYTES) ])
    #print("Data out is ", data_out)
    
    #data_out = [DATA_REG, 3, GET_CAPABILITY, 00, 00]
    data_Tx[0] = DATA_REG
    data_Tx[1] = NUM_BYTES_TRANSMITTED # number of data bytes transmitted
    data_Tx[2] = SET_SINK_PATH #command
    data_Tx[3] = DEFAULT_DATA_LENGTH# data length set to 00
    data_Tx[4] = (SINK_PATH << 7) | TYPE_C_CONNECTOR_NUMBER #connector number: 7bits + sink path: 1 bit
    

    Write_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS,data_Tx)
    Write_UCSI_Commands_PD(handle, PORT_PD_EC_ADDRESS)

    #Read data
    Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, COMMAND_REG)
    RetVal = Read_UCSI_Data_PD(handle, PORT_PD_EC_ADDRESS, DATA_REG)
    print("\n")

    if(RetVal[1] == TASK_COMPLETED_SUCCESSFUL):
        print("Task Completed Succesfully\n")
    elif(RetVal[1]  == TASK_TIMES_OUT):
        print("Task times-out or Aborted by ABERT request\n")
    elif(RetVal[1]  == TASK_REJECTED):
        print("Task Rejected\n")
    elif(RetVal[1]  == RX_BUFFER_LOCKED):
        print("Task Rejected because RX buffer was locked\n")
    else:
        print("Reserved for standard Tasks\n")

    print("End of TestCase_SET_SINK_PATH_user_input")
    print("\n")
    # Close the device
    aa_close(handle) 


