# Bemobi Integration for sofIA

This module provides integration between sofIA AI payment agent and Bemobi payment gateway for processing WhatsApp payments in emerging markets.

## Features

- **Multi-region Support**: Latin America, Africa, and Asia
- **AP2 Protocol Compliance**: Secure mandate-based payments
- **WhatsApp Integration**: Conversational payment processing
- **Merchant Management**: Easy merchant onboarding and configuration
- **Payment Methods**: Regional payment method support (PIX, mobile money, etc.)

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.bemobi.example .env.bemobi

# Edit with your Bemobi credentials
export BEMOBI_API_KEY="your_api_key"
export BEMOBI_SECRET_KEY="your_secret_key"
export BEMOBI_REGION="latam"  # or "africa", "asia"
```

### 2. Basic Usage

```python
from sofIA.tools.bemobi import bemobi_tool

# Create payment intent
result = await bemobi_tool(
    operation="create_payment_intent",
    merchant_id="bemobi_merchant_001",
    amount=25.50,
    currency="BRL",
    description="Coffee purchase via WhatsApp"
)

# Process payment
payment_result = await bemobi_tool(
    operation="process_payment",
    payment_intent_id=result["payment_intent_id"],
    payment_method="pix",
    payment_data={"pix_key": "user@example.com"}
)
```

### 3. Regional Examples

#### Latin America (Brazil)
```python
from sofIA.tools.bemobi.examples import run_example_scenario

result = await run_example_scenario(
    "latam_coffee_purchase",
    api_key="your_api_key",
    secret_key="your_secret_key"
)
```

#### Africa (Nigeria)
```python
result = await run_example_scenario(
    "africa_electronics_purchase", 
    api_key="your_api_key",
    secret_key="your_secret_key"
)
```

#### Asia (Indonesia)
```python
result = await run_example_scenario(
    "asia_fashion_purchase",
    api_key="your_api_key", 
    secret_key="your_secret_key"
)
```

## API Reference

### BemobiTool Operations

#### `create_payment_intent`
Creates a payment intent with Bemobi gateway.

**Parameters:**
- `merchant_id` (string): Bemobi merchant ID
- `amount` (number): Payment amount
- `currency` (string): Currency code (BRL, NGN, THB, etc.)
- `description` (string): Payment description

**Returns:**
```json
{
    "success": true,
    "payment_intent_id": "pi_1234567890",
    "client_secret": "pi_1234567890_secret_xyz",
    "amount": 25.50,
    "currency": "BRL",
    "status": "requires_payment_method"
}
```

#### `process_payment`
Processes payment through Bemobi.

**Parameters:**
- `payment_intent_id` (string): Payment intent ID
- `payment_method` (string): Payment method (card, pix, boleto, etc.)
- `payment_data` (object): Payment method specific data

**Returns:**
```json
{
    "success": true,
    "payment_id": "pay_1234567890",
    "status": "succeeded",
    "amount": 25.50,
    "currency": "BRL",
    "transaction_id": "txn_1234567890"
}
```

#### `add_merchant`
Adds a new merchant to the system.

**Parameters:**
- `merchant_id` (string): Unique merchant identifier
- `store_name` (string): Store/merchant name
- `region` (string): Geographic region (latam, africa, asia)
- `currency` (string): Primary currency
- `api_key` (string): Merchant API key

#### `get_merchant_info`
Retrieves merchant information.

**Parameters:**
- `merchant_id` (string): Merchant identifier

#### `get_payment_status`
Checks payment status.

**Parameters:**
- `payment_id` (string): Payment ID

## Regional Configuration

### Supported Regions

#### Latin America
- **Currencies**: BRL, ARS, CLP, COP, MXN
- **Payment Methods**: Card, PIX, Boleto, Bank Transfer
- **Key Markets**: Brazil, Mexico, Argentina, Chile, Colombia

#### Africa  
- **Currencies**: NGN, ZAR, KES, GHS, EGP
- **Payment Methods**: Card, Bank Transfer, Mobile Money
- **Key Markets**: Nigeria, South Africa, Kenya, Ghana, Egypt

#### Asia
- **Currencies**: THB, IDR, VND, PHP, MYR  
- **Payment Methods**: Card, Bank Transfer, Digital Wallet
- **Key Markets**: Thailand, Indonesia, Vietnam, Philippines, Malaysia

## Merchant Onboarding

### Small Business Template
```python
merchant_data = {
    "merchant_id": "small_biz_001",
    "store_name": "Local Coffee Shop",
    "currency": "BRL",
    "api_key": "merchant_api_key",
    "category": "food_beverage",
    "region": "latam"
}
```

### Enterprise Template
```python
merchant_data = {
    "merchant_id": "enterprise_001", 
    "store_name": "Global Electronics",
    "currency": "USD",
    "api_key": "enterprise_api_key",
    "webhook_url": "https://merchant.com/webhooks/sofia",
    "category": "electronics",
    "region": "global"
}
```

## Integration with sofIA Agent

The Bemobi tool is automatically available in the sofIA agent:

```python
from sofIA.agent import root_agent

# Agent now has access to:
# - ap2_protocol_tool (AP2 mandates)
# - whatsapp_tool (WhatsApp messaging)  
# - bemobi_tool (Bemobi payments)
```

## Webhook Integration

Configure webhooks to receive payment notifications:

```python
# Webhook endpoint
@app.post("/webhooks/bemobi/{merchant_id}")
async def bemobi_webhook(merchant_id: str, request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Bemobi-Signature")
    
    # Verify signature
    if integration.verify_webhook_signature(payload, signature):
        # Process webhook
        webhook_data = json.loads(payload)
        # Handle payment status updates
```

## Error Handling

All operations return structured error responses:

```json
{
    "error": "Error description",
    "error_code": "BEMOBI_API_ERROR",
    "details": {
        "status_code": 400,
        "response": "Invalid merchant ID"
    }
}
```

## Testing

Run example scenarios:

```bash
python -m sofIA.tools.bemobi.examples
```

This will:
1. Generate environment configuration files
2. Set up demo merchants for all regions
3. Run example payment scenarios
4. Display results and integration status

## Security

- All API communications use HTTPS
- Webhook signatures are verified using HMAC-SHA256
- Sensitive data is encrypted in transit
- AP2 mandates provide cryptographic verification
- Merchant credentials are stored securely

## Support

For Bemobi-specific issues:
- Check Bemobi API documentation
- Verify merchant credentials
- Ensure proper webhook configuration
- Review regional payment method availability

For sofIA integration issues:
- Check agent tool configuration
- Verify AP2 mandate creation
- Review WhatsApp webhook setup
- Test with demo scenarios first

