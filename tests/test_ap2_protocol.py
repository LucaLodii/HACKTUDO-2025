"""
Test suite for AP2 Protocol implementation

Tests the core AP2 protocol components including mandates, 
cryptographic signing, and payment flows.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from sofIA.tools.ap2_protocol.ap2_core import (
    AP2PaymentAgent,
    MandateSigner,
    WhatsAppPaymentFlow,
    VerifiableCredential
)
from sofIA.tools.ap2_protocol.types.mandate import IntentMandate, CartMandate
from sofIA.tools.ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount


class TestMandateSigner:
    """Test cryptographic signing and verification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.signer = MandateSigner()
    
    def test_generate_keys(self):
        """Test RSA key generation."""
        assert self.signer.private_key is not None
        assert self.signer.public_key is not None
    
    def test_cart_hash_computation(self):
        """Test cart contents hashing."""
        from sofIA.tools.ap2_protocol.types.mandate import CartContents
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentRequest
        
        # Create sample cart contents
        payment_request = PaymentRequest(
            method_data=[{"supported_methods": "basic-card", "data": {}}],
            details={
                "id": "test-cart-123",
                "display_items": [
                    {
                        "label": "Test Item",
                        "amount": {"currency": "USD", "value": 10.00}
                    }
                ],
                "total": {
                    "label": "Total",
                    "amount": {"currency": "USD", "value": 10.00}
                }
            }
        )
        
        cart_contents = CartContents(
            id="test-cart-123",
            user_cart_confirmation_required=True,
            payment_request=payment_request,
            cart_expiry=(datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
            merchant_name="Test Merchant",
            user_id="test-user-123"
        )
        
        hash1 = self.signer._compute_cart_hash(cart_contents)
        hash2 = self.signer._compute_cart_hash(cart_contents)
        
        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_cart_signing_and_verification(self):
        """Test cart mandate signing and verification."""
        from sofIA.tools.ap2_protocol.types.mandate import CartContents
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentRequest
        
        # Create sample cart contents
        payment_request = PaymentRequest(
            method_data=[{"supported_methods": "basic-card", "data": {}}],
            details={
                "id": "test-cart-123",
                "display_items": [
                    {
                        "label": "Test Item",
                        "amount": {"currency": "USD", "value": 10.00}
                    }
                ],
                "total": {
                    "label": "Total",
                    "amount": {"currency": "USD", "value": 10.00}
                }
            }
        )
        
        cart_contents = CartContents(
            id="test-cart-123",
            user_cart_confirmation_required=True,
            payment_request=payment_request,
            cart_expiry=(datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
            merchant_name="Test Merchant",
            user_id="test-user-123"
        )
        
        # Sign cart contents
        signature = self.signer.sign_cart_contents(cart_contents, "test-merchant")
        assert signature is not None
        
        # Create cart mandate
        cart_mandate = CartMandate(
            contents=cart_contents,
            merchant_authorization=signature
        )
        
        # Verify signature
        is_valid = self.signer.verify_cart_signature(cart_mandate, self.signer.public_key)
        assert is_valid is True


class TestAP2PaymentAgent:
    """Test AP2 payment agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = AP2PaymentAgent(
            agent_id="test-agent",
            merchant_id="test-merchant"
        )
    
    def test_create_intent_mandate(self):
        """Test intent mandate creation."""
        intent_mandate = self.agent.create_intent_mandate(
            user_message="I want to buy running shoes",
            user_id="user123"
        )
        
        assert intent_mandate.natural_language_description == "I want to buy running shoes"
        assert intent_mandate.user_cart_confirmation_required is True
        assert intent_mandate.intent_expiry is not None
        
        # Check that intent was stored
        assert len(self.agent.active_intents) == 1
    
    def test_create_cart_mandate(self):
        """Test cart mandate creation."""
        # First create an intent mandate
        intent_mandate = self.agent.create_intent_mandate(
            user_message="I want to buy running shoes",
            user_id="user123"
        )
        intent_id = list(self.agent.active_intents.keys())[0]
        
        # Create payment items
        items = [
            PaymentItem(
                label="Nike Running Shoes",
                amount=PaymentCurrencyAmount(currency="USD", value=129.99)
            )
        ]
        
        # Create cart mandate
        cart_mandate = self.agent.create_cart_mandate(intent_id, items)
        
        assert cart_mandate.contents.id is not None
        assert cart_mandate.contents.merchant_name == "sofIA Payment Agent"
        assert cart_mandate.merchant_authorization is not None
        
        # Verify total amount
        total_amount = cart_mandate.contents.payment_request.details.total.amount.value
        assert total_amount == 129.99
    
    def test_create_payment_mandate(self):
        """Test payment mandate creation."""
        # Create intent and cart mandates first
        intent_mandate = self.agent.create_intent_mandate(
            user_message="I want to buy running shoes",
            user_id="user123"
        )
        intent_id = list(self.agent.active_intents.keys())[0]
        
        items = [
            PaymentItem(
                label="Nike Running Shoes",
                amount=PaymentCurrencyAmount(currency="USD", value=129.99)
            )
        ]
        
        cart_mandate = self.agent.create_cart_mandate(intent_id, items)
        cart_id = cart_mandate.contents.id
        
        # Create payment response
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse
        payment_response = PaymentResponse(
            request_id=cart_id,
            method_name="basic-card",
            details={"card_number": "****1234"}
        )
        
        # Create payment mandate
        payment_mandate = self.agent.create_payment_mandate(
            cart_id, payment_response, "user123"
        )
        
        assert payment_mandate.payment_mandate_contents.payment_mandate_id is not None
        assert payment_mandate.payment_mandate_contents.merchant_agent == "test-agent"
        assert payment_mandate.user_authorization is not None
    
    def test_process_whatsapp_message(self):
        """Test WhatsApp message processing."""
        # Test purchase intent detection
        response = self.agent.process_whatsapp_message(
            "I want to buy a laptop", "user123"
        )
        
        assert response["type"] == "intent_created"
        assert "laptop" in response["message"]
        assert response["requires_confirmation"] is True
        
        # Test confirmation response
        response = self.agent.process_whatsapp_message("confirm", "user123")
        assert response["type"] == "confirmation_received"
        
        # Test general response
        response = self.agent.process_whatsapp_message("Hello", "user123")
        assert response["type"] == "general_response"


class TestWhatsAppPaymentFlow:
    """Test WhatsApp payment flow management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = AP2PaymentAgent(
            agent_id="test-agent",
            merchant_id="test-merchant"
        )
        self.flow = WhatsAppPaymentFlow(self.agent)
    
    def test_handle_webhook_idle_state(self):
        """Test webhook handling in idle state."""
        webhook_data = {
            "from": "user123",
            "text": {"body": "I want to buy shoes"}
        }
        
        response = self.flow.handle_webhook(webhook_data)
        
        assert response["type"] == "intent_created"
        assert "user123" in self.flow.user_sessions
        assert self.flow.user_sessions["user123"]["state"] == "shopping"
    
    def test_handle_webhook_shopping_state(self):
        """Test webhook handling in shopping state."""
        # First create a shopping session
        webhook_data = {
            "from": "user123",
            "text": {"body": "I want to buy shoes"}
        }
        self.flow.handle_webhook(webhook_data)
        
        # Now simulate finding items
        webhook_data = {
            "from": "user123",
            "text": {"body": "found items"}
        }
        
        response = self.flow.handle_webhook(webhook_data)
        
        assert response["type"] == "cart_ready"
        assert self.flow.user_sessions["user123"]["state"] == "cart_ready"
        assert "cart_id" in response
    
    def test_handle_webhook_cart_ready_state(self):
        """Test webhook handling in cart ready state."""
        # First create a real cart through the normal flow
        webhook_data = {
            "from": "user123",
            "text": {"body": "I want to buy shoes"}
        }
        self.flow.handle_webhook(webhook_data)
        
        # Simulate finding items
        webhook_data = {
            "from": "user123",
            "text": {"body": "found items"}
        }
        self.flow.handle_webhook(webhook_data)
        
        # Now confirm payment
        webhook_data = {
            "from": "user123",
            "text": {"body": "confirm"}
        }
        
        response = self.flow.handle_webhook(webhook_data)
        
        assert response["type"] == "payment_complete"
        assert self.flow.user_sessions["user123"]["state"] == "payment_complete"
        assert "payment_mandate_id" in response


class TestAP2ProtocolCompliance:
    """Test AP2 protocol compliance and security."""
    
    def test_mandate_expiry_handling(self):
        """Test mandate expiry handling."""
        agent = AP2PaymentAgent("test-agent", "test-merchant")
        
        # Create intent mandate
        intent_mandate = agent.create_intent_mandate(
            "Buy shoes", "user123"
        )
        
        # Check expiry is set correctly
        expiry = datetime.fromisoformat(intent_mandate.intent_expiry.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Should expire in 24 hours
        assert (expiry - now).total_seconds() > 23 * 3600
        assert (expiry - now).total_seconds() < 25 * 3600
    
    def test_cart_expiry_handling(self):
        """Test cart expiry handling."""
        agent = AP2PaymentAgent("test-agent", "test-merchant")
        
        # Create intent and cart
        intent_mandate = agent.create_intent_mandate("Buy shoes", "user123")
        intent_id = list(agent.active_intents.keys())[0]
        
        items = [
            PaymentItem(
                label="Test Item",
                amount=PaymentCurrencyAmount(currency="USD", value=10.00)
            )
        ]
        
        cart_mandate = agent.create_cart_mandate(intent_id, items)
        
        # Check cart expiry is set correctly
        expiry = datetime.fromisoformat(cart_mandate.contents.cart_expiry.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Should expire in 15 minutes
        assert (expiry - now).total_seconds() > 14 * 60
        assert (expiry - now).total_seconds() < 16 * 60
    
    def test_cryptographic_security(self):
        """Test cryptographic security measures."""
        signer = MandateSigner()
        
        # Test that different inputs produce different hashes
        from sofIA.tools.ap2_protocol.types.mandate import CartContents
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentRequest
        
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentDetails
        
        payment_details1 = PaymentDetails(
            id="cart1",
            display_items=[PaymentItem(label="Item 1", amount=PaymentCurrencyAmount(currency="USD", value=10.0))],
            total=PaymentItem(label="Total", amount=PaymentCurrencyAmount(currency="USD", value=10.0))
        )
        
        cart1 = CartContents(
            id="cart1",
            user_cart_confirmation_required=True,
            payment_request=PaymentRequest(
                method_data=[{"supported_methods": "basic-card", "data": {}}],
                details=payment_details1
            ),
            cart_expiry=datetime.now(timezone.utc).isoformat(),
            merchant_name="Merchant 1",
            user_id="test-user-123"
        )
        
        payment_details2 = PaymentDetails(
            id="cart2",
            display_items=[PaymentItem(label="Item 2", amount=PaymentCurrencyAmount(currency="USD", value=20.0))],
            total=PaymentItem(label="Total", amount=PaymentCurrencyAmount(currency="USD", value=20.0))
        )
        
        cart2 = CartContents(
            id="cart2",
            user_cart_confirmation_required=True,
            payment_request=PaymentRequest(
                method_data=[{"supported_methods": "basic-card", "data": {}}],
                details=payment_details2
            ),
            cart_expiry=datetime.now(timezone.utc).isoformat(),
            merchant_name="Merchant 2",
            user_id="test-user-456"
        )
        
        hash1 = signer._compute_cart_hash(cart1)
        hash2 = signer._compute_cart_hash(cart2)
        
        assert hash1 != hash2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
