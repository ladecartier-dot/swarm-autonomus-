#!/usr/bin/env python3
"""
Cron Scheduler - Set up automated daily data fetching and signal generation
Generates crontab entries and installs them
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def get_python_path():
    """Get current Python interpreter path"""
    return sys.executable


def get_project_path():
    """Get project root path"""
    return Path(__file__).parent.parent.resolve()


def generate_crontab():
    """Generate crontab entries"""
    python = get_python_path()
    project = get_project_path()
    
    crontab = f"""# Swarm Trader - Automated Daily Data Fetching
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Project: {project}

# ============================================
# DAILY DATA FETCHING
# ============================================

# Fetch daily market data at 00:05 UTC (after daily candle close)
5 0 * * * cd {project} && {python} data/daily_fetch.py >> logs/daily_data.log 2>&1

# Fetch H4 data every 4 hours (at 00:05, 04:05, 08:05, etc.)
5 */4 * * * cd {project} && {python} data/daily_fetch.py >> logs/daily_data.log 2>&1

# ============================================
# SIGNAL GENERATION
# ============================================

# Run swarm analysis every 4 hours (H4 candle close + 10 min)
10 */4 * * * cd {project} && {python} signals/generate_signals.py --all >> logs/signals.log 2>&1

# Deep daily analysis at 01:00 UTC
0 1 * * * cd {project} && {python} main.py --run --symbol BTCUSD >> logs/daily_analysis.log 2>&1

# ============================================
# BACKTESTING
# ============================================

# Weekly backtest every Sunday at 02:00 UTC
0 2 * * 0 cd {project} && {python} main.py --backtest >> logs/backtest.log 2>&1

# ============================================
# MAINTENANCE
# ============================================

# Clean old log files (keep last 7 days) - Daily at 03:00
0 3 * * * find {project}/logs -name "*.log" -mtime +7 -delete

# Clean old data files (keep last 30 days) - Weekly on Sunday
0 3 * * 0 find {project}/data/historical -name "*.json" -mtime +30 -delete

# ============================================
# TELEGRAM DIGEST
# ============================================

# Morning digest at 08:00 UTC (if you add a digest script)
# 0 8 * * * cd {project} && {python} utils/send_daily_digest.py >> logs/digest.log 2>&1

# Evening digest at 20:00 UTC
# 0 20 * * * cd {project} && {python} utils/send_daily_digest.py >> logs/digest.log 2>&1
"""
    
    return crontab


def install_crontab():
    """Install crontab entries"""
    crontab = generate_crontab()
    project = get_project_path()
    logs_dir = project / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("🕐 SWARM TRADER - CRON SCHEDULER SETUP")
    print("="*60)
    print(f"\n📁 Project: {project}")
    print(f"🐍 Python: {get_python_path()}")
    print(f"📝 Logs: {logs_dir}")
    
    # Option 1: Show crontab
    print("\n" + "="*60)
    print("📋 GENERATED CRONTAB ENTRIES")
    print("="*60)
    print(crontab)
    
    # Option 2: Install automatically
    print("\n" + "="*60)
    print("🔧 INSTALLATION OPTIONS")
    print("="*60)
    
    print("\n1️⃣  Manual Installation (Recommended):")
    print(f"   crontab -e")
    print(f"   # Then paste the entries above")
    
    print("\n2️⃣  Automatic Installation:")
    print(f"   echo '{crontab}' | crontab -")
    
    print("\n3️⃣  Append to existing crontab:")
    print(f"   (crontab -l 2>/dev/null; echo '{crontab}') | crontab -")
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMMANDS")
    print("="*60)
    print("\nCheck installed crontab:")
    print("   crontab -l")
    
    print("\nCheck cron logs:")
    print(f"   tail -f {logs_dir}/daily_data.log")
    print(f"   tail -f {logs_dir}/signals.log")
    
    print("\nTest data fetch manually:")
    print(f"   cd {project} && {get_python_path()} data/daily_fetch.py")
    
    print("\n" + "="*60)
    print("📅 SCHEDULE SUMMARY")
    print("="*60)
    print("""
┌─────────────────────────────────────────────────────────────┐
│ Task                    │ Schedule        │ Frequency       │
├─────────────────────────────────────────────────────────────┤
│ Daily Data Fetch        │ 00:05 UTC       │ Once daily      │
│ H4 Data Fetch           │ Every 4h        │ 6x daily        │
│ Signal Generation       │ Every 4h +10m   │ 6x daily        │
│ Daily Deep Analysis     │ 01:00 UTC       │ Once daily      │
│ Weekly Backtest         │ Sun 02:00 UTC   │ Once weekly     │
│ Log Cleanup             │ 03:00 UTC       │ Daily           │
│ Data Cleanup            │ Sun 03:00 UTC   │ Weekly          │
└─────────────────────────────────────────────────────────────┘
    """)
    
    # Save crontab to file
    cron_file = project / "swarm_crontab.txt"
    with open(cron_file, 'w') as f:
        f.write(crontab)
    
    print(f"\n💾 Crontab saved to: {cron_file}")
    print("\n🫡 Ready to install! Choose your method above.")


def test_fetch():
    """Test data fetch"""
    project = get_project_path()
    python = get_python_path()
    
    print("🧪 Testing data fetch...")
    subprocess.run([python, str(project / "data" / "daily_fetch.py")])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Cron Scheduler Setup')
    parser.add_argument('--install', action='store_true', help='Show installation instructions')
    parser.add_argument('--test', action='store_true', help='Test data fetch')
    
    args = parser.parse_args()
    
    if args.test:
        test_fetch()
    else:
        install_crontab()
