# 🏛️ Real-Time Macro Dashboard Widget

## ✅ What's Been Built

A **production-ready institutional macro dashboard** that displays live Federal Reserve Economic Data (FRED) and market sentiment indicators in a beautiful, auto-refreshing web UI.

## 🎯 Features

### Live Data Sources
- **DXY (Dollar Index)** - Alpha Vantage UUP ETF proxy (live daily updates)
- **13 FRED Economic Indicators** - Federal Reserve Economic Data API
- **Auto-refresh** - Updates every 60 seconds
- **Macro Score** - 0-5 scoring system with trading bias (BULLISH/NEUTRAL/BEARISH)

### Dashboard Components

#### 1. Trading Bias Card
- Overall macro score (0-5)
- Trading bias recommendation
- Color-coded status (green/yellow/red)

#### 2. Dollar Index (DXY)
- Live UUP ETF price
- Equivalent DXY index value
- Dollar strength status

#### 3. Yields & Yield Curve
- 10Y Treasury Yield
- 2Y Treasury Yield
- Real Yields (TIPS 10Y)
- Yield Curve Spread (10Y-2Y)

#### 4. Fed & Liquidity
- Fed Funds Rate
- Fed Balance Sheet (WALCL)
- M2 Money Supply
- Reverse Repo (RRP)
- Treasury General Account (TGA)

#### 5. Inflation & Markets
- CPI (Consumer Price Index)
- VIX (Volatility Index)

#### 6. Labor Market
- Non-Farm Payrolls (NFP)
- Unemployment Rate

## 🚀 Access the Dashboard

### Web UI
```
http://localhost:5000/macro
```

### API Endpoint
```
http://localhost:5000/api/macro
```

### Example API Response
```json
{
  "timestamp": "2026-06-26T02:38:20.127376",
  "dxy": {
    "value": 28.48,
    "date": "2026-06-25",
    "index_equiv": 114
  },
  "fred_data": {
    "10Y Treasury Yield": {"value": 4.41, "date": "2026-06-24"},
    "Real Yields (TIPS)": {"value": 2.23, "date": "2026-06-24"},
    "M2 Money Supply": {"value": 23052.3, "date": "2026-05-01"}
  },
  "macro_score": "3/5",
  "trading_bias": "NEUTRAL",
  "bias_color": "yellow",
  "analysis": {
    "dollar_status": "NEUTRAL",
    "real_yields_status": "HIGH",
    "liquidity_status": "SUPPORTIVE",
    "fed_stance": "NEUTRAL"
  }
}
```

## 📊 Macro Scoring System

The dashboard calculates a **0-5 score** based on:

1. **DXY Strength** (+1 if DXY < 110 → weak dollar bullish for crypto)
2. **Real Yields** (+1 if TIPS < 1.5% → low yields favor risk assets)
3. **Yield Curve** (+1 if spread > 0.3% → not inverted, low recession risk)
4. **VIX** (+1 if VIX < 20 → normal volatility, risk-on environment)
5. **M2 Liquidity** (+1 if M2 > $21T → ample liquidity)

### Trading Bias Interpretation

| Score | Bias | Meaning |
|-------|------|---------|
| 4-5/5 | 🟢 BULLISH | Strong macro tailwinds for risk assets |
| 2-3/5 | 🟡 NEUTRAL | Mixed signals, trade technicals (SMC) |
| 0-1/5 | 🔴 BEARISH | Macro headwinds, defensive positioning |

## 🔧 Technical Implementation

### Files Modified/Created
- `web/server.py` - Added `/api/macro` endpoint + `/macro` route
- `web/templates/macro_dashboard.html` - Beautiful responsive UI
- `state/api_keys.env` - FRED + Alpha Vantage API keys

### API Key Requirements
```bash
# Required environment variables
export FRED_API_KEY="your_fred_key_here"
export ALPHA_VANTAGE_KEY="your_av_key_here"
```

### Auto-Refresh
- UI refreshes every **60 seconds** via JavaScript
- No manual refresh needed
- Live indicator pulses in header

## 📈 Current Macro Snapshot (June 26, 2026)

```
🎯 TRADING BIAS: NEUTRAL (3/5)

🇺🇸 DXY: $28.48 (≈114 index) - NEUTRAL
📈 10Y Yield: 4.41% - Elevated
💎 Real Yields: 2.23% - HIGH (bearish for duration)
📊 Yield Curve: +0.31% - Flat, not inverted
💵 M2 Supply: $23.05T - SUPPORTIVE liquidity
🏦 Fed Balance: $6.74T - Stable
😰 VIX: 18.6% - Normal volatility
🏦 Fed Funds: 3.63% - Neutral stance
```

## 🎨 UI Features

- **Dark theme** - Easy on eyes for 24/7 monitoring
- **Responsive design** - Works on desktop, tablet, mobile
- **Color-coded status** - Green/Yellow/Red indicators
- **Hover effects** - Cards lift on hover
- **Gradient backgrounds** - Modern institutional look
- **Live pulse indicator** - Shows data is updating

## 🔗 Integration with Swarm

The macro dashboard integrates with your swarm-trader system:

1. **Macro Agent** uses this data for trading decisions
2. **Consensus scoring** incorporates macro bias
3. **Telegram alerts** can reference macro conditions
4. **Backtesting** can filter by macro regime

## 🚀 Next Steps

### Immediate
- ✅ Dashboard is LIVE at `http://localhost:5000/macro`
- ✅ API endpoint working: `/api/macro`
- ✅ Auto-refresh every 60 seconds

### Optional Enhancements
- Add COMEX Open Interest data (requires alternative source)
- Add COT (Commitment of Traders) positioning
- Add historical charts (Chart.js or Plotly)
- Add macro regime detection (inflationary/deflationary)
- Add correlation matrix with crypto assets
- Add Telegram digest of daily macro changes

## 📝 Usage in Trading

### When Macro is BULLISH (4-5/5)
- ✅ Increase position sizes
- ✅ Favor high-beta alts
- ✅ Use higher leverage (carefully)
- ✅ Trend-following strategies

### When Macro is NEUTRAL (2-3/5)
- ⚠️ Trade technicals (SMC, liquidity)
- ⚠️ Stock-picking over beta
- ⚠️ Reduce position sizes
- ⚠️ Focus on idiosyncratic opportunities

### When Macro is BEARISH (0-1/5)
- ❌ Reduce risk exposure
- ❌ Favor stablecoins/cash
- ❌ Short-biased strategies
- ❌ Capital preservation mode

---

**Dashboard Status:** ✅ LIVE  
**Data Sources:** FRED (120k calls/day) + Alpha Vantage (25 calls/day free)  
**Update Frequency:** Every 60 seconds  
**Access:** http://localhost:5000/macro
