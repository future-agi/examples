# 🚀 Text-to-SQL Agent - Deployment Guide

This guide provides step-by-step instructions for deploying the Text-to-SQL Agent in various environments.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Network**: Internet access for OpenAI API and BigQuery

### Required Accounts & Services
- **OpenAI API Account**: For GPT-4o access
- **Google Cloud Platform**: For BigQuery (optional for demo)
- **Domain/Hosting**: For production deployment (optional)

## 🔧 Environment Setup

### 1. OpenAI API Configuration

1. **Get API Key**
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Create account or sign in
   - Navigate to API Keys section
   - Create new API key
   - Copy the key (starts with `sk-`)

2. **Set Environment Variable**
   ```bash
   export OPENAI_API_KEY="sk-your-api-key-here"
   ```

### 2. BigQuery Configuration (Production)

1. **Create Google Cloud Project**
   ```bash
   # Install Google Cloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init
   
   # Create project
   gcloud projects create revionics-text2sql --name="Text2SQL"
   gcloud config set project revionics-text2sql
   ```

2. **Enable BigQuery API**
   ```bash
   gcloud services enable bigquery.googleapis.com
   ```

3. **Create Service Account**
   ```bash
   gcloud iam service-accounts create text2sql-agent \
       --display-name="Text2SQL Agent Service Account"
   
   # Grant BigQuery permissions
   gcloud projects add-iam-policy-binding revionics-text2sql \
       --member="serviceAccount:text2sql-agent@revionics-text2sql.iam.gserviceaccount.com" \
       --role="roles/bigquery.dataViewer"
   
   gcloud projects add-iam-policy-binding revionics-text2sql \
       --member="serviceAccount:text2sql-agent@revionics-text2sql.iam.gserviceaccount.com" \
       --role="roles/bigquery.jobUser"
   ```

4. **Download Credentials**
   ```bash
   gcloud iam service-accounts keys create credentials.json \
       --iam-account=text2sql-agent@revionics-text2sql.iam.gserviceaccount.com
   
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"
   ```

5. **Create Dataset and Tables**
   ```bash
   # Create dataset
   bq mk --dataset revionics-text2sql:retail_analytics
   
   # Create sample tables (customize based on your schema)
   bq mk --table revionics-text2sql:retail_analytics.products \
       upc_code:STRING,product_name:STRING,category:STRING,current_price:FLOAT
   
   bq mk --table revionics-text2sql:retail_analytics.pricing \
       upc_code:STRING,price_date:DATE,current_price:FLOAT,suggested_price:FLOAT
   
   bq mk --table revionics-text2sql:retail_analytics.elasticity \
       upc_code:STRING,elasticity_value:FLOAT,category:STRING
   ```

## 🏠 Local Development Deployment

### 1. Quick Start
```bash
# Clone or navigate to project directory
cd revionics-text2sql-agent

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-api-key"
export GOOGLE_CLOUD_PROJECT="revionics-text2sql"
export BIGQUERY_DATASET="retail_analytics"
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"

# Start the application
python src/main.py
```

### 2. Access Points
- **Gradio Interface**: http://localhost:7860
- **Flask API**: http://localhost:6001
- **Health Check**: http://localhost:6001/api/health

### 3. Verification
```bash
# Test API health
curl http://localhost:6001/api/health

# Test query endpoint
curl -X POST http://localhost:6001/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current price for UPC code 123456?"}'
```

## 🐳 Docker Deployment

### 1. Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY credentials.json ./

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Expose ports
EXPOSE 6001 7860

# Start application
CMD ["python", "src/main.py"]
```

### 2. Build and Run
```bash
# Build Docker image
docker build -t revionics-text2sql .

# Run container
docker run -d \
  --name revionics-text2sql \
  -p 6001:6001 \
  -p 7860:7860 \
  -e OPENAI_API_KEY="your-api-key" \
  -e GOOGLE_CLOUD_PROJECT="revionics-text2sql" \
  -e BIGQUERY_DATASET="retail_analytics" \
  revionics-text2sql
```

### 3. Docker Compose
```yaml
version: '3.8'
services:
  text2sql-agent:
    build: .
    ports:
      - "6001:6001"
      - "7860:7860"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - BIGQUERY_DATASET=${BIGQUERY_DATASET}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    volumes:
      - ./credentials.json:/app/credentials.json:ro
      - ./chroma_db:/app/chroma_db
    restart: unless-stopped
```

## ☁️ Cloud Deployment

### Google Cloud Run

1. **Prepare for Cloud Run**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/revionics-text2sql/text2sql-agent
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy text2sql-agent \
     --image gcr.io/revionics-text2sql/text2sql-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 6001 \
     --set-env-vars OPENAI_API_KEY="your-api-key" \
     --set-env-vars GOOGLE_CLOUD_PROJECT="revionics-text2sql" \
     --set-env-vars BIGQUERY_DATASET="retail_analytics" \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300
   ```

3. **Deploy Gradio Interface Separately**
   ```bash
   # Create separate service for Gradio
   gcloud run deploy text2sql-gradio \
     --image gcr.io/revionics-text2sql/text2sql-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 7860 \
     --set-env-vars OPENAI_API_KEY="your-api-key" \
     --memory 2Gi \
     --cpu 2
   ```

### AWS Deployment

1. **Elastic Container Service (ECS)**
   ```bash
   # Build and push to ECR
   aws ecr create-repository --repository-name revionics-text2sql
   docker tag revionics-text2sql:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/revionics-text2sql:latest
   docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/revionics-text2sql:latest
   
   # Create ECS task definition and service
   aws ecs create-cluster --cluster-name revionics-text2sql
   ```

2. **Lambda Deployment** (API only)
   ```bash
   # Use Serverless Framework or AWS SAM
   pip install serverless
   serverless create --template aws-python3 --path text2sql-lambda
   ```

### Azure Deployment

1. **Container Instances**
   ```bash
   az container create \
     --resource-group revionics-rg \
     --name text2sql-agent \
     --image revionics-text2sql:latest \
     --ports 6001 7860 \
     --environment-variables OPENAI_API_KEY="your-api-key" \
     --memory 4 \
     --cpu 2
   ```

## 🔧 Production Configuration

### 1. Environment Variables
```bash
# Required
export OPENAI_API_KEY="sk-your-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export BIGQUERY_DATASET="your-dataset"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Optional
export VECTOR_STORE_PATH="/app/chroma_db"
export ENABLE_CACHE="true"
export MAX_RESULTS="1000"
export LOG_LEVEL="INFO"
export FLASK_ENV="production"
```

### 2. Security Configuration
```bash
# Generate secure secret key
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')

# Configure CORS (if needed)
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Enable HTTPS
export FORCE_HTTPS="true"
```

### 3. Performance Tuning
```bash
# Increase worker processes
export WORKERS="4"
export THREADS="2"

# Configure caching
export REDIS_URL="redis://localhost:6379"
export CACHE_TTL="3600"

# Set resource limits
export MAX_MEMORY="2048m"
export MAX_CPU="1000m"
```

## 📊 Monitoring & Logging

### 1. Application Monitoring
```python
# Add to main.py for production monitoring
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/text2sql.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

### 2. Health Checks
```bash
# Add health check endpoint monitoring
curl -f http://localhost:6001/api/health || exit 1
```

### 3. Performance Metrics
```python
# Add metrics collection
from prometheus_client import Counter, Histogram, generate_latest

query_counter = Counter('text2sql_queries_total', 'Total queries processed')
query_duration = Histogram('text2sql_query_duration_seconds', 'Query processing time')
```

## 🔄 Maintenance & Updates

### 1. Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update vector store
python scripts/update_knowledge_base.py

# Clear caches
curl -X POST http://localhost:6001/api/clear-cache
```

### 2. Backup Procedures
```bash
# Backup vector store
tar -czf chroma_db_backup_$(date +%Y%m%d).tar.gz chroma_db/

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

### 3. Scaling Considerations
- **Horizontal Scaling**: Deploy multiple instances behind load balancer
- **Database Scaling**: Use BigQuery slots for better performance
- **Caching**: Implement Redis for distributed caching
- **CDN**: Use CDN for static assets and API responses

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   ```bash
   # Check API key
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   
   # Check quota
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/usage
   ```

2. **BigQuery Connection Issues**
   ```bash
   # Test credentials
   bq ls
   
   # Check permissions
   gcloud auth application-default print-access-token
   ```

3. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats revionics-text2sql
   
   # Increase memory limits
   docker update --memory 4g revionics-text2sql
   ```

4. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tlnp | grep :6001
   
   # Use different ports
   export FLASK_PORT=5001
   export GRADIO_PORT=7861
   ```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL="DEBUG"
export FLASK_ENV="development"

# Run with debug output
python src/main.py --debug
```

## 📞 Support

For deployment issues:
1. Check logs: `tail -f logs/text2sql.log`
2. Verify environment variables: `env | grep -E "(OPENAI|GOOGLE|BIGQUERY)"`
3. Test individual components: `python -m src.models.text2sql_agent`
4. Contact development team with error logs

## ✅ Deployment Checklist

### Pre-deployment
- [ ] OpenAI API key configured
- [ ] BigQuery credentials set up
- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] Security settings reviewed

### Post-deployment
- [ ] Health check passes
- [ ] API endpoints responding
- [ ] Gradio interface accessible
- [ ] Sample queries working
- [ ] Monitoring configured
- [ ] Backup procedures in place

### Production Readiness
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Rollback plan prepared

---

**Deployment Complete!** 🎉

Your Text-to-SQL Agent is now ready to transform retail analytics through natural language processing.

