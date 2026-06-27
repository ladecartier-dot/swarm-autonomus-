"""
On-Chain Data Collector
Collects: Exchange flows, SOPR, MVRV, NUPL, Whale wallets, Miner data
Sources: Glassnode API, Dune Analytics, Etherscan
Time Range: 2010-2026

Usage:
    python onchain_collector.py --asset BTC --start 2010-01-01
    python onchain_collector.py --asset ETH --metrics exchange,sopr,mvrv
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import asyncpg
import os

class OnChainCollector:
    def __init__(self):
        self.glassnode_api = "https://api.glassnode.com/v1"
        self.glassnode_key = os.getenv('GLASSNODE_API_KEY', '')
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
        
        self.session = None
        self.db_pool = None
        
        # Available metrics
        self.metrics = {
            'exchange_balance': 'bal_exc_total',
            'exchange_inflow': 'flow_exc_in_total',
            'exchange_outflow': 'flow_exc_out_total',
            'sopr': 'sopr',
            'mvrv': 'mvrv_zscore',
            'nupl': 'nupl',
            'whale_count': 'bal_hodl_waves_1m_pct',
            'miner_reserve': 'bal_miner_pos',
            'hash_rate': 'mining_hashrate',
            'active_addresses': 'addr_cnt',
            'transaction_count': 'tx_cnt',
            'transaction_volume': 'tx_vol'
        }
    
    async def connect(self):
        headers = {}
        if self.glassnode_key:
            headers['X-API-KEY'] = self.glassnode_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        print("✅ On-chain collector connected")
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def fetch_metric(self, asset: str, metric: str, start_date: str, end_date: str) -> List[Dict]:
        """Fetch a single on-chain metric from Glassnode"""
        url = f"{self.glassnode_api}/metrics/indicators/{metric}"
        
        params = {
            'a': asset,
            's': int(datetime.strptime(start_date, '%Y-%m-%d').timestamp()),
            'e': int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()),
            'i': '1d',  # Daily interval
            'f': 'json'
        }
        
        all_data = []
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        for item in data:
                            if 'v' in item and item['v'] is not None:
                                all_data.append({
                                    'timestamp': datetime.fromtimestamp(item['t']),
                                    'value': float(item['v']),
                                    'metric': metric
                                })
        except Exception as e:
            print(f"❌ Error fetching {metric}: {e}")
        
        return all_data
    
    async def save_to_db(self, asset: str, data: List[Dict]):
        """Save on-chain data to PostgreSQL"""
        if not data:
            return
        
        async with self.db_pool.acquire() as conn:
            for record in data:
                query = """
                    INSERT INTO onchain_metrics 
                    (metric, asset, timestamp, value, value_usd)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (metric, asset, timestamp) DO UPDATE SET
                        value = EXCLUDED.value,
                        value_usd = EXCLUDED.value_usd
                """
                
                # Estimate USD value for some metrics
                value_usd = None
                if record['metric'] in ['exchange_balance', 'miner_reserve']:
                    # Rough estimate based on BTC price (would need actual price data)
                    value_usd = record['value'] * 60000  # Placeholder
                
                await conn.execute(query, record['metric'], asset, record['timestamp'],
                                 record['value'], value_usd)
        
        print(f"✅ Saved {len(data)} on-chain records for {asset}")
    
    async def collect_historical(self, asset: str, start_date: str, end_date: str, metrics: List[str] = None):
        """Collect on-chain metrics historically"""
        if metrics is None:
            metrics = list(self.metrics.keys())
        
        print(f"\n🚀 Collecting on-chain data for {asset}")
        print(f"   Range: {start_date} to {end_date}")
        print(f"   Metrics: {', '.join(metrics)}")
        
        all_data = []
        
        for metric in metrics:
            glassnode_metric = self.metrics.get(metric, metric)
            print(f"   📊 Fetching {metric}...")
            
            data = await self.fetch_metric(asset, glassnode_metric, start_date, end_date)
            if data:
                all_data.extend(data)
                print(f"      Got {len(data)} data points")
            else:
                print(f"      ⚠️  No data for {metric}")
        
        # Save all metrics
        await self.save_to_db(asset, all_data)
        print(f"✅ On-chain collection complete for {asset}")
    
    async def collect_realtime(self, asset: str, metrics: List[str] = None):
        """Collect real-time on-chain data"""
        if metrics is None:
            metrics = ['exchange_balance', 'sopr', 'mvrv', 'nupl']
        
        print(f"🔴 Starting real-time on-chain collection for {asset}")
        
        while True:
            try:
                # Fetch last 7 days
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                all_data = []
                for metric in metrics:
                    glassnode_metric = self.metrics.get(metric, metric)
                    data = await self.fetch_metric(asset, glassnode_metric, start_date, end_date)
                    if data:
                        all_data.extend(data)
                
                if all_data:
                    await self.save_to_db(asset, all_data)
                    print(f"✅ Real-time on-chain update: {asset} @ {datetime.now()}")
                
                await asyncio.sleep(3600)  # Update hourly
                
            except Exception as e:
                print(f"❌ Real-time on-chain error: {e}")
                await asyncio.sleep(300)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='On-Chain Data Collector')
    parser.add_argument('--asset', type=str, required=True, help='BTC, ETH, etc.')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--metrics', type=str, help='Comma-separated metrics')
    parser.add_argument('--realtime', action='store_true')
    
    args = parser.parse_args()
    
    collector = OnChainCollector()
    await collector.connect()
    
    try:
        metrics = args.metrics.split(',') if args.metrics else None
        
        if args.realtime:
            await collector.collect_realtime(args.asset, metrics)
        else:
            if not args.start:
                args.start = '2010-01-01' if args.asset == 'BTC' else '2015-08-07'
            if not args.end:
                args.end = datetime.now().strftime('%Y-%m-%d')
            
            await collector.collect_historical(args.asset, args.start, args.end, metrics)
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
