#!/bin/bash
# Swarm Trader - Complete Setup Script
# Setup PostgreSQL, configure .env, and verify installation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        SWARM TRADER - DATABASE SETUP SCRIPT           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo ""
    echo "Please install Docker first:"
    echo "  Ubuntu/Debian: https://docs.docker.com/engine/install/ubuntu/"
    echo "  macOS: https://docs.docker.com/docker-for-mac/install/"
    echo "  Windows: https://docs.docker.com/docker-for-windows/install/"
    echo ""
    echo "Or install PostgreSQL manually:"
    echo "  sudo apt install postgresql-15 postgresql-15-timescaledb"
    exit 1
fi

echo -e "${GREEN}✅ Docker found: $(docker --version)${NC}"
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  docker-compose not found, trying 'docker compose' (v2)...${NC}"
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ docker-compose is not installed!${NC}"
        echo "Please install: https://docs.docker.com/compose/install/"
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}✅ Compose found: $COMPOSE_CMD${NC}"
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env and add your API keys!${NC}"
    echo "   Required for full functionality:"
    echo "   - GLASSNODE_API_KEY (On-Chain data)"
    echo "   - COINGLASS_API_KEY (Futures data)"
    echo "   - BINANCE_API_KEY (Real-time OHLCV)"
    echo ""
    echo "   Already configured (FREE):"
    echo "   - FRED_API_KEY ✅"
    echo "   - ALPHA_VANTAGE_KEY ✅"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to edit .env first..."
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Start PostgreSQL with Docker
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Starting PostgreSQL + TimescaleDB            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

$COMPOSE_CMD up -d postgres

echo -e "\n${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 10

# Check if PostgreSQL is running
if $COMPOSE_CMD ps | grep -q "swarm_postgres.*Up"; then
    echo -e "${GREEN}✅ PostgreSQL is running!${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start!${NC}"
    echo "Check logs: $COMPOSE_CMD logs postgres"
    exit 1
fi

# Verify database connection
echo -e "\n${YELLOW}🔍 Verifying database connection...${NC}"

if docker exec swarm_postgres pg_isready -U swarm_user -d swarm_trader > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database is ready!${NC}"
else
    echo -e "${RED}❌ Database connection failed!${NC}"
    docker exec swarm_postgres cat /var/lib/postgresql/data/log/*.log 2>/dev/null || true
    exit 1
fi

# Run schema
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            Creating Database Schema                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

docker exec -i swarm_postgres psql -U swarm_user -d swarm_trader -f /docker-entrypoint-initdb.d/schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Schema created successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Schema may already exist (this is OK)${NC}"
fi

# Verify tables
echo -e "\n${YELLOW}📊 Verifying tables...${NC}"

TABLES=$(docker exec swarm_postgres psql -U swarm_user -d swarm_trader -t -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

echo -e "${GREEN}✅ Created $TABLES tables${NC}"

# Show table names
echo -e "\n${BLUE}Tables created:${NC}"
docker exec swarm_postgres psql -U swarm_user -d swarm_trader -c \
  "\dt"

# Show connection info
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              SETUP COMPLETE!                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ PostgreSQL + TimescaleDB is ready!${NC}"
echo ""
echo "📊 Connection Details:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: swarm_trader"
echo "   User: swarm_user"
echo "   Password: swarm_password_2026"
echo ""
echo "🔧 Connection String:"
echo "   postgresql://swarm_user:swarm_password_2026@localhost:5432/swarm_trader"
echo ""
echo "🌐 Adminer GUI (if enabled):"
echo "   http://localhost:8080"
echo ""
echo "📝 Next Steps:"
echo "   1. Edit .env and add your API keys"
echo "   2. Run: ./run_data_collection.sh BTC,ETH,SOL 2010-01-01 \$(date +%Y-%m-%d)"
echo ""
echo "🛑 To stop database:"
echo "   $COMPOSE_CMD down"
echo ""
echo "🛑 To restart database:"
echo "   $COMPOSE_CMD restart"
echo ""
echo "📊 To view logs:"
echo "   $COMPOSE_CMD logs -f postgres"
echo ""
