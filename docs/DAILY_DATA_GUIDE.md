# 🕐 Daily Data Fetching - Complete Guide

## Overview

The Swarm Trader system can automatically fetch real-time market data daily from multiple sources, store it historically, and use it for analysis and signal generation.

---

## 📊 What Data Gets Fetched

| Data Type | Source | Frequency | Storage |
|-----------|--------|-----------|---------|
| **Current Prices** | CoinGecko | Every 4h | JSON + Blackboard |
| **OHLCV (D1/H4/H1)** | Binance | Every 4h | JSON + Blackboard |
| **Fear & Greed Index** | Alternative.me | Daily | JSON + Blackboard |
| **Funding Rates** | Binance | Every 4h | JSON + Blackboard |
| **Market Stats** | CoinGecko | Daily | JSON |

---

## 🚀 Quick Start

### 1. Test Manual Fetch

```bash
cd /mnt/data/hermes/workspace/swarm-trader
source venv/bin/activate

# Fetch real-time data
python data/daily_fetch.py
```

### 2. Check Output

```bash
# View latest data
cat data/historical/latest.json | python -m json.tool

# View today's file
cat data/historical/daily_data_$(date +%Y-%m-%d).json
```

### 3. Set Up Automation

```bash
# Generate crontab entries
python utils/cron_scheduler.py

# Copy the generated crontab entries
crontab -e  # Then paste the entries
```

---

## 📁 Data Storage Structure

```
swarm-trader/data/historical/
├── daily_data_2026-06-26.json    # Today's data
├── daily_data_2026-06-25.json    # Yesterday's data
├── daily_data_2026-06-24.json    # etc...
├── latest.json                    # Symlink to latest
└── daily_data_2026-06-26_mock.json # Mock data for testing
```

Each file contains:
```json
{
  "timestamp": "2026-06-26T00:05:00",
  "prices": {
    "BTCUSD": {"price": 95000, "change_24h": 2.5, ...},
    "ETHUSD": {...},
    ...
  },
  "ohlcv": {
    "BTCUSD": {
      "D1": [[timestamp, O, H, L, C, V], ...],
      "H4": [...],
      "H1": [...]
    }
  },
  "fear_greed": {"value": 45, "classification": "Neutral"},
  "funding_rates": {
    "BTCUSDT": {"funding_rate": 0.0001, ...}
  }
}
```

---

## 🕐 Automated Schedule

Once cron is installed, data is fetched automatically:

| Time (UTC) | Task |
|------------|------|
| **00:05** | Daily data fetch (after D1 candle close) |
| **04:05** | H4 data update |
| **08:05** | H4 data update |
| **12:05** | H4 data update |
| **16:05** | H4 data update |
| **20:05** | H4 data update |
| **01:00** | Deep daily analysis (BTCUSD) |
| **Sun 02:00** | Weekly backtest |

---

## 📋 Cron Setup (Step by Step)

### Option 1: Manual Install (Recommended)

1. **Generate crontab:**
   ```bash
   python utils/cron_scheduler.py
   ```

2. **Copy the output**

3. **Edit crontab:**
   ```bash
   crontab -e
   ```

4. **Paste the entries** and save

5. **Verify:**
   ```bash
   crontab -l
   ```

### Option 2: Automatic Install

```bash
# WARNING: This replaces your entire crontab!
python utils/cron_scheduler.py | crontab -

# Or append to existing:
(crontab -l 2>/dev/null; python utils/cron_scheduler.py) | crontab -
```

### Option 3: Use Generated File

```bash
# The script saves to swarm_crontab.txt
crontab swarm_crontab.txt
```

---

## 🔍 Monitoring

### Check Cron Logs

```bash
# Watch data fetch logs
tail -f logs/daily_data.log

# Watch signal logs
tail -f logs/signals.log

# Watch all logs
tail -f logs/*.log
```

### Check Data Files

```bash
# List all data files
ls -lh data/historical/

# Check latest data
cat data/historical/latest.json | python -m json.tool | head -50
```

### Check Blackboard

```bash
# SQLite database
sqlite3 state/blackboard.db "SELECT * FROM market_cache LIMIT 5;"
```

---

## 🧪 Testing

### Test Single Fetch

```bash
python data/daily_fetch.py
```

### Test with Mock Data

```bash
# Generate realistic mock data (for testing when APIs unavailable)
python data/mock_generator.py

# Verify
cat data/historical/latest.json | python -m json.tool
```

### Test Full Pipeline

```bash
# 1. Fetch data
python data/daily_fetch.py

# 2. Run analysis
python main.py --run

# 3. Generate signals
python signals/generate_signals.py --all

# 4. Check output
cat state/signals.json
```

---

## 🛠️ Troubleshooting

### APIs Rate Limited (429 Error)

**Symptom:** `Rate limited` or `429 Too Many Requests`

**Solution:**
1. Wait 5-10 minutes
2. Use backup source (CoinPaprika)
3. Use mock data for testing:
   ```bash
   python data/mock_generator.py
   ```

### APIs Unavailable (451 Error)

**Symptom:** `451 Unavailable For Legal Reasons`

**Solution:**
- Your region may block certain APIs
- Use a VPS in a different region
- Use mock data generator

### Cron Not Running

**Check cron status:**
```bash
# Check if cron is running
systemctl status cron  # Linux
sudo systemctl status crond  # Some systems

# Start if needed
sudo systemctl start cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | tail -20
```

**Test cron manually:**
```bash
# Run the command that cron would run
cd /mnt/data/hermes/workspace/swarm-trader
source venv/bin/activate
python data/daily_fetch.py
```

### Data Not Saving

**Check permissions:**
```bash
ls -la data/historical/
chmod 755 data/historical/
```

**Check disk space:**
```bash
df -h
```

---

## 📊 Data Usage

### In Swarm Analysis

The orchestrator automatically uses cached data:

```python
# orchestrator.py
ohlcv = await self._fetch_ohlcv(symbol)
# First checks blackboard cache (30 min TTL)
# Then fetches fresh if stale
```

### In Backtesting

```bash
# Backtest uses historical OHLCV
python main.py --backtest
```

### In Custom Scripts

```python
from core.blackboard import get_blackboard

bb = get_blackboard()

# Get cached price
price = bb.get_cached_market_data('BTCUSD', 'D1', 'price', max_age_minutes=60)

# Get OHLCV
ohlcv = bb.get_cached_market_data('BTCUSD', 'H4', 'ohlcv')

# Or read from file
import json
with open('data/historical/latest.json') as f:
    data = json.load(f)
```

---

## 🔧 Customization

### Add More Symbols

Edit `data/daily_fetch.py`:

```python
self.symbols = [
    'BTCUSD', 'ETHUSD', 'SOLUSD',  # Existing
    'ADAUSD', 'DOGEUSD', 'AVAXUSD',  # Add these
    'LINKUSD', 'MATICUSD', 'DOTUSD'
]
```

### Add New Data Sources

```python
async def _fetch_custom_source(self, symbol):
    # Your custom API logic
    pass
```

### Change Fetch Frequency

Edit crontab entries:
```bash
# Every 2 hours instead of 4
*/2 * * * * cd /path && python data/daily_fetch.py
```

---

## 📈 Example Output

```
============================================================
📊 DAILY DATA FETCH - 2026-06-26 00:05
============================================================

📈 Fetching Fear & Greed Index...
  ✅ Value: 45 (Neutral)

💰 Fetching prices...
  Fetching BTCUSD... ✅ $95,234 (+2.3%)
  Fetching ETHUSD... ✅ $3,512 (+1.8%)
  Fetching SOLUSD... ✅ $198 (-0.5%)

📊 Fetching OHLCV data...
  Fetching BTCUSD OHLCV... ✅ 200 candles (D1), 300 candles (H4)
  Fetching ETHUSD OHLCV... ✅ 200 candles (D1), 300 candles (H4)

💸 Fetching funding rates...
  BTCUSDT: 0.0100%
  ETHUSDT: 0.0050%

✅ Daily data fetch complete!
📁 Saved to: data/historical/daily_data_2026-06-26.json
```

---

## 🫡 Pro Tips

1. **Run on VPS** - Deploy on a VPS for 24/7 reliability
2. **Monitor disk space** - Old data files accumulate (cleanup runs weekly)
3. **Use mock data for dev** - Don't hammer APIs during development
4. **Check logs daily** - `tail -f logs/daily_data.log`
5. **Backup data** - Sync `data/historical/` to cloud storage
6. **Test before going live** - Always test cron jobs manually first

---

## 📞 Support

**Check logs:**
```bash
tail -100 logs/daily_data.log
```

**Test manually:**
```bash
python data/daily_fetch.py --verbose
```

**Verify cron:**
```bash
crontab -l
grep CRON /var/log/syslog | tail -20
```

---

**Automated daily data fetching is NOW READY** 🫡

Just run `python utils/cron_scheduler.py` and install the crontab!
