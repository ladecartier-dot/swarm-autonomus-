# 📊 API Keys Configuration

## Environment Variables

Add these to your `.bashrc` or `.zshrc`:

```bash
export FRED_API_KEY="8101e05db182ccd505bc50920a8f097c"
export ALPHA_VANTAGE_KEY="CS37J2Y39A7P4BHS"
```

Or create a `.env` file in the project root:

```bash
FRED_API_KEY=8101e05db182ccd505bc50920a8f097c
ALPHA_VANTAGE_KEY=CS37J2Y39A7P4BHS
```

## Usage

### Load API Keys

```bash
# Source the env file
source state/api_keys.env

# Or export manually
export FRED_API_KEY="your-key"
export ALPHA_VANTAGE_KEY="your-key"
```

### Verify Keys

```bash
# Test FRED API
curl "https://api.stlouisfed.org/fred/series/series_id?series_id=GDP&api_key=$FRED_API_KEY&file_type=json"

# Test Alpha Vantage
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=$ALPHA_VANTAGE_KEY"
```

---

## 📈 Available Data Sources

### FRED (Federal Reserve Economic Data)

**Economic Indicators:**
- `GDP` - Gross Domestic Product
- `CPIAUCSL` - Consumer Price Index (inflation)
- `UNRATE` - Unemployment Rate
- `FEDFUNDS` - Federal Funds Rate (interest rates)
- `DGS10` - 10-Year Treasury Yield
- `DGS2` - 2-Year Treasury Yield
- `T10Y2Y` - 10Y-2Y Treasury Spread (recession indicator)
- `M2SL` - M2 Money Supply
- `PCE` - Personal Consumption Expenditures
- `PCEPI` - PCE Price Index (Fed's preferred inflation gauge)

**Example:**
```python
import requests

def get_fred_data(series_id, api_key):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json"
    }
    response = requests.get(url, params=params)
    return response.json()

# Get 10Y Treasury Yield
data = get_fred_data("DGS10", FRED_API_KEY)
```

### Alpha Vantage

**Market Data:**
- `GLOBAL_QUOTE` - Real-time stock quotes
- `TIME_SERIES_DAILY` - Historical stock data
- `TIME_SERIES_WEEKLY` - Weekly OHLCV
- `TIME_SERIES_MONTHLY` - Monthly OHLCV
- `FX_DAILY` - Forex rates
- `DIGITAL_CURRENCY_DAILY` - Crypto prices
- `TECHNICAL_INDICATORS` - RSI, MACD, SMA, EMA, etc.
- `SECTOR` - Sector performance

**Example:**
```python
import requests

def get_alpha_vantage_data(function, symbol, api_key):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    return response.json()

# Get BTC daily data
data = get_alpha_vantage_data("DIGITAL_CURRENCY_DAILY", "BTC", ALPHA_VANTAGE_KEY)
```

---

## 🔌 Integration with Swarm

### Updated Fetcher

The `data/fetcher.py` now supports:

1. **CoinGecko** - Crypto prices, market cap, volume
2. **Binance** - OHLCV data, funding rates
3. **FRED** - Economic indicators (NEW!)
4. **Alpha Vantage** - Stocks, forex, crypto, technicals (NEW!)

### Macro Agent Enhancement

The Macro Agent now pulls:

- **Interest rates** (FEDFUNDS, DGS10, DGS2)
- **Inflation** (CPIAUCSL, PCEPI)
- **Yield curve** (T10Y2Y spread)
- **Unemployment** (UNRATE)
- **Money supply** (M2SL)

This gives **institutional-grade macro context** for trading decisions!

---

## 📊 Rate Limits

| API | Free Tier Limit | Upgrade |
|-----|-----------------|---------|
| **FRED** | 120,000/day | Unlimited (free!) |
| **Alpha Vantage** | 25 calls/day | 5 calls/min (paid) |
| **CoinGecko** | 10-50 calls/min | Pro plans available |
| **Binance** | 1,200 weight/min | VIP tiers |

**Tip:** Cache data locally to avoid rate limits!

---

## 🛡️ Security Best Practices

1. **Never commit API keys to Git**
   - Add `state/api_keys.env` to `.gitignore`
   - Use environment variables in production

2. **Use testnet first**
   - Test with paper trading before live

3. **Monitor usage**
   - Check API dashboards for unusual activity

4. **Rotate keys periodically**
   - Regenerate keys every 3-6 months

---

## 🧪 Testing

```bash
# Load keys
source state/api_keys.env

# Test FRED
python -c "
import os
import requests
key = os.getenv('FRED_API_KEY')
r = requests.get('https://api.stlouisfed.org/fred/series/series_id?series_id=GDP&api_key=' + key + '&file_type=json')
print('FRED Status:', r.status_code)
"

# Test Alpha Vantage
python -c "
import os
import requests
key = os.getenv('ALPHA_VANTAGE_KEY')
r = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={key}')
print('Alpha Vantage Status:', r.status_code)
print(r.json())
"
```

---

## ✅ Verification

After running tests, you should see:

```
FRED Status: 200
Alpha Vantage Status: 200
{'Global Quote': {'01. symbol': 'AAPL', '02. open': '...', ...}}
```

If you get errors:
- Check API keys are correct
- Verify internet connection
- Check rate limits haven't been exceeded
