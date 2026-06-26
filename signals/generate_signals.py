#!/usr/bin/env python3
"""
Signal Generator - Cron-ready script for scheduled signal generation
Runs the full swarm analysis pipeline and outputs signals
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import SwarmOrchestrator
from data.fetcher import DataFetcher


async def generate_signals():
    """
    Generate trading signals for all configured symbols.
    
    Output:
    - Prints signals to stdout (for cron email/capture)
    - Saves to state/ directory
    - Updates blackboard
    """
    print("="*60)
    print(f"🐝 SWARM TRADER - Signal Generation")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    orchestrator = SwarmOrchestrator()
    fetcher = DataFetcher()
    
    # Symbols to analyze
    symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD']
    
    signals = []
    
    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol}...")
        
        # Fetch fresh data
        market_data = await fetcher.fetch_all_for_analysis(symbol)
        
        if not market_data.get('price'):
            print(f"  ⚠️ No price data for {symbol}, skipping...")
            continue
        
        current_price = market_data['price'].get('price', 0)
        print(f"  💰 Current price: ${current_price:,.2f}")
        
        # Run swarm analysis
        result = await orchestrator.run_full_analysis(symbol)
        
        # Extract decision
        decision = result.get('decision', 'NO_TRADE')
        consensus = result.get('consensus', {})
        
        print(f"  📊 Consensus: {consensus.get('consensus', 'N/A')}")
        print(f"  ✅ Decision: {decision}")
        
        if decision == 'TRADE':
            signal = result.get('signal', {})
            risk = result.get('risk_analysis', {})
            
            signal_summary = {
                'symbol': symbol,
                'action': signal.get('side'),
                'entry': signal.get('entry'),
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'rr_ratio': risk.get('rr_ratio'),
                'position_size': risk.get('position_size'),
                'confidence': consensus.get('confidence'),
                'timestamp': datetime.now().isoformat()
            }
            
            signals.append(signal_summary)
            
            print(f"  🎯 Entry: ${signal.get('entry'):,.2f}")
            print(f"  🛑 SL: ${signal.get('stop_loss'):,.2f}")
            print(f"  🎯 TP: ${signal.get('take_profit'):,.2f}")
            print(f"  📈 R:R: {risk.get('rr_ratio', 0):.2f}:1")
        
        # Small delay between symbols
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("📋 SIGNAL SUMMARY")
    print("="*60)
    
    if signals:
        for sig in signals:
            print(f"\n{sig['symbol']}: {sig['action']} @ ${sig['entry']:,.2f}")
            print(f"  SL: ${sig['stop_loss']:,.2f} | TP: ${sig['take_profit']:,.2f} | R:R: {sig['rr_ratio']:.2f}:1")
    else:
        print("\n⚠️ No trade signals generated - waiting for better setups")
    
    # Save to file
    output_file = Path(__file__).parent.parent / "state" / "signals.json"
    output_file.parent.mkdir(exist_ok=True)
    
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'symbols_analyzed': symbols,
        'signals': signals,
        'market_snapshot': {
            sym: await fetcher.get_price(sym) for sym in symbols
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Signals saved to: {output_file}")
    
    await fetcher.close()
    
    return signals


async def run_single_analysis(symbol: str):
    """Run analysis for a single symbol"""
    orchestrator = SwarmOrchestrator()
    fetcher = DataFetcher()
    
    print(f"🔍 Deep analysis: {symbol}")
    print("="*60)
    
    market_data = await fetcher.fetch_all_for_analysis(symbol)
    result = await orchestrator.run_full_analysis(symbol)
    
    print(json.dumps(result, indent=2))
    
    await fetcher.close()
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Swarm Trader Signal Generator')
    parser.add_argument('--symbol', type=str, help='Analyze single symbol')
    parser.add_argument('--all', action='store_true', help='Analyze all symbols')
    
    args = parser.parse_args()
    
    if args.symbol:
        asyncio.run(run_single_analysis(args.symbol))
    else:
        asyncio.run(generate_signals())
