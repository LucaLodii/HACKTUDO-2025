# PagSeguro (PagBank) Integration for sofIA

Complete integration guide for PagSeguro payment gateway with AP2 protocol compliance for the sofIA WhatsApp payment agent.

## Overview

This integration allows sofIA to process payments through PagSeguro (PagBank) using tokenized payment data from the AP2 protocol. It supports transparent checkout without redirecting users, maintaining the seamless WhatsApp experience.

## Features

- ✅ **AP2 Protocol Compliant**: Full integration with your existing AP2 implementation
- ✅ **Transparent Checkout**: No user redirection, payments processed directly in WhatsApp
- ✅ **Tokenized Security**: Uses tokenized payment data, never handles raw card information
- ✅ **Multiple Payment Methods**: Credit card, debit card, PIX, boleto
- ✅ **Brazilian Market Ready**: Optimized for Brazilian payment preferences
- ✅ **Production Ready**: Comprehensive error handling and monitoring
- ✅ **Mock Mode**: Development and testing support

## Quick Start

### 1. Environment Setup

Create a `.env` file with your PagSeguro credentials:

```bash
# PagSeguro API Credentials
PAGSEGURO_CLIENT_ID=your_client_id_here
PAGSEGURO_CLIENT_SECRET=your_client_secret_here
PAGSEGURO_ACCESS_TOKEN=your_access_token_here

# Environment Configuration
PAGSEGURO_ENVIRONMENT=sandbox  # or 'production'
PAGSEGURO_BASE_URL=https://sandbox.api.pagseguro.com

# Development Settings
PAGSEGURO_USE_MOCK=true  # Use mock mode for development
PAGSEGURO_WEBHOOK_URL=https://your-domain.com/webhooks/pagseguro
```

### 2. Basic Usage

```python
from sofIA.tools.pagseguro.ap2_pagseguro_integration import AP2PagSeguroIntegration

# Initialize integration
integration = AP2PagSeguroIntegration()

# Process WhatsApp payment flow
result = await integration.process_whatsapp_payment_flow(
    user_message="Quero comprar um café",
    user_id="whatsapp_user_123",
    merchant_id="pagseguro_demo_001"
)

# Complete payment with tokenized data
payment_result = await integration.complete_payment(
    cart_id=result["cart_id"],
    payment_method="credit_card",
    tokenized_payment_data={
        "token": "tok_abc123",
        "cvv_token": "cvv_xyz789",
        "holder_name": "JOAO DA SILVA"
    }
)
```

### 3. Direct API Usage

For direct API integration without the AP2 wrapper:

```python
from examples.complete_pagseguro_payment_function import process_pagseguro_payment_with_ap2_tokens

# Tokenized payment data from AP2
tokenized_data = {
    "method": "credit_card",
    "token": "tok_1234567890abcdef",
    "cvv_token": "cvv_abc123456789",
    "holder_name": "JOAO DA SILVA",
    "installments": 1
}

# Transaction details
transaction_details = {
    "amount": 29.90,
    "currency": "BRL",
    "description": "WhatsApp purchase",
    "reference_id": "sofia_txn_123",
    "customer": {
        "name": "João da Silva",
        "email": "joao@email.com",
        "cpf": "12345678901",
        "phone": "11987654321"
    }
}

# Process payment
result = process_pagseguro_payment_with_ap2_tokens(tokenized_data, transaction_details)
```

## Payment Methods

### Credit Card

```python
tokenized_data = {
    "method": "credit_card",
    "token": "tok_abc123",           # PagSeguro card token
    "cvv_token": "cvv_xyz789",       # Tokenized CVV
    "holder_name": "JOAO DA SILVA",  # Cardholder name
    "installments": 3                # Number of installments
}
```

### Debit Card

```python
tokenized_data = {
    "method": "debit_card",
    "token": "tok_abc123",
    "cvv_token": "cvv_xyz789",
    "holder_name": "JOAO DA SILVA"
}
```

### PIX (Instant Payment)

```python
tokenized_data = {
    "method": "pix",
    "pix_key": "user@email.com",
    "pix_key_type": "email"
}
```

### Boleto (Bank Slip)

```python
tokenized_data = {
    "method": "boleto",
    "customer_document": "12345678901"
}
```

## API Response Format

### Success Response

```json
{
  "success": true,
  "transaction_id": "TXN_123456789",
  "pagseguro_order_id": "ORDE_ABC123",
  "ap2_payment_mandate_id": "mandate_xyz789",
  "status": "approved",
  "amount": 29.9,
  "currency": "BRL",
  "payment_method": "credit_card",
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
  "error_details": ["Invalid card token provided"]
}
```

## Status Mapping

| PagSeguro Status | Normalized Status | Description                             |
| ---------------- | ----------------- | --------------------------------------- |
| WAITING          | pending           | Payment created, waiting for processing |
| IN_ANALYSIS      | processing        | Payment under analysis                  |
| PAID             | approved          | Payment approved and completed          |
| AVAILABLE        | approved          | Payment completed and available         |
| DECLINED         | denied            | Payment declined by issuer              |
| CANCELLED        | cancelled         | Payment cancelled                       |

## Error Handling

The integration provides comprehensive error handling:

### Common Error Types

- **validation_error**: Invalid payment data or customer information
- **processing_error**: PagSeguro API processing failure
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

PagSeguro sends webhook notifications for payment status updates:

```python
from sofIA.tools.pagseguro.pagseguro_tool import PagSeguroPaymentProcessor

processor = PagSeguroPaymentProcessor(config)

# Verify webhook signature
is_valid = processor.verify_webhook_signature(payload, signature)

if is_valid:
    # Process webhook data
    webhook_data = json.loads(payload)
    order_id = webhook_data["reference_id"]
    new_status = webhook_data["status"]

    # Update your system with new status
    update_payment_status(order_id, new_status)
```

## Testing

### Mock Mode

For development and testing, enable mock mode:

```bash
PAGSEGURO_USE_MOCK=true
```

This will simulate PagSeguro responses without making real API calls.

### Running Examples

```bash
# Run the complete integration demo
python examples/pagseguro_integration_example.py

# Test the direct payment function
python examples/complete_pagseguro_payment_function.py
```

## Production Deployment

### Checklist

- [ ] PagSeguro production credentials configured
- [ ] `PAGSEGURO_ENVIRONMENT=production`
- [ ] `PAGSEGURO_USE_MOCK=false`
- [ ] Webhook URL configured and accessible
- [ ] SSL certificate installed
- [ ] Error logging and monitoring configured
- [ ] Payment method testing completed
- [ ] Customer data validation implemented

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
WhatsApp Message → sofIA Agent → AP2 Protocol → PagSeguro Integration → PagSeguro API
                                      ↓                    ↓                    ↓
User Confirmation ← sofIA Response ← AP2 Mandate ← Payment Result ← PagSeguro Response
```

### Components

- **PagSeguroTool**: Main tool for sofIA agent integration
- **PagSeguroPaymentProcessor**: Core payment processing logic
- **AP2PagSeguroIntegration**: AP2 protocol compliance wrapper
- **Complete Payment Function**: Direct API integration function

## Support

### Getting PagSeguro Credentials

1. Create account at [PagSeguro](https://pagseguro.uol.com.br/)
2. Access the Developer Dashboard
3. Generate API credentials
4. Copy Client ID, Client Secret, and Access Token
5. Start with sandbox environment for testing

### Common Issues

- **Invalid token**: Ensure tokens are generated correctly by PagSeguro's tokenization service
- **Customer validation**: All Brazilian payments require valid CPF and customer data
- **Webhook failures**: Verify webhook URL is accessible and returns 200 OK
- **Environment mismatch**: Ensure credentials match the environment (sandbox/production)

### Logging

Enable detailed logging for debugging:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## API Reference

### PagSeguroTool Operations

- `create_payment_intent`: Create payment intent
- `process_payment`: Process payment with tokenized data
- `get_payment_status`: Check payment status
- `add_merchant`: Add new merchant
- `get_merchant_info`: Get merchant information
- `get_payment_methods`: Get available payment methods

### AP2PagSeguroIntegration Methods

- `process_whatsapp_payment_flow()`: Complete AP2 payment flow
- `complete_payment()`: Complete payment with tokenized data
- `get_transaction_status()`: Get current transaction status

For detailed API documentation, see the docstrings in the source code.
