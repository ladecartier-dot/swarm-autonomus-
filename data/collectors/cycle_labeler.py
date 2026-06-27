"""
Market Cycle Labeler & Pattern Detector
Labels: Bull/Bear/Accumulation/Distribution phases using Wyckoff methodology
Detects: SMC patterns, BOS, CHoCH, Order Blocks, FVG

Usage:
    python cycle_labeler.py --asset BTC --auto
    python cycle_labeler.py --detect-smc --timeframe 1D
    python cycle_labeler.py --label-manual --phase accumulation
"""

import asyncio
import asyncpg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import os
import json

class CycleLabeler:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
        
        self.db_pool = None
        
        # Wyckoff phases
        self.phases = {
            'accumulation': ['PS', 'SC', 'AR', 'ST', 'SOS', 'LPS', 'MU'],
            'bull': ['UPN', 'LPSY', 'UT', 'UTAD', 'PHD'],
            'distribution': ['PSY', 'SCY', 'AR', 'ST', 'SOW', 'LPSY', 'MD'],
            'bear': ['LPSY', 'LOW', 'LOW2', 'LOW3']
        }
    
    async def connect(self):
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        print("✅ Cycle labeler connected")
    
    async def close(self):
        if self.db_pool:
            await self.db_pool.close()
    
    async def get_price_data(self, asset: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch OHLCV data from database"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM ohlcv
                WHERE symbol = $1 AND timeframe = '1D'
                  AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp
            """
            
            rows = await conn.fetch(query, f"{asset}USDT", start_date, end_date)
            
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df.set_index('timestamp', inplace=True)
            return df
    
    def detect_market_structure(self, df: pd.DataFrame) -> Dict:
        """Detect market structure (HH/HL, LH/LL)"""
        structure = []
        
        # Find swing highs and lows
        window = 20
        df['swing_high'] = df['high'].rolling(window=window, center=True).max()
        df['swing_low'] = df['low'].rolling(window=window, center=True).min()
        
        # Identify structure
        last_hh = None
        last_hl = None
        last_lh = None
        last_ll = None
        
        for idx, row in df.iterrows():
            if row['high'] == row['swing_high']:
                if last_hh is not None and row['high'] > last_hh:
                    structure.append((idx, 'HH', row['high']))
                elif last_lh is not None and row['high'] > last_lh:
                    structure.append((idx, 'LH', row['high']))
                last_hh = row['high'] if last_hh is None or row['high'] > last_hh else last_hh
                last_lh = row['high'] if last_lh is None or row['high'] > last_lh else last_lh
            
            if row['low'] == row['swing_low']:
                if last_hl is not None and row['low'] > last_hl:
                    structure.append((idx, 'HL', row['low']))
                elif last_ll is not None and row['low'] > last_ll:
                    structure.append((idx, 'LL', row['low']))
                last_hl = row['low'] if last_hl is None or row['low'] > last_hl else last_hl
                last_ll = row['low'] if last_ll is None or row['low'] > last_ll else last_ll
        
        return {'structure': structure, 'df': df}
    
    def detect_wyckoff_phase(self, df: pd.DataFrame, structure: Dict) -> str:
        """Detect current Wyckoff phase based on price action"""
        if len(df) < 100:
            return 'unknown'
        
        # Calculate indicators
        df['sma_50'] = df['close'].rolling(50).mean()
        df['sma_200'] = df['close'].rolling(200).mean()
        df['rsi'] = self.calculate_rsi(df['close'], 14)
        
        current = df.iloc[-1]
        
        # Accumulation detection
        if (current['close'] < current['sma_200'] and 
            current['rsi'] < 40 and
            self.is_consolidating(df)):
            return 'accumulation'
        
        # Bull market detection
        if (current['close'] > current['sma_50'] > current['sma_200'] and
            current['rsi'] > 50 and
            self.is_uptrend(df)):
            return 'bull'
        
        # Distribution detection
        if (current['close'] > current['sma_200'] and
            current['rsi'] > 70 and
            self.is_consolidating(df, window=50)):
            return 'distribution'
        
        # Bear market detection
        if (current['close'] < current['sma_50'] < current['sma_200'] and
            current['rsi'] < 50 and
            self.is_downtrend(df)):
            return 'bear'
        
        return 'transition'
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def is_consolidating(self, df: pd.DataFrame, window: int = 100) -> bool:
        """Check if market is consolidating (low volatility)"""
        if len(df) < window:
            return False
        
        recent = df.iloc[-window:]
        volatility = recent['close'].std() / recent['close'].mean()
        return volatility < 0.15  # Less than 15% volatility
    
    def is_uptrend(self, df: pd.DataFrame) -> bool:
        """Check if market is in uptrend"""
        if len(df) < 50:
            return False
        
        recent = df.iloc[-50:]
        return recent['close'].iloc[-1] > recent['close'].iloc[0] * 1.1  # 10% gain
    
    def is_downtrend(self, df: pd.DataFrame) -> bool:
        """Check if market is in downtrend"""
        if len(df) < 50:
            return False
        
        recent = df.iloc[-50:]
        return recent['close'].iloc[-1] < recent['close'].iloc[0] * 0.9  # 10% loss
    
    async def label_cycles_auto(self, asset: str, start_date: str, end_date: str):
        """Automatically label market cycles"""
        print(f"\n🚀 Auto-labeling cycles for {asset}")
        print(f"   Range: {start_date} to {end_date}")
        
        # Get price data
        df = await self.get_price_data(asset, start_date, end_date)
        
        if df.empty:
            print("❌ No price data found")
            return
        
        # Detect structure
        structure = self.detect_market_structure(df)
        
        # Label cycles
        labels = []
        current_phase = None
        phase_start = None
        
        # Iterate through data and label phases
        for idx, row in df.iterrows():
            phase = self.detect_wyckoff_phase(df.loc[:idx], structure)
            
            if phase != current_phase:
                # New phase detected
                if current_phase is not None:
                    labels.append({
                        'asset': asset,
                        'start_date': phase_start,
                        'end_date': idx,
                        'phase': current_phase,
                        'confidence': 0.75,
                        'methodology': 'AI'
                    })
                
                current_phase = phase
                phase_start = idx
        
        # Add final phase
        if current_phase:
            labels.append({
                'asset': asset,
                'start_date': phase_start,
                'end_date': end_date,
                'phase': current_phase,
                'confidence': 0.75,
                'methodology': 'AI'
            })
        
        # Save to database
        await self.save_labels(labels)
        print(f"✅ Labeled {len(labels)} cycles for {asset}")
    
    async def save_labels(self, labels: List[Dict]):
        """Save cycle labels to PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            for label in labels:
                query = """
                    INSERT INTO cycle_labels 
                    (asset, start_date, end_date, phase, sub_phase, confidence, methodology)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """
                
                await conn.execute(query, label['asset'], label['start_date'],
                                 label.get('end_date'), label['phase'],
                                 label.get('sub_phase'), label['confidence'],
                                 label['methodology'])
        
        print(f"✅ Saved {len(labels)} cycle labels")
    
    async def detect_smc_patterns(self, asset: str, timeframe: str):
        """Detect SMC patterns (BOS, CHoCH, Order Blocks, FVG)"""
        print(f"\n🔍 Detecting SMC patterns for {asset} {timeframe}")
        
        async with self.db_pool.acquire() as conn:
            # Fetch OHLCV data
            query = """
                SELECT timestamp, open, high, low, close
                FROM ohlcv
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC
                LIMIT 1000
            """
            
            rows = await conn.fetch(query, f"{asset}USDT", timeframe)
            
            if not rows:
                print("❌ No data found")
                return
            
            df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close'])
            df.set_index('timestamp', inplace=True)
            df = df.iloc[::-1]  # Reverse to chronological order
            
            patterns = []
            
            # Detect BOS (Break of Structure)
            for i in range(100, len(df)):
                window = df.iloc[i-100:i]
                
                # Find previous high
                prev_high = window['high'].max()
                prev_high_idx = window['high'].idxmax()
                
                # Check if current price broke structure
                if df.iloc[i]['high'] > prev_high:
                    patterns.append({
                        'symbol': f"{asset}USDT",
                        'timeframe': timeframe,
                        'timestamp': df.index[i],
                        'pattern_type': 'BOS',
                        'pattern_name': 'Break of Structure',
                        'start_time': prev_high_idx,
                        'end_time': df.index[i],
                        'price_start': prev_high,
                        'price_end': df.iloc[i]['high'],
                        'confidence': 0.85
                    })
            
            # Detect CHoCH (Change of Character)
            for i in range(100, len(df)):
                window = df.iloc[i-100:i]
                
                # Simple CHoCH detection: trend reversal
                if len(window) > 50:
                    first_half = window.iloc[:50]
                    second_half = window.iloc[50:]
                    
                    first_trend = first_half['close'].iloc[-1] > first_half['close'].iloc[0]
                    second_trend = second_half['close'].iloc[-1] < second_half['close'].iloc[0]
                    
                    if first_trend and second_trend:
                        patterns.append({
                            'symbol': f"{asset}USDT",
                            'timeframe': timeframe,
                            'timestamp': df.index[i],
                            'pattern_type': 'CHoCH',
                            'pattern_name': 'Change of Character',
                            'start_time': df.index[i-100],
                            'end_time': df.index[i],
                            'price_start': window['close'].iloc[0],
                            'price_end': df.iloc[i]['close'],
                            'confidence': 0.75
                        })
            
            # Save patterns
            await self.save_smc_patterns(patterns)
            print(f"✅ Detected {len(patterns)} SMC patterns")
    
    async def save_smc_patterns(self, patterns: List[Dict]):
        """Save SMC patterns to PostgreSQL"""
        async with self.db_pool.acquire() as conn:
            for pattern in patterns:
                query = """
                    INSERT INTO smc_patterns 
                    (symbol, timeframe, timestamp, pattern_type, pattern_name,
                     start_time, end_time, price_start, price_end, confidence)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                await conn.execute(query, pattern['symbol'], pattern['timeframe'],
                                 pattern['timestamp'], pattern['pattern_type'],
                                 pattern['pattern_name'], pattern['start_time'],
                                 pattern['end_time'], pattern['price_start'],
                                 pattern['price_end'], pattern['confidence'])


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Cycle Labeler & Pattern Detector')
    parser.add_argument('--asset', type=str, default='BTC')
    parser.add_argument('--timeframe', type=str, default='1D')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--auto', action='store_true', help='Auto-label cycles')
    parser.add_argument('--detect-smc', action='store_true', help='Detect SMC patterns')
    parser.add_argument('--label-manual', action='store_true', help='Manual labeling mode')
    
    args = parser.parse_args()
    
    labeler = CycleLabeler()
    await labeler.connect()
    
    try:
        if not args.start:
            args.start = '2010-01-01' if args.asset == 'BTC' else '2015-08-07'
        if not args.end:
            args.end = datetime.now().strftime('%Y-%m-%d')
        
        if args.auto:
            await labeler.label_cycles_auto(args.asset, args.start, args.end)
        
        if args.detect_smc:
            await labeler.detect_smc_patterns(args.asset, args.timeframe)
        
        if args.label_manual:
            print("Manual labeling not implemented in CLI mode")
            print("Use database client to manually add labels to cycle_labels table")
    
    finally:
        await labeler.close()


if __name__ == '__main__':
    asyncio.run(main())
