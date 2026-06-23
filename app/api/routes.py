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
API Routes for UCSI Decoder
Flask route definitions for the web API.

TODO: Migrate all routes from app.py to this file

Example structure:
- GET  /                           - Main page
- POST /api/decode                  - Decode UCSI response
- POST /api/execute_command         - Execute UCSI command
- GET  /api/platform-info           - Get platform information
- GET  /api/check_device            - Check UCSI device status
- GET  /api/check_aardvark          - Check Aardvark connection
etc.
"""

from flask import Blueprint, render_template, request, jsonify
import platform

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Example route - this shows the structure
# Actual routes should be migrated from app.py

@api_bp.route('/')
def index():
    """Main page route."""
    return render_template('index.html')


@api_bp.route('/api/platform-info', methods=['GET'])
def get_platform_info():
    """Get platform information."""
    return jsonify({
        'platform': platform.system(),
        'python_version': platform.python_version(),
        'architecture': platform.machine()
    })


# TODO: Migrate remaining routes from app.py:
# - /api/decode
# - /api/execute_command
# - /api/sudo-auth
# - /api/ucsi-status
# - /api/commands
# - /api/command/<int:cmd_id>
# - /api/format_command
# - /api/check_device
# - /api/check_aardvark
# - /api/scan_i2c_bus
# - /api/i2c_address_info
# - /api/set_ppm_address
# etc.

def register_routes(app):
    """
    Register all routes with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(api_bp)
