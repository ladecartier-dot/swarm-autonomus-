# 🏗️ Swarm Trader - Enterprise Data Infrastructure

## 📊 Complete Data Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA COLLECTION LAYER                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ OHLCV    │  │ Order    │  │ Futures  │  │ On-Chain │  │ Macro    │  │
│  │ Data     │  │ Book     │  │ Data     │  │ Data     │  │ Data     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │             │         │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐  │
│  │ Binance  │  │ Binance  │  │ Binance  │  │ Glassnode│  │ FRED     │  │
│  │ Coinbase │  │ FTX Arch │  │ Coinglass│  │ Dune     │  │ Alpha V  │  │
│  │ Kraken   │  │ CCXT     │  │ Laevitas │  │ Etherscan│  │ TradingE │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                               │
│  │ Sentiment│  │ News     │  │ Cycle    │                               │
│  │ Data     │  │ Data     │  │ Labels   │                               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                               │
│       │             │             │                                     │
│  ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐                              │
│  │ Twitter  │  │ CryptoPanic│ │ Manual   │                              │
│  │ Reddit   │  │ NewsAPI  │  │ Wyckoff  │                              │
│  │ LunarCrush│ │ CoinDesk │  │ Cycle    │                              │
│  └──────────┘  └──────────┘  └──────────┘                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROCESSING LAYER                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Raw Data → Cleaning → Validation → Normalization → Enrichment          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    INDICATOR ENGINE                               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │
│  │  │ Wyckoff     │ │ SMC/ICT     │ │ Volume      │ │ Elliott     │ │   │
│  │  │ Phases      │ │ Patterns    │ │ Profile     │ │ Wave        │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │
│  │  │ Market      │ │ Auction     │ │ Fractal     │ │ Liquidity   │ │   │
│  │  │ Structure   │ │ Theory      │ │ Theory      │ │ Theory      │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ PostgreSQL   │  │ ClickHouse   │  │ Parquet      │  │ Vector DB   │ │
│  │ (Numerical)  │  │ (Tick Data)  │  │ (Training)   │  │ (AI Memory) │ │
│  │              │  │              │  │              │  │             │ │
│  │ - OHLCV      │  │ - Orderbook  │  │ - Datasets   │  │ - Patterns  │ │
│  │ - Futures    │  │ - Trades     │  │ - Features   │  │ - Embeddings│ │
│  │ - Macro      │  │ - 1m bars    │  │ - Labels     │  │ - Similarity│ │
│  │ - On-Chain   │  │              │  │              │  │             │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         AI/ML LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PATTERN RECOGNITION                            │   │
│  │  "Show all historical periods with >95% similarity to current"   │   │
│  │  "What happened 30/60/90 days after similar setups?"             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    PREDICTION ENGINE                              │   │
│  │  - Multi-timeframe confluence scoring                            │   │
│  │  - Regime detection (Bear/Accumulation/Bull/Distribution)        │   │
│  │  - Scenario generation with probabilities                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
/mnt/data/hermes/workspace/swarm-trader/
├── data/
│   ├── collectors/           # Data collection scripts
│   │   ├── ohlcv_collector.py
│   │   ├── orderbook_collector.py
│   │   ├── futures_collector.py
│   │   ├── onchain_collector.py
│   │   ├── macro_collector.py
│   │   ├── sentiment_collector.py
│   │   ├── news_collector.py
│   │   └── cycle_labeler.py
│   │
│   ├── storage/
│   │   ├── postgres/         # PostgreSQL schemas
│   │   │   ├── schema.sql
│   │   │   └── queries.sql
│   │   ├── clickhouse/       # ClickHouse schemas
│   │   │   ├── schema.sql
│   │   │   └── queries.sql
│   │   ├── parquet/          # Training datasets
│   │   │   ├── ohlcv/
│   │   │   ├── futures/
│   │   │   └── onchain/
│   │   └── vector/           # Vector embeddings
│   │       ├── patterns/
│   │       └── memory/
│   │
│   ├── processing/
│   │   ├── cleaning.py
│   │   ├── indicators.py
│   │   ├── smc_detection.py
│   │   ├── pattern_extraction.py
│   │   └── labeling.py
│   │
│   └── historical/           # Raw downloaded data
│       ├── ohlcv/
│       ├── orderbook/
│       ├── futures/
│       ├── onchain/
│       ├── macro/
│       ├── sentiment/
│       ├── news/
│       └── labels/
│
├── ai/
│   ├── models/
│   │   ├── pattern_matcher.py
│   │   ├── regime_detector.py
│   │   └── similarity_search.py
│   ├── embeddings/
│   └── training/
│
└── docs/
    ├── DATA_ARCHITECTURE.md
    ├── COLLECTOR_GUIDE.md
    └── API_REFERENCE.md
```

---

## 🗄️ Database Schemas

### **PostgreSQL (Numerical Data)**

```sql
-- OHLCV Data
CREATE TABLE ohlcv (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(30, 8) NOT NULL,
    trades_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, timestamp)
);

-- Futures Data
CREATE TABLE futures_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    funding_rate NUMERIC(20, 10),
    open_interest NUMERIC(30, 8),
    liquidation_long NUMERIC(30, 8),
    liquidation_short NUMERIC(30, 8),
    taker_buy_volume NUMERIC(30, 8),
    taker_sell_volume NUMERIC(30, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);

-- Macro Data
CREATE TABLE macro_indicators (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,
    country VARCHAR(3) DEFAULT 'US',
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC(30, 8),
    previous NUMERIC(30, 8),
    forecast NUMERIC(30, 8),
    actual NUMERIC(30, 8),
    impact VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(indicator, timestamp)
);

-- On-Chain Metrics
CREATE TABLE onchain_metrics (
    id SERIAL PRIMARY KEY,
    metric VARCHAR(50) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC(30, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(metric, asset, timestamp)
);

-- Cycle Labels
CREATE TABLE cycle_labels (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(20) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    phase VARCHAR(20) NOT NULL, -- Bear, Accumulation, Bull, Distribution
    confidence NUMERIC(3, 2),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- News & Sentiment
CREATE TABLE news_headlines (
    id SERIAL PRIMARY KEY,
    headline TEXT NOT NULL,
    source VARCHAR(100),
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC(5, 4),
    impact_score NUMERIC(5, 4),
    assets TEXT[], -- Array of affected assets
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_ohlcv_symbol_tf ON ohlcv(symbol, timeframe, timestamp DESC);
CREATE INDEX idx_futures_symbol ON futures_metrics(symbol, timestamp DESC);
CREATE INDEX idx_macro_indicator ON macro_indicators(indicator, timestamp DESC);
CREATE INDEX idx_onchain_asset ON onchain_metrics(asset, timestamp DESC);
CREATE INDEX idx_cycle_asset ON cycle_labels(asset, start_date);
```

### **ClickHouse (High-Frequency Data)**

```sql
-- Orderbook Snapshots (Tick-level)
CREATE TABLE orderbook_ticks (
    timestamp DateTime64(3) NOT NULL,
    symbol String NOT NULL,
    bid_price Float64 NOT NULL,
    ask_price Float64 NOT NULL,
    bid_size Float64 NOT NULL,
    ask_size Float64 NOT NULL,
    spread Float64 NOT NULL,
    imbalance Float64 NOT NULL,
    depth_5bid Float64,
    depth_5ask Float64,
    depth_10bid Float64,
    depth_10ask Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

-- 1-minute OHLCV (Massive scale)
CREATE TABLE ohlcv_1m (
    timestamp DateTime64(3) NOT NULL,
    symbol String NOT NULL,
    open Float64 NOT NULL,
    high Float64 NOT NULL,
    low Float64 NOT NULL,
    close Float64 NOT NULL,
    volume Float64 NOT NULL,
    trades UInt32,
    vwap Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

-- Trades (Tick-level)
CREATE TABLE trades (
    timestamp DateTime64(3) NOT NULL,
    symbol String NOT NULL,
    trade_id String NOT NULL,
    price Float64 NOT NULL,
    amount Float64 NOT NULL,
    side String NOT NULL, -- buy or sell
    is_liquidation Boolean DEFAULT false
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);
```

---

## 🚀 Data Collection Workflow

### **Phase 1: Historical Backfill** (Week 1-2)
```bash
# BTC OHLCV (2010-2026)
python data/collectors/ohlcv_collector.py --symbol BTC --start 2010-01-01

# ETH OHLCV (2015-2026)
python data/collectors/ohlcv_collector.py --symbol ETH --start 2015-08-07

# SOL OHLCV (2020-2026)
python data/collectors/ohlcv_collector.py --symbol SOL --start 2020-04-10

# All timeframes
python data/collectors/ohllv_collector.py --symbol BTC --timeframes 1m,5m,15m,1H,4H,1D,1W
```

### **Phase 2: Real-Time Streaming** (Week 3)
```bash
# Start orderbook collector
python data/collectors/orderbook_collector.py --symbol BTC --realtime

# Start futures collector
python data/collectors/futures_collector.py --symbol BTC --metrics funding,oi,liquidation

# Start on-chain collector
python data/collectors/onchain_collector.py --asset BTC --metrics all
```

### **Phase 3: Processing & Labeling** (Week 4)
```bash
# Clean and validate
python data/processing/cleaning.py --all

# Calculate indicators
python data/processing/indicators.py --all

# Detect SMC patterns
python data/processing/smc_detection.py --all

# Extract patterns
python data/processing/pattern_extraction.py --all

# Label cycles
python data/collectors/cycle_labeler.py --asset BTC
```

### **Phase 4: Vector Embeddings** (Week 5)
```bash
# Generate embeddings for all patterns
python ai/embeddings/generate.py --patterns all

# Build similarity index
python ai/models/similarity_search.py --build
```

---

## 📊 APIs & Data Sources

| Data Type | Primary API | Backup API | Cost |
|-----------|-------------|------------|------|
| **OHLCV** | Binance API | CCXT (Kraken, Coinbase) | Free |
| **Orderbook** | Binance WebSocket | FTX Archive (historical) | Free |
| **Futures** | Binance Futures | Coinglass API | Free/$50mo |
| **On-Chain** | Glassnode API | Dune Analytics, Etherscan | $299mo |
| **Macro** | FRED API | Alpha Vantage, TradingEconomics | Free |
| **Sentiment** | LunarCrush API | Twitter API, Reddit API | $99mo |
| **News** | CryptoPanic API | NewsAPI, CoinDesk | Free/$30mo |
| **Cycle Labels** | Manual + AI | TradingView, Glassnode | Free |

---

## 💰 Estimated Costs

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| **Glassnode** | Advanced | $299 |
| **Coinglass** | Pro | $50 |
| **LunarCrush** | Silver | $99 |
| **CryptoPanic** | Pro | Free |
| **FRED** | Free | $0 |
| **Alpha Vantage** | Free | $0 |
| **VPS (Storage)** | 2TB SSD | $40 |
| **Total** | | **~$500/mo** |

**One-time setup:** ~$1000 (hardware, initial data purchases)

---

## 🎯 Expected Dataset Size

| Data Type | Time Range | Size (Raw) | Size (Processed) |
|-----------|------------|------------|------------------|
| **OHLCV (all TF)** | 2010-2026 | 50 GB | 20 GB |
| **Orderbook (1m)** | 2018-2026 | 5 TB | 500 GB |
| **Futures** | 2018-2026 | 100 GB | 50 GB |
| **On-Chain** | 2010-2026 | 200 GB | 100 GB |
| **Macro** | 1980-2026 | 10 GB | 5 GB |
| **Sentiment** | 2015-2026 | 500 GB | 100 GB |
| **News** | 2010-2026 | 50 GB | 20 GB |
| **Total** | | **~6 TB** | **~800 GB** |

---

## 🔧 Tech Stack

| Component | Technology | Why |
|-----------|------------|-----|
| **Database (SQL)** | PostgreSQL 15 | ACID, complex queries |
| **Database (TS)** | ClickHouse | Time-series, billions of rows |
| **File Storage** | Parquet + S3 | Efficient, columnar |
| **Vector DB** | Qdrant / Pinecone | Similarity search |
| **Processing** | Python + Polars | Fast data manipulation |
| **Streaming** | Apache Kafka | Real-time data pipeline |
| **Orchestration** | Apache Airflow | Scheduled jobs |
| **ML Framework** | PyTorch + LangChain | Pattern matching, LLM |

---

## 📈 AI Capabilities (After Training)

### **Similarity Search:**
```
Query: "Show all periods with >95% similarity to current market"

Results:
1. Nov 2018 - 87% similar → +45% in 90 days
2. Mar 2020 - 92% similar → +120% in 90 days
3. Jun 2022 - 95% similar → +65% in 90 days

Average outcome: +76% in 90 days
Confidence: High (3 strong historical matches)
```

### **Pattern Recognition:**
```
Current Setup:
- Liquidity sweep at $58,441 ✅
- CHoCH on 4H ✅
- Funding negative ✅
- Whale accumulation ✅

Historical matches: 12 instances
Average 30-day return: +23%
Average 90-day return: +67%
Win rate: 83% (10/12)
```

### **Regime Detection:**
```
Current Regime: EARLY ACCUMULATION
Confidence: 78%

Characteristics:
- Price down 55% from ATH
- MVRV < 1.5
- Negative funding
- Low volatility
- Whale accumulation

Historical duration: 4-8 months
Typical next phase: Markup (Bull)
Probability: 72%
```

---

## ✅ Next Steps

Gua udah siapin architecture lengkap! Sekarang tinggal:

1. **Setup databases** (PostgreSQL + ClickHouse + Vector DB)
2. **Write collectors** (8 data types)
3. **Backfill historical data** (2010-2026)
4. **Build processing pipeline** (cleaning, indicators, SMC)
5. **Generate embeddings** (pattern vectors)
6. **Train similarity model** (find historical matches)

**Mau gua mulai dari mana bro?**

A) **Database Setup** - Install & configure PostgreSQL + ClickHouse
B) **OHLCV Collector** - Start dengan data paling basic dulu
C) **Full Pipeline** - Build semua collectors sekaligus (aggressive)
D) **Prioritized** - OHLCV + Futures + On-Chain dulu (most important for SMC)

Pilih bro, langsung gua eksekusi! 🚀💪
