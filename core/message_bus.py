"""
Message Bus - Pub/Sub for Agent Communication
Async event-driven communication layer
"""
import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class Message:
    topic: str
    agent_name: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 0  # Higher = more urgent
    correlation_id: Optional[str] = None


class MessageBus:
    """Async pub/sub message bus for agent communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._message_history: List[Message] = []
        self._max_history = 1000
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        self._subscribers[topic].append(callback)
        print(f"📬 Agent subscribed to: {topic}")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)
    
    async def publish(self, topic: str, agent_name: str, payload: Dict[str, Any], priority: int = 0):
        """Publish a message to a topic"""
        msg = Message(
            topic=topic,
            agent_name=agent_name,
            payload=payload,
            timestamp=datetime.now(),
            priority=priority
        )
        
        await self._message_queue.put(msg)
        self._message_history.append(msg)
        
        # Trim history
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
        
        # Notify subscribers immediately (in addition to queue processing)
        await self._notify_subscribers(msg)
    
    async def _notify_subscribers(self, msg: Message):
        """Notify all subscribers of a message"""
        # Direct subscribers
        for callback in self._subscribers.get(msg.topic, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(msg)
                else:
                    callback(msg)
            except Exception as e:
                print(f"❌ Error notifying subscriber: {e}")
        
        # Wildcard subscribers (*)
        for callback in self._subscribers.get('*', []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(msg)
                else:
                    callback(msg)
            except Exception as e:
                print(f"❌ Error notifying wildcard subscriber: {e}")
    
    async def start(self):
        """Start the message bus processor"""
        self._running = True
        print("🚌 Message bus started")
        
        while self._running:
            try:
                msg = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)
                # Additional processing can happen here (logging, persistence, etc.)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Message bus error: {e}")
    
    def stop(self):
        """Stop the message bus"""
        self._running = False
        print("🛑 Message bus stopped")
    
    def get_history(self, topic: Optional[str] = None, limit: int = 50) -> List[Message]:
        """Get message history"""
        if topic:
            filtered = [m for m in self._message_history if m.topic == topic]
            return filtered[-limit:]
        return self._message_history[-limit:]
    
    def get_topics(self) -> List[str]:
        """Get all active topics"""
        return list(self._subscribers.keys())
    
    def get_subscriber_count(self, topic: str) -> int:
        """Get number of subscribers for a topic"""
        return len(self._subscribers.get(topic, 0))


# Topics for swarm communication
TOPICS = {
    # Market data updates
    'MARKET_DATA': 'market.data',
    'PRICE_UPDATE': 'market.price',
    'OHLCV_READY': 'market.ohlcv',
    
    # Signal generation
    'SIGNAL_GENERATED': 'signal.generated',
    'SIGNAL_CONFIRMED': 'signal.confirmed',
    'SIGNAL_INVALIDATED': 'signal.invalidated',
    
    # Analysis
    'LIQUIDITY_ANALYSIS': 'analysis.liquidity',
    'MARKET_STRUCTURE': 'analysis.structure',
    'MACRO_UPDATE': 'analysis.macro',
    'SENTIMENT_UPDATE': 'analysis.sentiment',
    
    # Risk management
    'RISK_CHECK': 'risk.check',
    'POSITION_OPENED': 'risk.position.opened',
    'POSITION_CLOSED': 'risk.position.closed',
    'DRAWDOWN_ALERT': 'risk.drawdown',
    
    # Orchestration
    'ORCHESTRATOR_COMMAND': 'orchestrator.command',
    'AGENT_STATUS': 'agent.status',
    'CONSENSUS_REQUEST': 'consensus.request',
    'CONSENSUS_RESULT': 'consensus.result',
    
    # Learning
    'TRADE_RESULT': 'learning.trade_result',
    'PATTERN_DETECTED': 'learning.pattern',
    'STRATEGY_UPDATE': 'learning.strategy',
}


# Global instance
_message_bus: Optional[MessageBus] = None

def get_message_bus() -> MessageBus:
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


if __name__ == "__main__":
    # Test
    async def test():
        bus = get_message_bus()
        
        async def handler(msg):
            print(f"📨 Received: {msg.topic} from {msg.agent_name}")
        
        bus.subscribe(TOPICS['SIGNAL_GENERATED'], handler)
        
        await bus.publish(TOPICS['SIGNAL_GENERATED'], "TestAgent", {"signal": "BUY", "symbol": "BTCUSD"})
        
        await asyncio.sleep(1)
        bus.stop()
    
    asyncio.run(test())
