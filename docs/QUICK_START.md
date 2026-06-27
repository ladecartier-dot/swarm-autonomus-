# 🏗️ Swarm Trader - Enterprise Data Infrastructure

## 🎯 Overview

Complete institutional-grade data pipeline untuk AI-powered trading swarm. Mengumpulkan **8 data types** dari **2010-2026** dengan multi-timeframe resolution.

### **8 Data Types:**

1. **OHLCV** - Candlestick data (1m to 1M) dari 2010
2. **Orderbook History** - Bid/ask, spread, imbalance, depth
3. **Futures Data** - Funding rate, OI, liquidation, taker volume
4. **On-Chain Metrics** - Exchange flows, SOPR, MVRV, whale wallets
5. **Macro Indicators** - CPI, FOMC, DXY, yields, VIX
6. **Sentiment** - Twitter, Reddit, Fear & Greed
7. **News** - Headlines dengan impact scoring
8. **Cycle Labels** - Wyckoff phases, bull/bear markets

---

## 📁 Project Structure

```
swarm-trader/
├── data/
│   ├── collectors/              # Data collection scripts
│   │   ├── ohlcv_collector.py   ✅ COMPLETE
│   │   ├── futures_collector.py
│   │   ├── onchain_collector.py
│   │   ├── macro_collector.py
│   │   ├── sentiment_collector.py
│   │   ├── news_collector.py
│   │   ├── orderbook_collector.py
│   │   ├── cycle_labeler.py
│   │   └── master_collector.py  ✅ COMPLETE
│   │
│   ├── storage/
│   │   ├── postgres/
│   │   │   └── schema.sql       ✅ COMPLETE
│   │   ├── clickhouse/
│   │   ├── parquet/
│   │   └── vector/
│   │
│   ├── processing/
│   │   ├── cleaning.py
│   │   ├── indicators.py
│   │   ├── smc_detection.py
│   │   └── pattern_extraction.py
│   │
│   └── historical/              # Raw downloaded data
│       ├── ohlcv/
│       ├── futures/
│       ├── onchain/
│       └── ...
│
├── ai/
│   ├── models/
│   │   ├── pattern_matcher.py
│   │   └── similarity_search.py
│   └── embeddings/
│
└── docs/
    ├── DATA_INFRASTRUCTURE.md   ✅ COMPLETE
    └── QUICK_START.md           ✅ THIS FILE
```

---

## 🚀 Quick Start

### **Step 1: Install Dependencies**

```bash
cd /mnt/data/hermes/workspace/swarm-trader

# Install Python packages
pip install asyncpg aiohttp pandas numpy polars ccxt

# Install database drivers
pip install psycopg2-binary clickhouse-driver

# Install ML libraries (for later)
pip install torch scikit-learn sentence-transformers
```

### **Step 2: Setup Databases**

#### **PostgreSQL (Required)**

```bash
# Install PostgreSQL 15 + TimescaleDB
sudo apt install postgresql-15 postgresql-15-timescaledb

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE swarm_trader;
CREATE USER swarm_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE swarm_trader TO swarm_user;
EOF

# Run schema
psql -U swarm_user -d swarm_trader -f data/storage/postgres/schema.sql
```

#### **ClickHouse (Optional - For High-Frequency Data)**

```bash
# Install ClickHouse
curl https://clickhouse.com/ | sh

# Start server
sudo clickhouse-server --daemon

# Run schema
clickhouse-client < data/storage/clickhouse/schema.sql
```

### **Step 3: Configure Environment**

Create `.env` file:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=swarm_user
DB_PASSWORD=your_password
DB_NAME=swarm_trader

# ClickHouse (optional)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# API Keys
BINANCE_API_KEY=
BINANCE_SECRET_KEY=
GLASSNODE_API_KEY=
COINGLASS_API_KEY=
FRED_API_KEY=8101e05db182ccd505bc50920a8f097c
ALPHA_VANTAGE_KEY=CS37J2Y39A7P4BHS
TWITTER_API_KEY=
REDDIT_CLIENT_ID=
CRYPTOPANIC_API_KEY=
```

### **Step 4: Run Historical Backfill**

#### **Option A: Collect OHLCV Only (Fastest)**

```bash
# BTC from 2010 (all timeframes)
python data/collectors/ohlcv_collector.py \
  --symbol BTC \
  --start 2010-01-01 \
  --timeframes 1m,5m,15m,1H,4H,1D,1W

# ETH from 2015
python data/collectors/ohlcv_collector.py \
  --symbol ETH \
  --start 2015-08-07 \
  --timeframes 1H,4H,1D,1W

# SOL from 2020
python data/collectors/ohlcv_collector.py \
  --symbol SOL \
  --start 2020-04-10 \
  --timeframes 1H,4H,1D
```

#### **Option B: Collect All Data Types (Full Backfill)**

```bash
# Backfill everything for BTC, ETH, SOL
python data/collectors/master_collector.py \
  --backfill \
  --symbols BTC,ETH,SOL \
  --start 2010-01-01 \
  --types ohlcv,futures,onchain,macro,sentiment,news
```

**Estimated Time:**
- OHLCV only: ~2-4 hours per symbol
- Full backfill: ~1-2 days per symbol

### **Step 5: Run Real-Time Collection**

```bash
# Start real-time collectors
python data/collectors/master_collector.py \
  --realtime \
  --symbols BTC,ETH,SOL \
  --types ohlcv,futures
```

**This runs continuously**, collecting new data every minute.

---

## 📊 Data Collection Status

| Collector | Status | File | Progress |
|-----------|--------|------|----------|
| OHLCV | ✅ COMPLETE | `ohlcv_collector.py` | Ready to run |
| Futures | ⏳ TODO | `futures_collector.py` | - |
| On-Chain | ⏳ TODO | `onchain_collector.py` | - |
| Macro | ⏳ TODO | `macro_collector.py` | - |
| Sentiment | ⏳ TODO | `sentiment_collector.py` | - |
| News | ⏳ TODO | `news_collector.py` | - |
| Orderbook | ⏳ TODO | `orderbook_collector.py` | - |
| Cycle Labels | ⏳ TODO | `cycle_labeler.py` | - |

**Next Priority:** Build remaining 7 collectors

---

## 🗄️ Database Schema

### **Tables Created:**

```sql
-- 9 main tables
ohlcv              -- Candlestick data (all timeframes)
futures_metrics    -- Funding, OI, liquidation
macro_indicators   -- CPI, FOMC, DXY, yields
onchain_metrics    -- Exchange flows, SOPR, MVRV
cycle_labels       -- Bull/Bear/Accumulation phases
sentiment_data     -- Social media sentiment
news_headlines     -- News with impact scoring
smc_patterns       -- Detected SMC/ICT patterns
similarity_matches -- Pre-computed similarity search
```

**Total Storage Estimate:**
- Raw data: ~6 TB (2010-2026)
- Processed: ~800 GB
- Compressed Parquet: ~400 GB

---

## 🔧 Collectors Detail

### **1. OHLCV Collector** ✅

**File:** `data/collectors/ohlcv_collector.py`

**Features:**
- Historical data from 2010 (BTC), 2015 (ETH), 2020 (SOL)
- All timeframes: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D, 1W, 1M
- Dual storage: PostgreSQL + Parquet
- Gap detection & backfill
- Real-time mode (updates every minute)

**Usage:**
```bash
python data/collectors/ohlcv_collector.py \
  --symbol BTC \
  --start 2010-01-01 \
  --timeframes 1m,5m,15m,1H,4H,1D,1W \
  --backfill
```

---

### **2. Futures Collector** ⏳

**Planned Features:**
- Funding rate history (Binance, Bybit, OKX)
- Open Interest with 24h change
- Liquidation data (long/short)
- Taker buy/sell volume
- Long/short ratio

**Usage (when complete):**
```bash
python data/collectors/futures_collector.py \
  --symbol BTC \
  --start 2018-01-01 \
  --metrics funding,oi,liquidation
```

---

### **3. On-Chain Collector** ⏳

**Planned Metrics:**
- Exchange Inflow/Outflow
- Exchange Balance
- SOPR (Spent Output Profit Ratio)
- MVRV (Market Value to Realized Value)
- NUPL (Net Unrealized Profit/Loss)
- Whale Wallet Count (>1k BTC)
- Miner Reserve
- Hash Rate, Difficulty
- Active Addresses
- Transaction Volume

**APIs:** Glassnode, Dune Analytics, Etherscan

---

### **4. Macro Collector** ⏳

**Planned Indicators:**
- **US Economic:** CPI, PPI, NFP, Unemployment
- **Fed Policy:** Fed Funds Rate, Balance Sheet
- **Yields:** 10Y, 2Y, Yield Curve (10Y-2Y)
- **Currency:** DXY (Dollar Index)
- **Risk:** VIX, Gold
- **Equities:** S&P 500, Nasdaq

**APIs:** FRED (120k calls/day free), Alpha Vantage

---

### **5. Sentiment Collector** ⏳

**Planned Sources:**
- Twitter/X (mentions, sentiment)
- Reddit (r/CryptoCurrency, r/Bitcoin)
- Telegram channels
- Fear & Greed Index
- Google Trends

**Output:** Sentiment score (-1 to 1), volume, keywords

---

### **6. News Collector** ⏳

**Planned Sources:**
- CryptoPanic (aggregator)
- CoinDesk, Cointelegraph
- The Block, Decrypt
- Twitter official accounts

**Features:**
- Headline + full text
- Sentiment analysis
- Impact scoring (0-5)
- Asset tagging
- Category classification

---

### **7. Orderbook Collector** ⏳

**Planned Features:**
- Real-time bid/ask snapshots (100ms)
- Spread calculation
- Orderbook imbalance
- Depth at 5/10/20 levels
- Stored in ClickHouse for speed

**Storage:** ClickHouse (billions of rows)

---

### **8. Cycle Labeler** ⏳

**Planned Methodology:**
- **Manual:** Expert labeling based on Wyckoff theory
- **AI:** Pattern recognition for phase detection
- **Hybrid:** AI suggests, human confirms

**Phases:**
- Bear Market
- Accumulation (PS, SC, AR, ST, SOS, LPS)
- Bull Market (MU, UPN, LPSY)
- Distribution (UT, UTAD, PHD)

---

## 🤖 AI/ML Pipeline

### **After Data Collection:**

1. **Pattern Detection**
   - SMC patterns (BOS, CHoCH, Order Blocks, FVG)
   - Wyckoff phases
   - Elliott Wave counts
   - Volume Profile analysis

2. **Feature Engineering**
   - Technical indicators (RSI, MACD, Bollinger)
   - Market structure features
   - Liquidity metrics
   - Sentiment aggregates

3. **Embedding Generation**
   - Convert patterns to vectors
   - Store in Vector DB (Qdrant/Pinecone)
   - Enable similarity search

4. **Similarity Search**
   ```
   Query: "Current market conditions"
   
   Results:
   - Nov 2018: 92% similar → +45% in 90 days
   - Mar 2020: 89% similar → +120% in 90 days
   - Jun 2022: 95% similar → +67% in 90 days
   
   Average outcome: +76% (90 days)
   Confidence: High
   ```

---

## 📈 Expected Dataset Size

| Data Type | Time Range | Raw Size | Processed |
|-----------|------------|----------|-----------|
| OHLCV (all TF) | 2010-2026 | 50 GB | 20 GB |
| Orderbook (1m) | 2018-2026 | 5 TB | 500 GB |
| Futures | 2018-2026 | 100 GB | 50 GB |
| On-Chain | 2010-2026 | 200 GB | 100 GB |
| Macro | 1980-2026 | 10 GB | 5 GB |
| Sentiment | 2015-2026 | 500 GB | 100 GB |
| News | 2010-2026 | 50 GB | 20 GB |
| **Total** | | **~6 TB** | **~800 GB** |

---

## 💰 Cost Estimate

| Service | Tier | Monthly | Annual |
|---------|------|---------|--------|
| **Glassnode** | Advanced | $299 | $3,588 |
| **Coinglass** | Pro | $50 | $600 |
| **LunarCrush** | Silver | $99 | $1,188 |
| **CryptoPanic** | Pro | Free | $0 |
| **FRED** | Free | $0 | $0 |
| **Alpha Vantage** | Free | $0 | $0 |
| **VPS (2TB SSD)** | - | $40 | $480 |
| **Total** | | **~$500/mo** | **~$6,000/yr** |

**One-time setup:** ~$1,000 (hardware, initial data purchases)

---

## ✅ Next Steps

### **Phase 1 (Week 1-2): OHLCV Backfill**
- [x] OHLCV collector complete
- [ ] Run BTC backfill (2010-2026, all TFs)
- [ ] Run ETH backfill (2015-2026)
- [ ] Run SOL backfill (2020-2026)
- [ ] Verify data quality

### **Phase 2 (Week 3-4): Build Remaining Collectors**
- [ ] Futures collector
- [ ] On-chain collector
- [ ] Macro collector
- [ ] Sentiment collector
- [ ] News collector
- [ ] Orderbook collector
- [ ] Cycle labeler

### **Phase 3 (Week 5-6): Processing Pipeline**
- [ ] Data cleaning scripts
- [ ] Indicator calculation
- [ ] SMC pattern detection
- [ ] Pattern extraction
- [ ] Embedding generation

### **Phase 4 (Week 7-8): AI/ML Models**
- [ ] Pattern matcher
- [ ] Similarity search
- [ ] Regime detector
- [ ] Backtesting framework

---

## 🎯 Ultimate Goal

Build AI yang bisa jawab:

> "Di seluruh sejarah BTC dari 2011 sampai 2026, tunjukkan semua kejadian yang mirip kondisi market hari ini dengan similarity >95%, lengkap dengan apa yang terjadi 30, 60, dan 90 hari setelahnya."

**Ini bukan lagi trading. Ini adalah oracle.** 🔮

---

## 📞 Support

**Documentation:**
- `DATA_INFRASTRUCTURE.md` - Full architecture
- `QUICK_START.md` - This file
- `API_REFERENCE.md` - API docs (coming soon)

**Issues & Questions:**
- Check existing collectors in `data/collectors/`
- Review schema in `data/storage/postgres/schema.sql`
- See example usage in each collector

---

**Let's build the most advanced crypto data infrastructure ever created!** 🚀💪

*Generated by Swarm Trader AI - Jun 26, 2026*
