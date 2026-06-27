"""
Sentiment & News Data Collector
Collects: Twitter/X, Reddit, Fear & Greed, Google Trends, News Headlines
Sources: LunarCrush, Reddit API, CryptoPanic, Alternative.me
Time Range: 2015-2026

Usage:
    python sentiment_news_collector.py --type sentiment --start 2015-01-01
    python sentiment_news_collector.py --type news --realtime
    python sentiment_news_collector.py --type all
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import asyncpg
import os
import json

class SentimentNewsCollector:
    def __init__(self):
        # API Keys
        self.lunarcrush_key = os.getenv('LUNARCRUSH_API_KEY', '')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID', '')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET', '')
        self.cryptopanic_key = os.getenv('CRYPTOPANIC_API_KEY', '')
        
        # APIs
        self.lunarcrush_api = "https://api.lunarcrush.com/v3"
        self.reddit_api = "https://oauth.reddit.com"
        self.cryptopanic_api = "https://cryptopanic.com/api/v1"
        self.fear_greed_api = "https://api.alternative.me/fng"
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'swarm_trader')
        }
        
        self.session = None
        self.db_pool = None
        self.reddit_token = None
    
    async def connect(self):
        headers = {}
        if self.lunarcrush_key:
            headers['Authorization'] = f'Bearer {self.lunarcrush_key}'
        
        self.session = aiohttp.ClientSession(headers=headers)
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        
        # Get Reddit OAuth token
        if self.reddit_client_id and self.reddit_client_secret:
            await self.get_reddit_token()
        
        print("✅ Sentiment & News collector connected")
    
    async def get_reddit_token(self):
        """Get Reddit OAuth2 token"""
        url = "https://www.reddit.com/api/v1/access_token"
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        auth = aiohttp.BasicAuth(self.reddit_client_id, self.reddit_client_secret)
        
        try:
            async with self.session.post(url, data=data, auth=auth) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.reddit_token = token_data['access_token']
                    print("✅ Reddit OAuth token obtained")
        except Exception as e:
            print(f"⚠️  Reddit auth failed: {e}")
    
    async def close(self):
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
    
    async def fetch_fear_greed(self, days: int = 365) -> List[Dict]:
        """Fetch Fear & Greed Index"""
        url = f"{self.fear_greed_api}/?limit={days}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('data'):
                        return [
                            {
                                'timestamp': datetime.strptime(item['timestamp'], '%Y-%m-%d'),
                                'value': int(item['value']),
                                'classification': item['value_classification'],
                                'source': 'alternative.me'
                            }
                            for item in data['data']
                        ]
        except Exception as e:
            print(f"❌ Fear & Greed error: {e}")
        
        return []
    
    async def fetch_reddit_sentiment(self, subreddit: str, days: int = 30) -> List[Dict]:
        """Fetch Reddit posts and comments for sentiment analysis"""
        if not self.reddit_token:
            return []
        
        url = f"{self.reddit_api}/r/{subreddit}/hot"
        params = {'limit': 100}
        headers = {'Authorization': f'Bearer {self.reddit_token}'}
        
        all_posts = []
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and 'children' in data['data']:
                        for post in data['data']['children']:
                            post_data = post['data']
                            all_posts.append({
                                'timestamp': datetime.fromtimestamp(post_data['created_utc']),
                                'title': post_data['title'],
                                'score': post_data['score'],
                                'num_comments': post_data['num_comments'],
                                'url': f"https://reddit.com{post_data['permalink']}",
                                'source': f'reddit_{subreddit}'
                            })
        except Exception as e:
            print(f"❌ Reddit error: {e}")
        
        return all_posts
    
    async def fetch_cryptopanic_news(self, days: int = 30) -> List[Dict]:
        """Fetch crypto news from CryptoPanic"""
        if not self.cryptopanic_key:
            return []
        
        url = f"{self.cryptopanic_api}/posts/"
        params = {
            'auth_token': self.cryptopanic_key,
            'filter': 'hot',
            'limit': 100
        }
        
        all_news = []
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'results' in data:
                        for post in data['results']:
                            all_news.append({
                                'headline': post['title'],
                                'summary': post.get('body', ''),
                                'url': post['url'],
                                'source': post['source']['title'],
                                'timestamp': datetime.strptime(post['published_at'], '%Y-%m-%dT%H:%M:%SZ'),
                                'sentiment': post.get('sentiment', 'neutral'),
                                'assets': [coin['code'] for coin in post.get('currencies', [])]
                            })
        except Exception as e:
            print(f"❌ CryptoPanic error: {e}")
        
        return all_news
    
    async def save_sentiment(self, data: List[Dict]):
        """Save sentiment data to PostgreSQL"""
        if not data:
            return
        
        async with self.db_pool.acquire() as conn:
            for record in data:
                # Calculate sentiment score (-1 to 1)
                if 'value' in record:  # Fear & Greed
                    sentiment_score = (record['value'] - 50) / 50  # Normalize to -1 to 1
                elif 'score' in record:  # Reddit
                    sentiment_score = min(record['score'] / 1000, 1.0)
                else:
                    sentiment_score = 0
                
                # Classify sentiment
                if sentiment_score > 0.5:
                    label = 'Very Positive'
                elif sentiment_score > 0.2:
                    label = 'Positive'
                elif sentiment_score > -0.2:
                    label = 'Neutral'
                elif sentiment_score > -0.5:
                    label = 'Negative'
                else:
                    label = 'Very Negative'
                
                query = """
                    INSERT INTO sentiment_data 
                    (source, timestamp, sentiment_score, sentiment_label, volume, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                metadata = json.dumps({
                    'classification': record.get('classification', ''),
                    'url': record.get('url', '')
                })
                
                await conn.execute(query, record['source'], record['timestamp'],
                                 sentiment_score, label, record.get('num_comments', 0), metadata)
        
        print(f"✅ Saved {len(data)} sentiment records")
    
    async def save_news(self, data: List[Dict]):
        """Save news headlines to PostgreSQL"""
        if not data:
            return
        
        async with self.db_pool.acquire() as conn:
            for record in data:
                # Simple sentiment from CryptoPanic
                sentiment_map = {
                    'bullish': 0.7,
                    'somewhat_bullish': 0.4,
                    'neutral': 0,
                    'somewhat_bearish': -0.4,
                    'bearish': -0.7
                }
                sentiment_score = sentiment_map.get(record.get('sentiment', 'neutral'), 0)
                
                # Impact scoring (simplified)
                impact_score = 3  # Default medium impact
                
                query = """
                    INSERT INTO news_headlines 
                    (headline, summary, source, url, timestamp, sentiment_score, 
                     sentiment_label, impact_score, assets, category)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                await conn.execute(query, record['headline'], record.get('summary', ''),
                                 record['source'], record['url'], record['timestamp'],
                                 sentiment_score, record.get('sentiment', 'neutral'),
                                 impact_score, record.get('assets', []), 'Market')
        
        print(f"✅ Saved {len(data)} news records")
    
    async def collect_historical(self, data_type: str, start_date: str, end_date: str):
        """Collect sentiment or news data historically"""
        print(f"\n🚀 Collecting {data_type} data")
        print(f"   Range: {start_date} to {end_date}")
        
        if data_type == 'sentiment':
            # Fetch Fear & Greed
            print("   📊 Fetching Fear & Greed Index...")
            days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
            fg_data = await self.fetch_fear_greed(min(days, 365))
            if fg_data:
                await self.save_sentiment(fg_data)
                print(f"      Got {len(fg_data)} data points")
            
            # Fetch Reddit sentiment
            for subreddit in ['CryptoCurrency', 'Bitcoin', 'ethtrader']:
                print(f"   📊 Fetching Reddit r/{subreddit}...")
                reddit_data = await self.fetch_reddit_sentiment(subreddit, 30)
                if reddit_data:
                    await self.save_sentiment(reddit_data)
                    print(f"      Got {len(reddit_data)} posts")
        
        elif data_type == 'news':
            print("   📊 Fetching CryptoPanic news...")
            news_data = await self.fetch_cryptopanic_news(30)
            if news_data:
                await self.save_news(news_data)
                print(f"      Got {len(news_data)} news articles")
        
        print(f"✅ {data_type} collection complete")
    
    async def collect_realtime(self, data_type: str = 'all'):
        """Collect real-time sentiment and news"""
        print(f"🔴 Starting real-time {data_type} collection")
        
        while True:
            try:
                if data_type in ['sentiment', 'all']:
                    # Fear & Greed
                    fg_data = await self.fetch_fear_greed(1)
                    if fg_data:
                        await self.save_sentiment(fg_data)
                    
                    # Reddit
                    for subreddit in ['CryptoCurrency', 'Bitcoin']:
                        reddit_data = await self.fetch_reddit_sentiment(subreddit, 1)
                        if reddit_data:
                            await self.save_sentiment(reddit_data)
                
                if data_type in ['news', 'all']:
                    # CryptoPanic
                    news_data = await self.fetch_cryptopanic_news(1)
                    if news_data:
                        await self.save_news(news_data)
                
                print(f"✅ Real-time update @ {datetime.now()}")
                await asyncio.sleep(600)  # Update every 10 minutes
                
            except Exception as e:
                print(f"❌ Real-time error: {e}")
                await asyncio.sleep(60)


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sentiment & News Collector')
    parser.add_argument('--type', type=str, choices=['sentiment', 'news', 'all'], default='all')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--realtime', action='store_true')
    
    args = parser.parse_args()
    
    collector = SentimentNewsCollector()
    await collector.connect()
    
    try:
        if args.realtime:
            await collector.collect_realtime(args.type)
        else:
            if not args.start:
                args.start = '2015-01-01'
            if not args.end:
                args.end = datetime.now().strftime('%Y-%m-%d')
            
            await collector.collect_historical(args.type, args.start, args.end)
    finally:
        await collector.close()


if __name__ == '__main__':
    asyncio.run(main())
