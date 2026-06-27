"""
Master Data Collection Pipeline
Collects ALL 8 data types:
1. OHLCV
2. Orderbook History
3. Futures Data
4. On-Chain Metrics
5. Macro Indicators
6. Sentiment Data
7. News Headlines
8. Cycle Labels

Usage:
    python master_collector.py --backfill --symbols BTC,ETH,SOL
    python master_collector.py --realtime
    python master_collector.py --ohlcv --futures --onchain
"""

import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MasterDataCollector:
    def __init__(self):
        self.collectors = {}
        self.status = {}
        
    def register_collector(self, name: str, collector):
        """Register a data collector"""
        self.collectors[name] = collector
        self.status[name] = "ready"
        print(f"✅ Registered collector: {name}")
    
    async def run_backfill(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str = None,
        data_types: List[str] = None
    ):
        """
        Run historical backfill for all data types
        
        Args:
            symbols: List of symbols (BTC, ETH, SOL)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (default: today)
            data_types: Specific data types to collect (default: all)
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if data_types is None:
            data_types = list(self.collectors.keys())
        
        print("\n" + "="*80)
        print("🚀 STARTING MASTER BACKFILL")
        print("="*80)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Date Range: {start_date} to {end_date}")
        print(f"Data Types: {', '.join(data_types)}")
        print("="*80 + "\n")
        
        for symbol in symbols:
            print(f"\n{'='*60}")
            print(f"📊 Processing: {symbol}")
            print(f"{'='*60}\n")
            
            for data_type in data_types:
                if data_type in self.collectors:
                    print(f"\n⏳ [{data_type.upper()}] Starting collection...")
                    start_time = datetime.now()
                    
                    try:
                        collector = self.collectors[data_type]
                        await collector.collect_historical(symbol, start_date, end_date)
                        
                        elapsed = (datetime.now() - start_time).total_seconds()
                        self.status[data_type] = f"✅ Success ({elapsed}s)"
                        print(f"✅ [{data_type.upper()}] Complete in {elapsed:.1f}s")
                        
                    except Exception as e:
                        self.status[data_type] = f"❌ Error: {str(e)}"
                        print(f"❌ [{data_type.upper()}] Failed: {e}")
                    
                    # Delay between collectors
                    await asyncio.sleep(2)
        
        # Print summary
        self.print_summary()
    
    async def run_realtime(self, symbols: List[str], data_types: List[str] = None):
        """Run real-time data collection"""
        if data_types is None:
            data_types = list(self.collectors.keys())
        
        print("\n" + "="*80)
        print("🔴 STARTING REAL-TIME COLLECTION")
        print("="*80)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Data Types: {', '.join(data_types)}")
        print("="*80 + "\n")
        
        tasks = []
        
        for symbol in symbols:
            for data_type in data_types:
                if data_type in self.collectors:
                    task = asyncio.create_task(
                        self.collectors[data_type].collect_realtime(symbol)
                    )
                    tasks.append(task)
                    print(f"✅ Started real-time: {symbol} - {data_type}")
        
        # Run all collectors concurrently
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n⚠️  Stopping real-time collection...")
            for task in tasks:
                task.cancel()
    
    def print_summary(self):
        """Print collection summary"""
        print("\n" + "="*80)
        print("📊 COLLECTION SUMMARY")
        print("="*80)
        
        for collector_name, status in self.status.items():
            icon = "✅" if "Success" in status else "❌" if "Error" in status else "⏳"
            print(f"{icon} {collector_name}: {status}")
        
        print("="*80)


async def main():
    parser = argparse.ArgumentParser(description='Master Data Collection Pipeline')
    parser.add_argument('--backfill', action='store_true', help='Run historical backfill')
    parser.add_argument('--realtime', action='store_true', help='Run real-time collection')
    parser.add_argument('--symbols', type=str, default='BTC,ETH,SOL', help='Comma-separated symbols')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--types', type=str, help='Comma-separated data types (default: all)')
    parser.add_argument('--ohlcv', action='store_true', help='Collect OHLCV only')
    parser.add_argument('--futures', action='store_true', help='Collect Futures only')
    parser.add_argument('--onchain', action='store_true', help='Collect On-Chain only')
    parser.add_argument('--macro', action='store_true', help='Collect Macro only')
    
    args = parser.parse_args()
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    # Parse data types
    data_types = None
    if args.types:
        data_types = [t.strip() for t in args.types.split(',')]
    elif args.ohlcv:
        data_types = ['ohlcv']
    elif args.futures:
        data_types = ['futures']
    elif args.onchain:
        data_types = ['onchain']
    elif args.macro:
        data_types = ['macro']
    
    # Initialize master collector
    master = MasterDataCollector()
    
    # TODO: Initialize individual collectors here
    # For now, we'll create placeholder collectors
    
    print("⚠️  WARNING: Individual collectors not yet implemented")
    print("   Run individual collectors manually:")
    print("   - python data/collectors/ohlcv_collector.py --symbol BTC --start 2010-01-01")
    print("   - python data/collectors/futures_collector.py --symbol BTC")
    print("   - etc.")
    
    if args.backfill:
        if not args.start:
            print("❌ Error: --start date required for backfill")
            sys.exit(1)
        
        await master.run_backfill(
            symbols=symbols,
            start_date=args.start,
            end_date=args.end,
            data_types=data_types
        )
    
    elif args.realtime:
        await master.run_realtime(
            symbols=symbols,
            data_types=data_types
        )
    
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
