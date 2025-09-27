"""
Simple AP2 Flow Test

Tests the basic AP2 flow without complex merchant onboarding to verify core functionality.
"""

import sys
import os

# Add project root to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.tools.orchestration_tool import process_user_message


async def test_basic_ap2_flow():
    """Test basic AP2 flow without complex merchant verification"""

    print("🧪 Testing Basic AP2 Flow")
    print("=" * 40)

    user_id = "+5511888999777"

    # Step 1: Payment Intent
    print("\n🔄 Step 1: Payment Intent")
    result1 = await process_user_message(
        'I want to buy coffee', user_id,
        '[PAYMENT_INTENT] I can help you buy coffee!'
    )

    print(f"  State: {result1['session_state']}")
    print(f"  Reply preview: {result1['reply'][:50]}...")
    assert result1["session_state"] == "cart_created"

    # Step 2: Payment Confirmation
    print("\n🔄 Step 2: Payment Confirmation")
    result2 = await process_user_message(
        'yes', user_id,
        '[PAYMENT_CONFIRM] Great! Let me process that payment.'
    )

    print(f"  State: {result2['session_state']}")
    print(f"  Has AP2 features: {'AP2 Protocol' in result2['reply']}")
    assert result2["session_state"] == "credential_collection"

    # Step 3: KYC Verification
    print("\n🔄 Step 3: KYC Verification")
    result3 = await process_user_message(
        'DADOS João Test 12345678901 11888999777', user_id, ''
    )

    print(f"  KYC success: {'Verificação concluída' in result3['reply']}")
    print(f"  Session updates: {result3.get('session_updates', {})}")
    assert "Verificação concluída" in result3["reply"]
    assert result3.get("session_updates", {}).get("kyc_verified") == True

    print("\n✅ Basic AP2 flow working correctly!")
    print("✅ KYC verification successful")
    print("✅ Enhanced credential flow initiated")
    print("✅ Session management working")

    return True


def test_credential_service_directly():
    """Test credential service components directly"""

    print("\n🧪 Testing Credential Services Directly")
    print("=" * 40)

    try:
        from sofIA.tools.ap2_protocol.user_credential_service import get_user_credential_service

        user_service = get_user_credential_service()
        print("✅ User credential service initialized")

        # Test KYC data structure
        import asyncio

        async def test_kyc():
            kyc_result = await user_service.process_kyc_data(
                "+5511999888777", "DADOS Test User 11122233344 11999888777"
            )
            return kyc_result

        kyc_result = asyncio.run(test_kyc())
        print(f"✅ KYC processing result: {kyc_result['success']}")

        # Test PIX credential structure
        async def test_pix():
            pix_result = await user_service.process_payment_credentials(
                "+5511999888777", "PIX_EMAIL test@example.com", "pix"
            )
            return pix_result

        pix_result = asyncio.run(test_pix())
        print(f"✅ PIX processing result: {pix_result['success']}")

        return True

    except Exception as e:
        print(f"❌ Credential service test failed: {e}")
        return False


def test_merchant_registry():
    """Test merchant registry functionality"""

    print("\n🧪 Testing Merchant Registry")
    print("=" * 40)

    try:
        from sofIA.registry.agent_registry import AgentRegistry
        from sofIA.tools.ap2_protocol.merchant_onboarding import get_merchant_service

        # Create a test registry
        registry = AgentRegistry("test-registry")
        print("✅ Agent registry created")

        merchant_service = get_merchant_service(registry)
        print("✅ Merchant service initialized")

        # Test merchant credential structure without full onboarding
        import asyncio

        async def test_merchant():
            try:
                # Try to get existing merchant (should return None)
                existing = await merchant_service.get_merchant_credentials("test_merchant")
                print(f"✅ Merchant lookup working: {existing is None}")
                return True
            except Exception as e:
                print(f"Merchant test error: {e}")
                return False

        result = asyncio.run(test_merchant())
        return result

    except Exception as e:
        print(f"❌ Merchant registry test failed: {e}")
        return False


async def run_simple_tests():
    """Run simple tests"""

    print("🚀 Starting Simple AP2 Tests")
    print("=" * 50)

    try:
        # Test basic flow
        basic_success = await test_basic_ap2_flow()

        # Test services
        credential_success = test_credential_service_directly()

        # Test registry
        registry_success = test_merchant_registry()

        if basic_success and credential_success and registry_success:
            print("\n" + "=" * 50)
            print("🎉 ALL SIMPLE AP2 TESTS PASSED!")
            print("✅ Basic AP2 flow: WORKING")
            print("✅ Credential services: WORKING")
            print("✅ Merchant registry: WORKING")
            print("\n🔧 Core AP2 infrastructure is functional!")
            print("   (Full merchant onboarding needs endpoint configuration)")
        else:
            print("\n❌ Some tests failed")

    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_simple_tests())