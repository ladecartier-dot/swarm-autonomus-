"""
Additional Swarm Agents - Sentiment, On-chain, Options Flow
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

from agents.base_agents import BaseAgent
from core.message_bus import TOPICS


class SentimentAgent(BaseAgent):
    """
    Analyzes market sentiment from news, social media, funding rates.
    
    Data sources:
    - Crypto Fear & Greed Index (free API)
    - Funding rates (Binance/Bybit public)
    - News sentiment (NewsAPI free tier)
    - Social volume (alternative.me)
    """
    
    def __init__(self):
        super().__init__(
            "SentimentAgent",
            topics_subscribe=[TOPICS['MARKET_DATA']]
        )
    
    def get_agent_type(self) -> str:
        return "sentiment_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment"""
        symbol = data.get('symbol', 'BTCUSD')
        
        # Fetch Fear & Greed Index
        fear_greed = await self._get_fear_greed()
        
        # Fetch funding rates
        funding = await self._get_funding_rates(symbol)
        
        # Calculate composite sentiment
        sentiment_score = 0
        
        # Fear & Greed contribution (0-100, >50 = greedy/bullish)
        if fear_greed:
            fg_value = fear_greed.get('value', 50)
            sentiment_score += (fg_value - 50) / 50 * 0.4  # 40% weight
        
        # Funding rates (negative = bearish sentiment, positive = bullish)
        if funding:
            avg_funding = funding.get('avg_funding', 0)
            sentiment_score += min(max(avg_funding * 10, -0.3), 0.3) * 0.6  # 60% weight
        
        # Determine bias
        if sentiment_score > 0.2:
            bias = 'bullish'
        elif sentiment_score < -0.2:
            bias = 'bearish'
        else:
            bias = 'neutral'
        
        return {
            'symbol': symbol,
            'sentiment_score': sentiment_score,
            'bias': bias,
            'fear_greed': fear_greed,
            'funding_rates': funding,
            'confidence': 0.60,
            'components': {
                'fear_greed_weight': 0.4,
                'funding_weight': 0.6
            }
        }
    
    async def _get_fear_greed(self) -> Dict:
        """Fetch Crypto Fear & Greed Index"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.alternative.me/fng/', timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 'success':
                            latest = data['data'][0]
                            return {
                                'value': int(latest['value']),
                                'classification': latest['value_classification'],
                                'timestamp': latest['timestamp']
                            }
        except Exception as e:
            pass
        
        # Fallback to mock
        return {
            'value': 50,
            'classification': 'Neutral',
            'timestamp': int(datetime.now().timestamp()),
            'source': 'mock'
        }
    
    async def _get_funding_rates(self, symbol: str) -> Dict:
        """Fetch funding rates from Binance"""
        try:
            import aiohttp
            binance_symbol = symbol.replace('USD', 'USDT')
            
            async with aiohttp.ClientSession() as session:
                url = f'https://fapi.binance.com/fapi/v1/premiumIndex?symbol={binance_symbol}'
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            'symbol': binance_symbol,
                            'funding_rate': float(data.get('lastFundingRate', 0)),
                            'avg_funding': float(data.get('lastFundingRate', 0)),
                            'next_funding': data.get('nextFundingTime', '')
                        }
        except Exception as e:
            pass
        
        return {
            'avg_funding': 0.0001,
            'source': 'mock'
        }


class OnChainAgent(BaseAgent):
    """
    On-chain analysis for crypto.
    
    Metrics:
    - Exchange flows (inflows/outflows)
    - Whale movements
    - Active addresses
    - Transaction volume
    - MVRV ratio
    """
    
    def __init__(self):
        super().__init__(
            "OnChainAgent",
            topics_subscribe=[TOPICS['MARKET_DATA']]
        )
    
    def get_agent_type(self) -> str:
        return "onchain_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze on-chain metrics"""
        symbol = data.get('symbol', 'BTCUSD')
        
        # Fetch on-chain data (mock for now, can integrate with Glassnode/CryptoQuant)
        metrics = await self._fetch_onchain_metrics(symbol)
        
        # Calculate on-chain score
        score = 0
        
        # Exchange outflows = bullish (supply shock)
        exchange_flow = metrics.get('exchange_flow_7d', 0)
        if exchange_flow < 0:  # Net outflow
            score += 0.3
        elif exchange_flow > 0:
            score -= 0.3
        
        # Active addresses growth = bullish
        addr_growth = metrics.get('active_addresses_growth', 0)
        score += min(addr_growth * 0.1, 0.3)
        
        # MVRV < 1 = undervalued (bullish)
        mvrv = metrics.get('mvrv_ratio', 1.5)
        if mvrv < 1:
            score += 0.3
        elif mvrv > 3:
            score -= 0.3
        
        # Determine bias
        if score > 0.2:
            bias = 'bullish'
        elif score < -0.2:
            bias = 'bearish'
        else:
            bias = 'neutral'
        
        return {
            'symbol': symbol,
            'onchain_score': score,
            'bias': bias,
            'metrics': metrics,
            'confidence': 0.55
        }
    
    async def _fetch_onchain_metrics(self, symbol: str) -> Dict:
        """Fetch on-chain metrics (mock implementation)"""
        # In production, integrate with:
        # - Glassnode API
        # - CryptoQuant API
        # - Dune Analytics
        # - Etherscan for ETH tokens
        
        return {
            'exchange_flow_7d': random.uniform(-5000, 5000),  # BTC
            'active_addresses_growth': random.uniform(-0.1, 0.2),
            'mvrv_ratio': random.uniform(0.8, 2.5),
            'whale_transactions_24h': random.randint(50, 200),
            'source': 'mock'
        }


class OptionsFlowAgent(BaseAgent):
    """
    Analyzes options flow for institutional positioning.
    
    Metrics:
    - Put/Call ratio
    - Max pain level
    - Open interest changes
    - Unusual options activity
    """
    
    def __init__(self):
        super().__init__(
            "OptionsFlowAgent",
            topics_subscribe=[TOPICS['MARKET_DATA']]
        )
    
    def get_agent_type(self) -> str:
        return "options_flow"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze options flow"""
        symbol = data.get('symbol', 'BTCUSD')
        
        # For crypto options (Deribit), would fetch from Deribit API
        # For traditional markets, would fetch from CBOE/CME
        
        # Mock implementation
        put_call_ratio = random.uniform(0.5, 1.5)
        max_pain = random.uniform(90000, 100000) if 'BTC' in symbol else random.uniform(3000, 4000)
        
        # PCR < 1 = bullish (more calls), PCR > 1 = bearish (more puts)
        if put_call_ratio < 0.8:
            bias = 'bullish'
            score = 0.4
        elif put_call_ratio > 1.2:
            bias = 'bearish'
            score = -0.4
        else:
            bias = 'neutral'
            score = 0
        
        return {
            'symbol': symbol,
            'options_score': score,
            'bias': bias,
            'put_call_ratio': put_call_ratio,
            'max_pain': max_pain,
            'confidence': 0.50,
            'note': 'Mock data - integrate Deribit/CBOE API for production'
        }


class NewsAgent(BaseAgent):
    """
    Real-time news analysis and event detection.
    
    Monitors:
    - Crypto news feeds
    - Economic calendar
    - Fed speeches
    - Regulatory announcements
    """
    
    def __init__(self):
        super().__init__(
            "NewsAgent",
            topics_subscribe=[TOPICS['MACRO_UPDATE']]
        )
    
    def get_agent_type(self) -> str:
        return "news_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze news sentiment and events"""
        # Would integrate with:
        # - NewsAPI
        # - CryptoPanic API
        # - Twitter API for whale/influencer tracking
        # - Economic calendar APIs
        
        # Mock implementation
        recent_events = []
        sentiment = 'neutral'
        impact_score = 0
        
        # Check for major events (mock)
        if random.random() > 0.8:
            sentiment = 'bullish' if random.random() > 0.5 else 'bearish'
            impact_score = random.uniform(0.3, 0.7)
            recent_events.append({
                'headline': 'Major institutional adoption announced',
                'sentiment': sentiment,
                'impact': impact_score,
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'sentiment': sentiment,
            'impact_score': impact_score,
            'recent_events': recent_events,
            'confidence': 0.45,
            'note': 'Mock data - integrate news APIs for production'
        }


class CorrelationAgent(BaseAgent):
    """
    Analyzes correlations between assets and macro factors.
    
    Tracks:
    - BTC-ETH correlation
    - Crypto-DXY inverse correlation
    - Crypto-equities correlation (QQQ, SPY)
    - Inter-asset correlations
    """
    
    def __init__(self):
        super().__init__(
            "CorrelationAgent",
            topics_subscribe=[TOPICS['MARKET_DATA'], TOPICS['MACRO_UPDATE']]
        )
    
    def get_agent_type(self) -> str:
        return "correlation_analysis"
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market correlations"""
        # Would fetch:
        # - DXY, yields, SPY, QQQ prices
        # - Major crypto prices
        # - Calculate rolling correlations
        
        # Mock implementation
        btc_eth_corr = random.uniform(0.6, 0.95)
        btc_dxy_corr = random.uniform(-0.6, -0.2)
        btc_spy_corr = random.uniform(0.2, 0.6)
        
        # High BTC-ETH correlation = risk-on crypto market
        # Negative BTC-DXY = dollar weakness = crypto strength
        
        regime = 'risk-on' if btc_eth_corr > 0.8 and btc_dxy_corr < -0.3 else 'mixed'
        
        return {
            'correlations': {
                'btc_eth': btc_eth_corr,
                'btc_dxy': btc_dxy_corr,
                'btc_spy': btc_spy_corr
            },
            'market_regime': regime,
            'bias': 'bullish' if regime == 'risk-on' else 'neutral',
            'confidence': 0.50,
            'note': 'Mock data - integrate macro data feeds for production'
        }


# Factory function
def create_agent(agent_name: str) -> BaseAgent:
    agents = {
        'sentiment': SentimentAgent,
        'onchain': OnChainAgent,
        'options': OptionsFlowAgent,
        'news': NewsAgent,
        'correlation': CorrelationAgent,
    }
    
    if agent_name not in agents:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    return agents[agent_name]()


if __name__ == "__main__":
    async def test():
        agent = SentimentAgent()
        result = await agent.run({'symbol': 'BTCUSD'})
        print(f"SentimentAgent: {result}")
        
        agent = OnChainAgent()
        result = await agent.run({'symbol': 'BTCUSD'})
        print(f"OnChainAgent: {result}")
    
    asyncio.run(test())
