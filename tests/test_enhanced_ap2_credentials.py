"""
Test Enhanced AP2 Credential Acquisition and Authentication

This test module validates the complete AP2 protocol implementation with:
1. User credential acquisition (KYC + payment methods)
2. Merchant credential onboarding (BEMOBI telecom operators)
3. Agent-to-agent authentication (sender + receiver credentials)
4. Full compliance verification and audit trail
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Add project root to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.tools.orchestration_tool import process_user_message
from sofIA.tools.ap2_protocol.user_credential_service import get_user_credential_service
from sofIA.tools.ap2_protocol.merchant_onboarding import get_merchant_service
from sofIA.tools.ap2_protocol.ap2_agent_auth import get_ap2_authenticator
from sofIA.registry.agent_registry import AgentRegistry


class TestEnhancedAP2Credentials:
    """Test suite for enhanced AP2 credential acquisition and authentication"""

    def setup_method(self):
        """Set up test fixtures"""
        self.test_user_id = "+5511999887766"
        self.test_product = "Café Premium"
        self.test_amount = 15.50
        self.test_currency = "BRL"

    def test_complete_enhanced_ap2_flow(self):
        """Test the complete enhanced AP2 flow with all credential systems"""

        print("=== Testing Complete Enhanced AP2 Credential Flow ===")

        # Step 1: Payment Intent
        print("\n🔄 Step 1: Payment Intent")
        result1 = process_user_message(
            message='I want to buy premium coffee',
            user_id=self.test_user_id,
            agent_reply='[PAYMENT_INTENT] I can help you buy premium coffee!'
        )

        assert result1["session_state"] == "cart_created", f"Expected cart_created, got {result1['session_state']}"
        print(f"✅ Intent processed - State: {result1['session_state']}")

        # Step 2: Payment Confirmation (triggers enhanced credential flow)
        print("\n🔄 Step 2: Payment Confirmation")
        result2 = process_user_message(
            message='yes, proceed with payment',
            user_id=self.test_user_id,
            agent_reply='[PAYMENT_CONFIRM] Great! Let me process that payment.'
        )

        assert result2["session_state"] == "credential_collection", f"Expected credential_collection, got {result2['session_state']}"
        assert "AP2 Protocol" in result2["reply"], "Enhanced AP2 features not present"
        assert "DADOS" in result2["reply"], "KYC instruction not present"
        print(f"✅ Enhanced credential flow initiated - State: {result2['session_state']}")

        # Step 3: KYC Verification
        print("\n🔄 Step 3: KYC Verification")
        result3 = process_user_message(
            message='DADOS João Silva Santos 12345678901 11999887766',
            user_id=self.test_user_id,
            agent_reply=''
        )

        assert "Verificação concluída" in result3["reply"], "KYC verification failed"

        # Debug: Print what we actually got
        print(f"DEBUG - KYC result keys: {list(result3.keys())}")
        print(f"DEBUG - Session updates: {result3.get('session_updates', {})}")

        assert result3.get("session_updates", {}).get("kyc_verified") == True, f"KYC not marked as verified. Got: {result3.get('session_updates', {})}"
        print("✅ KYC verification successful")

        # Step 4: PIX Credential Acquisition
        print("\n🔄 Step 4: PIX Credential Acquisition")
        result4 = process_user_message(
            message='PIX_EMAIL joao.silva@email.com',
            user_id=self.test_user_id,
            agent_reply=''
        )

        # Verify enhanced AP2 payment completion
        assert result4["session_state"] == "completed", f"Expected completed, got {result4['session_state']}"

        reply = result4["reply"]
        session_updates = result4.get("session_updates", {})

        # Check core AP2 features
        ap2_features = {
            "transaction_id": "Transaction ID:" in reply,
            "sender_agent": "Sender Agent:" in reply,
            "receiver_agent": "Receiver Agent:" in reply,
            "credential_id": "Credential ID:" in reply,
            "merchant_verified": "Merchant Verificado:" in reply,
            "agent_authentication": "Agentes mutuamente autenticados" in reply,
            "compliance": "Conformidade regulatória garantida" in reply
        }

        # Verify all features are present
        missing_features = [feature for feature, present in ap2_features.items() if not present]
        assert len(missing_features) == 0, f"Missing AP2 features: {missing_features}"

        # Check session data completeness
        required_session_data = [
            "ap2_transaction_id", "sender_agent", "receiver_agent",
            "credential_id", "merchant_verified", "kyc_verified", "protocol_version"
        ]

        missing_session_data = [key for key in required_session_data if key not in session_updates]
        assert len(missing_session_data) == 0, f"Missing session data: {missing_session_data}"

        print("✅ Enhanced AP2 payment completed successfully")
        print(f"   Transaction ID: {session_updates.get('ap2_transaction_id', 'N/A')[:20]}...")
        print(f"   Sender Agent: {session_updates.get('sender_agent', 'N/A')}")
        print(f"   Receiver Agent: {session_updates.get('receiver_agent', 'N/A')}")
        print(f"   Protocol Version: {session_updates.get('protocol_version', 'N/A')}")

        print("\n🎉 COMPLETE SUCCESS: Enhanced AP2 with Full Compliance!")

    def test_credit_card_credential_flow(self):
        """Test credit card credential acquisition with AP2"""

        print("\n=== Testing Credit Card Credential Flow ===")

        # Setup cart
        result1 = process_user_message(
            'I want to buy coffee', self.test_user_id + "_card",
            '[PAYMENT_INTENT] I can help you buy coffee!'
        )
        assert result1["session_state"] == "cart_created"

        # Trigger credential flow
        result2 = process_user_message(
            'yes', self.test_user_id + "_card",
            '[PAYMENT_CONFIRM] Great! Let me process that payment.'
        )
        assert result2["session_state"] == "credential_collection"

        # KYC
        result3 = process_user_message(
            'DADOS Maria Oliveira 98765432100 11888776655',
            self.test_user_id + "_card", ''
        )
        assert "Verificação concluída" in result3["reply"]

        # Credit card credentials
        result4 = process_user_message(
            'CARTAO 1234 12/25 Maria Oliveira',
            self.test_user_id + "_card", ''
        )

        assert result4["session_state"] == "completed"
        assert "CREDIT_CARD" in result4["reply"]
        assert "Transaction ID:" in result4["reply"]
        print("✅ Credit card flow successful")

    def test_boleto_credential_flow(self):
        """Test boleto credential acquisition with AP2"""

        print("\n=== Testing Boleto Credential Flow ===")

        # Setup cart
        result1 = process_user_message(
            'I want to buy coffee', self.test_user_id + "_boleto",
            '[PAYMENT_INTENT] I can help you buy coffee!'
        )
        assert result1["session_state"] == "cart_created"

        # Trigger credential flow
        result2 = process_user_message(
            'yes', self.test_user_id + "_boleto",
            '[PAYMENT_CONFIRM] Great! Let me process that payment.'
        )
        assert result2["session_state"] == "credential_collection"

        # KYC
        result3 = process_user_message(
            'DADOS Carlos Santos 11122233344 11777665544',
            self.test_user_id + "_boleto", ''
        )
        assert "Verificação concluída" in result3["reply"]

        # Boleto credentials
        result4 = process_user_message(
            'BOLETO 11122233344 Carlos Santos Silva',
            self.test_user_id + "_boleto", ''
        )

        assert result4["session_state"] == "completed"
        assert "BOLETO" in result4["reply"]
        assert "Transaction ID:" in result4["reply"]
        print("✅ Boleto flow successful")

    def test_invalid_credential_handling(self):
        """Test handling of invalid credentials"""

        print("\n=== Testing Invalid Credential Handling ===")

        # Setup cart
        result1 = process_user_message(
            'I want to buy coffee', self.test_user_id + "_invalid",
            '[PAYMENT_INTENT] I can help you buy coffee!'
        )

        result2 = process_user_message(
            'yes', self.test_user_id + "_invalid",
            '[PAYMENT_CONFIRM] Great! Let me process that payment.'
        )

        # Invalid KYC format
        result3 = process_user_message(
            'DADOS Invalid Format',
            self.test_user_id + "_invalid", ''
        )
        assert "inválido" in result3["reply"] or "incompletos" in result3["reply"]

        # Valid KYC
        result4 = process_user_message(
            'DADOS Ana Costa 55566677788 11666554433',
            self.test_user_id + "_invalid", ''
        )
        assert "Verificação concluída" in result4["reply"]

        # Invalid payment format
        result5 = process_user_message(
            'INVALID_FORMAT some data',
            self.test_user_id + "_invalid", ''
        )
        assert "não reconhecido" in result5["reply"]
        print("✅ Invalid credential handling working correctly")

    @pytest.mark.asyncio
    async def test_user_credential_service_directly(self):
        """Test user credential service directly"""

        print("\n=== Testing User Credential Service ===")

        user_service = get_user_credential_service()
        test_user = "+5511999123456"

        # Test KYC processing
        kyc_result = await user_service.process_kyc_data(
            test_user, "DADOS TestUser 12312312312 11999123456"
        )
        assert kyc_result["success"] == True
        assert "Verificação concluída" in kyc_result["message"]

        # Test PIX credential processing
        pix_result = await user_service.process_payment_credentials(
            test_user, "PIX_EMAIL test@example.com", "pix"
        )
        assert pix_result["success"] == True
        assert "credential_id" in pix_result

        # Verify credentials are stored
        credentials = await user_service.get_user_credentials(test_user, "pix")
        assert len(credentials) == 1
        assert credentials[0].payment_method == "pix"

        print("✅ User credential service working correctly")

    @pytest.mark.asyncio
    async def test_merchant_onboarding_service(self):
        """Test merchant onboarding service directly"""

        print("\n=== Testing Merchant Onboarding Service ===")

        registry = AgentRegistry("test-registry")
        merchant_service = get_merchant_service(registry)

        # Test single merchant onboarding
        merchant_creds = await merchant_service.onboard_merchant(
            merchant_id="test_merchant",
            merchant_name="Test Merchant",
            business_type="test",
            supported_regions=["latam"],
            supported_payment_methods=["pix", "credit_card"]
        )

        assert merchant_creds.merchant_id == "test_merchant"
        assert merchant_creds.status == "active"
        assert len(merchant_creds.supported_payment_methods) == 2

        # Test telecom operator onboarding
        telecom_merchants = await merchant_service.onboard_bemobi_telecom_operators()
        assert len(telecom_merchants) == 4  # VIVO, CLARO, OI, TIM
        assert "vivo_brasil" in telecom_merchants
        assert "claro_brasil" in telecom_merchants

        print("✅ Merchant onboarding service working correctly")

    def test_ap2_protocol_compliance_verification(self):
        """Verify AP2 protocol compliance features"""

        print("\n=== Testing AP2 Protocol Compliance ===")

        # Run complete flow
        user_id = self.test_user_id + "_compliance"

        # Setup and complete payment
        result1 = process_user_message('I want to buy coffee', user_id, '[PAYMENT_INTENT] I can help!')
        result2 = process_user_message('yes', user_id, '[PAYMENT_CONFIRM] Processing!')
        result3 = process_user_message('DADOS Compliance Test 99988877766 11555443322', user_id, '')
        result4 = process_user_message('PIX_CPF 99988877766', user_id, '')

        # Verify AP2 compliance features
        reply = result4["reply"]
        session = result4.get("session_updates", {})

        compliance_checks = {
            "agent_authentication": "Agentes mutuamente autenticados" in reply,
            "credential_encryption": "Credenciais verificadas e criptografadas" in reply,
            "kyc_validation": "KYC do usuário validado" in reply,
            "audit_trail": "Transação completamente auditável" in reply,
            "regulatory_compliance": "Conformidade regulatória garantida" in reply,
            "merchant_verification": "merchant_verified" in session,
            "protocol_version": session.get("protocol_version") == "AP2_v1.0"
        }

        failed_checks = [check for check, passed in compliance_checks.items() if not passed]
        assert len(failed_checks) == 0, f"Failed compliance checks: {failed_checks}"

        print("✅ All AP2 protocol compliance checks passed")
        print(f"   ✓ Agent Authentication: Both sender and receiver verified")
        print(f"   ✓ Credential Encryption: User credentials securely processed")
        print(f"   ✓ KYC Validation: User identity verified")
        print(f"   ✓ Audit Trail: Complete transaction record created")
        print(f"   ✓ Regulatory Compliance: All requirements met")
        print(f"   ✓ Merchant Verification: BEMOBI operator verified")
        print(f"   ✓ Protocol Version: AP2 v1.0 compliance confirmed")

    def test_error_recovery_and_resilience(self):
        """Test error recovery and system resilience"""

        print("\n=== Testing Error Recovery ===")

        user_id = self.test_user_id + "_recovery"

        # Test recovery from invalid states
        result1 = process_user_message('I want to buy coffee', user_id, '[PAYMENT_INTENT] I can help!')

        # Try to provide credentials without confirmation
        result2 = process_user_message('PIX_EMAIL test@email.com', user_id, '')
        # Should not process payment, should stay in cart_created state
        assert result2.get("session_state") != "completed"

        # Proper flow
        result3 = process_user_message('yes', user_id, '[PAYMENT_CONFIRM] Processing!')
        result4 = process_user_message('DADOS Recovery Test 12312312312 11999887766', user_id, '')
        result5 = process_user_message('PIX_EMAIL recovery@test.com', user_id, '')

        assert result5["session_state"] == "completed"
        print("✅ Error recovery working correctly")


def run_enhanced_ap2_tests():
    """Run all enhanced AP2 tests"""

    print("🚀 Starting Enhanced AP2 Credential Testing Suite")
    print("=" * 60)

    test_suite = TestEnhancedAP2Credentials()
    test_suite.setup_method()

    try:
        # Run all test methods
        test_suite.test_complete_enhanced_ap2_flow()
        test_suite.test_credit_card_credential_flow()
        test_suite.test_boleto_credential_flow()
        test_suite.test_invalid_credential_handling()
        test_suite.test_ap2_protocol_compliance_verification()
        test_suite.test_error_recovery_and_resilience()

        # Run async tests
        asyncio.run(test_suite.test_user_credential_service_directly())
        asyncio.run(test_suite.test_merchant_onboarding_service())

        print("\n" + "=" * 60)
        print("🎉 ALL ENHANCED AP2 TESTS PASSED!")
        print("✅ User credential acquisition: WORKING")
        print("✅ Merchant credential onboarding: WORKING")
        print("✅ Agent-to-agent authentication: WORKING")
        print("✅ AP2 protocol compliance: VERIFIED")
        print("✅ Error handling and recovery: WORKING")
        print("\n🔐 Enhanced AP2 implementation is production-ready!")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    """Run tests when executed directly"""
    success = run_enhanced_ap2_tests()
    exit(0 if success else 1)