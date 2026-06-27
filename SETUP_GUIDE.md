# 🚀 Swarm Trader - Quick Setup Guide

## ⚡ 3-Minute Setup (Using Docker)

### **Prerequisites:**
- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Git cloned repo

### **Step 1: Clone & Enter Directory**
```bash
cd /mnt/data/hermes/workspace/swarm-trader
```

### **Step 2: Run Setup Script**
```bash
./setup_database.sh
```

This will:
- ✅ Start PostgreSQL + TimescaleDB via Docker
- ✅ Create database `swarm_trader`
- ✅ Create user `swarm_user`
- ✅ Run schema.sql (create 9 tables)
- ✅ Verify connection

### **Step 3: Configure .env**
```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

**Required API Keys (add these):**
```bash
# Get free API keys:
GLASSNODE_API_KEY=your_key_here      # https://glassnode.com
COINGLASS_API_KEY=your_key_here      # https://coinglass.com/api
BINANCE_API_KEY=your_key_here        # https://binance.com
```

**Already configured (FREE):**
```bash
FRED_API_KEY=8101e05db182ccd505bc50920a8f097c  # ✅ Ready
ALPHA_VANTAGE_KEY=CS37J2Y39A7P4BHS         # ✅ Ready
```

### **Step 4: Verify Setup**
```bash
# Check if database is running
docker ps | grep swarm_postgres

# Check tables
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c "\dt"

# Should show 9 tables:
# ohlcv, futures_metrics, macro_indicators, onchain_metrics,
# cycle_labels, sentiment_data, news_headlines, smc_patterns,
# similarity_matches
```

---

## 🐳 Docker Commands

### **Start Database:**
```bash
docker-compose up -d postgres
```

### **Stop Database:**
```bash
docker-compose down
```

### **Restart Database:**
```bash
docker-compose restart
```

### **View Logs:**
```bash
docker-compose logs -f postgres
```

### **Access Database CLI:**
```bash
docker exec -it swarm_postgres psql -U swarm_user -d swarm_trader
```

### **Backup Database:**
```bash
docker exec swarm_postgres pg_dump -U swarm_user swarm_trader > backup.sql
```

### **Restore Database:**
```bash
docker exec -i swarm_postgres psql -U swarm_user swarm_trader < backup.sql
```

---

## 🖥️ Manual Setup (Without Docker)

If you prefer to install PostgreSQL directly:

### **Ubuntu/Debian:**
```bash
# Install PostgreSQL 15 + TimescaleDB
sudo apt update
sudo apt install postgresql-15 postgresql-15-timescaledb

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE swarm_trader;
CREATE USER swarm_user WITH PASSWORD 'swarm_password_2026';
GRANT ALL PRIVILEGES ON DATABASE swarm_trader TO swarm_user;
EOF

# Run schema
psql -U swarm_user -d swarm_trader -f data/storage/postgres/schema.sql
```

### **macOS (Homebrew):**
```bash
# Install PostgreSQL + TimescaleDB
brew install postgresql@15
brew tap timescale/tap
brew install timescaledb

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb swarm_trader
psql -d swarm_trader -c "CREATE USER swarm_user WITH PASSWORD 'swarm_password_2026';"
psql -d swarm_trader -c "GRANT ALL PRIVILEGES ON DATABASE swarm_trader TO swarm_user;"

# Run schema
psql -U swarm_user -d swarm_trader -f data/storage/postgres/schema.sql
```

### **Windows:**
1. Download PostgreSQL 15: https://www.postgresql.org/download/windows/
2. During installation, select TimescaleDB extension
3. Open pgAdmin and create database `swarm_trader`
4. Run `schema.sql` in pgAdmin

---

## 🔧 Configure .env File

### **Database Configuration (Default):**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=swarm_user
DB_PASSWORD=swarm_password_2026
DB_NAME=swarm_trader
```

### **Free API Keys (Already Configured):**
```bash
FRED_API_KEY=8101e05db182ccd505bc50920a8f097c
ALPHA_VANTAGE_KEY=CS37J2Y39A7P4BHS
```

### **Optional API Keys (Recommended for Production):**

**1. Glassnode (On-Chain Data):**
- Get free API key: https://glassnode.com
- Free tier: 10 calls/hour
```bash
GLASSNODE_API_KEY=your_key_here
```

**2. Coinglass (Futures Data):**
- Get free API key: https://coinglass.com/api
- Free tier: Limited calls/day
```bash
COINGLASS_API_KEY=your_key_here
```

**3. Binance (Real-time OHLCV):**
- Get API key: https://www.binance.com/en/my/settings/api-management
- Free: Unlimited public API calls
```bash
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
```

**4. CryptoPanic (News - FREE):**
- Get free API key: https://cryptopanic.com/developers/api/
```bash
CRYPTOPANIC_API_KEY=your_key_here
```

---

## ✅ Verify Setup

### **1. Check Database Connection:**
```bash
docker exec swarm_postgres pg_isready -U swarm_user -d swarm_trader
# Should return: swarm_postgres:5432 - accepting connections
```

### **2. Check Tables:**
```bash
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c "\dt"
```

Expected output:
```
                 List of relations
 Schema |        Name         | Type |  Owner   
--------+---------------------+------+----------
 public | cycle_labels        | table | swarm_user
 public | futures_metrics     | table | swarm_user
 public | macro_indicators    | table | swarm_user
 public | news_headlines      | table | swarm_user
 public | ohlcv               | table | swarm_user
 public | onchain_metrics     | table | swarm_user
 public | sentiment_data      | table | swarm_user
 public | similarity_matches  | table | swarm_user
 public | smc_patterns        | table | swarm_user
```

### **3. Test Data Insertion:**
```bash
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c \
  "INSERT INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume) 
   VALUES ('BTCUSDT', '1D', NOW(), 60000, 61000, 59000, 60500, 1000);"
```

### **4. Verify Data:**
```bash
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c \
  "SELECT * FROM ohlcv;"
```

---

## 🚀 Next Steps

After setup is complete:

### **1. Run Data Collection:**
```bash
./run_data_collection.sh BTC,ETH,SOL 2010-01-01 $(date +%Y-%m-%d)
```

### **2. Monitor Progress:**
```bash
# Check row counts
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c \
  "SELECT 'ohlcv' as table_name, COUNT(*) as row_count FROM ohlcv
   UNION ALL SELECT 'futures_metrics', COUNT(*) FROM futures_metrics
   UNION ALL SELECT 'macro_indicators', COUNT(*) FROM macro_indicators;"
```

### **3. Start Real-Time Collectors:**
```bash
# Run in background
python data/collectors/ohlcv_collector.py --symbol BTC --realtime &
python data/collectors/futures_collector.py --symbol BTC --realtime &
```

---

## 🛠️ Troubleshooting

### **Issue: Docker not found**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### **Issue: Port 5432 already in use**
```bash
# Find what's using port 5432
lsof -i :5432

# Stop existing PostgreSQL
sudo systemctl stop postgresql

# Or change port in docker-compose.yml to 5433
```

### **Issue: Permission denied on schema.sql**
```bash
chmod 644 data/storage/postgres/schema.sql
```

### **Issue: Database won't start**
```bash
# Check logs
docker-compose logs postgres

# Remove old data and restart
docker-compose down -v
docker-compose up -d postgres
```

### **Issue: API rate limits**
- Use free tiers first (FRED, Alpha Vantage already configured)
- Add delays between API calls
- Consider paid tiers for production

---

## 📞 Support

**Documentation:**
- `docs/README_DATA_COLLECTION.md` - Complete guide
- `docs/QUICK_START.md` - Quick start
- `docs/DATA_INFRASTRUCTURE.md` - Architecture

**Files:**
- `docker-compose.yml` - Docker setup
- `setup_database.sh` - Automated setup script
- `.env.example` - Environment template
- `data/storage/postgres/schema.sql` - Database schema

---

**Setup should take 3-5 minutes. Then you're ready to collect data!** 🚀

*Generated by Swarm Trader AI - Jun 26, 2026*
