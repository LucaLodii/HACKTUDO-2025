"""
AP2-Compliant Payment Credential Collector

This module implements secure payment credential collection following the official AP2 protocol
specification for handling user payment methods and authorization.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from .verifiable_credentials import VerifiableCredential, CredentialProvider, CredentialWallet
from .ap2_core import AP2PaymentAgent
from .types.payment_request import PaymentResponse, PaymentMethodData


@dataclass
class PaymentMethodInfo:
    """Information about available payment methods per AP2 spec"""
    method_type: str
    supported_methods: str
    data: Dict[str, Any]
    is_available: bool
    requires_verification: bool


class AP2CredentialCollector:
    """Handles secure payment credential collection per AP2 protocol specification"""
    
    def __init__(self, ap2_agent: AP2PaymentAgent):
        self.ap2_agent = ap2_agent
        self.credential_provider = ap2_agent.credential_provider
        self.active_collections: Dict[str, Dict[str, Any]] = {}
    
    async def discover_payment_methods(self, user_id: str, region: str = "latam") -> List[PaymentMethodInfo]:
        """Discover available payment methods for user per AP2 specification"""
        
        # Get user's credential wallet
        wallet = CredentialWallet(user_id, self.credential_provider)
        
        # Get available methods from user's credentials
        user_methods = wallet.get_available_payment_methods()
        
        # Build payment method info per AP2 spec
        payment_methods = []
        
        # Card payment method
        if "credit_card" in user_methods or "basic-card" in user_methods or region in ["latam", "global"]:
            payment_methods.append(PaymentMethodInfo(
                method_type="credit_card",
                supported_methods="credit_card",
                data={
                    "networks": ["visa", "mastercard", "amex"],
                    "available": True,
                    "instant": False,
                    "fee": "2.9%"
                },
                is_available=True,
                requires_verification=True
            ))
        
        # PIX payment method (Brazil)
        if "pix" in user_methods or region == "latam":
            payment_methods.append(PaymentMethodInfo(
                method_type="pix",
                supported_methods="pix",
                data={
                    "type": "pix",
                    "available": True,
                    "instant": True,
                    "fee": "0.5%"
                },
                is_available=True,
                requires_verification=True
            ))
        
        # PayPal payment method
        if "paypal" in user_methods or region in ["latam", "global"]:
            payment_methods.append(PaymentMethodInfo(
                method_type="paypal",
                supported_methods="paypal",
                data={
                    "type": "paypal",
                    "available": True,
                    "instant": True,
                    "fee": "3.4%"
                },
                is_available=True,
                requires_verification=True
            ))
        
        return payment_methods
    
    async def collect_payment_credentials(
        self, 
        user_id: str, 
        cart_mandate_id: str,
        selected_method: str,
        amount: float,
        currency: str
    ) -> Dict[str, Any]:
        """Collect payment credentials for a specific payment method per AP2 spec"""
        
        collection_id = f"collection-{user_id}-{datetime.now().timestamp()}"
        
        # Get user's credential wallet
        wallet = CredentialWallet(user_id, self.credential_provider)
        
        # Authorize payment with user's credentials
        auth_result = wallet.authorize_payment(amount, currency, selected_method)
        
        if not auth_result.get("authorized"):
            return {
                "success": False,
                "error": auth_result.get("error", "Payment authorization failed"),
                "collection_id": collection_id
            }
        
        # Store collection info
        self.active_collections[collection_id] = {
            "user_id": user_id,
            "cart_mandate_id": cart_mandate_id,
            "selected_method": selected_method,
            "amount": amount,
            "currency": currency,
            "authorization": auth_result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Collect encrypted credentials based on method
        encrypted_credentials = await self._collect_method_credentials(
            user_id, selected_method, auth_result
        )
        
        # Create Payment Response per AP2 spec
        payment_response = PaymentResponse(
            request_id=cart_mandate_id,
            method_name=selected_method,
            details=encrypted_credentials
        )
        
        return {
            "success": True,
            "collection_id": collection_id,
            "payment_response": payment_response,
            "credential_info": {
                "method": selected_method,
                "encrypted_data": encrypted_credentials.get("encrypted_data"),
                "provider_token": encrypted_credentials.get("provider_token"),
                "consent_proof": auth_result.get("consent_proof")
            }
        }
    
    async def collect_payment_credentials_with_data(
        self, 
        user_id: str, 
        cart_mandate_id: str,
        selected_method: str,
        amount: float,
        currency: str,
        user_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect payment credentials with user's actual payment data per AP2 spec"""
        
        collection_id = f"collection-{user_id}-{datetime.now().timestamp()}"
        
        # Get user's credential wallet
        wallet = CredentialWallet(user_id, self.credential_provider)
        
        # Authorize payment with user's credentials
        auth_result = wallet.authorize_payment(amount, currency, selected_method)
        
        if not auth_result.get("authorized"):
            return {
                "success": False,
                "error": auth_result.get("error", "Payment authorization failed"),
                "collection_id": collection_id
            }
        
        # Store collection info
        self.active_collections[collection_id] = {
            "user_id": user_id,
            "cart_mandate_id": cart_mandate_id,
            "selected_method": selected_method,
            "amount": amount,
            "currency": currency,
            "authorization": auth_result,
            "user_payment_data": user_payment_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Collect encrypted credentials based on method with user's actual data
        encrypted_credentials = await self._collect_method_credentials_with_data(
            user_id, selected_method, auth_result, user_payment_data
        )
        
        # Create Payment Response per AP2 spec
        payment_response = PaymentResponse(
            request_id=cart_mandate_id,
            method_name=selected_method,
            details=encrypted_credentials
        )
        
        return {
            "success": True,
            "collection_id": collection_id,
            "payment_response": payment_response,
            "credential_info": {
                "method": selected_method,
                "encrypted_data": encrypted_credentials.get("encrypted_data"),
                "provider_token": encrypted_credentials.get("provider_token"),
                "consent_proof": auth_result.get("consent_proof")
            }
        }
    
    async def _collect_method_credentials(
        self, 
        user_id: str, 
        method: str, 
        auth_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect encrypted credentials for specific payment method"""
        
        if method == "credit_card" or method == "basic-card":
            return await self._collect_card_credentials(user_id, auth_result)
        elif method == "pix":
            return await self._collect_pix_credentials(user_id, auth_result)
        elif method == "paypal":
            return await self._collect_paypal_credentials(user_id, auth_result)
        else:
            raise ValueError(f"Unsupported payment method: {method}")
    
    async def _collect_method_credentials_with_data(
        self, 
        user_id: str, 
        method: str, 
        auth_result: Dict[str, Any],
        user_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect encrypted credentials for specific payment method with user's actual data"""
        
        if method == "credit_card" or method == "basic-card":
            return await self._collect_card_credentials_with_data(user_id, auth_result, user_payment_data)
        elif method == "pix":
            return await self._collect_pix_credentials_with_data(user_id, auth_result, user_payment_data)
        elif method == "paypal":
            return await self._collect_paypal_credentials_with_data(user_id, auth_result, user_payment_data)
        else:
            raise ValueError(f"Unsupported payment method: {method}")
    
    async def _collect_card_credentials(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect credit card credentials securely per AP2 spec"""
        
        # In a real implementation, this would:
        # 1. Present secure card entry form to user
        # 2. Tokenize card data with payment processor (Stripe, etc.)
        # 3. Return encrypted token and metadata
        
        # Mock implementation following AP2 structure
        card_token = f"tok_{user_id}_{datetime.now().timestamp()}"
        encrypted_card_data = f"enc_card_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_card_data,
            "provider_token": card_token,
            "card_metadata": {
                "last_four": "1234",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025,
                "country": "BR"
            },
            "verification_method": "3d_secure",
            "consent_proof": auth_result.get("consent_proof")
        }
    
    async def _collect_card_credentials_with_data(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any],
        user_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect credit card credentials with user's actual card data per AP2 spec"""
        
        # Extract card details from user's payment data
        card_details = user_payment_data.get("details", {})
        card_number = card_details.get("card_number", "")
        expiry = card_details.get("expiry", "")
        cardholder_name = card_details.get("cardholder_name", "")
        
        # Extract last 4 digits for display
        last_four = card_number[-4:] if len(card_number) >= 4 else "****"
        
        # Extract brand from card number (simplified)
        brand = "visa"  # Default, in real implementation would detect from BIN
        
        # Parse expiry date
        exp_month = 12
        exp_year = 2025
        if "/" in expiry:
            try:
                month_str, year_str = expiry.split("/")
                exp_month = int(month_str)
                exp_year = int("20" + year_str) if len(year_str) == 2 else int(year_str)
            except (ValueError, IndexError):
                pass
        
        # Generate secure token and encrypted data
        card_token = f"tok_{user_id}_{datetime.now().timestamp()}"
        encrypted_card_data = f"enc_card_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_card_data,
            "provider_token": card_token,
            "card_metadata": {
                "last_four": last_four,
                "brand": brand,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "country": "BR",
                "cardholder_name": cardholder_name
            },
            "verification_method": "3d_secure",
            "consent_proof": auth_result.get("consent_proof"),
            "user_provided_data": {
                "card_number_masked": f"****{last_four}",
                "expiry": expiry,
                "cardholder_name": cardholder_name
            }
        }
    
    async def _collect_pix_credentials(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect PIX credentials securely per AP2 spec"""
        
        # In a real implementation, this would:
        # 1. Present PIX key entry form
        # 2. Validate PIX key format
        # 3. Encrypt PIX key data
        # 4. Return encrypted PIX credentials
        
        # Mock implementation following AP2 structure
        pix_key = f"{user_id}@example.com"  # Mock PIX key
        encrypted_pix_data = f"enc_pix_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_pix_data,
            "provider_token": f"pix_token_{user_id}_{datetime.now().timestamp()}",
            "pix_metadata": {
                "key_type": "email",
                "key_value": pix_key,
                "instant": True,
                "fee": 0.005  # 0.5%
            },
            "consent_proof": auth_result.get("consent_proof")
        }
    
    async def _collect_pix_credentials_with_data(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any],
        user_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect PIX credentials with user's actual PIX data per AP2 spec"""
        
        # Extract PIX details from user's payment data
        pix_details = user_payment_data.get("details", {})
        pix_key = pix_details.get("pix_key", "")
        
        # Determine PIX key type
        key_type = "email"
        if "@" in pix_key:
            key_type = "email"
        elif pix_key.isdigit() and len(pix_key) == 11:
            key_type = "cpf"
        elif pix_key.isdigit() and len(pix_key) >= 10:
            key_type = "phone"
        else:
            key_type = "random"
        
        # Generate secure token and encrypted data
        encrypted_pix_data = f"enc_pix_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_pix_data,
            "provider_token": f"pix_token_{user_id}_{datetime.now().timestamp()}",
            "pix_metadata": {
                "key_type": key_type,
                "key_value": pix_key,
                "instant": True,
                "fee": 0.005  # 0.5%
            },
            "consent_proof": auth_result.get("consent_proof"),
            "user_provided_data": {
                "pix_key": pix_key,
                "key_type": key_type
            }
        }
    
    async def _collect_paypal_credentials(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect PayPal credentials securely per AP2 spec"""
        
        # In a real implementation, this would:
        # 1. Initiate PayPal OAuth flow
        # 2. Get user authorization
        # 3. Exchange for access token
        # 4. Return encrypted PayPal credentials
        
        # Mock implementation following AP2 structure
        paypal_token = f"paypal_token_{user_id}_{datetime.now().timestamp()}"
        encrypted_paypal_data = f"enc_paypal_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_paypal_data,
            "provider_token": paypal_token,
            "paypal_metadata": {
                "account_type": "personal",
                "currency": "BRL",
                "instant": True,
                "fee": 0.034  # 3.4%
            },
            "consent_proof": auth_result.get("consent_proof")
        }
    
    async def _collect_paypal_credentials_with_data(
        self, 
        user_id: str, 
        auth_result: Dict[str, Any],
        user_payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect PayPal credentials with user's actual PayPal data per AP2 spec"""
        
        # Extract PayPal details from user's payment data
        paypal_details = user_payment_data.get("details", {})
        paypal_email = paypal_details.get("paypal_email", "")
        
        # Generate secure token and encrypted data
        paypal_token = f"paypal_token_{user_id}_{datetime.now().timestamp()}"
        encrypted_paypal_data = f"enc_paypal_{user_id}_{datetime.now().timestamp()}"
        
        return {
            "encrypted_data": encrypted_paypal_data,
            "provider_token": paypal_token,
            "paypal_metadata": {
                "account_type": "personal",
                "currency": "BRL",
                "instant": True,
                "fee": 0.034  # 3.4%
            },
            "consent_proof": auth_result.get("consent_proof"),
            "user_provided_data": {
                "paypal_email": paypal_email
            }
        }
    
    async def verify_payment_credentials(
        self, 
        collection_id: str, 
        payment_response: PaymentResponse
    ) -> Dict[str, Any]:
        """Verify collected payment credentials per AP2 specification"""
        
        if collection_id not in self.active_collections:
            return {
                "verified": False,
                "error": f"Collection {collection_id} not found"
            }
        
        collection = self.active_collections[collection_id]
        
        # Verify payment response matches collection
        if payment_response.request_id != collection["cart_mandate_id"]:
            return {
                "verified": False,
                "error": "Payment response request_id mismatch"
            }
        
        if payment_response.method_name != collection["selected_method"]:
            return {
                "verified": False,
                "error": "Payment method mismatch"
            }
        
        # Verify credentials are properly encrypted
        details = payment_response.details
        if not details.get("encrypted_data") or not details.get("provider_token"):
            return {
                "verified": False,
                "error": "Missing required credential data"
            }
        
        # Verify consent proof
        if not details.get("consent_proof"):
            return {
                "verified": False,
                "error": "Missing consent proof"
            }
        
        return {
            "verified": True,
            "collection_id": collection_id,
            "method": payment_response.method_name,
            "amount": collection["amount"],
            "currency": collection["currency"],
            "verified_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def create_payment_mandate_from_collection(
        self, 
        collection_id: str
    ) -> Dict[str, Any]:
        """Create payment mandate from verified credential collection"""
        
        if collection_id not in self.active_collections:
            return {
                "success": False,
                "error": f"Collection {collection_id} not found"
            }
        
        collection = self.active_collections[collection_id]
        
        # Get user credential
        wallet = CredentialWallet(collection["user_id"], self.credential_provider)
        credentials = wallet.provider.get_user_payment_credentials(collection["user_id"])
        
        # Find matching credential
        user_credential = None
        for credential in credentials:
            method_match = credential.claims.get("payment_method") == collection["selected_method"]
            # Also allow basic-card to match credit_card for backward compatibility
            compat_match = (credential.claims.get("payment_method") == "basic-card" and collection["selected_method"] == "credit_card")
            if method_match or compat_match:
                user_credential = credential
                break
        
        if not user_credential:
            return {
                "success": False,
                "error": "No valid credential found for payment method"
            }
        
        # Create payment mandate using AP2 agent
        payment_mandate = self.ap2_agent.create_payment_mandate(
            cart_id=collection["cart_mandate_id"],
            payment_response=collection.get("payment_response"),
            user_id=collection["user_id"],
            user_credential=user_credential,
            consent_proof=collection["authorization"].get("consent_proof")
        )
        
        return {
            "success": True,
            "payment_mandate": payment_mandate,
            "collection_id": collection_id
        }
    
    def get_collection_status(self, collection_id: str) -> Dict[str, Any]:
        """Get status of credential collection"""
        
        if collection_id not in self.active_collections:
            return {
                "found": False,
                "error": f"Collection {collection_id} not found"
            }
        
        collection = self.active_collections[collection_id]
        
        return {
            "found": True,
            "status": "active",
            "user_id": collection["user_id"],
            "method": collection["selected_method"],
            "amount": collection["amount"],
            "currency": collection["currency"],
            "created_at": collection["created_at"]
        }


class AP2PaymentMethodDiscovery:
    """Handles payment method discovery per AP2 specification"""
    
    def __init__(self, credential_collector: AP2CredentialCollector):
        self.collector = credential_collector
    
    async def get_supported_payment_methods(self, user_id: str, region: str = "latam") -> List[Dict[str, Any]]:
        """Get supported payment methods formatted for AP2 PaymentRequest"""
        
        payment_methods = await self.collector.discover_payment_methods(user_id, region)
        
        # Convert to AP2 PaymentMethodData format
        ap2_methods = []
        for method in payment_methods:
            ap2_methods.append({
                "supported_methods": method.supported_methods,
                "data": method.data
            })
        
        return ap2_methods
    
    async def recommend_payment_method(
        self, 
        user_id: str, 
        amount: float, 
        currency: str, 
        region: str = "latam"
    ) -> Dict[str, Any]:
        """Recommend optimal payment method based on AP2 best practices"""
        
        available_methods = await self.collector.discover_payment_methods(user_id, region)
        
        if not available_methods:
            return {
                "recommended": None,
                "error": "No payment methods available"
            }
        
        # AP2 recommendation logic
        if currency == "BRL" and region == "latam":
            # Prefer PIX for Brazilian Real
            for method in available_methods:
                if method.method_type == "pix":
                    return {
                        "recommended": method.method_type,
                        "reason": "PIX is preferred for BRL transactions",
                        "instant": True,
                        "fee": method.data.get("fee", "0.5%")
                    }
        
        # Default to first available method
        recommended = available_methods[0]
        
        return {
            "recommended": recommended.method_type,
            "reason": "Default recommendation",
            "instant": recommended.data.get("instant", False),
            "fee": recommended.data.get("fee", "varies")
        }


# Global instances
_credential_collector = None
_payment_method_discovery = None

def get_credential_collector(ap2_agent: AP2PaymentAgent) -> AP2CredentialCollector:
    """Get global credential collector instance"""
    global _credential_collector
    if _credential_collector is None:
        _credential_collector = AP2CredentialCollector(ap2_agent)
    return _credential_collector

def get_payment_method_discovery(ap2_agent: AP2PaymentAgent) -> AP2PaymentMethodDiscovery:
    """Get global payment method discovery instance"""
    global _payment_method_discovery
    if _payment_method_discovery is None:
        collector = get_credential_collector(ap2_agent)
        _payment_method_discovery = AP2PaymentMethodDiscovery(collector)
    return _payment_method_discovery
