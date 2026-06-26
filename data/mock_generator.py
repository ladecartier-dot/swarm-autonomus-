#!/usr/bin/env python3
"""
Mock Data Generator - Generate realistic market data for testing
Use when APIs are unavailable or for backtesting
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_realistic_ohlcv(symbol: str, days: int = 200) -> list:
    """Generate realistic OHLCV data with trends and volatility"""
    
    # Base prices
    base_prices = {
        'BTCUSD': 95000,
        'ETHUSD': 3500,
        'SOLUSD': 200,
        'BNBUSD': 600,
        'XRPUSD': 0.50
    }
    
    base = base_prices.get(symbol, 100)
    
    # Generate data
    ohlcv = []
    current_price = base * random.uniform(0.8, 1.2)
    start_date = datetime.now() - timedelta(days=days)
    
    for i in range(days * 6):  # 6 H4 candles per day
        # Random walk with drift
        drift = random.uniform(-0.002, 0.003)  # Slight upward bias
        volatility = random.uniform(0.01, 0.04)
        
        open_price = current_price
        close_price = open_price * (1 + drift + random.uniform(-volatility, volatility))
        high = max(open_price, close_price) * (1 + random.uniform(0, volatility/2))
        low = min(open_price, close_price) * (1 - random.uniform(0, volatility/2))
        volume = random.uniform(1000, 50000) * (base / 1000)
        
        timestamp = int((start_date + timedelta(hours=4*i)).timestamp())
        
        ohlcv.append([
            timestamp,
            round(open_price, 2),
            round(high, 2),
            round(low, 2),
            round(close_price, 2),
            round(volume, 2)
        ])
        
        current_price = close_price
    
    return ohlcv


def generate_daily_data() -> dict:
    """Generate complete daily data package"""
    
    symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'BNBUSD', 'XRPUSD']
    
    # Generate prices
    base_prices = {
        'BTCUSD': 95000 + random.uniform(-2000, 2000),
        'ETHUSD': 3500 + random.uniform(-100, 100),
        'SOLUSD': 200 + random.uniform(-10, 10),
        'BNBUSD': 600 + random.uniform(-20, 20),
        'XRPUSD': 0.50 + random.uniform(-0.02, 0.02)
    }
    
    prices = {}
    for symbol in symbols:
        price = base_prices[symbol]
        change = random.uniform(-5, 5)
        prices[symbol] = {
            'symbol': symbol,
            'price': round(price, 2),
            'market_cap': round(price * random.uniform(1e9, 1e12)),
            'volume_24h': round(random.uniform(1e8, 1e10)),
            'change_24h': round(change, 2),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }
    
    # Generate OHLCV
    ohlcv = {}
    for symbol in ['BTCUSD', 'ETHUSD', 'SOLUSD']:
        ohlcv[symbol] = {
            'D1': generate_realistic_ohlcv(symbol, days=200)[-200:],
            'H4': generate_realistic_ohlcv(symbol, days=50)[-300:],
            'H1': generate_realistic_ohlcv(symbol, days=10)[-240:]
        }
    
    # Fear & Greed
    fg_value = random.randint(20, 80)
    if fg_value < 30:
        classification = 'Fear'
    elif fg_value < 50:
        classification = 'Neutral'
    elif fg_value < 70:
        classification = 'Greed'
    else:
        classification = 'Extreme Greed'
    
    fear_greed = {
        'value': fg_value,
        'classification': classification,
        'timestamp': int(datetime.now().timestamp()),
        'source': 'mock'
    }
    
    # Funding rates
    funding_rates = {
        'BTCUSDT': {
            'symbol': 'BTCUSDT',
            'funding_rate': random.uniform(0.0001, 0.0005),
            'next_funding': int((datetime.now() + timedelta(hours=8)).timestamp() * 1000),
            'mark_price': base_prices['BTCUSD'] * random.uniform(0.999, 1.001)
        },
        'ETHUSDT': {
            'symbol': 'ETHUSDT',
            'funding_rate': random.uniform(0.0001, 0.0005),
            'mark_price': base_prices['ETHUSD'] * random.uniform(0.999, 1.001)
        }
    }
    
    return {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'ohlcv': ohlcv,
        'fear_greed': fear_greed,
        'funding_rates': funding_rates,
        'market_stats': {
            'total_market_cap': random.uniform(2e12, 3e12),
            'total_volume_24h': random.uniform(5e10, 1e11),
            'btc_dominance': random.uniform(45, 55)
        }
    }


def main():
    """Generate and save mock daily data"""
    print("="*60)
    print("📊 MOCK DATA GENERATOR")
    print("="*60)
    
    data = generate_daily_data()
    
    # Save to file
    data_dir = Path(__file__).parent.parent / "data" / "historical"
    data_dir.mkdir(exist_ok=True)
    
    filename = f"daily_data_{datetime.now().strftime('%Y-%m-%d')}_mock.json"
    filepath = data_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Also update latest
    latest_path = data_dir / "latest.json"
    with open(latest_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Mock data generated!")
    print(f"📁 Saved to: {filepath}")
    
    # Print summary
    print("\n" + "="*60)
    print("📋 DATA SUMMARY")
    print("="*60)
    
    print("\n😨 Fear & Greed:")
    fg = data['fear_greed']
    print(f"  Value: {fg['value']} ({fg['classification']})")
    
    print("\n💰 Prices:")
    for symbol, p in data['prices'].items():
        change = p['change_24h']
        emoji = '📈' if change > 0 else '📉'
        print(f"  {symbol}: ${p['price']:,.2f} {emoji} ({change:+.2f}%)")
    
    print("\n📊 OHLCV Datasets:")
    for symbol, tfs in data['ohlcv'].items():
        for tf, candles in tfs.items():
            print(f"  {symbol} {tf}: {len(candles)} candles")
    
    print("\n💸 Funding Rates:")
    for symbol, f in data['funding_rates'].items():
        rate = f['funding_rate'] * 100
        print(f"  {symbol}: {rate:.4f}%")
    
    print(f"\n💾 File: {filepath}")


if __name__ == "__main__":
    main()
