"""
Teste de Produção do Mercado Pago
AVISO: Este teste usa credenciais de produção e pode processar pagamentos reais!
"""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use production Mercado Pago settings
os.environ["MERCADOPAGO_USE_MOCK"] = "false"
os.environ["MERCADOPAGO_ENVIRONMENT"] = "production"

async def test_mercadopago_production():
    """Test Mercado Pago production integration - HANDLES REAL MONEY"""
    print("🚨 ATENÇÃO: TESTE DE PRODUÇÃO - PODE PROCESSAR PAGAMENTOS REAIS!")
    print("=" * 60)

    # Double confirmation for production testing
    confirmation = input("Digite 'CONFIRMO' para continuar com teste de produção: ")
    if confirmation != "CONFIRMO":
        print("❌ Teste cancelado por segurança")
        return

    try:
        from sofIA.tools.mercadopago.ap2_mercadopago_integration import AP2MercadoPagoIntegration

        # Initialize integration with production settings
        integration = AP2MercadoPagoIntegration()
        print("✅ Integration initialized for PRODUCTION")

        # Test payment flow with smaller amount for safety
        user_message = "Quero comprar um café"
        user_id = "test_production_user_123"

        print(f"\n🔷 Testing production payment flow")
        print(f"💬 Message: '{user_message}'")
        print(f"👤 User: {user_id}")

        result = await integration.process_whatsapp_payment_flow(
            user_message=user_message,
            user_id=user_id,
            merchant_id="mercadopago_demo_001"  # Using demo merchant for safety
        )

        if result["success"]:
            print("✅ Production payment flow created successfully!")
            print(f"   💰 Amount: {result['currency']} {result['total_amount']:.2f}")
            print(f"   🛒 Cart ID: {result['cart_id']}")
            print(f"   📦 Preference ID: {result['mercadopago_preference_id']}")
            print(f"   🌐 Checkout URL: {result.get('checkout_url', 'N/A')}")

            # For production, we should NOT automatically complete payment
            # This requires actual user interaction/payment method entry
            print(f"\n🔷 Production payment flow ready")
            print(f"ℹ️  In production, user would:")
            print(f"   1. Access checkout URL to enter payment details")
            print(f"   2. Complete payment through Mercado Pago interface")
            print(f"   3. Webhook would notify payment completion")
            print(f"   4. AP2 Payment Mandate would be created automatically")

            # Check if we have a valid checkout URL
            if result.get('checkout_url'):
                print(f"\n✅ Real Mercado Pago checkout available at:")
                print(f"   {result['checkout_url']}")
                print(f"🚨 WARNING: This is a REAL payment link!")

        else:
            print(f"❌ Production payment flow failed: {result.get('error')}")

    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
    except Exception as e:
        print(f"❌ Production Test Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"\n🎉 Production test completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_mercadopago_production())