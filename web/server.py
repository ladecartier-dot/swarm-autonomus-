"""
Swarm Trader Macro Dashboard - Production Server
Standalone version for Render/Railway deployment
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import asyncio
import os
from datetime import datetime
import aiohttp

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# API Keys from environment
FRED_API_KEY = os.environ.get('FRED_API_KEY', '')
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY', '')

# Cache for macro data (refresh every 5 minutes)
macro_cache = None
cache_timestamp = None

async def fetch_fred_data(session, series_id):
    """Fetch data from FRED API"""
    if not FRED_API_KEY:
        return None
    
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&limit=1"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('observations'):
                    obs = data['observations'][0]
                    return {
                        'value': float(obs['value']) if obs['value'] else None,
                        'date': obs['date']
                    }
    except Exception as e:
        print(f"FRED error {series_id}: {e}")
    
    return None


async def fetch_alpha_vantage(session, symbol, function='GLOBAL_QUOTE'):
    """Fetch data from Alpha Vantage"""
    if not ALPHA_VANTAGE_KEY:
        return None
    
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Alpha Vantage error: {e}")
    
    return None


async def fetch_all_macro():
    """Fetch all macroeconomic data"""
    async with aiohttp.ClientSession() as session:
        # Fetch DXY (UUP ETF as proxy)
        dxy_data = await fetch_alpha_vantage(session, 'UUP', 'GLOBAL_QUOTE')
        dxy_value = None
        dxy_date = None
        
        if dxy_data and 'Global Quote' in dxy_data:
            quote = dxy_data['Global Quote']
            if '5. price' in quote:
                dxy_value = float(quote['5. price'])
                dxy_date = quote.get('7. latest trading day', 'N/A')
        
        # Fetch FRED indicators
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
        
        fred_data = {}
        tasks = {code: fetch_fred_data(session, code) for code in indicators.keys()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for (code, name), result in zip(tasks.items(), results):
            if isinstance(result, dict) and result:
                fred_data[name] = {
                    'value': result['value'],
                    'date': result['date'],
                    'code': code
                }
        
        return dxy_value, dxy_date, fred_data


def calculate_macro_score(dxy_value, fred_data):
    """Calculate macro trading bias score (0-5)"""
    score = 0
    
    # DXY < 110 (weak dollar = bullish for crypto)
    if dxy_value and (dxy_value * 4) < 110:
        score += 1
    
    # Real Yields < 1.5% (low yields favor risk assets)
    tips = fred_data.get('Real Yields (TIPS)', {})
    if tips.get('value', 999) < 1.5:
        score += 1
    
    # Yield Curve > 0.3% (not inverted = low recession risk)
    yc = fred_data.get('Yield Curve (10Y-2Y)', {})
    if yc.get('value', 0) > 0.3:
        score += 1
    
    # VIX < 20 (normal volatility = risk-on)
    vix = fred_data.get('VIX', {})
    if vix.get('value', 100) < 20:
        score += 1
    
    # M2 > $21T (ample liquidity)
    m2 = fred_data.get('M2 Money Supply', {})
    if m2.get('value', 0) > 21000:
        score += 1
    
    return score


@app.route('/')
def index():
    return render_template('macro_dashboard.html')


@app.route('/macro')
def macro_dashboard():
    return render_template('macro_dashboard.html')


@app.route('/api/macro')
async def get_macro_data():
    """Get live macroeconomic data"""
    global macro_cache, cache_timestamp
    
    # Check cache (5 minute TTL)
    now = datetime.now()
    if macro_cache and cache_timestamp and (now - cache_timestamp).seconds < 300:
        return jsonify(macro_cache)
    
    try:
        # Fetch data
        dxy_value, dxy_date, fred_data = await fetch_all_macro()
        
        # Calculate score
        score = calculate_macro_score(dxy_value, fred_data)
        
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
        
        # Analysis
        tips = fred_data.get('Real Yields (TIPS)', {})
        m2 = fred_data.get('M2 Money Supply', {})
        fed_funds = fred_data.get('Fed Funds Rate', {})
        
        macro_data = {
            'timestamp': now.isoformat(),
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
                'fed_stance': 'HAWKISH' if fed_funds.get('value', 0) > 4.5 else ('DOVISH' if fed_funds.get('value', 0) < 3.0 else 'NEUTRAL')
            }
        }
        
        # Update cache
        macro_cache = macro_data
        cache_timestamp = now
        
        return jsonify(macro_data)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to fetch macro data',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'api_keys_configured': bool(FRED_API_KEY and ALPHA_VANTAGE_KEY)
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Macro Dashboard on port {port}")
    print(f"📊 Dashboard: /macro")
    print(f"📡 API: /api/macro")
    print(f"🏥 Health: /health")
    app.run(host='0.0.0.0', port=port, debug=False)
