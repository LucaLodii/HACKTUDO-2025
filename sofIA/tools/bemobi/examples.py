"""
Bemobi Integration Examples for sofIA

This module contains example configurations and usage patterns for
different regions and merchant types in the Bemobi integration.
"""

import os
from typing import Dict, Any, List
from .bemobi_integration import SofiaBemobiIntegration, SofiaBemobiConfig


# Regional configurations
REGIONAL_CONFIGS = {
    "latam": {
        "region": "latam",
        "base_url": "https://api.bemobi.com/v1",
        "supported_currencies": ["BRL", "ARS", "CLP", "COP", "MXN"],
        "payment_methods": ["card", "pix", "boleto", "bank_transfer"],
        "demo_merchants": [
            {
                "merchant_id": "bemobi_br_001",
                "store_name": "Café do João",
                "currency": "BRL",
                "category": "food_beverage",
                "description": "Local coffee shop in São Paulo"
            },
            {
                "merchant_id": "bemobi_mx_002", 
                "store_name": "Electrónica México",
                "currency": "MXN",
                "category": "electronics",
                "description": "Electronics store in Mexico City"
            }
        ]
    },
    "africa": {
        "region": "africa",
        "base_url": "https://api.bemobi.com/v1",
        "supported_currencies": ["NGN", "ZAR", "KES", "GHS", "EGP"],
        "payment_methods": ["card", "bank_transfer", "mobile_money"],
        "demo_merchants": [
            {
                "merchant_id": "bemobi_ng_001",
                "store_name": "Tech Store Lagos",
                "currency": "NGN", 
                "category": "electronics",
                "description": "Technology store in Lagos, Nigeria"
            },
            {
                "merchant_id": "bemobi_za_002",
                "store_name": "Cape Town Fashion",
                "currency": "ZAR",
                "category": "fashion",
                "description": "Fashion boutique in Cape Town"
            }
        ]
    },
    "asia": {
        "region": "asia",
        "base_url": "https://api.bemobi.com/v1",
        "supported_currencies": ["THB", "IDR", "VND", "PHP", "MYR"],
        "payment_methods": ["card", "bank_transfer", "wallet"],
        "demo_merchants": [
            {
                "merchant_id": "bemobi_th_001",
                "store_name": "Bangkok Electronics",
                "currency": "THB",
                "category": "electronics", 
                "description": "Electronics store in Bangkok"
            },
            {
                "merchant_id": "bemobi_id_002",
                "store_name": "Jakarta Fashion",
                "currency": "IDR",
                "category": "fashion",
                "description": "Fashion store in Jakarta"
            }
        ]
    }
}


def create_regional_integration(region: str, api_key: str, secret_key: str) -> SofiaBemobiIntegration:
    """Create sofIA-Bemobi integration for a specific region"""
    config_data = REGIONAL_CONFIGS.get(region)
    if not config_data:
        raise ValueError(f"Unsupported region: {region}. Supported regions: {list(REGIONAL_CONFIGS.keys())}")
    
    config = SofiaBemobiConfig(
        bemobi_api_key=api_key,
        bemobi_secret_key=secret_key,
        bemobi_base_url=config_data["base_url"],
        region=region,
        supported_currencies=config_data["supported_currencies"],
        webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    )
    
    return SofiaBemobiIntegration(config)


async def setup_demo_merchants(integration: SofiaBemobiIntegration, region: str) -> List[Dict[str, Any]]:
    """Set up demo merchants for a region"""
    config_data = REGIONAL_CONFIGS.get(region)
    if not config_data:
        return []
    
    results = []
    for merchant_data in config_data["demo_merchants"]:
        # Add API key (in production, this would come from merchant registration)
        merchant_data["api_key"] = f"demo_api_key_{merchant_data['merchant_id']}"
        
        result = await integration.register_merchant(merchant_data)
        results.append(result)
    
    return results


# Example usage scenarios
EXAMPLE_SCENARIOS = {
    "latam_coffee_purchase": {
        "region": "latam",
        "user_message": "Quero comprar um café",
        "user_id": "user_123",
        "merchant_id": "bemobi_br_001",
        "expected_amount": 5.50,
        "currency": "BRL",
        "payment_methods": ["pix", "card"]
    },
    "africa_electronics_purchase": {
        "region": "africa", 
        "user_message": "I want to buy a smartphone",
        "user_id": "user_456",
        "merchant_id": "bemobi_ng_001",
        "expected_amount": 150000.00,
        "currency": "NGN",
        "payment_methods": ["card", "bank_transfer"]
    },
    "asia_fashion_purchase": {
        "region": "asia",
        "user_message": "I need to buy a shirt",
        "user_id": "user_789", 
        "merchant_id": "bemobi_id_002",
        "expected_amount": 250000.00,
        "currency": "IDR",
        "payment_methods": ["card", "wallet"]
    }
}


async def run_example_scenario(scenario_name: str, api_key: str, secret_key: str) -> Dict[str, Any]:
    """Run an example payment scenario"""
    scenario = EXAMPLE_SCENARIOS.get(scenario_name)
    if not scenario:
        return {"error": f"Scenario {scenario_name} not found"}
    
    # Create integration
    integration = create_regional_integration(
        scenario["region"], 
        api_key, 
        secret_key
    )
    
    # Set up demo merchants
    await setup_demo_merchants(integration, scenario["region"])
    
    # Process payment flow
    result = await integration.process_whatsapp_payment_flow(
        user_message=scenario["user_message"],
        user_id=scenario["user_id"],
        merchant_id=scenario["merchant_id"]
    )
    
    return {
        "scenario": scenario_name,
        "region": scenario["region"],
        "result": result,
        "expected_amount": scenario["expected_amount"],
        "currency": scenario["currency"],
        "available_payment_methods": scenario["payment_methods"]
    }


# Environment configuration templates
ENVIRONMENT_TEMPLATES = {
    "development": {
        "BEMOBI_API_KEY": "demo_api_key_dev",
        "BEMOBI_SECRET_KEY": "demo_secret_key_dev", 
        "BEMOBI_BASE_URL": "https://api-sandbox.bemobi.com/v1",
        "BEMOBI_REGION": "latam",
        "WEBHOOK_BASE_URL": "https://dev.your-domain.com"
    },
    "staging": {
        "BEMOBI_API_KEY": "staging_api_key",
        "BEMOBI_SECRET_KEY": "staging_secret_key",
        "BEMOBI_BASE_URL": "https://api-staging.bemobi.com/v1", 
        "BEMOBI_REGION": "latam",
        "WEBHOOK_BASE_URL": "https://staging.your-domain.com"
    },
    "production": {
        "BEMOBI_API_KEY": "prod_api_key",
        "BEMOBI_SECRET_KEY": "prod_secret_key",
        "BEMOBI_BASE_URL": "https://api.bemobi.com/v1",
        "BEMOBI_REGION": "latam", 
        "WEBHOOK_BASE_URL": "https://your-domain.com"
    }
}


def generate_env_file(environment: str, output_file: str = ".env.bemobi"):
    """Generate environment file for Bemobi integration"""
    env_data = ENVIRONMENT_TEMPLATES.get(environment)
    if not env_data:
        raise ValueError(f"Unknown environment: {environment}")
    
    with open(output_file, 'w') as f:
        f.write("# Bemobi Integration Environment Variables\n")
        f.write("# Generated for sofIA WhatsApp Payment Agent\n\n")
        
        for key, value in env_data.items():
            f.write(f"{key}={value}\n")
        
        f.write("\n# WhatsApp Configuration\n")
        f.write("WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token\n")
        f.write("WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id\n")
        f.write("WHATSAPP_VERIFY_TOKEN=your_verify_token\n")
    
    return output_file


# Merchant onboarding templates
MERCHANT_ONBOARDING_TEMPLATES = {
    "small_business": {
        "merchant_type": "small_business",
        "required_fields": [
            "store_name", "merchant_id", "currency", "api_key"
        ],
        "optional_fields": [
            "description", "category", "website", "contact_email"
        ],
        "default_payment_methods": ["card", "pix"],
        "setup_fee": 0,
        "transaction_fee_rate": 0.029  # 2.9%
    },
    "enterprise": {
        "merchant_type": "enterprise", 
        "required_fields": [
            "store_name", "merchant_id", "currency", "api_key", "webhook_url"
        ],
        "optional_fields": [
            "description", "category", "website", "contact_email", "support_phone"
        ],
        "default_payment_methods": ["card", "pix", "boleto", "bank_transfer"],
        "setup_fee": 500,
        "transaction_fee_rate": 0.024  # 2.4%
    }
}


def get_merchant_onboarding_template(merchant_type: str) -> Dict[str, Any]:
    """Get merchant onboarding template"""
    return MERCHANT_ONBOARDING_TEMPLATES.get(merchant_type, MERCHANT_ONBOARDING_TEMPLATES["small_business"])


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        # Create development environment file
        generate_env_file("development", ".env.bemobi.example")
        print("Generated .env.bemobi.example file")
        
        # Run example scenario
        result = await run_example_scenario(
            "latam_coffee_purchase",
            "demo_api_key",
            "demo_secret_key"
        )
        print(f"Example scenario result: {result}")
    
    asyncio.run(main())
