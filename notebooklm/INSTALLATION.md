# Installation Guide - NotebookLM Open Source

This comprehensive guide will walk you through setting up NotebookLM on your system, from basic installation to advanced configuration options.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Manual Installation](#manual-installation)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Setup](#advanced-setup)

## System Requirements

### Minimum Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11 with WSL2
- **Memory**: 4GB RAM (8GB recommended)
- **Storage**: 10GB free disk space
- **CPU**: 2 cores (4 cores recommended)
- **Network**: Internet connection for AI API calls

### Software Dependencies

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository
- **curl**: For health checks and testing

### Optional Requirements

- **Python 3.11+**: For local development
- **Node.js 18+**: For frontend development
- **PostgreSQL 15+**: For production database
- **Redis 7+**: For caching and sessions

## Quick Installation

The fastest way to get NotebookLM running is using our automated deployment script.

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/notebooklm-opensource.git
cd notebooklm-opensource
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp notebooklm-backend/.env.example .env

# Edit configuration (see Configuration section below)
nano .env
```

### Step 3: Deploy

```bash
# Make deployment script executable
chmod +x deploy.sh

# Start all services
./deploy.sh start
```

### Step 4: Verify Installation

```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs
```

The application will be available at:
- **Frontend**: http://localhost
- **Backend API**: http://localhost:5050
- **Health Check**: http://localhost:5050/api/health

### Default Login Credentials

- **Email**: test@example.com
- **Password**: password123

## Manual Installation

For development or custom setups, you can install components manually.

### Backend Setup

1. **Create Virtual Environment**
   ```bash
   cd notebooklm-backend
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. **Initialize Database**
   ```bash
   python src/database/init_db.py
   ```

5. **Start Backend Server**
   ```bash
   python src/main.py
   ```

### Frontend Setup

1. **Install Node.js Dependencies**
   ```bash
   cd notebooklm-frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   # Create environment file
   echo "VITE_API_BASE_URL=http://localhost:5050/api" > .env.local
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

### Database Setup

#### SQLite (Development)
SQLite is used by default for development. No additional setup required.

#### PostgreSQL (Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   brew services start postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE notebooklm;
   CREATE USER notebooklm WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE notebooklm TO notebooklm;
   \q
   ```

3. **Update Configuration**
   ```bash
   # In .env file
   DATABASE_URL=postgresql://notebooklm:your_password@localhost:5432/notebooklm
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration:

#### Core Settings
```env
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/notebooklm

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
```

#### AI Provider Configuration

##### OpenAI (Recommended)
```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1
```

##### Anthropic Claude
```env
ANTHROPIC_API_KEY=your-anthropic-api-key
```

##### Google Gemini
```env
GOOGLE_API_KEY=your-google-api-key
```

##### Local LLM (Ollama)
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

#### Vector Database
```env
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### File Upload
```env
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
ALLOWED_EXTENSIONS=pdf,docx,txt,pptx,xlsx
```

#### Audio/TTS
```env
TTS_PROVIDER=openai  # openai, elevenlabs, gtts
ELEVENLABS_API_KEY=your-elevenlabs-key
```

#### CORS and Security
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
```

### Advanced Configuration

#### Custom LLM Providers

To add support for custom LLM providers, modify `src/services/ai_service.py`:

```python
class CustomLLMProvider:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
    
    def generate_response(self, messages, model="custom-model"):
        # Implement your custom LLM integration
        pass
```

#### Custom Document Processors

Add support for new document formats in `src/services/document_processor.py`:

```python
def process_custom_format(self, file_path):
    """Process custom document format"""
    # Implement custom processing logic
    return {
        'text': extracted_text,
        'metadata': document_metadata
    }
```

## Troubleshooting

### Common Issues

#### 1. Docker Permission Errors
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in, or run:
newgrp docker
```

#### 2. Port Already in Use
```bash
# Find process using port
sudo lsof -i :5050
# Kill process
sudo kill -9 <PID>
```

#### 3. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 4. Memory Issues
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory
# Or add to docker-compose.yml:
services:
  backend:
    mem_limit: 2g
```

#### 5. API Key Issues
- Verify API keys are correctly set in `.env`
- Check API key permissions and quotas
- Test API keys independently

### Debugging

#### Enable Debug Mode
```env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

#### View Logs
```bash
# Docker deployment
./deploy.sh logs backend
./deploy.sh logs frontend

# Manual deployment
tail -f notebooklm.log
```

#### Database Debugging
```bash
# Connect to database
docker-compose exec postgres psql -U notebooklm -d notebooklm

# View tables
\dt

# Check user table
SELECT * FROM users;
```

### Performance Optimization

#### Backend Optimization
```env
# Increase worker processes
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=gevent
GUNICORN_TIMEOUT=120

# Enable caching
REDIS_URL=redis://localhost:6379/0
CACHE_TYPE=redis
```

#### Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_sources_notebook_id ON sources(notebook_id);
CREATE INDEX idx_conversations_notebook_id ON conversations(notebook_id);
CREATE INDEX idx_embeddings_source_id ON embeddings(source_id);
```

#### Frontend Optimization
```bash
# Build optimized production bundle
npm run build

# Serve with nginx for better performance
```

## Advanced Setup

### SSL/HTTPS Configuration

#### Using Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Update nginx configuration
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Your existing configuration
}
```

### Load Balancing

#### Multiple Backend Instances
```yaml
# docker-compose.yml
services:
  backend-1:
    build: ./notebooklm-backend
    environment:
      - INSTANCE_ID=1
  
  backend-2:
    build: ./notebooklm-backend
    environment:
      - INSTANCE_ID=2
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
```

#### nginx Load Balancer Configuration
```nginx
upstream backend {
    server backend-1:5050;
    server backend-2:5050;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

### Monitoring and Logging

#### Prometheus Metrics
```python
# Add to requirements.txt
prometheus-flask-exporter==0.21.0

# Add to main.py
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

#### Centralized Logging
```yaml
# docker-compose.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Backup and Recovery

#### Database Backup
```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U notebooklm notebooklm > "$BACKUP_DIR/notebooklm_$DATE.sql"

# Schedule with cron
0 2 * * * /path/to/backup-script.sh
```

#### File Backup
```bash
# Backup uploads and vector database
tar -czf backup_$(date +%Y%m%d).tar.gz uploads/ chroma_db/
```

### Security Hardening

#### Firewall Configuration
```bash
# Ubuntu UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Application Security
```env
# Security headers
SECURITY_HEADERS=true
SECURE_COOKIES=true
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
```

#### Rate Limiting
```python
# Add to requirements.txt
Flask-Limiter==3.5.0

# Add to main.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

This completes the comprehensive installation guide. For additional support, please refer to the main README.md file or open an issue on GitHub.

