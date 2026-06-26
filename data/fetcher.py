"""
Live Data Fetcher - Real-time market data from multiple sources
Supports: CoinGecko, Diadata, Binance, FRED (economic data), Alpha Vantage (stocks/forex)
"""
import asyncio
import aiohttp
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from core.blackboard import get_blackboard


class DataFetcher:
    """
    Fetch live market data from multiple sources.
    
    Sources:
    - CoinGecko (primary, no key needed)
    - Diadata (backup, no key needed)
    - CoinPaprika (backup, no key needed)
    - Binance public API (OHLCV, no key needed)
    - FRED (economic indicators - requires API key)
    - Alpha Vantage (stocks, forex, crypto, technicals - requires API key)
    """
    
    def __init__(self):
        self.blackboard = get_blackboard()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API keys from environment
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        
        # API endpoints
        self.endpoints = {
            'coingecko': {
                'price': 'https://api.coingecko.com/api/v3/simple/price',
                'ohlcv': 'https://api.coingecko.com/api/v3/coins/{id}/ohlc',
            },
            'diadata': {
                'price': 'https://api.diadata.org/quotes',
            },
            'coinpaprika': {
                'price': 'https://api.coinpaprika.com/v1/tickers',
            },
            'binance': {
                'klines': 'https://api.binance.com/api/v3/klines',
            },
            'fred': {
                'series': 'https://api.stlouisfed.org/fred/series/observations',
            },
            'alpha_vantage': {
                'quote': 'https://www.alphavantage.co/query',
            }
        }
        
        # CoinGecko ID mapping
        self.coin_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'LINK': 'chainlink',
            'DOT': 'polkadot',
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_price(self, symbol: str, source: str = 'coingecko') -> Optional[Dict]:
        """Get current price for a symbol"""
        
        if source == 'coingecko':
            return await self._get_price_coingecko(symbol)
        elif source == 'diadata':
            return await self._get_price_diadata(symbol)
        elif source == 'coinpaprika':
            return await self._get_price_coinpaprika(symbol)
        
        return None
    
    async def _get_price_coingecko(self, symbol: str) -> Optional[Dict]:
        """Fetch from CoinGecko"""
        coin_id = self.coin_ids.get(symbol.upper().replace('USD', ''))
        if not coin_id:
            print(f"⚠️ Unknown symbol: {symbol}")
            return None
        
        try:
            session = await self._get_session()
            # Fix: include_24hr_vol and include_24hr_change must be "true" (string) not True (bool)
            params = {'ids': coin_id, 'vs_currencies': 'usd', 'include_24hr_vol': 'true', 'include_24hr_change': 'true'}
            
            async with session.get(self.endpoints['coingecko']['price'], params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if coin_id in data:
                        price_data = data[coin_id]
                        return {
                            'symbol': symbol,
                            'price': price_data.get('usd'),
                            'volume_24h': price_data.get('usd_24h_vol'),
                            'change_24h': price_data.get('usd_24h_change'),
                            'source': 'coingecko',
                            'timestamp': datetime.now().isoformat()
                        }
                elif resp.status == 429:
                    print(f"⚠️ CoinGecko rate limited, using fallback...")
                    return self._get_mock_price(symbol)
                else:
                    print(f"❌ CoinGecko error: {resp.status}")
                    return self._get_mock_price(symbol)
        except Exception as e:
            print(f"❌ CoinGecko fetch failed: {e}")
            return self._get_mock_price(symbol)
        
        return self._get_mock_price(symbol)
    
    def _get_mock_price(self, symbol: str) -> Dict:
        """Return mock price data when APIs are unavailable"""
        import random
        base_prices = {
            'BTCUSD': 95000,
            'ETHUSD': 3500,
            'SOLUSD': 200,
            'BNBUSD': 600,
            'XRPUSD': 0.50,
        }
        base = base_prices.get(symbol.upper(), 100)
        price = base * (1 + random.uniform(-0.02, 0.02))
        change = random.uniform(-5, 5)
        
        return {
            'symbol': symbol,
            'price': price,
            'volume_24h': random.uniform(1e9, 5e9),
            'change_24h': change,
            'source': 'mock',
            'timestamp': datetime.now().isoformat(),
            'note': 'Mock data - APIs unavailable'
        }
    
    async def _get_price_diadata(self, symbol: str) -> Optional[Dict]:
        """Fetch from Diadata"""
        try:
            session = await self._get_session()
            # Diadata uses trading pair format
            pair = f"{symbol.replace('USD', '')}/USD"
            
            async with session.get(f"{self.endpoints['diadata']['price']}?symbol={pair}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and len(data) > 0:
                        quote = data[0]
                        return {
                            'symbol': symbol,
                            'price': float(quote.get('askPrice', 0)),
                            'source': 'diadata',
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception as e:
            print(f"❌ Diadata fetch failed: {e}")
        
        return None
    
    async def _get_price_coinpaprika(self, symbol: str) -> Optional[Dict]:
        """Fetch from CoinPaprika"""
        try:
            session = await self._get_session()
            
            async with session.get(self.endpoints['coinpaprika']['price']) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Find matching symbol
                    for ticker in data:
                        if ticker['symbol'] == symbol.replace('USD', ''):
                            return {
                                'symbol': symbol,
                                'price': ticker['quotes']['USD']['price'],
                                'volume_24h': ticker['quotes']['USD']['volume_24h'],
                                'change_24h': ticker['quotes']['USD']['percent_change_24h'],
                                'source': 'coinpaprika',
                                'timestamp': datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"❌ CoinPaprika fetch failed: {e}")
        
        return None
    
    async def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List[List]]:
        """
        Fetch OHLCV data from Binance public API.
        
        Timeframes: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        try:
            session = await self._get_session()
            
            # Convert symbol to Binance format
            binance_symbol = symbol.replace('USD', 'USDT')
            
            # Convert timeframe
            tf_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '4h': '4h', '6h': '6h', '12h': '12h',
                'D1': '1d', 'W1': '1w', 'M1': '1M'
            }
            binance_tf = tf_map.get(timeframe, '4h')
            
            params = {
                'symbol': binance_symbol,
                'interval': binance_tf,
                'limit': limit
            }
            
            async with session.get(self.endpoints['binance']['klines'], params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Convert to standard OHLCV format
                    ohlcv = []
                    for candle in data:
                        ohlcv.append([
                            candle[0] // 1000,  # Timestamp (seconds)
                            float(candle[1]),   # Open
                            float(candle[2]),   # High
                            float(candle[3]),   # Low
                            float(candle[4]),   # Close
                            float(candle[5]),   # Volume
                        ])
                    
                    return ohlcv
                else:
                    print(f"❌ Binance error: {resp.status}")
        
        except Exception as e:
            print(f"❌ Binance fetch failed: {e}")
        
        return None
    
    async def get_multi_symbol_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch prices for multiple symbols at once"""
        tasks = [self.get_price(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for sym, result in zip(symbols, results):
            if isinstance(result, Exception):
                prices[sym] = {'error': str(result)}
            elif result:
                prices[sym] = result
            else:
                prices[sym] = {'error': 'No data'}
        
        return prices
    
    async def fetch_all_for_analysis(self, symbol: str, timeframes: List[str] = None) -> Dict[str, Any]:
        """
        Fetch all data needed for swarm analysis.
        
        Returns:
        - Current price
        - OHLCV for multiple timeframes
        - 24h stats
        """
        timeframes = timeframes or ['D1', 'H4', 'H1']
        
        # Fetch price
        price_data = await self.get_price(symbol)
        
        # Fetch OHLCV for each timeframe
        ohlcv_data = {}
        for tf in timeframes:
            ohlcv = await self.get_ohlcv(symbol, timeframe=tf, limit=100)
            if ohlcv:
                ohlcv_data[tf] = ohlcv
                # Cache it
                self.blackboard.cache_market_data(symbol, tf, 'ohlcv', ohlcv)
        
        return {
            'symbol': symbol,
            'price': price_data,
            'ohlcv': ohlcv_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_fred_data(self, series_id: str) -> Optional[Dict]:
        """
        Fetch economic data from FRED (Federal Reserve Economic Data).
        
        Common series IDs:
        - GDP: Gross Domestic Product
        - CPIAUCSL: Consumer Price Index (inflation)
        - UNRATE: Unemployment Rate
        - FEDFUNDS: Federal Funds Rate (interest rates)
        - DGS10: 10-Year Treasury Yield
        - DGS2: 2-Year Treasury Yield
        - T10Y2Y: 10Y-2Y Treasury Spread (recession indicator)
        - M2SL: M2 Money Supply
        - PCE: Personal Consumption Expenditures
        - PCEPI: PCE Price Index (Fed's preferred inflation gauge)
        """
        if not self.fred_api_key:
            print("⚠️ FRED API key not set. Set FRED_API_KEY environment variable.")
            return None
        
        try:
            session = await self._get_session()
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json'
            }
            
            async with session.get(self.endpoints['fred']['series'], params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if 'observations' in data and len(data['observations']) > 0:
                        latest = data['observations'][-1]
                        return {
                            'series_id': series_id,
                            'value': float(latest.get('value', 0)),
                            'date': latest.get('date'),
                            'source': 'FRED',
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    print(f"❌ FRED error: {resp.status}")
        except Exception as e:
            print(f"❌ FRED fetch failed: {e}")
        
        return None
    
    async def get_alpha_vantage_quote(self, symbol: str, function: str = 'GLOBAL_QUOTE') -> Optional[Dict]:
        """
        Fetch stock/forex/crypto data from Alpha Vantage.
        
        Functions:
        - GLOBAL_QUOTE: Real-time stock quotes
        - TIME_SERIES_DAILY: Historical daily data
        - TIME_SERIES_WEEKLY: Weekly OHLCV
        - TIME_SERIES_MONTHLY: Monthly OHLCV
        - FX_DAILY: Forex rates
        - DIGITAL_CURRENCY_DAILY: Crypto prices
        - TECHNICAL_INDICATORS: RSI, MACD, SMA, EMA, etc.
        """
        if not self.alpha_vantage_key:
            print("⚠️ Alpha Vantage API key not set. Set ALPHA_VANTAGE_KEY environment variable.")
            return None
        
        try:
            session = await self._get_session()
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            async with session.get(self.endpoints['alpha_vantage']['quote'], params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'symbol': symbol,
                        'function': function,
                        'data': data,
                        'source': 'Alpha Vantage',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    print(f"❌ Alpha Vantage error: {resp.status}")
        except Exception as e:
            print(f"❌ Alpha Vantage fetch failed: {e}")
        
        return None
    
    async def get_macro_indicators(self) -> Dict[str, Optional[Dict]]:
        """
        Fetch key macroeconomic indicators from FRED.
        
        Returns:
        - Interest rates (FEDFUNDS, DGS10, DGS2)
        - Inflation (CPIAUCSL, PCEPI)
        - Yield curve spread (T10Y2Y)
        - Unemployment (UNRATE)
        - Money supply (M2SL)
        """
        indicators = {
            'FEDFUNDS': None,  # Federal Funds Rate
            'DGS10': None,     # 10-Year Treasury Yield
            'DGS2': None,      # 2-Year Treasury Yield
            'T10Y2Y': None,    # 10Y-2Y Spread
            'CPIAUCSL': None,  # CPI (inflation)
            'PCEPI': None,     # PCE Price Index
            'UNRATE': None,    # Unemployment Rate
            'M2SL': None,      # M2 Money Supply
        }
        
        tasks = {k: self.get_fred_data(k) for k in indicators.keys()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for (key, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                indicators[key] = {'error': str(result)}
            elif result:
                indicators[key] = result
            else:
                indicators[key] = None
        
        return indicators
    
    async def get_market_sentiment(self) -> Dict[str, Optional[Dict]]:
        """
        Fetch market sentiment indicators from Alpha Vantage.
        
        Returns:
        - DXY (Dollar Index) - USD strength
        - SPY (S&P 500) - Risk sentiment
        - GLD (Gold) - Safe haven flows
        - VIX (Volatility) - Fear gauge
        """
        if not self.alpha_vantage_key:
            print("⚠️ Alpha Vantage API key not set.")
            return {}
        
        indicators = {
            'DXY': 'UUP',        # Invesco Dollar Bullish ETF (real-time DXY proxy)
            'SPY': 'SPY',        # S&P 500 ETF
            'GLD': 'GLD',        # Gold ETF
            'QQQ': 'QQQ',        # Nasdaq ETF
            'VIX': '^VIX',       # VIX Index
        }
        
        results = {}
        for name, symbol in indicators.items():
            try:
                data = await self.get_alpha_vantage_quote(symbol, 'GLOBAL_QUOTE')
                if data and 'Global Quote' in data.get('data', {}):
                    quote = data['data']['Global Quote']
                    change_str = quote.get('03. percent change', '0')
                    # Handle both string and numeric
                    if isinstance(change_str, (int, float)):
                        change = float(change_str)
                    else:
                        change = float(change_str.replace('%', ''))
                    
                    results[name] = {
                        'symbol': symbol,
                        'price': float(quote.get('05. price', 0)),
                        'change': change,
                        'volume': quote.get('06. volume', 0),
                        'source': 'Alpha Vantage',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    results[name] = None
            except Exception as e:
                print(f"❌ Alpha Vantage {name} fetch failed: {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    async def get_crypto_technicals(self, symbol: str = 'BTC') -> Dict[str, Optional[Dict]]:
        """
        Fetch crypto technical indicators from Alpha Vantage.
        
        Returns:
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - SMA (Simple Moving Average)
        - EMA (Exponential Moving Average)
        """
        if not self.alpha_vantage_key:
            print("⚠️ Alpha Vantage API key not set.")
            return {}
        
        # Map crypto symbols to Alpha Vantage format
        crypto_symbols = {
            'BTC': 'BTCUSD',
            'ETH': 'ETHUSD',
            'SOL': 'SOLUSD',
        }
        
        av_symbol = crypto_symbols.get(symbol.upper(), 'BTCUSD')
        
        technicals = {}
        
        # Fetch RSI
        try:
            rsi_data = await self.get_alpha_vantage_quote(av_symbol, 'RSI')
            if rsi_data and 'Technical Analysis: RSI' in rsi_data.get('data', {}):
                rsi_values = rsi_data['data']['Technical Analysis: RSI']
                latest_rsi = list(rsi_values.values())[0] if rsi_values else None
                technicals['RSI'] = {
                    'value': float(latest_rsi.get('RSI', 50)) if latest_rsi else 50,
                    'signal': 'overbought' if float(latest_rsi.get('RSI', 50)) > 70 else ('oversold' if float(latest_rsi.get('RSI', 50)) < 30 else 'neutral'),
                    'source': 'Alpha Vantage'
                }
        except Exception as e:
            print(f"❌ RSI fetch failed: {e}")
            technicals['RSI'] = {'error': str(e)}
        
        # Fetch MACD
        try:
            macd_data = await self.get_alpha_vantage_quote(av_symbol, 'MACD')
            if macd_data and 'Technical Analysis: MACD' in macd_data.get('data', {}):
                macd_values = macd_data['data']['Technical Analysis: MACD']
                latest_macd = list(macd_values.values())[0] if macd_values else None
                if latest_macd:
                    technicals['MACD'] = {
                        'macd': float(latest_macd.get('MACD', 0)),
                        'signal': float(latest_macd.get('MACD_Signal', 0)),
                        'histogram': float(latest_macd.get('MACD_Hist', 0)),
                        'signal_interpretation': 'bullish' if float(latest_macd.get('MACD', 0)) > float(latest_macd.get('MACD_Signal', 0)) else 'bearish',
                        'source': 'Alpha Vantage'
                    }
        except Exception as e:
            print(f"❌ MACD fetch failed: {e}")
            technicals['MACD'] = {'error': str(e)}
        
        # Fetch SMA (50-day)
        try:
            sma_data = await self.get_alpha_vantage_quote(av_symbol, 'SMA')
            if sma_data and 'Technical Analysis: SMA' in sma_data.get('data', {}):
                sma_values = sma_data['data']['Technical Analysis: SMA']
                latest_sma = list(sma_values.values())[0] if sma_values else None
                technicals['SMA50'] = {
                    'value': float(latest_sma.get('SMA', 0)) if latest_sma else 0,
                    'period': 50,
                    'source': 'Alpha Vantage'
                }
        except Exception as e:
            print(f"❌ SMA fetch failed: {e}")
            technicals['SMA50'] = {'error': str(e)}
        
        return technicals


# ============================================================================
# CLI Test
# ============================================================================

async def main():
    fetcher = DataFetcher()
    
    print("📊 Fetching live crypto prices...\n")
    
    # Test single price
    btc = await fetcher.get_price('BTCUSD')
    print(f"BTC/USD: ${btc['price']:,.2f} ({btc['change_24h']:+.2f}%)") if btc else print("❌ Failed to fetch BTC")
    
    eth = await fetcher.get_price('ETHUSD')
    print(f"ETH/USD: ${eth['price']:,.2f} ({eth['change_24h']:+.2f}%)") if eth else print("❌ Failed to fetch ETH")
    
    sol = await fetcher.get_price('SOLUSD')
    print(f"SOL/USD: ${sol['price']:,.2f} ({sol['change_24h']:+.2f}%)") if sol else print("❌ Failed to fetch SOL")
    
    # Test OHLCV
    print("\n📈 Fetching BTC OHLCV (H4)...")
    ohlcv = await fetcher.get_ohlcv('BTCUSD', timeframe='H4', limit=10)
    if ohlcv:
        print(f"Got {len(ohlcv)} candles")
        latest = ohlcv[-1]
        print(f"Latest: O={latest[1]:.2f} H={latest[2]:.2f} L={latest[3]:.2f} C={latest[4]:.2f}")
    
    await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
