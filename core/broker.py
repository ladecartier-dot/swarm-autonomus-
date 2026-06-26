"""
Broker Integration - Execute trades on Binance/Bybit
Supports: Binance Spot/Futures, Bybit Futures
"""
import hashlib
import hmac
import time
from typing import Dict, Optional, List
from datetime import datetime
import aiohttp
import json


class BinanceClient:
    """
    Binance API client for spot and futures trading.
    
    Setup:
    1. Create API key on Binance
    2. Enable spot & margin trading (or futures)
    3. Set IP whitelist (recommended)
    4. Add keys to state/binance_config.json
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        self.base_url = 'https://testnet.binance.vision' if testnet else 'https://api.binance.com'
        self.futures_url = 'https://testnet.binancefuture.com' if testnet else 'https://fapi.binance.com'
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _sign(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_timestamp(self) -> int:
        return int(time.time() * 1000)
    
    async def _request(self, method: str, url: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make API request"""
        session = await self._get_session()
        
        if params is None:
            params = {}
        
        if signed:
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._sign(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        async with session.request(method, url, params=params, headers=headers) as resp:
            result = await resp.json()
            return result
    
    async def get_balance(self, asset: str = 'USDT') -> Dict:
        """Get account balance"""
        url = f"{self.base_url}/api/v3/account"
        result = await self._request('GET', url, signed=True)
        
        if 'balances' in result:
            for bal in result['balances']:
                if bal['asset'] == asset:
                    return {
                        'asset': asset,
                        'free': float(bal['free']),
                        'locked': float(bal['locked']),
                        'total': float(bal['free']) + float(bal['locked'])
                    }
        
        return {'error': 'Asset not found', 'raw': result}
    
    async def get_price(self, symbol: str) -> float:
        """Get current price"""
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {'symbol': symbol.replace('USD', 'USDT')}
        result = await self._request('GET', url, params=params)
        
        return float(result.get('price', 0))
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = 'MARKET',
        quantity: float = None,
        quote_qty: float = None,
        price: float = None,
        stop_price: float = None
    ) -> Dict:
        """
        Place an order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'STOP_LOSS_LIMIT', etc.
            quantity: Amount of base asset
            quote_qty: Amount of quote asset (for MARKET orders)
            price: Limit price
            stop_price: Stop price for stop orders
        """
        url = f"{self.base_url}/api/v3/order"
        
        params = {
            'symbol': symbol.replace('USD', 'USDT'),
            'side': side,
            'type': order_type,
            'recvWindow': 5000
        }
        
        if quantity:
            params['quantity'] = quantity
        if quote_qty:
            params['quoteOrderQty'] = quote_qty
        if price:
            params['price'] = price
        if stop_price:
            params['stopPrice'] = stop_price
        
        result = await self._request('POST', url, params=params, signed=True)
        return result
    
    async def place_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        limit_price: float = None
    ) -> Dict:
        """Place a stop-loss order"""
        order_type = 'STOP_LOSS_LIMIT' if limit_price else 'STOP_LOSS'
        return await self.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=limit_price,
            stop_price=stop_price
        )
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        url = f"{self.base_url}/api/v3/order"
        params = {
            'symbol': symbol.replace('USD', 'USDT'),
            'orderId': order_id
        }
        return await self._request('DELETE', url, params=params, signed=True)
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        url = f"{self.base_url}/api/v3/openOrders"
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('USD', 'USDT')
        
        return await self._request('GET', url, params=params, signed=True)
    
    async def execute_signal(self, signal: Dict) -> Dict:
        """
        Execute a swarm signal.
        
        Places entry order + stop loss + take profit.
        """
        symbol = signal.get('symbol', 'BTCUSDT')
        side = signal.get('side', 'LONG')
        entry = signal.get('entry')
        sl = signal.get('stop_loss')
        tp = signal.get('take_profit')
        size = signal.get('position_size')
        
        results = {
            'entry': None,
            'stop_loss': None,
            'take_profit': None,
            'error': None
        }
        
        try:
            # Place entry order
            binance_side = 'BUY' if side == 'LONG' else 'SELL'
            entry_result = await self.place_order(
                symbol=symbol,
                side=binance_side,
                order_type='MARKET',
                quantity=size
            )
            
            if 'orderId' in entry_result:
                results['entry'] = entry_result
                
                # Place stop loss
                sl_side = 'SELL' if side == 'LONG' else 'BUY'
                sl_result = await self.place_stop_loss(
                    symbol=symbol,
                    side=sl_side,
                    quantity=size,
                    stop_price=sl,
                    limit_price=sl * 0.999 if side == 'LONG' else sl * 1.001
                )
                results['stop_loss'] = sl_result
                
                # Place take profit
                tp_side = 'SELL' if side == 'LONG' else 'BUY'
                tp_result = await self.place_stop_loss(
                    symbol=symbol,
                    side=tp_side,
                    quantity=size,
                    stop_price=tp,
                    limit_price=tp * 1.001 if side == 'LONG' else tp * 0.999
                )
                results['take_profit'] = tp_result
            else:
                results['error'] = entry_result
            
        except Exception as e:
            results['error'] = str(e)
        
        return results


class BybitClient:
    """
    Bybit V5 API client for futures trading.
    
    Similar structure to Binance, adapted for Bybit's API.
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        self.base_url = 'https://api-testnet.bybit.com' if testnet else 'https://api.bybit.com'
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _sign(self, params: str, timestamp: str, recv_window: str = '5000') -> str:
        """Generate HMAC SHA256 signature for Bybit"""
        param_str = timestamp + self.api_key + recv_window + params
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make signed request to Bybit V5"""
        session = await self._get_session()
        
        timestamp = str(int(time.time() * 1000))
        recv_window = '5000'
        
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            'X-BAPI-API-KEY': self.api_key,
            'X-BAPI-SIGN': self._sign(json.dumps(params) if params else '', timestamp, recv_window),
            'X-BAPI-SIGN-TYPE': '2',
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'Content-Type': 'application/json'
        }
        
        async with session.request(method, url, json=params, headers=headers) as resp:
            result = await resp.json()
            return result
    
    async def get_balance(self, coin: str = 'USDT') -> Dict:
        """Get wallet balance"""
        result = await self._request('GET', '/v5/account/wallet-balance', {'accountType': 'CONTRACT'})
        
        if result.get('retCode') == 0:
            for coin_bal in result['result']['list'][0]['coin']:
                if coin_bal['coin'] == coin:
                    return {
                        'asset': coin,
                        'free': float(coin_bal['availableToWithdraw']),
                        'total': float(coin_bal['walletBalance'])
                    }
        
        return {'error': 'Failed to get balance', 'raw': result}
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = 'Market',
        qty: float = None,
        price: float = None,
        stop_loss: float = None,
        take_profit: float = None
    ) -> Dict:
        """Place an order on Bybit"""
        endpoint = '/v5/order/create'
        
        params = {
            'category': 'linear',
            'symbol': symbol,
            'side': side,
            'orderType': order_type,
            'qty': str(qty),
            'timeInForce': 'IOC' if order_type == 'Market' else 'GTC'
        }
        
        if price and order_type != 'Market':
            params['price'] = str(price)
        if stop_loss:
            params['stopLoss'] = str(stop_loss)
        if take_profit:
            params['takeProfit'] = str(take_profit)
        
        return await self._request('POST', endpoint, params)
    
    async def execute_signal(self, signal: Dict) -> Dict:
        """Execute a swarm signal on Bybit"""
        symbol = signal.get('symbol', 'BTCUSDT').replace('USD', 'USDT')
        side = 'Buy' if signal.get('side') == 'LONG' else 'Sell'
        qty = signal.get('position_size')
        sl = signal.get('stop_loss')
        tp = signal.get('take_profit')
        
        result = await self.place_order(
            symbol=symbol,
            side=side,
            order_type='Market',
            qty=qty,
            stop_loss=sl,
            take_profit=tp
        )
        
        return {
            'order': result,
            'success': result.get('retCode') == 0,
            'error': result.get('retMsg') if result.get('retCode') != 0 else None
        }


def get_broker_client(broker: str = 'binance', testnet: bool = True):
    """
    Get broker client from config.
    
    Config file: state/broker_config.json
    {
        "broker": "binance",
        "binance": {
            "api_key": "...",
            "api_secret": "..."
        },
        "bybit": {
            "api_key": "...",
            "api_secret": "..."
        }
    }
    """
    from pathlib import Path
    
    config_file = Path(__file__).parent.parent / "state" / "broker_config.json"
    
    if not config_file.exists():
        print("⚠️ Broker config not found. Create state/broker_config.json")
        return None
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        if broker == 'binance':
            creds = config.get('binance', {})
            return BinanceClient(
                api_key=creds.get('api_key', ''),
                api_secret=creds.get('api_secret', ''),
                testnet=testnet
            )
        elif broker == 'bybit':
            creds = config.get('bybit', {})
            return BybitClient(
                api_key=creds.get('api_key', ''),
                api_secret=creds.get('api_secret', ''),
                testnet=testnet
            )
    except Exception as e:
        print(f"❌ Failed to load broker config: {e}")
    
    return None


if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test with mock credentials (will fail but shows structure)
        client = BinanceClient(api_key='test', api_secret='test', testnet=True)
        
        try:
            balance = await client.get_balance('USDT')
            print(f"Balance: {balance}")
        except Exception as e:
            print(f"Expected error (mock creds): {e}")
        
        await client.close()
    
    asyncio.run(test())
