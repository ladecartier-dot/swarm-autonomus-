#!/usr/bin/env python3
"""
Institutional Macro Dashboard
Fetches and displays key macroeconomic indicators from FRED
"""
import asyncio
import sys
sys.path.insert(0, '/mnt/data/hermes/workspace/swarm-trader')

from data.fetcher import DataFetcher


async def main():
    fetcher = DataFetcher()
    
    print('='*80)
    print('🏛️  INSTITUTIONAL MACRO DASHBOARD - LIVE FRED DATA')
    print('='*80)
    print()
    
    # Get DXY from Alpha Vantage first (UUP ETF as proxy)
    print('📊 Fetching DXY from Alpha Vantage (UUP ETF)...')
    dxy_data = await fetcher.get_alpha_vantage_quote('UUP', 'GLOBAL_QUOTE')
    dxy_value = None
    dxy_date = None
    
    if dxy_data and 'Global Quote' in dxy_data.get('data', {}):
        quote = dxy_data['data']['Global Quote']
        try:
            dxy_value = float(quote.get('05. price', 0))
            dxy_date = quote.get('07. latest trading day', 'N/A')
            print(f'  ✅ DXY (UUP): ${dxy_value:.2f} ({dxy_date})')
        except:
            print('  ⚠️  DXY fetch failed, will use fallback')
    else:
        print('  ⚠️  Alpha Vantage rate limited, using FRED fallback (2019 data)')
    
    print()
    
    # All other indicators from FRED
    # FRED units: WALCL/RRPONTSYD/WTREGEN = Millions, M2SL = Billions
    indicators = {
        # Dollar & Yields
        ('📈 10Y Treasury Yield', 'DGS10', 'percent'),
        ('📉 2Y Treasury Yield', 'DGS2', 'percent'),
        ('💎 Real Yields (TIPS 10Y)', 'DFII10', 'percent'),
        ('📊 Yield Curve (10Y-2Y)', 'T10Y2Y', 'percent'),
        
        # Fed & Liquidity
        ('🏦 Fed Funds Rate', 'FEDFUNDS', 'percent'),
        ('🏛️ Fed Balance Sheet', 'WALCL', 'millions'),
        ('💵 M2 Money Supply', 'M2SL', 'billions_fred'),  # Special: FRED reports in billions
        ('📦 Reverse Repo (RRP)', 'RRPONTSYD', 'millions'),
        ('🏦 Treasury General (TGA)', 'WTREGEN', 'millions'),
        
        # Inflation
        ('🏷️ CPI (Consumer Prices)', 'CPIAUCSL', 'index'),
        ('🏭 PPI (Producer Prices)', 'PPIFGS', 'index'),
        
        # Markets
        ('😰 VIX (Volatility)', 'VIXCLS', 'percent'),
        
        # Labor
        ('👷 Non-Farm Payrolls', 'PAYEMS', 'thousands'),
        ('😰 Unemployment Rate', 'UNRATE', 'percent'),
    }
    
    results = {}
    
    # Add DXY manually
    if dxy_value:
        results['🇺🇸 DXY (Dollar Index)'] = {
            'value': dxy_value,
            'date': dxy_date,
            'type': 'dxy_uup'
        }
    
    print('📊 Fetching FRED Economic Data...\n')
    
    for name, code, fmt_type in indicators:
        data = await fetcher.get_fred_data(code)
        if data and 'value' in data:
            results[name] = {
                'value': data['value'],
                'date': data['date'],
                'type': fmt_type
            }
        else:
            results[name] = None
    
    await fetcher.close()
    
    # Display with proper formatting
    print('='*80)
    print(f'{"INDICATOR":<35} {"VALUE":>15} {"DATE":>12}')
    print('='*80)
    
    for name, code, fmt_type in indicators:
        data = results.get(name)
        if data:
            val = data['value']
            date = data['date']
            
            # Format based on type
            if fmt_type == 'percent':
                formatted = f'{val:>14.2f}%'
            elif fmt_type == 'dxy_uup':
                # DXY from UUP ETF
                formatted = f'{val:>14.2f}'
            elif fmt_type == 'billions':
                # FRED reports in billions
                if val > 1000:
                    formatted = f'${val/1000:>12.2f}T'
                else:
                    formatted = f'${val:>12.1f}B'
            elif fmt_type == 'billions_fred':
                # M2SL: FRED reports in billions, convert to trillions for display
                formatted = f'${val/1000:>12.2f}T'
            elif fmt_type == 'millions':
                # FRED reports in millions
                if val > 1000000:
                    formatted = f'${val/1000000:>12.2f}T'
                elif val > 1000:
                    formatted = f'${val/1000:>12.1f}B'
                else:
                    formatted = f'${val:>12.0f}M'
            elif fmt_type == 'thousands':
                formatted = f'{val/1000:>14.1f}K'
            else:  # index
                formatted = f'{val:>14.1f}'
            
            # Color coding (using emoji)
            status = '✅'
            print(f'{status} {name:<32} {formatted}  {date}')
        else:
            print(f'❌ {name:<32} {"N/A":>14}  (failed)')
    
    print('='*80)
    print()
    
    # Analysis
    print('📈 MACRO ANALYSIS & TRADING IMPLICATIONS')
    print('='*80)
    print()
    
    # Dollar analysis (from UUP ETF)
    dxy = results.get('🇺🇸 DXY (Dollar Index)')
    if dxy:
        val = dxy['value']
        # UUP ETF typically trades around $25-35 (1/10 of DXY index scale)
        # DXY index 100-130 ≈ UUP $25-35
        dxy_index_equiv = val * 4  # Rough conversion to DXY index scale
        
        if dxy_index_equiv > 115 or val > 29:
            print('🇺🇸  DOLLAR: STRONG')
            print(f'    UUP: ${val:.2f} (≈ DXY {dxy_index_equiv:.0f})')
            print('    → Headwind for BTC/crypto (inverse correlation)')
            print('    → Favor USD-long positions')
        elif dxy_index_equiv < 95 or val < 24:
            print('🇺🇸  DOLLAR: WEAK')
            print(f'    UUP: ${val:.2f} (≈ DXY {dxy_index_equiv:.0f})')
            print('    → Tailwind for BTC/crypto')
            print('    → Favor risk assets')
        else:
            print('🇺🇸  DOLLAR: NEUTRAL')
            print(f'    UUP: ${val:.2f} (≈ DXY {dxy_index_equiv:.0f})')
            print('    → No major USD-driven pressure')
    
    # Real yields
    tips = results.get('💎 Real Yields (TIPS 10Y)')
    if tips:
        val = tips['value']
        if val > 2.0:
            print(f'\n📉  REAL YIELDS: HIGH ({val:.2f}%)')
            print('    → Bearish for duration assets (crypto, growth stocks)')
            print('    → Bonds attractive vs. zero-yield assets')
        elif val < 0:
            print(f'\n📈  REAL YIELDS: NEGATIVE ({val:.2f}%)')
            print('    → Bullish for crypto/gold/hard assets')
            print('    → TINA (There Is No Alternative) trade')
        else:
            print(f'\n📊  REAL YIELDS: NEUTRAL ({val:.2f}%)')
    
    # Yield curve
    yc = results.get('📊 Yield Curve (10Y-2Y)')
    if yc:
        val = yc['value']
        if val < 0:
            print(f'\n🔻  YIELD CURVE: INVERTED ({val:.2f}%)')
            print('    → Recession risk HIGH')
            print('    → Historically accurate predictor')
        elif val < 0.5:
            print(f'\n🔶  YIELD CURVE: FLAT ({val:.2f}%)')
            print('    → Recession risk MODERATE')
            print('    → Economic slowdown warning')
        else:
            print(f'\n🔺  YIELD CURVE: NORMAL ({val:.2f}%)')
            print('    → Healthy growth environment')
    
    # VIX
    vix = results.get('😰 VIX (Volatility)')
    if vix:
        val = vix['value']
        if val > 25:
            print(f'\n😰  VIX: ELEVATED ({val:.1f})')
            print('    → Fear in markets')
            print('    → Potential capitulation or buying opportunity')
        elif val < 15:
            print(f'\n😌  VIX: COMPLACENT ({val:.1f})')
            print('    → Low fear, potential top signal')
            print('    → Risk of complacency')
        else:
            print(f'\n📊  VIX: NORMAL ({val:.1f})')
            print('    → Standard volatility regime')
    
    # Liquidity conditions
    print()
    m2 = results.get('💵 M2 Money Supply')
    fed_bs = results.get('🏛️ Fed Balance Sheet')
    rrp = results.get('📦 Reverse Repo (RRP)')
    
    print('💧  LIQUIDITY CONDITIONS:')
    if m2 and fed_bs:
        # M2 is in billions (FRED), Fed BS is in millions
        m2_val = m2['value'] / 1000  # Billions to trillions
        fed_val = fed_bs['value'] / 1000000  # Millions to trillions
        
        print(f'      M2 Supply:       ${m2_val:.2f}T')
        print(f'      Fed Balance:     ${fed_val:.2f}T')
        if rrp:
            rrp_val = rrp['value'] / 1000000  # Millions to trillions
            print(f'      RRP Outstanding: ${rrp_val:.2f}T')
        
        # Simple liquidity assessment
        if m2_val > 21 and fed_val > 6:
            print('      → 🟢 LIQUIDITY: SUPPORTIVE (bullish for risk assets)')
        elif m2_val < 20 and fed_val < 7:
            print('      → 🔴 LIQUIDITY: TIGHT (bearish for risk assets)')
        else:
            print('      → 🟡 LIQUIDITY: NEUTRAL')
    
    # Fed policy stance
    print()
    fed_funds = results.get('🏦 Fed Funds Rate')
    if fed_funds:
        val = fed_funds['value']
        if val > 5.0:
            stance = 'VERY HAWKISH'
        elif val > 4.0:
            stance = 'HAWKISH'
        elif val > 3.0:
            stance = 'NEUTRAL'
        elif val > 2.0:
            stance = 'DOVISH'
        else:
            stance = 'VERY DOVISH'
        
        print('🏦  FED POLICY:')
        print(f'      Fed Funds: {val:.2f}% → {stance}')
        
        if stance in ['HAWKISH', 'VERY HAWKISH']:
            print('      → Tightening financial conditions')
            print('      → Headwind for risk assets')
        elif stance in ['DOVISH', 'VERY DOVISH']:
            print('      → Accommodative policy')
            print('      → Tailwind for risk assets')
        else:
            print('      → On hold, data-dependent')
    
    # Inflation
    print()
    cpi = results.get('🏷️ CPI (Consumer Prices)')
    ppi = results.get('🏭 PPI (Producer Prices)')
    if cpi:
        print('🏷️  INFLATION:')
        print(f'      CPI Index: {cpi["value"]:.1f}')
        # Would need historical data for YoY calculation
    if ppi:
        print(f'      PPI Index: {ppi["value"]:.1f}')
    
    # Labor market
    print()
    nfp = results.get('👷 Non-Farm Payrolls')
    unrate = results.get('😰 Unemployment Rate')
    if nfp or unrate:
        print('👷  LABOR MARKET:')
        if nfp:
            print(f'      Non-Farm Payrolls: {nfp["value"]/1000:.1f}K')
        if unrate:
            print(f'      Unemployment Rate: {unrate["value"]:.1f}%')
    
    # Overall trading bias
    print()
    print('='*80)
    print('🎯 TRADING BIAS (Macro Score)')
    print('='*80)
    
    score = 0
    max_score = 5
    
    # Scoring system (using raw values)
    # DXY from UUP: $25-35 range (multiply by 4 for DXY index equivalent)
    if dxy and (dxy['value'] * 4) < 110: score += 1  # Weak dollar = bullish
    if tips and tips['value'] < 1.5: score += 1  # Low real yields = bullish
    if yc and yc['value'] > 0.3: score += 1  # Normal yield curve = bullish
    if vix and vix['value'] < 20: score += 1  # Low VIX = bullish
    if m2 and m2['value'] > 21000: score += 1  # M2 > 21T (in billions) = bullish
    
    print()
    print(f'  Score: {score}/{max_score}')
    print()
    
    if score >= 4:
        print('  🐂 BULLISH BIAS')
        print('  → Macro tailwinds for risk assets')
        print('  → Favor long positions, higher conviction')
        print('  → Crypto/equities supported by liquidity')
    elif score >= 2:
        print('  🟰 NEUTRAL BIAS')
        print('  → Mixed macro signals')
        print('  → Trade technicals (SMC, liquidity levels)')
        print('  → Stock-picking over beta exposure')
    else:
        print('  🐻 BEARISH BIAS')
        print('  → Macro headwinds for risk assets')
        print('  → Favor shorts, defensive positioning')
        print('  → USD, gold, bonds over crypto/equities')
    
    print()
    print('='*80)
    print(f'Data Source: FRED (Federal Reserve Economic Data)')
    print(f'Timestamp: {__import__("datetime").datetime.now().isoformat()}')
    print('='*80)


if __name__ == '__main__':
    asyncio.run(main())
