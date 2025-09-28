# Complete Mercado Pago Setup Guide for sofIA Integration

## 🚀 Step-by-Step Setup Process

### 1. Mercado Pago Account Creation

#### Go to Mercado Pago Website

- **URL**: https://www.mercadopago.com.br/
- **Click**: "Criar conta" (Create account)

#### Choose Account Type

- **Pessoa Física** (Individual) - For personal projects
- **Pessoa Jurídica** (Business) - For commercial use
- **International** - For developers outside Brazil

#### Required Information

```
Individual Account (Pessoa Física):
- CPF (Brazilian tax ID) OR International passport
- Full name
- Email address
- Phone number
- Address

Business Account (Pessoa Jurídica):
- CNPJ (Business tax ID) OR International business documents
- Company name
- Business email
- Phone number
- Business address

International Account:
- Passport or national ID
- Full name
- Email address
- Phone number
- Address in your country
```

### 2. Developer Dashboard Access

#### Navigate to Developer Area

1. **Login** to your Mercado Pago account
2. **Go to**: https://www.mercadopago.com.br/developers
3. **Click**: "Suas integrações" (Your integrations)
4. **Click**: "Criar aplicação" (Create application)

#### Application Configuration

```
Application Name: sofIA WhatsApp Payment Agent
Description: AI payment agent for WhatsApp transactions
Application Model: Payments
Integration Type: Online payments
```

### 3. Getting API Credentials

#### In the Developer Dashboard:

1. **Select your application**
2. **Go to "Credenciais"** (Credentials) section
3. **You'll find these credentials**:

```bash
# Sandbox Credentials (for testing)
MERCADOPAGO_ACCESS_TOKEN=TEST-your_sandbox_access_token
MERCADOPAGO_PUBLIC_KEY=TEST-your_sandbox_public_key
MERCADOPAGO_CLIENT_ID=your_sandbox_client_id
MERCADOPAGO_CLIENT_SECRET=your_sandbox_client_secret

# Production Credentials (for live payments)
MERCADOPAGO_ACCESS_TOKEN=APP_USR-your_production_access_token
MERCADOPAGO_PUBLIC_KEY=APP_USR-your_production_public_key
MERCADOPAGO_CLIENT_ID=your_production_client_id
MERCADOPAGO_CLIENT_SECRET=your_production_client_secret
```

#### Credential Locations:

- **Access Token**: Main credential for API access (starts with TEST- or APP_USR-)
- **Public Key**: Used for frontend tokenization (starts with TEST- or APP_USR-)
- **Client ID**: Application identifier
- **Client Secret**: Used for webhook signature verification

### 4. Environment Configuration

#### Create `.env` file in your project root:

```bash
# Mercado Pago API Credentials (START WITH SANDBOX)
MERCADOPAGO_ACCESS_TOKEN=TEST-your_sandbox_access_token_here
MERCADOPAGO_PUBLIC_KEY=TEST-your_sandbox_public_key_here
MERCADOPAGO_CLIENT_ID=your_sandbox_client_id_here
MERCADOPAGO_CLIENT_SECRET=your_sandbox_client_secret_here

# Environment Configuration
MERCADOPAGO_ENVIRONMENT=sandbox  # IMPORTANT: Start with sandbox!

# Development Settings
MERCADOPAGO_USE_MOCK=false  # Set to false to use real sandbox
MERCADOPAGO_WEBHOOK_URL=https://your-domain.com/webhooks/mercadopago

# Required for AP2 Protocol
GOOGLE_API_KEY=your_google_api_key_here
```

### 5. Webhook Configuration

#### In Mercado Pago Dashboard:

1. **Go to your application settings**
2. **Find "Webhooks" or "Notificações"** section
3. **Add webhook URL**: `https://your-domain.com/webhooks/mercadopago`
4. **Select events**:
   - Payment status changes
   - Payment updates
   - Refund notifications
   - Chargeback notifications

#### Webhook URL Requirements:

- Must be HTTPS (SSL certificate required)
- Must return HTTP 200 OK
- Must be publicly accessible
- Should handle POST requests
- Should validate webhook signatures

### 6. Testing Setup

#### Test with Sandbox First:

```bash
# In your .env file
MERCADOPAGO_ENVIRONMENT=sandbox
MERCADOPAGO_USE_MOCK=false
```

#### Run Test:

```bash
# Test the integration
python examples/mercadopago_integration_example.py
```

### 7. Production Deployment

#### When ready for production:

```bash
# Update .env file
MERCADOPAGO_ENVIRONMENT=production
MERCADOPAGO_ACCESS_TOKEN=APP_USR-your_production_access_token
MERCADOPAGO_PUBLIC_KEY=APP_USR-your_production_public_key
MERCADOPAGO_CLIENT_ID=your_production_client_id
MERCADOPAGO_CLIENT_SECRET=your_production_client_secret
MERCADOPAGO_USE_MOCK=false
```

## 🔍 Where to Find Each Credential

### In Mercado Pago Developer Dashboard:

#### Access Token

- **Location**: Application → Credentials → "Access token"
- **Format**: TEST-xxxx (sandbox) or APP_USR-xxxx (production)
- **Example**: `TEST-1234567890123456-112233-abcdef123456789012345678901234567890123456-987654321`
- **⚠️ Keep this secret!**

#### Public Key

- **Location**: Application → Credentials → "Public key"
- **Format**: TEST-xxxx (sandbox) or APP_USR-xxxx (production)
- **Example**: `TEST-abcdef12-3456-7890-abcd-ef1234567890`
- **Used for**: Frontend tokenization (safe to expose)

#### Client ID

- **Location**: Application → Credentials → "Client ID"
- **Format**: Numeric string
- **Example**: `1234567890123456`

#### Client Secret

- **Location**: Application → Credentials → "Client secret"
- **Format**: Alphanumeric string
- **Example**: `abcdefghijklmnopqrstuvwxyz123456`
- **⚠️ Keep this secret!**

## 🛠️ Common Setup Issues & Solutions

### Issue 1: "Invalid credentials"

**Solution**:

- Verify you're using sandbox credentials with sandbox environment
- Check for extra spaces in credential strings
- Ensure credentials are from the correct application
- Verify Access Token starts with TEST- (sandbox) or APP_USR- (production)

### Issue 2: "Webhook not receiving notifications"

**Solution**:

- Verify webhook URL is HTTPS
- Test webhook URL returns 200 OK
- Check firewall settings
- Verify webhook is configured in Mercado Pago dashboard
- Test webhook signature validation

### Issue 3: "Payment processing failed"

**Solution**:

- Start with sandbox environment
- Use test card numbers provided by Mercado Pago
- Verify customer data format (CPF, email, phone)
- Check Mercado Pago API status page

### Issue 4: "Token validation failed"

**Solution**:

- Ensure you're using Mercado Pago's tokenization service
- Verify token format and expiration
- Check if token was generated with correct Public Key
- Verify issuer_id matches the card

### Issue 5: "International account issues"

**Solution**:

- Mercado Pago accepts international developers
- Use passport instead of CPF for identification
- Ensure all documents are valid and not expired
- Contact Mercado Pago support if needed

## 📋 Pre-Launch Checklist

### Sandbox Testing

- [ ] Mercado Pago sandbox account created
- [ ] Application created in developer dashboard
- [ ] Sandbox credentials configured in .env
- [ ] Test payments working with sandbox
- [ ] PIX payments tested
- [ ] Credit card payments tested (with installments)
- [ ] Webhook receiving notifications
- [ ] Error handling tested

### Production Preparation

- [ ] Account verification completed (if required)
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
- [ ] Webhook signature verification implemented

## 📞 Support Resources

### Mercado Pago Support

- **Developer Documentation**: https://www.mercadopago.com.br/developers/en/docs
- **API Reference**: https://www.mercadopago.com.br/developers/en/reference
- **Support Portal**: https://www.mercadopago.com.br/ajuda
- **Developer Community**: Available in Mercado Pago developer area
- **Status Page**: https://status.mercadopago.com/

### Test Cards for Sandbox

```
Credit Card (Approved):
Number: 4509 9535 6623 3704
CVV: 123
Expiry: 11/2025
Name: APRO

Credit Card (Declined - Insufficient Funds):
Number: 4013 5406 8274 6260
CVV: 123
Expiry: 11/2025
Name: OTHE

Credit Card (Declined - Call for Auth):
Number: 5031 4332 1540 6351
CVV: 123
Expiry: 11/2025
Name: CALL

Debit Card (Approved):
Number: 5031 7557 3453 0604
CVV: 123
Expiry: 11/2025
Name: APRO
```

### PIX Test Data

```
For PIX payments in sandbox:
- Use any valid email or phone number
- PIX QR codes will be generated automatically
- Test payments are automatically approved after 5 seconds
```

### Integration Support

If you need help with the sofIA integration:

1. Check the logs for detailed error messages
2. Verify environment variables are set correctly
3. Test with mock mode first (`MERCADOPAGO_USE_MOCK=true`)
4. Review the examples in the `examples/` directory
5. Check the comprehensive README in `sofIA/tools/mercadopago/`

## 🚨 Important Security Notes

1. **Never commit credentials to version control**
2. **Use environment variables for all sensitive data**
3. **Start with sandbox environment for testing**
4. **Implement proper webhook signature verification**
5. **Log all transactions for audit purposes**
6. **Monitor for suspicious payment patterns**
7. **Keep credentials secure and rotate them regularly**
8. **Use HTTPS for all communications**

## 🌟 Mercado Pago Advantages

### Why Mercado Pago is Perfect for International Developers:

1. **🌍 International Friendly**: No Brazilian documents required
2. **🇧🇷 Market Leader**: Most popular payment method in Brazil
3. **⚡ Instant PIX**: Real-time payments, 24/7 availability
4. **💳 All Cards**: Visa, Mastercard, Elo, American Express
5. **📱 Mobile Optimized**: Perfect for WhatsApp integration
6. **🔒 Security**: Advanced fraud protection
7. **📊 Analytics**: Comprehensive payment insights
8. **🛠️ Developer Friendly**: Excellent documentation and support
9. **💰 Competitive Rates**: Transparent pricing
10. **🔄 Easy Refunds**: Simple refund management

## 🎯 Next Steps After Setup

1. **Test in sandbox environment**
2. **Integrate with your WhatsApp flow**
3. **Test all payment methods (credit, debit, PIX, boleto)**
4. **Test installment payments**
5. **Implement error handling**
6. **Configure monitoring and logging**
7. **Test webhook notifications**
8. **Deploy to production when ready**

## 🆚 Comparison with PagSeguro

| Feature            | PagSeguro | Mercado Pago |
| ------------------ | --------- | ------------ |
| International Devs | ❌        | ✅           |
| Market Share       | High      | Higher       |
| PIX Support        | ✅        | ✅           |
| API Quality        | Good      | Excellent    |
| Documentation      | Good      | Excellent    |
| Developer Support  | Limited   | 24/7         |
| Approval Rates     | High      | Higher       |
| Mobile Experience  | Good      | Excellent    |

**Recommendation**: Mercado Pago is the better choice for international developers and offers superior API experience! 🚀
