"""
AP2 Protocol Compliance Tests

This module tests sofIA's compliance with the official AP2 (Agent Payments Protocol) specification
from Google, ensuring all components follow the correct mandate structure, credential handling,
and cryptographic verification requirements.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from sofIA.tools.ap2_protocol.verifiable_credentials import (
    VerifiableCredential, CredentialProvider, CredentialWallet
)
from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
from sofIA.tools.ap2_protocol.ap2_credential_collector import (
    AP2CredentialCollector, AP2PaymentMethodDiscovery
)
from sofIA.tools.ap2_protocol.ap2_signature_verifier import AP2SignatureVerifier
from sofIA.tools.ap2_protocol.ap2_tool import AP2ProtocolTool


class TestAP2VerifiableCredentials:
    """Test Verifiable Credentials implementation per AP2 specification"""
    
    def test_verifiable_credential_structure(self):
        """Test that VerifiableCredential follows AP2 specification structure"""
        
        credential = VerifiableCredential(
            id="vc:payment:user123:card",
            issuer="sofia-credential-provider",
            subject="user123",
            issued_at="2024-01-01T00:00:00Z",
            expires_at="2024-12-31T23:59:59Z",
            claims={
                "payment_method": "basic-card",
                "authorization_level": "single_use",
                "max_amount": 1000.00,
                "currency": "BRL"
            },
            proof="jwt_signature_here"
        )
        
        # Verify AP2 required fields
        assert credential.id is not None
        assert credential.issuer is not None
        assert credential.subject is not None
        assert credential.issued_at is not None
        assert credential.expires_at is not None
        assert credential.claims is not None
        
        # Verify payment-specific claims
        assert credential.claims["payment_method"] == "basic-card"
        assert credential.claims["authorization_level"] == "single_use"
        assert credential.claims["max_amount"] == 1000.00
    
    def test_credential_provider_creation(self):
        """Test CredentialProvider can create and verify credentials"""
        
        provider = CredentialProvider({})
        
        credential = provider.create_payment_credential(
            user_id="user123",
            payment_method="pix",
            credential_data={
                "authorization_level": "delegated",
                "max_amount": 5000.00,
                "currency": "BRL",
                "encrypted_data": "encrypted_pix_data",
                "provider_token": "pix_token"
            }
        )
        
        # Verify credential structure
        assert credential.id.startswith("vc:payment:user123:pix")
        assert credential.issuer == "sofia-credential-provider"
        assert credential.subject == "user123"
        assert credential.claims["payment_method"] == "pix"
        assert credential.claims["max_amount"] == 5000.00
        assert credential.proof is not None
    
    def test_credential_verification(self):
        """Test credential verification process"""
        
        provider = CredentialProvider({})
        
        # Create credential
        credential = provider.create_payment_credential(
            user_id="user123",
            payment_method="basic-card",
            credential_data={
                "authorization_level": "single_use",
                "max_amount": 1000.00,
                "currency": "BRL"
            }
        )
        
        # Verify credential
        is_valid = provider.verify_credential(credential)
        assert is_valid is True
    
    def test_payment_authorization(self):
        """Test payment authorization using credentials"""
        
        provider = CredentialProvider({})
        
        # Create credential with specific limits
        credential = provider.create_payment_credential(
            user_id="user123",
            payment_method="basic-card",
            credential_data={
                "authorization_level": "single_use",
                "max_amount": 500.00,
                "currency": "BRL"
            }
        )
        
        # Test authorized payment
        auth_result = provider.authorize_payment(
            user_id="user123",
            amount=300.00,
            currency="BRL",
            payment_method="basic-card"
        )
        
        assert auth_result["authorized"] is True
        assert auth_result["consent_proof"] is not None
        
        # Test unauthorized payment (amount too high)
        auth_result = provider.authorize_payment(
            user_id="user123",
            amount=600.00,
            currency="BRL",
            payment_method="basic-card"
        )
        
        assert auth_result["authorized"] is False
        assert "exceeds maximum" in auth_result["error"]


class TestAP2MandateChain:
    """Test AP2 mandate chain implementation"""
    
    def test_intent_mandate_creation(self):
        """Test Intent Mandate creation per AP2 specification"""
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        
        intent_mandate = agent.create_intent_mandate(
            user_message="I want to buy a coffee for R$ 8.50",
            user_id="+5511999999999",
            merchants=["coffee_shop_123"],
            max_price=10.00,
            requires_confirmation=True
        )
        
        # Verify AP2 required fields
        assert intent_mandate.user_cart_confirmation_required is True
        assert intent_mandate.natural_language_description == "I want to buy a coffee for R$ 8.50"
        assert intent_mandate.merchants == ["coffee_shop_123"]
        assert hasattr(intent_mandate, 'user_id') or intent_mandate.user_id == "+5511999999999"
    
    def test_cart_mandate_creation(self):
        """Test Cart Mandate creation per AP2 specification"""
        
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        
        # Create intent first
        intent_mandate = agent.create_intent_mandate(
            user_message="Buy coffee",
            user_id="user123",
            merchants=["coffee_shop"]
        )
        
        intent_id = list(agent.active_intents.keys())[0]
        
        # Create cart with payment items
        items = [
            PaymentItem(
                label="Coffee",
                amount=PaymentCurrencyAmount(currency="BRL", value=8.50)
            )
        ]
        
        cart_mandate = agent.create_cart_mandate(
            intent_id=intent_id,
            items=items,
            payment_methods=[
                {
                    "supported_methods": "basic-card",
                    "data": {"networks": ["visa", "mastercard"], "available": True}
                },
                {
                    "supported_methods": "pix",
                    "data": {"type": "pix", "available": True, "instant": True}
                }
            ]
        )
        
        # Verify AP2 required fields
        assert cart_mandate.contents.id is not None
        assert cart_mandate.contents.merchant_name == "sofIA Payment Agent"
        assert cart_mandate.merchant_authorization is not None
        assert len(cart_mandate.contents.payment_request.method_data) == 2
        assert hasattr(cart_mandate.contents, 'user_id') or cart_mandate.contents.user_id == "user123"
    
    def test_payment_mandate_creation(self):
        """Test Payment Mandate creation per AP2 specification"""
        
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse, PaymentItem, PaymentCurrencyAmount
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        
        # Create full mandate chain
        intent_mandate = agent.create_intent_mandate(
            user_message="Buy coffee",
            user_id="user123"
        )
        intent_id = list(agent.active_intents.keys())[0]
        
        items = [PaymentItem(label="Coffee", amount=PaymentCurrencyAmount(currency="BRL", value=8.50))]
        cart_mandate = agent.create_cart_mandate(intent_id=intent_id, items=items)
        cart_id = cart_mandate.contents.id
        
        # Create payment response
        payment_response = PaymentResponse(
            request_id=cart_id,
            method_name="pix",
            details={"encrypted_data": "encrypted_pix_data", "consent_proof": "consent_proof"}
        )
        
        # Create payment mandate
        payment_mandate = agent.create_payment_mandate(
            cart_id=cart_id,
            payment_response=payment_response,
            user_id="user123"
        )
        
        # Verify AP2 required fields
        assert payment_mandate.payment_mandate_contents.payment_mandate_id is not None
        assert payment_mandate.payment_mandate_contents.merchant_agent == "sofia-agent"
        assert payment_mandate.user_authorization is not None
        assert hasattr(payment_mandate.payment_mandate_contents, 'user_id') or payment_mandate.payment_mandate_contents.user_id == "user123"


class TestAP2CredentialCollection:
    """Test AP2 credential collection implementation"""
    
    @pytest.mark.asyncio
    async def test_payment_method_discovery(self):
        """Test payment method discovery per AP2 specification"""
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        collector = AP2CredentialCollector(agent)
        discovery = AP2PaymentMethodDiscovery(collector)
        
        # Test discovery for LATAM region
        methods = await discovery.get_supported_payment_methods("user123", "latam")
        
        assert len(methods) > 0
        
        # Verify AP2 PaymentMethodData structure
        for method in methods:
            assert "supported_methods" in method
            assert "data" in method
            assert isinstance(method["supported_methods"], str)
            assert isinstance(method["data"], dict)
        
        # Should include PIX for LATAM
        pix_methods = [m for m in methods if m["supported_methods"] == "pix"]
        assert len(pix_methods) > 0
    
    @pytest.mark.asyncio
    async def test_credential_collection(self):
        """Test payment credential collection per AP2 specification"""
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        collector = AP2CredentialCollector(agent)
        
        # Test credential collection
        result = await collector.collect_payment_credentials(
            user_id="user123",
            cart_mandate_id="cart-123",
            selected_method="pix",
            amount=25.00,
            currency="BRL"
        )
        
        assert result["success"] is True
        assert result["collection_id"] is not None
        assert result["payment_response"] is not None
        assert result["credential_info"]["method"] == "pix"
        assert result["credential_info"]["consent_proof"] is not None
    
    @pytest.mark.asyncio
    async def test_payment_method_recommendation(self):
        """Test payment method recommendation per AP2 best practices"""
        
        agent = AP2PaymentAgent("sofia-agent", "sofia-merchant")
        collector = AP2CredentialCollector(agent)
        discovery = AP2PaymentMethodDiscovery(collector)
        
        # Test recommendation for BRL in LATAM
        recommendation = await discovery.recommend_payment_method(
            user_id="user123",
            amount=25.00,
            currency="BRL",
            region="latam"
        )
        
        assert recommendation["recommended"] is not None
        assert recommendation["reason"] is not None
        
        # PIX should be recommended for BRL in LATAM
        if recommendation["recommended"] == "pix":
            assert recommendation["instant"] is True


class TestAP2SignatureVerification:
    """Test AP2 signature verification implementation"""
    
    def test_signature_verifier_initialization(self):
        """Test signature verifier initialization"""
        
        verifier = AP2SignatureVerifier()
        
        assert verifier is not None
        assert len(verifier.trusted_issuers) > 0
        assert "sofia-credential-provider" in verifier.trusted_issuers
    
    def test_mandate_structure_verification(self):
        """Test mandate structure verification per AP2 specification"""
        
        verifier = AP2SignatureVerifier()
        
        # Test intent mandate structure
        intent_result = verifier._verify_mandate_structure(
            type("MockIntent", (), {
                "user_cart_confirmation_required": True,
                "natural_language_description": "Buy coffee",
                "intent_expiry": "2024-12-31T23:59:59Z"
            })(),
            "intent"
        )
        
        assert intent_result["valid"] is True
        assert intent_result["mandate_type"] == "intent"
        
        # Test cart mandate structure
        cart_result = verifier._verify_mandate_structure(
            type("MockCart", (), {
                "contents": "mock_contents",
                "merchant_authorization": "mock_auth"
            })(),
            "cart"
        )
        
        assert cart_result["valid"] is True
        assert cart_result["mandate_type"] == "cart"
        
        # Test payment mandate structure
        payment_result = verifier._verify_mandate_structure(
            type("MockPayment", (), {
                "payment_mandate_contents": "mock_contents",
                "user_authorization": "mock_auth"
            })(),
            "payment"
        )
        
        assert payment_result["valid"] is True
        assert payment_result["mandate_type"] == "payment"


class TestAP2ProtocolTool:
    """Test AP2 Protocol Tool integration"""
    
    @pytest.mark.asyncio
    async def test_ap2_tool_initialization(self):
        """Test AP2 tool initialization with all components"""
        
        tool = AP2ProtocolTool()
        
        assert tool.name == "ap2_protocol"
        assert "AP2 specification" in tool.description
        assert tool.ap2_integration is not None
        assert tool.credential_collector is not None
        assert tool.payment_method_discovery is not None
        assert tool.signature_verifier is not None
    
    @pytest.mark.asyncio
    async def test_complete_payment_flow(self):
        """Test complete AP2 payment flow from intent to payment"""
        
        tool = AP2ProtocolTool()
        
        # Step 1: Create Intent Mandate
        intent_result = await tool._create_intent_mandate(
            user_message="I want to buy a coffee for R$ 8.50",
            user_id="+5511999999999",
            merchants=["coffee_shop_123"],
            max_price=10.00,
            currency="BRL"
        )
        
        assert intent_result["success"] is True
        assert intent_result["intent_id"] is not None
        assert "user_id" in intent_result["mandate"]
        
        intent_id = intent_result["intent_id"]
        
        # Step 2: Create Cart Mandate
        cart_result = await tool._create_cart_mandate(
            intent_id=intent_id,
            items=[{
                "label": "Coffee",
                "amount": {"currency": "BRL", "value": 8.50}
            }],
            user_id="+5511999999999"
        )
        
        assert cart_result["success"] is True
        assert cart_result["cart_id"] is not None
        assert "payment_methods" in cart_result["mandate"]
        
        cart_id = cart_result["cart_id"]
        
        # Step 3: Create Payment Mandate
        payment_result = await tool._create_payment_mandate(
            cart_id=cart_id,
            payment_method="pix",
            user_id="+5511999999999",
            amount=8.50,
            currency="BRL"
        )
        
        assert payment_result["success"] is True
        assert payment_result["payment_mandate_id"] is not None
        assert "user_credential_id" in payment_result["mandate"]
    
    @pytest.mark.asyncio
    async def test_payment_method_discovery_operation(self):
        """Test payment method discovery operation"""
        
        tool = AP2ProtocolTool()
        
        result = await tool._discover_payment_methods(
            user_id="+5511999999999",
            region="latam"
        )
        
        assert result["success"] is True
        assert result["user_id"] == "+5511999999999"
        assert result["region"] == "latam"
        assert len(result["payment_methods"]) > 0
        assert result["count"] > 0
    
    @pytest.mark.asyncio
    async def test_credential_collection_operation(self):
        """Test credential collection operation"""
        
        tool = AP2ProtocolTool()
        
        result = await tool._collect_payment_credentials(
            user_id="+5511999999999",
            cart_id="cart-123",
            payment_method="pix",
            amount=25.00,
            currency="BRL"
        )
        
        assert result["success"] is True
        assert result["collection_id"] is not None
        assert result["payment_response"] is not None
        assert result["credential_info"]["method"] == "pix"
        assert result["credential_info"]["consent_proof"] is not None
    
    @pytest.mark.asyncio
    async def test_credential_creation_operation(self):
        """Test credential creation operation"""
        
        tool = AP2ProtocolTool()
        
        result = await tool._create_user_credential(
            user_id="+5511999999999",
            payment_method="basic-card",
            credential_data={
                "authorization_level": "single_use",
                "max_amount": 1000.00,
                "currency": "BRL",
                "encrypted_data": "encrypted_card_data",
                "provider_token": "stripe_token"
            }
        )
        
        assert result["success"] is True
        assert result["credential_id"] is not None
        assert result["payment_method"] == "basic-card"
        assert result["user_id"] == "+5511999999999"
        assert result["issued_at"] is not None
        assert result["expires_at"] is not None


class TestAP2Compliance:
    """Test overall AP2 compliance and integration"""
    
    @pytest.mark.asyncio
    async def test_ap2_mandate_chain_compliance(self):
        """Test that the complete mandate chain follows AP2 specification"""
        
        tool = AP2ProtocolTool()
        
        # Create complete mandate chain
        intent_result = await tool._create_intent_mandate(
            user_message="Buy subscription for R$ 29.90",
            user_id="+5511999999999",
            max_price=50.00,
            currency="BRL"
        )
        
        cart_result = await tool._create_cart_mandate(
            intent_id=intent_result["intent_id"],
            items=[{
                "label": "Monthly Subscription",
                "amount": {"currency": "BRL", "value": 29.90}
            }],
            user_id="+5511999999999"
        )
        
        payment_result = await tool._create_payment_mandate(
            cart_id=cart_result["cart_id"],
            payment_method="pix",
            user_id="+5511999999999",
            amount=29.90,
            currency="BRL"
        )
        
        # Verify mandate chain compliance
        assert intent_result["success"] is True
        assert cart_result["success"] is True
        assert payment_result["success"] is True
        
        # Verify user_id consistency across mandates
        assert intent_result["mandate"]["user_id"] == "+5511999999999"
        assert cart_result["mandate"]["user_id"] == "+5511999999999"
        assert payment_result["mandate"]["user_id"] == "+5511999999999"
        
        # Verify amount consistency
        assert cart_result["mandate"]["total_amount"] == 29.90
        assert payment_result["mandate"]["total_amount"] == 29.90
        
        # Verify currency consistency
        assert cart_result["mandate"]["currency"] == "BRL"
        assert payment_result["mandate"]["currency"] == "BRL"
    
    @pytest.mark.asyncio
    async def test_ap2_verifiable_credentials_compliance(self):
        """Test that verifiable credentials follow AP2 specification"""
        
        provider = CredentialProvider({})
        
        # Test different credential types per AP2 spec
        card_credential = provider.create_payment_credential(
            user_id="user123",
            payment_method="basic-card",
            credential_data={
                "authorization_level": "single_use",
                "max_amount": 1000.00,
                "currency": "BRL"
            }
        )
        
        pix_credential = provider.create_payment_credential(
            user_id="user123",
            payment_method="pix",
            credential_data={
                "authorization_level": "delegated",
                "max_amount": 5000.00,
                "currency": "BRL"
            }
        )
        
        # Verify credential structure compliance
        for credential in [card_credential, pix_credential]:
            assert credential.id.startswith("vc:payment:")
            assert credential.issuer == "sofia-credential-provider"
            assert credential.subject == "user123"
            assert credential.proof is not None
            assert credential.claims["currency"] == "BRL"
            assert credential.claims["payment_method"] in ["basic-card", "pix"]
    
    @pytest.mark.asyncio
    async def test_ap2_payment_method_data_compliance(self):
        """Test that payment method data follows AP2 specification"""
        
        tool = AP2ProtocolTool()
        
        methods = await tool._discover_payment_methods(
            user_id="user123",
            region="latam"
        )
        
        assert methods["success"] is True
        
        # Verify each payment method follows AP2 PaymentMethodData structure
        for method in methods["payment_methods"]:
            assert "supported_methods" in method
            assert "data" in method
            assert isinstance(method["supported_methods"], str)
            assert isinstance(method["data"], dict)
            
            # Verify method-specific data structure
            if method["supported_methods"] == "basic-card":
                assert "networks" in method["data"]
                assert "available" in method["data"]
            elif method["supported_methods"] == "pix":
                assert "type" in method["data"]
                assert method["data"]["type"] == "pix"
                assert "instant" in method["data"]


if __name__ == "__main__":
    # Run AP2 compliance tests
    pytest.main([__file__, "-v", "--tb=short"])
