"""
Futures Data Collector - Historical & Real-Time
Collects: Funding Rate, Open Interest, Liquidation, Taker Volume
Sources: Coinglass API, Binance Futures
Time Range: 2018-2026

Usage:
    python futures_collector.py --symbol BTC --start 2018-01-01
    python futures_collector.py --symbol ETH, SOL --realtime
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncpg
import os
from pathlib import Path
import time

class FuturesCollector:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.coinglass_api = "https://open-api.coinglass.com/api/v3"
        self.binance_api = "https://fapi.binance.com/fapi/v1"
        self.db_config = self.load_db_config()
        self.session = None
        
        # API Keys
        self.coinglass_key = os.getenv('COINGLASS_API_KEY', '')
        self.binance_key = os.getenv('BINANCE_API_KEY', '')
        
        # Symbol mapping
        self.symbol_map = {
            'BTC': 'BTC',
            'ETH': 'ETH',
            'SOL': 'SOL',
            'BNB': 'BNB',
            'XRP': 'XRP'
        }
        
    def load_db_config(self) -> Dict:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
    
    async def connect(self):
        """Initialize connections"""
        headers = {'Content-Type': 'application/json'}
        if self.coinglass_key:
            headers['coinglassSecret'] = self.coinglass_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        print(f"✅ Futures collector connected")
    
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def fetch_funding_rate(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch funding rate history from Coinglass"""
        all_data = []
        
        url = f"{self.coinglass_api}/futures/funding-rate-history"
        
        # Coinglass returns limited data per request, need to paginate
        current_date = start_date
        while current_date <= end_date:
            params = {
                'symbol': symbol,
                'startTime': int(datetime.strptime(current_date, '%Y-%m-%d').timestamp() * 1000),
                'endTime': int((datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=7)).timestamp() * 1000),
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and data.get('data'):
                            for item in data['data']:
                                all_data.append({
                                    'timestamp': datetime.fromtimestamp(item['fundingTime'] / 1000),
                                    'funding_rate': float(item.get('fundingRate', 0)),
                                    'predicted_funding': float(item.get('predictRate', 0))
                                })
                        current_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
                    else:
                        print(f"⚠️  Coinglass API error: {response.status}")
                        time.sleep(1)
                        break
            except Exception as e:
                print(f"❌ Funding rate error: {e}")
                time.sleep(2)
        
        return all_data
    
    async def fetch_open_interest(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch open interest history"""
        all_data = []
        
        url = f"{self.coinglass_api}/futures/open-interest-history"
        
        current_date = start_date
        while current_date <= end_date:
            params = {
                'symbol': symbol,
                'startTime': int(datetime.strptime(current_date, '%Y-%m-%d').timestamp() * 1000),
                'endTime': int((datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=30)).timestamp() * 1000),
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and data.get('data'):
                            for item in data['data']:
                                all_data.append({
                                    'timestamp': datetime.fromtimestamp(item['ts'] / 1000),
                                    'open_interest': float(item.get('openInterest', 0)),
                                    'oi_change_24h': float(item.get('openInterestChange', 0))
                                })
                        current_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            except Exception as e:
                print(f"❌ OI error: {e}")
                time.sleep(2)
        
        return all_data
    
    async def fetch_liquidation(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch liquidation data"""
        all_data = []
        
        url = f"{self.coinglass_api}/futures/liquidation"
        
        # Fetch daily liquidation data
        current_date = start_date
        while current_date <= end_date:
            params = {
                'symbol': symbol,
                'startTime': int(datetime.strptime(current_date, '%Y-%m-%d').timestamp() * 1000),
                'endTime': int((datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=1)).timestamp() * 1000),
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success') and data.get('data'):
                            daily_long = 0
                            daily_short = 0
                            for item in data['data']:
                                if item.get('side') == 'long' or item.get('side') == 'sell':
                                    daily_long += float(item.get('usd_value', 0))
                                else:
                                    daily_short += float(item.get('usd_value', 0))
                            
                            all_data.append({
                                'timestamp': datetime.strptime(current_date, '%Y-%m-%d'),
                                'liquidation_long': daily_long,
                                'liquidation_short': daily_short,
                                'liquidation_total': daily_long + daily_short
                            })
                        current_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            except Exception as e:
                print(f"❌ Liquidation error: {e}")
                time.sleep(2)
        
        return all_data
    
    async def fetch_taker_volume(self, symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch taker buy/sell volume from Binance"""
        all_data = []
        
        # Use Binance Taker Buy/Sell Volume API
        url = f"{self.binance_api}/taker_long_short_ratio"
        
        current_date = start_date
        while current_date <= end_date:
            params = {
                'symbol': f"{symbol}USDT",
                'period': '1d',
                'startTime': int(datetime.strptime(current_date, '%Y-%m-%d').timestamp() * 1000),
                'endTime': int((datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=30)).timestamp() * 1000),
                'limit': 30
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data:
                            all_data.append({
                                'timestamp': datetime.fromtimestamp(item['timestamp'] / 1000),
                                'taker_buy_volume': float(item.get('buyVol', 0)),
                                'taker_sell_volume': float(item.get('sellVol', 0)),
                                'taker_ratio': float(item.get('buyVol', 1)) / max(float(item.get('sellVol', 1)), 0.001),
                                'long_short_ratio': float(item.get('buySellRatio', 1))
                            })
                        current_date = (datetime.strptime(current_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            except Exception as e:
                print(f"❌ Taker volume error: {e}")
                time.sleep(2)
        
        return all_data
    
    async def save_to_db(self, symbol: str, data: List[Dict], data_type: str):
        """Save futures data to PostgreSQL"""
        if not data:
            return
        
        async with self.db_pool.acquire() as conn:
            for record in data:
                if data_type == 'funding':
                    query = """
                        INSERT INTO futures_metrics 
                        (symbol, timestamp, funding_rate, predicted_funding)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (symbol, timestamp) DO UPDATE SET
                            funding_rate = EXCLUDED.funding_rate,
                            predicted_funding = EXCLUDED.predicted_funding
                    """
                    await conn.execute(query, symbol, record['timestamp'], 
                                     record.get('funding_rate'), record.get('predicted_funding'))
                
                elif data_type == 'oi':
                    query = """
                        INSERT INTO futures_metrics 
                        (symbol, timestamp, open_interest, oi_change_24h)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (symbol, timestamp) DO UPDATE SET
                            open_interest = EXCLUDED.open_interest,
                            oi_change_24h = EXCLUDED.oi_change_24h
                    """
                    await conn.execute(query, symbol, record['timestamp'],
                                     record.get('open_interest'), record.get('oi_change_24h'))
                
                elif data_type == 'liquidation':
                    query = """
                        INSERT INTO futures_metrics 
                        (symbol, timestamp, liquidation_long, liquidation_short, liquidation_total)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (symbol, timestamp) DO UPDATE SET
                            liquidation_long = EXCLUDED.liquidation_long,
                            liquidation_short = EXCLUDED.liquidation_short,
                            liquidation_total = EXCLUDED.liquidation_total
                    """
                    await conn.execute(query, symbol, record['timestamp'],
                                     record.get('liquidation_long'), record.get('liquidation_short'),
                                     record.get('liquidation_total'))
                
                elif data_type == 'taker':
                    query = """
                        INSERT INTO futures_metrics 
                        (symbol, timestamp, taker_buy_volume, taker_sell_volume, taker_ratio, long_short_ratio)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (symbol, timestamp) DO UPDATE SET
                            taker_buy_volume = EXCLUDED.taker_buy_volume,
                            taker_sell_volume = EXCLUDED.taker_sell_volume,
                            taker_ratio = EXCLUDED.taker_ratio,
                            long_short_ratio = EXCLUDED.long_short_ratio
                    """
                    await conn.execute(query, symbol, record['timestamp'],
                                     record.get('taker_buy_volume'), record.get('taker_sell_volume'),
                                     record.get('taker_ratio'), record.get('long_short_ratio'))
        
        print(f"✅ Saved {len(data)} {data_type} records for {symbol}")
    
    async def collect_historical(self, symbol: str, start_date: str, end_date: str):
        """Collect all futures metrics historically"""
        binance_symbol = self.symbol_map.get(symbol, symbol)
        
        print(f"\n🚀 Collecting futures data for {symbol}")
        print(f"   Range: {start_date} to {end_date}")
        
        # Fetch all metrics
        print("   📊 Fetching funding rates...")
        funding_data = await self.fetch_funding_rate(binance_symbol, start_date, end_date)
        await self.save_to_db(binance_symbol, funding_data, 'funding')
        
        print("   📊 Fetching open interest...")
        oi_data = await self.fetch_open_interest(binance_symbol, start_date, end_date)
        await self.save_to_db(binance_symbol, oi_data, 'oi')
        
        print("   📊 Fetching liquidation data...")
        liq_data = await self.fetch_liquidation(binance_symbol, start_date, end_date)
        await self.save_to_db(binance_symbol, liq_data, 'liquidation')
        
        print("   📊 Fetching taker volume...")
        taker_data = await self.fetch_taker_volume(binance_symbol, start_date, end_date)
        await self.save_to_db(binance_symbol, taker_data, 'taker')
        
        print(f"✅ Futures collection complete for {symbol}")
    
    async def collect_realtime(self, symbol: str):
        """Collect real-time futures data"""
        binance_symbol = self.symbol_map.get(symbol, symbol)
        print(f"🔴 Starting real-time futures collection for {symbol}")
        
        while True:
            try:
                # Fetch latest data (last 24h)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                # Quick fetch of all metrics
                funding = await self.fetch_funding_rate(binance_symbol, start_date, end_date)
                oi = await self.fetch_open_interest(binance_symbol, start_date, end_date)
                liq = await self.fetch_liquidation(binance_symbol, start_date, end_date)
                
                # Save to DB
                if funding:
                    await self.save_to_db(binance_symbol, funding[-24:], 'funding')
                if oi:
                    await self.save_to_db(binance_symbol, oi[-24:], 'oi')
                if liq:
                    await self.save_to_db(binance_symbol, liq, 'liquidation')
                
                print(f"✅ Real-time futures update: {symbol} @ {datetime.now()}")
                await asyncio.sleep(300)  # Update every 5 minutes
                
            except Exception as e:
                print(f"❌ Real-time futures error: {e}")
                await asyncio.sleep(60)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Futures Data Collector')
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--realtime', action='store_true')
    
    args = parser.parse_args()
    
    collector = FuturesCollector()
    await collector.connect()
    
    try:
        if args.realtime:
            await collector.collect_realtime(args.symbol)
        else:
            if not args.start:
                args.start = '2018-01-01'
            if not args.end:
                args.end = datetime.now().strftime('%Y-%m-%d')
            
            await collector.collect_historical(args.symbol, args.start, args.end)
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
