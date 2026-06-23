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
Decoder Service
Wraps the original decode rs module for UCSI command/response decoding.
"""

import sys
import os

# Add parent directory to path to import original decoders module
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import from original decoders module
from decoders import ucsi_decoders

# Re-export all functions
decode_hex_string = ucsi_decoders.decode_hex_string
get_decoder = ucsi_decoders.get_decoder
decode_generic = ucsi_decoders.decode_generic
format_hex_bytes = ucsi_decoders.format_hex_bytes

# Re-export specific decoders
decode_get_capability = ucsi_decoders.decode_capability
decode_get_connector_capability = ucsi_decoders.decode_connector_capability
decode_get_connector_status = ucsi_decoders.decode_connector_status
decode_get_cable_property = ucsi_decoders.decode_cable_property
decode_get_pdos = ucsi_decoders.decode_get_pdos
decode_get_alternate_modes = ucsi_decoders.decode_alternate_modes
decode_get_cam_supported = ucsi_decoders.decode_cam_supported
decode_get_current_cam = ucsi_decoders.decode_current_cam
decode_get_pd_message = ucsi_decoders.decode_get_pd_message if hasattr(ucsi_decoders, 'decode_get_pd_message') else None
decode_get_attention_vdo = ucsi_decoders.decode_attention_vdo
decode_get_error_status = ucsi_decoders.decode_error_status
decode_read_power_level = ucsi_decoders.decode_read_power_level
decode_get_lpm_ppm_info = ucsi_decoders.decode_lpm_ppm_info

__all__ = [
    'decode_hex_string',
    'get_decoder',
    'decode_generic',
    'format_hex_bytes',
    'decode_get_capability',
    'decode_get_connector_capability',
    'decode_get_connector_status',
    'decode_get_cable_property',
    'decode_get_pdos',
    'decode_get_alternate_modes',
    'decode_get_cam_supported',
    'decode_get_current_cam',
    'decode_get_pd_message',
    'decode_get_attention_vdo',
    'decode_get_error_status',
    'decode_read_power_level',
    'decode_get_lpm_ppm_info',
]
