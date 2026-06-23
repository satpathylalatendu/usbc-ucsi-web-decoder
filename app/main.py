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
UCSI Decoder Web Application - Main Entry Point  
Professional structured Flask application for USB Type-C UCSI protocol analysis.

NOTE: This is the new professional structure entry point.
      The original app.py at the root level is still fully functional.
      This new structure provides better organization for contributors.
      
To run with the new structure (once routes are migrated):
    python -m app.main
    
To run with the original structure:
    python app.py
"""

import sys
import os
import platform

# Add parent directory to path for compatibility
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from flask import Flask

# Application metadata
__version__ = "1.0.0"
__author__ = "Lalatendu Satpathy"

# Debug flag
DEBUG = os.getenv('DEBUG', '0') == '1'

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Create Flask app with correct paths
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    
    # Configure app
    app.config['SECRET_KEY'] = 'ucsi-decoder-secret-key-2026'
    app.config['DEBUG'] = DEBUG
    
    # Import and register routes
    # TODO: Create app/api/routes.py with all Flask routes
    # For now, point users to the original app.py
    
    @app.route('/')
    def index():
        return """
        <html>
        <head><title>UCSI Decoder - New Structure</title></head>
        <body style="font-family: Arial; padding: 40px; max-width: 800px; margin: auto;">
            <h1>🚀 UCSI Web Decoder - New Professional Structure</h1>
            <p><strong>Version:</strong> 1.0.0</p>
            
            <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>✅ New Structure Created!</h2>
                <p>The professional project structure has been set up:</p>
                <ul>
                    <li><code>app/</code> - Main application package</li>
                    <li><code>app/api/</code> - API routes (to be migrated)</li>
                    <li><code>app/backend/</code> - Platform-specific backends</li>
                    <li><code>app/services/</code> - Business logic</li>
                    <li><code>app/templates/</code> - HTML templates</li>
                    <li><code>app/static/</code> - Static assets</li>
                </ul>
            </div>
            
            <div style="background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>📝 Next Steps</h2>
                <p>The original fully-functional application is still available at the root level.</p>
                <p><strong>To use the working application:</strong></p>
                <pre style="background: #333; color: #fff; padding: 10px; border-radius: 3px;">python app.py</pre>
                
                <p><strong>To contribute to the new structure:</strong></p>
                <ol>
                    <li>Gradually migrate routes from <code>app.py</code> to <code>app/api/routes.py</code></li>
                    <li>Update imports to use new backend modules</li>
                    <li>Add tests in <code>tests/</code> directory</li>
                    <li>See <code>CONTRIBUTING.md</code> for guidelines</li>
                </ol>
            </div>
            
            <div style="background: #d4edda; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h2>📦 New Modules Available</h2>
                <ul>
                    <li><code>app.backend.linux_ucsi</code> - Linux debugfs operations</li>
                    <li><code>app.backend.windows_ucsi</code> - Windows UcsiControl operations</li>
                    <li><code>app.backend.aardvark</code> - Aardvark hardware interface</li>
                    <li><code>app.services.decoder</code> - UCSI protocol decoders</li>
                    <li><code>app.services.decoder</code> - UCSI command decoding</li>
                </ul>
            </div>
            
            <p style="margin-top: 40px; color: #666;">
                <strong>Platform:</strong> """ + platform.system() + """<br>
                <strong>Python:</strong> """ + sys.version.split()[0] + """
            </p>
        </body>
        </html>
        """
    
    return app


def main():
    """Main entry point for the application."""
    print("=" * 70)
    print("UCSI Web Decoder v1.0.0 - Professional Edition")
    print("=" * 70)
    print()
    print("📁 New professional structure ready!")
    print("📝 See CONTRIBUTING.md for migration guide")
    print()
    print("⚠️  NOTE: Routes not fully migrated yet")
    print("    Use 'python app.py' for full functionality")
    print("    Or contribute route migration to app/api/routes.py")
    print()
    print("Starting development server...")
    print("=" * 70)
    
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)


if __name__ == '__main__':
    main()
