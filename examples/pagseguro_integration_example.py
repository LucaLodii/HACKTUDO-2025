"""
PagSeguro Integration Example for sofIA

This example demonstrates how to integrate PagSeguro (PagBank) payment processing
with the sofIA WhatsApp payment agent using the AP2 protocol.

This is a complete, production-ready example showing:
1. Environment setup
2. Payment intent creation
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

from sofIA.tools.pagseguro.ap2_pagseguro_integration import AP2PagSeguroIntegration


async def demonstrate_pagseguro_integration():
    """
    Complete demonstration of PagSeguro integration with AP2 protocol
    """
    print("🚀 PagSeguro Integration Demo with AP2 Protocol")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize integration
    integration = AP2PagSeguroIntegration()
    
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
        merchant_id="pagseguro_demo_001"
    )
    
    if not payment_flow_result["success"]:
        print(f"❌ Payment flow failed: {payment_flow_result['error']}")
        return
    
    print(f"✅ Payment Intent Created Successfully!")
    print(f"   💰 Amount: {payment_flow_result['currency']} {payment_flow_result['total_amount']:.2f}")
    print(f"   🛒 Cart ID: {payment_flow_result['cart_id']}")
    print(f"   📦 PagSeguro Order: {payment_flow_result['pagseguro_order_id']}")
    
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
            print(f"   💬 Message: {payment_result['message']}")
            print(f"   🔐 AP2 Compliant: {payment_result['ap2_compliant']}")
            print(f"   🛡️ Tokenized: {payment_result['tokenized_payment']}")
            
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
    
    print(f"\n🎉 PagSeguro Integration Demo Complete!")
    print("=" * 60)


def demonstrate_tokenized_payment_data():
    """
    Show how to handle real tokenized payment data from AP2 protocol
    """
    print("\n🔐 Tokenized Payment Data Examples")
    print("-" * 40)
    
    # Example 1: Credit Card Token (from AP2 protocol)
    credit_card_token = {
        "token": "tok_1234567890abcdef",  # PagSeguro card token
        "cvv_token": "cvv_abc123",        # Tokenized CVV
        "holder_name": "JOAO DA SILVA",
        "installments": 3,
        "brand": "visa"
    }
    
    print("💳 Credit Card Tokenized Data:")
    print(f"   Token: {credit_card_token['token']}")
    print(f"   CVV Token: {credit_card_token['cvv_token']}")
    print(f"   Holder: {credit_card_token['holder_name']}")
    print(f"   Installments: {credit_card_token['installments']}")
    
    # Example 2: PIX Payment Data
    pix_data = {
        "pix_key": "user@email.com",
        "pix_key_type": "email"
    }
    
    print("\n🏦 PIX Payment Data:")
    print(f"   PIX Key: {pix_data['pix_key']}")
    print(f"   Key Type: {pix_data['pix_key_type']}")
    
    # Example 3: Customer Data (required for some payments)
    customer_data = {
        "name": "João da Silva",
        "email": "joao@email.com",
        "cpf": "12345678901",
        "phone_area": "11",
        "phone_number": "987654321",
        "address": {
            "street": "Rua das Flores, 123",
            "city": "São Paulo",
            "state": "SP",
            "postal_code": "01234567"
        }
    }
    
    print("\n👤 Customer Data (for compliance):")
    print(f"   Name: {customer_data['name']}")
    print(f"   Email: {customer_data['email']}")
    print(f"   CPF: {customer_data['cpf']}")
    print(f"   Phone: ({customer_data['phone_area']}) {customer_data['phone_number']}")


def show_environment_setup():
    """
    Show how to set up environment variables for PagSeguro
    """
    print("\n⚙️ Environment Setup for PagSeguro")
    print("-" * 40)
    
    env_example = """
# PagSeguro API Credentials (get from PagSeguro Dashboard)
PAGSEGURO_CLIENT_ID=your_client_id_here
PAGSEGURO_CLIENT_SECRET=your_client_secret_here
PAGSEGURO_ACCESS_TOKEN=your_access_token_here

# Environment Configuration
PAGSEGURO_ENVIRONMENT=sandbox  # or 'production'
PAGSEGURO_BASE_URL=https://sandbox.api.pagseguro.com

# Development Settings
PAGSEGURO_USE_MOCK=true  # Use mock mode for development
PAGSEGURO_WEBHOOK_URL=https://your-domain.com/webhooks/pagseguro

# sofIA Integration
GOOGLE_API_KEY=your_google_api_key_here  # Required for AP2 protocol
"""
    
    print("📝 Required Environment Variables (.env file):")
    print(env_example)
    
    print("🔑 How to get PagSeguro credentials:")
    print("   1. Create account at https://pagseguro.uol.com.br/")
    print("   2. Access the Developer Dashboard")
    print("   3. Generate API credentials")
    print("   4. Copy Client ID, Client Secret, and Access Token")
    print("   5. Start with sandbox environment for testing")


def show_production_checklist():
    """
    Show production deployment checklist
    """
    print("\n✅ Production Deployment Checklist")
    print("-" * 40)
    
    checklist = [
        "✅ PagSeguro production credentials configured",
        "✅ PAGSEGURO_ENVIRONMENT set to 'production'",
        "✅ PAGSEGURO_USE_MOCK set to 'false'", 
        "✅ Webhook URL configured and accessible",
        "✅ SSL certificate installed",
        "✅ Error logging and monitoring configured",
        "✅ AP2 protocol compliance verified",
        "✅ Payment method testing completed",
        "✅ Customer data validation implemented",
        "✅ Refund and chargeback handling ready"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n⚠️ Important Security Notes:")
    print("   - Never hardcode API credentials in source code")
    print("   - Use environment variables for all sensitive data")
    print("   - Implement proper webhook signature verification")
    print("   - Log all transactions for audit purposes")
    print("   - Follow PCI DSS compliance guidelines")


async def main():
    """Main demo function"""
    print("🏦 PagSeguro + AP2 Protocol Integration for sofIA")
    print("🤖 AI WhatsApp Payment Agent")
    print("=" * 60)
    
    # Show setup information
    show_environment_setup()
    
    # Show tokenized data examples
    demonstrate_tokenized_payment_data()
    
    # Run integration demo
    await demonstrate_pagseguro_integration()
    
    # Show production checklist
    show_production_checklist()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
