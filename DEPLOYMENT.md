# Deployment Guide: AI-Powered Prompt Optimizer SaaS

Complete guide to deploying the Prompt Optimizer in production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Option A: Docker Deployment (Recommended)](#option-a-docker-deployment)
4. [Option B: Manual Deployment](#option-b-manual-deployment)
5. [Option C: Cloud Platform Deployment](#option-c-cloud-platform-deployment)
6. [Database Setup](#database-setup)
7. [Stripe Payment Setup](#stripe-payment-setup)
8. [Domain & SSL Configuration](#domain--ssl-configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Scaling & Performance](#scaling--performance)
11. [Security Checklist](#security-checklist)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts & API Keys

| Service | Purpose | Sign Up |
|---------|---------|---------|
| **xAI** | Grok API for prompt optimization | https://console.x.ai |
| **Stripe** | Payment processing | https://dashboard.stripe.com |
| **Sentry** (optional) | Error tracking | https://sentry.io |

### System Requirements

- Python 3.11+
- PostgreSQL 14+ (production) or SQLite (development)
- Redis 6+ (optional, for caching)
- 2GB RAM minimum, 4GB recommended
- 10GB disk space

---

## Environment Variables

Create a `.env` file with these variables:

```bash
# ===================
# REQUIRED
# ===================

# xAI Grok API (get from https://console.x.ai)
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Secret key for session encryption (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your-secret-key-here-minimum-32-characters

# Database URL
DATABASE_URL=postgresql://user:password@localhost:5432/prompt_optimizer
# For SQLite (development only): DATABASE_URL=sqlite:///./app.db

# ===================
# STRIPE PAYMENTS
# ===================

# Get from https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx

# Price IDs (create in Stripe Dashboard > Products)
STRIPE_PRICE_ID_PRO=price_xxxxxxxxxxxxxxxxxxxx
STRIPE_PRICE_ID_ENTERPRISE=price_xxxxxxxxxxxxxxxxxxxx

# ===================
# OPTIONAL
# ===================

# Application settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Sentry error tracking (https://sentry.io)
SENTRY_DSN=https://xxxx@sentry.io/xxxx

# Redis caching (optional but recommended)
REDIS_URL=redis://localhost:6379/0

# Agentic RAG (experimental)
ENABLE_AGENTIC_RAG=false

# Collections API (for document search)
ENABLE_COLLECTIONS=false
COLLECTION_ID_PROMPT_EXAMPLES=col_xxxx
COLLECTION_ID_MARKETING=col_xxxx
COLLECTION_ID_TECHNICAL=col_xxxx
```

---

## Option A: Docker Deployment

### Quick Start (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/AI-Powered-Prompt-Optimizer-SaaS.git
cd AI-Powered-Prompt-Optimizer-SaaS

# 2. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker compose up -d

# 4. Check status
docker compose ps
docker compose logs -f app
```

### Services Started

| Service | Port | Description |
|---------|------|-------------|
| `app` | 8501 | Streamlit UI |
| `api` | 8000 | FastAPI REST API |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache |

### Docker Commands

```bash
# View logs
docker compose logs -f app

# Restart a service
docker compose restart app

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up -d --build

# Scale the app (multiple instances)
docker compose up -d --scale app=3
```

### Production Docker Compose

For production, create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - ENVIRONMENT=production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: always
```

---

## Option B: Manual Deployment

### 1. System Setup (Ubuntu/Debian)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis (optional)
sudo apt install redis-server -y
```

### 2. Application Setup

```bash
# Create application user
sudo useradd -m -s /bin/bash promptopt
sudo su - promptopt

# Clone repository
git clone https://github.com/your-org/AI-Powered-Prompt-Optimizer-SaaS.git
cd AI-Powered-Prompt-Optimizer-SaaS

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE USER promptopt WITH PASSWORD 'your-secure-password';
CREATE DATABASE prompt_optimizer OWNER promptopt;
GRANT ALL PRIVILEGES ON DATABASE prompt_optimizer TO promptopt;
EOF
```

### 4. Systemd Service

Create `/etc/systemd/system/prompt-optimizer.service`:

```ini
[Unit]
Description=AI Prompt Optimizer
After=network.target postgresql.service

[Service]
Type=simple
User=promptopt
Group=promptopt
WorkingDirectory=/home/promptopt/AI-Powered-Prompt-Optimizer-SaaS
Environment="PATH=/home/promptopt/AI-Powered-Prompt-Optimizer-SaaS/venv/bin"
EnvironmentFile=/home/promptopt/AI-Powered-Prompt-Optimizer-SaaS/.env
ExecStart=/home/promptopt/AI-Powered-Prompt-Optimizer-SaaS/venv/bin/streamlit run main.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable prompt-optimizer
sudo systemctl start prompt-optimizer

# Check status
sudo systemctl status prompt-optimizer
```

---

## Option C: Cloud Platform Deployment

### Railway (Easiest)

1. Connect GitHub repository at https://railway.app
2. Add environment variables in Railway dashboard
3. Deploy automatically on push

```bash
# railway.json (optional config)
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "healthcheckPath": "/_stcore/health",
    "restartPolicyType": "always"
  }
}
```

### Render

1. Create new Web Service at https://render.com
2. Connect repository
3. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run main.py --server.port=$PORT --server.address=0.0.0.0`
4. Add environment variables

### AWS (EC2 + RDS)

```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. Create RDS PostgreSQL instance
# 3. SSH into EC2 and follow Manual Deployment steps
# 4. Configure security groups:
#    - EC2: Allow 80, 443, 22
#    - RDS: Allow 5432 from EC2 security group
```

### Google Cloud Run

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/prompt-optimizer

# Deploy to Cloud Run
gcloud run deploy prompt-optimizer \
  --image gcr.io/PROJECT_ID/prompt-optimizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "XAI_API_KEY=xxx,SECRET_KEY=xxx"
```

---

## Database Setup

### PostgreSQL Schema Migration

The application auto-creates tables on first run. To manually initialize:

```bash
# Activate virtual environment
source venv/bin/activate

# Run Python to create tables
python << EOF
from database import Database, Base
db = Database()
print("Database tables created successfully!")
EOF
```

### Backup & Restore

```bash
# Backup
pg_dump -U promptopt prompt_optimizer > backup_$(date +%Y%m%d).sql

# Restore
psql -U promptopt prompt_optimizer < backup_20240103.sql
```

---

## Stripe Payment Setup

### 1. Create Products in Stripe Dashboard

Go to https://dashboard.stripe.com/products and create:

| Product | Price | Billing |
|---------|-------|---------|
| Pro Plan | $19.99/month | Recurring |
| Enterprise Plan | $99.99/month | Recurring |

### 2. Configure Webhooks

1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://your-domain.com/api/webhooks/stripe`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

### 3. Test with Stripe CLI

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Test checkout
stripe trigger checkout.session.completed
```

---

## Domain & SSL Configuration

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/prompt-optimizer`:

```nginx
upstream streamlit {
    server 127.0.0.1:8501;
}

upstream fastapi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Streamlit app
    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # FastAPI
    location /api/ {
        proxy_pass http://fastapi/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support for Streamlit
    location /_stcore/stream {
        proxy_pass http://streamlit/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

### SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

---

## Monitoring & Observability

### Sentry Error Tracking

```bash
# Add to .env
SENTRY_DSN=https://xxxx@sentry.io/xxxx
```

The application automatically initializes Sentry when the DSN is set.

### Structured Logging

Logs are output in JSON format. View with:

```bash
# Docker
docker compose logs -f app | jq

# Systemd
journalctl -u prompt-optimizer -f | jq
```

### Health Checks

```bash
# Streamlit health
curl http://localhost:8501/_stcore/health

# FastAPI health
curl http://localhost:8000/health

# Full system check
curl http://localhost:8000/api/health
```

### Metrics Dashboard

Access LLM usage metrics:

```python
from observability import get_tracker

tracker = get_tracker()
summary = tracker.get_summary()
print(f"Total API cost: ${summary['total_cost_usd']}")
print(f"Total tokens: {summary['total_tokens']}")
```

---

## Scaling & Performance

### Horizontal Scaling

```bash
# Docker Compose
docker compose up -d --scale app=3

# Add load balancer (nginx upstream)
upstream streamlit {
    least_conn;
    server app1:8501;
    server app2:8501;
    server app3:8501;
}
```

### Redis Caching

Enable Redis for better performance:

```bash
# .env
REDIS_URL=redis://localhost:6379/0
```

### Database Connection Pooling

Already configured in `database.py` with SQLAlchemy connection pooling.

### CDN for Static Assets

Use Cloudflare or AWS CloudFront in front of your domain.

---

## Security Checklist

Before going live, verify:

- [ ] **Environment variables** are set (not hardcoded)
- [ ] **SECRET_KEY** is unique and secure (32+ characters)
- [ ] **DEBUG=false** in production
- [ ] **HTTPS** is enforced (redirect HTTP to HTTPS)
- [ ] **Stripe webhook secret** is configured
- [ ] **Database** is not publicly accessible
- [ ] **Firewall** allows only necessary ports (80, 443)
- [ ] **API keys** are not in git history
- [ ] **Rate limiting** is enabled
- [ ] **Security headers** are configured in nginx
- [ ] **Backups** are configured for database
- [ ] **Monitoring** is set up (Sentry, logs)

### Security Headers Test

```bash
# Test security headers
curl -I https://your-domain.com
```

---

## Troubleshooting

### Common Issues

**App won't start:**
```bash
# Check logs
docker compose logs app
# or
journalctl -u prompt-optimizer -n 100

# Common fixes:
# - Verify all environment variables are set
# - Check database connection
# - Ensure port 8501 is available
```

**Database connection failed:**
```bash
# Test connection
psql -h localhost -U promptopt -d prompt_optimizer

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

**Stripe webhooks failing:**
```bash
# Verify webhook secret
stripe listen --print-secret

# Test webhook endpoint
curl -X POST https://your-domain.com/api/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"type": "test"}'
```

**High memory usage:**
```bash
# Check memory
docker stats

# Limit memory in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

### Support

- GitHub Issues: https://github.com/your-org/AI-Powered-Prompt-Optimizer-SaaS/issues
- Documentation: See `CLAUDE.md` for development guide

---

## Quick Reference

```bash
# Start (Docker)
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f app

# Restart
docker compose restart app

# Update
git pull && docker compose up -d --build

# Backup database
docker compose exec postgres pg_dump -U postgres prompt_optimizer > backup.sql

# Run tests
docker compose exec app pytest tests/ -v
```

---

*Last updated: January 2026*
