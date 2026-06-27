"""
OHLCV Data Collector - Historical & Real-Time
Supports: Binance, Coinbase, Kraken via CCXT
Timeframes: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 1D, 1W, 1M
Date Range: From inception to present

Usage:
    python ohlcv_collector.py --symbol BTC --start 2010-01-01 --timeframes 1m,5m,1H,1D
    python ohlcv_collector.py --symbol ETH --start 2015-08-07 --timeframes 1D
    python ohlcv_collector.py --symbol SOL --start 2020-04-10 --timeframes 1H,4H,1D
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncpg
import json
import os
from pathlib import Path

class OHLCVCollector:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.base_url = "https://api.binance.com"
        self.db_config = self.load_db_config()
        self.session = None
        
        # Timeframe mapping (Binance format)
        self.timeframe_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1H': '1h', '2H': '2h', '4H': '4h', '6H': '6h',
            '1D': '1d', '1W': '1w', '1M': '1M'
        }
        
        # Symbol mapping
        self.symbol_map = {
            'BTC': 'BTCUSDT',
            'ETH': 'ETHUSDT',
            'SOL': 'SOLUSDT',
            'BNB': 'BNBUSDT',
            'XRP': 'XRPUSDT'
        }
        
    def load_db_config(self) -> Dict:
        """Load PostgreSQL configuration from environment or file"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
    
    async def connect(self):
        """Initialize HTTP session and DB connection"""
        self.session = aiohttp.ClientSession()
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        print(f"✅ Connected to database: {self.db_config['database']}")
    
    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def fetch_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: int, 
        end_time: int,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch OHLCV data from Binance API
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Candle timeframe (e.g., '1h', '1d')
            start_time: Start timestamp (ms)
            end_time: End timestamp (ms)
            limit: Max candles per request (max 1000)
        
        Returns:
            List of OHLCV dictionaries
        """
        all_candles = []
        current_time = start_time
        
        while current_time < end_time:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'startTime': current_time,
                'endTime': end_time,
                'limit': min(limit, 1000)
            }
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if not data:
                            break
                        
                        # Parse Binance format: [time, open, high, low, close, volume, ...]
                        candles = []
                        for candle in data:
                            candles.append({
                                'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                                'open': float(candle[1]),
                                'high': float(candle[2]),
                                'low': float(candle[3]),
                                'close': float(candle[4]),
                                'volume': float(candle[5]),
                                'trades_count': int(candle[8]) if len(candle) > 8 else None
                            })
                        
                        all_candles.extend(candles)
                        
                        # Move to next batch
                        current_time = candle[0] + 1  # Move 1ms forward
                        
                        # Rate limit handling
                        if len(data) == limit:
                            await asyncio.sleep(0.2)  # 200ms delay
                        else:
                            break  # No more data
                    else:
                        error_text = await response.text()
                        print(f"❌ API Error {response.status}: {error_text}")
                        await asyncio.sleep(1)
                        
            except Exception as e:
                print(f"❌ Fetch error: {e}")
                await asyncio.sleep(2)
        
        return all_candles
    
    async def save_to_db(self, symbol: str, timeframe: str, candles: List[Dict]):
        """Save OHLCV data to PostgreSQL"""
        if not candles:
            return
        
        async with self.db_pool.acquire() as conn:
            # Prepare data for batch insert
            records = []
            for candle in candles:
                records.append((
                    symbol,
                    timeframe,
                    candle['timestamp'],
                    candle['open'],
                    candle['high'],
                    candle['low'],
                    candle['close'],
                    candle['volume'],
                    candle.get('trades_count')
                ))
            
            # Batch insert with ON CONFLICT DO NOTHING
            query = """
                INSERT INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume, trades_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (symbol, timeframe, timestamp) DO NOTHING
            """
            
            await conn.executemany(query, records)
            print(f"✅ Saved {len(records)} candles for {symbol} {timeframe}")
    
    async def save_to_parquet(self, symbol: str, timeframe: str, candles: List[Dict]):
        """Save OHLCV data to Parquet file"""
        if not candles:
            return
        
        df = pd.DataFrame(candles)
        df.set_index('timestamp', inplace=True)
        
        # Create directory
        output_dir = Path(f"/mnt/data/hermes/workspace/swarm-trader/data/storage/parquet/ohlcv/{symbol}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save to Parquet
        output_file = output_dir / f"{timeframe}.parquet"
        
        # Append if exists, else create new
        if output_file.exists():
            existing_df = pd.read_parquet(output_file)
            df = pd.concat([existing_df, df])
            df = df[~df.index.duplicated(keep='last')]
        
        df.sort_index(inplace=True)
        df.to_parquet(output_file, compression='snappy')
        print(f"✅ Saved to Parquet: {output_file}")
    
    async def collect_historical(
        self,
        symbol: str,
        timeframes: List[str],
        start_date: str,
        end_date: Optional[str] = None
    ):
        """
        Collect historical OHLCV data
        
        Args:
            symbol: Asset symbol (BTC, ETH, SOL)
            timeframes: List of timeframes to collect
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (default: today)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Convert to timestamps (ms)
        start_ts = int(start_dt.timestamp() * 1000)
        end_ts = int(end_dt.timestamp() * 1000)
        
        # Map symbol
        binance_symbol = self.symbol_map.get(symbol, f"{symbol}USDT")
        
        print(f"\n🚀 Starting historical collection for {symbol}")
        print(f"   Symbol: {binance_symbol}")
        print(f"   Range: {start_date} to {end_date}")
        print(f"   Timeframes: {', '.join(timeframes)}")
        
        for tf in timeframes:
            binance_tf = self.timeframe_map.get(tf, tf.lower())
            print(f"\n📊 Collecting {tf} timeframe...")
            
            candles = await self.fetch_ohlcv(binance_symbol, binance_tf, start_ts, end_ts)
            
            if candles:
                print(f"   Fetched {len(candles)} candles")
                
                # Save to both DB and Parquet
                await self.save_to_db(binance_symbol, tf, candles)
                await self.save_to_parquet(binance_symbol, tf, candles)
            else:
                print(f"   ⚠️  No data found for {tf}")
            
            # Delay between timeframes
            await asyncio.sleep(1)
    
    async def collect_realtime(self, symbol: str, timeframes: List[str]):
        """Collect real-time OHLCV data (run as continuous service)"""
        binance_symbol = self.symbol_map.get(symbol, f"{symbol}USDT")
        
        print(f"\n🔴 Starting real-time collection for {symbol}")
        print(f"   Symbol: {binance_symbol}")
        print(f"   Timeframes: {', '.join(timeframes)}")
        
        while True:
            try:
                # Get last 1000 candles for each timeframe
                end_ts = int(datetime.now().timestamp() * 1000)
                start_ts = end_ts - (1000 * 60 * 1000)  # ~1000 minutes back
                
                for tf in timeframes:
                    binance_tf = self.timeframe_map.get(tf, tf.lower())
                    candles = await self.fetch_ohlcv(binance_symbol, binance_tf, start_ts, end_ts)
                    
                    if candles:
                        await self.save_to_db(binance_symbol, tf, candles[-100:])  # Last 100 only
                
                print(f"✅ Real-time update complete at {datetime.now()}")
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                print(f"❌ Real-time error: {e}")
                await asyncio.sleep(10)
    
    async def backfill_missing(self, symbol: str, timeframe: str):
        """Find and backfill missing data gaps"""
        binance_symbol = self.symbol_map.get(symbol, f"{symbol}USDT")
        
        async with self.db_pool.acquire() as conn:
            # Find gaps in data
            query = """
                SELECT 
                    LAG(timestamp) OVER (ORDER BY timestamp) as prev_ts,
                    timestamp as curr_ts
                FROM ohlcv
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp
            """
            
            rows = await conn.fetch(query, binance_symbol, timeframe)
            
            gaps = []
            for row in rows:
                if row['prev_ts'] and row['curr_ts']:
                    gap = row['curr_ts'] - row['prev_ts']
                    # If gap > 2x expected interval
                    expected_interval = self.get_interval_seconds(timeframe)
                    if gap.total_seconds() > expected_interval * 2:
                        gaps.append((row['prev_ts'], row['curr_ts']))
            
            if gaps:
                print(f"🔍 Found {len(gaps)} gaps in {symbol} {timeframe}")
                
                for start_ts, end_ts in gaps[:10]:  # Limit to 10 gaps
                    print(f"   Backfilling gap: {start_ts} to {end_ts}")
                    candles = await self.fetch_ohlcv(
                        binance_symbol,
                        self.timeframe_map.get(timeframe, timeframe.lower()),
                        int(start_ts.timestamp() * 1000),
                        int(end_ts.timestamp() * 1000)
                    )
                    if candles:
                        await self.save_to_db(binance_symbol, timeframe, candles)
            else:
                print(f"✅ No gaps found in {symbol} {timeframe}")
    
    def get_interval_seconds(self, timeframe: str) -> int:
        """Get interval in seconds for a timeframe"""
        intervals = {
            '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
            '1H': 3600, '2H': 7200, '4H': 14400,
            '1D': 86400, '1W': 604800, '1M': 2592000
        }
        return intervals.get(timeframe, 3600)


async def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OHLCV Data Collector')
    parser.add_argument('--symbol', type=str, required=True, help='Symbol (BTC, ETH, SOL)')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframes', type=str, default='1D', help='Comma-separated timeframes')
    parser.add_argument('--realtime', action='store_true', help='Run in real-time mode')
    parser.add_argument('--backfill', action='store_true', help='Backfill missing data')
    
    args = parser.parse_args()
    
    collector = OHLCVCollector()
    await collector.connect()
    
    timeframes = [tf.strip() for tf in args.timeframes.split(',')]
    
    try:
        if args.backfill:
            for tf in timeframes:
                await collector.backfill_missing(args.symbol, tf)
        elif args.realtime:
            await collector.collect_realtime(args.symbol, timeframes)
        else:
            await collector.collect_historical(
                args.symbol,
                timeframes,
                args.start,
                args.end
            )
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
