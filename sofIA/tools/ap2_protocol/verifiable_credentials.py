"""
Verifiable Credentials (VCs) Framework for AP2 Protocol

This module implements the Verifiable Credentials framework as specified in the official AP2 protocol
for secure user authorization and payment credential management.
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import jwt
from pydantic import BaseModel, Field


class VerifiableCredential(BaseModel):
    """AP2-compliant Verifiable Credential for user authorization"""
    
    id: str = Field(..., description="Unique identifier for the credential")
    issuer: str = Field(..., description="Issuer of the credential (user's wallet/agent)")
    subject: str = Field(..., description="Subject (user) of the credential")
    issued_at: str = Field(..., description="ISO 8601 timestamp of issuance")
    expires_at: str = Field(..., description="ISO 8601 timestamp of expiration")
    claims: Dict[str, Any] = Field(..., description="Credential claims and permissions")
    proof: Optional[str] = Field(None, description="Cryptographic proof of the credential")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "vc:payment:user123:card",
                "issuer": "user-wallet-agent",
                "subject": "user123",
                "issued_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-12-31T23:59:59Z",
                "claims": {
                    "payment_methods": ["basic-card", "pix"],
                    "authorization_level": "single_use",
                    "max_amount": 1000.00,
                    "currency": "BRL"
                },
                "proof": "jwt_signature_here"
            }
        }


class PaymentMethodCredential(BaseModel):
    """Verifiable credential for specific payment methods"""
    
    method_type: str = Field(..., description="Payment method type (basic-card, pix, paypal)")
    method_id: str = Field(..., description="Unique identifier for this payment method")
    encrypted_data: str = Field(..., description="Encrypted payment method data")
    provider_token: str = Field(..., description="Token from credential provider")
    is_verified: bool = Field(default=False, description="Whether this credential is verified")
    last_used: Optional[str] = Field(None, description="ISO 8601 timestamp of last use")
    usage_count: int = Field(default=0, description="Number of times this credential was used")


class UserAuthorizationLevel(BaseModel):
    """User authorization levels for payment operations"""
    
    level: str = Field(..., description="Authorization level")
    description: str = Field(..., description="Description of authorization level")
    max_amount: Optional[float] = Field(None, description="Maximum amount allowed")
    max_frequency: Optional[str] = Field(None, description="Maximum frequency (daily, monthly, etc.)")
    expires_at: Optional[str] = Field(None, description="When this authorization expires")
    
    class Config:
        json_schema_extra = {
            "example": {
                "level": "delegated",
                "description": "Can make purchases up to R$ 500 without real-time confirmation",
                "max_amount": 500.00,
                "max_frequency": "daily",
                "expires_at": "2024-12-31T23:59:59Z"
            }
        }


@dataclass
class CredentialProvider:
    """Manages user payment credentials securely per AP2 protocol"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        self.config = provider_config
        self.private_key = self._generate_or_load_private_key()
        self.public_key = self.private_key.public_key()
        self.credential_storage: Dict[str, List[VerifiableCredential]] = {}  # Store credentials by user_id
    
    def _generate_or_load_private_key(self):
        """Generate or load RSA private key for credential signing"""
        # In production, this would load from secure key storage
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
    
    def create_payment_credential(
        self, 
        user_id: str, 
        payment_method: str, 
        credential_data: Dict[str, Any]
    ) -> VerifiableCredential:
        """Create a verifiable credential for payment method"""
        
        credential_id = f"vc:payment:{user_id}:{payment_method}:{datetime.now().timestamp()}"
        
        # Create credential claims
        claims = {
            "payment_method": payment_method,
            "user_id": user_id,
            "authorization_level": credential_data.get("authorization_level", "single_use"),
            "max_amount": credential_data.get("max_amount", 1000.00),
            "currency": credential_data.get("currency", "BRL"),
            "encrypted_payment_data": credential_data.get("encrypted_data"),
            "provider_token": credential_data.get("provider_token"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Create the credential
        credential = VerifiableCredential(
            id=credential_id,
            issuer="sofia-credential-provider",
            subject=user_id,
            issued_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            claims=claims
        )
        
        # Sign the credential
        credential.proof = self._sign_credential(credential)
        
        # Store the credential
        if user_id not in self.credential_storage:
            self.credential_storage[user_id] = []
        self.credential_storage[user_id].append(credential)
        
        return credential
    
    def _sign_credential(self, credential: VerifiableCredential) -> str:
        """Sign a verifiable credential with cryptographic proof"""
        
        # Create payload for signing (exclude proof field)
        payload = {
            "id": credential.id,
            "issuer": credential.issuer,
            "subject": credential.subject,
            "issued_at": credential.issued_at,
            "expires_at": credential.expires_at,
            "claims": credential.claims
        }
        
        # Sign with RS256 algorithm
        token = jwt.encode(
            payload, 
            self.private_key, 
            algorithm="RS256",
            headers={"typ": "JWT", "alg": "RS256"}
        )
        
        return token
    
    def verify_credential(self, credential: VerifiableCredential) -> bool:
        """Verify a verifiable credential's cryptographic proof"""
        
        try:
            if not credential.proof:
                return False
            
            # Verify JWT signature
            payload = jwt.decode(
                credential.proof,
                self.public_key,
                algorithms=["RS256"],
                options={"verify_exp": True}
            )
            
            # Verify credential hasn't expired
            expires_at = datetime.fromisoformat(credential.expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                return False
            
            return True
            
        except jwt.InvalidTokenError:
            return False
        except Exception:
            return False
    
    def get_user_payment_credentials(self, user_id: str) -> List[VerifiableCredential]:
        """Get all valid payment credentials for a user"""
        
        # Return stored credentials for the user
        if user_id in self.credential_storage:
            credentials = self.credential_storage[user_id]
            
            # Ensure we have both basic-card and PIX credentials
            has_basic_card = any(cred.claims.get('payment_method') == 'basic-card' for cred in credentials)
            has_pix = any(cred.claims.get('payment_method') == 'pix' for cred in credentials)
            
            if not has_basic_card or not has_pix:
                # Create missing credentials
                if not has_basic_card:
                    card_credential = self.create_payment_credential(
                        user_id=user_id,
                        payment_method="basic-card",
                        credential_data={
                            "authorization_level": "single_use",
                            "max_amount": 1000.00,
                            "currency": "BRL",
                            "encrypted_data": f"encrypted_card_data_{user_id}",
                            "provider_token": f"stripe_token_{user_id}"
                        }
                    )
                    credentials.append(card_credential)
                
                if not has_pix:
                    pix_credential = self.create_payment_credential(
                        user_id=user_id,
                        payment_method="pix",
                        credential_data={
                            "authorization_level": "delegated",
                            "max_amount": 5000.00,
                            "currency": "BRL",
                            "encrypted_data": f"encrypted_pix_key_{user_id}",
                            "provider_token": f"pix_token_{user_id}"
                        }
                    )
                    credentials.append(pix_credential)
                
                # Update storage
                self.credential_storage[user_id] = credentials
            
            return credentials
        
        # If no stored credentials, create default mock credentials
        mock_credentials = []
        
        # Mock card credential
        card_credential = self.create_payment_credential(
            user_id=user_id,
            payment_method="basic-card",
            credential_data={
                "authorization_level": "single_use",
                "max_amount": 1000.00,
                "currency": "BRL",
                "encrypted_data": f"encrypted_card_data_{user_id}",
                "provider_token": f"stripe_token_{user_id}"
            }
        )
        mock_credentials.append(card_credential)
        
        # Mock PIX credential
        pix_credential = self.create_payment_credential(
            user_id=user_id,
            payment_method="pix",
            credential_data={
                "authorization_level": "delegated",
                "max_amount": 5000.00,
                "currency": "BRL",
                "encrypted_data": f"encrypted_pix_key_{user_id}",
                "provider_token": f"pix_token_{user_id}"
            }
        )
        mock_credentials.append(pix_credential)
        
        return mock_credentials
    
    def authorize_payment(
        self, 
        user_id: str, 
        amount: float, 
        currency: str,
        payment_method: str
    ) -> Dict[str, Any]:
        """Authorize a payment using user's verifiable credentials"""
        
        credentials = self.get_user_payment_credentials(user_id)
        
        # Find matching credential
        matching_credential = None
        for credential in credentials:
            if (credential.claims.get("payment_method") == payment_method and
                self.verify_credential(credential)):
                matching_credential = credential
                break
        
        if not matching_credential:
            return {
                "authorized": False,
                "error": f"No valid {payment_method} credential found for user {user_id}"
            }
        
        # Check authorization level and limits
        auth_level = matching_credential.claims.get("authorization_level")
        max_amount = matching_credential.claims.get("max_amount", 0)
        credential_currency = matching_credential.claims.get("currency", "BRL")
        
        if currency != credential_currency:
            return {
                "authorized": False,
                "error": f"Currency mismatch: credential supports {credential_currency}, requested {currency}"
            }
        
        if amount > max_amount:
            return {
                "authorized": False,
                "error": f"Amount {amount} exceeds maximum allowed {max_amount}"
            }
        
        if auth_level == "single_use" and matching_credential.claims.get("usage_count", 0) > 0:
            return {
                "authorized": False,
                "error": "Single-use credential already used"
            }
        
        # Generate consent proof
        consent_proof = self._generate_consent_proof(
            user_id, amount, currency, payment_method, matching_credential
        )
        
        return {
            "authorized": True,
            "credential_id": matching_credential.id,
            "authorization_level": auth_level,
            "consent_proof": consent_proof,
            "encrypted_payment_data": matching_credential.claims.get("encrypted_payment_data"),
            "provider_token": matching_credential.claims.get("provider_token")
        }
    
    def _generate_consent_proof(
        self, 
        user_id: str, 
        amount: float, 
        currency: str, 
        payment_method: str,
        credential: VerifiableCredential
    ) -> str:
        """Generate cryptographic proof of user consent for payment"""
        
        consent_data = {
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "credential_id": credential.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "nonce": hashlib.sha256(f"{user_id}{amount}{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        }
        
        # Sign consent proof
        consent_proof = jwt.encode(
            consent_data,
            self.private_key,
            algorithm="RS256",
            headers={"typ": "JWT", "alg": "RS256"}
        )
        
        return consent_proof


class CredentialWallet:
    """User's credential wallet for managing payment credentials"""
    
    def __init__(self, user_id: str, credential_provider: CredentialProvider):
        self.user_id = user_id
        self.provider = credential_provider
        self.credentials: List[VerifiableCredential] = []
    
    def add_payment_method(
        self, 
        payment_method: str, 
        payment_data: Dict[str, Any]
    ) -> VerifiableCredential:
        """Add a new payment method credential to user's wallet"""
        
        credential = self.provider.create_payment_credential(
            user_id=self.user_id,
            payment_method=payment_method,
            credential_data=payment_data
        )
        
        self.credentials.append(credential)
        return credential
    
    def get_available_payment_methods(self) -> List[str]:
        """Get list of available payment methods from user's credentials"""
        
        available_methods = []
        for credential in self.credentials:
            if self.provider.verify_credential(credential):
                method = credential.claims.get("payment_method")
                if method and method not in available_methods:
                    available_methods.append(method)
        
        return available_methods
    
    def authorize_payment(self, amount: float, currency: str, payment_method: str) -> Dict[str, Any]:
        """Authorize a payment using wallet credentials"""
        
        return self.provider.authorize_payment(
            user_id=self.user_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )
    
    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a specific credential"""
        
        for i, credential in enumerate(self.credentials):
            if credential.id == credential_id:
                # In production, mark as revoked in database
                del self.credentials[i]
                return True
        
        return False


# Global credential provider instance
_credential_provider = None

def get_credential_provider() -> CredentialProvider:
    """Get global credential provider instance"""
    global _credential_provider
    if _credential_provider is None:
        _credential_provider = CredentialProvider({})
    return _credential_provider


def create_user_credential_wallet(user_id: str) -> CredentialWallet:
    """Create a credential wallet for a user"""
    provider = get_credential_provider()
    return CredentialWallet(user_id, provider)
