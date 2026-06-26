"""
Base Agent Class - All swarm agents inherit from this
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path

from core.blackboard import get_blackboard, Blackboard
from core.message_bus import get_message_bus, MessageBus, Message, TOPICS


class BaseAgent(ABC):
    """
    Base class for all swarm agents.
    
    Each agent has:
    - Local reasoning (via LLM calls)
    - Access to shared blackboard memory
    - Pub/sub communication via message bus
    - Performance tracking
    - Error recovery
    """
    
    def __init__(self, name: str, topics_subscribe: Optional[List[str]] = None):
        self.name = name
        self.blackboard: Blackboard = get_blackboard()
        self.message_bus: MessageBus = get_message_bus()
        self.topics_subscribe = topics_subscribe or []
        self.running = False
        self.stats = {
            'calls': 0,
            'successful': 0,
            'failed': 0,
            'last_active': None
        }
        
        # Subscribe to topics
        for topic in self.topics_subscribe:
            self.message_bus.subscribe(topic, self._on_message)
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing logic - must be implemented by each agent.
        Returns a dict with results and optional confidence score.
        """
        pass
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """Return the agent type/category"""
        pass
    
    async def _on_message(self, msg: Message):
        """Handle incoming messages from the bus"""
        if not self.running:
            return
        
        try:
            result = await self.process(msg.payload)
            
            if result:
                # Publish result back to bus
                await self.message_bus.publish(
                    f"agent.{self.name.lower()}.result",
                    self.name,
                    result,
                    priority=result.get('priority', 0)
                )
                
                # Also publish to blackboard
                self.blackboard.publish(
                    self.name,
                    self.get_agent_type(),
                    result,
                    confidence=result.get('confidence', 0.5)
                )
                
                self.stats['successful'] += 1
        except Exception as e:
            print(f"❌ {self.name} error processing message: {e}")
            self.stats['failed'] += 1
    
    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with input data"""
        self.stats['calls'] += 1
        self.stats['last_active'] = datetime.now().isoformat()
        
        try:
            result = await self.process(data)
            
            # Store in blackboard
            if result:
                self.blackboard.publish(
                    self.name,
                    self.get_agent_type(),
                    result,
                    confidence=result.get('confidence', 0.5)
                )
            
            self.stats['successful'] += 1
            return result
            
        except Exception as e:
            print(f"❌ {self.name} failed: {e}")
            self.stats['failed'] += 1
            return {
                'error': str(e),
                'agent': self.name,
                'confidence': 0.0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance stats"""
        total = self.stats['calls']
        success_rate = (self.stats['successful'] / total * 100) if total > 0 else 0
        
        return {
            'name': self.name,
            'type': self.get_agent_type(),
            'total_calls': total,
            'successful': self.stats['successful'],
            'failed': self.stats['failed'],
            'success_rate': success_rate,
            'last_active': self.stats['last_active']
        }
    
    def start(self):
        """Mark agent as running"""
        self.running = True
        print(f"🟢 {self.name} started")
    
    def stop(self):
        """Mark agent as stopped"""
        self.running = False
        print(f"🔴 {self.name} stopped")


# ============================================================================
# SPECIALIZED AGENT IMPLEMENTATIONS
# ============================================================================

class LiquidityAgent(BaseAgent):
    """Analyzes liquidity zones, order blocks, and smart money levels"""
    
    def __init__(self):
        super().__init__(
            "LiquidityAgent",
            topics_subscribe=[TOPICS['MARKET_DATA'], TOPICS['OHLCV_READY']]
        )
    
    def get_agent_type(self) -> str:
        return "liquidity_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze liquidity zones"""
        symbol = data.get('symbol', 'BTCUSD')
        timeframe = data.get('timeframe', 'H4')
        ohlcv = data.get('ohlcv', [])
        
        if not ohlcv:
            return {'error': 'No OHLCV data provided', 'confidence': 0.0}
        
        # Simple liquidity analysis (expand with real logic)
        highs = [candle[2] for candle in ohlcv[-50:]]  # High prices
        lows = [candle[3] for candle in ohlcv[-50:]]   # Low prices
        
        # Find recent swing highs/lows (simplified)
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        
        # Liquidity pools above/below
        liquidity_above = recent_high * 1.02  # 2% above
        liquidity_below = recent_low * 0.98   # 2% below
        
        current_price = ohlcv[-1][4]  # Close price
        
        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'current_price': current_price,
            'liquidity_pools': {
                'above': {
                    'level': liquidity_above,
                    'distance_pct': ((liquidity_above - current_price) / current_price) * 100
                },
                'below': {
                    'level': liquidity_below,
                    'distance_pct': ((current_price - liquidity_below) / current_price) * 100
                }
            },
            'recent_range': {
                'high': recent_high,
                'low': recent_low
            },
            'bias': 'bullish' if current_price > (recent_high + recent_low) / 2 else 'bearish',
            'confidence': 0.65
        }
        
        return analysis


class MarketStructureAgent(BaseAgent):
    """Analyzes market structure: BOS, CHoCH, trends"""
    
    def __init__(self):
        super().__init__(
            "MarketStructureAgent",
            topics_subscribe=[TOPICS['MARKET_DATA'], TOPICS['LIQUIDITY_ANALYSIS']]
        )
    
    def get_agent_type(self) -> str:
        return "market_structure"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market structure"""
        symbol = data.get('symbol', 'BTCUSD')
        ohlcv = data.get('ohlcv', [])
        
        if len(ohlcv) < 20:
            return {'error': 'Insufficient data for structure analysis', 'confidence': 0.0}
        
        # Detect BOS (Break of Structure) and CHoCH (Change of Character)
        # Simplified logic - expand with real SMC detection
        
        closes = [candle[4] for candle in ohlcv]
        
        # Simple trend detection
        short_term = closes[-5:]
        medium_term = closes[-20:]
        
        uptrend_short = all(short_term[i] <= short_term[i+1] for i in range(len(short_term)-1))
        downtrend_short = all(short_term[i] >= short_term[i+1] for i in range(len(short_term)-1))
        
        structure = {
            'symbol': symbol,
            'short_term_trend': 'bullish' if uptrend_short else ('bearish' if downtrend_short else 'ranging'),
            'medium_term_trend': 'bullish' if closes[-1] > closes[-20] else 'bearish',
            'last_bos': None,  # Would be calculated from swing points
            'last_choch': None,
            'structure_status': 'continuation' if uptrend_short or downtrend_short else 'consolidation',
            'confidence': 0.60
        }
        
        return structure


class RiskAgent(BaseAgent):
    """Risk management: position sizing, R:R, drawdown monitoring"""
    
    def __init__(self):
        super().__init__(
            "RiskAgent",
            topics_subscribe=[TOPICS['SIGNAL_GENERATED'], TOPICS['POSITION_OPENED']]
        )
    
    def get_agent_type(self) -> str:
        return "risk_management"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk metrics"""
        account_size = data.get('account_size', 100000)
        signal = data.get('signal', {})
        
        entry = signal.get('entry', 0)
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)
        
        if not all([entry, stop_loss, take_profit]):
            return {'error': 'Missing entry/SL/TP', 'confidence': 0.0}
        
        # Risk calculation
        risk_per_trade_pct = 0.01  # 1% risk
        risk_amount = account_size * risk_per_trade_pct
        
        if signal.get('side') == 'LONG':
            risk_distance = entry - stop_loss
        else:
            risk_distance = stop_loss - entry
        
        position_size = risk_amount / risk_distance if risk_distance > 0 else 0
        
        reward_distance = abs(take_profit - entry)
        rr_ratio = reward_distance / risk_distance if risk_distance > 0 else 0
        
        risk_analysis = {
            'account_size': account_size,
            'risk_per_trade_pct': risk_per_trade_pct * 100,
            'risk_amount': risk_amount,
            'position_size': position_size,
            'risk_distance': risk_distance,
            'reward_distance': reward_distance,
            'rr_ratio': rr_ratio,
            'acceptable': rr_ratio >= 2.0,  # Minimum 2:1 R:R
            'confidence': 0.90
        }
        
        return risk_analysis


class MacroAgent(BaseAgent):
    """Macro economic analysis: DXY, yields, liquidity conditions, FRED data"""
    
    def __init__(self):
        super().__init__(
            "MacroAgent",
            topics_subscribe=[TOPICS['MARKET_DATA']]
        )
    
    def get_agent_type(self) -> str:
        return "macro_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze macro conditions using FRED + Alpha Vantage data"""
        from data.fetcher import DataFetcher
        
        fetcher = DataFetcher()
        
        # Fetch real macro data from FRED
        macro_data = await fetcher.get_macro_indicators()
        
        # Fetch market sentiment from Alpha Vantage
        sentiment_data = await fetcher.get_market_sentiment()
        
        # Extract key metrics
        fed_funds = macro_data.get('FEDFUNDS', {})
        dgs10 = macro_data.get('DGS10', {})
        dgs2 = macro_data.get('DGS2', {})
        t10y2y = macro_data.get('T10Y2Y', {})
        cpi = macro_data.get('CPIAUCSL', {})
        pcepi = macro_data.get('PCEPI', {})
        unrate = macro_data.get('UNRATE', {})
        m2sl = macro_data.get('M2SL', {})
        
        # Market sentiment
        dxy_data = sentiment_data.get('DXY', {})
        spy_data = sentiment_data.get('SPY', {})
        gld_data = sentiment_data.get('GLD', {})
        qqq_data = sentiment_data.get('QQQ', {})
        
        # Calculate macro stance
        fed_rate = fed_funds.get('value', 5.33) if fed_funds else 5.33
        yield_10y = dgs10.get('value', 4.2) if dgs10 else 4.2
        yield_2y = dgs2.get('value', 4.0) if dgs2 else 4.0
        yield_spread = t10y2y.get('value', 0.2) if t10y2y else 0.2
        inflation = cpi.get('value', 3.2) if cpi else 3.2
        unemployment = unrate.get('value', 3.7) if unrate else 3.7
        
        # Determine Fed stance
        if fed_rate > 5.0:
            fed_stance = 'very_hawkish'
        elif fed_rate > 4.0:
            fed_stance = 'hawkish'
        elif fed_rate > 3.0:
            fed_stance = 'neutral'
        elif fed_rate > 2.0:
            fed_stance = 'dovish'
        else:
            fed_stance = 'very_dovish'
        
        # Determine liquidity condition
        if yield_spread < 0:
            liquidity_condition = 'tightening'  # Inverted yield curve
            recession_risk = 'high'
        elif yield_spread < 0.5:
            liquidity_condition = 'neutral'
            recession_risk = 'moderate'
        else:
            liquidity_condition = 'expanding'
            recession_risk = 'low'
        
        # Determine risk sentiment from macro
        if inflation > 4.0 and fed_stance in ['hawkish', 'very_hawkish']:
            risk_sentiment = 'risk-off'
            recommendation = 'reduce_risk'
        elif inflation < 3.0 and fed_stance in ['dovish', 'neutral']:
            risk_sentiment = 'risk-on'
            recommendation = 'increase_risk'
        else:
            risk_sentiment = 'neutral'
            recommendation = 'maintain_risk'
        
        # DXY trend from real data
        dxy_change = dxy_data.get('change', 0) if dxy_data else 0
        if dxy_change > 0.5:
            dxy_trend = 'strong_bullish'  # Strong USD = bearish for crypto
        elif dxy_change > 0:
            dxy_trend = 'bullish'
        elif dxy_change < -0.5:
            dxy_trend = 'strong_bearish'  # Weak USD = bullish for crypto
        elif dxy_change < 0:
            dxy_trend = 'bearish'
        else:
            dxy_trend = 'neutral'
        
        # SPY trend (risk sentiment)
        spy_change = spy_data.get('change', 0) if spy_data else 0
        if spy_change > 1.0:
            equity_sentiment = 'risk-on'
        elif spy_change < -1.0:
            equity_sentiment = 'risk-off'
        else:
            equity_sentiment = 'neutral'
        
        # Gold trend (safe haven)
        gld_change = gld_data.get('change', 0) if gld_data else 0
        if gld_change > 1.0:
            safe_haven_demand = 'high'
        elif gld_change < -1.0:
            safe_haven_demand = 'low'
        else:
            safe_haven_demand = 'neutral'
        
        # Combine macro + sentiment for final recommendation
        if risk_sentiment == 'risk-off' or equity_sentiment == 'risk-off' or safe_haven_demand == 'high':
            final_recommendation = 'reduce_risk'
        elif risk_sentiment == 'risk-on' and equity_sentiment == 'risk-on':
            final_recommendation = 'increase_risk'
        else:
            final_recommendation = 'maintain_risk'
        
        macro_conditions = {
            # FRED Economic Data
            'fed_funds_rate': fed_rate,
            'yield_10y': yield_10y,
            'yield_2y': yield_2y,
            'yield_spread_10y2y': yield_spread,
            'inflation_cpi': inflation,
            'inflation_pce': pcepi.get('value', 2.8) if pcepi else 2.8,
            'unemployment_rate': unemployment,
            'm2_money_supply': m2sl.get('value', 20800) if m2sl else 20800,
            
            # Fed Policy
            'fed_stance': fed_stance,
            'liquidity_condition': liquidity_condition,
            'recession_risk': recession_risk,
            
            # Market Sentiment (Alpha Vantage)
            'dxy_trend': dxy_trend,
            'dxy_change': dxy_change,
            'spy_change': spy_change,
            'gld_change': gld_change,
            'equity_sentiment': equity_sentiment,
            'safe_haven_demand': safe_haven_demand,
            
            # Combined Analysis
            'risk_sentiment': risk_sentiment,
            'recommendation': final_recommendation,
            
            # Metadata
            'data_sources': ['FRED', 'Alpha Vantage'],
            'data_timestamp': datetime.now().isoformat(),
            'confidence': 0.85 if all([fed_funds, dgs10, cpi, dxy_data, spy_data]) else 0.65
        }
        
        return macro_conditions


class ConsensusAgent(BaseAgent):
    """Aggregates signals from all agents, determines consensus"""
    
    def __init__(self):
        super().__init__(
            "ConsensusAgent",
            topics_subscribe=[TOPICS['CONSENSUS_REQUEST']]
        )
    
    def get_agent_type(self) -> str:
        return "consensus"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate agent outputs and determine consensus"""
        agent_outputs = data.get('agent_outputs', [])
        
        if not agent_outputs:
            return {'error': 'No agent outputs to aggregate', 'confidence': 0.0}
        
        # Weight by confidence
        weighted_signals = []
        for output in agent_outputs:
            confidence = output.get('confidence', 0.5)
            bias = output.get('bias', 'neutral')
            
            # Also check for bullish/bearish in different keys
            if not bias or bias == 'neutral':
                if output.get('recommendation') == 'reduce_risk':
                    bias = 'bearish'
                elif output.get('structure_status') == 'continuation':
                    bias = output.get('short_term_trend', 'neutral')
            
            if bias == 'bullish':
                weighted_signals.append(confidence)
            elif bias == 'bearish':
                weighted_signals.append(-confidence)
            else:
                weighted_signals.append(0)
        
        avg_signal = sum(weighted_signals) / len(weighted_signals) if weighted_signals else 0
        
        # Determine consensus - LOWERED thresholds for more signals
        if avg_signal > 0.15:  # Was 0.3
            consensus = 'bullish'
        elif avg_signal < -0.15:  # Was -0.3
            consensus = 'bearish'
        else:
            consensus = 'neutral'
        
        consensus_result = {
            'consensus': consensus,
            'avg_signal': avg_signal,
            'agent_count': len(agent_outputs),
            'bullish_agents': sum(1 for s in weighted_signals if s > 0),
            'bearish_agents': sum(1 for s in weighted_signals if s < 0),
            'neutral_agents': sum(1 for s in weighted_signals if s == 0),
            'confidence': abs(avg_signal),
            'recommendation': 'TRADE' if abs(avg_signal) > 0.25 else 'WAIT'  # Was 0.4
        }
        
        return consensus_result


# Factory function to create agents
def create_agent(agent_name: str) -> BaseAgent:
    agents = {
        'liquidity': LiquidityAgent,
        'structure': MarketStructureAgent,
        'risk': RiskAgent,
        'macro': MacroAgent,
        'consensus': ConsensusAgent,
    }
    
    if agent_name not in agents:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    return agents[agent_name]()


if __name__ == "__main__":
    # Test agents
    async def test():
        agent = LiquidityAgent()
        result = await agent.run({
            'symbol': 'BTCUSD',
            'timeframe': 'H4',
            'ohlcv': [[0, 100, 105, 98, 102, 1000]] * 50  # Mock OHLCV
        })
        print(f"LiquidityAgent result: {json.dumps(result, indent=2)}")
    
    asyncio.run(test())
