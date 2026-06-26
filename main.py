#!/usr/bin/env python3
"""
Swarm Trader - Main Entry Point
Run the complete autonomous trading swarm
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import SwarmOrchestrator
from data.fetcher import DataFetcher
from utils.telegram_alerts import get_telegram_alerter
from core.blackboard import get_blackboard


async def run_daemon():
    """Run swarm in daemon mode (continuous operation)"""
    print("="*60)
    print("🐝 SWARM TRADER - Daemon Mode")
    print("="*60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    orchestrator = SwarmOrchestrator()
    fetcher = DataFetcher()
    alerter = get_telegram_alerter()
    
    if alerter:
        await alerter.send_message("🟢 <b>Swarm Trader Started</b>\n\nDaemon mode activated")
    
    # Start the orchestrator
    await orchestrator.start()


async def run_single_cycle(symbols: list):
    """Run one analysis cycle for all symbols"""
    print("="*60)
    print("🐝 SWARM TRADER - Analysis Cycle")
    print("="*60)
    
    orchestrator = SwarmOrchestrator()
    fetcher = DataFetcher()
    alerter = get_telegram_alerter()
    
    signals = []
    
    for symbol in symbols:
        print(f"\n🔍 Analyzing {symbol}...")
        
        # Fetch data
        market_data = await fetcher.fetch_all_for_analysis(symbol)
        
        # Run analysis
        result = await orchestrator.run_full_analysis(symbol)
        
        # Send alerts if signals generated
        if result.get('decision') == 'TRADE':
            signal = result.get('signal')
            signals.append(signal)
            
            if alerter:
                await alerter.send_signal(signal)
        else:
            print(f"  ⚪ No trade signal for {symbol}")
    
    # Send summary
    if alerter:
        if signals:
            await alerter.send_message(f"✅ <b>{len(signals)} signals generated</b>")
        else:
            await alerter.send_message("⚪ <b>No trades</b>\n\nWaiting for better setups")
    
    await fetcher.close()
    return signals


async def main():
    parser = argparse.ArgumentParser(description='Swarm Trader - Autonomous Trading System')
    
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode (continuous)')
    parser.add_argument('--run', action='store_true', help='Run single analysis cycle')
    parser.add_argument('--symbols', nargs='+', default=['BTCUSD', 'ETHUSD', 'SOLUSD'], help='Symbols to analyze')
    parser.add_argument('--backtest', action='store_true', help='Run backtest')
    parser.add_argument('--web', action='store_true', help='Start web server')
    parser.add_argument('--status', action='store_true', help='Show status')
    
    args = parser.parse_args()
    
    if args.daemon:
        await run_daemon()
    elif args.run:
        await run_single_cycle(args.symbols)
    elif args.backtest:
        from core.backtester import run_backtest_demo
        await run_backtest_demo()
    elif args.web:
        # Start web server
        import subprocess
        web_path = Path(__file__).parent / "web" / "server.py"
        subprocess.run([sys.executable, str(web_path)])
    elif args.status:
        orch = SwarmOrchestrator()
        status = orch.get_swarm_status()
        import json
        print(json.dumps(status, indent=2))
    else:
        # Default: run single cycle
        await run_single_cycle(args.symbols)


if __name__ == "__main__":
    asyncio.run(main())
