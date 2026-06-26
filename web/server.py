"""
Web Server - Flask API and Dashboard for Swarm Trader
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API keys from env file at startup
env_file = Path(__file__).parent.parent / 'state' / 'api_keys.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.startswith('export '):
                line = line[7:]
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                value = value.strip('"\'')
                os.environ[key] = value
    print(f"✅ Loaded API keys from {env_file}")

from orchestrator import SwarmOrchestrator
from data.fetcher import DataFetcher
from core.blackboard import get_blackboard


app = Flask(__name__)
CORS(app)

orchestrator = None
fetcher = None


def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        orchestrator = SwarmOrchestrator()
    return orchestrator


def get_fetcher():
    global fetcher
    if fetcher is None:
        fetcher = DataFetcher()
    return fetcher


@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('dashboard.html')


@app.route('/macro')
def macro_dashboard():
    """Serve the institutional macro dashboard"""
    return render_template('macro_dashboard.html')


@app.route('/api/status')
def get_status():
    """Get current swarm status"""
    try:
        orch = get_orchestrator()
        status = orch.get_swarm_status()
        
        # Get latest prices
        fetcher = get_fetcher()
        
        return jsonify({
            'status': 'running' if status.get('orchestrator_running') else 'stopped',
            'timestamp': datetime.now().isoformat(),
            'portfolio': {
                'capital': 100000,  # Would get from actual broker
                'pnl': 5230,
                'return': 5.23,
                'winRate': 68,
                'maxDrawdown': 3.2
            },
            'agents': [
                {'name': 'Liquidity', 'confidence': 0.65, 'active': True},
                {'name': 'Structure', 'confidence': 0.60, 'active': True},
                {'name': 'Macro', 'confidence': 0.55, 'active': True},
                {'name': 'Risk', 'confidence': 0.90, 'active': True},
                {'name': 'Consensus', 'confidence': 0.0, 'active': True}
            ],
            'signals': get_latest_signals(),
            'prices': {
                'BTCUSD': {'price': 95000, 'change': 2.5},
                'ETHUSD': {'price': 3500, 'change': 1.8},
                'SOLUSD': {'price': 200, 'change': -0.5}
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
async def run_analysis():
    """Run swarm analysis for a symbol"""
    try:
        data = request.json
        symbol = data.get('symbol', 'BTCUSD')
        
        orch = get_orchestrator()
        result = await orch.run_full_analysis(symbol)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signals')
def get_signals():
    """Get latest signals"""
    signals = get_latest_signals()
    return jsonify({'signals': signals})


@app.route('/api/prices')
def get_prices():
    """Get current prices"""
    try:
        fetcher = get_fetcher()
        
        async def fetch():
            prices = await fetcher.get_multi_symbol_prices(['BTCUSD', 'ETHUSD', 'SOLUSD'])
            return prices
        
        prices = asyncio.run(fetch())
        return jsonify({'prices': prices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtest', methods=['POST'])
async def run_backtest():
    """Run backtest"""
    try:
        from core.backtester import Backtester
        
        data = request.json
        symbol = data.get('symbol', 'BTCUSD')
        
        backtester = Backtester(initial_capital=data.get('capital', 100000))
        
        # Generate mock data for now
        import random
        ohlcv = []
        base_price = 95000
        for i in range(500):
            open_p = base_price * (1 + random.uniform(-0.02, 0.02))
            high = open_p * (1 + random.uniform(0, 0.03))
            low = open_p * (1 - random.uniform(0, 0.03))
            close = random.uniform(low, high)
            ohlcv.append([0, open_p, high, low, close, 0])
        
        metrics = await backtester.run_backtest(symbol, ohlcv)
        
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents')
def get_agents():
    """Get agent performance stats"""
    try:
        orch = get_orchestrator()
        status = orch.get_swarm_status()
        return jsonify({'agents': status.get('agents', {})})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/macro')
def get_macro_data():
    """Get live macroeconomic data dashboard"""
    try:
        import asyncio
        from data.fetcher import DataFetcher
        
        fetcher = get_fetcher()
        
        async def fetch_macro():
            # Get DXY from Alpha Vantage
            dxy_data = await fetcher.get_alpha_vantage_quote('UUP', 'GLOBAL_QUOTE')
            dxy_value = None
            dxy_date = None
            
            if dxy_data and 'Global Quote' in dxy_data.get('data', {}):
                quote = dxy_data['data']['Global Quote']
                dxy_value = float(quote.get('05. price', 0))
                dxy_date = quote.get('07. latest trading day', 'N/A')
            
            # Fetch all FRED data
            indicators = {
                'DGS10': '10Y Treasury Yield',
                'DGS2': '2Y Treasury Yield',
                'DFII10': 'Real Yields (TIPS)',
                'T10Y2Y': 'Yield Curve (10Y-2Y)',
                'FEDFUNDS': 'Fed Funds Rate',
                'WALCL': 'Fed Balance Sheet',
                'M2SL': 'M2 Money Supply',
                'RRPONTSYD': 'Reverse Repo (RRP)',
                'WTREGEN': 'Treasury General (TGA)',
                'CPIAUCSL': 'CPI',
                'VIXCLS': 'VIX',
                'PAYEMS': 'Non-Farm Payrolls',
                'UNRATE': 'Unemployment Rate',
            }
            
            results = {}
            for code, name in indicators.items():
                try:
                    data = await fetcher.get_fred_data(code)
                    if data and 'value' in data:
                        results[name] = {
                            'value': data['value'],
                            'date': data['date'],
                            'code': code
                        }
                except Exception as e:
                    print(f"Error fetching {code}: {e}")
            
            return dxy_value, dxy_date, results
        
        dxy_value, dxy_date, fred_data = asyncio.run(fetch_macro())
        
        # Calculate macro score
        score = 0
        if dxy_value and (dxy_value * 4) < 110: score += 1
        tips = fred_data.get('Real Yields (TIPS)', {})
        if tips.get('value', 999) < 1.5: score += 1
        yc = fred_data.get('Yield Curve (10Y-2Y)', {})
        if yc.get('value', 0) > 0.3: score += 1
        vix = fred_data.get('VIX', {})
        if vix.get('value', 100) < 20: score += 1
        m2 = fred_data.get('M2 Money Supply', {})
        if m2.get('value', 0) > 21000: score += 1
        
        # Determine bias
        if score >= 4:
            bias = 'BULLISH'
            bias_color = 'green'
        elif score >= 2:
            bias = 'NEUTRAL'
            bias_color = 'yellow'
        else:
            bias = 'BEARISH'
            bias_color = 'red'
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'dxy': {
                'value': dxy_value,
                'date': dxy_date,
                'index_equiv': round(dxy_value * 4) if dxy_value else None
            },
            'fred_data': fred_data,
            'macro_score': f'{score}/5',
            'trading_bias': bias,
            'bias_color': bias_color,
            'analysis': {
                'dollar_status': 'STRONG' if dxy_value and dxy_value > 29 else ('WEAK' if dxy_value and dxy_value < 24 else 'NEUTRAL'),
                'real_yields_status': 'HIGH' if tips.get('value', 0) > 2.0 else ('LOW' if tips.get('value', 0) < 0 else 'NEUTRAL'),
                'liquidity_status': 'SUPPORTIVE' if m2.get('value', 0) > 21000 else 'TIGHT',
                'fed_stance': 'HAWKISH' if fred_data.get('Fed Funds Rate', {}).get('value', 0) > 4.5 else ('DOVISH' if fred_data.get('Fed Funds Rate', {}).get('value', 0) < 3.0 else 'NEUTRAL')
            }
        })
    except Exception as e:
        import traceback
        print(f"Macro API error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


def get_latest_signals():
    """Get latest signals from state file"""
    signals_file = Path(__file__).parent.parent / "state" / "signals.json"
    
    if signals_file.exists():
        with open(signals_file) as f:
            data = json.load(f)
            return data.get('signals', [])
    
    return []


if __name__ == '__main__':
    print("🌐 Starting Swarm Trader Web Server...")
    print("📊 Dashboard: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/status")
    app.run(host='0.0.0.0', port=5000, debug=True)
