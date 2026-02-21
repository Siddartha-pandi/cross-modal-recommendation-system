# Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Cloud Platforms](#cloud-platforms)
7. [Scaling](#scaling)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free space
- OS: Windows 10+, macOS 10.15+, Ubuntu 20.04+

**Recommended (Production):**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD
- GPU: NVIDIA GPU with 8GB+ VRAM (optional, for faster CLIP inference)

### Software Dependencies

- **Docker:** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose:** 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))
- **Python:** 3.10+ (for local development)
- **Node.js:** 18+ (for frontend development)
- **PostgreSQL:** 15+ (if not using Docker)
- **Redis:** 7+ (if not using Docker)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cross-modal-recommendation-system.git
cd cross-modal-recommendation-system
```

### 2. Create Environment File

```bash
cp .env.production.example .env
```

### 3. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Database
POSTGRES_USER=cmrs_user
POSTGRES_PASSWORD=secure_password_here
DATABASE_URL=postgresql://cmrs_user:secure_password_here@postgres:5432/cmrs_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_redis_password_here

# JWT Authentication
JWT_SECRET_KEY=generate_random_256_bit_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# E-commerce APIs (Optional)
SHOPIFY_SHOP_URL=your-shop.myshopify.com
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_PASSWORD=your_shopify_password

# AWS (Optional - for S3 image storage)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO

# Deployment
ENVIRONMENT=production
APP_VERSION=1.0.0
```

### 4. Generate Secure Keys

```bash
# Generate JWT secret key (Python)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Redis password
openssl rand -base64 32
```

---

## Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/init_db.py

# Build FAISS index
python scripts/build_index.py

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## Docker Deployment

### Development with Docker

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/api/v1/docs
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### Production with Docker

```bash
# Use production docker-compose file
docker-compose -f docker-compose.prod.yml up -d --build

# Or use deployment script
chmod +x deploy.sh
./deploy.sh
```

The deployment script will:
1. ✓ Validate environment configuration
2. ✓ Check Docker installation
3. ✓ Build optimized images
4. ✓ Start all services
5. ✓ Run database migrations
6. ✓ Build FAISS index
7. ✓ Perform health checks

---

## Production Deployment

### Option 1: VPS/Dedicated Server

**Recommended Providers:** DigitalOcean, Linode, AWS EC2, Google Cloud Compute

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Step 2: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

#### Step 3: Configure Nginx

Update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of configuration
}
```

#### Step 4: Deploy

```bash
# Clone repository
git clone https://github.com/yourusername/cross-modal-recommendation-system.git
cd cross-modal-recommendation-system

# Configure environment
cp .env.production.example .env
nano .env

# Deploy
chmod +x deploy.sh
./deploy.sh
```

#### Step 5: Setup Firewall

```bash
# Configure UFW
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable
```

---

### Option 2: Cloud Platforms

#### Deploy to AWS

**Using AWS Elastic Beanstalk:**

```bash
# Initialize EB CLI
eb init -p docker cross-modal-recommendation

# Create environment
eb create production-env --instance-type t3.large

# Deploy
eb deploy

# Open application
eb open
```

**Using AWS ECS (Elastic Container Service):**

1. Push images to Amazon ECR
2. Create ECS task definitions
3. Configure Application Load Balancer
4. Deploy ECS service

#### Deploy to Azure

```bash
# Login to Azure
az login

# Create resource group
az group create --name cmrs-rg --location eastus

# Create container registry
az acr create --resource-group cmrs-rg --name cmrsregistry --sku Basic

# Build and push images
az acr build --registry cmrsregistry --image cmrs-backend:latest ./backend
az acr build --registry cmrsregistry --image cmrs-frontend:latest ./frontend

# Create container instances
az container create --resource-group cmrs-rg \
  --name cmrs-production \
  --image cmrsregistry.azurecr.io/cmrs-backend:latest \
  --ports 8000 \
  --dns-name-label cmrs-api
```

#### Deploy to Google Cloud

```bash
# Setup gcloud
gcloud init

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/cmrs-backend backend/
gcloud builds submit --tag gcr.io/PROJECT_ID/cmrs-frontend frontend/

# Deploy to Cloud Run
gcloud run deploy cmrs-backend \
  --image gcr.io/PROJECT_ID/cmrs-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy cmrs-frontend \
  --image gcr.io/PROJECT_ID/cmrs-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Scaling

### Horizontal Scaling

#### Backend Service

```yaml
# docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3  # Run 3 instances
    environment:
      WORKERS_PER_INSTANCE: 4
```

#### Load Balancer Configuration

```nginx
# nginx/nginx.conf
upstream backend {
    least_conn;  # Load balancing method
    server backend1:8000 max_fails=3 fail_timeout=30s;
    server backend2:8000 max_fails=3 fail_timeout=30s;
    server backend3:8000 max_fails=3 fail_timeout=30s;
}
```

### Vertical Scaling

Increase resources in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### Database Scaling

#### PostgreSQL Read Replicas

```yaml
services:
  postgres-primary:
    image: postgres:15-alpine
    
  postgres-replica:
    image: postgres:15-alpine
    environment:
      PGUSER: replicator
      PGPASSWORD: replica_password
    command: |
      -c 'hot_standby=on'
      -c 'primary_conninfo=host=postgres-primary port=5432 user=replicator'
```

#### Redis Cluster

```yaml
services:
  redis-master:
    image: redis:7-alpine
    
  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
    
  redis-replica-2:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
```

---

## Monitoring

### Setup Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

check_service() {
    local url=$1
    local service=$2
    
    if curl -f -s "$url" > /dev/null; then
        echo "✓ $service is healthy"
        return 0
    else
        echo "✗ $service is down"
        return 1
    fi
}

check_service "http://localhost:8000/api/v1/health" "Backend API"
check_service "http://localhost:3000" "Frontend"
check_service "http://localhost:6379" "Redis"
```

### Log Aggregation

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Export logs
docker-compose logs --no-color > logs_$(date +%Y%m%d).txt
```

---

## Troubleshooting

### Common Issues

#### 1. Backend fails to start

**Error:** `Cannot connect to database`

**Solution:**
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Run migrations manually
docker-compose exec backend alembic upgrade head
```

#### 2. CLIP model loading fails

**Error:** `RuntimeError: CUDA out of memory`

**Solution:**
```bash
# Edit .env to use CPU
DEVICE=cpu

# Or increase Docker memory limit
docker-compose down
docker-compose up -d --memory="8g"
```

#### 3. Redis connection errors

**Error:** `redis.exceptions.ConnectionError`

**Solution:**
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Clear cache if corrupted
docker-compose exec redis redis-cli FLUSHALL

# Restart Redis
docker-compose restart redis
```

#### 4. Slow search performance

**Symptoms:** Search takes >5 seconds

**Diagnosis:**
```bash
# Check cache hit rate
curl http://localhost:8000/api/v1/cache/stats | jq '.hit_rate'

# Check FAISS index size
curl http://localhost:8000/api/v1/health | jq '.index_size'
```

**Solutions:**
- Enable Redis caching
- Reduce `top_k` parameter
- Use GPU for CLIP inference
- Build IVF FAISS index for large datasets

#### 5. SSL certificate issues

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution:**
```bash
# Renew certificate
sudo certbot renew --force-renewal

# Check certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Debug Mode

Enable debug logging:

```bash
# Edit .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend
```

### Performance Profiling

```bash
# Install profiling tools
pip install py-spy

# Profile backend
py-spy top --pid $(pgrep -f uvicorn)

# Generate flamegraph
py-spy record -o profile.svg --pid $(pgrep -f uvicorn)
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup database
docker-compose exec -T postgres pg_dump -U cmrs_user cmrs_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (crontab)
0 2 * * * docker-compose exec -T postgres pg_dump -U cmrs_user cmrs_db > /backups/db_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose exec -T postgres psql -U cmrs_user cmrs_db < backup_20240115_020000.sql
```

### FAISS Index Backup

```bash
# Backup index files
cp -r index/ backups/index_$(date +%Y%m%d)/

# Rebuild index if corrupted
docker-compose exec backend python scripts/build_index.py --rebuild
```

---

## Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Use strong JWT secret key (256-bit)
- [ ] Enable SSL/TLS with valid certificate
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Set up fail2ban for SSH protection
- [ ] Regular security updates: `apt update && apt upgrade`
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault)
- [ ] Enable audit logging
- [ ] Implement backup strategy

---

**For support, contact:** support@yourdomain.com
