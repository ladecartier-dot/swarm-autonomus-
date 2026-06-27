"""
Macro Economic Data Collector
Collects: CPI, PPI, Fed Funds, DXY, Yields, VIX, Gold, S&P500, Nasdaq
Sources: FRED API, Alpha Vantage
Time Range: 1980-2026

Usage:
    python macro_collector.py --indicators CPI,DXY,FFR --start 1980-01-01
    python macro_collector.py --realtime
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import asyncpg
import os

class MacroCollector:
    def __init__(self):
        self.fred_api = "https://api.stlouisfed.org/fred"
        self.fred_key = os.getenv('FRED_API_KEY', '8101e05db182ccd505bc50920a8f097c')
        
        self.alphavantage_api = "https://www.alphavantage.co/query"
        self.alphavantage_key = os.getenv('ALPHA_VANTAGE_KEY', 'CS37J2Y39A7P4BHS')
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
        
        self.session = None
        self.db_pool = None
        
        # FRED series IDs
        self.fred_series = {
            'CPI': 'CPIAUCSL',
            'PPI': 'PPIACO',
            'fed_funds': 'FEDFUNDS',
            'yield_10y': 'DGS10',
            'yield_2y': 'DGS2',
            'unemployment': 'UNRATE',
            'nfp': 'PAYEMS',
            'm2': 'M2SL',
            'fed_balance': 'WALCL',
            'vix': 'VIXCLS'
        }
        
        # Alpha Vantage symbols
        self.av_symbols = {
            'DXY': 'UUP',  # USD ETF as DXY proxy
            'gold': 'GLD',
            'sp500': 'SPY',
            'nasdaq': 'QQQ'
        }
    
    async def connect(self):
        self.session = aiohttp.ClientSession()
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        print("✅ Macro collector connected")
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def fetch_fred_series(self, series_id: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch data from FRED API"""
        url = f"{self.fred_api}/series/observations"
        
        params = {
            'series_id': series_id,
            'api_key': self.fred_key,
            'file': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }
        
        all_data = []
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'observations' in data:
                        for obs in data['observations']:
                            if obs['value'] and obs['value'] != '.':
                                all_data.append({
                                    'timestamp': datetime.strptime(obs['date'], '%Y-%m-%d'),
                                    'value': float(obs['value']),
                                    'series_id': series_id
                                })
        except Exception as e:
            print(f"❌ FRED error for {series_id}: {e}")
        
        return all_data
    
    async def fetch_alphavantage(self, symbol: str) -> List[Dict]:
        """Fetch data from Alpha Vantage (for DXY, Gold, etc.)"""
        url = self.alphavantage_api
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.alphavantage_key,
            'outputsize': 'full'
        }
        
        all_data = []
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'Time Series (Daily)' in data:
                        for date, values in data['Time Series (Daily)'].items():
                            all_data.append({
                                'timestamp': datetime.strptime(date, '%Y-%m-%d'),
                                'value': float(values['4. close']),
                                'series_id': symbol
                            })
        except Exception as e:
            print(f"❌ Alpha Vantage error for {symbol}: {e}")
        
        return all_data
    
    async def save_to_db(self, data: List[Dict]):
        """Save macro data to PostgreSQL"""
        if not data:
            return
        
        async with self.db_pool.acquire() as conn:
            for record in data:
                # Determine indicator name
                indicator = record['series_id']
                for name, series in {**self.fred_series, **self.av_symbols}.items():
                    if series == indicator:
                        indicator = name
                        break
                
                query = """
                    INSERT INTO macro_indicators 
                    (indicator, timestamp, value, source)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (indicator, timestamp) DO UPDATE SET
                        value = EXCLUDED.value
                """
                
                await conn.execute(query, indicator, record['timestamp'], 
                                 record['value'], 'FRED' if record['series_id'] in self.fred_series.values() else 'AlphaVantage')
        
        print(f"✅ Saved {len(data)} macro records")
    
    async def collect_historical(self, indicators: List[str], start_date: str, end_date: str):
        """Collect macro data historically"""
        print(f"\n🚀 Collecting macro data")
        print(f"   Range: {start_date} to {end_date}")
        print(f"   Indicators: {', '.join(indicators)}")
        
        all_data = []
        
        for indicator in indicators:
            if indicator in self.fred_series:
                series_id = self.fred_series[indicator]
                print(f"   📊 Fetching {indicator} from FRED...")
                data = await self.fetch_fred_series(series_id, start_date, end_date)
                if data:
                    all_data.extend(data)
                    print(f"      Got {len(data)} data points")
            
            elif indicator in self.av_symbols:
                symbol = self.av_symbols[indicator]
                print(f"   📊 Fetching {indicator} from Alpha Vantage...")
                data = await self.fetch_alphavantage(symbol)
                if data:
                    all_data.extend(data)
                    print(f"      Got {len(data)} data points")
        
        # Save all data
        await self.save_to_db(all_data)
        print(f"✅ Macro collection complete")
    
    async def collect_realtime(self, indicators: List[str] = None):
        """Collect real-time macro data"""
        if indicators is None:
            indicators = ['DXY', 'yield_10y', 'fed_funds', 'vix', 'gold']
        
        print(f"🔴 Starting real-time macro collection")
        
        while True:
            try:
                # Fetch last 30 days
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
                all_data = []
                
                for indicator in indicators:
                    if indicator in self.fred_series:
                        data = await self.fetch_fred_series(self.fred_series[indicator], start_date, end_date)
                        if data:
                            all_data.extend(data)
                    elif indicator in self.av_symbols:
                        data = await self.fetch_alphavantage(self.av_symbols[indicator])
                        if data:
                            all_data.extend(data[-30:])  # Last 30 days
                
                if all_data:
                    await self.save_to_db(all_data)
                    print(f"✅ Real-time macro update @ {datetime.now()}")
                
                await asyncio.sleep(3600)  # Update hourly
                
            except Exception as e:
                print(f"❌ Real-time macro error: {e}")
                await asyncio.sleep(300)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Macro Data Collector')
    parser.add_argument('--indicators', type=str, help='Comma-separated indicators')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--realtime', action='store_true')
    
    args = parser.parse_args()
    
    collector = MacroCollector()
    await collector.connect()
    
    try:
        indicators = args.indicators.split(',') if args.indicators else list(MacroCollector().fred_series.keys())
        
        if args.realtime:
            await collector.collect_realtime(indicators)
        else:
            if not args.start:
                args.start = '1980-01-01'
            if not args.end:
                args.end = datetime.now().strftime('%Y-%m-%d')
            
            await collector.collect_historical(indicators, args.start, args.end)
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
