#!/bin/bash

# =================================================================
# AI SRS Engineer - Deployment Verification Script
# =================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "\n${BLUE}=====================================================${NC}"
echo -e "${BLUE}        AI SRS Engineer - Server Health Check        ${NC}"
echo -e "${BLUE}=====================================================${NC}\n"

ERRORS=0

# Check Docker containers
echo -e "${YELLOW}[1/5] Checking Docker Container Status...${NC}"
CONTAINERS=$(docker compose ps --format "{{.Name}} - {{.Status}}")
echo "$CONTAINERS"

if echo "$CONTAINERS" | grep -qi "srs_postgres" && echo "$CONTAINERS" | grep -qi "Up"; then
    echo -e "${GREEN}  ✓ Database container is UP${NC}"
else
    echo -e "${RED}  ✗ Database container is NOT running${NC}"
    ERRORS=$((ERRORS+1))
fi

if echo "$CONTAINERS" | grep -qi "srs_backend" && echo "$CONTAINERS" | grep -qi "Up"; then
    echo -e "${GREEN}  ✓ Backend container is UP${NC}"
else
    echo -e "${RED}  ✗ Backend container is NOT running${NC}"
    ERRORS=$((ERRORS+1))
fi

if echo "$CONTAINERS" | grep -qi "srs_frontend" && echo "$CONTAINERS" | grep -qi "Up"; then
    echo -e "${GREEN}  ✓ Frontend container is UP${NC}"
else
    echo -e "${RED}  ✗ Frontend container is NOT running${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check PostgreSQL connection
echo -e "\n${YELLOW}[2/5] Testing PostgreSQL Connection...${NC}"
if docker compose exec -T db pg_isready > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ PostgreSQL is accepting connections${NC}"
else
    echo -e "${RED}  ✗ PostgreSQL is not responding${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check Direct FastAPI Health & DB Check
echo -e "\n${YELLOW}[3/5] Testing FastAPI Backend directly (port 8000)...${NC}"
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/db-check || true)
if [ "$BACKEND_STATUS" = "200" ]; then
    DB_CHECK_RESP=$(curl -s http://localhost:8000/db-check)
    echo -e "${GREEN}  ✓ FastAPI Backend is healthy: $DB_CHECK_RESP${NC}"
else
    echo -e "${RED}  ✗ FastAPI Backend returned HTTP $BACKEND_STATUS (expected 200)${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check Frontend Nginx Web Server
echo -e "\n${YELLOW}[4/5] Testing Frontend Nginx Server (port 80)...${NC}"
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ || true)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}  ✓ Frontend Angular SPA is serving properly (HTTP 200)${NC}"
else
    echo -e "${RED}  ✗ Frontend returned HTTP $FRONTEND_STATUS${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check Frontend Reverse Proxy to Backend via Port 80
echo -e "\n${YELLOW}[5/5] Testing Reverse Proxy routing (/api/db-check on port 80)...${NC}"
PROXY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/api/db-check || true)
if [ "$PROXY_STATUS" = "200" ]; then
    PROXY_RESP=$(curl -s http://localhost/api/db-check)
    echo -e "${GREEN}  ✓ Nginx -> FastAPI Proxy working perfectly: $PROXY_RESP${NC}"
else
    echo -e "${RED}  ✗ Reverse proxy failed with HTTP $PROXY_STATUS${NC}"
    ERRORS=$((ERRORS+1))
fi

echo -e "\n${BLUE}=====================================================${NC}"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS OPERATIONAL! Your project is running properly.${NC}"
    echo -e "You can access the application in your browser at:"
    echo -e "  Frontend UI:  http://$(curl -s ifconfig.me || echo 'YOUR_SERVER_IP')"
    echo -e "  Backend Docs: http://$(curl -s ifconfig.me || echo 'YOUR_SERVER_IP'):8000/docs"
else
    echo -e "${RED}⚠️  Found $ERRORS issue(s) during verification.${NC}"
    echo -e "Inspect logs with:"
    echo -e "  docker compose logs backend"
    echo -e "  docker compose logs db"
    echo -e "  docker compose logs frontend"
fi
echo -e "${BLUE}=====================================================${NC}\n"
