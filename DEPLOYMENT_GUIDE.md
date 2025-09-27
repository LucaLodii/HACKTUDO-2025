# sofIA Deployment Guide - Agent + WhatsApp Bridge

This guide shows you how to deploy both the **sofIA Python Payment Agent** and the **WhatsApp WebSocket Bridge** together.

## 🏗️ Architecture Overview

```
WhatsApp Phone ←→ WhatsApp Web.js ←→ Node.js Bridge ←→ Python sofIA Agent
                                                              ↓
                                                     AP2 Protocol Processing
```

**Two Services:**
1. **sofIA Payment Agent** (Python FastAPI) - Port 8000
2. **WhatsApp Bridge** (Node.js WebSocket) - Port 3001

## 🚀 Quick Deployment (Docker Compose)

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit with your values
nano .env
```

**Required Environment Variables:**
```bash
# Google AI Configuration (Required)
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# AP2 Protocol Configuration
AGENT_ID=sofia-whatsapp-agent
MERCHANT_ID=sofia-merchant

# Security Configuration
JWT_SECRET=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

### 2. Deploy Both Services

```bash
# Build and start both services
docker-compose up -d

# Check service status
docker-compose ps

# View logs for both services
docker-compose logs -f sofia-payment-agent
docker-compose logs -f whatsapp-bridge
```

### 3. Verify Deployment

```bash
# Check sofIA Agent health
curl http://localhost:8000/health

# Check WhatsApp Bridge health
curl http://localhost:3001/health

# Expected responses:
# sofIA: {"status": "healthy", "service": "sofIA WhatsApp Payment Agent", "ap2_ready": true}
# Bridge: {"status": "healthy", "whatsapp_ready": false, "service": "sofIA WhatsApp Bridge"}
```

### 4. Connect WhatsApp

1. **Check bridge logs for QR code:**
   ```bash
   docker-compose logs -f whatsapp-bridge
   ```

2. **Scan QR code** with your WhatsApp phone
3. **Wait for connection:** Look for "WhatsApp client is ready!"
4. **Test:** Send a message to your WhatsApp number

## 🔧 Manual Deployment (Without Docker)

### 1. Deploy sofIA Python Agent

```bash
# Install Python dependencies
uv sync

# Set environment variables
export GOOGLE_API_KEY=your_key
export HOST=0.0.0.0
export PORT=8000

# Start the agent
uv run app.py
```

### 2. Deploy WhatsApp Bridge

```bash
# Navigate to bridge directory
cd whatsapp-bridge

# Install Node.js dependencies
npm install

# Set environment variables
export SOFIA_API_URL=http://localhost:8000
export PORT=3001

# Start the bridge
npm start
```

### 3. Connect WhatsApp

1. **Scan QR code** from bridge terminal
2. **Wait for "WhatsApp client is ready!"**
3. **Test the connection**

## 🌐 Cloud Deployment Options

### Option 1: Google Cloud Run (Recommended)

**Deploy sofIA Agent:**
```bash
# Build and deploy agent
gcloud run deploy sofia-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_API_KEY=your_key,HOST=0.0.0.0,PORT=8000"
```

**Deploy WhatsApp Bridge:**
```bash
# Build and deploy bridge
cd whatsapp-bridge
gcloud run deploy whatsapp-bridge \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="SOFIA_API_URL=https://sofia-agent-url.run.app,PORT=3001"
```

### Option 2: AWS ECS

**Create ECS Task Definition:**
```json
{
  "family": "sofia-services",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "sofia-agent",
      "image": "your-registry/sofia-agent:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "GOOGLE_API_KEY", "value": "your_key"},
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "PORT", "value": "8000"}
      ]
    },
    {
      "name": "whatsapp-bridge",
      "image": "your-registry/whatsapp-bridge:latest",
      "portMappings": [{"containerPort": 3001}],
      "environment": [
        {"name": "SOFIA_API_URL", "value": "http://localhost:8000"},
        {"name": "PORT", "value": "3001"}
      ],
      "dependsOn": [{"containerName": "sofia-agent", "condition": "START"}]
    }
  ]
}
```

### Option 3: DigitalOcean App Platform

**Create `.do/app.yaml`:**
```yaml
name: sofia-payment-system
services:
- name: sofia-agent
  source_dir: /
  github:
    repo: your-username/sofia-payment-agent
    branch: main
  run_command: uv run app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: GOOGLE_API_KEY
    value: your_google_api_key
  - key: HOST
    value: 0.0.0.0
  - key: PORT
    value: "8000"

- name: whatsapp-bridge
  source_dir: /whatsapp-bridge
  github:
    repo: your-username/sofia-payment-agent
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SOFIA_API_URL
    value: ${sofia-agent.URL}
  - key: PORT
    value: "3001"
```

## 🔍 Service Communication

### Internal Communication
- **Bridge → Agent:** `http://sofia-payment-agent:8000/process-whatsapp-message`
- **Agent → Bridge:** `http://whatsapp-bridge:3001/send-message`

### External Access
- **sofIA Agent API:** `http://localhost:8000`
- **WhatsApp Bridge API:** `http://localhost:3001`
- **Health Checks:** `/health` endpoint on both services

## 📊 Monitoring & Logs

### Docker Compose Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f sofia-payment-agent
docker-compose logs -f whatsapp-bridge

# View last 100 lines
docker-compose logs --tail=100 whatsapp-bridge
```

### Health Monitoring
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:3001/health

# Check WhatsApp connection status
curl http://localhost:3001/client-info
```

## 🛠️ Troubleshooting

### Common Issues

**1. WhatsApp Bridge Not Connecting**
```bash
# Check bridge logs
docker-compose logs whatsapp-bridge

# Clear WhatsApp session
docker-compose exec whatsapp-bridge rm -rf /app/.wwebjs_auth
docker-compose restart whatsapp-bridge
```

**2. Agent Not Responding**
```bash
# Check agent logs
docker-compose logs sofia-payment-agent

# Verify Google API key
docker-compose exec sofia-payment-agent env | grep GOOGLE_API_KEY
```

**3. Services Can't Communicate**
```bash
# Check network connectivity
docker-compose exec whatsapp-bridge ping sofia-payment-agent
docker-compose exec sofia-payment-agent ping whatsapp-bridge

# Check service URLs
docker-compose exec whatsapp-bridge curl http://sofia-payment-agent:8000/health
```

**4. Port Conflicts**
```bash
# Check port usage
lsof -i :8000
lsof -i :3001

# Kill conflicting processes
sudo kill -9 <PID>
```

### Reset Everything
```bash
# Stop all services
docker-compose down

# Remove volumes (clears WhatsApp session)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build
```

## 🚀 Production Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] Google API key set
- [ ] SSL certificate obtained (for HTTPS)
- [ ] Domain configured
- [ ] Monitoring setup

### Security
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] API keys rotated
- [ ] Firewall configured
- [ ] Backup strategy implemented

### Testing
- [ ] Both services health checks passing
- [ ] WhatsApp bridge connected
- [ ] Message flow working
- [ ] AP2 protocol functioning
- [ ] Error handling verified

## 📱 Testing the Complete System

### 1. Send Test Message
```bash
# Send message via WhatsApp to your connected number
# Message: "Hello sofIA"
```

### 2. Check Logs
```bash
# Watch both services process the message
docker-compose logs -f
```

### 3. Verify Response
- You should receive a response from sofIA
- Check logs for AP2 protocol processing
- Verify payment flow if testing purchase intent

## 🎯 Next Steps

1. **Deploy using your preferred method**
2. **Connect WhatsApp and test**
3. **Set up monitoring and alerts**
4. **Configure production environment variables**
5. **Test payment flows with real transactions**

Your sofIA payment system is now ready for production use! 🚀

