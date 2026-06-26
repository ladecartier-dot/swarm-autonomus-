# 🚀 Swarm Trader Macro Dashboard - VPS Deployment Guide

## 📋 Prerequisites

- VPS with Ubuntu 20.04+ (DigitalOcean, Hetzner, AWS, etc.)
- Root or sudo access
- Domain/subdomain (optional, for HTTPS)
- FRED API Key (free: https://fred.stlouisfed.org/api-key)
- Alpha Vantage API Key (free: https://www.alphavantage.co/support/#api-key)

## 🔧 Quick Deploy (5 minutes)

```bash
# 1. Clone/setup project
mkdir -p ~/swarm-trader && cd ~/swarm-trader

# 2. Run deployment script
curl -O https://raw.githubusercontent.com/your-repo/swarm-trader/main/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## 📦 Manual Installation

### 1. System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot
```

### 2. Application Setup

```bash
cd ~/swarm-trader

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install flask flask-cors aiohttp pyngrok
```

### 3. Configuration

```bash
# Create state directory
mkdir -p state

# Create API keys file
cat > state/api_keys.env << 'EOF'
export FRED_API_KEY="your_fred_key_here"
export ALPHA_VANTAGE_KEY="your_av_key_here"
EOF

chmod 600 state/api_keys.env
```

### 4. Systemd Service

```bash
sudo tee /etc/systemd/system/swarm-macro.service > /dev/null << 'EOF'
[Unit]
Description=Swarm Trader Macro Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/swarm-trader
Environment="PATH=/home/ubuntu/swarm-trader/venv/bin"
ExecStart=/home/ubuntu/swarm-trader/venv/bin/python web/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable swarm-macro
sudo systemctl start swarm-macro
```

### 5. Nginx Reverse Proxy

```bash
sudo tee /etc/nginx/sites-available/swarm-macro > /dev/null << 'EOF'
server {
    listen 80;
    server_name macro.yourdomain.com;  # Change to your domain

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/swarm-macro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (HTTPS)

```bash
sudo certbot --nginx -d macro.yourdomain.com
```

## 🔍 Verify Deployment

```bash
# Check service status
sudo systemctl status swarm-macro

# Check logs
sudo journalctl -u swarm-macro -f

# Test locally
curl http://localhost:5000/api/macro

# Test publicly
curl https://macro.yourdomain.com/api/macro
```

## 🛡️ Security Hardening

### Firewall (UFW)

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### API Key Protection

```bash
# Restrict access to api_keys.env
chmod 600 state/api_keys.env
chown ubuntu:ubuntu state/api_keys.env

# Never commit to git
echo "state/api_keys.env" >> .gitignore
```

### Rate Limiting (Nginx)

```bash
# Add to nginx config
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
        # ... rest of config
    }
}
```

## 📊 Monitoring

### Log Rotation

```bash
sudo tee /etc/logrotate.d/swarm-macro > /dev/null << 'EOF'
/home/ubuntu/swarm-trader/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
EOF
```

### Health Check Script

```bash
cat > ~/check-macro.sh << 'EOF'
#!/bin/bash
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/macro)
if [ "$RESPONSE" -eq 200 ]; then
    echo "✅ Macro Dashboard OK"
    exit 0
else
    echo "❌ Macro Dashboard FAILED (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x ~/check-macro.sh
```

### Cron Health Check

```bash
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/check-macro.sh") | crontab -
```

## 🔄 Update Deployment

```bash
cd ~/swarm-trader
git pull  # or copy new files

sudo systemctl restart swarm-macro
sudo systemctl status swarm-macro
```

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u swarm-macro -n 50 --no-pager

# Test manually
cd ~/swarm-trader
source venv/bin/activate
source state/api_keys.env
python web/server.py
```

### Port 5000 Already in Use

```bash
# Find and kill process
sudo lsof -ti:5000 | xargs kill -9

# Or change port in server.py
# app.run(host='0.0.0.0', port=5001)
```

### Nginx 502 Bad Gateway

```bash
# Check if Flask is running
sudo systemctl status swarm-macro

# Check nginx error log
sudo tail -f /var/log/nginx/error.log

# Restart both
sudo systemctl restart swarm-macro
sudo systemctl restart nginx
```

## 📈 Performance Tuning

### Use Gunicorn (Production WSGI)

```bash
pip install gunicorn

# Update systemd service
sudo tee /etc/systemd/system/swarm-macro.service > /dev/null << 'EOF'
[Unit]
Description=Swarm Trader Macro Dashboard
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/swarm-trader
Environment="PATH=/home/ubuntu/swarm-trader/venv/bin"
ExecStart=/home/ubuntu/swarm-trader/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 web.server:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart swarm-macro
```

### Redis Caching (Optional)

For high-traffic deployments, add Redis caching for FRED API calls:

```bash
sudo apt install -y redis-server
pip install redis

# Add to server.py
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)
```

## 🎯 Recommended VPS Specs

| Traffic Level | CPU | RAM | Storage | Cost/mo |
|--------------|-----|-----|---------|---------|
| Personal Use | 1 vCPU | 1GB | 25GB | $5-6 |
| Small Team | 2 vCPU | 2GB | 50GB | $10-12 |
| Production | 4 vCPU | 4GB | 80GB | $20-24 |

**Recommended Providers:**
- DigitalOcean ($6/mo)
- Hetzner (€5/mo, EU)
- Linode ($5/mo)
- AWS Lightsail ($3.50/mo)
- Vultr ($6/mo)

---

**Deployment Time:** ~15 minutes  
**Difficulty:** Intermediate  
**Uptime:** 99.9%+ with proper setup
