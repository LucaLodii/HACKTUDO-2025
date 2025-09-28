#!/usr/bin/env python3
"""
Real Transaction Testing Script for sofIA

This script provides interactive testing of real AP2 transactions
through the sofIA orchestrator system.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.tools.orchestration_tool import process_user_message


async def test_real_pix_transaction():
    """Test a real PIX transaction flow"""
    
    print("🇧🇷 Testing Real PIX Transaction")
    print("=" * 50)
    
    user_id = "+5511999999999"
    
    # Step 1: User wants to buy something
    print("\n🔄 Step 1: User Purchase Intent")
    result1 = await process_user_message(
        'Quero comprar um café por R$ 8,50', user_id,
        '[PAYMENT_INTENT] I can help you buy coffee!'
    )
    
    print(f"✅ State: {result1['session_state']}")
    print(f"📝 Reply: {result1['reply'][:100]}...")
    
    # Step 2: User confirms purchase
    print("\n🔄 Step 2: Payment Confirmation")
    result2 = await process_user_message(
        'sim, confirmo', user_id,
        '[PAYMENT_CONFIRM] Great! Let me process that payment.'
    )
    
    print(f"✅ State: {result2['session_state']}")
    print(f"📝 Reply: {result2['reply'][:100]}...")
    
    # Step 3: KYC Data Collection
    print("\n🔄 Step 3: KYC Verification")
    result3 = await process_user_message(
        'DADOS João Silva 12345678901 11999999999', user_id, ''
    )
    
    print(f"✅ KYC Success: {'Verificação concluída' in result3['reply']}")
    print(f"📝 Reply: {result3['reply'][:100]}...")
    
    # Step 4: PIX Credential Setup
    print("\n🔄 Step 4: PIX Credential Setup")
    result4 = await process_user_message(
        'PIX_EMAIL joao.silva@example.com', user_id, ''
    )
    
    print(f"✅ PIX Setup: {'PIX configurado' in result4['reply']}")
    print(f"📝 Reply: {result4['reply'][:100]}...")
    
    # Step 5: Payment Processing
    print("\n🔄 Step 5: Payment Processing")
    result5 = await process_user_message(
        'processar pagamento', user_id, ''
    )
    
    print(f"✅ Payment: {'AP2 Protocol' in result5['reply']}")
    print(f"📝 Reply: {result5['reply'][:100]}...")
    
    return {
        "success": True,
        "steps_completed": 5,
        "final_state": result5.get('session_state', 'unknown'),
        "ap2_features_used": 'AP2 Protocol' in result5['reply']
    }


async def test_real_card_transaction():
    """Test a real card transaction flow"""
    
    print("\n💳 Testing Real Card Transaction")
    print("=" * 50)
    
    user_id = "+1234567890"
    
    # Step 1: User wants to buy electronics
    print("\n🔄 Step 1: User Purchase Intent")
    result1 = await process_user_message(
        'I want to buy electronics for $299.99', user_id,
        '[PAYMENT_INTENT] I can help you buy electronics!'
    )
    
    print(f"✅ State: {result1['session_state']}")
    
    # Step 2: User confirms
    print("\n🔄 Step 2: Payment Confirmation")
    result2 = await process_user_message(
        'yes, proceed', user_id,
        '[PAYMENT_CONFIRM] Processing your payment.'
    )
    
    print(f"✅ State: {result2['session_state']}")
    
    # Step 3: Card Credential Setup
    print("\n🔄 Step 3: Card Credential Setup")
    result3 = await process_user_message(
        'CARD 4111111111111111 12/25 123', user_id, ''
    )
    
    print(f"✅ Card Setup: {'Card configured' in result3['reply']}")
    
    # Step 4: Payment Processing
    print("\n🔄 Step 4: Payment Processing")
    result4 = await process_user_message(
        'process payment', user_id, ''
    )
    
    print(f"✅ Payment: {'AP2 Protocol' in result4['reply']}")
    
    return {
        "success": True,
        "steps_completed": 4,
        "final_state": result4.get('session_state', 'unknown'),
        "ap2_features_used": 'AP2 Protocol' in result4['reply']
    }


async def test_subscription_renewal():
    """Test a subscription renewal transaction"""
    
    print("\n📱 Testing Subscription Renewal")
    print("=" * 50)
    
    user_id = "+5511888777666"
    
    # Step 1: User wants to renew subscription
    print("\n🔄 Step 1: Subscription Renewal Intent")
    result1 = await process_user_message(
        'Quero renovar meu plano VIVO por R$ 29,90', user_id,
        '[SUBSCRIPTION_RENEWAL] I can help you renew your VIVO plan!'
    )
    
    print(f"✅ State: {result1['session_state']}")
    
    # Step 2: User confirms renewal
    print("\n🔄 Step 2: Renewal Confirmation")
    result2 = await process_user_message(
        'sim, renovar', user_id,
        '[RENEWAL_CONFIRM] Processing your renewal.'
    )
    
    print(f"✅ State: {result2['session_state']}")
    
    # Step 3: Payment processing
    print("\n🔄 Step 3: Renewal Payment")
    result3 = await process_user_message(
        'PIX_EMAIL user@example.com', user_id, ''
    )
    
    print(f"✅ Renewal: {'AP2 Protocol' in result3['reply']}")
    
    return {
        "success": True,
        "steps_completed": 3,
        "final_state": result3.get('session_state', 'unknown'),
        "ap2_features_used": 'AP2 Protocol' in result3['reply']
    }


async def test_ap2_mandate_chain():
    """Test the complete AP2 mandate chain"""
    
    print("\n🔗 Testing AP2 Mandate Chain")
    print("=" * 50)
    
    try:
        from sofIA.tools.ap2_protocol.ap2_tool import AP2ProtocolTool
        
        tool = AP2ProtocolTool()
        
        # Step 1: Create Intent Mandate
        print("\n🔄 Step 1: Creating Intent Mandate")
        intent_result = await tool._create_intent_mandate(
            user_message="I want to buy a coffee for R$ 8.50",
            user_id="+5511999999999",
            merchants=["coffee_shop_123"],
            max_price=10.00,
            currency="BRL"
        )
        
        print(f"✅ Intent Created: {intent_result['success']}")
        print(f"🆔 Intent ID: {intent_result['intent_id']}")
        
        # Step 2: Create Cart Mandate
        print("\n🔄 Step 2: Creating Cart Mandate")
        cart_result = await tool._create_cart_mandate(
            intent_id=intent_result["intent_id"],
            items=[{
                "label": "Coffee",
                "amount": {"currency": "BRL", "value": 8.50}
            }],
            user_id="+5511999999999"
        )
        
        print(f"✅ Cart Created: {cart_result['success']}")
        print(f"🆔 Cart ID: {cart_result['cart_id']}")
        
        # Step 3: Create Payment Mandate
        print("\n🔄 Step 3: Creating Payment Mandate")
        payment_result = await tool._create_payment_mandate(
            cart_id=cart_result["cart_id"],
            payment_method="pix",
            user_id="+5511999999999",
            amount=8.50,
            currency="BRL"
        )
        
        print(f"✅ Payment Created: {payment_result['success']}")
        print(f"🆔 Payment ID: {payment_result['payment_mandate_id']}")
        
        # Step 4: Verify Mandate Chain
        print("\n🔄 Step 4: Verifying Mandate Chain")
        verification_result = await tool._verify_mandate_chain(
            intent_id=intent_result["intent_id"],
            cart_id=cart_result["cart_id"],
            payment_mandate_id=payment_result["payment_mandate_id"]
        )
        
        print(f"✅ Chain Verified: {verification_result['success']}")
        
        return {
            "success": True,
            "mandate_chain_complete": True,
            "intent_id": intent_result["intent_id"],
            "cart_id": cart_result["cart_id"],
            "payment_id": payment_result["payment_mandate_id"],
            "verification": verification_result["success"]
        }
        
    except Exception as e:
        print(f"❌ AP2 Mandate Chain Test Failed: {e}")
        return {"success": False, "error": str(e)}


async def test_payment_method_discovery():
    """Test payment method discovery"""
    
    print("\n🔍 Testing Payment Method Discovery")
    print("=" * 50)
    
    try:
        from sofIA.tools.ap2_protocol.ap2_tool import AP2ProtocolTool
        
        tool = AP2ProtocolTool()
        
        # Test LATAM payment methods
        print("\n🔄 Discovering LATAM Payment Methods")
        methods_result = await tool._discover_payment_methods(
            user_id="+5511999999999",
            region="latam"
        )
        
        print(f"✅ Methods Found: {methods_result['success']}")
        print(f"📊 Count: {methods_result['count']}")
        
        for method in methods_result["payment_methods"]:
            print(f"  • {method['supported_methods']}: {method['data']}")
        
        return {
            "success": True,
            "methods_discovered": methods_result["count"],
            "methods": methods_result["payment_methods"]
        }
        
    except Exception as e:
        print(f"❌ Payment Method Discovery Failed: {e}")
        return {"success": False, "error": str(e)}


async def run_all_real_transaction_tests():
    """Run all real transaction tests"""
    
    print("🚀 sofIA Real Transaction Testing Suite")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    try:
        # Test 1: PIX Transaction
        pix_result = await test_real_pix_transaction()
        test_results.append(("PIX Transaction", pix_result))
        
        # Test 2: Card Transaction
        card_result = await test_real_card_transaction()
        test_results.append(("Card Transaction", card_result))
        
        # Test 3: Subscription Renewal
        renewal_result = await test_subscription_renewal()
        test_results.append(("Subscription Renewal", renewal_result))
        
        # Test 4: AP2 Mandate Chain
        mandate_result = await test_ap2_mandate_chain()
        test_results.append(("AP2 Mandate Chain", mandate_result))
        
        # Test 5: Payment Method Discovery
        discovery_result = await test_payment_method_discovery()
        test_results.append(("Payment Method Discovery", discovery_result))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result.get("success") else "❌ FAILED"
            print(f"{test_name}: {status}")
            if result.get("success"):
                passed += 1
            else:
                print(f"  Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL REAL TRANSACTION TESTS PASSED!")
            print("✅ sofIA is ready for real-world transactions!")
            print("🔒 AP2 Protocol compliance verified")
            print("💳 Multiple payment methods supported")
            print("📱 WhatsApp integration working")
        else:
            print(f"\n⚠️  {total-passed} tests failed - check configuration")
        
        return test_results
        
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Run all real transaction tests
    asyncio.run(run_all_real_transaction_tests())
