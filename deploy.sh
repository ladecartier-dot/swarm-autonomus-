#!/bin/bash
# 🚀 Swarm Trader Macro Dashboard - Automated Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Swarm Trader Macro Dashboard - VPS Deployment"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="$HOME/swarm-trader"
SERVICE_NAME="swarm-macro"
PYTHON_VERSION="python3"

echo -e "${YELLOW}📦 Step 1: System Updates${NC}"
sudo apt update -qq
sudo apt upgrade -y -qq
sudo apt install -y -qq python3 python3-venv python3-pip nginx curl wget

echo -e "${GREEN}✅ System packages installed${NC}"
echo ""

echo -e "${YELLOW}📂 Step 2: Application Setup${NC}"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy project files (adjust source path as needed)
# For now, create minimal structure
mkdir -p web templates state logs data

echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

echo -e "${YELLOW}🐍 Step 3: Python Virtual Environment${NC}"
$PYTHON_VERSION -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install flask flask-cors aiohttp -q

echo -e "${GREEN}✅ Python environment ready${NC}"
echo ""

echo -e "${YELLOW}🔑 Step 4: API Configuration${NC}"
read -p "Enter your FRED API Key (or press Enter to skip): " FRED_KEY
read -p "Enter your Alpha Vantage API Key (or press Enter to skip): " AV_KEY

cat > state/api_keys.env << EOF
# Swarm Trader API Keys
export FRED_API_KEY="${FRED_KEY:-your_fred_key_here}"
export ALPHA_VANTAGE_KEY="${AV_KEY:-your_av_key_here}"
EOF

chmod 600 state/api_keys.env
echo -e "${GREEN}✅ API keys configured${NC}"
echo ""

echo -e "${YELLOW}📝 Step 5: Creating Flask Application${NC}"
cat > web/server.py << 'PYEOF'
"""
Swarm Trader Macro Dashboard - Production Server
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API keys
env_file = Path(__file__).parent.parent / 'state' / 'api_keys.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith('export '):
                line = line[7:]
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value

app = Flask(__name__, template_folder='../templates')
CORS(app)

@app.route('/')
def dashboard():
    return render_template('macro_dashboard.html')

@app.route('/macro')
def macro_dashboard():
    return render_template('macro_dashboard.html')

@app.route('/api/macro')
def get_macro_data():
    """Get live macroeconomic data"""
    try:
        # Simplified for deployment - returns mock data if APIs not configured
        fred_key = os.environ.get('FRED_API_KEY', '')
        av_key = os.environ.get('ALPHA_VANTAGE_KEY', '')
        
        if not fred_key or fred_key == 'your_fred_key_here':
            return jsonify({
                'error': 'API keys not configured',
                'message': 'Please update state/api_keys.env with valid keys',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Full implementation would fetch from FRED/Alpha Vantage here
        return jsonify({
            'status': 'configured',
            'message': 'API keys valid - full implementation in main project',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Swarm Trader Macro Dashboard...")
    print(f"📊 Dashboard: http://localhost:5000/macro")
    print(f"📡 API: http://localhost:5000/api/macro")
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

echo -e "${GREEN}✅ Flask application created${NC}"
echo ""

echo -e "${YELLOW}🎨 Step 6: Creating Dashboard Template${NC}"
cat > templates/macro_dashboard.html << 'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏛️ Macro Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            text-align: center;
            background: rgba(255,255,255,0.05);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            padding: 15px 30px;
            border-radius: 10px;
            margin: 20px 0;
            font-size: 1.2rem;
        }
        .status.success { background: rgba(0,255,136,0.2); color: #00ff88; }
        .status.warning { background: rgba(255,215,0,0.2); color: #ffd700; }
        .status.error { background: rgba(255,71,87,0.2); color: #ff4757; }
        .info { color: #888; margin-top: 30px; }
        code {
            background: rgba(0,0,0,0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ Macro Dashboard</h1>
        <div id="status" class="status warning">⏳ Loading...</div>
        <div id="message"></div>
        <div class="info">
            <p>📊 Access API: <code>/api/macro</code></p>
            <p>🔄 Auto-refreshes every 60 seconds</p>
        </div>
    </div>
    
    <script>
        async function checkStatus() {
            try {
                const res = await fetch('/api/macro');
                const data = await res.json();
                
                const statusEl = document.getElementById('status');
                const messageEl = document.getElementById('message');
                
                if (data.error) {
                    statusEl.className = 'status error';
                    statusEl.textContent = '❌ Configuration Required';
                    messageEl.innerHTML = `<p>${data.message}</p>`;
                } else {
                    statusEl.className = 'status success';
                    statusEl.textContent = '✅ Dashboard Active';
                    messageEl.innerHTML = `<p>Server running on ${window.location.hostname}</p>`;
                }
            } catch (err) {
                document.getElementById('status').textContent = '❌ Connection Failed';
            }
        }
        
        checkStatus();
        setInterval(checkStatus, 60000);
    </script>
</body>
</html>
HTMLEOF

echo -e "${GREEN}✅ Dashboard template created${NC}"
echo ""

echo -e "${YELLOW}⚙️ Step 7: Systemd Service${NC}"
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Swarm Trader Macro Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python web/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo -e "${GREEN}✅ Systemd service configured${NC}"
echo ""

echo -e "${YELLOW}🌐 Step 8: Nginx Configuration${NC}"
sudo tee /etc/nginx/sites-available/swarm-macro > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/swarm-macro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo -e "${GREEN}✅ Nginx configured${NC}"
echo ""

echo -e "${YELLOW}🔥 Step 9: Starting Service${NC}"
sudo systemctl start $SERVICE_NAME
sleep 3

echo -e "${GREEN}✅ Service started${NC}"
echo ""

echo -e "${YELLOW}🔍 Step 10: Verification${NC}"
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/macro)
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "503" ]; then
    echo -e "${GREEN}✅ API responding (HTTP $RESPONSE)${NC}"
else
    echo -e "${YELLOW}⚠️ API returned HTTP $RESPONSE${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "📊 Dashboard: http://$(hostname -I | awk '{print $1}')/macro"
echo "📡 API: http://$(hostname -I | awk '{print $1}')/api/macro"
echo ""
echo "🔧 Useful Commands:"
echo "  - Status: sudo systemctl status $SERVICE_NAME"
echo "  - Logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  - Restart: sudo systemctl restart $SERVICE_NAME"
echo "  - Stop: sudo systemctl stop $SERVICE_NAME"
echo ""
echo "📝 Next Steps:"
echo "  1. Update API keys: nano $APP_DIR/state/api_keys.env"
echo "  2. Copy full project files to $APP_DIR"
echo "  3. Setup domain & SSL (see DEPLOY_VPS.md)"
echo "  4. Configure firewall: sudo ufw allow 80,443,22"
echo ""
echo "================================================"
