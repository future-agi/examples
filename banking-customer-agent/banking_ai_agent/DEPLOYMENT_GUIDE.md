# Banking AI Agent - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Local Development Deployment](#local-development-deployment)
5. [Production Deployment](#production-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Security Configuration](#security-configuration)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Overview

This deployment guide provides comprehensive instructions for deploying the Banking AI Agent in various environments, from local development to production cloud deployments. The guide covers security considerations, monitoring setup, and best practices for banking-grade deployments.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended Requirements:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ SSD
- Network: 1 Gbps

### Software Dependencies

**Backend Requirements:**
- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment support
- SQLite 3.x (for development) or PostgreSQL 13+ (for production)

**Frontend Requirements:**
- Node.js 20.x or higher
- npm or pnpm package manager
- Modern web browser support

**External Services:**
- OpenAI API access (GPT-4o)
- SMTP server (for notifications)
- SSL certificates (for production)

### API Keys and Credentials

Before deployment, ensure you have:
- OpenAI API key with GPT-4o access
- Database credentials (for production)
- SSL certificates (for HTTPS)
- SMTP credentials (for email notifications)

## Environment Setup

### Development Environment

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd banking-ai-agent
   ```

2. **Backend Setup**
   ```bash
   cd banking_ai_agent
   python -m venv venv
   
   # Activate virtual environment
   # Linux/Mac:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd banking-ai-frontend
   npm install
   ```

4. **Environment Configuration**
   ```bash
   # Copy environment template
   cp banking_ai_agent/.env.example banking_ai_agent/.env
   
   # Edit configuration
   nano banking_ai_agent/.env
   ```

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Application Environment
ENVIRONMENT=development
DEBUG=True
PORT=5000

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
MODEL_NAME=gpt-4o
TEMPERATURE=0.1
MAX_TOKENS=2000
EMBEDDING_MODEL=text-embedding-ada-002

# Database Configuration
DATABASE_URL=sqlite:///./data/banking_agent.db
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Memory Configuration
MAX_CONTEXT_LENGTH=10
CONTEXT_WINDOW_HOURS=24

# RAG Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_RETRIEVAL_DOCS=10

# Security Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/banking_agent.log
AUDIT_LOG_FILE=./logs/audit.log

# Email Configuration (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True

# Monitoring Configuration
ENABLE_METRICS=True
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
```

## Local Development Deployment

### Quick Start

1. **Start the Backend Server**
   ```bash
   cd banking_ai_agent
   source venv/bin/activate
   python src/main.py
   ```

2. **Start the Frontend Development Server**
   ```bash
   cd banking-ai-frontend
   npm run dev --host
   ```

3. **Verify Deployment**
   - Frontend: http://localhost:5174
   - Backend API: http://localhost:5000
   - Health Check: http://localhost:5000/health

### Development Tools

**Backend Development:**
```bash
# Run tests
python run_tests.py

# Code formatting
black src/
isort src/

# Linting
flake8 src/

# Type checking
mypy src/
```

**Frontend Development:**
```bash
# Run tests
npm test

# Linting
npm run lint

# Type checking
npm run type-check

# Build for production
npm run build
```

## Production Deployment

### Production Environment Setup

1. **System Preparation**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Install required packages
   sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx postgresql redis-server
   
   # Create application user
   sudo useradd -m -s /bin/bash bankingai
   sudo usermod -aG sudo bankingai
   ```

2. **Database Setup (PostgreSQL)**
   ```bash
   # Switch to postgres user
   sudo -u postgres psql
   
   # Create database and user
   CREATE DATABASE banking_agent;
   CREATE USER banking_agent_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE banking_agent TO banking_agent_user;
   \q
   ```

3. **Application Deployment**
   ```bash
   # Switch to application user
   sudo su - bankingai
   
   # Clone repository
   git clone <repository-url> /opt/banking-ai-agent
   cd /opt/banking-ai-agent
   
   # Setup backend
   cd banking_ai_agent
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Setup frontend
   cd ../banking-ai-frontend
   npm install
   npm run build
   ```

### Production Configuration

**Production Environment File:**
```env
# Application Environment
ENVIRONMENT=production
DEBUG=False
PORT=5000
HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://banking_agent_user:secure_password@localhost:5432/banking_agent

# Security Configuration
SECRET_KEY=your-very-secure-secret-key-here
JWT_SECRET=your-very-secure-jwt-secret-here
ENCRYPTION_KEY=your-very-secure-encryption-key-here

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/banking-ai-agent.crt
SSL_KEY_PATH=/etc/ssl/private/banking-ai-agent.key

# Logging Configuration
LOG_LEVEL=WARNING
LOG_FILE=/var/log/banking-ai-agent/application.log
AUDIT_LOG_FILE=/var/log/banking-ai-agent/audit.log
ERROR_LOG_FILE=/var/log/banking-ai-agent/error.log

# Performance Configuration
WORKERS=4
MAX_CONNECTIONS=1000
TIMEOUT=30
KEEPALIVE=2

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# Monitoring Configuration
ENABLE_METRICS=True
METRICS_PORT=9090
SENTRY_DSN=your-sentry-dsn-here
```

### Systemd Service Configuration

**Backend Service (`/etc/systemd/system/banking-ai-agent.service`):**
```ini
[Unit]
Description=Banking AI Agent Backend
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=bankingai
Group=bankingai
WorkingDirectory=/opt/banking-ai-agent/banking_ai_agent
Environment=PATH=/opt/banking-ai-agent/banking_ai_agent/venv/bin
ExecStart=/opt/banking-ai-agent/banking_ai_agent/venv/bin/python src/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=banking-ai-agent

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/banking-ai-agent /var/log/banking-ai-agent /tmp

[Install]
WantedBy=multi-user.target
```

**Enable and Start Service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable banking-ai-agent
sudo systemctl start banking-ai-agent
sudo systemctl status banking-ai-agent
```

### Nginx Configuration

**Nginx Configuration (`/etc/nginx/sites-available/banking-ai-agent`):**
```nginx
upstream banking_ai_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/banking-ai-agent.crt;
    ssl_certificate_key /etc/ssl/private/banking-ai-agent.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Frontend Static Files
    location / {
        root /opt/banking-ai-agent/banking-ai-frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Proxy
    location /api/ {
        proxy_pass http://banking_ai_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # Health Check
    location /health {
        proxy_pass http://banking_ai_backend/health;
        access_log off;
    }

    # Metrics (restrict access)
    location /metrics {
        proxy_pass http://banking_ai_backend/metrics;
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }

    # Logging
    access_log /var/log/nginx/banking-ai-agent.access.log;
    error_log /var/log/nginx/banking-ai-agent.error.log;
}
```

**Enable Nginx Configuration:**
```bash
sudo ln -s /etc/nginx/sites-available/banking-ai-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Cloud Deployment

### AWS Deployment

**Using AWS ECS with Fargate:**

1. **Create Dockerfile**
   ```dockerfile
   # Backend Dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   # Copy requirements and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY . .
   
   # Create non-root user
   RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
   USER appuser
   
   # Expose port
   EXPOSE 5000
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:5000/health || exit 1
   
   # Start application
   CMD ["python", "src/main.py"]
   ```

2. **ECS Task Definition**
   ```json
   {
     "family": "banking-ai-agent",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "1024",
     "memory": "2048",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
     "containerDefinitions": [
       {
         "name": "banking-ai-agent",
         "image": "your-account.dkr.ecr.region.amazonaws.com/banking-ai-agent:latest",
         "portMappings": [
           {
             "containerPort": 5000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "ENVIRONMENT",
             "value": "production"
           }
         ],
         "secrets": [
           {
             "name": "OPENAI_API_KEY",
             "valueFrom": "arn:aws:secretsmanager:region:account:secret:banking-ai-agent/openai-key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/banking-ai-agent",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         },
         "healthCheck": {
           "command": ["CMD-SHELL", "curl -f http://localhost:5000/health || exit 1"],
           "interval": 30,
           "timeout": 5,
           "retries": 3,
           "startPeriod": 60
         }
       }
     ]
   }
   ```

3. **Deploy with AWS CLI**
   ```bash
   # Build and push Docker image
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   docker build -t banking-ai-agent .
   docker tag banking-ai-agent:latest your-account.dkr.ecr.us-east-1.amazonaws.com/banking-ai-agent:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/banking-ai-agent:latest
   
   # Create ECS service
   aws ecs create-service \
     --cluster banking-ai-cluster \
     --service-name banking-ai-agent \
     --task-definition banking-ai-agent:1 \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-abcdef],assignPublicIp=ENABLED}"
   ```

### Google Cloud Platform Deployment

**Using Cloud Run:**

1. **Create cloudbuild.yaml**
   ```yaml
   steps:
   - name: 'gcr.io/cloud-builders/docker'
     args: ['build', '-t', 'gcr.io/$PROJECT_ID/banking-ai-agent', '.']
   - name: 'gcr.io/cloud-builders/docker'
     args: ['push', 'gcr.io/$PROJECT_ID/banking-ai-agent']
   - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
     entrypoint: gcloud
     args:
     - 'run'
     - 'deploy'
     - 'banking-ai-agent'
     - '--image'
     - 'gcr.io/$PROJECT_ID/banking-ai-agent'
     - '--region'
     - 'us-central1'
     - '--platform'
     - 'managed'
     - '--allow-unauthenticated'
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

### Azure Deployment

**Using Azure Container Instances:**

```bash
# Create resource group
az group create --name banking-ai-rg --location eastus

# Create container instance
az container create \
  --resource-group banking-ai-rg \
  --name banking-ai-agent \
  --image your-registry.azurecr.io/banking-ai-agent:latest \
  --cpu 2 \
  --memory 4 \
  --ports 5000 \
  --environment-variables ENVIRONMENT=production \
  --secure-environment-variables OPENAI_API_KEY=your-api-key
```

## Security Configuration

### SSL/TLS Configuration

1. **Obtain SSL Certificates**
   ```bash
   # Using Let's Encrypt
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Configure SSL in Application**
   ```python
   # In main.py
   if __name__ == '__main__':
       if os.getenv('ENVIRONMENT') == 'production':
           app.run(
               host='0.0.0.0',
               port=5000,
               ssl_context=(
                   os.getenv('SSL_CERT_PATH'),
                   os.getenv('SSL_KEY_PATH')
               )
           )
       else:
           app.run(host='0.0.0.0', port=5000, debug=True)
   ```

### Authentication and Authorization

1. **JWT Configuration**
   ```python
   # In auth.py
   JWT_SECRET = os.getenv('JWT_SECRET')
   JWT_ALGORITHM = 'HS256'
   JWT_EXPIRATION_DELTA = timedelta(hours=24)
   ```

2. **API Key Management**
   ```python
   # In middleware.py
   def require_api_key(f):
       @wraps(f)
       def decorated_function(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           if not api_key or not validate_api_key(api_key):
               return jsonify({'error': 'Invalid API key'}), 401
           return f(*args, **kwargs)
       return decorated_function
   ```

### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Monitoring and Logging

### Application Monitoring

1. **Prometheus Metrics**
   ```python
   # In metrics.py
   from prometheus_client import Counter, Histogram, Gauge
   
   REQUEST_COUNT = Counter('banking_ai_requests_total', 'Total requests')
   REQUEST_LATENCY = Histogram('banking_ai_request_duration_seconds', 'Request latency')
   ACTIVE_SESSIONS = Gauge('banking_ai_active_sessions', 'Active sessions')
   ```

2. **Health Check Endpoint**
   ```python
   @app.route('/health')
   def health_check():
       return jsonify({
           'status': 'healthy',
           'timestamp': datetime.now().isoformat(),
           'version': '1.0.0',
           'components': {
               'database': check_database_health(),
               'openai': check_openai_health(),
               'memory': check_memory_health()
           }
       })
   ```

### Logging Configuration

**Structured Logging Setup:**
```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'customer_id'):
            log_entry['customer_id'] = record.customer_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
            
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('/var/log/banking-ai-agent/application.log'),
        logging.StreamHandler()
    ]
)

# Set formatter
for handler in logging.getLogger().handlers:
    handler.setFormatter(JSONFormatter())
```

### Log Rotation

**Logrotate Configuration (`/etc/logrotate.d/banking-ai-agent`):**
```
/var/log/banking-ai-agent/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 bankingai bankingai
    postrotate
        systemctl reload banking-ai-agent
    endscript
}
```

## Backup and Recovery

### Database Backup

**Automated Backup Script:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/opt/backups/banking-ai-agent"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="banking_agent"

# Create backup directory
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump -h localhost -U banking_agent_user -d $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

**Cron Job for Automated Backups:**
```bash
# Add to crontab
0 2 * * * /opt/scripts/backup_database.sh
```

### Application Data Backup

```bash
#!/bin/bash
# backup_application.sh

BACKUP_DIR="/opt/backups/banking-ai-agent"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/banking-ai-agent"

# Create backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='*.log' \
    $APP_DIR

echo "Application backup completed: $BACKUP_DIR/app_backup_$DATE.tar.gz"
```

### Recovery Procedures

**Database Recovery:**
```bash
# Stop application
sudo systemctl stop banking-ai-agent

# Restore database
gunzip -c /opt/backups/banking-ai-agent/db_backup_YYYYMMDD_HHMMSS.sql.gz | psql -h localhost -U banking_agent_user -d banking_agent

# Start application
sudo systemctl start banking-ai-agent
```

**Application Recovery:**
```bash
# Stop application
sudo systemctl stop banking-ai-agent

# Restore application files
cd /opt
sudo tar -xzf /opt/backups/banking-ai-agent/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Restore permissions
sudo chown -R bankingai:bankingai /opt/banking-ai-agent

# Start application
sudo systemctl start banking-ai-agent
```

## Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check service status
   sudo systemctl status banking-ai-agent
   
   # Check logs
   sudo journalctl -u banking-ai-agent -f
   
   # Check application logs
   tail -f /var/log/banking-ai-agent/application.log
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   psql -h localhost -U banking_agent_user -d banking_agent
   
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database logs
   sudo tail -f /var/log/postgresql/postgresql-13-main.log
   ```

3. **High Memory Usage**
   ```bash
   # Monitor memory usage
   htop
   
   # Check application memory
   ps aux | grep python
   
   # Restart application if needed
   sudo systemctl restart banking-ai-agent
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in /etc/ssl/certs/banking-ai-agent.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect your-domain.com:443
   
   # Renew Let's Encrypt certificate
   sudo certbot renew
   ```

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX idx_customer_sessions ON conversations(customer_id, session_id);
   CREATE INDEX idx_conversation_timestamp ON conversations(created_at);
   
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM conversations WHERE customer_id = 'CUST001';
   ```

2. **Application Optimization**
   ```python
   # Enable connection pooling
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool
   
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20,
       pool_pre_ping=True
   )
   ```

3. **Nginx Optimization**
   ```nginx
   # Enable gzip compression
   gzip on;
   gzip_vary on;
   gzip_min_length 1024;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   
   # Enable caching
   location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

### Monitoring Commands

```bash
# System monitoring
htop                          # System resources
iotop                         # Disk I/O
netstat -tulpn               # Network connections
df -h                        # Disk usage
free -h                      # Memory usage

# Application monitoring
sudo systemctl status banking-ai-agent    # Service status
sudo journalctl -u banking-ai-agent -f    # Service logs
curl http://localhost:5000/health         # Health check
curl http://localhost:9090/metrics        # Prometheus metrics

# Database monitoring
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"  # Active connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_database;"  # Database stats
```

### Emergency Procedures

**Service Recovery:**
```bash
# Quick restart
sudo systemctl restart banking-ai-agent nginx postgresql

# Full system restart
sudo reboot

# Rollback deployment
cd /opt/banking-ai-agent
git checkout previous-stable-tag
sudo systemctl restart banking-ai-agent
```

**Data Recovery:**
```bash
# Restore from latest backup
/opt/scripts/restore_database.sh latest
/opt/scripts/restore_application.sh latest
```

This deployment guide provides comprehensive instructions for deploying the Banking AI Agent in various environments while maintaining security, performance, and reliability standards required for banking applications.

