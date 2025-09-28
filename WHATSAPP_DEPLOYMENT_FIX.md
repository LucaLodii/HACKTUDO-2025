# WhatsApp QR Code Deployment Fix Guide

## Problem
WhatsApp Web.js QR code is not accessible during deployment, preventing connection setup.

## Root Causes
1. **Network Access**: QR code interface not exposed publicly
2. **Container Resources**: Puppeteer crashes in cloud environments
3. **Session Persistence**: Auth data lost between deployments

## Solutions

### 1. Access QR Code Interface

**Option A: Via NGINX Reverse Proxy (Recommended)**
```
https://your-domain.com/qr
```

**Option B: Direct Port Access**
```
http://your-domain.com:3001/qr
```

### 2. Environment Variables for Cloud Deployment

Add to your deployment environment:
```bash
# Increase memory for Puppeteer
NODE_OPTIONS="--max-old-space-size=1024"

# Puppeteer specific
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
```

### 3. Docker Optimization

**For Cloud Platforms (Render, Railway, etc.):**

Create `whatsapp-bridge/Dockerfile.cloud`:
```dockerfile
FROM node:18-alpine

# Install Chrome for Puppeteer
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

# Set Puppeteer to use installed Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV NODE_OPTIONS="--max-old-space-size=1024"

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

COPY . .

EXPOSE 3001
CMD ["node", "server.js"]
```

### 4. Update Docker Compose for Better Resource Management

```yaml
whatsapp-bridge:
  build:
    context: ./whatsapp-bridge
    dockerfile: Dockerfile.cloud  # Use cloud-optimized dockerfile
  ports:
    - "3001:3001"
  environment:
    - SOFIA_API_URL=http://sofia-payment-agent:8000
    - PORT=3001
    - NODE_OPTIONS=--max-old-space-size=1024
    - PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
  volumes:
    - ./whatsapp-bridge/.wwebjs_auth:/app/.wwebjs_auth
    - ./logs:/app/logs
  restart: unless-stopped
  deploy:
    resources:
      limits:
        memory: 1G
      reservations:
        memory: 512M
  depends_on:
    - sofia-payment-agent
```

### 5. Session Persistence Strategy

**Local Development:**
1. Connect once locally with `npm start` in whatsapp-bridge/
2. Copy `.wwebjs_auth` folder to deployment
3. Upload as persistent volume

**Cloud Deployment:**
1. Use volume mounting for `.wwebjs_auth`
2. Connect via QR once, then sessions persist
3. Monitor `/bridge/health` endpoint for connection status

## Step-by-Step Deployment Process

### 1. Pre-deployment Setup
```bash
# Build and test locally first
cd whatsapp-bridge
npm install
npm start

# Wait for QR code, scan with WhatsApp
# Verify connection works locally
```

### 2. Deploy with QR Access
```bash
# Deploy your application
docker-compose up -d

# Check services are running
docker-compose ps

# Access QR interface
curl http://your-domain.com/qr
```

### 3. Connect WhatsApp
1. Navigate to `https://your-domain.com/qr`
2. Open WhatsApp on phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code displayed on the page
5. Wait for "WhatsApp Connected" status

### 4. Verify Connection
```bash
# Test health endpoint
curl http://your-domain.com/bridge/health

# Should return:
{
  "status": "healthy",
  "whatsapp_ready": true,
  "service": "sofIA WhatsApp Bridge"
}
```

## Troubleshooting

### QR Code Not Loading
- Check container logs: `docker-compose logs whatsapp-bridge`
- Verify Puppeteer args in server.js:212-250
- Increase container memory allocation

### QR Code Not Accessible
- Verify nginx configuration includes QR routes
- Check port 3001 is exposed in docker-compose.yml
- Test direct access: `http://your-domain.com:3001/qr`

### Connection Fails After Scanning
- Monitor logs for "WhatsApp client is ready!" message
- Verify `.wwebjs_auth` volume is persistent
- Check WhatsApp hasn't logged out the session

### Puppeteer Crashes
- Add `--no-sandbox --disable-setuid-sandbox` args
- Increase `--max-old-space-size` memory limit
- Use Alpine Linux with pre-installed Chrome

## Quick Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs whatsapp-bridge

# Restart WhatsApp bridge
docker-compose restart whatsapp-bridge

# Access QR interface
open https://your-domain.com/qr

# Test API endpoint
curl https://your-domain.com/bridge/health
```

## Cloud Platform Specific Notes

### Render.com
- Use Web Service type
- Set `NODE_OPTIONS=--max-old-space-size=1024`
- QR access: `https://your-app.onrender.com/qr`

### Railway.app
- Use Dockerfile.cloud
- Add `RAILWAY_STATIC_URL` for external access
- QR access: `https://your-app.railway.app/qr`

### Heroku
- Use heroku/nodejs buildpack + puppeteer buildpack
- Set dyno type to Standard (1GB memory minimum)
- QR access: `https://your-app.herokuapp.com/qr`

The key is ensuring the QR interface is publicly accessible and Puppeteer has sufficient resources to run Chrome in your deployment environment.