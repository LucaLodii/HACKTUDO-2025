# BEMOBI Mock Implementation Setup

## Overview

The sofIA system now includes a comprehensive mock implementation of the BEMOBI payment gateway for hackathon demonstration purposes. This allows you to showcase the complete payment flow without requiring access to the real BEMOBI API.

## Features

### 🔧 Mock Implementation
- **Realistic API Simulation**: Mimics real BEMOBI API responses and behavior
- **Configurable Delays**: Simulates network latency for realistic demo experience
- **Failure Simulation**: Configurable failure rate for testing error handling
- **Regional Support**: Mock data for LATAM, Africa, and Asia regions

### 🌍 Regional Mock Data
- **LATAM**: BRL currency, PIX, Boleto, Card payments
- **Africa**: NGN, GHS, KES currencies, Mobile Money, Bank Transfer
- **Asia**: THB, IDR, PHP currencies, Digital Wallets, Bank Transfer

### 🏪 Demo Merchants
- **Café do João** (LATAM) - Coffee shop with PIX payments
- **Tech Store Lagos** (Africa) - Electronics with Mobile Money
- **Bangkok Electronics** (Asia) - Electronics with Digital Wallets
- **Mercado Central** (LATAM) - Grocery store with multiple payment methods

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# BEMOBI Configuration
BEMOBI_ENABLED=true
BEMOBI_MOCK_MODE=true
BEMOBI_API_KEY=your_bemobi_api_key_here
BEMOBI_SECRET_KEY=your_bemobi_secret_key_here
BEMOBI_BASE_URL=https://api.bemobi.com/v1
BEMOBI_REGION=latam
BEMOBI_MOCK_DELAY=0.5
BEMOBI_MOCK_FAILURE_RATE=0.05
```

### Configuration Options

- **BEMOBI_ENABLED**: Enable/disable BEMOBI integration (default: true)
- **BEMOBI_MOCK_MODE**: Use mock implementation (default: true)
- **BEMOBI_REGION**: Target region (latam, africa, asia)
- **BEMOBI_MOCK_DELAY**: Simulated API delay in seconds (default: 0.5)
- **BEMOBI_MOCK_FAILURE_RATE**: Failure rate for testing (default: 0.05 = 5%)

## Usage

### Automatic Switching

The system automatically uses the mock implementation when:
1. `BEMOBI_MOCK_MODE=true` (default)
2. Real API credentials are not provided
3. BEMOBI integration is enabled

### Demo Scenarios

The mock system includes pre-configured demo scenarios:

```python
from sofIA.tools.bemobi.mock_data_generators import generate_demo_scenario

# Generate a complete demo scenario
scenario = generate_demo_scenario("latam")
print(scenario["demo_message"])
# Output: "User wants to buy Coffee from Café do João for BRL 5.50"
```

### Mock Statistics

Get mock processor statistics:

```python
from sofIA.tools.bemobi.mock_bemobi import mock_bemobi_tool

stats = await mock_bemobi_tool(operation="get_mock_statistics")
print(stats)
```

## Integration with sofIA

### Agent Integration

The mock BEMOBI tool is automatically integrated with the sofIA agent:

```python
# The agent automatically uses mock BEMOBI when configured
from sofIA.agent import root_agent

# Agent now has access to mock BEMOBI operations
response = await root_agent.run("Create a payment intent for coffee purchase")
```

### Orchestrator Integration

The orchestrator automatically coordinates with the mock BEMOBI system:

```python
# A2A communication with mock BEMOBI
from orchestrator.tools.orchestration_tool import process_user_message

result = process_user_message("I want to buy coffee", "user_123", "agent_response")
# This will use mock BEMOBI for payment processing
```

## Demo Flow

### Complete Payment Flow

1. **User Intent**: "I want to buy coffee"
2. **AP2 Intent Mandate**: Created with mock merchant data
3. **BEMOBI Payment Intent**: Mock API call to create payment intent
4. **AP2 Cart Mandate**: Generated with mock product data
5. **Payment Processing**: Mock payment through BEMOBI
6. **AP2 Payment Mandate**: Final mandate with transaction details

### Example Demo Session

```
User: "I want to buy coffee"
sofIA: "I found Café do João with premium coffee for BRL 5.50. Shall I proceed?"

User: "Yes, pay with PIX"
sofIA: "✅ Payment Successful!
       Transaction ID: txn_mock_a1b2c3d4e5f6
       Amount: BRL 5.50
       Status: Completed
       🔐 Secured by AP2 Protocol
       🤝 Processed via Mock BEMOBI"
```

## Switching to Real API

When you have access to the real BEMOBI API:

1. Set `BEMOBI_MOCK_MODE=false`
2. Provide real API credentials:
   ```bash
   BEMOBI_API_KEY=your_real_api_key
   BEMOBI_SECRET_KEY=your_real_secret_key
   ```
3. The system will automatically switch to the real API

## Testing

### Mock Data Validation

```python
# Test mock data generation
from sofIA.tools.bemobi.mock_data_generators import get_regional_generator

generator = get_regional_generator("latam")
merchant = generator.get_random_merchant()
print(f"Merchant: {merchant.store_name} - {merchant.currency}")
```

### Payment Flow Testing

```python
# Test complete payment flow
from sofIA.tools.bemobi.mock_bemobi import mock_bemobi_tool

# Create payment intent
intent = await mock_bemobi_tool(
    operation="create_payment_intent",
    merchant_id="bemobi_demo_001",
    amount=15.50,
    currency="BRL",
    description="Coffee purchase"
)

# Process payment
payment = await mock_bemobi_tool(
    operation="process_payment",
    payment_intent_id=intent["payment_intent_id"],
    payment_method="pix",
    payment_data={"pix_key": "user@example.com"}
)
```

## Benefits for Hackathon

### 🎯 Demo Ready
- No external API dependencies
- Consistent, predictable responses
- Realistic payment flows

### 🔧 Configurable
- Adjustable delays and failure rates
- Multiple regional scenarios
- Easy switching between mock and real API

### 📊 Comprehensive
- Complete AP2 Protocol integration
- Multi-agent coordination
- End-to-end payment processing

### 🚀 Production Ready
- Same interface as real API
- Easy migration path
- Comprehensive error handling

## Next Steps

1. **Run the demo**: `python app.py demo`
2. **Test mock BEMOBI**: Use the mock tool functions
3. **Customize scenarios**: Modify mock data generators
4. **Prepare for real API**: When available, switch to real BEMOBI

The mock implementation provides a complete, realistic demonstration of the sofIA-BEMOBI integration for your hackathon presentation! 🚀
