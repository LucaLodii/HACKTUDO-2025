"""
Teste Simples da Integração Mercado Pago
Este teste funciona sem credenciais usando modo mock
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set mock mode for testing without credentials
os.environ["MERCADOPAGO_USE_MOCK"] = "true"
os.environ["MERCADOPAGO_ENVIRONMENT"] = "sandbox"

async def test_mercadopago_integration():
    """Test Mercado Pago integration in mock mode"""
    print("🚀 Testing Mercado Pago Integration (Mock Mode)")
    print("=" * 50)
    
    try:
        from sofIA.tools.mercadopago.ap2_mercadopago_integration import AP2MercadoPagoIntegration
        
        # Initialize integration
        integration = AP2MercadoPagoIntegration()
        print("✅ Integration initialized successfully")
        
        # Test payment flow
        user_message = "Quero comprar um café"
        user_id = "test_user_123"
        
        print(f"\n🔷 Testing payment flow with message: '{user_message}'")
        
        result = await integration.process_whatsapp_payment_flow(
            user_message=user_message,
            user_id=user_id,
            merchant_id="mercadopago_demo_001"
        )
        
        if result["success"]:
            print("✅ Payment flow created successfully!")
            print(f"   💰 Amount: {result['currency']} {result['total_amount']:.2f}")
            print(f"   🛒 Cart ID: {result['cart_id']}")
            print(f"   📦 Preference ID: {result['mercadopago_preference_id']}")
            
            # Test payment completion
            cart_id = result["cart_id"]
            print(f"\n🔷 Testing payment completion...")
            
            payment_result = await integration.complete_payment(
                cart_id=cart_id,
                payment_method="credit_card"
            )
            
            if payment_result["success"]:
                print("✅ Payment completed successfully!")
                print(f"   🆔 Transaction ID: {payment_result['transaction_id']}")
                print(f"   📊 Status: {payment_result['status']}")
                print(f"   💬 Message: {payment_result['message']}")
                print(f"   🔐 AP2 Compliant: {payment_result['ap2_compliant']}")
                print(f"   🛡️ Tokenized: {payment_result['tokenized_payment']}")
            else:
                print(f"❌ Payment completion failed: {payment_result.get('error')}")
        else:
            print(f"❌ Payment flow failed: {result.get('error')}")
        
    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("💡 Make sure all dependencies are installed")
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_mercadopago_integration())
