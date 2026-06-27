#!/bin/bash
# Swarm Trader - Complete Data Collection Runner
# Runs all 8 data collectors with proper error handling

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SYMBOLS="${1:-BTC,ETH,SOL}"
START_DATE="${2:-2010-01-01}"
END_DATE="${3:-$(date +%Y-%m-%d)}"
MODE="${4:-backfill}"  # backfill or realtime

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SWARM TRADER - COMPLETE DATA COLLECTION RUNNER      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Symbols:${NC} $SYMBOLS"
echo -e "${GREEN}Date Range:${NC} $START_DATE to $END_DATE"
echo -e "${GREEN}Mode:${NC} $MODE"
echo ""

# Activate virtual environment
source venv/bin/activate

# Function to run collector with error handling
run_collector() {
    local name=$1
    local script=$2
    local args=$3
    
    echo -e "\n${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}[$name] Starting...${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    
    if python "$script" $args; then
        echo -e "${GREEN}✅ [$name] SUCCESS${NC}"
        return 0
    else
        echo -e "${RED}❌ [$name] FAILED${NC}"
        return 1
    fi
}

# Counters
SUCCESS=0
FAILED=0

# Parse symbols
IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"

for SYMBOL in "${SYMBOL_ARRAY[@]}"; do
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Processing: $SYMBOL                                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    
    # 1. OHLCV Collector
    if run_collector "OHLCV" "data/collectors/ohlcv_collector.py" \
        "--symbol $SYMBOL --start $START_DATE --end $END_DATE --timeframes 1m,5m,15m,1H,4H,1D,1W"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    
    # 2. Futures Collector
    if run_collector "Futures" "data/collectors/futures_collector.py" \
        "--symbol $SYMBOL --start 2018-01-01 --end $END_DATE"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    
    # 3. On-Chain Collector
    if run_collector "On-Chain" "data/collectors/onchain_collector.py" \
        "--asset $SYMBOL --start $START_DATE --end $END_DATE"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    
    # 4. Macro Collector (run once, not per symbol)
    if [ "$SYMBOL" = "BTC" ]; then
        if run_collector "Macro" "data/collectors/macro_collector.py" \
            "--indicators CPI,PPI,fed_funds,yield_10y,yield_2y,DXY,gold,vix,sp500,nasdaq --start 1980-01-01 --end $END_DATE"; then
            ((SUCCESS++))
        else
            ((FAILED++))
        fi
    fi
    
    # 5. Sentiment & News Collector
    if run_collector "Sentiment" "data/collectors/sentiment_news_collector.py" \
        "--type sentiment --start $START_DATE --end $END_DATE"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    
    if run_collector "News" "data/collectors/sentiment_news_collector.py" \
        "--type news --start $START_DATE --end $END_DATE"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
    
    # 6. Cycle Labeler
    if run_collector "Cycle Labels" "data/collectors/cycle_labeler.py" \
        "--asset $SYMBOL --start $START_DATE --end $END_DATE --auto --detect-smc"; then
        ((SUCCESS++))
    else
        ((FAILED++))
    fi
done

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  COLLECTION SUMMARY                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}Successful:${NC} $SUCCESS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL COLLECTORS COMPLETED SUCCESSFULLY!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some collectors failed. Check logs above.${NC}"
    exit 1
fi
