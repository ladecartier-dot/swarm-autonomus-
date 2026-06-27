"""
PostgreSQL Database Schema for Swarm Trader
Stores: OHLCV, Futures, Macro, On-Chain, Sentiment, News, Cycle Labels
"""

SCHEMA = """
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================
-- OHLCV DATA (All Timeframes)
-- ============================================
CREATE TABLE IF NOT EXISTS ohlcv (
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
    vwap NUMERIC(20, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timeframe, timestamp)
);

-- Indexes for OHLCV
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf_ts ON ohlcv(symbol, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_tf_ts ON ohlcv(timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol ON ohlcv(symbol);

-- Hypertable for time-series optimization (TimescaleDB)
SELECT create_hypertable('ohlcv', 'timestamp', if_not_exists => TRUE);

-- ============================================
-- FUTURES METRICS
-- ============================================
CREATE TABLE IF NOT EXISTS futures_metrics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    funding_rate NUMERIC(20, 10),
    predicted_funding NUMERIC(20, 10),
    open_interest NUMERIC(30, 8),
    oi_change_24h NUMERIC(10, 4),
    liquidation_long NUMERIC(30, 8),
    liquidation_short NUMERIC(30, 8),
    liquidation_total NUMERIC(30, 8),
    taker_buy_volume NUMERIC(30, 8),
    taker_sell_volume NUMERIC(30, 8),
    taker_ratio NUMERIC(10, 4),
    long_short_ratio NUMERIC(10, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_futures_symbol_ts ON futures_metrics(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_futures_funding ON futures_metrics(symbol, funding_rate);

SELECT create_hypertable('futures_metrics', 'timestamp', if_not_exists => TRUE);

-- ============================================
-- MACRO INDICATORS
-- ============================================
CREATE TABLE IF NOT EXISTS macro_indicators (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50) NOT NULL,
    country VARCHAR(3) DEFAULT 'US',
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC(30, 8),
    previous NUMERIC(30, 8),
    forecast NUMERIC(30, 8),
    actual NUMERIC(30, 8),
    surprise NUMERIC(10, 4),
    impact VARCHAR(10), -- Low, Medium, High
    unit VARCHAR(20),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(indicator, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_macro_indicator_ts ON macro_indicators(indicator, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_macro_impact ON macro_indicators(impact, timestamp DESC);

-- Key indicators to track:
-- DXY, CPI, PPI, Fed Funds Rate, 10Y Yield, 2Y Yield, Yield Curve (10Y-2Y)
-- M2 Money Supply, Fed Balance Sheet, Unemployment, NFP, VIX, Gold, S&P500, Nasdaq

-- ============================================
-- ON-CHAIN METRICS
-- ============================================
CREATE TABLE IF NOT EXISTS onchain_metrics (
    id SERIAL PRIMARY KEY,
    metric VARCHAR(50) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC(30, 8),
    value_usd NUMERIC(30, 2),
    change_24h NUMERIC(10, 4),
    change_7d NUMERIC(10, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(metric, asset, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_onchain_asset_ts ON onchain_metrics(asset, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_onchain_metric ON onchain_metrics(metric, asset, timestamp DESC);

-- Key metrics:
-- Exchange Inflow/Outflow, Exchange Balance
-- SOPR (Spent Output Profit Ratio)
-- MVRV (Market Value to Realized Value)
-- NUPL (Net Unrealized Profit/Loss)
-- Whale Wallet Count (>1k BTC)
-- Miner Reserve, Hash Rate, Difficulty
-- Active Addresses, Transaction Count, Transaction Volume
-- Fear & Greed Index

-- ============================================
-- CYCLE LABELS (Manual + AI Generated)
-- ============================================
CREATE TABLE IF NOT EXISTS cycle_labels (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(20) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    phase VARCHAR(20) NOT NULL,
    sub_phase VARCHAR(20),
    confidence NUMERIC(3, 2) CHECK (confidence >= 0 AND confidence <= 1),
    methodology VARCHAR(50), -- Manual, Wyckoff, SMC, AI
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cycle_asset ON cycle_labels(asset, start_date);
CREATE INDEX IF NOT EXISTS idx_cycle_phase ON cycle_labels(phase);

-- Standard phases:
-- Bear, Accumulation, Bull, Distribution
-- Sub-phases: PS, SC, AR, ST, SOS, LPS, MU, UPN, LPSY, UT, UTAD, PHD

-- ============================================
-- SENTIMENT DATA
-- ============================================
CREATE TABLE IF NOT EXISTS sentiment_data (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- Twitter, Reddit, Telegram, etc.
    asset VARCHAR(20),
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC(5, 4), -- -1 to 1
    sentiment_label VARCHAR(10), -- Very Negative, Negative, Neutral, Positive, Very Positive
    volume INTEGER, -- Number of mentions
    volume_change_24h NUMERIC(10, 4),
    top_keywords TEXT[],
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sentiment_source_ts ON sentiment_data(source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_asset ON sentiment_data(asset, timestamp DESC);

SELECT create_hypertable('sentiment_data', 'timestamp', if_not_exists => TRUE);

-- ============================================
-- NEWS HEADLINES
-- ============================================
CREATE TABLE IF NOT EXISTS news_headlines (
    id SERIAL PRIMARY KEY,
    headline TEXT NOT NULL,
    summary TEXT,
    source VARCHAR(100),
    author VARCHAR(100),
    url TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC(5, 4),
    sentiment_label VARCHAR(10),
    impact_score NUMERIC(5, 4), -- 0-5 scale
    assets TEXT[], -- Array of affected assets
    category VARCHAR(50), -- Regulation, Adoption, Technology, Security, Market
    tags TEXT[],
    full_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_ts ON news_headlines(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_news_assets ON news_headlines USING GIN(assets);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_headlines(category);
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_headlines(sentiment_label);

-- Full-text search
CREATE INDEX IF NOT EXISTS idx_news_headline_fts ON news_headlines USING GIN(to_tsvector('english', headline));

-- ============================================
-- PATTERN LIBRARY (Detected SMC/ICT Patterns)
-- ============================================
CREATE TABLE IF NOT EXISTS smc_patterns (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(100),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    price_start NUMERIC(20, 8),
    price_end NUMERIC(20, 8),
    price_high NUMERIC(20, 8),
    price_low NUMERIC(20, 8),
    confidence NUMERIC(3, 2),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_smc_symbol_tf ON smc_patterns(symbol, timeframe, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_smc_type ON smc_patterns(pattern_type);

-- Pattern types:
-- BOS (Break of Structure), CHoCH (Change of Character)
-- Order Block (Bullish/Bearish), Fair Value Gap
-- Liquidity Sweep, Equal Highs/Lows
-- Premium/Discount Zones, Imbalance
-- Wyckoff PS/SC/AR/ST/SOS/LPS/UT/UTAD

-- ============================================
-- SIMILARITY SEARCH RESULTS (Pre-computed)
-- ============================================
CREATE TABLE IF NOT EXISTS similarity_matches (
    id SERIAL PRIMARY KEY,
    query_timestamp TIMESTAMPTZ NOT NULL,
    query_conditions JSONB,
    match_timestamp TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20),
    similarity_score NUMERIC(5, 4), -- 0-1
    days_after_30 NUMERIC(10, 4), -- Return after 30 days
    days_after_60 NUMERIC(10, 4),
    days_after_90 NUMERIC(10, 4),
    outcome VARCHAR(20), -- Bullish, Bearish, Neutral
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_similarity_score ON similarity_matches(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_similarity_symbol ON similarity_matches(symbol);

-- ============================================
-- AGGREGATION VIEWS
-- ============================================

-- Daily OHLCV aggregation
CREATE OR REPLACE VIEW ohlcv_daily AS
SELECT 
    symbol,
    DATE(timestamp) as date,
    FIRST(open, timestamp) as open,
    MAX(high) as high,
    MIN(low) as low,
    LAST(close, timestamp) as close,
    SUM(volume) as volume,
    AVG(vwap) as vwap
FROM ohlcv
WHERE timeframe = '1m'
GROUP BY symbol, DATE(timestamp);

-- Weekly OHLCV aggregation
CREATE OR REPLACE VIEW ohlcv_weekly AS
SELECT 
    symbol,
    DATE_TRUNC('week', timestamp) as week,
    FIRST(open, timestamp) as open,
    MAX(high) as high,
    MIN(low) as low,
    LAST(close, timestamp) as close,
    SUM(volume) as volume
FROM ohlcv
WHERE timeframe = '1m'
GROUP BY symbol, DATE_TRUNC('week', timestamp);

-- Monthly futures stats
CREATE OR REPLACE VIEW futures_monthly AS
SELECT 
    symbol,
    DATE_TRUNC('month', timestamp) as month,
    AVG(funding_rate) as avg_funding,
    AVG(open_interest) as avg_oi,
    SUM(liquidation_total) as total_liquidations,
    AVG(long_short_ratio) as avg_ls_ratio
FROM futures_metrics
GROUP BY symbol, DATE_TRUNC('month', timestamp);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Get OHLCV for a symbol/timeframe in date range
CREATE OR REPLACE FUNCTION get_ohlcv_range(
    p_symbol VARCHAR,
    p_timeframe VARCHAR,
    p_start TIMESTAMPTZ,
    p_end TIMESTAMPTZ
)
RETURNS TABLE(
    timestamp TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT o.timestamp, o.open, o.high, o.low, o.close, o.volume
    FROM ohlcv o
    WHERE o.symbol = p_symbol 
      AND o.timeframe = p_timeframe
      AND o.timestamp BETWEEN p_start AND p_end
    ORDER BY o.timestamp;
END;
$$ LANGUAGE plpgsql;

-- Get latest macro indicators
CREATE OR REPLACE FUNCTION get_latest_macro(p_indicator VARCHAR)
RETURNS TABLE(
    timestamp TIMESTAMPTZ,
    value NUMERIC,
    previous NUMERIC,
    surprise NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT m.timestamp, m.value, m.previous, m.surprise
    FROM macro_indicators m
    WHERE m.indicator = p_indicator
    ORDER BY m.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Get cycle phase for a date
CREATE OR REPLACE FUNCTION get_cycle_phase(
    p_asset VARCHAR,
    p_date TIMESTAMPTZ
)
RETURNS TABLE(
    phase VARCHAR,
    sub_phase VARCHAR,
    confidence NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT c.phase, c.sub_phase, c.confidence
    FROM cycle_labels c
    WHERE c.asset = p_asset
      AND c.start_date <= p_date
      AND (c.end_date IS NULL OR c.end_date >= p_date)
    ORDER BY c.confidence DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

"""

print("✅ PostgreSQL schema generated!")
print(f"Schema size: {len(SCHEMA)} characters")
print("\nTables included:")
tables = [
    "ohlcv", "futures_metrics", "macro_indicators", "onchain_metrics",
    "cycle_labels", "sentiment_data", "news_headlines", "smc_patterns",
    "similarity_matches"
]
for t in tables:
    print(f"  - {t}")
