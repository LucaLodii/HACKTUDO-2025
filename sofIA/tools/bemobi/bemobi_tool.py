"""
Bemobi Payment Gateway Tool for sofIA

This tool provides integration with Bemobi payment gateway for processing
WhatsApp payments through sofIA agent in emerging markets.
"""

import os
import json
import requests
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class BemobiMerchant:
    """Bemobi merchant configuration"""
    merchant_id: str
    store_name: str
    region: str
    currency: str
    api_key: str
    webhook_url: Optional[str] = None
    supported_payment_methods: List[str] = None
    
    def __post_init__(self):
        if self.supported_payment_methods is None:
            self.supported_payment_methods = ["card", "pix", "boleto"]


class BemobiPaymentProcessor:
    """Handles payment processing through Bemobi gateway"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.bemobi.com/v1")
        self.api_key = config.get("api_key")
        self.secret_key = config.get("secret_key")
        self.region = config.get("region", "latam")
        self.merchants: Dict[str, BemobiMerchant] = {}
        
        if not self.api_key:
            raise ValueError("Bemobi API key is required")
    
    def add_merchant(self, merchant: BemobiMerchant):
        """Add a merchant to the Bemobi processor"""
        self.merchants[merchant.merchant_id] = merchant
    
    def get_merchant(self, merchant_id: str) -> Optional[BemobiMerchant]:
        """Get merchant configuration by ID"""
        return self.merchants.get(merchant_id)
    
    async def create_payment_intent(self, merchant_id: str, amount: float, 
                                  currency: str, description: str) -> Dict[str, Any]:
        """Create a payment intent with Bemobi"""
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Bemobi-Merchant-ID": merchant_id
        }
        
        payload = {
            "amount": amount,
            "currency": currency,
            "description": description,
            "merchant_id": merchant_id,
            "region": self.region,
            "metadata": {
                "source": "sofia_whatsapp",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments/intent",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Bemobi payment intent creation failed: {str(e)}"}
    
    async def process_payment(self, payment_intent_id: str, payment_method: str,
                            payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through Bemobi"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "payment_intent_id": payment_intent_id,
            "payment_method": payment_method,
            "payment_data": payment_data,
            "metadata": {
                "source": "sofia_whatsapp",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments/process",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Bemobi payment processing failed: {str(e)}"}
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from Bemobi"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Bemobi payment status check failed: {str(e)}"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Bemobi webhook signature"""
        if not self.secret_key:
            return False
        
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)


class BemobiTool:
    """Tool for handling Bemobi payment gateway operations"""
    
    def __init__(self):
        self.name = "bemobi_payment"
        self.description = "Process payments through Bemobi payment gateway for WhatsApp transactions"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "create_payment_intent",
                        "process_payment", 
                        "get_payment_status",
                        "add_merchant",
                        "get_merchant_info"
                    ],
                    "description": "The Bemobi operation to perform"
                },
                "merchant_id": {
                    "type": "string",
                    "description": "Bemobi merchant ID"
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount"
                },
                "currency": {
                    "type": "string",
                    "description": "Payment currency (BRL, USD, etc.)"
                },
                "description": {
                    "type": "string",
                    "description": "Payment description"
                },
                "payment_intent_id": {
                    "type": "string",
                    "description": "Payment intent ID for processing"
                },
                "payment_method": {
                    "type": "string",
                    "enum": ["card", "pix", "boleto", "bank_transfer"],
                    "description": "Payment method"
                },
                "payment_data": {
                    "type": "object",
                    "description": "Payment method specific data"
                },
                "payment_id": {
                    "type": "string",
                    "description": "Payment ID for status check"
                },
                "store_name": {
                    "type": "string",
                    "description": "Store/merchant name"
                },
                "region": {
                    "type": "string",
                    "enum": ["latam", "africa", "asia"],
                    "description": "Geographic region"
                },
                "api_key": {
                    "type": "string",
                    "description": "Merchant API key"
                }
            },
            "required": ["operation"]
        }
        
        # Initialize Bemobi processor
        bemobi_config = {
            "api_key": os.getenv("BEMOBI_API_KEY"),
            "secret_key": os.getenv("BEMOBI_SECRET_KEY"),
            "base_url": os.getenv("BEMOBI_BASE_URL", "https://api.bemobi.com/v1"),
            "region": os.getenv("BEMOBI_REGION", "latam")
        }
        
        self.processor = BemobiPaymentProcessor(bemobi_config)
        
        # Add default merchants for demo
        self._add_demo_merchants()
    
    def _add_demo_merchants(self):
        """Add demo merchants for testing"""
        demo_merchants = [
            BemobiMerchant(
                merchant_id="bemobi_demo_001",
                store_name="Café do João",
                region="latam",
                currency="BRL",
                api_key="demo_api_key_001",
                supported_payment_methods=["card", "pix"]
            ),
            BemobiMerchant(
                merchant_id="bemobi_demo_002", 
                store_name="Tech Store Lagos",
                region="africa",
                currency="NGN",
                api_key="demo_api_key_002",
                supported_payment_methods=["card", "bank_transfer"]
            ),
            BemobiMerchant(
                merchant_id="bemobi_demo_003",
                store_name="Bangkok Electronics",
                region="asia", 
                currency="THB",
                api_key="demo_api_key_003",
                supported_payment_methods=["card", "bank_transfer"]
            )
        ]
        
        for merchant in demo_merchants:
            self.processor.add_merchant(merchant)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Bemobi operation"""
        operation = kwargs.get("operation")
        
        try:
            if operation == "create_payment_intent":
                return await self._create_payment_intent(**kwargs)
            elif operation == "process_payment":
                return await self._process_payment(**kwargs)
            elif operation == "get_payment_status":
                return await self._get_payment_status(**kwargs)
            elif operation == "add_merchant":
                return await self._add_merchant(**kwargs)
            elif operation == "get_merchant_info":
                return await self._get_merchant_info(**kwargs)
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"error": f"Bemobi operation failed: {str(e)}"}
    
    async def _create_payment_intent(self, merchant_id: str, amount: float,
                                   currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """Create payment intent with Bemobi"""
        result = await self.processor.create_payment_intent(
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            description=description
        )
        
        if "error" in result:
            return result
        
        return {
            "success": True,
            "payment_intent_id": result.get("id"),
            "client_secret": result.get("client_secret"),
            "amount": amount,
            "currency": currency,
            "status": result.get("status", "requires_payment_method"),
            "merchant_id": merchant_id
        }
    
    async def _process_payment(self, payment_intent_id: str, payment_method: str,
                             payment_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process payment through Bemobi"""
        result = await self.processor.process_payment(
            payment_intent_id=payment_intent_id,
            payment_method=payment_method,
            payment_data=payment_data
        )
        
        if "error" in result:
            return result
        
        return {
            "success": True,
            "payment_id": result.get("id"),
            "status": result.get("status"),
            "amount": result.get("amount"),
            "currency": result.get("currency"),
            "payment_method": payment_method,
            "transaction_id": result.get("transaction_id")
        }
    
    async def _get_payment_status(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """Get payment status from Bemobi"""
        result = await self.processor.get_payment_status(payment_id)
        
        if "error" in result:
            return result
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": result.get("status"),
            "amount": result.get("amount"),
            "currency": result.get("currency"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "failure_reason": result.get("failure_reason")
        }
    
    async def _add_merchant(self, merchant_id: str, store_name: str, region: str,
                          currency: str, api_key: str, **kwargs) -> Dict[str, Any]:
        """Add a new merchant to Bemobi processor"""
        merchant = BemobiMerchant(
            merchant_id=merchant_id,
            store_name=store_name,
            region=region,
            currency=currency,
            api_key=api_key,
            supported_payment_methods=kwargs.get("supported_payment_methods", ["card", "pix"])
        )
        
        self.processor.add_merchant(merchant)
        
        return {
            "success": True,
            "merchant_id": merchant_id,
            "store_name": store_name,
            "region": region,
            "currency": currency,
            "message": f"Merchant {store_name} added successfully"
        }
    
    async def _get_merchant_info(self, merchant_id: str, **kwargs) -> Dict[str, Any]:
        """Get merchant information"""
        merchant = self.processor.get_merchant(merchant_id)
        
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        return {
            "success": True,
            "merchant_id": merchant.merchant_id,
            "store_name": merchant.store_name,
            "region": merchant.region,
            "currency": merchant.currency,
            "supported_payment_methods": merchant.supported_payment_methods,
            "webhook_url": merchant.webhook_url
        }


# Initialize tool instance
_bemobi_tool = BemobiTool()


def bemobi_tool(**kwargs):
    """Bemobi payment tool function."""
    return _bemobi_tool.execute(**kwargs)
