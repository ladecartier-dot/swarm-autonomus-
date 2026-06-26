# 🎯 BTCUSDT Trade Setup - SMC Strategy
**Date:** Jun 26, 2026  
**Timeframe:** 1W (Primary), 4H/1D (Entry)  
**Exchange:** Binance

---

## 📊 Market Structure

### Current Bias: ________ (Bullish/Bearish/Neutral)

**Structure Points:**
```
Last Significant High: $________
Last Significant Low:  $________
Current Price:         $________

Market Structure: 
□ Bullish (HH + HL)
□ Bearish (LH + LL)
□ Ranging (Consolidation)
```

---

## 🎯 Key Levels

### Liquidity Zones
| Type | Price | Notes |
|------|-------|-------|
| Buy-Side Liquidity (BSL) | $______ | Equal lows / swing lows |
| Sell-Side Liquidity (SSL) | $______ | Equal highs / swing highs |
| Internal Liquidity | $______ | Trendline touches |

### Order Blocks
| Type | Price | Timeframe | Mitigated? |
|------|-------|-----------|------------|
| Bullish OB | $______ | 1W / 4H | □ Yes □ No |
| Bearish OB | $______ | 1W / 4H | □ Yes □ No |

### Fair Value Gaps (FVG)
| Direction | Price Range | Filled? |
|-----------|-------------|---------|
| Bullish FVG | $______ - $______ | □ Yes □ No |
| Bearish FVG | $______ - $______ | □ Yes □ No |

---

## 🎯 Trade Scenarios

### **Scenario A: Bullish Continuation** 🟢
**Condition:** Price holds above key support + takes BSL

**Entry Zone:** $______ - $______
- Wait for liquidity sweep of lows
- Look for displacement (strong candle) up
- Entry on retest to bullish OB / FVG

**Stop Loss:** $______ (below recent swing low)
**Take Profit:**
- TP1: $______ (recent high / internal liquidity)
- TP2: $______ (major resistance)
- TP3: $______ (price discovery)

**Risk:Reward:** 1:___

---

### **Scenario B: Bearish Reversal** 🔴
**Condition:** CHoCH (Change of Character) + takes SSL

**Entry Zone:** $______ - $______
- Wait for liquidity sweep of highs
- Look for bearish displacement
- Entry on retest to bearish OB / FVG

**Stop Loss:** $______ (above recent swing high)
**Take Profit:**
- TP1: $______ (recent low)
- TP2: $______ (major support)
- TP3: $______ (liquidity below)

**Risk:Reward:** 1:___

---

### **Scenario C: Range Play** 🟡
**Condition:** Price consolidating between clear levels

**Long:** Near range low + BSL sweep
**Short:** Near range high + SSL sweep

**Stop Loss:** Outside range
**Take Profit:** Opposite side of range

---

## ⚠️ Invalidation

**Bullish Invalidated If:**
- Price closes below $______ (key level)
- Market structure breaks (LH → LL)

**Bearish Invalidated If:**
- Price closes above $______ (key level)
- Market structure breaks (HL → HH)

---

## 📈 Confirmation Signals

Wait for these before entry:

### On 4H/1D:
- [ ] Liquidity sweep (wick through key level)
- [ ] Displacement (strong impulsive candle)
- [ ] Market structure shift (CHoCH)
- [ ] Return to OB/FVG
- [ ] Entry candle (rejection/engulfing)

### Volume:
- [ ] Above average on displacement
- [ ] Decreasing on pullback

---

## 💰 Risk Management

**Position Size:** ___% of portfolio  
**Risk per Trade:** ___% (max 2%)  
**R:R Minimum:** 1:2  

**Calculation:**
```
Entry:     $______
Stop:      $______
Risk:      $______ (___%)

Position = (Account × Risk%) ÷ (Entry - Stop)
Position = $______

Leverage: ___x (max 5x for swing)
```

---

## 📝 Trade Journal

### Pre-Trade Checklist
- [ ] Market structure clear
- [ ] Liquidity identified
- [ ] OB/FVG marked
- [ ] Entry plan defined
- [ ] R:R ≥ 1:2
- [ ] No major news events

### Post-Trade Notes
**Entry:** $______  
**Exit:** $______  
**PnL:** $______ (___%)  

**What went well:**
- 

**What to improve:**
- 

---

## 🔗 Integration dengan Swarm

Setelah setup complete, integrate dengan swarm-trader:

```bash
# Add to swarm agents
python signals/generate_signals.py --symbol BTCUSDT --setup "SMC_1W_BULLISH"

# Monitor via dashboard
curl https://YOUR_URL.onrender.com/api/macro
```

---

**Last Updated:** Jun 26, 2026  
**Status:** □ Active □ Pending □ Filled □ Closed
