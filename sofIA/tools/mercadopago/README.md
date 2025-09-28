# Mercado Pago Integration for sofIA

Complete integration guide for Mercado Pago payment gateway with AP2 protocol compliance for the sofIA WhatsApp payment agent.

## Overview

This integration allows sofIA to process payments through Mercado Pago using tokenized payment data from the AP2 protocol. It supports transparent checkout without redirecting users, maintaining the seamless WhatsApp experience. **Perfect for international developers who can't use PagSeguro.**

## Features

- ✅ **AP2 Protocol Compliant**: Full integration with your existing AP2 implementation
- ✅ **International Friendly**: Accepts developers from any country
- ✅ **Transparent Checkout**: No user redirection, payments processed directly in WhatsApp
- ✅ **Tokenized Security**: Uses tokenized payment data, never handles raw card information
- ✅ **Multiple Payment Methods**: Credit card, debit card, PIX, boleto
- ✅ **Brazilian Market Ready**: Optimized for Brazilian payment preferences
- ✅ **Production Ready**: Comprehensive error handling and monitoring
- ✅ **Mock Mode**: Development and testing support

## Quick Start

### 1. Environment Setup

Create a `.env` file with your Mercado Pago credentials:

```bash
# Mercado Pago API Credentials
MERCADOPAGO_ACCESS_TOKEN=your_access_token_here
MERCADOPAGO_PUBLIC_KEY=your_public_key_here
MERCADOPAGO_CLIENT_ID=your_client_id_here
MERCADOPAGO_CLIENT_SECRET=your_client_secret_here

# Environment Configuration
MERCADOPAGO_ENVIRONMENT=sandbox  # or 'production'

# Development Settings
MERCADOPAGO_USE_MOCK=true  # Use mock mode for development
MERCADOPAGO_WEBHOOK_URL=https://your-domain.com/webhooks/mercadopago

# Required for AP2 Protocol
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. Basic Usage

```python
from sofIA.tools.mercadopago.ap2_mercadopago_integration import AP2MercadoPagoIntegration

# Initialize integration
integration = AP2MercadoPagoIntegration()

# Process WhatsApp payment flow
result = await integration.process_whatsapp_payment_flow(
    user_message="Quero comprar um café",
    user_id="whatsapp_user_123",
    merchant_id="mercadopago_demo_001"
)

# Complete payment with tokenized data
payment_result = await integration.complete_payment(
    cart_id=result["cart_id"],
    payment_method="credit_card",
    tokenized_payment_data={
        "token": "card_token_123",
        "installments": 3,
        "issuer_id": "25",
        "payment_method_id": "visa"
    }
)
```

### 3. Direct API Usage

For direct API integration without the AP2 wrapper:

```python
from examples.complete_mercadopago_payment_function import process_mercadopago_payment_with_ap2_tokens

# Tokenized payment data from AP2
tokenized_data = {
    "method": "credit_card",
    "token": "card_token_1234567890abcdef",
    "installments": 3,
    "issuer_id": "25",
    "payment_method_id": "visa"
}

# Transaction details
transaction_details = {
    "amount": 29.90,
    "currency": "BRL",
    "description": "WhatsApp purchase",
    "external_reference": "sofia_txn_123",
    "customer": {
        "name": "João",
        "surname": "da Silva",
        "email": "joao@email.com",
        "cpf": "12345678901",
        "phone": "11987654321"
    }
}

# Process payment
result = process_mercadopago_payment_with_ap2_tokens(tokenized_data, transaction_details)
```

## Payment Methods

### Credit Card

```python
tokenized_data = {
    "method": "credit_card",
    "token": "card_token_123",        # Mercado Pago card token
    "installments": 3,                # Number of installments (1-12)
    "issuer_id": "25",                # Bank issuer ID
    "payment_method_id": "visa",      # Card brand (visa, mastercard, etc.)
    "security_code": "123"            # CVV (if required)
}
```

### Debit Card

```python
tokenized_data = {
    "method": "debit_card",
    "token": "card_token_123",
    "issuer_id": "25",
    "payment_method_id": "debvisa"
}
```

### PIX (Instant Payment)

```python
tokenized_data = {
    "method": "pix"
    # PIX doesn't require additional tokenized data
}
```

### Boleto (Bank Slip)

```python
tokenized_data = {
    "method": "boleto"
    # Boleto doesn't require additional tokenized data
}
```

## API Response Format

### Success Response

```json
{
  "success": true,
  "transaction_id": "123456789",
  "mercadopago_preference_id": "PREF_ABC123",
  "mercadopago_payment_id": "123456789",
  "ap2_payment_mandate_id": "mandate_xyz789",
  "status": "approved",
  "status_detail": "accredited",
  "amount": 29.9,
  "currency": "BRL",
  "payment_method": "credit_card",
  "payment_method_id": "visa",
  "authorization_code": "AUTH123456",
  "created_at": "2024-01-01T10:00:00Z",
  "ap2_compliant": true,
  "tokenized_payment": true
}
```

### Error Response

```json
{
  "success": false,
  "error": "Payment processing failed: Invalid token",
  "error_type": "validation_error",
  "status_code": 422,
  "error_details": "Invalid card token provided"
}
```

## Status Mapping

| Mercado Pago Status | Normalized Status | Description                             |
| ------------------- | ----------------- | --------------------------------------- |
| pending             | pending           | Payment created, waiting for processing |
| approved            | approved          | Payment approved and completed          |
| authorized          | approved          | Payment authorized                      |
| in_process          | processing        | Payment under analysis                  |
| in_mediation        | processing        | Payment in mediation process            |
| rejected            | denied            | Payment declined by issuer              |
| cancelled           | cancelled         | Payment cancelled                       |
| refunded            | refunded          | Payment refunded                        |

## Error Handling

The integration provides comprehensive error handling:

### Common Error Types

- **validation_error**: Invalid payment data or customer information
- **processing_error**: Mercado Pago API processing failure
- **token_error**: Invalid or expired tokenized data
- **network_error**: Connection or timeout issues

### Error Handling Example

```python
result = await integration.complete_payment(cart_id, payment_method, tokenized_data)

if not result["success"]:
    error_type = result.get("error_type", "unknown")

    if error_type == "validation_error":
        # Handle validation errors (e.g., invalid CPF, missing data)
        handle_validation_error(result["error_details"])
    elif error_type == "token_error":
        # Request new tokenization from AP2
        request_new_tokenization()
    elif error_type == "processing_error":
        # Log and retry or show generic error
        log_error_and_retry(result["error"])
```

## Webhook Integration

Mercado Pago sends webhook notifications for payment status updates:

```python
from sofIA.tools.mercadopago.mercadopago_tool import MercadoPagoPaymentProcessor

config = MercadoPagoConfig.from_env()
processor = MercadoPagoPaymentProcessor(config)

# Verify webhook signature
is_valid = processor.verify_webhook_signature(payload, signature)

if is_valid:
    # Process webhook data
    webhook_data = json.loads(payload)
    payment_id = webhook_data["data"]["id"]

    # Get updated payment status
    status = await processor.get_payment_status(payment_id)

    # Update your system with new status
    update_payment_status(payment_id, status["status"])
```

## Testing

### Mock Mode

For development and testing, enable mock mode:

```bash
MERCADOPAGO_USE_MOCK=true
```

This will simulate Mercado Pago responses without making real API calls.

### Running Examples

```bash
# Run the complete integration demo
python examples/mercadopago_integration_example.py

# Test the direct payment function
python examples/complete_mercadopago_payment_function.py
```

### Test Cards for Sandbox

```
Credit Card (Approved):
Number: 4509 9535 6623 3704
CVV: 123
Expiry: 11/2025
Name: APRO

Credit Card (Declined):
Number: 4013 5406 8274 6260
CVV: 123
Expiry: 11/2025
Name: OTHE
```

## Production Deployment

### Checklist

- [ ] Mercado Pago production credentials configured
- [ ] `MERCADOPAGO_ENVIRONMENT=production`
- [ ] `MERCADOPAGO_USE_MOCK=false`
- [ ] Webhook URL configured and accessible
- [ ] SSL certificate installed
- [ ] Error logging and monitoring configured
- [ ] Payment method testing completed
- [ ] Customer data validation implemented
- [ ] PIX integration tested
- [ ] Installments configuration verified

### Security Best Practices

- Never hardcode API credentials in source code
- Use environment variables for all sensitive data
- Implement proper webhook signature verification
- Log all transactions for audit purposes
- Follow PCI DSS compliance guidelines
- Monitor for suspicious payment patterns

## Architecture

### Integration Flow

```
WhatsApp Message → sofIA Agent → AP2 Protocol → Mercado Pago Integration → Mercado Pago API
                                      ↓                    ↓                    ↓
User Confirmation ← sofIA Response ← AP2 Mandate ← Payment Result ← Mercado Pago Response
```

### Components

- **MercadoPagoTool**: Main tool for sofIA agent integration
- **MercadoPagoPaymentProcessor**: Core payment processing logic
- **AP2MercadoPagoIntegration**: AP2 protocol compliance wrapper
- **Complete Payment Function**: Direct API integration function

## Support

### Getting Mercado Pago Credentials

1. Create account at [Mercado Pago](https://www.mercadopago.com.br/)
2. Access "Suas integrações" in the developer panel
3. Click "Criar aplicação" (Create application)
4. Fill in application details
5. Copy Access Token and Public Key
6. Start with sandbox credentials for testing

### Common Issues

- **Invalid token**: Ensure tokens are generated correctly by Mercado Pago's tokenization service
- **Customer validation**: All Brazilian payments require valid CPF and customer data
- **Webhook failures**: Verify webhook URL is accessible and returns 200 OK
- **Environment mismatch**: Ensure credentials match the environment (sandbox/production)
- **Installments**: Verify issuer supports the number of installments requested

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Mercado Pago Advantages

### Why Choose Mercado Pago?

- 🌍 **International developers accepted** - No need for Brazilian documents
- 🇧🇷 **Strong presence in Brazil** - Trusted by millions of users
- ⚡ **Instant PIX payments** - Real-time money transfers
- 💳 **All major cards supported** - Visa, Mastercard, Elo, American Express
- 📱 **Mobile-first experience** - Optimized for mobile payments
- 🔒 **Advanced fraud protection** - Machine learning-based security
- 📊 **Comprehensive analytics** - Detailed payment insights
- 🛠️ **Excellent API documentation** - Easy integration
- 🎯 **High approval rates** - Optimized for Brazilian market
- 💰 **Competitive fees** - Transparent pricing structure
- 🔄 **Easy refund management** - Simple refund process
- 📞 **24/7 support** - Developer and merchant support

## API Reference

### MercadoPagoTool Operations

- `create_payment_intent`: Create payment preference
- `process_payment`: Process payment with tokenized data
- `get_payment_status`: Check payment status
- `add_merchant`: Add new merchant
- `get_merchant_info`: Get merchant information
- `get_payment_methods`: Get available payment methods

### AP2MercadoPagoIntegration Methods

- `process_whatsapp_payment_flow()`: Complete AP2 payment flow
- `complete_payment()`: Complete payment with tokenized data
- `get_transaction_status()`: Get current transaction status

### Main Integration Function

- `process_mercadopago_payment_with_ap2_tokens()`: Direct API payment processing

For detailed API documentation, see the docstrings in the source code.

## Migration from PagSeguro

If you're migrating from PagSeguro to Mercado Pago, the integration follows the same patterns:

### Key Differences

| Feature           | PagSeguro                   | Mercado Pago                  |
| ----------------- | --------------------------- | ----------------------------- |
| **International** | ❌ Brazilian documents only | ✅ Accepts international devs |
| **API Structure** | Orders → Pay                | Preferences → Payments        |
| **Tokenization**  | PagSeguro tokens            | Mercado Pago card tokens      |
| **PIX**           | ✅ Supported                | ✅ Supported                  |
| **Installments**  | Up to 18x                   | Up to 12x                     |
| **Webhooks**      | HMAC-SHA256                 | HMAC-SHA256                   |

### Migration Steps

1. **Replace credentials** in `.env` file
2. **Update imports** from `pagseguro_tool` to `mercadopago_tool`
3. **Test with sandbox** credentials first
4. **Update webhook URLs** to handle Mercado Pago format
5. **Deploy to production** when ready

The AP2 protocol integration remains exactly the same! 🚀
