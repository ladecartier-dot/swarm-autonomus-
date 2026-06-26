"""
Swarm Orchestrator - Coordinates all agents, runs consensus, executes decisions
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from core.blackboard import get_blackboard
from core.message_bus import get_message_bus, TOPICS
from agents.base_agents import (
    LiquidityAgent, MarketStructureAgent, RiskAgent, 
    MacroAgent, ConsensusAgent, BaseAgent
)


class SwarmOrchestrator:
    """
    Main orchestrator for the trading swarm.
    
    Responsibilities:
    - Initialize and manage all agents
    - Fetch market data
    - Coordinate analysis pipeline
    - Run consensus mechanism
    - Execute trades (when integrated with broker)
    - Monitor agent health
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.blackboard = get_blackboard()
        self.message_bus = get_message_bus()
        
        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {
            'liquidity': LiquidityAgent(),
            'structure': MarketStructureAgent(),
            'risk': RiskAgent(),
            'macro': MacroAgent(),
            'consensus': ConsensusAgent(),
        }
        
        self.running = False
        self.analysis_results = {}
        
        print(f"🧠 Swarm Orchestrator initialized with {len(self.agents)} agents")
    
    def _default_config(self) -> Dict:
        return {
            'symbols': ['BTCUSD', 'ETHUSD', 'SOLUSD'],
            'timeframes': ['D1', 'H4', 'H1'],
            'account_size': 100000,
            'max_risk_per_trade': 0.01,
            'min_rr_ratio': 2.0,
            'consensus_threshold': 0.4,
            'data_source': 'coingecko',  # or 'binance', 'custom'
        }
    
    async def start(self):
        """Start the orchestrator and all agents"""
        self.running = True
        
        # Start message bus
        asyncio.create_task(self.message_bus.start())
        
        # Start all agents
        for agent in self.agents.values():
            agent.start()
        
        print("✅ Swarm Orchestrator started")
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the orchestrator and all agents"""
        self.running = False
        
        for agent in self.agents.values():
            agent.stop()
        
        self.message_bus.stop()
        
        print("🛑 Swarm Orchestrator stopped")
    
    async def run_full_analysis(self, symbol: str = 'BTCUSD') -> Dict[str, Any]:
        """
        Run complete analysis pipeline for a symbol.
        
        Pipeline:
        1. Fetch market data
        2. Run all analysis agents in parallel
        3. Aggregate results
        4. Run consensus
        5. Risk check
        6. Return decision
        """
        print(f"\n🔍 Starting analysis for {symbol}...")
        
        # Step 1: Fetch market data (mock for now)
        ohlcv = await self._fetch_ohlcv(symbol)
        
        if not ohlcv:
            return {'error': 'Failed to fetch market data'}
        
        # Step 2: Run analysis agents in parallel
        analysis_tasks = []
        
        # Liquidity analysis
        analysis_tasks.append(self.agents['liquidity'].run({
            'symbol': symbol,
            'timeframe': 'H4',
            'ohlcv': ohlcv
        }))
        
        # Market structure
        analysis_tasks.append(self.agents['structure'].run({
            'symbol': symbol,
            'ohlcv': ohlcv
        }))
        
        # Macro
        analysis_tasks.append(self.agents['macro'].run({
            'symbol': symbol
        }))
        
        # Run in parallel
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Process results
        agent_outputs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Agent {i} failed: {result}")
                continue
            agent_outputs.append(result)
            print(f"✅ Agent {i} completed: confidence={result.get('confidence', 0):.2f}")
        
        # Step 3: Run consensus
        consensus_result = await self.agents['consensus'].run({
            'agent_outputs': agent_outputs
        })
        
        # Step 4: Risk check (if consensus says trade)
        final_decision = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'analysis': agent_outputs,
            'consensus': consensus_result,
            'decision': 'NO_TRADE',
            'reason': '',
        }
        
        if consensus_result.get('recommendation') == 'TRADE':
            # Generate a signal for risk check
            signal = self._generate_signal(symbol, agent_outputs, consensus_result)
            
            risk_result = await self.agents['risk'].run({
                'account_size': self.config['account_size'],
                'signal': signal
            })
            
            final_decision['risk_analysis'] = risk_result
            
            if risk_result.get('acceptable', False):
                final_decision['decision'] = 'TRADE'
                final_decision['signal'] = signal
                final_decision['reason'] = f"Consensus: {consensus_result.get('consensus')}, R:R: {risk_result.get('rr_ratio', 0):.2f}"
            else:
                final_decision['reason'] = f"Risk not acceptable: R:R {risk_result.get('rr_ratio', 0):.2f} < {self.config['min_rr_ratio']}"
        
        # Store in blackboard
        self.blackboard.set_state(f'latest_analysis_{symbol}', final_decision)
        self.blackboard.update_state_file('Analysis Complete', json.dumps(final_decision, indent=2))
        
        return final_decision
    
    async def _fetch_ohlcv(self, symbol: str, limit: int = 100) -> List[List]:
        """
        Fetch OHLCV data.
        
        In production, this would call:
        - CoinGecko API
        - Binance API
        - Or your existing data pipeline
        """
        # Check cache first
        cached = self.blackboard.get_cached_market_data(symbol, 'H4', 'ohlcv', max_age_minutes=15)
        if cached:
            print(f"📦 Using cached data for {symbol}")
            return cached
        
        # Mock data for now (replace with real API call)
        import random
        base_price = 95000 if 'BTC' in symbol else (3500 if 'ETH' in symbol else 200)
        
        ohlcv = []
        for i in range(limit):
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            high = open_price * (1 + random.uniform(0, 0.03))
            low = open_price * (1 - random.uniform(0, 0.03))
            close = random.uniform(low, high)
            volume = random.uniform(1000, 10000)
            
            ohlcv.append([
                int(datetime.now().timestamp()) - (i * 4 * 3600),  # Timestamp
                open_price,
                high,
                low,
                close,
                volume
            ])
        
        # Cache the data
        self.blackboard.cache_market_data(symbol, 'H4', 'ohlcv', ohlcv)
        
        return ohlcv
    
    def _generate_signal(self, symbol: str, agent_outputs: List[Dict], consensus: Dict) -> Dict:
        """Generate a trade signal from analysis"""
        # Get current price from liquidity agent
        liquidity = next((o for o in agent_outputs if o.get('current_price')), {})
        current_price = liquidity.get('current_price', 95000)
        
        bias = consensus.get('consensus', 'neutral')
        
        if bias == 'bullish':
            side = 'LONG'
            stop_loss = current_price * 0.97  # 3% SL
            take_profit = current_price * 1.09  # 9% TP (3:1 R:R)
        elif bias == 'bearish':
            side = 'SHORT'
            stop_loss = current_price * 1.03  # 3% SL
            take_profit = current_price * 0.91  # 9% TP
        else:
            side = 'NEUTRAL'
            stop_loss = current_price
            take_profit = current_price
        
        return {
            'symbol': symbol,
            'side': side,
            'entry': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timeframe': 'H4',
            'setup_type': 'swarm_consensus',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            'orchestrator_running': self.running,
            'agents': {
                name: agent.get_stats()
                for name, agent in self.agents.items()
            },
            'message_bus_topics': self.message_bus.get_topics(),
            'latest_analysis': self.blackboard.get_state('latest_analysis_BTCUSD')
        }


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Swarm Trader Orchestrator')
    parser.add_argument('--run', action='store_true', help='Run single analysis')
    parser.add_argument('--symbol', default='BTCUSD', help='Symbol to analyze')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--status', action='store_true', help='Show status')
    
    args = parser.parse_args()
    
    orchestrator = SwarmOrchestrator()
    
    if args.status:
        status = orchestrator.get_swarm_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.run:
        result = await orchestrator.run_full_analysis(args.symbol)
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULT")
        print("="*60)
        print(json.dumps(result, indent=2))
        return
    
    if args.daemon:
        await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
