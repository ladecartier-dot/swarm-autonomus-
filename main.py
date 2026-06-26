"""
Main entry point for Render/Railway deployment
Imports Flask app from web/server.py
"""
import sys
import os

# Add web directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

# Import app from server.py
from server import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
