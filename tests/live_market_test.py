#!/usr/bin/env python3
"""
Live Market Test - Test swarm with volatile market conditions
Generates scenarios that should trigger trade signals
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import SwarmOrchestrator
from core.blackboard import get_blackboard


async def test_bull_market():
    """Test with strong bullish setup"""
    print("="*60)
    print("🐂 TESTING BULL MARKET SCENARIO")
    print("="*60)
    
    bb = get_blackboard()
    
    # Simulate strong uptrend with clear liquidity levels
    import random
    base = 95000
    ohlcv = []
    for i in range(100):
        # Strong uptrend
        trend = 0.005 * i  # 0.5% per candle uptrend
        open_p = base * (1 + trend + random.uniform(-0.01, 0.01))
        close_p = open_p * (1 + random.uniform(0.01, 0.03))  # Bullish candles
        high = close_p * (1 + random.uniform(0, 0.01))
        low = open_p * (1 - random.uniform(0, 0.01))
        volume = random.uniform(5000, 20000)
        
        ohlcv.append([
            int(datetime.now().timestamp()) - ((100-i) * 4 * 3600),
            open_p, high, low, close_p, volume
        ])
    
    # Cache the data
    bb.cache_market_data('BTCUSD', 'H4', 'ohlcv', ohlcv)
    bb.cache_market_data('BTCUSD', 'D1', 'price', {
        'price': ohlcv[-1][4],
        'change_24h': 5.2
    })
    
    # Run analysis
    orch = SwarmOrchestrator()
    result = await orch.run_full_analysis('BTCUSD')
    
    print(f"\n📊 RESULT:")
    print(f"  Decision: {result.get('decision')}")
    print(f"  Consensus: {result.get('consensus', {}).get('consensus')}")
    
    if result.get('decision') == 'TRADE':
        signal = result.get('signal')
        print(f"\n🎯 SIGNAL:")
        print(f"  Side: {signal.get('side')}")
        print(f"  Entry: ${signal.get('entry'):,.2f}")
        print(f"  SL: ${signal.get('stop_loss'):,.2f}")
        print(f"  TP: ${signal.get('take_profit'):,.2f}")
        print(f"  R:R: {result.get('risk_analysis', {}).get('rr_ratio', 0):.2f}:1")
    
    return result


async def test_bear_market():
    """Test with strong bearish setup"""
    print("\n" + "="*60)
    print("🐻 TESTING BEAR MARKET SCENARIO")
    print("="*60)
    
    bb = get_blackboard()
    
    # Simulate strong downtrend
    import random
    base = 98000
    ohlcv = []
    for i in range(100):
        # Strong downtrend
        trend = -0.006 * i  # -0.6% per candle
        open_p = base * (1 + trend + random.uniform(-0.01, 0.01))
        close_p = open_p * (1 - random.uniform(0.015, 0.035))  # Bearish candles
        high = open_p * (1 + random.uniform(0, 0.01))
        low = close_p * (1 - random.uniform(0, 0.01))
        volume = random.uniform(5000, 20000)
        
        ohlcv.append([
            int(datetime.now().timestamp()) - ((100-i) * 4 * 3600),
            open_p, high, low, close_p, volume
        ])
    
    bb.cache_market_data('BTCUSD', 'H4', 'ohlcv', ohlcv)
    
    orch = SwarmOrchestrator()
    result = await orch.run_full_analysis('BTCUSD')
    
    print(f"\n📊 RESULT:")
    print(f"  Decision: {result.get('decision')}")
    print(f"  Consensus: {result.get('consensus', {}).get('consensus')}")
    
    if result.get('decision') == 'TRADE':
        signal = result.get('signal')
        print(f"\n🎯 SIGNAL:")
        print(f"  Side: {signal.get('side')}")
        print(f"  Entry: ${signal.get('entry'):,.2f}")
        print(f"  SL: ${signal.get('stop_loss'):,.2f}")
        print(f"  TP: ${signal.get('take_profit'):,.2f}")
        print(f"  R:R: {result.get('risk_analysis', {}).get('rr_ratio', 0):.2f}:1")
    
    return result


async def test_ranging_market():
    """Test with sideways/choppy market"""
    print("\n" + "="*60)
    print("〰️ TESTING RANGING MARKET SCENARIO")
    print("="*60)
    
    bb = get_blackboard()
    
    # Simulate ranging market
    import random
    base = 95000
    ohlcv = []
    for i in range(100):
        # No trend, just noise
        open_p = base + random.uniform(-2000, 2000)
        close_p = open_p + random.uniform(-500, 500)
        high = max(open_p, close_p) + random.uniform(0, 300)
        low = min(open_p, close_p) - random.uniform(0, 300)
        volume = random.uniform(3000, 10000)
        
        ohlcv.append([
            int(datetime.now().timestamp()) - ((100-i) * 4 * 3600),
            open_p, high, low, close_p, volume
        ])
    
    bb.cache_market_data('BTCUSD', 'H4', 'ohlcv', ohlcv)
    
    orch = SwarmOrchestrator()
    result = await orch.run_full_analysis('BTCUSD')
    
    print(f"\n📊 RESULT:")
    print(f"  Decision: {result.get('decision')}")
    print(f"  Consensus: {result.get('consensus', {}).get('consensus')}")
    print(f"  Reason: {result.get('reason', 'N/A')}")
    
    return result


async def main():
    """Run all test scenarios"""
    print("\n🧪 SWARM TRADER - LIVE MARKET TEST SUITE")
    print("="*60)
    
    # Test all scenarios
    bull_result = await test_bull_market()
    bear_result = await test_bear_market()
    range_result = await test_ranging_market()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    print(f"\n🐂 Bull Market: {bull_result.get('decision', 'NO_TRADE')}")
    print(f"🐻 Bear Market: {bear_result.get('decision', 'NO_TRADE')}")
    print(f"〰️ Ranging Market: {range_result.get('decision', 'NO_TRADE')}")
    
    trades = sum(1 for r in [bull_result, bear_result, range_result] if r.get('decision') == 'TRADE')
    print(f"\n✅ Signals Generated: {trades}/3")
    
    if trades > 0:
        print("\n🎉 SWARM IS WORKING - Detecting trade setups!")
    else:
        print("\n⚠️ Risk management being conservative (good for live trading)")
    
    print("\n💾 Results saved to state/ directory")


if __name__ == "__main__":
    asyncio.run(main())
