# Complete PagSeguro Setup Guide for sofIA Integration

## 🚀 Step-by-Step Setup Process

### 1. PagSeguro Account Creation

#### Go to PagSeguro Website

- **URL**: https://pagseguro.uol.com.br/
- **Click**: "Criar conta" (Create account)

#### Choose Account Type

- **Pessoa Jurídica** (Business) - Recommended for commercial use
- **Pessoa Física** (Individual) - For personal projects

#### Required Information

```
Business Account (Pessoa Jurídica):
- CNPJ (Business tax ID)
- Company name
- Business email
- Phone number
- Business address

Individual Account (Pessoa Física):
- CPF (Individual tax ID)
- Full name
- Personal email
- Phone number
- Address
```

### 2. Developer Dashboard Access

#### Navigate to Developer Area

1. **Login** to your PagSeguro account
2. **Go to**: https://dev.pagseguro.uol.com.br/
3. **Click**: "Minhas Aplicações" (My Applications)
4. **Click**: "Criar nova aplicação" (Create new application)

#### Application Configuration

```
Application Name: sofIA WhatsApp Payment Agent
Description: AI payment agent for WhatsApp transactions
Application Type: E-commerce
Integration Type: Transparent Checkout
```

### 3. Getting API Credentials

#### In the Developer Dashboard:

1. **Select your application**
2. **Go to "Credenciais"** (Credentials) tab
3. **You'll find these credentials**:

```bash
# Sandbox Credentials (for testing)
PAGSEGURO_CLIENT_ID=your_sandbox_client_id
PAGSEGURO_CLIENT_SECRET=your_sandbox_client_secret
PAGSEGURO_ACCESS_TOKEN=your_sandbox_access_token

# Production Credentials (for live payments)
PAGSEGURO_CLIENT_ID=your_production_client_id
PAGSEGURO_CLIENT_SECRET=your_production_client_secret
PAGSEGURO_ACCESS_TOKEN=your_production_access_token
```

#### Screenshot Locations:

- **Client ID**: Usually labeled as "App ID" or "Client ID"
- **Client Secret**: Usually labeled as "App Key" or "Client Secret"
- **Access Token**: Usually labeled as "Token" or "Access Token"

### 4. Environment Configuration

#### Create `.env` file in your project root:

```bash
# PagSeguro API Credentials (START WITH SANDBOX)
PAGSEGURO_CLIENT_ID=your_sandbox_client_id_here
PAGSEGURO_CLIENT_SECRET=your_sandbox_client_secret_here
PAGSEGURO_ACCESS_TOKEN=your_sandbox_access_token_here

# Environment Configuration
PAGSEGURO_ENVIRONMENT=sandbox  # IMPORTANT: Start with sandbox!
PAGSEGURO_BASE_URL=https://sandbox.api.pagseguro.com

# Development Settings
PAGSEGURO_USE_MOCK=false  # Set to false to use real sandbox
PAGSEGURO_WEBHOOK_URL=https://your-domain.com/webhooks/pagseguro

# Required for AP2 Protocol
GOOGLE_API_KEY=your_google_api_key_here
```

### 5. Webhook Configuration

#### In PagSeguro Dashboard:

1. **Go to your application settings**
2. **Find "Notificações"** (Notifications) or "Webhooks"
3. **Add webhook URL**: `https://your-domain.com/webhooks/pagseguro`
4. **Select events**:
   - Payment status changes
   - Transaction updates
   - Refund notifications

#### Webhook URL Requirements:

- Must be HTTPS (SSL certificate required)
- Must return HTTP 200 OK
- Must be publicly accessible
- Should handle POST requests

### 6. Testing Setup

#### Test with Sandbox First:

```bash
# In your .env file
PAGSEGURO_ENVIRONMENT=sandbox
PAGSEGURO_USE_MOCK=false
```

#### Run Test:

```bash
# Test the integration
python examples/pagseguro_integration_example.py
```

### 7. Production Deployment

#### When ready for production:

```bash
# Update .env file
PAGSEGURO_ENVIRONMENT=production
PAGSEGURO_CLIENT_ID=your_production_client_id
PAGSEGURO_CLIENT_SECRET=your_production_client_secret
PAGSEGURO_ACCESS_TOKEN=your_production_access_token
PAGSEGURO_BASE_URL=https://api.pagseguro.com
PAGSEGURO_USE_MOCK=false
```

## 🔍 Where to Find Each Credential

### In PagSeguro Developer Dashboard:

#### Client ID (App ID)

- **Location**: Application → Credentials → "App ID" or "Client ID"
- **Format**: Usually alphanumeric string
- **Example**: `app123456789`

#### Client Secret (App Key)

- **Location**: Application → Credentials → "App Key" or "Client Secret"
- **Format**: Long alphanumeric string
- **Example**: `abcd1234efgh5678ijkl9012mnop3456`
- **⚠️ Keep this secret!**

#### Access Token

- **Location**: Application → Credentials → "Token" or "Access Token"
- **Format**: Long string starting with letters
- **Example**: `E11B3B6E4A5F4C7D8E9F0A1B2C3D4E5F`
- **⚠️ Keep this secret!**

## 🛠️ Common Setup Issues & Solutions

### Issue 1: "Invalid credentials"

**Solution**:

- Verify you're using sandbox credentials with sandbox environment
- Check for extra spaces in credential strings
- Ensure credentials are from the correct application

### Issue 2: "Webhook not receiving notifications"

**Solution**:

- Verify webhook URL is HTTPS
- Test webhook URL returns 200 OK
- Check firewall settings
- Verify webhook is configured in PagSeguro dashboard

### Issue 3: "Payment processing failed"

**Solution**:

- Start with sandbox environment
- Use test card numbers provided by PagSeguro
- Verify customer data format (CPF, phone, etc.)
- Check PagSeguro API status

### Issue 4: "Token validation failed"

**Solution**:

- Ensure you're using PagSeguro's tokenization service
- Verify token format and expiration
- Check if token was generated for correct environment

## 📋 Pre-Launch Checklist

### Sandbox Testing

- [ ] PagSeguro sandbox account created
- [ ] Application created in developer dashboard
- [ ] Sandbox credentials configured in .env
- [ ] Test payments working with sandbox
- [ ] Webhook receiving notifications
- [ ] Error handling tested

### Production Preparation

- [ ] Business verification completed (if required)
- [ ] Production credentials obtained
- [ ] SSL certificate installed
- [ ] Webhook URL configured and tested
- [ ] Customer data validation implemented
- [ ] Transaction logging configured
- [ ] Monitoring and alerts setup

### Compliance & Security

- [ ] PCI DSS compliance reviewed
- [ ] Customer data protection implemented
- [ ] Audit logging configured
- [ ] Error monitoring setup
- [ ] Backup and recovery plan
- [ ] Security testing completed

## 📞 Support Resources

### PagSeguro Support

- **Developer Documentation**: https://dev.pagseguro.uol.com.br/docs
- **API Reference**: https://dev.pagseguro.uol.com.br/reference
- **Support Portal**: https://pagseguro.uol.com.br/atendimento
- **Developer Forum**: Available in PagSeguro developer area

### Test Cards for Sandbox

```
Credit Card (Approved):
Number: 4111111111111111
CVV: 123
Expiry: 12/2030
Name: JOSE DA SILVA

Credit Card (Declined):
Number: 4000000000000002
CVV: 123
Expiry: 12/2030
Name: JOSE DA SILVA

PIX Test:
Use any valid email or phone number in sandbox
```

### Integration Support

If you need help with the sofIA integration:

1. Check the logs for detailed error messages
2. Verify environment variables are set correctly
3. Test with mock mode first (`PAGSEGURO_USE_MOCK=true`)
4. Review the examples in the `examples/` directory

## 🚨 Important Security Notes

1. **Never commit credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Start with sandbox environment for testing**
4. **Implement proper webhook signature verification**
5. **Log all transactions for audit purposes**
6. **Monitor for suspicious payment patterns**
7. **Keep credentials secure and rotate them regularly**

## 🎯 Next Steps After Setup

1. **Test in sandbox environment**
2. **Integrate with your WhatsApp flow**
3. **Test all payment methods (credit, debit, PIX, boleto)**
4. **Implement error handling**
5. **Configure monitoring and logging**
6. **Deploy to production when ready**
