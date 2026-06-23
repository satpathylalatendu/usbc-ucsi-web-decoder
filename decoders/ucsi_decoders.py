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
UCSI Decoder Functions
Decoding functions for various UCSI 3.0 commands

Based on UCSI Specification Version 3.0
Author: Lalatendu Satpathy
"""

import struct

def format_hex_bytes(resp_bytes):
    """Format bytes as hex with spaces between bytes and 8 bytes per line."""
    hex_str = resp_bytes.hex()
    # Insert space after every 2 characters (1 byte)
    spaced = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    # Split into lines of 8 bytes (24 chars + 7 spaces = 8 bytes)
    lines = []
    bytes_list = spaced.split(' ')
    for i in range(0, len(bytes_list), 8):
        lines.append(' '.join(bytes_list[i:i+8]))
    return '\n'.join(lines)

def decode_hex_string(hexstr):
    """Normalize input: accept space-separated or continuous hex and return bytes."""
    s = ''.join(hexstr.split())
    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]
    if len(s) % 2 == 1:
        s = "0" + s
    try:
        return bytes.fromhex(s)
    except Exception:
        return None

def decode_generic(resp_bytes, version):
    """Generic decoder for commands without specific decoder."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    # Break into 32-bit words
    if len(resp_bytes) >= 4:
        words = []
        for i in range(0, len(resp_bytes) - (len(resp_bytes) % 4), 4):
            word = struct.unpack_from("<I", resp_bytes, i)[0]
            words.append(f"0x{word:08x}")
        out["data_words"] = words
    
    # Show bytes
    out["bytes"] = ' '.join(f"{b:02x}" for b in resp_bytes)
    
    return out

def decode_ack_cc_ci(resp_bytes, version):
    """Decode ACK_CC_CI response per UCSI 3.0 Table 6-8."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Acknowledgment Completed Successfully"
    out["Description"] = "Command Completion and/or Connector Change has been acknowledged"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Next_Step"] = "System has acknowledged the notification. No further action required."
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
        if len(resp_bytes) >= 4:
            words = []
            for i in range(0, len(resp_bytes) - (len(resp_bytes) % 4), 4):
                word = struct.unpack_from("<I", resp_bytes, i)[0]
                words.append(f"0x{word:08x}")
            out["Unexpected_Data_Words"] = words
    
    return out

def decode_connector_reset(resp_bytes, version):
    """Decode CONNECTOR_RESET response per UCSI 3.0 Table 6-6."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Reset Initiated Successfully"
    out["Description"] = "Connector reset process has started"
    out["Reset_Types"] = "Hard Reset: Full disconnect/reconnect cycle | Data Reset: USB data reset, VBUS preserved"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Next_Step"] = "Wait for async notification when reset completes. Check CONNECTOR_STATUS after notification."
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

def decode_set_notification_enable(resp_bytes, version):
    """Decode SET_NOTIFICATION_ENABLE response per UCSI 3.0 Table 6-10."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Notification Settings Updated Successfully"
    out["Description"] = "Notification enable/disable settings have been applied"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Important_Note"] = "⚠ If ANY notification is enabled, Command Completed notification MUST also be enabled"
    out["Next_Step"] = "System will now send notifications based on configured settings"
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

def decode_set_uor(resp_bytes, version):
    """Decode SET_UOR response per UCSI 3.0 Table 6-21."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ USB Operation Role Command Completed Successfully"
    out["Description"] = "USB Operation Role has been set or role swap has been initiated"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Operation_Modes"] = {
        "DFP": "Connector will swap to Downstream Facing Port (Host) mode",
        "UFP": "Connector will swap to Upstream Facing Port (Device) mode", 
        "Accept Swap": "Connector will accept role swap requests from port partner"
    }
    out["Next_Step"] = "Check CONNECTOR_STATUS to verify current USB operation role. May trigger async notification if role changed."
    out["Note"] = "This command is only valid if connector supports USB Power Delivery"
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

def decode_set_pdr(resp_bytes, version):
    """Decode SET_PDR response per UCSI 3.0 Table 6-23."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Power Direction Role Command Completed Successfully"
    out["Description"] = "Power Direction Role has been set or power swap has been initiated"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Power_Roles"] = {
        "Provider/Source": "Connector will swap to Source mode (providing power)",
        "Consumer/Sink": "Connector will swap to Sink mode (consuming power)",
        "Accept Swap": "Connector will accept power swap requests from port partner"
    }
    out["Next_Step"] = "Check CONNECTOR_STATUS to verify current power role. May trigger async notification if role changed."
    out["Important_Notes"] = [
        "Command has no effect if connector has no active connection",
        "Command has no effect if port partner is not PD-capable",
        "If power direction is already the requested one, command completes successfully",
        "Role swap failure will return error and power direction remains unchanged"
    ]
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

def decode_set_retimer_mode(resp_bytes, version):
    """Decode SET_RETIMER_MODE response per UCSI 3.0 Section 6.5.25."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Re-timer Mode Configuration Completed"
    out["Description"] = "Re-timer functional mode, state, or flash operation has been configured successfully"
    out["Expected_Response"] = "Empty (No data returned unless in Flashing Mode with Payload)"
    out["Re-timer_Modes"] = {
        "State": "Off, On/Force Power, Low Power Mode, Compliance Mode, Flashing Mode",
        "Functional_Mode": "USB 3.2 Gen1/Gen2/2x2, USB4 Gen2/Gen3/Gen4, TBT3/TBT4, DP1.4/DP2.0, MFD USB3.2+DP, Debug accessory",
        "Target": "Re-timer facing connector (1), Re-timer facing SoC (2), or both (3)"
    }
    out["Next_Step"] = "For flashing mode with payload, check Data Index field in CCI for synchronization"
    out["Use_Cases"] = [
        "Firmware updates for re-timer devices",
        "EV/DV calibration routines",
        "Forcing specific USB/TBT/DP modes for testing",
        "Power management optimization"
    ]
    out["Important"] = "⚠ This command is OPTIONAL (O) for OPM and LPM - may not be implemented on all platforms"
    
    if len(resp_bytes) > 0:
        out["Info"] = f"Response contains {len(resp_bytes)} bytes (may be valid for Flashing Mode with Payload)"
    
    return out

def decode_set_power_level(resp_bytes, version):
    """Decode SET_POWER_LEVEL response per UCSI 3.0 Section 6.5.16."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ SET_POWER_LEVEL Command Completed"
    out["Description"] = "Power level configuration has been applied to the connector"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["Workflow_Info"] = {
        "Automatic_Workflow": "System automatically compares GET_CONNECTOR_STATUS before and after",
        "Before": "Reads connector status before executing SET_POWER_LEVEL",
        "Execute": "Applies the power level configuration",
        "After": "Reads connector status after execution",
        "Compare": "Identifies and highlights changed fields"
    }
    out["Power_Level_Types"] = {
        "Source_Current_Limit": "Maximum current that can be sourced (e.g., 1.5A, 3.0A)",
        "Sink_Maximum_Power": "Maximum power that can be consumed",
        "Time_To_Read": "Duration for power measurement sampling"
    }
    out["Next_Step"] = "Check the Before/After Comparison table below to see which connector status fields changed"
    out["Important_Notes"] = [
        "Changed fields are highlighted in yellow in the comparison table",
        "Before values shown in gray, After values in green with dark background",
        "This command works in conjunction with GET_CONNECTOR_STATUS",
        "Power level changes may affect charging negotiation with port partner"
    ]
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

def decode_capability(resp_bytes, version):
    """Decode GET_CAPABILITY response - Table 6-13."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 16:
        out["error"] = "Response too short (expected at least 16 bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-13
    fields = []
    
    # Offset 0 (Bits 0-31): bmAttributes (32 bits)
    attr = struct.unpack_from("<I", resp_bytes, 0)[0]
    fields.append({
        "offset": "0",
        "field": "bmAttributes",
        "size": "32",
        "value": f"0x{attr:08x}",
        "interpretation": "Bitmap encoding of supported PPM features.",
        "children": []
    })
    
    # Table 6-14: bmAttributes sub-fields
    fields[-1]["children"].append({
        "field": "Disabled State Support",
        "value": "Yes" if attr & 0x01 else "No",
        "interpretation": "This bit shall be set to one to indicate this platform supports the Disabled State as defined in Section 4.5.2.2.1 in the [USBTYPEC]."
    })
    fields[-1]["children"].append({
        "field": "Battery Charging",
        "value": "Yes" if attr & 0x02 else "No",
        "interpretation": "This bit shall be set to one to indicate this platform supports the Battery Charging Specification as per the value reported in the bcdBCVersion field."
    })
    fields[-1]["children"].append({
        "field": "USB Power Delivery",
        "value": "Yes" if attr & 0x04 else "No",
        "interpretation": "This bit shall be set to one to indicate this platform supports the USB Power Delivery Specification as per the value reported in the bcdPDVersion field."
    })
    fields[-1]["children"].append({
        "field": "Reserved (Bits 3-5)",
        "value": "0",
        "interpretation": "Shall be set to zero."
    })
    fields[-1]["children"].append({
        "field": "USB Type-C Current",
        "value": "Yes" if attr & 0x40 else "No",
        "interpretation": "This bit shall be set to one to indicate this platform supports power capabilities defined in the USB Type-C Specification as per the value reported in the bcdUSBTypeCVersion field."
    })
    fields[-1]["children"].append({
        "field": "Reserved (Bit 7)",
        "value": "0",
        "interpretation": "Shall be set to zero."
    })
    
    # bmPowerSource (Bits 8-15)
    power_source_byte = (attr >> 8) & 0xFF
    power_source_item = {
        "field": "bmPowerSource",
        "value": f"0x{power_source_byte:02x}",
        "interpretation": "At least one of the following bits (AC Supply, Other, Uses VBUS) shall be set to indicate which power sources are supported.",
        "children": []
    }
    power_source_item["children"].append({
        "field": "AC Supply",
        "value": "Yes" if attr & (1 << 8) else "No",
        "interpretation": "Indicates AC Supply power source support."
    })
    power_source_item["children"].append({
        "field": "Reserved (Bit 9)",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    power_source_item["children"].append({
        "field": "Other",
        "value": "Yes" if attr & (1 << 10) else "No",
        "interpretation": "Indicates Other power source support."
    })
    power_source_item["children"].append({
        "field": "Reserved (Bits 11-13)",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    power_source_item["children"].append({
        "field": "Uses VBUS",
        "value": "Yes" if attr & (1 << 14) else "No",
        "interpretation": "Indicates VBUS power source support."
    })
    power_source_item["children"].append({
        "field": "Reserved (Bit 15)",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    fields[-1]["children"].append(power_source_item)
    
    fields[-1]["children"].append({
        "field": "Reserved (Bits 16-31)",
        "value": "0",
        "interpretation": "Shall be set to zero."
    })
    
    # Offset 32 (Bits 32-38): bNumConnectors (7 bits)
    num_connectors = resp_bytes[4] & 0x7F
    fields.append({
        "offset": "32",
        "field": "bNumConnectors",
        "size": "7",
        "value": str(num_connectors),
        "interpretation": "This field indicates the number of Connectors that this PPM supports. A value of zero is illegal in this field."
    })
    
    # Offset 39 (Bit 39): Reserved
    fields.append({
        "offset": "39",
        "field": "Reserved",
        "size": "1",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    
    # Offset 40 (Bits 40-63): bmOptionalFeatures (24 bits)
    opt_features = (resp_bytes[5]) | (resp_bytes[6] << 8) | (resp_bytes[7] << 16)
    fields.append({
        "offset": "40",
        "field": "bmOptionalFeatures",
        "size": "24",
        "value": f"0x{opt_features:06x}",
        "interpretation": "Bitmap encoding indicating which optional features are supported by the PPM. This field is described in detail in Section 6.5.27.",
        "children": []
    })
    
    fields[-1]["children"].append({"field": "Set CCOM Support", "value": "Yes" if opt_features & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "Set Power Level Support", "value": "Yes" if opt_features & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "Alternate Mode Details Available", "value": "Yes" if opt_features & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "Alternate Mode Override Supported", "value": "Yes" if opt_features & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "PDO Details Available", "value": "Yes" if opt_features & (1 << 4) else "No"})
    fields[-1]["children"].append({"field": "Cable Details Available", "value": "Yes" if opt_features & (1 << 5) else "No"})
    fields[-1]["children"].append({"field": "PD Reset Notification Supported", "value": "Yes" if opt_features & (1 << 7) else "No"})
    fields[-1]["children"].append({"field": "Get PD Message Supported", "value": "Yes" if opt_features & (1 << 8) else "No"})
    fields[-1]["children"].append({"field": "Get Attention VDO Supported", "value": "Yes" if opt_features & (1 << 9) else "No"})
    fields[-1]["children"].append({"field": "FW Update Request Supported", "value": "Yes" if opt_features & (1 << 10) else "No"})
    fields[-1]["children"].append({"field": "Negotiated Power Level Change Supported", "value": "Yes" if opt_features & (1 << 11) else "No"})
    fields[-1]["children"].append({"field": "Security Request Supported", "value": "Yes" if opt_features & (1 << 12) else "No"})
    fields[-1]["children"].append({"field": "Set Retimer Mode Supported", "value": "Yes" if opt_features & (1 << 13) else "No"})
    fields[-1]["children"].append({"field": "Chunking Supported", "value": "Yes" if opt_features & (1 << 14) else "No"})
    
    # Offset 64 (Bits 64-71): bNumAltModes
    num_alt_modes = resp_bytes[8] if len(resp_bytes) > 8 else 0
    fields.append({
        "offset": "64",
        "field": "bNumAltModes",
        "size": "8",
        "value": str(num_alt_modes),
        "interpretation": "This field indicates the number of Alternate Modes that this PPM supports. A value of zero indicates that the PPM does not support Alternate Modes. The complete list can be obtained using the GET_ALTERNATE_MODE command. Maximum is limited to MAX_NUM_ALT_MODE."
    })
    
    # Offset 72 (Bits 72-79): Reserved
    fields.append({
        "offset": "72",
        "field": "Reserved",
        "size": "8",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    
    # Offset 80 (Bits 80-95): bcdBCVersion
    if len(resp_bytes) >= 12:
        bc_version = struct.unpack_from("<H", resp_bytes, 10)[0]
        major = (bc_version >> 8) & 0xFF
        minor = bc_version & 0xFF
        fields.append({
            "offset": "80",
            "field": "bcdBCVersion",
            "size": "16",
            "value": f"{major}.{minor:02d}" if bc_version else "N/A",
            "interpretation": "Battery Charging Specification Release Number in Binary-Coded Decimal (e.g., V1.20 is 120H). This field shall only be valid if the device indicates that it supports BC in the bmAttributes field."
        })
    
    # Offset 96 (Bits 96-111): bcdPDVersion
    if len(resp_bytes) >= 14:
        pd_version = struct.unpack_from("<H", resp_bytes, 12)[0]
        major = (pd_version >> 8) & 0xFF
        minor = pd_version & 0xFF
        fields.append({
            "offset": "96",
            "field": "bcdPDVersion",
            "size": "16",
            "value": f"{major}.{minor:02d}" if pd_version else "N/A",
            "interpretation": "USB Power Delivery Specification Revision Number in Binary-Coded Decimal (e.g. Revision 3.0 is 300h). This field shall only be valid if the device indicates that it supports PD in the bmAttributes field."
        })
    
    # Offset 112 (Bits 112-127): bcdUSBTypeCVersion
    if len(resp_bytes) >= 16:
        typec_version = struct.unpack_from("<H", resp_bytes, 14)[0]
        major = (typec_version >> 8) & 0xFF
        minor = typec_version & 0xFF
        fields.append({
            "offset": "112",
            "field": "bcdUSBTypeCVersion",
            "size": "16",
            "value": f"{major}.{minor:02d}" if typec_version else "N/A",
            "interpretation": "USB Type-C Specification Release Number in Binary-Coded Decimal (e.g. Release 2.0 is 200h). This field shall only be valid if the device indicates that it supports USB Type-C in the bmAttributes field."
        })
    
    out["fields"] = fields
    return out

def decode_connector_capability(resp_bytes, version):
    """Decode GET_CONNECTOR_CAPABILITY response - Table 6-17."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 4:
        out["error"] = "Response too short (expected at least 4 bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-17
    fields = []
    
    # All data is in the first 4 bytes (32 bits)
    all_data = struct.unpack_from("<I", resp_bytes, 0)[0]
    
    # Offset 0 (Bits 0-7): Operation Mode (8 bits)
    op_mode = all_data & 0xFF
    fields.append({
        "offset": "0",
        "field": "Operation Mode",
        "size": "8",
        "value": f"0x{op_mode:02x}",
        "interpretation": "This field shall indicate the mode that the connector can support. Note: Additional capabilities are described in the Extended Operation Mode field.",
        "children": []
    })
    
    # Operation Mode sub-fields (bits 0-7)
    fields[-1]["children"].append({"field": "Rp only", "value": "Yes" if op_mode & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "Rd only", "value": "Yes" if op_mode & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "DRP (Rp/Rd)", "value": "Yes" if op_mode & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "Analog Audio Accessory Mode (Ra/Ra)", "value": "Yes" if op_mode & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "Debug Accessory Mode (Rd/Rd)", "value": "Yes" if op_mode & (1 << 4) else "No"})
    fields[-1]["children"].append({"field": "USB2", "value": "Yes" if op_mode & (1 << 5) else "No"})
    fields[-1]["children"].append({"field": "USB3", "value": "Yes" if op_mode & (1 << 6) else "No"})
    fields[-1]["children"].append({"field": "Alternate Mode", "value": "Yes" if op_mode & (1 << 7) else "No"})
    
    # Offset 8 (Bit 8): Provider
    fields.append({
        "offset": "8",
        "field": "Provider",
        "size": "1",
        "value": "Yes" if all_data & (1 << 8) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP or Rp only. This bit shall be set to one if the connector is capable of providing power on this connector [Either PD, USB Type-C Current or BC 1.2]."
    })
    
    # Offset 9 (Bit 9): Consumer
    fields.append({
        "offset": "9",
        "field": "Consumer",
        "size": "1",
        "value": "Yes" if all_data & (1 << 9) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP or Rd only. This bit shall be set to one if the connector is capable of consuming power on this connector [Either PD, USB Type-C Current or BC 1.2]."
    })
    
    # Offset 10 (Bit 10): Swap to DFP
    fields.append({
        "offset": "10",
        "field": "Swap to DFP",
        "size": "1",
        "value": "Yes" if all_data & (1 << 10) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP or Rp only or Rd only. This bit shall be set to one if the connector is capable of accepting swap to DFP."
    })
    
    # Offset 11 (Bit 11): Swap to UFP
    fields.append({
        "offset": "11",
        "field": "Swap to UFP",
        "size": "1",
        "value": "Yes" if all_data & (1 << 11) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP or Rp only or Rd only. This bit shall be set to one if the connector is capable of accepting swap to UFP."
    })
    
    # Offset 12 (Bit 12): Swap to SRC
    fields.append({
        "offset": "12",
        "field": "Swap to SRC",
        "size": "1",
        "value": "Yes" if all_data & (1 << 12) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP. This bit shall be set to one if the connector is capable of accepting swap to SRC."
    })
    
    # Offset 13 (Bit 13): Swap to SNK
    fields.append({
        "offset": "13",
        "field": "Swap to SNK",
        "size": "1",
        "value": "Yes" if all_data & (1 << 13) else "No",
        "interpretation": "This bit is valid only when the operation mode is DRP. This bit shall be set to one if the connector is capable of accepting swap to SNK."
    })
    
    # Offset 14 (Bits 14-21): Extended Operation Mode (8 bits)
    ext_op_mode = (all_data >> 14) & 0xFF
    fields.append({
        "offset": "14",
        "field": "Extended Operation Mode",
        "size": "8",
        "value": f"0x{ext_op_mode:02x}",
        "interpretation": "Extended operation mode capabilities including USB4 Gen 2/3/4 and EPR Source/Sink support.",
        "children": []
    })
    
    # Extended Operation Mode sub-fields
    fields[-1]["children"].append({"field": "USB4 Gen 2", "value": "Yes" if ext_op_mode & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "EPR Source", "value": "Yes" if ext_op_mode & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "EPR Sink", "value": "Yes" if ext_op_mode & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "USB4 Gen 3", "value": "Yes" if ext_op_mode & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "USB4 Gen 4", "value": "Yes" if ext_op_mode & (1 << 4) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bits 5-7)", "value": "0"})
    
    # Offset 22 (Bits 22-25): Miscellaneous Capabilities (4 bits)
    misc_cap = (all_data >> 22) & 0x0F
    fields.append({
        "offset": "22",
        "field": "Miscellaneous Capabilities",
        "size": "4",
        "value": f"0x{misc_cap:01x}",
        "interpretation": "Bitmap indicating support for FW Update and Security features.",
        "children": []
    })
    
    # Miscellaneous Capabilities sub-fields
    fields[-1]["children"].append({"field": "FW Update", "value": "Yes" if misc_cap & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "Security", "value": "Yes" if misc_cap & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bits 2-3)", "value": "0"})
    
    # Offset 26 (Bit 26): Reverse Current Protection Support
    fields.append({
        "offset": "26",
        "field": "Reverse Current Protection Support",
        "size": "1",
        "value": "Yes" if all_data & (1 << 26) else "No",
        "interpretation": "This is debug level information. This bit shall be set to one if the LPM supports this feature. Otherwise, this bit shall be set to zero."
    })
    
    # Offset 27 (Bits 27-28): Partner PD Revision (2 bits)
    partner_pd_rev = (all_data >> 27) & 0x03
    pd_rev_map = {0: "Reserved", 1: "PD 1.0", 2: "PD 2.0", 3: "PD 3.0"}
    fields.append({
        "offset": "27",
        "field": "Partner PD Revision",
        "size": "2",
        "value": pd_rev_map.get(partner_pd_rev, "Unknown"),
        "interpretation": "Partner's major USB PD Revision from the Specification Revision field of the USB PD message Header."
    })
    
    # Offset 29 (Bits 29-31): Reserved (3 bits)
    fields.append({
        "offset": "29",
        "field": "Reserved",
        "size": "3",
        "value": "0",
        "interpretation": "Set to zero."
    })
    
    out["fields"] = fields
    return out

def decode_connector_status(resp_bytes, version):
    """Decode GET_CONNECTOR_STATUS response per Table 6-43."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 16:
        out["error"] = "Response too short (expected at least 16 bytes)"
        return out
    
    # Check if Power Reading Ready (bit 89) - this indicates READ_POWER_LEVEL data is available
    data_qword1 = struct.unpack_from("<Q", resp_bytes, 8)[0] if len(resp_bytes) >= 16 else 0
    pwr_reading_ready = (data_qword1 >> 25) & 0x01
    
    if pwr_reading_ready:
        out["Power_Data_Available"] = "✓ READ_POWER_LEVEL data is available in this response"
        out["Power_Fields"] = "See: Power Reading Ready, Peak Current, Average Current, Voltage Reading below"
    
    # Create structured table format matching UCSI spec Table 6-43
    fields = []
    
    # Read data for bit extraction
    data_qword0 = struct.unpack_from("<Q", resp_bytes, 0)[0]
    
    # Offset 0 (Bits 0-15): Connector Status Change (Table 6-44)
    change_bits = struct.unpack_from("<H", resp_bytes, 0)[0]
    fields.append({
        "offset": "0",
        "field": "Connector Status Change",
        "size": "16",
        "value": f"0x{change_bits:04x}",
        "interpretation": "A bitmap indicating the types of status changes that have occurred on the connector.",
        "children": []
    })
    
    # Connector Status Change sub-fields (Table 6-44)
    fields[-1]["children"].append({"field": "Reserved (Bit 0)", "value": "0"})
    fields[-1]["children"].append({"field": "External Supply Change", "value": "Yes" if change_bits & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "Power Operation Mode Change", "value": "Yes" if change_bits & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "Attention", "value": "Yes" if change_bits & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bit 4)", "value": "0"})
    fields[-1]["children"].append({"field": "Supported Provider Capabilities Change", "value": "Yes" if change_bits & (1 << 5) else "No"})
    fields[-1]["children"].append({"field": "Negotiated Power Level Change", "value": "Yes" if change_bits & (1 << 6) else "No"})
    fields[-1]["children"].append({"field": "PD Reset Complete", "value": "Yes" if change_bits & (1 << 7) else "No"})
    fields[-1]["children"].append({"field": "Supported CAM Change", "value": "Yes" if change_bits & (1 << 8) else "No"})
    fields[-1]["children"].append({"field": "Battery Charging Status Change", "value": "Yes" if change_bits & (1 << 9) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bit 10)", "value": "0"})
    fields[-1]["children"].append({"field": "Connector Partner Changed", "value": "Yes" if change_bits & (1 << 11) else "No"})
    fields[-1]["children"].append({"field": "Power Direction Changed", "value": "Yes" if change_bits & (1 << 12) else "No"})
    fields[-1]["children"].append({"field": "Sink Path Status Change", "value": "Yes" if change_bits & (1 << 13) else "No"})
    fields[-1]["children"].append({"field": "Connect Change", "value": "Yes" if change_bits & (1 << 14) else "No"})
    fields[-1]["children"].append({"field": "Error", "value": "Yes" if change_bits & (1 << 15) else "No"})
    
    # Offset 16 (Bits 16-18): Power Operation Mode
    pwr_op_mode = (data_qword0 >> 16) & 0x07
    pwr_mode_names = {
        0: "Reserved",
        1: "USB Default Operation",
        2: "BC",
        3: "PD",
        4: "USB Type-C Current - 1.5A",
        5: "USB Type-C Current - 3A",
        6: "USB Type-C Current - 5A",
        7: "Reserved"
    }
    fields.append({
        "offset": "16",
        "field": "Power Operation Mode",
        "size": "3",
        "value": pwr_mode_names.get(pwr_op_mode, f"Unknown ({pwr_op_mode})"),
        "interpretation": "This field is only valid when the Connect Status field is set to one. This field shall indicate the current power operation mode of the connector."
    })
    
    # Offset 19 (Bit 19): Connect Status
    conn_status = (data_qword0 >> 19) & 0x01
    fields.append({
        "offset": "19",
        "field": "Connect Status",
        "size": "1",
        "value": "Connected" if conn_status else "Disconnected",
        "interpretation": "This field indicates the current connect status of the connector. This field shall be set to one when a device is connected to this connector."
    })
    
    # Offset 20 (Bit 20): Power Direction
    pwr_dir = (data_qword0 >> 20) & 0x01
    fields.append({
        "offset": "20",
        "field": "Power Direction",
        "size": "1",
        "value": "Provider" if pwr_dir else "Consumer",
        "interpretation": "This field is only valid when the Connect Status field is set to one. The field shall indicate whether the connector is operating as a consumer or provider. 0=Consumer, 1=Provider"
    })
    
    # Offset 21 (Bits 21-28): Connector Partner Flags
    partner_flags = (data_qword0 >> 21) & 0xFF
    fields.append({
        "offset": "21",
        "field": "Connector Partner Flags",
        "size": "8",
        "value": f"0x{partner_flags:02x}",
        "interpretation": "This field is only valid when the Connect Status field is set to one. This field indicates the current mode the connector is operating in.",
        "children": []
    })
    
    # Connector Partner Flags sub-fields
    fields[-1]["children"].append({"field": "USB (USB 2.0 or USB 3.x)", "value": "Yes" if partner_flags & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "Alternate Mode", "value": "Yes" if partner_flags & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "USB4 Gen 3", "value": "Yes" if partner_flags & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "USB4 Gen 4", "value": "Yes" if partner_flags & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bits 4-7)", "value": "0"})
    
    # Offset 29 (Bits 29-31): Connector Partner Type
    partner_type = (data_qword0 >> 29) & 0x07
    partner_types = {
        0: "Reserved",
        1: "DFP attached",
        2: "UFP attached",
        3: "Powered cable/No UFP attached",
        4: "Powered cable/UFP attached",
        5: "Debug Accessory attached",
        6: "Audio Adapter Accessory attached",
        7: "Reserved"
    }
    fields.append({
        "offset": "29",
        "field": "Connector Partner Type",
        "size": "3",
        "value": partner_types.get(partner_type, f"Unknown ({partner_type})"),
        "interpretation": "This field is only valid when the Connect Status field is set to one. This field indicates the type of connector partner detected on this connector."
    })
    
    # Offset 32 (Bits 32-63): Request Data Object (Optional)
    if len(resp_bytes) >= 8:
        rdo = struct.unpack_from("<I", resp_bytes, 4)[0]
        fields.append({
            "offset": "32",
            "field": "Request Data Object (RDO)",
            "size": "32",
            "value": f"0x{rdo:08x}",
            "interpretation": "This field is only valid when the Connect Status field is set to one and the Power Operation Mode field is set to PD. This field shall return the currently negotiated power level."
        })
    
    # Read bytes 8-15 for remaining fields
    if len(resp_bytes) >= 16:
        data_qword1 = struct.unpack_from("<Q", resp_bytes, 8)[0]
        
        # Offset 64 (Bits 64-65): Battery Charging Capability Status
        battery_status = (data_qword1 >> 0) & 0x03
        battery_status_names = {
            0: "Not charging",
            1: "Nominal charging rate",
            2: "Slow charging rate",
            3: "Very slow charging rate"
        }
        fields.append({
            "offset": "64",
            "field": "Battery Charging Capability Status",
            "size": "2",
            "value": battery_status_names.get(battery_status, f"Unknown ({battery_status})"),
            "interpretation": "This field is only valid if the connector is operating as a Sink. Slow or very slow charging rate shall be indicated only if the PPM determines that the currently negotiated contract is not sufficient for nominal charging rate."
        })
        
        # Offset 66 (Bits 66-69): Provider Capabilities Limited Reason (Table 6-45)
        prov_cap_limited = (data_qword1 >> 2) & 0x0F
        fields.append({
            "offset": "66",
            "field": "Provider Capabilities Limited Reason",
            "size": "4",
            "value": f"0x{prov_cap_limited:01x}",
            "interpretation": "A bitmap indicating the reasons why the Provider capabilities of the connector have been limited. This field is only valid if the connector is operating as a provider.",
            "children": []
        })
        
        # Provider Capabilities Limited Reason sub-fields
        fields[-1]["children"].append({"field": "Power Budget Lowered", "value": "Yes" if prov_cap_limited & (1 << 0) else "No"})
        fields[-1]["children"].append({"field": "Reaching Power Budget Limit", "value": "Yes" if prov_cap_limited & (1 << 1) else "No"})
        fields[-1]["children"].append({"field": "Reserved (Bits 2-3)", "value": "0"})
        
        # Offset 70 (Bits 70-85): bcdPDVersion Operation Mode
        bcd_pd_version = (data_qword1 >> 6) & 0xFFFF
        if bcd_pd_version > 0:
            major = (bcd_pd_version >> 8) & 0xFF
            minor = bcd_pd_version & 0xFF
            fields.append({
                "offset": "70",
                "field": "bcdPDVersion Operation Mode",
                "size": "16",
                "value": f"{major}.{minor:02d}",
                "interpretation": "This field indicates the USB Power Delivery Specification Revision Number the connector uses during an Explicit Contract, in Binary-Coded Decimal format (e.g., Revision 3.0 is 300H). This field shall only be valid if the Power Operation Mode field is set to PD."
            })
        else:
            fields.append({
                "offset": "70",
                "field": "bcdPDVersion Operation Mode",
                "size": "16",
                "value": "N/A",
                "interpretation": "This field indicates the USB Power Delivery Specification Revision Number. Not applicable when Power Operation Mode is not set to PD."
            })
        
        # Offset 86 (Bit 86): Orientation
        orientation = (data_qword1 >> 22) & 0x01
        fields.append({
            "offset": "86",
            "field": "Orientation",
            "size": "1",
            "value": "Flipped" if orientation else "Direct",
            "interpretation": "This field shall be set to 0 when the connection is in the direct orientation. This field shall be set to 1 when the connection is in the flipped orientation."
        })
        
        # Offset 87 (Bit 87): Sink Path Status
        sink_path = (data_qword1 >> 23) & 0x01
        fields.append({
            "offset": "87",
            "field": "Sink Path Status",
            "size": "1",
            "value": "Enabled" if sink_path else "Disabled",
            "interpretation": "This field shall indicate the status of the Sink Path. The bit shall be set to one if the sink path is enabled and set to zero if the sink is disabled. The PPM can disable or enable the Sink Path without OPM knowledge."
        })
        
        # Offset 88 (Bit 88): Reverse Current Protection Status
        rcp_status = (data_qword1 >> 24) & 0x01
        fields.append({
            "offset": "88",
            "field": "Reverse Current Protection Status",
            "size": "1",
            "value": "Active" if rcp_status else "Inactive",
            "interpretation": "This field is valid if the Reverse Current Protection Support field is set to one in the GET_CONNECTOR_CAPABILITY. This field shall be set to one when the Reverse Current Protection happens."
        })
        
        # Offset 89 (Bit 89): Power Reading Ready
        pwr_reading_ready = (data_qword1 >> 25) & 0x01
        fields.append({
            "offset": "89",
            "field": "Power Reading Ready",
            "size": "1",
            "value": "Valid" if pwr_reading_ready else "Not Valid",
            "interpretation": "This field is set to 1 if the power reading is valid. The Power Reading Ready field shall be set by LPM in response to READ_POWER_LEVEL command when data is ready for OPM collection. This field shall be cleared to 0 after OPM reads the values."
        })
        
        # Offset 90 (Bits 90-92): Scale (Current)
        current_scale = (data_qword1 >> 26) & 0x07
        current_resolution = current_scale * 5  # Each bit is 5mA
        fields.append({
            "offset": "90",
            "field": "Scale (Current)",
            "size": "3",
            "value": f"{current_scale} ({current_resolution}mA resolution)",
            "interpretation": "This field indicates the current resolution. Each bit is 5mA. Example: 1b=5mA, 101b=25mA"
        })
        
        # Offset 93 (Bits 93-108): Peak Current
        peak_current = (data_qword1 >> 29) & 0xFFFF
        if pwr_reading_ready:
            peak_current_ma = peak_current * current_resolution
            fields.append({
                "offset": "93",
                "field": "Peak Current",
                "size": "16",
                "value": f"{peak_current_ma}mA (raw: {peak_current})",
                "interpretation": "This field is a peak current measurement reading. If the ADC supports only less than 16 bits, the most significant bits shall be set to 0."
            })
        else:
            fields.append({
                "offset": "93",
                "field": "Peak Current",
                "size": "16",
                "value": f"N/A (raw: {peak_current})",
                "interpretation": "Peak current measurement reading. Not valid when Power Reading Ready is 0."
            })
    
    # Read bytes 16-18 for additional power measurements (bits 93-151 = 19 bytes total)
    if len(resp_bytes) >= 19:
        # Only unpack 3 bytes (16, 17, 18) since we have 19 bytes total, pad with 0x00 for the 4th byte
        data_bytes = resp_bytes[16:19] + b'\x00'
        data_dword2 = struct.unpack("<I", data_bytes)[0]
        
        # Offset 109 (Bits 109-124): Average Current
        avg_current_low = (data_qword1 >> 45) & 0x1FFF
        avg_current_high = (data_dword2 >> 0) & 0x07
        avg_current = (avg_current_high << 13) | avg_current_low
        
        if pwr_reading_ready:
            avg_current_ma = avg_current * current_resolution
            fields.append({
                "offset": "109",
                "field": "Average Current",
                "size": "16",
                "value": f"{avg_current_ma}mA (raw: {avg_current})",
                "interpretation": "This field represents the moving average for the minimum time interval specified either in the READ_POWER_LEVEL command or default 100mS of total time with interval of 5mS if the READ_POWER_LEVEL command has not been issued. If the ADC supports less than 16 bits, the most significant bits shall be set to 0."
            })
        else:
            fields.append({
                "offset": "109",
                "field": "Average Current",
                "size": "16",
                "value": f"N/A (raw: {avg_current})",
                "interpretation": "Average current measurement. Not valid when Power Reading Ready is 0."
            })
        
        # Offset 125 (Bits 125-128): Scale (Voltage)
        voltage_scale = (data_dword2 >> 13) & 0x0F
        voltage_resolution = voltage_scale * 5  # Each bit is 5mV
        fields.append({
            "offset": "125",
            "field": "Scale (Voltage)",
            "size": "4",
            "value": f"{voltage_scale} ({voltage_resolution}mV resolution)",
            "interpretation": "This field indicates the voltage resolution. Each bit is 5mV. Example: 010b=10mV, 0101b=25mV, 1010b=50mV"
        })
        
        # Offset 129 (Bits 129-144): Voltage Reading
        voltage_reading = (data_dword2 >> 17) & 0xFFFF
        if pwr_reading_ready:
            voltage_mv = voltage_reading * voltage_resolution
            fields.append({
                "offset": "129",
                "field": "Voltage Reading",
                "size": "16",
                "value": f"{voltage_mv}mV (raw: {voltage_reading})",
                "interpretation": "This field is the most recent VBUS voltage measurement within the time window specified by the READ_POWER_LEVEL command 'Time to Read Power' or 100mS which is the default value. If the ADC supports less than 16 bits, the most significant bits shall be set to 0."
            })
        else:
            fields.append({
                "offset": "129",
                "field": "Voltage Reading",
                "size": "16",
                "value": f"N/A (raw: {voltage_reading})",
                "interpretation": "Voltage measurement. Not valid when Power Reading Ready is 0."
            })
        
        # Offset 145 (Bits 145-151): Reserved
        fields.append({
            "offset": "145",
            "field": "Reserved",
            "size": "7",
            "value": "0",
            "interpretation": "Reserved and shall be set to zero."
        })
    
    out["fields"] = fields
    return out

def decode_get_pdos(resp_bytes, version):
    """Decode GET_PDOS response - parses Power Data Objects per Table 6-37."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) == 0:
        out["note"] = "No PDOs available (Data Length = 0)"
        return out
    
    if len(resp_bytes) < 4:
        out["error"] = "Response too short for PDO data"
        return out
    
    # Create structured table format matching UCSI spec Table 6-37
    fields = []
    i = 0
    pdo_index = 0
    
    while i + 4 <= len(resp_bytes):
        word = struct.unpack_from("<I", resp_bytes, i)[0]
        offset_bits = i * 8
        
        # Determine PDO type
        pdo_type = (word >> 30) & 0x03
        
        # Create main PDO field
        pdo_field = {
            "offset": str(offset_bits),
            "field": f"PDO[{pdo_index}]",
            "size": "32",
            "value": f"0x{word:08x}",
            "children": []
        }
        
        if pdo_type == 0:  # Fixed Supply
            pdo_field["children"].append({"field": "Type", "value": "Fixed Supply"})
            
            # Decode Fixed Supply PDO
            voltage = ((word >> 10) & 0x3FF) * 50
            current = (word & 0x3FF) * 10
            
            pdo_field["children"].append({"field": "Voltage", "value": f"{voltage}mV ({voltage/1000.0}V)"})
            pdo_field["children"].append({"field": "Max Current", "value": f"{current}mA ({current/1000.0}A)"})
            pdo_field["children"].append({"field": "Max Power", "value": f"{(voltage * current) / 1000000.0:.2f}W"})
            
            # Additional flags (bits 20-29)
            dual_role_power = (word >> 29) & 0x01
            usb_suspend = (word >> 28) & 0x01
            unconstrained_power = (word >> 27) & 0x01
            usb_comms = (word >> 26) & 0x01
            dual_role_data = (word >> 25) & 0x01
            unchunked_msg = (word >> 24) & 0x01
            epr_mode = (word >> 23) & 0x01
            peak_current = (word >> 20) & 0x03
            
            pdo_field["children"].append({"field": "Dual-Role Power", "value": "Yes" if dual_role_power else "No"})
            pdo_field["children"].append({"field": "USB Suspend Supported", "value": "Yes" if usb_suspend else "No"})
            pdo_field["children"].append({"field": "Unconstrained Power", "value": "Yes" if unconstrained_power else "No"})
            pdo_field["children"].append({"field": "USB Communications Capable", "value": "Yes" if usb_comms else "No"})
            pdo_field["children"].append({"field": "Dual-Role Data", "value": "Yes" if dual_role_data else "No"})
            pdo_field["children"].append({"field": "Unchunked Extended Messages Supported", "value": "Yes" if unchunked_msg else "No"})
            pdo_field["children"].append({"field": "EPR Mode Capable", "value": "Yes" if epr_mode else "No"})
            
            peak_names = {0: "Overload not supported", 1: "Overload 1", 2: "Overload 2", 3: "Overload 3"}
            pdo_field["children"].append({"field": "Peak Current", "value": peak_names.get(peak_current, "Reserved")})
            
        elif pdo_type == 1:  # Battery
            pdo_field["children"].append({"field": "Type", "value": "Battery"})
            
            max_voltage = ((word >> 20) & 0x3FF) * 50
            min_voltage = ((word >> 10) & 0x3FF) * 50
            max_power = (word & 0x3FF) * 250
            
            pdo_field["children"].append({"field": "Max Voltage", "value": f"{max_voltage}mV ({max_voltage/1000.0}V)"})
            pdo_field["children"].append({"field": "Min Voltage", "value": f"{min_voltage}mV ({min_voltage/1000.0}V)"})
            pdo_field["children"].append({"field": "Max Power", "value": f"{max_power}mW ({max_power/1000.0}W)"})
            
        elif pdo_type == 2:  # Variable Supply
            pdo_field["children"].append({"field": "Type", "value": "Variable Supply"})
            
            max_voltage = ((word >> 20) & 0x3FF) * 50
            min_voltage = ((word >> 10) & 0x3FF) * 50
            max_current = (word & 0x3FF) * 10
            
            pdo_field["children"].append({"field": "Max Voltage", "value": f"{max_voltage}mV ({max_voltage/1000.0}V)"})
            pdo_field["children"].append({"field": "Min Voltage", "value": f"{min_voltage}mV ({min_voltage/1000.0}V)"})
            pdo_field["children"].append({"field": "Max Current", "value": f"{max_current}mA ({max_current/1000.0}A)"})
            
        elif pdo_type == 3:  # APDO (Augmented Power Data Object)
            apdo_type = (word >> 28) & 0x03
            
            if apdo_type == 0:  # SPR Programmable Power Supply
                pdo_field["children"].append({"field": "Type", "value": "APDO - SPR Programmable Power Supply"})
                
                max_voltage = ((word >> 17) & 0xFF) * 100
                min_voltage = ((word >> 8) & 0xFF) * 100
                max_current = (word & 0x7F) * 50
                pps_power_limited = (word >> 27) & 0x01
                
                pdo_field["children"].append({"field": "Max Voltage", "value": f"{max_voltage}mV ({max_voltage/1000.0}V)"})
                pdo_field["children"].append({"field": "Min Voltage", "value": f"{min_voltage}mV ({min_voltage/1000.0}V)"})
                pdo_field["children"].append({"field": "Max Current", "value": f"{max_current}mA ({max_current/1000.0}A)"})
                pdo_field["children"].append({"field": "PPS Power Limited", "value": "Yes" if pps_power_limited else "No"})
                
            elif apdo_type == 1:  # EPR Adjustable Voltage Supply
                pdo_field["children"].append({"field": "Type", "value": "APDO - EPR Adjustable Voltage Supply"})
                
                max_voltage = ((word >> 17) & 0x3FF) * 100
                min_voltage = ((word >> 8) & 0xFF) * 100
                max_current = (word & 0x7F) * 50
                peak_current = (word >> 7) & 0x01
                
                pdo_field["children"].append({"field": "Max Voltage", "value": f"{max_voltage}mV ({max_voltage/1000.0}V)"})
                pdo_field["children"].append({"field": "Min Voltage", "value": f"{min_voltage}mV ({min_voltage/1000.0}V)"})
                pdo_field["children"].append({"field": "PDP", "value": f"{max_current * 50}mA"})
                pdo_field["children"].append({"field": "Peak Current", "value": "Yes" if peak_current else "No"})
            else:
                pdo_field["children"].append({"field": "Type", "value": f"APDO - Reserved Type ({apdo_type})"})
        
        fields.append(pdo_field)
        i += 4
        pdo_index += 1
    
    out["fields"] = fields
    out["pdo_count"] = pdo_index
    
    return out

def decode_error_status(resp_bytes, version):
    """Decode GET_ERROR_STATUS response per Table 6-48."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 2:
        out["error"] = "Response too short (expected at least 2 bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-48
    fields = []
    
    # Offset 0 (Bits 0-15): Error Information
    error_info = struct.unpack_from("<H", resp_bytes, 0)[0]
    fields.append({
        "offset": "0",
        "field": "Error Information",
        "size": "16",
        "value": f"0x{error_info:04x}",
        "children": []
    })
    
    # Error Information sub-fields (Table 6-48)
    fields[-1]["children"].append({"field": "Unrecognized Command", "value": "Yes" if error_info & (1 << 0) else "No"})
    fields[-1]["children"].append({"field": "Non-Existent Connector Number", "value": "Yes" if error_info & (1 << 1) else "No"})
    fields[-1]["children"].append({"field": "Invalid Command Specific Parameters", "value": "Yes" if error_info & (1 << 2) else "No"})
    fields[-1]["children"].append({"field": "Incompatible Connector Partner", "value": "Yes" if error_info & (1 << 3) else "No"})
    fields[-1]["children"].append({"field": "CC Communication Error", "value": "Yes" if error_info & (1 << 4) else "No"})
    fields[-1]["children"].append({"field": "Command Unsuccessful Due to Dead Battery Condition", "value": "Yes" if error_info & (1 << 5) else "No"})
    fields[-1]["children"].append({"field": "Contract Negotiation Failure", "value": "Yes" if error_info & (1 << 6) else "No"})
    fields[-1]["children"].append({"field": "Overcurrent", "value": "Yes" if error_info & (1 << 7) else "No"})
    fields[-1]["children"].append({"field": "Undefined", "value": "Yes" if error_info & (1 << 8) else "No"})
    fields[-1]["children"].append({"field": "Port Partner Rejected Swap", "value": "Yes" if error_info & (1 << 9) else "No"})
    fields[-1]["children"].append({"field": "Hard Reset", "value": "Yes" if error_info & (1 << 10) else "No"})
    fields[-1]["children"].append({"field": "PPM Policy Conflict", "value": "Yes" if error_info & (1 << 11) else "No"})
    fields[-1]["children"].append({"field": "Swap Rejected", "value": "Yes" if error_info & (1 << 12) else "No"})
    fields[-1]["children"].append({"field": "Reverse Current Protection", "value": "Yes" if error_info & (1 << 13) else "No"})
    fields[-1]["children"].append({"field": "Set Sink Path Rejected", "value": "Yes" if error_info & (1 << 14) else "No"})
    fields[-1]["children"].append({"field": "Reserved (Bit 15)", "value": "0"})
    
    # Offset 16 (Bits 16+): Vendor Defined (if present)
    if len(resp_bytes) > 2:
        vendor_data_len = (len(resp_bytes) - 2) * 8
        vendor_data = resp_bytes[2:]
        vendor_hex = ' '.join(f"{b:02x}" for b in vendor_data)
        
        fields.append({
            "offset": "16",
            "field": "Vendor Defined",
            "size": str(vendor_data_len),
            "value": vendor_hex
        })
    
    out["fields"] = fields
    return out

def decode_current_cam(resp_bytes, version):
    """Decode GET_CURRENT_CAM response per UCSI 3.0 Table 6-32.
    
    Returns the offset(s) of alternate mode(s) the connector is currently operating in.
    Each byte represents one active alternate mode offset from the GET_ALTERNATE_MODES list.
    0xFF indicates the connector is not operating in any alternate mode.
    
    Note: Multiple bytes indicate the connector is operating in multiple alternate modes simultaneously.
    """
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) == 0:
        out["note"] = "No data returned - connector not in alternate mode"
        return out
    
    # Common alternate mode names based on typical offset positions
    # Note: Actual mapping depends on GET_ALTERNATE_MODES response
    COMMON_MODE_NAMES = {
        0: "Thunderbolt (typical offset 0)",
        1: "DisplayPort (typical offset 1)",
        2: "Alternate mode at offset 2",
        3: "Alternate mode at offset 3",
        4: "Alternate mode at offset 4"
    }
    
    # Create structured table format matching UCSI spec Table 6-32
    fields = []
    active_modes = []  # Track active modes for summary
    
    for i in range(len(resp_bytes)):
        cam_offset = resp_bytes[i]
        offset_bits = i * 8
        
        if cam_offset == 0xFF:
            value_str = "0xFF"
            description = "Not operating in any alternate mode"
            mode_status = "Inactive"
        else:
            mode_hint = COMMON_MODE_NAMES.get(cam_offset, f"Alternate mode at offset {cam_offset}")
            value_str = f"0x{cam_offset:02X} ({cam_offset} decimal)"
            description = f"{mode_hint}"
            mode_status = f"Active at offset {cam_offset}"
            active_modes.append(cam_offset)
        
        field_entry = {
            "offset": str(offset_bits),
            "field": f"Current Alternate Mode[{i}]",
            "size": "8",
            "value": value_str,
            "interpretation": f"Offset into the list of Alternate Modes that the connector is currently operating in. This is an offset into the list of Alternate Modes supported by the PPM. If the connector is not operating in an alternate mode, the PPM shall set this field to 0xFF."
        }
        
        # Add children with detailed information
        children = []
        
        if cam_offset != 0xFF:
            children.append({
                "field": "Status",
                "value": mode_status
            })
            children.append({
                "field": "Description",
                "value": description
            })
            children.append({
                "field": "Identify Mode",
                "value": f"Use GET_ALTERNATE_MODES to get SVID/MID for offset {cam_offset}"
            })
        else:
            children.append({
                "field": "Status",
                "value": description
            })
        
        if children:
            field_entry["children"] = children
        
        fields.append(field_entry)
    
    out["fields"] = fields
    out["cam_count"] = len(resp_bytes)
    
    # Add helpful summary
    if active_modes:
        if len(active_modes) == 1:
            out["note"] = f"Connector is operating in 1 alternate mode at offset {active_modes[0]}. Use GET_ALTERNATE_MODES to identify the SVID/MID."
        else:
            offsets_str = ", ".join(str(o) for o in active_modes)
            out["note"] = f"Connector is operating in {len(active_modes)} alternate modes simultaneously at offsets: {offsets_str}"
    else:
        out["note"] = "Connector is not operating in any alternate mode (all offsets are 0xFF)"
    
    out["active_mode_offsets"] = active_modes  # For programmatic access
    
    return out

def decode_cam_cs(resp_bytes, version):
    """Decode GET_CAM_CS (CAM Command Specific) response per UCSI 3.0 Table 6-60.
    
    Returns the status and VDOs for the currently active alternate mode.
    The format and interpretation of Status and VDO fields depend on the specific
    alternate mode (DisplayPort, Thunderbolt, etc.) as defined in their respective specifications.
    """
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 6:
        out["error"] = "Response too short (expected at least 6 bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-60
    fields = []
    
    # Offset 0 (Bits 0-7): Current Alternate Mode
    current_alt_mode = resp_bytes[0]
    fields.append({
        "offset": "0",
        "field": "Current Alternate Mode",
        "size": "8",
        "value": f"{current_alt_mode}",
        "interpretation": "The index of the Alternate Mode that is currently being used. This index is from the array of indexes obtained by the GET_CURRENT_CAM command."
    })
    
    # Offset 8 (Bits 8-39): Status (32 bits)
    status = struct.unpack_from("<I", resp_bytes, 1)[0]
    fields.append({
        "offset": "8",
        "field": "Status",
        "size": "32",
        "value": f"0x{status:08X}",
        "interpretation": "The status of the Current Alternate Mode. The Status for an Alternate Mode is defined in the specification that defines that Alternate Mode. If a status is not defined for the Alternate Mode, this field shall be set to 0."
    })
    
    # Offset 40 (Bits 40-47): Number of VDOs
    num_vdos = resp_bytes[5] if len(resp_bytes) > 5 else 0
    fields.append({
        "offset": "40",
        "field": "Number of VDOs",
        "size": "8",
        "value": f"{num_vdos}",
        "interpretation": f"Number of returned VDOs (N). {num_vdos} VDO(s) follow this field."
    })
    
    # Offset 48 onwards: VDO[N] - each VDO is 32 bits
    if num_vdos > 0 and len(resp_bytes) >= 6 + (num_vdos * 4):
        for i in range(num_vdos):
            vdo_offset = 6 + (i * 4)
            if len(resp_bytes) >= vdo_offset + 4:
                vdo = struct.unpack_from("<I", resp_bytes, vdo_offset)[0]
                bit_offset = 48 + (i * 32)
                fields.append({
                    "offset": str(bit_offset),
                    "field": f"VDO[{i}]",
                    "size": "32",
                    "value": f"0x{vdo:08X}",
                    "interpretation": f"Contains VDO {i}. The interpretation of this VDO depends on the specific Alternate Mode."
                })
    
    out["fields"] = fields
    out["current_mode_index"] = current_alt_mode
    out["status"] = status
    out["vdo_count"] = num_vdos
    out["note"] = f"Mode index {current_alt_mode} with {num_vdos} VDO(s). Status and VDO interpretation depends on the specific Alternate Mode specification."
    
    return out

def decode_alternate_modes(resp_bytes, version):
    """Decode GET_ALTERNATE_MODES response per UCSI 3.0 Table 6-26.
    
    Returns SVID/MID pairs (6 bytes each) for alternate modes.
    Each mode occupies 48 bits: SVID[n] (16 bits) + MID[n] (32 bits).
    The offset value from this list is used by GET_CURRENT_CAM and SET_NEW_CAM.
    """
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) == 0:
        out["note"] = "No alternate modes available"
        return out
    
    if len(resp_bytes) % 6 != 0:
        out["error"] = f"Invalid response length (expected multiple of 6 bytes, got {len(resp_bytes)} bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-26
    # Each alternate mode is 6 bytes (48 bits): SVID (16 bits) + MID (32 bits)
    fields = []
    alternate_modes = []  # For easy consumption by UI
    
    num_modes = len(resp_bytes) // 6
    
    # Known SVID mappings for common alternate mode identifiers
    SVID_NAMES = {
        0xFF01: "DisplayPort",
        0x8087: "Thunderbolt 3/4",
        0x04B4: "Cypress (USB4)",
        0x045E: "Microsoft",
        0x18D1: "Google",
        0x2109: "VIA Labs",
        0x0000: "Reserved"
    }
    
    for mode_idx in range(num_modes):
        offset = mode_idx * 6  # 6 bytes per mode
        offset_bits = offset * 8
        
        # Bits 0-15: SVID (Standard or Vendor ID)
        svid = struct.unpack_from("<H", resp_bytes, offset)[0]
        svid_name = SVID_NAMES.get(svid, f"Vendor 0x{svid:04X}")
        
        # Bits 16-47: MID (Mode ID) - 32 bits
        mid = struct.unpack_from("<I", resp_bytes, offset + 2)[0]
        
        # Create main field for this alternate mode
        mode_field = {
            "offset": str(offset_bits),
            "field": f"Alternate Mode Offset {mode_idx}: {svid_name}",
            "size": "48",
            "value": f"SVID: 0x{svid:04X}, MID: 0x{mid:08X}",
            "interpretation": f"Standard or Vendor ID (SVID) and Mode ID (MID) for alternate mode at offset {mode_idx}.",
            "children": []
        }
        
        # Add child fields with detailed information
        mode_field["children"].append({
            "field": "SVID[{0}] (Standard/Vendor ID)".format(mode_idx),
            "value": f"0x{svid:04X} - {svid_name}",
            "interpretation": "Standard or Vendor ID."
        })
        mode_field["children"].append({
            "field": "MID[{0}] (Mode ID)".format(mode_idx),
            "value": f"0x{mid:08X}",
            "interpretation": "Mode ID associated with the above SVID."
        })
        mode_field["children"].append({
            "field": "Usage",
            "value": f"Use offset {mode_idx} in GET_CURRENT_CAM/SET_NEW_CAM commands"
        })
        
        fields.append(mode_field)
        
        # Add to alternate_modes list for UI consumption
        alternate_modes.append({
            "index": mode_idx,
            "svid": f"0x{svid:04X}",
            "name": svid_name,
            "mid": f"0x{mid:08X}"
        })
    
    out["fields"] = fields
    out["mode_count"] = num_modes
    out["alternate_modes"] = alternate_modes  # Add for easy UI access
    out["note"] = f"Returned {num_modes} alternate mode(s). Each mode is identified by its offset (0-{num_modes-1})."
    
    return out

def decode_cam_supported(resp_bytes, version):
    """Decode GET_CAM_SUPPORTED response per UCSI 3.0 Table 6-29.
    
    Returns a bitmap of currently supported alternate modes on this connector.
    This is a subset of modes from GET_ALTERNATE_MODES - some modes may be unavailable
    if alternate mode resources are being used by other connectors.
    
    Workflow: GET_ALTERNATE_MODES → GET_CAM_SUPPORTED → SET_NEW_CAM
    """
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) == 0:
        out["note"] = "No alternate modes currently supported on this connector"
        return out
    
    # Create structured table format matching UCSI spec Table 6-29
    fields = []
    
    # Total number of bits
    total_bits = len(resp_bytes) * 8
    
    # Parse bmAlternateModeSuppported bitmap
    supported_modes = []
    for byte_idx, byte_val in enumerate(resp_bytes):
        for bit_idx in range(8):
            mode_index = byte_idx * 8 + bit_idx
            if byte_val & (1 << bit_idx):
                supported_modes.append(mode_index)
    
    # Offset 0 (Bits 0-N): bmAlternateModeSuppported
    # N varies based on number of supported modes
    bitmap_hex = ' '.join(f"{b:02x}" for b in resp_bytes)
    
    fields.append({
        "offset": "0",
        "field": "bmAlternateModeSuppported (Bitmap)",
        "size": str(total_bits),
        "value": f"{bitmap_hex}",
        "interpretation": "If an Alternate Mode is supported, then that bit position shall be set to one. Else it shall be set to zero.",
        "children": []
    })
    
    # Add each supported mode as a child
    if supported_modes:
        for mode_idx in supported_modes:
            fields[-1]["children"].append({
                "field": f"Offset {mode_idx}",
                "value": f"Supported - Can be used in SET_NEW_CAM"
            })
        out["note"] = f"Currently supports {len(supported_modes)} alternate mode(s). These offsets can be used with SET_NEW_CAM."
    else:
        fields[-1]["children"].append({
            "field": "No Alternate Modes",
            "value": "All bits are zero - no modes currently supported"
        })
        out["note"] = "No alternate modes are currently supported on this connector (all bits zero)"
    
    # Calculate zero bits padding
    n = total_bits  # Total bits used
    if n % 8 == 0:
        m = 0
    else:
        m = 8 - (n % 8)
    
    if m > 0:
        fields.append({
            "offset": str(n),
            "field": "ZeroBits",
            "size": str(m),
            "value": "0 (Padding to byte boundary)",
            "interpretation": f"If (N Mod 8 == 0) then M = 0, else M = (8 - (N Mod 8)). The PPM shall set these bits to zero. Here M={m}."
        })
    
    out["fields"] = fields
    out["supported_modes_count"] = len(supported_modes)
    out["supported_modes"] = supported_modes
    
    return out

def decode_attention_vdo(resp_bytes, version):
    """Decode GET_ATTENTION_VDO response per UCSI 3.0 Table 6-57."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    # Handle empty response - this is NORMAL when no attention event occurred
    if len(resp_bytes) == 0:
        out["Command_Status"] = "✓ Command Completed Successfully - No Attention VDO Available"
        out["Explanation"] = "Empty response (0 bytes) is correct behavior when no Attention event has occurred"
        out["Reason"] = "No Attention message has been received from port partner, or VDO was already retrieved"
        out["When_Data_Appears"] = "MESSAGE_IN will contain data only after receiving an Attention message from port partner"
        out["Expected_Data_Format"] = "When available: 11 bytes containing Alt Mode Index (2), Control byte (1), VDM Header (4), VDO (4)"
        out["Next_Step"] = "Wait for Attention notification, then query again to retrieve VDO"
        out["Note"] = "⚠ This is NOT an error - the command executed successfully but there's no attention data to return"
        return out
    
    if len(resp_bytes) < 3:
        out["Error"] = f"Response too short ({len(resp_bytes)} bytes) - expected at least 3 bytes"
        out["Minimum_Format"] = "Alt Mode Index (2 bytes) + Control byte (1 byte) = 3 bytes minimum"
        out["Received_Data"] = ' '.join(f"{b:02x}" for b in resp_bytes)
        return out
    
    # Valid response - parse the structure
    out["Command_Status"] = "✓ Attention VDO Retrieved Successfully"
    out["Description"] = "VDO received from port partner after an Attention message"
    
    # Create structured table format matching UCSI spec Table 6-57
    fields = []
    
    # Offset 0 (Bits 0-15): Alt Mode Index
    alt_mode_index = struct.unpack_from("<H", resp_bytes, 0)[0]
    if alt_mode_index == 0xFF or alt_mode_index == 0xFFFF:
        alt_mode_str = f"0xFF (Not currently operating in Alternate Mode)"
        out["Alternate_Mode_Status"] = "Not Operating in Alternate Mode"
    else:
        alt_mode_str = f"{alt_mode_index} (Offset into supported Alternate Modes list)"
        out["Alternate_Mode_Status"] = f"Operating in Alternate Mode at offset {alt_mode_index}"
    
    fields.append({
        "offset": "0 (Bits 0-15)",
        "field": "Alt Mode Index",
        "size": "16 bits (2 bytes)",
        "value": alt_mode_str,
        "interpretation": "Offset into the list of Alternate Modes supported by PPM. If not operating in Alternate Mode, set to 0xFF."
    })
    
    # Read byte 2 for bits 16-23
    byte2 = resp_bytes[2] if len(resp_bytes) > 2 else 0
    
    # Offset 16 (Bits 16-18): Number of VDOs
    num_vdos = byte2 & 0x07
    fields.append({
        "offset": "16 (Bits 16-18)",
        "field": "Number of VDOs",
        "size": "3 bits",
        "value": f"{num_vdos} VDO(s)",
        "interpretation": "Number of returned VDOs. Set to 1 if a VDO is returned, 0 if not returned."
    })
    
    # Offset 19 (Bits 19-20): Reserved
    reserved_bits = (byte2 >> 3) & 0x03
    fields.append({
        "offset": "19 (Bits 19-20)",
        "field": "Reserved",
        "size": "2 bits",
        "value": f"{reserved_bits} (should be 0)",
        "interpretation": "Reserved and shall be set to zero."
    })
    
    # Offset 21 (Bits 21-23): Sequence Number
    sequence_num = (byte2 >> 5) & 0x07
    fields.append({
        "offset": "21 (Bits 21-23)",
        "field": "Sequence Number",
        "size": "3 bits",
        "value": f"{sequence_num}",
        "interpretation": "Identifies ordering of GET_ATTENTION_VDO completion data. Increments by 1 for each set, rolls over to 0."
    })
    
    out["Number_of_VDOs"] = num_vdos
    out["Sequence_Number"] = sequence_num
    
    # Offset 24 (Bits 24-55): VDM Header
    if len(resp_bytes) >= 7:
        vdm_header = struct.unpack_from("<I", resp_bytes, 3)[0]
        fields.append({
            "offset": "24 (Bits 24-55)",
            "field": "VDM Header",
            "size": "32 bits (4 bytes)",
            "value": f"0x{vdm_header:08X}",
            "interpretation": "Contains the Vendor Defined Message Header",
            "children": []
        })
        
        # Decode VDM Header fields according to USB PD spec
        vdm_type = (vdm_header >> 15) & 0x01
        svid = (vdm_header >> 16) & 0xFFFF
        
        fields[-1]["children"].append({"field": "SVID (Standard/Vendor ID)", "value": f"0x{svid:04X}"})
        fields[-1]["children"].append({"field": "VDM Type", "value": "Structured VDM" if vdm_type else "Unstructured VDM"})
        
        if vdm_type:  # Structured VDM
            vdm_version = (vdm_header >> 13) & 0x03
            obj_pos = (vdm_header >> 8) & 0x07
            cmd_type = (vdm_header >> 6) & 0x03
            cmd = vdm_header & 0x1F
            
            vdm_ver_names = {0: "1.0", 1: "2.0", 2: "2.1", 3: "Reserved"}
            cmd_type_names = {0: "REQ (Request)", 1: "ACK (Acknowledge)", 2: "NAK (Not Acknowledge)", 3: "BUSY"}
            
            fields[-1]["children"].append({"field": "VDM Version", "value": vdm_ver_names.get(vdm_version, f"Unknown ({vdm_version})")})
            fields[-1]["children"].append({"field": "Object Position", "value": f"{obj_pos}"})
            fields[-1]["children"].append({"field": "Command Type", "value": cmd_type_names.get(cmd_type, f"Unknown ({cmd_type})")})
            fields[-1]["children"].append({"field": "Command", "value": f"0x{cmd:02X} ({cmd})"})
        else:  # Unstructured VDM
            data = vdm_header & 0x7FFF
            fields[-1]["children"].append({"field": "Unstructured Data", "value": f"0x{data:04X}"})
        
        out["VDM_Type"] = "Structured" if vdm_type else "Unstructured"
        out["SVID"] = f"0x{svid:04X}"
    else:
        out["Warning"] = f"Response too short for VDM Header (need 7 bytes, got {len(resp_bytes)})"
    
    # Offset 56 (Bits 56-87): VDO
    if len(resp_bytes) >= 11:
        vdo = struct.unpack_from("<I", resp_bytes, 7)[0]
        fields.append({
            "offset": "56 (Bits 56-87)",
            "field": "VDO (Vendor Defined Object)",
            "size": "32 bits (4 bytes)",
            "value": f"0x{vdo:08X}",
            "interpretation": "Contains the Vendor Defined Object data. Content depends on SVID and command."
        })
        out["VDO_Value"] = f"0x{vdo:08X}"
    elif num_vdos > 0:
        out["Warning"] = f"Response indicates {num_vdos} VDO(s) but data too short (need 11 bytes, got {len(resp_bytes)})"
    
    out["fields"] = fields
    out["Total_Data_Length"] = f"{len(resp_bytes)} bytes ({len(resp_bytes)*8} bits)"
    
    return out

def decode_cable_property(resp_bytes, version):
    """Decode GET_CABLE_PROPERTY response per Table 6-40."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    # Create structured table format matching UCSI spec Table 6-40
    fields = []
    
    # Handle partial response (some implementations return 5 bytes instead of 8)
    if len(resp_bytes) < 5:
        out["error"] = "Response too short (expected at least 5 bytes)"
        return out
    
    # Pad response to 8 bytes if needed
    padded_bytes = resp_bytes + b'\x00' * (8 - len(resp_bytes))
    data_qword = struct.unpack_from("<Q", padded_bytes, 0)[0]
    
    if len(resp_bytes) < 8:
        out["Note"] = f"Partial response received ({len(resp_bytes)} bytes). Spec expects 8 bytes. Bytes 5-7 assumed zero."
    
    # Offset 0 (Bits 0-15): bmSpeedSupported
    speed_supported = data_qword & 0xFFFF
    speed_exponent = speed_supported & 0x03
    speed_mantissa = (speed_supported >> 2) & 0x3FFF
    
    speed_exp_names = {0: "Bits per second", 1: "Kb/s", 2: "Mb/s", 3: "Gb/s"}
    
    fields.append({
        "offset": "0",
        "field": "bmSpeedSupported",
        "size": "16",
        "value": f"0x{speed_supported:04x}",
        "interpretation": "Speed Exponent (bits 1:0) defines the base 10 exponent times 3, applied to the Speed Mantissa (bits 15:2) when calculating the maximum bit rate that this cable supports. 0=bps, 1=Kb/s, 2=Mb/s, 3=Gb/s",
        "children": []
    })
    
    # bmSpeedSupported sub-fields
    fields[-1]["children"].append({"field": "Speed Exponent (SE)", "value": f"{speed_exponent} ({speed_exp_names.get(speed_exponent, 'Unknown')})"})
    fields[-1]["children"].append({"field": "Speed Mantissa (SM)", "value": f"{speed_mantissa}"})
    
    # Offset 16 (Bits 16-23): bCurrentCapability
    current_capability = (data_qword >> 16) & 0xFF
    current_ma = current_capability * 50
    fields.append({
        "offset": "16",
        "field": "bCurrentCapability",
        "size": "8",
        "value": f"{current_capability} ({current_ma}mA)",
        "interpretation": "Return the amount of current the cable is designed for in 50mA units."
    })
    
    # Offset 24 (Bit 24): VBUSInCable
    vbus_in_cable = (data_qword >> 24) & 0x01
    fields.append({
        "offset": "24",
        "field": "VBUSInCable",
        "size": "1",
        "value": "Yes" if vbus_in_cable else "No",
        "interpretation": "The PPM shall set this field to a one if the cable has a VBUS connection from end to end."
    })
    
    # Offset 25 (Bit 25): CableType
    cable_type = (data_qword >> 25) & 0x01
    fields.append({
        "offset": "25",
        "field": "CableType",
        "size": "1",
        "value": "Active" if cable_type else "Passive",
        "interpretation": "The PPM shall set this field to one if the cable is an Active cable otherwise it shall set this field to zero if the cable is a Passive cable."
    })
    
    # Offset 26 (Bit 26): Directionality
    directionality = (data_qword >> 26) & 0x01
    fields.append({
        "offset": "26",
        "field": "Directionality",
        "size": "1",
        "value": "Configurable" if directionality else "Fixed",
        "interpretation": "The PPM shall set this field to one if the lane directionality is configurable else it shall set this field to zero if the lane directionality is fixed in the cable."
    })
    
    # Offset 27 (Bits 27-28): Plug End Type
    plug_end_type = (data_qword >> 27) & 0x03
    plug_type_names = {0: "USB Type-A", 1: "USB Type-B", 2: "USB Type-C", 3: "Other (Not USB)"}
    fields.append({
        "offset": "27",
        "field": "Plug End Type",
        "size": "2",
        "value": plug_type_names.get(plug_end_type, f"Unknown ({plug_end_type})"),
        "interpretation": "0=USB Type-A, 1=USB Type-B, 2=USB Type-C, 3=Other (Not USB)"
    })
    
    # Offset 29 (Bit 29): Mode Support
    mode_support = (data_qword >> 29) & 0x01
    fields.append({
        "offset": "29",
        "field": "Mode Support",
        "size": "1",
        "value": "Yes" if mode_support else "No",
        "interpretation": "This field shall only be valid if the CableType field is set to one. This field shall indicate that the cable supports Alternate Modes. The OPM can use the GET_ALTERNATE_MODE command to get the list of modes this cable supports."
    })
    
    # Offset 30 (Bits 30-31): Cable PD Revision
    cable_pd_rev = (data_qword >> 30) & 0x03
    pd_rev_names = {0: "Reserved", 1: "PD 1.0", 2: "PD 2.0", 3: "PD 3.0"}
    fields.append({
        "offset": "30",
        "field": "Cable PD Revision",
        "size": "2",
        "value": pd_rev_names.get(cable_pd_rev, f"Unknown ({cable_pd_rev})"),
        "interpretation": "Cable's major USB PD Revision from the Specification Revision field of the USB PD Message Header."
    })
    
    # Offset 32 (Bits 32-35): Latency
    latency = (data_qword >> 32) & 0x0F
    fields.append({
        "offset": "32",
        "field": "Latency",
        "size": "4",
        "value": f"{latency}",
        "interpretation": "See Table 6-41 in the [USBPD] for additional information on the contents of this field."
    })
    
    # Offset 36 (Bits 36-63): Reserved
    fields.append({
        "offset": "36",
        "field": "Reserved",
        "size": "28",
        "value": "0",
        "interpretation": "Reserved and shall be set to zero."
    })
    
    out["fields"] = fields
    return out

def decode_lpm_ppm_info(resp_bytes, version):
    """Decode GET_LPM_PPM_INFO response per Table 6-82."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    if len(resp_bytes) < 16:
        out["error"] = "Response too short (expected at least 16 bytes)"
        return out
    
    # Create structured table format matching UCSI spec Table 6-82
    fields = []
    
    # Offset 0 (Bits 0-15): VID
    vid = struct.unpack_from("<H", resp_bytes, 0)[0]
    fields.append({
        "offset": "0",
        "field": "VID",
        "size": "16",
        "value": f"0x{vid:04X}",
        "interpretation": "Vendor ID of LPM/PPM."
    })
    
    # Offset 16 (Bits 16-31): PID
    pid = struct.unpack_from("<H", resp_bytes, 2)[0]
    fields.append({
        "offset": "16",
        "field": "PID",
        "size": "16",
        "value": f"0x{pid:04X}",
        "interpretation": "Product ID of LPM/PPM."
    })
    
    # Offset 32 (Bits 32-63): XID
    xid = struct.unpack_from("<I", resp_bytes, 4)[0]
    fields.append({
        "offset": "32",
        "field": "XID",
        "size": "32",
        "value": f"0x{xid:08X}",
        "interpretation": "Identifier value assigned to the product."
    })
    
    # Offset 64 (Bits 64-95): FW Version Upper
    if len(resp_bytes) >= 12:
        fw_version_upper = struct.unpack_from("<I", resp_bytes, 8)[0]
        fields.append({
            "offset": "64",
            "field": "FW Version Upper",
            "size": "32",
            "value": f"0x{fw_version_upper:08X}",
            "interpretation": "FW Version."
        })
    
    # Offset 96 (Bits 96-127): FW Version Lower
    if len(resp_bytes) >= 16:
        fw_version_lower = struct.unpack_from("<I", resp_bytes, 12)[0]
        fields.append({
            "offset": "96",
            "field": "FW Version Lower",
            "size": "32",
            "value": f"0x{fw_version_lower:08X}",
            "interpretation": "Sub. FW Version."
        })
    
    # Offset 128 (Bits 128-159): HW Version (bytes 16-19, total 20 bytes needed)
    if len(resp_bytes) >= 20:
        hw_version = struct.unpack_from("<I", resp_bytes, 16)[0]
        fields.append({
            "offset": "128",
            "field": "HW Version",
            "size": "32",
            "value": f"0x{hw_version:08X}",
            "interpretation": "HW version of LPM/PPM."
        })
    
    out["fields"] = fields
    return out

def decode_pd_message(resp_bytes, version):
    """Decode GET_PD_MESSAGE response per UCSI 3.0 Tables 6-51 to 6-54."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    # Response Message Type definitions
    MESSAGE_TYPES = {
        0: "Sink_Capabilities_Extended (Extended Message)",
        1: "Source_Capabilities_Extended (Extended Message)",
        2: "Battery_Capabilities (Extended Message)",
        3: "Battery_Status (Data Message)",
        4: "Discover Identity Response - ACK/NAK/BUSY (Structured VDM)",
        5: "Revision (Data Message)"
    }
    
    RECIPIENT_TYPES = {
        0: "Connector (Platform's own capabilities)",
        1: "SOP (Port Partner)",
        2: "SOP' (Cable Plug)",
        3: "SOP'' (Cable Plug)"
    }
    
    # Handle empty response
    if len(resp_bytes) == 0:
        out["Command_Status"] = "⚠ No Data Returned"
        out["Explanation"] = "Empty response - check CCI Error Indicator to determine if this is an error"
        out["Common_Reasons"] = [
            "Command failed (Error Indicator = 1)",
            "Port partner not present (when Recipient = SOP/SOP'/SOP'')",
            "Message type not supported by connector or partner",
            "Invalid parameters in command",
            "Requested offset beyond message size"
        ]
        out["Response_Message_Types"] = MESSAGE_TYPES
        out["Recipient_Field"] = RECIPIENT_TYPES
        out["Next_Step"] = "If Error Indicator=1, check GET_ERROR_STATUS for specific error code"
        return out
    
    # Determine likely message type based on data size and content
    likely_type = None
    if len(resp_bytes) >= 16:
        # Check if it looks like Sink/Source Capabilities Extended (21-24 bytes typical)
        if len(resp_bytes) >= 21 or (len(resp_bytes) >= 16 and resp_bytes[0:2] != b'\x00\x00'):
            likely_type = 0  # Likely Sink_Capabilities_Extended
    
    out["Command_Status"] = "✓ PD Message Data Retrieved Successfully"
    out["Data_Length"] = f"{len(resp_bytes)} bytes ({len(resp_bytes)*8} bits)"
    out["Likely_Message_Type"] = MESSAGE_TYPES.get(likely_type, "Unknown - depends on command parameters")
    out["Supported_Message_Types"] = MESSAGE_TYPES
    
    # Decode based on likely message type
    fields = []
    
    if len(resp_bytes) >= 16:
        # Decode as Sink Capabilities Extended (most common, Tables 6-53 and 6-54)
        out["Decoding_As"] = "Sink Capabilities Extended (Type 0) - Common format"
        out["Note"] = "If this doesn't match expected data, response may be different message type"
        
        # Offset 0 (Bits 0-15): VID
        vid = struct.unpack_from("<H", resp_bytes, 0)[0]
        fields.append({
            "offset": "0 (Bits 0-15)",
            "field": "VID (Vendor ID)",
            "size": "16 bits (2 bytes)",
            "value": f"0x{vid:04X}",
            "interpretation": "USB vendor identifier"
        })
        
        # Offset 16 (Bits 16-31): PID
        pid = struct.unpack_from("<H", resp_bytes, 2)[0]
        fields.append({
            "offset": "16 (Bits 16-31)",
            "field": "PID (Product ID)",
            "size": "16 bits (2 bytes)",
            "value": f"0x{pid:04X}",
            "interpretation": "Product ID assigned by vendor"
        })
        
        # Offset 32 (Bits 32-63): XID
        xid = struct.unpack_from("<I", resp_bytes, 4)[0]
        fields.append({
            "offset": "32 (Bits 32-63)",
            "field": "XID",
            "size": "32 bits (4 bytes)",
            "value": f"0x{xid:08X}",
            "interpretation": "Identifier value assigned to the product"
        })
        
        # Offset 64 (Bits 64-71): FW Version
        if len(resp_bytes) >= 9:
            fw_version = resp_bytes[8]
            fields.append({
                "offset": "64 (Bits 64-71)",
                "field": "FW Version",
                "size": "8 bits (1 byte)",
                "value": f"0x{fw_version:02X} ({fw_version})",
                "interpretation": "Firmware version"
            })
        
        # Offset 72 (Bits 72-79): HW Version
        if len(resp_bytes) >= 10:
            hw_version = resp_bytes[9]
            fields.append({
                "offset": "72 (Bits 72-79)",
                "field": "HW Version",
                "size": "8 bits (1 byte)",
                "value": f"0x{hw_version:02X} ({hw_version})",
                "interpretation": "Hardware version"
            })
        
        # Offset 80 (Bits 80-87): SKEDB Version
        if len(resp_bytes) >= 11:
            skedb_version = resp_bytes[10]
            fields.append({
                "offset": "80 (Bits 80-87)",
                "field": "SKEDB Version",
                "size": "8 bits (1 byte)",
                "value": f"0x{skedb_version:02X} ({skedb_version})",
                "interpretation": "Sink Keyboard Database version"
            })
        
        # Offset 88 (Bits 88-95): Load Step
        if len(resp_bytes) >= 12:
            load_step = resp_bytes[11]
            fields.append({
                "offset": "88 (Bits 88-95)",
                "field": "Load Step",
                "size": "8 bits (1 byte)",
                "value": f"0x{load_step:02X} ({load_step} mA)",
                "interpretation": "Load step in 10mA increments"
            })
        
        # Offset 96 (Bits 96-111): Sink Load Characteristics
        if len(resp_bytes) >= 14:
            load_char = struct.unpack_from("<H", resp_bytes, 12)[0]
            fields.append({
                "offset": "96 (Bits 96-111)",
                "field": "Sink Load Characteristics",
                "size": "16 bits (2 bytes)",
                "value": f"0x{load_char:04X}",
                "interpretation": "Bitmap describing sink load characteristics"
            })
        
        # Offset 112 (Bits 112-119): Compliance
        if len(resp_bytes) >= 15:
            compliance = resp_bytes[14]
            fields.append({
                "offset": "112 (Bits 112-119)",
                "field": "Compliance",
                "size": "8 bits (1 byte)",
                "value": f"0x{compliance:02X}",
                "interpretation": "Compliance bitmap"
            })
        
        # Offset 120 (Bits 120-127): Touch Temp
        if len(resp_bytes) >= 16:
            touch_temp = resp_bytes[15]
            fields.append({
                "offset": "120 (Bits 120-127)",
                "field": "Touch Temp",
                "size": "8 bits (1 byte)",
                "value": f"0x{touch_temp:02X} ({touch_temp}°C)",
                "interpretation": "Maximum touch temperature"
            })
        
        # Second part of Sink Capabilities Extended (if present)
        if len(resp_bytes) >= 17:
            out["Additional_Fields"] = "Message continues beyond first 16 bytes"
            
            # Offset 128 (Bits 0-7 of 2nd part): Battery Info
            battery_info = resp_bytes[16]
            fields.append({
                "offset": "128 (Bits 0-7 of Part 2)",
                "field": "Battery Info",
                "size": "8 bits (1 byte)",
                "value": f"0x{battery_info:02X}",
                "interpretation": "Battery information bitmap"
            })
        
        if len(resp_bytes) >= 18:
            # Offset 136: Sink Modes
            sink_modes = resp_bytes[17]
            fields.append({
                "offset": "136 (Bits 8-15 of Part 2)",
                "field": "Sink Modes",
                "size": "8 bits (1 byte)",
                "value": f"0x{sink_modes:02X}",
                "interpretation": "Sink operational modes"
            })
        
        if len(resp_bytes) >= 19:
            # Offset 144: Sink Minimum PDP
            min_pdp = resp_bytes[18]
            fields.append({
                "offset": "144 (Bits 16-23 of Part 2)",
                "field": "Sink Minimum PDP",
                "size": "8 bits (1 byte)",
                "value": f"0x{min_pdp:02X} ({min_pdp * 0.5}W)",
                "interpretation": "Minimum power in 0.5W increments"
            })
        
        if len(resp_bytes) >= 20:
            # Offset 152: Sink Operational PDP
            op_pdp = resp_bytes[19]
            fields.append({
                "offset": "152 (Bits 24-31 of Part 2)",
                "field": "Sink Operational PDP",
                "size": "8 bits (1 byte)",
                "value": f"0x{op_pdp:02X} ({op_pdp * 0.5}W)",
                "interpretation": "Operational power in 0.5W increments"
            })
        
        if len(resp_bytes) >= 21:
            # Offset 160: Sink Maximum PDP
            max_pdp = resp_bytes[20]
            fields.append({
                "offset": "160 (Bits 32-39 of Part 2)",
                "field": "Sink Maximum PDP",
                "size": "8 bits (1 byte)",
                "value": f"0x{max_pdp:02X} ({max_pdp * 0.5}W)",
                "interpretation": "Maximum power in 0.5W increments"
            })
        
        out["fields"] = fields
        
        if len(resp_bytes) == 21:
            out["Message_Complete"] = "✓ Full Sink Capabilities Extended message (21 bytes)"
        elif len(resp_bytes) < 21:
            out["Message_Partial"] = f"⚠ Partial message ({len(resp_bytes)}/21 bytes) - may be chunked request"
        else:
            out["Extra_Data"] = f"⚠ {len(resp_bytes) - 21} extra bytes beyond standard 21-byte message"
    
    else:
        # Response is too short for Sink Capabilities Extended
        out["Decoding_As"] = "Unknown/Short Message"
        out["Note"] = "Response too short for Sink Capabilities Extended. May be different message type or error."
        
        # Try to show raw data
        if len(resp_bytes) >= 2:
            word0 = struct.unpack_from("<H", resp_bytes, 0)[0]
            fields.append({
                "offset": "0",
                "field": "Word 0",
                "value": f"0x{word0:04X}",
                "interpretation": "First 2 bytes - interpretation depends on message type"
            })
        
        if len(resp_bytes) >= 4:
            word1 = struct.unpack_from("<H", resp_bytes, 2)[0]
            fields.append({
                "offset": "2",
                "field": "Word 1",
                "value": f"0x{word1:04X}",
                "interpretation": "Bytes 2-3 - interpretation depends on message type"
            })
        
        if fields:
            out["fields"] = fields
        
        out["Raw_Bytes"] = ' '.join(f"{b:02X}" for b in resp_bytes)
    
    out["Command_Parameters_Note"] = "Actual content depends on Response Message Type, Recipient, Message Offset, and Number of Bytes in command"
    
    return out
    # Decoding as Sink Capabilities Extended (most common)
    fields = []
    
    # Table 6-53: 1st Part of Sink Capabilities Extended (16 bytes)
    
    # Offset 0 (Bits 0-15): VID
    vid = struct.unpack_from("<H", resp_bytes, 0)[0]
    fields.append({
        "offset": "0",
        "field": "VID",
        "size": "16",
        "value": f"0x{vid:04X}"
    })
    
    # Offset 16 (Bits 16-31): PID
    pid = struct.unpack_from("<H", resp_bytes, 2)[0]
    fields.append({
        "offset": "16",
        "field": "PID",
        "size": "16",
        "value": f"0x{pid:04X}"
    })
    
    # Offset 32 (Bits 32-63): XID
    xid = struct.unpack_from("<I", resp_bytes, 4)[0]
    fields.append({
        "offset": "32",
        "field": "XID",
        "size": "32",
        "value": f"0x{xid:08X}"
    })
    
    # Offset 64 (Bits 64-71): FW Version
    fw_version = struct.unpack_from("<B", resp_bytes, 8)[0]
    fields.append({
        "offset": "64",
        "field": "FW Version",
        "size": "8",
        "value": f"0x{fw_version:02X}"
    })
    
    # Offset 72 (Bits 72-79): HW Version
    hw_version = struct.unpack_from("<B", resp_bytes, 9)[0]
    fields.append({
        "offset": "72",
        "field": "HW Version",
        "size": "8",
        "value": f"0x{hw_version:02X}"
    })
    
    # Offset 80 (Bits 80-87): SKEDB Version
    skedb_version = struct.unpack_from("<B", resp_bytes, 10)[0]
    fields.append({
        "offset": "80",
        "field": "SKEDB Version",
        "size": "8",
        "value": f"0x{skedb_version:02X}"
    })
    
    # Offset 88 (Bits 88-95): Load Step
    load_step = struct.unpack_from("<B", resp_bytes, 11)[0]
    fields.append({
        "offset": "88",
        "field": "Load Step",
        "size": "8",
        "value": f"0x{load_step:02X}"
    })
    
    # Offset 96 (Bits 96-111): Sink Load Characteristics
    sink_load_char = struct.unpack_from("<H", resp_bytes, 12)[0]
    fields.append({
        "offset": "96",
        "field": "Sink Load Characteristics",
        "size": "16",
        "value": f"0x{sink_load_char:04X}"
    })
    
    # Offset 112 (Bits 112-119): Compliance
    compliance = struct.unpack_from("<B", resp_bytes, 14)[0]
    fields.append({
        "offset": "112",
        "field": "Compliance",
        "size": "8",
        "value": f"0x{compliance:02X}"
    })
    
    # Offset 120 (Bits 120-127): Touch Temp
    touch_temp = struct.unpack_from("<B", resp_bytes, 15)[0]
    fields.append({
        "offset": "120",
        "field": "Touch Temp",
        "size": "8",
        "value": f"0x{touch_temp:02X}"
    })
    
    # Table 6-54: 2nd Part of Sink Capabilities Extended (5 bytes, if present)
    if len(resp_bytes) >= 21:
        # Offset 128 (Bits 0-7 of 2nd part): Battery Info
        battery_info = struct.unpack_from("<B", resp_bytes, 16)[0]
        fields.append({
            "offset": "128",
            "field": "Battery Info",
            "size": "8",
            "value": f"0x{battery_info:02X}"
        })
        
        # Offset 136 (Bits 8-15 of 2nd part): Sink Modes
        sink_modes = struct.unpack_from("<B", resp_bytes, 17)[0]
        fields.append({
            "offset": "136",
            "field": "Sink Modes",
            "size": "8",
            "value": f"0x{sink_modes:02X}"
        })
        
        # Offset 144 (Bits 16-23 of 2nd part): Sink Minimum PDP
        sink_min_pdp = struct.unpack_from("<B", resp_bytes, 18)[0]
        fields.append({
            "offset": "144",
            "field": "Sink Minimum PDP",
            "size": "8",
            "value": f"0x{sink_min_pdp:02X}"
        })
        
        # Offset 152 (Bits 24-31 of 2nd part): Sink Operational PDP
        sink_op_pdp = struct.unpack_from("<B", resp_bytes, 19)[0]
        fields.append({
            "offset": "152",
            "field": "Sink Operational PDP",
            "size": "8",
            "value": f"0x{sink_op_pdp:02X}"
        })
        
        # Offset 160 (Bits 32-39 of 2nd part): Sink Maximum PDP
        sink_max_pdp = struct.unpack_from("<B", resp_bytes, 20)[0]
        fields.append({
            "offset": "160",
            "field": "Sink Maximum PDP",
            "size": "8",
            "value": f"0x{sink_max_pdp:02X}"
        })
    
    out["fields"] = fields
    return out

def decode_read_power_level(resp_bytes, version):
    """Decode READ_POWER_LEVEL response per UCSI 3.0 Tables 6-85 and 6-86."""
    out = {"raw_len": len(resp_bytes), "raw_hex": format_hex_bytes(resp_bytes)}
    
    out["Command_Status"] = "✓ Power Level Read Initiated Successfully"
    out["Description"] = "Power measurement process started. Actual power data will be available via GET_CONNECTOR_STATUS"
    out["Expected_Response"] = "Empty (No data returned for this command)"
    out["How_It_Works"] = "1) READ_POWER_LEVEL starts measurement | 2) LPM measures during Time To Read period | 3) Connector Change Indicator raised when ready | 4) Use GET_CONNECTOR_STATUS to retrieve power data"
    out["Important_Note"] = "⚠ Only works when LPM is in SOURCING mode with active connection. Returns error if sinking or no connection."
    out["Next_Step"] = "Wait for Connector Change Indicator, then run GET_CONNECTOR_STATUS to see Peak/Average Power data"
    out["Spec_Reference"] = "See Section 6.5.32 and Appendix A.5 for READ_POWER_LEVEL workflow"
    
    if len(resp_bytes) > 0:
        out["Warning"] = "⚠ Response contains unexpected data (should be empty per UCSI spec)"
    
    return out

# Decoder mapping
DECODER_MAP = {
    "4 - ACK_CC_CI": decode_ack_cc_ci,
    "3 - CONNECTOR_RESET": decode_connector_reset,
    "5 - SET_NOTIFICATION_ENABLE": decode_set_notification_enable,
    "9 - SET_UOR (DFP)": decode_set_uor,
    "9 - SET_UOR (UFP)": decode_set_uor,
    "9 - SET_UOR (Accept Swap)": decode_set_uor,
    "9 - SET_UOR (Swap to DFP)": decode_set_uor,
    "9 - SET_UOR (Swap to UFP)": decode_set_uor,
    "B - SET_PDR (Provider)": decode_set_pdr,
    "B - SET_PDR (Consumer)": decode_set_pdr,
    "B - SET_PDR (Accept Swap)": decode_set_pdr,
    "B - SET_PDR (Swap to Provider)": decode_set_pdr,
    "B - SET_PDR (Swap to Consumer)": decode_set_pdr,
    "1B - SET_RETIMER_MODE": decode_set_retimer_mode,
    "14 - SET_POWER_LEVEL": decode_set_power_level,
    "14 - SET_POWER_LEVEL (Source)": decode_set_power_level,
    "14 - SET_POWER_LEVEL (Sink)": decode_set_power_level,
    "6 - GET_CAPABILITY": decode_capability,
    "7 - GET_CONNECTOR_CAPABILITY": decode_connector_capability,
    "12 - GET_CONNECTOR_STATUS": decode_connector_status,
    "C - GET_ALTERNATE_MODES": decode_alternate_modes,
    "C - GET_ALTERNATE_MODES (Connector)": decode_alternate_modes,
    "C - GET_ALTERNATE_MODES (Partner)": decode_alternate_modes,
    "10 - GET_PDOS (Local Source)": decode_get_pdos,
    "10 - GET_PDOS (Local Sink)": decode_get_pdos,
    "10 - GET_PDOS (Partner Source)": decode_get_pdos,
    "10 - GET_PDOS (Partner Sink)": decode_get_pdos,
    "11 - GET_CABLE_PROPERTY": decode_cable_property,
    "D - GET_CAM_SUPPORTED": decode_cam_supported,
    "E - GET_CURRENT_CAM": decode_current_cam,
    "18 - GET_CAM_CS": decode_cam_cs,
    "16 - GET_ATTENTION_VDO": decode_attention_vdo,
    "13 - GET_ERROR_STATUS": decode_error_status,
    "22 - GET_LPM_PPM_INFO": decode_lpm_ppm_info,
    "15 - GET_PD_MESSAGE": decode_pd_message,
    "1E - READ_POWER_LEVEL": decode_read_power_level,
}

def get_decoder(command_key):
    """Get decoder function for a command key."""
    return DECODER_MAP.get(command_key, None)
