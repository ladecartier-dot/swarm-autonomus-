# 🎯 BTCUSDT QUICK REFERENCE - SMC Trade Setup
**Current Price:** $60,100 | **Date:** Jun 26, 2026 | **Bias:** 🟡 NEUTRAL

---

## 📊 KEY LEVELS (Memorize These!)

```
🔴 RESISTANCE (SSL - Sell Side Liquidity)
├── $64,500 ──── Major SSL (1W) ──── 🎯 TP3
├── $62,800 ──── Medium SSL (4H) ─── 🎯 TP2
└── $61,200 ──── Weak SSL (Near) ─── 🎯 TP1 / Entry Short

🟡 CURRENT: $60,100 (Mid-Range, WAIT)

🟢 SUPPORT (BSL - Buy Side Liquidity)
├── $59,500 ──── Weak BSL (Near) ─── 🎯 Entry Long
├── $58,000 ──── Major BSL (1W) ──── 🎯 TP1 / Entry Long
└── $56,200 ──── Medium BSL ──────── 🎯 TP2
```

---

## 🎯 TWO SCENARIOS (Pick One When Triggered)

### 🟢 LONG SETUP (Bullish)

**Wait For:**
1. ✅ Sweep of $58,000-$59,500 (BSL)
2. ✅ Strong rally (>3%)
3. ✅ Break above $61,200 (CHoCH)
4. ✅ Return to $59,200-$59,600

**Entry:** $59,400 (limit)  
**SL:** $57,500 (-3.2%)  
**TP1:** $61,200 (+3.0%)  
**TP2:** $62,800 (+5.7%)  
**TP3:** $64,500 (+8.6%)  
**R:R:** 1:2.7 ✅

**Position:** 0.105 BTC per $10k account (2% risk)

---

### 🔴 SHORT SETUP (Bearish)

**Wait For:**
1. ✅ Sweep of $61,200-$62,800 (SSL)
2. ✅ Strong drop (>3%)
3. ✅ Break below $58,000 (CHoCH)
4. ✅ Return to $61,800-$62,200

**Entry:** $62,000 (limit)  
**SL:** $64,500 (-4.0%)  
**TP1:** $59,500 (-4.0%)  
**TP2:** $58,000 (-6.4%)  
**TP3:** $56,200 (-9.3%)  
**R:R:** 1:2.3 ✅

**Position:** 0.08 BTC per $10k account (2% risk)

---

## ⚠️ INVALIDATION

**Long Invalid:** Close below $56,200  
**Short Invalid:** Close above $64,500

---

## ✅ PRE-ENTRY CHECKLIST

- [ ] Liquidity sweep confirmed?
- [ ] Displacement candle (>3%)?
- [ ] CHoCH (structure break)?
- [ ] Return to OB/FVG?
- [ ] Entry candle (engulfing/pinbar)?
- [ ] R:R ≥ 1:2?
- [ ] No major news?
- [ ] Macro aligned (check dashboard)?

**ALL must be ✅ before entry!**

---

## 📱 SET ALERTS NOW!

**TradingView Alerts:**
```
🔔 $59,500 - "BSL Sweep Watch"
🔔 $58,000 - "Major Support / Long Entry"
🔔 $61,200 - "SSL Sweep Watch"
🔔 $62,800 - "Major Resistance / Short Entry"
```

**Telegram Alerts:**
```bash
python utils/telegram_alerts.py --symbol BTCUSDT --watch
```

---

## 🔗 SWARM COMMANDS

**Generate Signal:**
```bash
# Long
python signals/generate_signals.py --symbol BTCUSDT --setup SMC_BULLISH --entry 59400 --sl 57500 --tp1 61200 --tp2 62800 --tp3 64500 --confidence 0.75

# Short
python signals/generate_signals.py --symbol BTCUSDT --setup SMC_BEARISH --entry 62000 --sl 64500 --tp1 59500 --tp2 58000 --tp3 56200 --confidence 0.65
```

**Check Dashboard:**
```bash
curl https://YOUR_URL.onrender.com/api/macro
curl https://YOUR_URL.onrender.com/api/signals
```

---

## 💰 POSITION SIZE CALCULATOR

**Formula:**
```
Position = (Account × Risk%) ÷ (Entry - SL)

Example ($10k account, 2% risk):
Long:  ($10,000 × 0.02) ÷ ($59,400 - $57,500) = 0.105 BTC
Short: ($10,000 × 0.02) ÷ ($64,500 - $62,000) = 0.08 BTC
```

**Quick Reference:**
| Account | Risk | Long Size | Short Size |
|---------|------|-----------|------------|
| $5,000  | 2%   | 0.052 BTC | 0.04 BTC   |
| $10,000 | 2%   | 0.105 BTC | 0.08 BTC   |
| $25,000 | 2%   | 0.26 BTC  | 0.20 BTC   |
| $50,000 | 2%   | 0.52 BTC  | 0.40 BTC   |

---

## 📊 EXECUTION FLOW

```
NOW (🟡 WAIT)
  ↓
Liquidity Sweep (BSL or SSL)
  ↓
Displacement (>3% move)
  ↓
CHoCH (Structure Break)
  ↓
Return to OB/FVG
  ↓
Entry Candle ✅
  ↓
ENTER TRADE (50% position)
  ↓
Retest Confirmation → Add 30%
  ↓
Momentum → Add 20%
  ↓
TP1 Hit → Close 30%, SL to BE
  ↓
TP2 Hit → Close 30%, Trail SL
  ↓
TP3 Hit → Close 20%, Runner 20%
  ↓
Journal & Review
```

---

## 🎯 ACTION NOW!

1. ✅ **Mark levels on TradingView**
2. ✅ **Set 4 price alerts** (see above)
3. ✅ **Set limit orders** (optional):
   - Long: $59,400
   - Short: $62,000
4. ✅ **Check macro dashboard:** https://YOUR_URL.onrender.com/macro
5. ✅ **Wait patiently!** Don't chase!

---

**STATUS:** 🟡 **WAITING FOR SETUP**  
**Next Move:** BSL sweep ($59,500) or SSL sweep ($61,200)  
**Patience = Profit!** 💰

---

*Print this page or save as PDF for quick reference!*  
*Full details: BTCUSDT_COMPLETE_SETUP.md*
