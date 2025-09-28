"""
Mercado Pago Integration Example for sofIA

This example demonstrates how to integrate Mercado Pago payment processing
with the sofIA WhatsApp payment agent using the AP2 protocol.

This is a complete, production-ready example showing:
1. Environment setup
2. Payment preference creation
3. Tokenized payment processing
4. Error handling
5. Status monitoring
"""

import os
import sys
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sofIA.tools.mercadopago.ap2_mercadopago_integration import AP2MercadoPagoIntegration


async def demonstrate_mercadopago_integration():
    """
    Complete demonstration of Mercado Pago integration with AP2 protocol
    """
    print("🚀 Mercado Pago Integration Demo with AP2 Protocol")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize integration
    integration = AP2MercadoPagoIntegration()
    
    # Demo user data
    user_id = "demo_whatsapp_user_123"
    
    # ===============================
    # Step 1: Process User Intent
    # ===============================
    print("\n🔷 STEP 1: Processing User Purchase Intent")
    print("-" * 40)
    
    user_message = "Quero comprar um café"
    print(f"User Message: '{user_message}'")
    
    payment_flow_result = await integration.process_whatsapp_payment_flow(
        user_message=user_message,
        user_id=user_id,
        merchant_id="mercadopago_demo_001"
    )
    
    if not payment_flow_result["success"]:
        print(f"❌ Payment flow failed: {payment_flow_result['error']}")
        return
    
    print(f"✅ Payment Intent Created Successfully!")
    print(f"   💰 Amount: {payment_flow_result['currency']} {payment_flow_result['total_amount']:.2f}")
    print(f"   🛒 Cart ID: {payment_flow_result['cart_id']}")
    print(f"   📦 Mercado Pago Preference: {payment_flow_result['mercadopago_preference_id']}")
    print(f"   🔗 Checkout URL: {payment_flow_result.get('checkout_url', 'N/A')}")
    
    cart_id = payment_flow_result["cart_id"]
    
    # Show available payment methods
    print(f"\n💳 Available Payment Methods:")
    for method in payment_flow_result["available_payment_methods"]:
        print(f"   - {method.replace('_', ' ').title()}")
    
    # ===============================
    # Step 2: Complete Payment
    # ===============================
    print(f"\n🔷 STEP 2: Completing Payment")
    print("-" * 40)
    
    # Demo: Try different payment methods
    payment_methods_to_test = ["credit_card", "pix", "boleto"]
    
    for payment_method in payment_methods_to_test:
        print(f"\n🧪 Testing Payment Method: {payment_method.replace('_', ' ').title()}")
        
        # Complete payment with mock tokenized data
        payment_result = await integration.complete_payment(
            cart_id=cart_id,
            payment_method=payment_method
        )
        
        if payment_result["success"]:
            print(f"✅ Payment Successful!")
            print(f"   🆔 Transaction ID: {payment_result['transaction_id']}")
            print(f"   📋 AP2 Mandate ID: {payment_result['ap2_payment_mandate_id']}")
            print(f"   📊 Status: {payment_result['status']}")
            print(f"   📊 Status Detail: {payment_result.get('status_detail', 'N/A')}")
            print(f"   💳 Payment Method ID: {payment_result.get('payment_method_id', 'N/A')}")
            print(f"   💬 Message: {payment_result['message']}")
            print(f"   🔐 AP2 Compliant: {payment_result['ap2_compliant']}")
            print(f"   🛡️ Tokenized: {payment_result['tokenized_payment']}")
            
            # Show PIX specific data
            if payment_method == "pix":
                point_of_interaction = payment_result.get("point_of_interaction", {})
                if point_of_interaction:
                    print(f"   🔗 PIX Data Available: {bool(point_of_interaction)}")
            
            # Test status checking
            print(f"\n🔍 Checking Transaction Status...")
            status_result = await integration.get_transaction_status(cart_id)
            
            if status_result["success"]:
                print(f"   📊 Current Status: {status_result['status']}")
                print(f"   💰 Amount: {status_result['currency']} {status_result['amount']:.2f}")
                print(f"   📅 Created: {status_result['created_at']}")
            
            break  # Exit after first successful payment
        else:
            print(f"❌ Payment Failed: {payment_result['error']}")
    
    # ===============================
    # Step 3: Error Handling Demo
    # ===============================
    print(f"\n🔷 STEP 3: Error Handling Demonstration")
    print("-" * 40)
    
    # Test with invalid cart ID
    invalid_status = await integration.get_transaction_status("invalid_cart_id")
    print(f"🧪 Invalid Cart ID Test: {invalid_status}")
    
    # Test with invalid payment method
    invalid_payment = await integration.complete_payment(
        cart_id=cart_id,
        payment_method="invalid_method"
    )
    print(f"🧪 Invalid Payment Method Test: {'Success' if not invalid_payment.get('success') else 'Unexpected Success'}")
    
    print(f"\n🎉 Mercado Pago Integration Demo Complete!")
    print("=" * 60)


def demonstrate_tokenized_payment_data():
    """
    Show how to handle real tokenized payment data from AP2 protocol
    """
    print("\n🔐 Tokenized Payment Data Examples")
    print("-" * 40)
    
    # Example 1: Credit Card Token (from AP2 protocol)
    credit_card_token = {
        "method": "credit_card",
        "token": "card_token_1234567890abcdef",  # Mercado Pago card token
        "installments": 3,                       # 3x installments
        "issuer_id": "25",                       # Banco do Brasil
        "payment_method_id": "visa",             # Visa card
        "security_code": "123"                   # CVV (if required)
    }
    
    print("💳 Credit Card Tokenized Data:")
    print(f"   Token: {credit_card_token['token']}")
    print(f"   Installments: {credit_card_token['installments']}")
    print(f"   Issuer ID: {credit_card_token['issuer_id']}")
    print(f"   Payment Method: {credit_card_token['payment_method_id']}")
    
    # Example 2: PIX Payment Data
    pix_data = {
        "method": "pix"
    }
    
    print("\n🏦 PIX Payment Data:")
    print(f"   Method: {pix_data['method']}")
    print(f"   Note: PIX doesn't require additional tokenized data")
    
    # Example 3: Customer Data (required for Mercado Pago)
    customer_data = {
        "name": "João",
        "surname": "da Silva",
        "email": "joao@email.com",
        "cpf": "12345678901",
        "phone": "11987654321",
        "address": {
            "street": "Rua das Flores",
            "number": "123",
            "city": "São Paulo",
            "state": "SP",
            "zip_code": "01234567"
        }
    }
    
    print("\n👤 Customer Data (for compliance):")
    print(f"   Name: {customer_data['name']} {customer_data['surname']}")
    print(f"   Email: {customer_data['email']}")
    print(f"   CPF: {customer_data['cpf']}")
    print(f"   Phone: {customer_data['phone']}")


def show_environment_setup():
    """
    Show how to set up environment variables for Mercado Pago
    """
    print("\n⚙️ Environment Setup for Mercado Pago")
    print("-" * 40)
    
    env_example = """
# Mercado Pago API Credentials (get from Mercado Pago Dashboard)
MERCADOPAGO_ACCESS_TOKEN=your_access_token_here
MERCADOPAGO_PUBLIC_KEY=your_public_key_here
MERCADOPAGO_CLIENT_ID=your_client_id_here
MERCADOPAGO_CLIENT_SECRET=your_client_secret_here

# Environment Configuration
MERCADOPAGO_ENVIRONMENT=sandbox  # or 'production'

# Development Settings
MERCADOPAGO_USE_MOCK=true  # Use mock mode for development
MERCADOPAGO_WEBHOOK_URL=https://your-domain.com/webhooks/mercadopago

# sofIA Integration
GOOGLE_API_KEY=your_google_api_key_here  # Required for AP2 protocol
"""
    
    print("📝 Required Environment Variables (.env file):")
    print(env_example)
    
    print("🔑 How to get Mercado Pago credentials:")
    print("   1. Create account at https://www.mercadopago.com.br/")
    print("   2. Access the Developer Dashboard")
    print("   3. Create a new application")
    print("   4. Copy Access Token and Public Key")
    print("   5. Start with sandbox credentials for testing")


def show_production_checklist():
    """
    Show production deployment checklist
    """
    print("\n✅ Production Deployment Checklist")
    print("-" * 40)
    
    checklist = [
        "✅ Mercado Pago production credentials configured",
        "✅ MERCADOPAGO_ENVIRONMENT set to 'production'",
        "✅ MERCADOPAGO_USE_MOCK set to 'false'", 
        "✅ Webhook URL configured and accessible",
        "✅ SSL certificate installed",
        "✅ Error logging and monitoring configured",
        "✅ AP2 protocol compliance verified",
        "✅ Payment method testing completed",
        "✅ Customer data validation implemented",
        "✅ Refund and chargeback handling ready",
        "✅ PIX integration tested",
        "✅ Installments configuration verified"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n⚠️ Important Security Notes:")
    print("   - Never hardcode API credentials in source code")
    print("   - Use environment variables for all sensitive data")
    print("   - Implement proper webhook signature verification")
    print("   - Log all transactions for audit purposes")
    print("   - Follow PCI DSS compliance guidelines")
    print("   - Monitor for suspicious payment patterns")


def show_mercadopago_advantages():
    """
    Show advantages of Mercado Pago over other gateways
    """
    print("\n🌟 Mercado Pago Advantages")
    print("-" * 40)
    
    advantages = [
        "🌍 International developers accepted",
        "🇧🇷 Strong presence in Brazil and LATAM",
        "⚡ Instant PIX payments",
        "💳 All major credit/debit cards supported",
        "📱 Mobile-first payment experience",
        "🔒 Advanced fraud protection",
        "📊 Comprehensive analytics dashboard",
        "🛠️ Excellent API documentation",
        "🎯 High approval rates",
        "💰 Competitive transaction fees",
        "🔄 Easy refund and chargeback management",
        "📞 24/7 developer support"
    ]
    
    for advantage in advantages:
        print(f"   {advantage}")


async def main():
    """Main demo function"""
    print("🏦 Mercado Pago + AP2 Protocol Integration for sofIA")
    print("🤖 AI WhatsApp Payment Agent")
    print("=" * 60)
    
    # Show setup information
    show_environment_setup()
    
    # Show Mercado Pago advantages
    show_mercadopago_advantages()
    
    # Show tokenized data examples
    demonstrate_tokenized_payment_data()
    
    # Run integration demo
    await demonstrate_mercadopago_integration()
    
    # Show production checklist
    show_production_checklist()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
