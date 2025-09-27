# sofIA Environment Setup Guide

## Quick Start

For the **fastest setup**, you only need **2 environment variables**:

```bash
# Copy minimal template
cp env.minimal .env

# Edit .env and add your values
GOOGLE_API_KEY=your-actual-google-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-actual-supabase-key
```

## Required Environment Variables

### 🔑 **Essential (Must Have)**

| Variable | Description | How to Get |
|----------|-------------|------------|
| `GOOGLE_API_KEY` | Google Gemini AI API key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `SUPABASE_URL` | Your Supabase project URL | [Supabase Dashboard](https://supabase.com/dashboard) |
| `SUPABASE_KEY` | Your Supabase anon key | [Supabase Dashboard](https://supabase.com/dashboard) |

### 📱 **WhatsApp Integration**

| Variable | Description | Default |
|----------|-------------|---------|
| `WHATSAPP_BRIDGE_URL` | Node.js bridge service URL | `http://localhost:3001` |

### 🏢 **BEMOBI Integration (Optional)**

| Variable | Description | When Needed |
|----------|-------------|-------------|
| `BEMOBI_API_KEY` | BEMOBI API key | Only for real BEMOBI integration |
| `BEMOBI_SECRET_KEY` | BEMOBI secret key | Only for real BEMOBI integration |

## Step-by-Step Setup

### 1. **Google API Key Setup**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Add to `.env`: `GOOGLE_API_KEY=your-key-here`

### 2. **Supabase Setup**

1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy your Project URL and anon public key
5. Add to `.env`:
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-key-here
   ```

### 3. **Database Schema Setup**

1. In your Supabase project, go to SQL Editor
2. Copy the contents of `database/schema.sql`
3. Run the SQL to create all tables
4. (Optional) Run `database/seed_data.sql` for sample data

### 4. **WhatsApp Bridge Setup**

1. Install Node.js dependencies:
   ```bash
   cd whatsapp-bridge
   npm install
   ```

2. Start the bridge service:
   ```bash
   npm start
   ```

3. The bridge will be available at `http://localhost:3001`

### 5. **Run sofIA**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

## Environment Templates

### **Minimal Setup** (`env.minimal`)
For quick development with just the essentials:
```bash
cp env.minimal .env
```

### **Complete Setup** (`env.template`)
For production deployment with all features:
```bash
cp env.template .env
```

## Testing Without External Services

**Great news!** sofIA works with **mock data** by default:

- ✅ **No Google API needed** for testing
- ✅ **No Supabase needed** for testing  
- ✅ **No WhatsApp bridge needed** for testing
- ✅ **All tools use mock data** automatically

Just run:
```bash
python app.py
```

The system will use mock Brazilian telecom data (VIVO, CLARO, OI, TIM) for all operations.

## Environment Variable Categories

### **Core Application**
```bash
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### **AI Services**
```bash
GOOGLE_API_KEY=your-key
GOOGLE_CLOUD_PROJECT=your-project
```

### **Database**
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
DATABASE_URL=postgresql://...
```

### **WhatsApp**
```bash
WHATSAPP_BRIDGE_URL=http://localhost:3001
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-id
```

### **BEMOBI (Optional)**
```bash
BEMOBI_API_KEY=your-key
BEMOBI_SECRET_KEY=your-secret
BEMOBI_BASE_URL=https://api.bemobi.com/v1
```

### **Business Configuration**
```bash
DEFAULT_CURRENCY=BRL
DEFAULT_TIMEZONE=America/Sao_Paulo
DEFAULT_LANGUAGE=pt-BR
```

### **Subscription Management**
```bash
ENABLE_PROACTIVE_REMINDERS=true
REMINDER_CHECK_INTERVAL_MINUTES=60
AUTO_SCHEDULE_RENEWALS=true
```

### **Security & Performance**
```bash
ENCRYPT_SENSITIVE_DATA=true
AUDIT_ALL_OPERATIONS=true
RATE_LIMIT_PER_MINUTE=100
CACHE_SUBSCRIPTION_DATA_MINUTES=5
```

## Troubleshooting

### **Common Issues**

#### 1. "No module named 'google'"
- **Solution**: This is expected in test mode. The system uses mocks.

#### 2. "Supabase connection failed"
- **Solution**: Check your `SUPABASE_URL` and `SUPABASE_KEY`. The system will use mock data if connection fails.

#### 3. "WhatsApp bridge not responding"
- **Solution**: Start the bridge with `cd whatsapp-bridge && npm start`

#### 4. "Google API key invalid"
- **Solution**: Get a new key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### **Validation Commands**

Check your setup:
```bash
# Validate environment
python validate_subscription_system.py

# Run tests
python run_tests.py --mode quick

# Check dependencies
python run_tests.py --check-deps
```

## Security Best Practices

### **Never Commit .env Files**
```bash
# .env should be in .gitignore
echo ".env" >> .gitignore
```

### **Use Strong Keys**
- Generate long, random API keys
- Rotate keys regularly
- Use different keys for different environments

### **Environment-Specific Values**
- Development: Use test/sandbox keys
- Production: Use production keys
- Staging: Use staging keys

## Production Deployment

### **Required for Production**
```bash
ENVIRONMENT=production
DEBUG=false
ENCRYPT_SENSITIVE_DATA=true
AUDIT_ALL_OPERATIONS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### **Optional for Production**
```bash
# Monitoring
ENABLE_METRICS=true
MONITORING_ENDPOINT=https://monitoring.com

# Backup
ENABLE_AUTO_BACKUP=true
BACKUP_INTERVAL_HOURS=24

# Rate limiting
RATE_LIMIT_PER_MINUTE=1000
```

## Quick Reference

### **Minimal Working Setup**
```bash
GOOGLE_API_KEY=your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
WHATSAPP_BRIDGE_URL=http://localhost:3001
```

### **Test Mode (No External Services)**
```bash
# Just run without any .env file
python app.py
# System will use mock data automatically
```

### **Development Mode**
```bash
ENVIRONMENT=development
DEBUG=true
MOCK_MODE=false
LOG_REQUESTS=true
VERBOSE_ERRORS=true
```

---

## Summary

**For immediate testing**: No .env file needed - uses mock data
**For development**: 3 variables needed (Google API + Supabase)
**For production**: Complete configuration with security settings

The system is designed to **gracefully fall back to mock data** when external services are unavailable, making it easy to develop and test without complex setup! 🚀
