# Deployment Guide

## Overview

This guide covers deploying the Cross-Modal Fashion Recommendation System to production environments.

**Recommended Architecture:**
- **Frontend**: Vercel (serverless, automatic scaling)
- **Backend**: AWS EC2, Render, or Railway (with GPU support optional)
- **Alternative**: Docker Compose on single VPS

---

## Option 1: Docker Deployment (Recommended)

### Prerequisites
- Docker 20.x+
- Docker Compose 2.x+
- 4GB+ RAM
- 20GB+ disk space

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.simple
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data:ro
      - ./index:/app/index:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.simple
      args:
        NEXT_PUBLIC_API_URL: ${BACKEND_URL:-http://localhost:8000/api/v1}
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=${BACKEND_URL:-http://localhost:8000/api/v1}
    depends_on:
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### Deploy Steps

```bash
# 1. Build index (one-time setup)
python backend/scripts/simple_build_index.py

# 2. Build images
docker-compose -f docker-compose.prod.yml build

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Check status
docker-compose -f docker-compose.prod.yml ps

# 5. View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Option 2: Vercel + Render

### Frontend on Vercel

**1. Prepare Frontend**

```bash
cd frontend
```

**2. Add `vercel.json`:**

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url"
  }
}
```

**3. Deploy to Vercel:**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**4. Set Environment Variable in Vercel Dashboard:**
- `NEXT_PUBLIC_API_URL`: Your backend URL (e.g., https://api.yourdomain.com/api/v1)

### Backend on Render

**1. Create `render.yaml`:**

```yaml
services:
  - type: web
    name: fashion-search-api
    env: python
    region: oregon
    plan: standard
    buildCommand: "pip install -r requirements.txt && python scripts/simple_build_index.py"
    startCommand: "uvicorn simple_main:app --host 0.0.0.0 --port $PORT --workers 4"
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: ENVIRONMENT
        value: production
    disk:
      name: data
      mountPath: /app/data
      sizeGB: 10
```

**2. Deploy:**

1. Push code to GitHub
2. Connect repository to Render
3. Render will automatically deploy
4. Note the backend URL

**3. Update Frontend Environment:**

In Vercel, set `NEXT_PUBLIC_API_URL` to your Render backend URL.

---

## Option 3: AWS EC2

### EC2 Instance Setup

**1. Launch EC2 Instance:**
- **Type**: t3.large or t3.xlarge (4GB+ RAM)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 30GB+ SSD
- **Security Group**: Open ports 22, 80, 443, 8000

**2. SSH into Instance:**

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

**3. Install Dependencies:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3-pip python3-venv -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

**4. Clone and Setup:**

```bash
git clone <your-repo>
cd cross-modal-recommendation-system

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/simple_build_index.py

# Frontend setup
cd ../frontend
npm install
npm run build
```

**5. Setup Systemd Services:**

**Backend Service** (`/etc/systemd/system/fashion-api.service`):

```ini
[Unit]
Description=Fashion Search API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cross-modal-recommendation-system/backend
Environment="PATH=/home/ubuntu/cross-modal-recommendation-system/backend/venv/bin"
ExecStart=/home/ubuntu/cross-modal-recommendation-system/backend/venv/bin/uvicorn simple_main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service** (`/etc/systemd/system/fashion-frontend.service`):

```ini
[Unit]
Description=Fashion Search Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cross-modal-recommendation-system/frontend
Environment="NODE_ENV=production"
Environment="NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**6. Start Services:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable fashion-api fashion-frontend
sudo systemctl start fashion-api fashion-frontend
sudo systemctl status fashion-api fashion-frontend
```

**7. Setup Nginx Reverse Proxy:**

```nginx
# /etc/nginx/sites-available/fashion-search
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static images
    location /images/ {
        proxy_pass http://localhost:8000/images/;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/fashion-search /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**8. Setup SSL with Let's Encrypt:**

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## Environment Variables

### Backend (.env)

```env
ENVIRONMENT=production
LOG_LEVEL=info
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

---

## Security Checklist

- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS properly configured (no wildcards in production)
- [ ] API rate limiting implemented
- [ ] File upload size limits enforced (5MB max)
- [ ] Input validation on all endpoints
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] Firewall rules configured
- [ ] Regular security updates
- [ ] Logs monitoring setup

---

## Performance Optimization

### Backend
- Use `--workers 4` for uvicorn (number of CPU cores)
- Enable gzip compression
- Implement response caching for popular queries
- Use CDN for static images

### Frontend
- Enable Next.js image optimization
- Use Vercel Edge Network
- Implement lazy loading
- Minimize bundle size

### FAISS Index
- Use HNSW index for large datasets (>10k products)
- Pre-warm index on startup
- Consider memory-mapped index for very large datasets

---

## Monitoring

### Health Checks

```bash
# Backend health
curl https://api.yourdomain.com/api/v1/health

# Index stats
curl https://api.yourdomain.com/api/v1/stats
```

### Logs

```bash
# Using Docker
docker-compose logs -f backend

# Using systemd
sudo journalctl -u fashion-api -f

# Application logs
tail -f /var/log/fashion-api.log
```

### Metrics to Monitor
- API response time
- Search query latency
- Memory usage
- Error rates
- Request throughput

---

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (AWS ALB, Nginx)
- Run multiple backend instances
- Share index via network storage or replicate

### Vertical Scaling
- Increase instance size for more RAM
- Consider GPU instances for faster inference
- Use high-memory instances for large indices

### Database (Optional)
- Add PostgreSQL for product metadata
- Use Redis for caching search results
- Implement query result caching

---

## Backup & Recovery

### Data to Backup
- FAISS index files (`index/`)
- Product metadata (`data/products.json`)
- Downloaded images (`data/images/`)
- Application configuration

### Backup Schedule
```bash
# Daily backup script
#!/bin/bash
tar -czf backup-$(date +%Y%m%d).tar.gz index/ data/
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-bucket/backups/
```

---

## Troubleshooting

### High Memory Usage
- Reduce FAISS index size
- Use memory-mapped indices
- Implement pagination

### Slow Search
- Check index type (use HNSW)
- Reduce top_k value
- Optimize embedding generation

### Failed Deployments
- Check logs: `docker-compose logs`
- Verify disk space: `df -h`
- Check memory: `free -m`

---

## Cost Estimation

### Vercel + Render
- Vercel (Frontend): $0/month (hobby) or $20/month (pro)
- Render (Backend): $7-25/month
- **Total**: ~$7-45/month

### AWS EC2
- t3.large instance: ~$60/month
- t3.xlarge instance: ~$120/month
- Plus bandwidth and storage
- **Total**: ~$70-150/month

### Single VPS (DigitalOcean/Linode)
- 4GB RAM droplet: ~$24/month
- 8GB RAM droplet: ~$48/month
- **Total**: ~$24-48/month

---

## Production Checklist

- [ ] Index built with production data
- [ ] Environment variables configured
- [ ] HTTPS/SSL enabled
- [ ] CORS configured correctly
- [ ] Health checks passing
- [ ] Monitoring setup
- [ ] Backups configured
- [ ] Security hardening complete
- [ ] Load testing performed
- [ ] Documentation updated
- [ ] Rollback plan in place

---

## Support & Maintenance

### Regular Maintenance
- Update dependencies monthly
- Rebuild index when products change
- Monitor disk space
- Review logs weekly
- Update SSL certificates (auto with Let's Encrypt)

### Emergency Contacts
- Backend issues: Check `/api/v1/health`
- Frontend issues: Check Vercel dashboard
- Infrastructure: Check cloud provider status pages
