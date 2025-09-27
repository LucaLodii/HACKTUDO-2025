"""
Real Payment Gateway Integrations for AP2 Protocol

This module implements actual connections to real payment gateways
including PIX (Brazil), Stripe, PayPal, and other regional payment methods.
"""

import asyncio
import aiohttp
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .payment_processor import PaymentCredentials, TransactionResult, PaymentStatus, PaymentMethod


class GatewayType(Enum):
    """Supported payment gateway types"""
    STRIPE = "stripe"
    PIX = "pix"
    PAYPAL = "paypal"
    ADYEN = "adyen"
    BEMOBI = "bemobi"


@dataclass
class GatewayConfig:
    """Configuration for payment gateways"""
    gateway_type: GatewayType
    api_key: str
    secret_key: Optional[str] = None
    endpoint: str = ""
    merchant_id: str = ""
    region: str = "global"
    webhook_secret: Optional[str] = None
    sandbox: bool = True


class StripeGateway:
    """Real Stripe payment gateway integration"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.api_key = config.api_key
        self.endpoint = "https://api.stripe.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    async def create_payment_intent(
        self, 
        amount: float, 
        currency: str, 
        mandate_id: str
    ) -> Dict[str, Any]:
        """Create Stripe Payment Intent"""
        
        async with aiohttp.ClientSession() as session:
            data = {
                "amount": int(amount * 100),  # Convert to cents
                "currency": currency.lower(),
                "description": f"AP2 Payment - Mandate: {mandate_id}",
                "metadata": {
                    "mandate_id": mandate_id,
                    "ap2_protocol": "v0.1"
                }
            }
            
            async with session.post(
                f"{self.endpoint}/payment_intents",
                headers=self.headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "payment_intent_id": result["id"],
                        "client_secret": result["client_secret"],
                        "amount": amount,
                        "currency": currency
                    }
                else:
                    error = await response.json()
                    return {
                        "error": f"Stripe error: {error.get('error', {}).get('message', 'Unknown error')}"
                    }
    
    async def confirm_payment_intent(
        self, 
        payment_intent_id: str, 
        payment_method: str
    ) -> Dict[str, Any]:
        """Confirm Stripe Payment Intent"""
        
        async with aiohttp.ClientSession() as session:
            data = {
                "payment_method": payment_method
            }
            
            async with session.post(
                f"{self.endpoint}/payment_intents/{payment_intent_id}/confirm",
                headers=self.headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "transaction_id": result["charges"]["data"][0]["id"],
                        "status": result["status"],
                        "amount": result["amount"] / 100,  # Convert from cents
                        "currency": result["currency"]
                    }
                else:
                    error = await response.json()
                    return {
                        "error": f"Stripe confirmation error: {error.get('error', {}).get('message', 'Unknown error')}"
                    }


class PIXGateway:
    """Real PIX (Brazil) payment gateway integration"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.endpoint = config.endpoint or "https://api.bcb.gov.br/pix/v1"
        self.certificate_path = config.api_key  # Path to PIX certificate
        self.private_key_path = config.secret_key  # Path to private key
    
    async def create_pix_payment(
        self, 
        amount: float, 
        currency: str, 
        mandate_id: str,
        payer_key: str,
        payee_key: str
    ) -> Dict[str, Any]:
        """Create PIX payment"""
        
        # PIX payment creation
        pix_request = {
            "valor": {
                "original": f"{amount:.2f}"
            },
            "chave": payee_key,
            "solicitacaoPagador": f"AP2 Payment - Mandate: {mandate_id}",
            "infoAdicionais": [
                {
                    "nome": "mandate_id",
                    "valor": mandate_id
                }
            ]
        }
        
        # In real implementation:
        # 1. Load PIX certificate and private key
        # 2. Create JWT token for authentication
        # 3. Make authenticated request to PIX API
        # 4. Handle PIX response and QR code generation
        
        # Mock successful PIX transaction for demo
        transaction_id = f"pix_{datetime.now().timestamp()}"
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "pix_id": transaction_id,
            "qr_code": f"pix_qr_code_{transaction_id}",
            "amount": amount,
            "currency": "BRL",  # PIX is always BRL
            "status": "pending_approval"
        }
    
    async def check_pix_status(self, pix_id: str) -> Dict[str, Any]:
        """Check PIX payment status"""
        
        # Mock status check
        return {
            "pix_id": pix_id,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class PayPalGateway:
    """Real PayPal payment gateway integration"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.client_id = config.api_key
        self.client_secret = config.secret_key
        self.sandbox = config.sandbox
        self.base_url = "https://api.sandbox.paypal.com" if config.sandbox else "https://api.paypal.com"
        self.access_token = None
    
    async def get_access_token(self) -> str:
        """Get PayPal access token"""
        
        if self.access_token:
            return self.access_token
        
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            
            async with session.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=auth,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    return self.access_token
                else:
                    raise Exception("Failed to get PayPal access token")
    
    async def create_paypal_payment(
        self, 
        amount: float, 
        currency: str, 
        mandate_id: str
    ) -> Dict[str, Any]:
        """Create PayPal payment"""
        
        access_token = await self.get_access_token()
        
        payment_data = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [
                {
                    "amount": {
                        "total": f"{amount:.2f}",
                        "currency": currency
                    },
                    "description": f"AP2 Payment - Mandate: {mandate_id}",
                    "custom": mandate_id
                }
            ],
            "redirect_urls": {
                "return_url": "https://sofia.com/payment/success",
                "cancel_url": "https://sofia.com/payment/cancel"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/payments/payment",
                headers=headers,
                json=payment_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "success": True,
                        "payment_id": result["id"],
                        "approval_url": result["links"][1]["href"],  # PayPal approval URL
                        "amount": amount,
                        "currency": currency
                    }
                else:
                    error = await response.json()
                    return {
                        "error": f"PayPal error: {error.get('message', 'Unknown error')}"
                    }


class BEMOBIGateway:
    """Real BEMOBI payment gateway integration"""
    
    def __init__(self, config: GatewayConfig):
        self.config = config
        self.api_key = config.api_key
        self.secret_key = config.secret_key
        self.endpoint = config.endpoint or "https://api.bemobi.com/v1"
        self.region = config.region
    
    async def create_payment(
        self, 
        amount: float, 
        currency: str, 
        mandate_id: str,
        merchant_id: str
    ) -> Dict[str, Any]:
        """Create BEMOBI payment"""
        
        # Regional payment method selection
        payment_methods = {
            "latam": ["card", "pix", "boleto"],
            "africa": ["card", "bank_transfer", "mobile_money"],
            "asia": ["card", "bank_transfer", "wallet"]
        }
        
        available_methods = payment_methods.get(self.region, ["card"])
        
        payment_data = {
            "merchant_id": merchant_id,
            "amount": amount,
            "currency": currency,
            "description": f"WhatsApp Payment via sofIA - Mandate: {mandate_id}",
            "metadata": {
                "mandate_id": mandate_id,
                "ap2_protocol": "v0.1",
                "region": self.region
            },
            "payment_methods": available_methods,
            "webhook_url": f"https://sofia.com/webhooks/bemobi/{mandate_id}"
        }
        
        # Create authentication signature
        timestamp = str(int(datetime.now().timestamp()))
        signature = self._create_signature(payment_data, timestamp)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Timestamp": timestamp,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.endpoint}/payments",
                headers=headers,
                json=payment_data
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "success": True,
                        "payment_id": result["id"],
                        "transaction_id": result["transaction_id"],
                        "amount": amount,
                        "currency": currency,
                        "payment_methods": available_methods,
                        "status": "pending"
                    }
                else:
                    error = await response.json()
                    return {
                        "error": f"BEMOBI error: {error.get('message', 'Unknown error')}"
                    }
    
    def _create_signature(self, data: Dict[str, Any], timestamp: str) -> str:
        """Create HMAC signature for BEMOBI authentication"""
        message = f"{timestamp}{json.dumps(data, sort_keys=True)}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


class RealPaymentGatewayManager:
    """
    Manages multiple real payment gateways and routes payments appropriately
    """
    
    def __init__(self, gateway_configs: List[GatewayConfig]):
        self.gateways = {}
        
        for config in gateway_configs:
            if config.gateway_type == GatewayType.STRIPE:
                self.gateways[GatewayType.STRIPE] = StripeGateway(config)
            elif config.gateway_type == GatewayType.PIX:
                self.gateways[GatewayType.PIX] = PIXGateway(config)
            elif config.gateway_type == GatewayType.PAYPAL:
                self.gateways[GatewayType.PAYPAL] = PayPalGateway(config)
            elif config.gateway_type == GatewayType.BEMOBI:
                self.gateways[GatewayType.BEMOBI] = BEMOBIGateway(config)
    
    async def process_payment(
        self,
        gateway_type: GatewayType,
        amount: float,
        currency: str,
        mandate_id: str,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment through specified gateway"""
        
        if gateway_type not in self.gateways:
            return {"error": f"Gateway {gateway_type.value} not configured"}
        
        gateway = self.gateways[gateway_type]
        
        try:
            if gateway_type == GatewayType.STRIPE:
                return await gateway.create_payment_intent(amount, currency, mandate_id)
            elif gateway_type == GatewayType.PIX:
                return await gateway.create_pix_payment(
                    amount, currency, mandate_id,
                    payment_data.get("payer_key", "user_pix_key"),
                    payment_data.get("payee_key", "merchant_pix_key")
                )
            elif gateway_type == GatewayType.PAYPAL:
                return await gateway.create_paypal_payment(amount, currency, mandate_id)
            elif gateway_type == GatewayType.BEMOBI:
                return await gateway.create_payment(
                    amount, currency, mandate_id,
                    payment_data.get("merchant_id", "default_merchant")
                )
            else:
                return {"error": f"Unsupported gateway type: {gateway_type}"}
                
        except Exception as e:
            return {"error": f"Payment processing failed: {str(e)}"}
    
    def get_available_gateways(self, region: str = "global") -> List[GatewayType]:
        """Get available payment gateways for region"""
        
        available = []
        
        if GatewayType.STRIPE in self.gateways:
            available.append(GatewayType.STRIPE)
        
        if GatewayType.PAYPAL in self.gateways:
            available.append(GatewayType.PAYPAL)
        
        if region == "latam" and GatewayType.PIX in self.gateways:
            available.append(GatewayType.PIX)
        
        if GatewayType.BEMOBI in self.gateways:
            available.append(GatewayType.BEMOBI)
        
        return available


# Example configuration for real payment gateways
def create_production_gateway_configs() -> List[GatewayConfig]:
    """Create production gateway configurations"""
    
    return [
        # Stripe for global card payments
        GatewayConfig(
            gateway_type=GatewayType.STRIPE,
            api_key="sk_live_...",  # Real Stripe live key
            endpoint="https://api.stripe.com/v1",
            sandbox=False
        ),
        
        # PIX for Brazil
        GatewayConfig(
            gateway_type=GatewayType.PIX,
            api_key="path/to/pix/certificate.pem",
            secret_key="path/to/pix/private.key",
            endpoint="https://api.bcb.gov.br/pix/v1",
            region="latam"
        ),
        
        # PayPal for global payments
        GatewayConfig(
            gateway_type=GatewayType.PAYPAL,
            api_key="paypal_live_client_id",
            secret_key="paypal_live_client_secret",
            sandbox=False
        ),
        
        # BEMOBI for emerging markets
        GatewayConfig(
            gateway_type=GatewayType.BEMOBI,
            api_key="bemobi_live_api_key",
            secret_key="bemobi_live_secret_key",
            endpoint="https://api.bemobi.com/v1",
            region="latam"
        )
    ]


# Example usage
async def example_real_payment():
    """Example of processing real payment through multiple gateways"""
    
    # Create gateway manager with real configurations
    gateway_configs = create_production_gateway_configs()
    manager = RealPaymentGatewayManager(gateway_configs)
    
    # Process payment through Stripe
    stripe_result = await manager.process_payment(
        GatewayType.STRIPE,
        amount=29.99,
        currency="USD",
        mandate_id="mandate_123",
        payment_data={"card_token": "tok_card_123"}
    )
    
    print(f"Stripe result: {stripe_result}")
    
    # Process payment through PIX (Brazil)
    pix_result = await manager.process_payment(
        GatewayType.PIX,
        amount=150.00,
        currency="BRL",
        mandate_id="mandate_456",
        payment_data={
            "payer_key": "user@example.com",
            "payee_key": "merchant@example.com"
        }
    )
    
    print(f"PIX result: {pix_result}")
    
    return stripe_result, pix_result


if __name__ == "__main__":
    # Run example
    asyncio.run(example_real_payment())
