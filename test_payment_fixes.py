#!/usr/bin/env python3
"""
Test script to verify payment processing fixes
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.tools.orchestration_tool import _parse_payment_credentials, _detect_payment_method

def test_credit_card_parsing():
    """Test credit card data parsing"""
    print("🧪 Testing credit card data parsing...")
    
    # Test credit card message from the logs
    credit_card_message = """CARTAO: 5361 1903 6574 9424 
CVV: 920
Data de validade: 08/27
Nome: Leonardo Ramalho"""
    
    result = _parse_payment_credentials(credit_card_message)
    
    if result:
        print(f"✅ Credit card parsing successful:")
        print(f"   Method: {result['method']}")
        print(f"   Card number: {result['details']['card_number']}")
        print(f"   Expiry: {result['details']['expiry']}")
        print(f"   Name: {result['details']['cardholder_name']}")
        return True
    else:
        print("❌ Credit card parsing failed")
        return False

def test_pix_parsing():
    """Test PIX data parsing"""
    print("\n🧪 Testing PIX data parsing...")
    
    pix_message = "PIX leostuart05@gmail.com"
    
    result = _parse_payment_credentials(pix_message)
    
    if result:
        print(f"✅ PIX parsing successful:")
        print(f"   Method: {result['method']}")
        print(f"   PIX key: {result['details']['pix_key']}")
        return True
    else:
        print("❌ PIX parsing failed")
        return False

def test_payment_method_detection():
    """Test payment method detection"""
    print("\n🧪 Testing payment method detection...")
    
    test_cases = [
        ("CARTAO: 5361 1903 6574 9424", "credit_card"),
        ("PIX leostuart05@gmail.com", "pix"),
        ("Cartão de Crédito", "credit_card"),
        ("PIX_EMAIL test@example.com", "pix")
    ]
    
    all_passed = True
    for message, expected in test_cases:
        detected = _detect_payment_method(message)
        if detected == expected:
            print(f"✅ '{message}' -> {detected}")
        else:
            print(f"❌ '{message}' -> {detected} (expected {expected})")
            all_passed = False
    
    return all_passed

async def test_credential_collection():
    """Test credential collection with actual data"""
    print("\n🧪 Testing credential collection...")
    
    try:
        from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
        from sofIA.tools.ap2_protocol.ap2_credential_collector import get_credential_collector
        
        # Create AP2 agent
        ap2_agent = AP2PaymentAgent(agent_id="test_agent", merchant_id="test_merchant")
        credential_collector = get_credential_collector(ap2_agent)
        
        # Test credit card credentials
        user_payment_data = {
            "method": "basic-card",
            "details": {
                "card_number": "5361190365749424",
                "expiry": "08/27",
                "cardholder_name": "Leonardo Ramalho"
            }
        }
        
        result = await credential_collector.collect_payment_credentials_with_data(
            user_id="test_user",
            cart_mandate_id="test_cart",
            selected_method="basic-card",
            amount=39.90,
            currency="BRL",
            user_payment_data=user_payment_data
        )
        
        if result["success"]:
            print("✅ Credential collection successful")
            print(f"   Collection ID: {result['collection_id']}")
            print(f"   Method: {result['credential_info']['method']}")
            return True
        else:
            print(f"❌ Credential collection failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Credential collection test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing payment processing fixes...\n")
    
    tests = [
        test_credit_card_parsing(),
        test_pix_parsing(),
        test_payment_method_detection(),
        await test_credential_collection()
    ]
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Payment processing fixes are working.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
