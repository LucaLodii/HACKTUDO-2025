#!/usr/bin/env python3
"""
API Transaction Testing Script

Test real transactions via HTTP API calls to the sofIA system.
"""

import requests
import json
import asyncio
import time
from datetime import datetime


class sofIATransactionTester:
    """Test sofIA transactions via API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_webhook_endpoint(self, user_id="+5511999999999", message="Quero comprar café por R$ 8,50"):
        """Test WhatsApp webhook endpoint"""
        
        print(f"📱 Testing WhatsApp Webhook")
        print(f"👤 User: {user_id}")
        print(f"💬 Message: {message}")
        
        webhook_data = {
            "from": user_id,
            "text": {"body": message},
            "timestamp": str(int(time.time())),
            "type": "text"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/webhook/whatsapp",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Status: {response.status_code}")
            print(f"📝 Response: {response.text[:200]}...")
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e)}
    
    def test_payment_processing(self, user_id="+5511999999999"):
        """Test complete payment processing flow"""
        
        print(f"\n💳 Testing Complete Payment Flow")
        print(f"👤 User: {user_id}")
        
        # Step 1: Payment intent
        print("\n🔄 Step 1: Payment Intent")
        result1 = self.test_webhook_endpoint(user_id, "Quero comprar café por R$ 8,50")
        
        if not result1["success"]:
            return {"success": False, "error": "Payment intent failed"}
        
        # Step 2: Confirmation
        print("\n🔄 Step 2: Payment Confirmation")
        result2 = self.test_webhook_endpoint(user_id, "sim, confirmo")
        
        if not result2["success"]:
            return {"success": False, "error": "Payment confirmation failed"}
        
        # Step 3: KYC
        print("\n🔄 Step 3: KYC Verification")
        result3 = self.test_webhook_endpoint(user_id, "DADOS João Silva 12345678901 11999999999")
        
        if not result3["success"]:
            return {"success": False, "error": "KYC verification failed"}
        
        # Step 4: PIX Setup
        print("\n🔄 Step 4: PIX Credential Setup")
        result4 = self.test_webhook_endpoint(user_id, "PIX_EMAIL joao.silva@example.com")
        
        if not result4["success"]:
            return {"success": False, "error": "PIX setup failed"}
        
        # Step 5: Payment Processing
        print("\n🔄 Step 5: Payment Processing")
        result5 = self.test_webhook_endpoint(user_id, "processar pagamento")
        
        return {
            "success": result5["success"],
            "steps_completed": 5,
            "results": [result1, result2, result3, result4, result5]
        }
    
    def test_subscription_renewal(self, user_id="+5511888777666"):
        """Test subscription renewal flow"""
        
        print(f"\n📱 Testing Subscription Renewal")
        print(f"👤 User: {user_id}")
        
        # Step 1: Renewal intent
        print("\n🔄 Step 1: Renewal Intent")
        result1 = self.test_webhook_endpoint(user_id, "Quero renovar meu plano VIVO por R$ 29,90")
        
        if not result1["success"]:
            return {"success": False, "error": "Renewal intent failed"}
        
        # Step 2: Confirmation
        print("\n🔄 Step 2: Renewal Confirmation")
        result2 = self.test_webhook_endpoint(user_id, "sim, renovar")
        
        if not result2["success"]:
            return {"success": False, "error": "Renewal confirmation failed"}
        
        # Step 3: Payment
        print("\n🔄 Step 3: Renewal Payment")
        result3 = self.test_webhook_endpoint(user_id, "PIX_EMAIL user@example.com")
        
        return {
            "success": result3["success"],
            "steps_completed": 3,
            "results": [result1, result2, result3]
        }
    
    def test_health_check(self):
        """Test API health"""
        
        print(f"\n🏥 Testing API Health")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"✅ Health Status: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """Run all API tests"""
        
        print("🚀 sofIA API Transaction Testing")
        print("=" * 50)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        
        test_results = []
        
        # Test 1: Health Check
        health_result = self.test_health_check()
        test_results.append(("Health Check", health_result))
        
        if not health_result["success"]:
            print("\n❌ API is not available. Make sure sofIA is running:")
            print("   python app.py")
            return test_results
        
        # Test 2: Payment Processing
        payment_result = self.test_payment_processing()
        test_results.append(("Payment Processing", payment_result))
        
        # Test 3: Subscription Renewal
        renewal_result = self.test_subscription_renewal()
        test_results.append(("Subscription Renewal", renewal_result))
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 API TEST RESULTS")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result.get("success") else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not result.get("success"):
                print(f"  Error: {result.get('error', 'Unknown error')}")
            else:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 ALL API TESTS PASSED!")
            print("✅ sofIA API is working correctly!")
            print("💳 Real transactions can be processed via API")
        else:
            print(f"\n⚠️  {total-passed} tests failed - check API configuration")
        
        return test_results


def main():
    """Main function"""
    
    # Test with default localhost
    tester = sofIATransactionTester()
    
    # You can also test against deployed instances
    # tester = sofIATransactionTester("https://your-deployed-sofia.com")
    
    results = tester.run_all_tests()
    
    return results


if __name__ == "__main__":
    main()
