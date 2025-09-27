"""
AP2 Protocol Core Implementation for WhatsApp Payment Agent

This module implements the core components of the Agent Payments Protocol (AP2)
including Mandates, Verifiable Credentials, and cryptographic signing.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import jwt
from pydantic import BaseModel, Field

# AP2 Protocol types - using local implementations for hackathon
# from ap2.types.mandate import (
#     IntentMandate,
#     CartMandate,
#     CartContents,
#     PaymentMandate,
#     PaymentMandateContents,
# )
# AP2 Protocol types - using local implementations for hackathon
# from ap2.types.payment_request import (
#     PaymentRequest,
#     PaymentResponse,
#     PaymentItem,
#     PaymentCurrencyAmount,
# )

# Local AP2 Protocol type definitions for hackathon
class PaymentItem(BaseModel):
    """Represents a payment item in a cart."""
    name: str
    description: str = ""
    price: float
    currency: str = "BRL"
    quantity: int = 1

class PaymentCurrencyAmount(BaseModel):
    """Represents a currency amount."""
    amount: float
    currency: str = "BRL"

class PaymentRequest(BaseModel):
    """Represents a payment request."""
    items: list[PaymentItem]
    total_amount: PaymentCurrencyAmount
    merchant_name: str
    merchant_id: str

class PaymentResponse(BaseModel):
    """Represents a payment response."""
    transaction_id: str
    status: str
    amount: PaymentCurrencyAmount
    timestamp: str

class CartContents(BaseModel):
    """Represents the contents of a cart."""
    items: list[PaymentItem]
    total_amount: PaymentCurrencyAmount
    merchant_name: str

class IntentMandate(BaseModel):
    """Represents an intent mandate."""
    mandate_id: str
    user_id: str
    natural_language_description: str
    intent_expiry: str
    user_cart_confirmation_required: bool = True
    created_at: str

class CartMandate(BaseModel):
    """Represents a cart mandate."""
    mandate_id: str
    payment_request: PaymentRequest
    merchant_name: str
    cart_expiry: str
    merchant_authorization: str
    created_at: str

class PaymentMandateContents(BaseModel):
    """Represents payment mandate contents."""
    payment_mandate_id: str
    merchant_agent: str
    payment_response: PaymentResponse

class PaymentMandate(BaseModel):
    """Represents a payment mandate."""
    mandate_id: str
    user_id: str
    payment_mandate_contents: PaymentMandateContents
    user_authorization: str
    created_at: str

class VerifiableCredential(BaseModel):
    """Represents a verifiable credential for user authorization."""
    
    id: str = Field(..., description="Unique identifier for the credential")
    issuer: str = Field(..., description="Issuer of the credential")
    subject: str = Field(..., description="Subject (user) of the credential")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    expires_at: str = Field(..., description="ISO 8601 timestamp of expiration")
    claims: Dict[str, Any] = Field(..., description="Credential claims")
    proof: Optional[str] = Field(None, description="Cryptographic proof")


class MandateSigner:
    """Handles cryptographic signing and verification of AP2 mandates."""
    
    def __init__(self, private_key_path: Optional[str] = None, public_key_path: Optional[str] = None):
        """Initialize the mandate signer with RSA keys."""
        if private_key_path and public_key_path:
            self._load_keys(private_key_path, public_key_path)
        else:
            self._generate_keys()
    
    def _generate_keys(self):
        """Generate RSA key pair for signing."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def _load_keys(self, private_key_path: str, public_key_path: str):
        """Load RSA keys from files."""
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        
        with open(public_key_path, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
    
    def sign_cart_contents(self, cart_contents: CartContents, merchant_id: str) -> str:
        """Sign cart contents to create a CartMandate."""
        # Create JWT payload
        payload = {
            "iss": merchant_id,
            "sub": merchant_id,
            "aud": "payment-processor",
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": datetime.now(timezone.utc).timestamp() + 900,  # 15 minutes
            "jti": f"cart-{datetime.now(timezone.utc).timestamp()}",
            "cart_hash": self._compute_cart_hash(cart_contents)
        }
        
        # Sign JWT
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        return token
    
    def verify_cart_signature(self, cart_mandate: CartMandate, public_key) -> bool:
        """Verify the signature of a CartMandate."""
        try:
            payload = jwt.decode(
                cart_mandate.merchant_authorization,
                public_key,
                algorithms=["RS256"],
                audience="payment-processor"
            )
            # Verify cart hash
            computed_hash = self._compute_cart_hash(cart_mandate.contents)
            return payload["cart_hash"] == computed_hash
        except jwt.InvalidTokenError:
            return False
    
    def _compute_cart_hash(self, cart_contents: CartContents) -> str:
        """Compute secure hash of cart contents."""
        # Convert to canonical JSON
        data = cart_contents.model_dump()
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(json_str.encode())
        return hash_obj.hexdigest()
    
    def create_user_authorization(self, cart_hash: str, payment_hash: str, user_id: str) -> str:
        """Create user authorization for payment mandate."""
        # Create verifiable presentation
        payload = {
            "aud": "payment-processor",
            "nonce": f"nonce-{datetime.now(timezone.utc).timestamp()}",
            "sd_hash": "issuer-signed-jwt-hash",  # This would be computed from actual issuer JWT
            "transaction_data": [cart_hash, payment_hash],
            "user_id": user_id,
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": datetime.now(timezone.utc).timestamp() + 3600  # 1 hour
        }
        
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        return token


class AP2PaymentAgent:
    """Main payment agent implementing AP2 protocol for WhatsApp integration."""
    
    def __init__(self, agent_id: str, merchant_id: str):
        self.agent_id = agent_id
        self.merchant_id = merchant_id
        self.signer = MandateSigner()
        self.active_intents: Dict[str, IntentMandate] = {}
        self.active_carts: Dict[str, CartMandate] = {}
    
    def create_intent_mandate(
        self,
        user_message: str,
        user_id: str,
        merchants: Optional[List[str]] = None,
        max_price: Optional[float] = None,
        requires_confirmation: bool = True
    ) -> IntentMandate:
        """Create an Intent Mandate from user's WhatsApp message."""
        
        intent_id = f"intent-{user_id}-{datetime.now(timezone.utc).timestamp()}"
        expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        
        intent_mandate = IntentMandate(
            user_cart_confirmation_required=requires_confirmation,
            natural_language_description=user_message,
            merchants=merchants,
            intent_expiry=expiry.isoformat()
        )
        
        self.active_intents[intent_id] = intent_mandate
        return intent_mandate
    
    def create_cart_mandate(
        self,
        intent_id: str,
        items: List[PaymentItem],
        shipping_address: Optional[Dict[str, Any]] = None
    ) -> CartMandate:
        """Create a Cart Mandate from payment items."""
        
        if intent_id not in self.active_intents:
            raise ValueError(f"Intent {intent_id} not found")
        
        intent_mandate = self.active_intents[intent_id]
        cart_id = f"cart-{intent_id}-{datetime.now(timezone.utc).timestamp()}"
        cart_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Create payment request
        total_amount = sum(item.amount.value for item in items)
        total_item = PaymentItem(
            label="Total",
            amount=PaymentCurrencyAmount(currency="USD", value=total_amount)
        )
        
        payment_request = PaymentRequest(
            method_data=[
                {
                    "supported_methods": "basic-card",
                    "data": {}
                }
            ],
            details={
                "id": cart_id,
                "display_items": items,
                "total": total_item
            },
            options={
                "request_shipping": bool(shipping_address)
            },
            shipping_address=shipping_address
        )
        
        cart_contents = CartContents(
            id=cart_id,
            user_cart_confirmation_required=intent_mandate.user_cart_confirmation_required,
            payment_request=payment_request,
            cart_expiry=cart_expiry.isoformat(),
            merchant_name="sofIA Payment Agent"
        )
        
        # Sign cart contents
        merchant_auth = self.signer.sign_cart_contents(cart_contents, self.merchant_id)
        
        cart_mandate = CartMandate(
            contents=cart_contents,
            merchant_authorization=merchant_auth
        )
        
        self.active_carts[cart_id] = cart_mandate
        return cart_mandate
    
    def create_payment_mandate(
        self,
        cart_id: str,
        payment_response: PaymentResponse,
        user_id: str
    ) -> PaymentMandate:
        """Create a Payment Mandate after user confirms payment."""
        
        if cart_id not in self.active_carts:
            raise ValueError(f"Cart {cart_id} not found")
        
        cart_mandate = self.active_carts[cart_id]
        payment_mandate_id = f"payment-{cart_id}-{datetime.now(timezone.utc).timestamp()}"
        
        payment_mandate_contents = PaymentMandateContents(
            payment_mandate_id=payment_mandate_id,
            payment_details_id=cart_mandate.contents.payment_request.details.id,
            payment_details_total=cart_mandate.contents.payment_request.details.total,
            payment_response=payment_response,
            merchant_agent=self.agent_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Create user authorization
        cart_hash = self.signer._compute_cart_hash(cart_mandate.contents)
        payment_data = payment_mandate_contents.model_dump()
        payment_json = json.dumps(payment_data, sort_keys=True, separators=(',', ':'))
        payment_hash = hashlib.sha256(payment_json.encode()).hexdigest()
        
        user_auth = self.signer.create_user_authorization(
            cart_hash, payment_hash, user_id
        )
        
        payment_mandate = PaymentMandate(
            payment_mandate_contents=payment_mandate_contents,
            user_authorization=user_auth
        )
        
        return payment_mandate
    
    def get_intent_status(self, intent_id: str) -> Dict[str, Any]:
        """Get status of an intent mandate."""
        if intent_id in self.active_intents:
            intent = self.active_intents[intent_id]
            return {
                "intent_id": intent_id,
                "status": "active",
                "user_id": intent.contents.user_id,
                "description": intent.contents.description,
                "created_at": intent.contents.created_at,
                "requires_confirmation": intent.user_cart_confirmation_required
            }
        return {"error": f"Intent {intent_id} not found"}

    def get_payment_mandate_status(self, payment_mandate_id: str) -> Dict[str, Any]:
        """Get status of a payment mandate."""
        if payment_mandate_id in self.payment_mandates:
            mandate = self.payment_mandates[payment_mandate_id]
            return {
                "payment_mandate_id": payment_mandate_id,
                "status": "completed",
                "amount": mandate.payment_mandate_contents.payment_response.details,
                "timestamp": mandate.payment_mandate_contents.created_at
            }
        return {"error": f"Payment mandate {payment_mandate_id} not found"}


class WhatsAppPaymentFlow:
    """Manages the complete payment flow within WhatsApp."""
    
    def __init__(self, agent: AP2PaymentAgent):
        self.agent = agent
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
    
    def handle_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming WhatsApp webhook and process payment flow."""
        
        user_id = webhook_data.get("from")
        message = webhook_data.get("text", {}).get("body", "")
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {"state": "idle"}
        
        session = self.user_sessions[user_id]
        
        # Process message based on current state
        if session["state"] == "idle":
            response = self.agent.process_whatsapp_message(message, user_id)
            if response["type"] == "intent_created":
                session["state"] = "shopping"
                session["intent_id"] = response["intent_id"]
            return response
        
        elif session["state"] == "shopping":
            # Simulate finding items (in production, integrate with merchant APIs)
            if "found items" in message.lower():
                # Create sample cart
                sample_items = [
                    PaymentItem(
                        label="Sample Product",
                        amount=PaymentCurrencyAmount(currency="USD", value=29.99)
                    )
                ]
                
                cart_mandate = self.agent.create_cart_mandate(
                    session["intent_id"], sample_items
                )
                
                session["state"] = "cart_ready"
                session["cart_id"] = cart_mandate.contents.id
                
                return {
                    "type": "cart_ready",
                    "message": f"Found items for you! Total: $29.99. Type 'confirm' to proceed with payment.",
                    "cart_id": cart_mandate.contents.id
                }
        
        elif session["state"] == "cart_ready":
            if "confirm" in message.lower():
                # Create payment response (in production, integrate with payment processor)
                payment_response = PaymentResponse(
                    request_id=session["cart_id"],
                    method_name="basic-card",
                    details={"card_number": "****1234"}  # Masked for security
                )
                
                payment_mandate = self.agent.create_payment_mandate(
                    session["cart_id"], payment_response, user_id
                )
                
                session["state"] = "payment_complete"
                
                return {
                    "type": "payment_complete",
                    "message": "Payment processed successfully! You'll receive confirmation shortly.",
                    "payment_mandate_id": payment_mandate.payment_mandate_contents.payment_mandate_id
                }
        
        return {
            "type": "error",
            "message": "I didn't understand that. Please try again."
        }
