#!/usr/bin/env python3
"""
Daily Data Fetcher - Fetch real-time market data daily
Stores OHLCV, prices, and metrics for analysis
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.blackboard import get_blackboard


class DailyDataFetcher:
    """
    Fetch and store daily market data from multiple sources.
    
    Data collected:
    - Current prices (BTC, ETH, SOL, etc.)
    - OHLCV data (D1, H4, H1 timeframes)
    - Fear & Greed Index
    - Funding rates
    - 24h stats
    """
    
    def __init__(self):
        self.blackboard = get_blackboard()
        self.session: Optional[aiohttp.ClientSession] = None
        self.data_dir = Path(__file__).parent.parent / "data" / "historical"
        self.data_dir.mkdir(exist_ok=True)
        
        # Symbols to track
        self.symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'BNBUSD', 'XRPUSD']
        
        # CoinGecko IDs
        self.coin_ids = {
            'BTCUSD': 'bitcoin',
            'ETHUSD': 'ethereum',
            'SOLUSD': 'solana',
            'BNBUSD': 'binancecoin',
            'XRPUSD': 'ripple',
            'ADAUSD': 'cardano',
            'DOGEUSD': 'dogecoin',
            'AVAXUSD': 'avalanche-2',
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_all_daily_data(self) -> Dict:
        """Fetch all daily data"""
        print("="*60)
        print(f"📊 DAILY DATA FETCH - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'prices': {},
            'ohlcv': {},
            'fear_greed': None,
            'funding_rates': {},
            'market_stats': {}
        }
        
        # 1. Fetch Fear & Greed Index
        print("\n📈 Fetching Fear & Greed Index...")
        results['fear_greed'] = await self._fetch_fear_greed()
        
        # 2. Fetch prices for all symbols
        print("\n💰 Fetching prices...")
        for symbol in self.symbols:
            print(f"  Fetching {symbol}...")
            price_data = await self._fetch_price(symbol)
            if price_data:
                results['prices'][symbol] = price_data
        
        # 3. Fetch OHLCV for key symbols
        print("\n📊 Fetching OHLCV data...")
        for symbol in ['BTCUSD', 'ETHUSD', 'SOLUSD']:
            print(f"  Fetching {symbol} OHLCV...")
            ohlcv_data = await self._fetch_ohlcv_multi_timeframe(symbol)
            if ohlcv_data:
                results['ohlcv'][symbol] = ohlcv_data
        
        # 4. Fetch funding rates
        print("\n💸 Fetching funding rates...")
        for symbol in ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']:
            funding = await self._fetch_funding_rate(symbol)
            if funding:
                results['funding_rates'][symbol] = funding
        
        # 5. Save to file
        await self._save_daily_data(results)
        
        # 6. Update blackboard
        self._update_blackboard(results)
        
        print("\n✅ Daily data fetch complete!")
        print(f"📁 Saved to: {self.data_dir / self._get_today_filename()}")
        
        return results
    
    async def _fetch_price(self, symbol: str) -> Optional[Dict]:
        """Fetch current price from CoinGecko"""
        coin_id = self.coin_ids.get(symbol.replace('USD', ''))
        if not coin_id:
            return None
        
        try:
            session = await self._get_session()
            url = 'https://api.coingecko.com/api/v3/simple/price'
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if coin_id in data:
                        p = data[coin_id]
                        return {
                            'symbol': symbol,
                            'price': p.get('usd'),
                            'market_cap': p.get('usd_market_cap'),
                            'volume_24h': p.get('usd_24h_vol'),
                            'change_24h': p.get('usd_24h_change'),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'coingecko'
                        }
                elif resp.status == 429:
                    print(f"    ⚠️ Rate limited, using backup...")
                    return await self._fetch_price_backup(symbol)
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return await self._fetch_price_backup(symbol)
        
        return None
    
    async def _fetch_price_backup(self, symbol: str) -> Optional[Dict]:
        """Backup price fetch from CoinPaprika"""
        try:
            session = await self._get_session()
            sym = symbol.replace('USD', '').upper()
            url = f'https://api.coinpaprika.com/v1/tickers/{sym}-{sym}'
            
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'symbol': symbol,
                        'price': data['quotes']['USD']['price'],
                        'volume_24h': data['quotes']['USD']['volume_24h'],
                        'change_24h': data['quotes']['USD']['percent_change_24h'],
                        'timestamp': datetime.now().isoformat(),
                        'source': 'coinpaprika'
                    }
        except:
            pass
        return None
    
    async def _fetch_ohlcv_multi_timeframe(self, symbol: str) -> Dict:
        """Fetch OHLCV for multiple timeframes"""
        result = {}
        
        # Fetch D1, H4, H1
        for tf in ['D1', 'H4', 'H1']:
            ohlcv = await self._fetch_ohlcv(symbol, tf)
            if ohlcv:
                result[tf] = ohlcv
        
        return result
    
    async def _fetch_ohlcv(self, symbol: str, timeframe: str) -> Optional[List[List]]:
        """Fetch OHLCV from Binance public API"""
        try:
            session = await self._get_session()
            
            # Convert to Binance format
            binance_symbol = symbol.replace('USD', 'USDT')
            tf_map = {'D1': '1d', 'H4': '4h', 'H1': '1h'}
            binance_tf = tf_map.get(timeframe, '4h')
            
            url = 'https://api.binance.com/api/v3/klines'
            params = {
                'symbol': binance_symbol,
                'interval': binance_tf,
                'limit': 200
            }
            
            async with session.get(url, params=params, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    ohlcv = []
                    for candle in data:
                        ohlcv.append([
                            candle[0] // 1000,  # Timestamp
                            float(candle[1]),   # Open
                            float(candle[2]),   # High
                            float(candle[3]),   # Low
                            float(candle[4]),   # Close
                            float(candle[5]),   # Volume
                        ])
                    return ohlcv
        except Exception as e:
            print(f"    ❌ OHLCV fetch error for {symbol} {timeframe}: {e}")
        return None
    
    async def _fetch_fear_greed(self) -> Optional[Dict]:
        """Fetch Crypto Fear & Greed Index"""
        try:
            session = await self._get_session()
            url = 'https://api.alternative.me/fng/'
            
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'success':
                        latest = data['data'][0]
                        return {
                            'value': int(latest['value']),
                            'classification': latest['value_classification'],
                            'timestamp': latest['timestamp'],
                            'source': 'alternative.me'
                        }
        except Exception as e:
            print(f"    ❌ Fear & Greed fetch error: {e}")
        return None
    
    async def _fetch_funding_rate(self, symbol: str) -> Optional[Dict]:
        """Fetch funding rate from Binance"""
        try:
            session = await self._get_session()
            url = f'https://fapi.binance.com/fapi/v1/premiumIndex'
            params = {'symbol': symbol}
            
            async with session.get(url, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'symbol': symbol,
                        'funding_rate': float(data.get('lastFundingRate', 0)),
                        'next_funding': data.get('nextFundingTime', ''),
                        'mark_price': float(data.get('markPrice', 0))
                    }
        except Exception as e:
            pass
        return None
    
    def _get_today_filename(self) -> str:
        """Get filename for today's data"""
        return f"daily_data_{datetime.now().strftime('%Y-%m-%d')}.json"
    
    async def _save_daily_data(self, data: Dict):
        """Save data to JSON file"""
        filename = self._get_today_filename()
        filepath = self.data_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Also update latest.json symlink
        latest_path = self.data_dir / "latest.json"
        with open(latest_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _update_blackboard(self, data: Dict):
        """Update blackboard with latest data"""
        bb = self.blackboard
        
        # Cache prices
        for symbol, price_data in data.get('prices', {}).items():
            bb.cache_market_data(symbol, 'D1', 'price', price_data)
        
        # Cache OHLCV
        for symbol, tf_data in data.get('ohlcv', {}).items():
            for tf, ohlcv in tf_data.items():
                bb.cache_market_data(symbol, tf, 'ohlcv', ohlcv)
        
        # Store fear & greed
        if data.get('fear_greed'):
            bb.set_state('fear_greed_latest', data['fear_greed'])
        
        # Update state file
        bb.update_state_file(
            'Daily Data Fetch',
            f"Fetched {len(data.get('prices', {}))} prices, {len(data.get('ohlcv', {}))} OHLCV datasets"
        )


async def main():
    """Main entry point"""
    fetcher = DailyDataFetcher()
    
    try:
        results = await fetcher.fetch_all_daily_data()
        
        # Print summary
        print("\n" + "="*60)
        print("📋 DAILY DATA SUMMARY")
        print("="*60)
        
        if results.get('fear_greed'):
            fg = results['fear_greed']
            print(f"\n😨 Fear & Greed: {fg['value']} ({fg['classification']})")
        
        print("\n💰 Prices:")
        for symbol, data in results.get('prices', {}).items():
            change = data.get('change_24h', 0)
            emoji = '📈' if change > 0 else '📉' if change < 0 else '➡️'
            print(f"  {symbol}: ${data['price']:,.2f} {emoji} ({change:+.2f}%)")
        
        print("\n💸 Funding Rates:")
        for symbol, data in results.get('funding_rates', {}).items():
            rate = data.get('funding_rate', 0) * 100
            print(f"  {symbol}: {rate:.4f}%")
        
        print("\n✅ All data saved successfully!")
        
    finally:
        await fetcher.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Daily Data Fetcher')
    parser.add_argument('--symbols', nargs='+', help='Override symbols to fetch')
    parser.add_argument('--output', type=str, help='Output directory')
    
    args = parser.parse_args()
    
    asyncio.run(main())
