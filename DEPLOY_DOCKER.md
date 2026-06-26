[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/your-repo/swarm-trader/tree/main)

# 🐳 Docker Deployment

## Quick Start

```bash
# Build image
docker build -t swarm-macro .

# Run container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/state:/app/state \
  -e FRED_API_KEY=your_key \
  -e ALPHA_VANTAGE_KEY=your_key \
  --name swarm-macro \
  swarm-macro
```

## Docker Compose (Recommended)

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Files

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/macro || exit 1

# Run
CMD ["python", "web/server.py"]
```

### `docker-compose.yml`
```yaml
version: '3.8'

services:
  macro-dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FRED_API_KEY=${FRED_API_KEY}
      - ALPHA_VANTAGE_KEY=${ALPHA_VANTAGE_KEY}
    volumes:
      - ./state:/app/state
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/macro"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### `requirements.txt`
```
flask==3.0.0
flask-cors==4.0.0
aiohttp==3.9.1
requests==2.31.0
```

### `.env.example`
```bash
FRED_API_KEY=your_fred_key_here
ALPHA_VANTAGE_KEY=your_av_key_here
```

## Deployment to Cloud

### Google Cloud Run
```bash
gcloud run deploy swarm-macro \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FRED_API_KEY=xxx,ALPHA_VANTAGE_KEY=xxx
```

### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag swarm-macro:latest <account>.dkr.ecr.us-east-1.amazonaws.com/swarm-macro:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/swarm-macro:latest

# Deploy to ECS (via console or CLI)
```

### Azure Container Instances
```bash
az container create \
  --resource-group myResourceGroup \
  --name swarm-macro \
  --image swarm-macro:latest \
  --dns-name-label swarm-macro \
  --ports 5000 \
  --environment-variables FRED_API_KEY=xxx ALPHA_VANTAGE_KEY=xxx
```

## Production Considerations

1. **Use secrets management** (AWS Secrets Manager, GCP Secret Manager)
2. **Add logging** (ELK stack, CloudWatch, etc.)
3. **Setup monitoring** (Prometheus, Grafana, Datadog)
4. **Configure auto-scaling** based on CPU/memory
5. **Add SSL/TLS** termination at load balancer
6. **Implement rate limiting** for API endpoints
