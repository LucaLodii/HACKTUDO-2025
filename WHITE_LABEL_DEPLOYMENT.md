# sofIA White-label Deployment Guide

## Overview

sofIA now supports true white-label deployment where each telecom operator (VIVO, CLARO, OI, TIM) gets their own isolated instance of sofIA with only their subscription plans and branding.

## Architecture

Each operator deployment includes:
- **Separate WhatsApp phone numbers** for each operator
- **Operator-specific sofIA instances** with isolated configurations
- **Operator-only subscription plans** (no cross-contamination)
- **Branded user experience** with operator colors and messaging
- **Separate Bemobi merchant credentials** for each operator

## Quick Start

### 1. Choose Your Operator

Deploy sofIA for your specific operator:

```bash
# Deploy for VIVO (Purple branding)
./scripts/deploy_vivo.sh

# Deploy for CLARO (Red branding)  
./scripts/deploy_claro.sh

# Deploy for OI (Yellow branding)
./scripts/deploy_oi.sh

# Deploy for TIM (Blue branding)
./scripts/deploy_tim.sh
```

### 2. Configure Your Environment

Each operator has its own environment file:

- **VIVO**: `.env.vivo`
- **CLARO**: `.env.claro`
- **OI**: `.env.oi`
- **TIM**: `.env.tim`

**Required Configuration:**
```bash
# Set your Google API key in the operator's .env file
GOOGLE_API_KEY=your_actual_google_api_key_here

# Operator-specific configuration (already set)
OPERATOR_NAME=VIVO
OPERATOR_DISPLAY_NAME=Vivo
OPERATOR_ID=11111111-1111-1111-1111-111111111111
BRAND_COLOR=#8B2797
```

### 3. Test the Deployment

```bash
# Test with uv (recommended)
uv run python test_white_label.py

# Or test manually
uv run python -c "
from sofIA.tools.operator_subscription_manager import MerchantSubscriptionManager
import asyncio

# Test VIVO plans
manager = MerchantSubscriptionManager('VIVO')
result = asyncio.run(manager.get_available_plans())
print(f'VIVO has {len(result[\"plans\"])} plans')
"
```

## Operator-Specific Features

### VIVO (Purple Branding)
- **4 subscription plans** (Basic 5GB to Infinity 50GB)
- **Price range**: R$ 29.90 - R$ 129.90/month
- **Payment methods**: PIX, Card, Boleto, VIVO Wallet
- **Features**: WhatsApp free, unlimited calls, streaming apps

### CLARO (Red Branding)
- **4 subscription plans** (Easy 3GB to Unlimited 30GB)
- **Price range**: R$ 19.90 - R$ 99.90/month
- **Payment methods**: PIX, Card, Boleto, CLARO Pay
- **Features**: Netflix included, social media free, unlimited calls

### OI (Yellow Branding)
- **4 subscription plans** (Simples 2GB to Premium 25GB)
- **Price range**: R$ 15.90 - R$ 89.90/month
- **Payment methods**: PIX, Card, Boleto, OI Money
- **Features**: Music streaming, video streaming, social media free

### TIM (Blue Branding)
- **4 subscription plans** (Light 4GB to Black Família 60GB)
- **Price range**: R$ 24.90 - R$ 119.90/month
- **Payment methods**: PIX, Card, Boleto, TIM Pay
- **Features**: Netflix TIM, Paramount+, Deezer Premium, family sharing

## User Experience Flow

### 1. Operator Detection
When a user messages the operator's WhatsApp number:
```
User: "Quero contratar um plano"
sofIA: "Olá! Sou a sofIA, assistente de pagamentos da VIVO. 
        Vou te ajudar a escolher o melhor plano VIVO para você!"
```

### 2. Plan Selection
sofIA shows only the operator's plans:
```
📱 Planos VIVO Disponíveis

1. Vivo Basic 5GB
💰 R$ 29.90/mês
📊 5GB de internet
📞 Ligações ilimitadas
💬 100 SMS

2. Vivo Premium 10GB
💰 R$ 49.90/mês
📊 10GB de internet
📞 Ligações ilimitadas
💬 SMS ilimitados
```

### 3. AP2 Payment Processing
All payments are processed through the AP2 Protocol with operator-specific credentials:
- **Intent Mandate**: Captures user's intent to subscribe
- **Cart Mandate**: Creates operator-specific subscription cart
- **Payment Mandate**: Processes payment with operator's Bemobi credentials

## Production Deployment

### Docker Deployment

```bash
# Build operator-specific image
docker build -t sofia-vivo -f Dockerfile.vivo .
docker build -t sofia-claro -f Dockerfile.claro .
docker build -t sofia-oi -f Dockerfile.oi .
docker build -t sofia-tim -f Dockerfile.tim .

# Deploy with operator environment
docker run -d --env-file .env.vivo -p 8000:8000 sofia-vivo
docker run -d --env-file .env.claro -p 8001:8000 sofia-claro
docker run -d --env-file .env.oi -p 8002:8000 sofia-oi
docker run -d --env-file .env.tim -p 8003:8000 sofia-tim
```

### Environment Variables

Each operator needs these environment variables:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key

# Operator Identity
OPERATOR_NAME=VIVO
OPERATOR_DISPLAY_NAME=Vivo
OPERATOR_ID=11111111-1111-1111-1111-111111111111

# Branding
BRAND_COLOR=#8B2797
BRAND_LOGO_URL=https://example.com/logo.png

# Bemobi Integration
BEMOBI_USE_MOCK=true
BEMOBI_MERCHANT_ID=MOCK_VIVO_MERCHANT_001
BEMOBI_API_KEY=mock_vivo_api_key_123456789
BEMOBI_SECRET_KEY=mock_vivo_secret_987654321

# WhatsApp Bridge
WHATSAPP_BRIDGE_URL=http://whatsapp-bridge:3001

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Monitoring & Logs

### Health Checks
```bash
# Check operator-specific health
curl http://localhost:8000/health

# Response includes operator information
{
  "status": "healthy",
  "service": "sofIA VIVO Payment Agent",
  "operator": "VIVO",
  "ap2_ready": true
}
```

### Logs
Each operator instance logs with its branding:
```
🏷️  Initializing WHITE-LABEL sofIA for: Vivo
🤖 Agent: sofIA VIVO Payment Agent
🎨 Brand Color: #8B2797
📱 AP2 Protocol Implementation for Secure Payments
```

## Security & Compliance

### AP2 Protocol Compliance
- **Agent Authentication**: Each operator has unique agent credentials
- **Mandate Verification**: All transactions use AP2 cryptographic signatures
- **Audit Trails**: Complete transaction logs for regulatory compliance
- **Data Isolation**: Operator data is completely isolated

### Bemobi Integration
- **Mock Mode**: Development uses mock Bemobi gateway
- **Production Mode**: Real Bemobi API with operator-specific credentials
- **Webhook Security**: HMAC-SHA256 signature verification
- **Regional Compliance**: Supports LATAM, Africa, and Asia regions

## Troubleshooting

### Common Issues

1. **"No plans found for operator"**
   ```bash
   # Check operator name is correct
   echo $OPERATOR_NAME
   
   # Verify subscription manager
   uv run python -c "
   from sofIA.tools.operator_subscription_manager import MerchantSubscriptionManager
   import asyncio
   manager = MerchantSubscriptionManager('VIVO')
   result = asyncio.run(manager.get_available_plans())
   print(result)
   "
   ```

2. **"Environment configuration not found"**
   ```bash
   # Ensure .env file exists for your operator
   ls -la .env.vivo .env.claro .env.oi .env.tim
   
   # Copy operator environment to .env
   cp .env.vivo .env
   ```

3. **"AP2 authentication failed"**
   ```bash
   # Check Google API key
   grep GOOGLE_API_KEY .env
   
   # Verify API key is valid
   uv run python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print('API Key set:', bool(os.getenv('GOOGLE_API_KEY')))
   "
   ```

## Support

For white-label deployment support:
- **Documentation**: Check this guide and the main PRD
- **Testing**: Use `test_white_label.py` to verify implementation
- **Logs**: Check application logs for operator-specific information
- **Health**: Use `/health` endpoint to verify operator configuration

---

**🎉 Congratulations!** You now have a fully white-labeled sofIA deployment where each telecom operator gets their own isolated instance with only their plans and branding.
