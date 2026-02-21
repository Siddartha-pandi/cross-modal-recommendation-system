#!/bin/bash
# Production Deployment Script

set -e

echo "========================================="
echo "Cross-Modal Recommendation System"
echo "Production Deployment Script"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Load environment variables
source .env

echo -e "${GREEN}✓ Environment variables loaded${NC}"

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"

# Build images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Check health
echo -e "${YELLOW}Checking service health...${NC}"

services=("postgres" "redis" "backend" "frontend" "nginx")

for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "$service.*Up"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service failed to start${NC}"
        docker-compose -f docker-compose.prod.yml logs $service
        exit 1
    fi
done

# Run database migrations (if needed)
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head || true

# Index products
echo -e "${YELLOW}Building product index...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python scripts/build_index.py || true

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Services:"
echo "  Frontend: http://localhost"
echo "  Backend API: http://localhost/api/v1"
echo "  API Docs: http://localhost/api/v1/docs"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f [service_name]"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
