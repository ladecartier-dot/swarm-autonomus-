"""
Shared Blackboard Memory System
Agents publish/subscribe to shared state via SQLite + JSON
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

STATE_DIR = Path(__file__).parent.parent / "state"
DB_PATH = STATE_DIR / "blackboard.db"
STATE_FILE = STATE_DIR / "STATE.md"
LEARNINGS_FILE = STATE_DIR / "LEARNINGS.md"

class Blackboard:
    """Shared memory for swarm agents"""
    
    def __init__(self):
        self._init_db()
        self._ensure_state_files()
    
    def _init_db(self):
        """Initialize SQLite database for shared state"""
        STATE_DIR.mkdir(exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Agent messages table
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            )
        ''')
        
        # Shared state table (key-value)
        c.execute('''
            CREATE TABLE IF NOT EXISTS state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Agent performance tracking
        c.execute('''
            CREATE TABLE IF NOT EXISTS agent_stats (
                agent_name TEXT PRIMARY KEY,
                calls_count INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                failed_calls INTEGER DEFAULT 0,
                avg_confidence REAL,
                last_active DATETIME
            )
        ''')
        
        # Market data cache
        c.execute('''
            CREATE TABLE IF NOT EXISTS market_cache (
                symbol TEXT,
                timeframe TEXT,
                data_type TEXT,
                content TEXT NOT NULL,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, timeframe, data_type)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _ensure_state_files(self):
        """Ensure STATE.md and LEARNINGS.md exist"""
        if not STATE_FILE.exists():
            STATE_FILE.write_text("# Swarm State\n\n*Last updated: Never*\n\n## Active Positions\n\n## Pending Signals\n\n## Current Market Regime\n\n")
        
        if not LEARNINGS_FILE.exists():
            LEARNINGS_FILE.write_text("# Swarm Learnings\n\n*Accumulated knowledge from trades and analysis*\n\n## Pattern Recognitions\n\n## Failed Setups\n\n## Successful Setups\n\n## Market Regime Insights\n\n")
    
    def publish(self, agent_name: str, message_type: str, content: Dict[str, Any], confidence: float = 0.5):
        """Publish a message to the blackboard"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            'INSERT INTO messages (agent_name, message_type, content, confidence) VALUES (?, ?, ?, ?)',
            (agent_name, message_type, json.dumps(content), confidence)
        )
        conn.commit()
        conn.close()
        
        # Update agent stats
        self._update_agent_stats(agent_name, success=True, confidence=confidence)
        
        return c.lastrowid
    
    def subscribe(self, message_type: Optional[str] = None, agent_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Subscribe to messages (optionally filtered by type or agent)"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        query = 'SELECT * FROM messages WHERE 1=1'
        params = []
        
        if message_type:
            query += ' AND message_type = ?'
            params.append(message_type)
        
        if agent_name:
            query += ' AND agent_name = ?'
            params.append(agent_name)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                'id': r[0],
                'agent_name': r[1],
                'message_type': r[2],
                'content': json.loads(r[3]),
                'confidence': r[4],
                'timestamp': r[5],
                'processed': bool(r[6])
            }
            for r in rows
        ]
    
    def mark_processed(self, message_id: int):
        """Mark a message as processed"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('UPDATE messages SET processed = 1 WHERE id = ?', (message_id,))
        conn.commit()
        conn.close()
    
    def get_state(self, key: str) -> Optional[Any]:
        """Get a state value"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('SELECT value FROM state WHERE key = ?', (key,))
        row = c.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
    
    def set_state(self, key: str, value: Any):
        """Set a state value"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
            (key, json.dumps(value))
        )
        conn.commit()
        conn.close()
    
    def cache_market_data(self, symbol: str, timeframe: str, data_type: str, content: Dict):
        """Cache market data"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO market_cache (symbol, timeframe, data_type, content, fetched_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (symbol, timeframe, data_type, json.dumps(content))
        )
        conn.commit()
        conn.close()
    
    def get_cached_market_data(self, symbol: str, timeframe: str, data_type: str, max_age_minutes: int = 30) -> Optional[Dict]:
        """Get cached market data if not stale"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute(
            'SELECT content, fetched_at FROM market_cache WHERE symbol = ? AND timeframe = ? AND data_type = ?',
            (symbol, timeframe, data_type)
        )
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Check age
        fetched = datetime.fromisoformat(row[1])
        age = (datetime.now() - fetched).total_seconds() / 60
        if age > max_age_minutes:
            return None
        
        return json.loads(row[0])
    
    def _update_agent_stats(self, agent_name: str, success: bool, confidence: float):
        """Update agent performance stats"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        
        # Get current stats
        c.execute('SELECT * FROM agent_stats WHERE agent_name = ?', (agent_name,))
        row = c.fetchone()
        
        if row:
            calls = row[1] + 1
            successful = row[2] + (1 if success else 0)
            failed = row[3] + (0 if success else 1)
            # Update avg confidence
            old_avg = row[4] or 0
            new_avg = (old_avg * row[1] + confidence) / calls if calls > 0 else confidence
            c.execute(
                'UPDATE agent_stats SET calls_count = ?, successful_calls = ?, failed_calls = ?, avg_confidence = ?, last_active = CURRENT_TIMESTAMP WHERE agent_name = ?',
                (calls, successful, failed, new_avg, agent_name)
            )
        else:
            c.execute(
                'INSERT INTO agent_stats (agent_name, calls_count, successful_calls, failed_calls, avg_confidence, last_active) VALUES (?, 1, ?, ?, ?, CURRENT_TIMESTAMP)',
                (agent_name, 1 if success else 0, 0 if success else 1, confidence)
            )
        
        conn.commit()
        conn.close()
    
    def get_agent_stats(self) -> List[Dict]:
        """Get all agent performance stats"""
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute('SELECT * FROM agent_stats ORDER BY avg_confidence DESC')
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                'agent_name': r[0],
                'calls_count': r[1],
                'successful_calls': r[2],
                'failed_calls': r[3],
                'avg_confidence': r[4],
                'last_active': r[5]
            }
            for r in rows
        ]
    
    def update_state_file(self, section: str, content: str):
        """Update STATE.md with new content"""
        current = STATE_FILE.read_text()
        # Simple append for now - can be smarter later
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update = f"\n## [{timestamp}] {section}\n\n{content}\n"
        STATE_FILE.write_text(current + update)
    
    def add_learning(self, category: str, insight: str):
        """Add a learning to LEARNINGS.md"""
        current = LEARNINGS_FILE.read_text()
        timestamp = datetime.now().strftime("%Y-%m-%d")
        learning = f"\n### [{timestamp}] {category}\n\n{insight}\n"
        LEARNINGS_FILE.write_text(current + learning)


# Singleton instance
_blackboard = None

def get_blackboard() -> Blackboard:
    global _blackboard
    if _blackboard is None:
        _blackboard = Blackboard()
    return _blackboard


if __name__ == "__main__":
    # Test
    bb = get_blackboard()
    bb.publish("TestAgent", "test", {"message": "hello swarm"}, confidence=0.8)
    msgs = bb.subscribe(limit=5)
    print(f"Published and retrieved {len(msgs)} messages")
    print(f"State files: {STATE_FILE.exists()}, {LEARNINGS_FILE.exists()}")
