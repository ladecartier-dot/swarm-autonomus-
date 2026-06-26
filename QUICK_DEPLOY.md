# 🚀 Quick Deploy - Swarm Trader Macro Dashboard

## Option 1: Automated Script (Recommended)

### 1. Setup VPS

```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y
```

### 2. Run Deployment

```bash
# Download deployment script
cd ~
curl -O https://raw.githubusercontent.com/your-repo/swarm-trader/main/deploy.sh
chmod +x deploy.sh

# Run automated deployment
./deploy.sh
```

The script will:
- ✅ Install Python & dependencies
- ✅ Create virtual environment
- ✅ Setup Flask application
- ✅ Configure systemd service
- ✅ Setup Nginx reverse proxy
- ✅ Start the dashboard

### 3. Configure API Keys

```bash
# Edit API keys
nano ~/swarm-trader/state/api_keys.env

# Add your keys:
export FRED_API_KEY="your_fred_key"
export ALPHA_VANTAGE_KEY="your_av_key"

# Restart service
systemctl restart swarm-macro
```

### 4. Access Dashboard

```
http://your-vps-ip/macro
http://your-vps-ip/api/macro
```

---

## Option 2: Manual Deploy (Full Control)

Follow the complete guide in `DEPLOY_VPS.md`

---

## Option 3: Docker Deploy

```bash
# Clone repo
git clone https://github.com/your-repo/swarm-trader.git
cd swarm-trader

# Setup environment
cp .env.example .env
nano .env  # Add your API keys

# Deploy with Docker Compose
docker-compose up -d
```

Access at: `http://localhost:5000/macro`

---

## Option 4: Cloud Platforms

### Render (Free Tier)
1. Push code to GitHub
2. Connect repo to Render
3. Add environment variables (FRED_API_KEY, ALPHA_VANTAGE_KEY)
4. Deploy!

### Railway
1. `railway login`
2. `railway init`
3. Add environment variables
4. `railway up`

---

## 🔧 Post-Deployment

### Setup Domain & SSL

```bash
# Point domain to VPS IP
# A record: macro.yourdomain.com → your-vps-ip

# Install SSL certificate
certbot --nginx -d macro.yourdomain.com
```

### Firewall Setup

```bash
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### Monitoring

```bash
# Check service status
systemctl status swarm-macro

# View logs
journalctl -u swarm-macro -f

# Test API
curl http://localhost:5000/api/macro
```

---

## 📊 VPS Recommendations

| Provider | Plan | RAM | CPU | Storage | Price/mo |
|----------|------|-----|-----|---------|----------|
| DigitalOcean | Basic | 1GB | 1 vCPU | 25GB | $6 |
| Hetzner | CPX11 | 2GB | 2 vCPU | 40GB | €5 |
| Linode | Nanode | 1GB | 1 vCPU | 25GB | $5 |
| AWS | Lightsail | 1GB | 1 vCPU | 32GB | $3.50 |

**Recommended:** Hetzner (best value) or DigitalOcean (easiest)

---

## 🆘 Troubleshooting

### Service Not Starting
```bash
journalctl -u swarm-macro -n 50 --no-pager
```

### API Keys Not Working
```bash
# Verify keys are loaded
cat ~/swarm-trader/state/api_keys.env
source ~/swarm-trader/state/api_keys.env
echo $FRED_API_KEY
```

### Port 5000 In Use
```bash
lsof -i:5000
kill -9 <PID>
systemctl restart swarm-macro
```

---

## 📝 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | ✅ | FRED economic data API key |
| `ALPHA_VANTAGE_KEY` | ✅ | Alpha Vantage market data API key |
| `FLASK_ENV` | ❌ | Set to `production` for prod |
| `LOG_LEVEL` | ❌ | Logging level (INFO, DEBUG, ERROR) |

---

**Deployment Time:** 5-15 minutes  
**Difficulty:** Easy to Intermediate  
**Cost:** $5-10/month (VPS)

Need help? Check `DEPLOY_VPS.md` for detailed instructions!
