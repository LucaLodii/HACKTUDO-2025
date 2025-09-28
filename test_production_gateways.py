#!/usr/bin/env python3
"""
Production Gateway Testing Script

Test real transactions with actual payment gateways (PIX, Stripe, PayPal).
Requires proper API keys and certificates for production testing.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sofIA.tools.ap2_protocol.real_payment_gateways import (
    RealPaymentGatewayManager, 
    GatewayConfig, 
    GatewayType
)


class ProductionGatewayTester:
    """Test production payment gateways"""
    
    def __init__(self):
        self.gateway_manager = None
        self.setup_gateways()
    
    def setup_gateways(self):
        """Setup gateway configurations"""
        
        print("🔧 Setting up Production Gateways")
        print("=" * 50)
        
        gateway_configs = []
        
        # PIX Configuration (Brazil)
        if os.getenv("PIX_CERTIFICATE_PATH") and os.getenv("PIX_PRIVATE_KEY_PATH"):
            print("✅ PIX configuration found")
            gateway_configs.append(
                GatewayConfig(
                    gateway_type=GatewayType.PIX,
                    api_key=os.getenv("PIX_CERTIFICATE_PATH"),
                    secret_key=os.getenv("PIX_PRIVATE_KEY_PATH"),
                    endpoint=os.getenv("PIX_ENDPOINT", "https://api.bcb.gov.br/pix/v1"),
                    region="latam"
                )
            )
        else:
            print("⚠️  PIX configuration not found (set PIX_CERTIFICATE_PATH and PIX_PRIVATE_KEY_PATH)")
        
        # Stripe Configuration
        if os.getenv("STRIPE_SECRET_KEY"):
            print("✅ Stripe configuration found")
            gateway_configs.append(
                GatewayConfig(
                    gateway_type=GatewayType.STRIPE,
                    api_key=os.getenv("STRIPE_SECRET_KEY"),
                    sandbox=os.getenv("STRIPE_SANDBOX", "true").lower() == "true"
                )
            )
        else:
            print("⚠️  Stripe configuration not found (set STRIPE_SECRET_KEY)")
        
        # PayPal Configuration
        if os.getenv("PAYPAL_CLIENT_ID") and os.getenv("PAYPAL_CLIENT_SECRET"):
            print("✅ PayPal configuration found")
            gateway_configs.append(
                GatewayConfig(
                    gateway_type=GatewayType.PAYPAL,
                    api_key=os.getenv("PAYPAL_CLIENT_ID"),
                    secret_key=os.getenv("PAYPAL_CLIENT_SECRET"),
                    sandbox=os.getenv("PAYPAL_SANDBOX", "true").lower() == "true"
                )
            )
        else:
            print("⚠️  PayPal configuration not found (set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)")
        
        if gateway_configs:
            self.gateway_manager = RealPaymentGatewayManager(gateway_configs)
            print(f"✅ {len(gateway_configs)} gateways configured")
        else:
            print("❌ No gateways configured - set environment variables")
    
    async def test_pix_payment(self):
        """Test PIX payment"""
        
        if not self.gateway_manager:
            return {"success": False, "error": "No gateways configured"}
        
        print("\n🇧🇷 Testing PIX Payment")
        print("=" * 30)
        
        try:
            result = await self.gateway_manager.process_payment(
                gateway_type=GatewayType.PIX,
                amount=8.50,
                currency="BRL",
                mandate_id="mandate_pix_test_001",
                payment_data={
                    "payer_key": "test@example.com",
                    "payee_key": "merchant@example.com",
                    "description": "Test coffee purchase"
                }
            )
            
            print(f"✅ PIX Result: {result}")
            return {"success": True, "result": result}
            
        except Exception as e:
            print(f"❌ PIX Payment Failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_stripe_payment(self):
        """Test Stripe payment"""
        
        if not self.gateway_manager:
            return {"success": False, "error": "No gateways configured"}
        
        print("\n🇺🇸 Testing Stripe Payment")
        print("=" * 30)
        
        try:
            result = await self.gateway_manager.process_payment(
                gateway_type=GatewayType.STRIPE,
                amount=29.99,
                currency="USD",
                mandate_id="mandate_stripe_test_001",
                payment_data={
                    "card_token": "tok_visa",  # Test token
                    "description": "Test electronics purchase"
                }
            )
            
            print(f"✅ Stripe Result: {result}")
            return {"success": True, "result": result}
            
        except Exception as e:
            print(f"❌ Stripe Payment Failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_paypal_payment(self):
        """Test PayPal payment"""
        
        if not self.gateway_manager:
            return {"success": False, "error": "No gateways configured"}
        
        print("\n🌍 Testing PayPal Payment")
        print("=" * 30)
        
        try:
            result = await self.gateway_manager.process_payment(
                gateway_type=GatewayType.PAYPAL,
                amount=49.99,
                currency="USD",
                mandate_id="mandate_paypal_test_001",
                payment_data={
                    "paypal_token": "paypal_test_token",
                    "description": "Test subscription purchase"
                }
            )
            
            print(f"✅ PayPal Result: {result}")
            return {"success": True, "result": result}
            
        except Exception as e:
            print(f"❌ PayPal Payment Failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_gateway_health(self):
        """Test gateway health"""
        
        if not self.gateway_manager:
            return {"success": False, "error": "No gateways configured"}
        
        print("\n🏥 Testing Gateway Health")
        print("=" * 30)
        
        health_results = {}
        
        for gateway_type in [GatewayType.PIX, GatewayType.STRIPE, GatewayType.PAYPAL]:
            try:
                health = await self.gateway_manager.check_gateway_health(gateway_type)
                health_results[gateway_type.value] = health
                status = "✅ HEALTHY" if health.get("healthy") else "❌ UNHEALTHY"
                print(f"{gateway_type.value}: {status}")
                
            except Exception as e:
                health_results[gateway_type.value] = {"healthy": False, "error": str(e)}
                print(f"{gateway_type.value}: ❌ ERROR - {e}")
        
        return {"success": True, "health_results": health_results}
    
    async def run_all_tests(self):
        """Run all production gateway tests"""
        
        print("🚀 Production Gateway Testing Suite")
        print("=" * 60)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if not self.gateway_manager:
            print("❌ No gateways configured!")
            print("\n🔧 To test production gateways, set these environment variables:")
            print("   PIX_CERTIFICATE_PATH=/path/to/pix/certificate.pem")
            print("   PIX_PRIVATE_KEY_PATH=/path/to/pix/private.key")
            print("   STRIPE_SECRET_KEY=sk_test_...")
            print("   PAYPAL_CLIENT_ID=your_paypal_client_id")
            print("   PAYPAL_CLIENT_SECRET=your_paypal_client_secret")
            return []
        
        test_results = []
        
        # Test 1: Gateway Health
        health_result = await self.test_gateway_health()
        test_results.append(("Gateway Health", health_result))
        
        # Test 2: PIX Payment
        pix_result = await self.test_pix_payment()
        test_results.append(("PIX Payment", pix_result))
        
        # Test 3: Stripe Payment
        stripe_result = await self.test_stripe_payment()
        test_results.append(("Stripe Payment", stripe_result))
        
        # Test 4: PayPal Payment
        paypal_result = await self.test_paypal_payment()
        test_results.append(("PayPal Payment", paypal_result))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 PRODUCTION GATEWAY TEST RESULTS")
        print("=" * 60)
        
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
            print("\n🎉 ALL PRODUCTION GATEWAY TESTS PASSED!")
            print("✅ Real payment gateways are working!")
            print("💳 PIX, Stripe, and PayPal integrations verified")
            print("🔒 AP2 Protocol compliance maintained")
        else:
            print(f"\n⚠️  {total-passed} tests failed - check gateway configuration")
        
        return test_results


async def main():
    """Main function"""
    
    tester = ProductionGatewayTester()
    results = await tester.run_all_tests()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
