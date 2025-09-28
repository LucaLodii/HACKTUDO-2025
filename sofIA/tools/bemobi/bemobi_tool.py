"""
Bemobi Payment Gateway Tool for sofIA

This tool provides integration with Bemobi payment gateway for processing
WhatsApp payments through sofIA agent in emerging markets.

Now supports white-label implementation with mock merchants per telecom operator.
"""

import os
import json
import requests
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .mock_bemobi_gateway import (
    mock_bemobi_gateway,
    initialize_mock_gateway,
    get_merchant_for_operator,
    create_operator_payment_intent,
    process_operator_payment
)


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
    """Tool for handling Bemobi payment gateway operations with white-label support"""

    def __init__(self):
        self.name = "bemobi_payment"
        self.description = "Process payments through Bemobi payment gateway for WhatsApp transactions with operator-specific credentials"
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
                        "get_merchant_info",
                        "create_operator_payment",
                        "get_operator_payment_methods",
                        "list_available_operators"
                    ],
                    "description": "The Bemobi operation to perform"
                },
                "operator_name": {
                    "type": "string",
                    "enum": ["VIVO", "CLARO", "OI", "TIM"],
                    "description": "Telecom operator name for white-label payments"
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
                    "enum": ["PIX", "CARD", "BOLETO", "VIVO_WALLET", "CLARO_PAY", "OI_MONEY", "TIM_PAY"],
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
                "user_id": {
                    "type": "string",
                    "description": "User ID for payment tracking"
                }
            },
            "required": ["operation"]
        }

        # Initialize mock gateway instead of real Bemobi processor
        self.use_mock = os.getenv("BEMOBI_USE_MOCK", "true").lower() == "true"

        if self.use_mock:
            # Initialize mock gateway
            self.mock_initialized = False
        else:
            # Initialize real Bemobi processor for production
            bemobi_config = {
                "api_key": os.getenv("BEMOBI_API_KEY", "demo_api_key"),
                "secret_key": os.getenv("BEMOBI_SECRET_KEY", "demo_secret"),
                "base_url": os.getenv("BEMOBI_BASE_URL", "https://api.bemobi.com/v1"),
                "region": os.getenv("BEMOBI_REGION", "latam")
            }
            self.processor = BemobiPaymentProcessor(bemobi_config)
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
    
    async def _ensure_mock_initialized(self):
        """Ensure mock gateway is initialized"""
        if self.use_mock and not self.mock_initialized:
            await initialize_mock_gateway()
            self.mock_initialized = True

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Bemobi operation with white-label support"""
        operation = kwargs.get("operation")

        try:
            # Ensure mock gateway is initialized if using mock
            if self.use_mock:
                await self._ensure_mock_initialized()

            if operation == "create_operator_payment":
                return await self._create_operator_payment(**kwargs)
            elif operation == "get_operator_payment_methods":
                return await self._get_operator_payment_methods(**kwargs)
            elif operation == "list_available_operators":
                return await self._list_available_operators(**kwargs)
            elif operation == "create_payment_intent":
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

    async def _create_operator_payment(self, operator_name: str, amount: float,
                                     description: str, user_id: str = None, **kwargs) -> Dict[str, Any]:
        """Create payment intent for a specific telecom operator"""
        if self.use_mock:
            return await create_operator_payment_intent(
                operator_name=operator_name,
                amount=amount,
                description=description,
                user_id=user_id
            )
        else:
            # For real implementation, you'd look up operator credentials from database
            return {"error": "Real Bemobi integration not implemented for operators"}

    async def _get_operator_payment_methods(self, operator_name: str, **kwargs) -> Dict[str, Any]:
        """Get payment methods available for a specific operator"""
        if self.use_mock:
            merchant = await get_merchant_for_operator(operator_name)
            if not merchant:
                return {
                    "error": f"No merchant configuration found for operator {operator_name}",
                    "available_operators": ["VIVO", "CLARO", "OI", "TIM"]
                }

            return await mock_bemobi_gateway.get_payment_methods(merchant.mock_merchant_id)
        else:
            # For real implementation
            return {"error": "Real Bemobi integration not implemented for operators"}

    async def _list_available_operators(self, **kwargs) -> Dict[str, Any]:
        """List all available operators with their configurations"""
        if self.use_mock:
            operators = []
            for operator_name in ["VIVO", "CLARO", "OI", "TIM"]:
                merchant = await get_merchant_for_operator(operator_name)
                if merchant:
                    operators.append({
                        "operator_name": operator_name,
                        "merchant_id": merchant.mock_merchant_id,
                        "sofia_agent_id": merchant.sofia_agent_id,
                        "sofia_agent_name": merchant.sofia_agent_name,
                        "supported_payment_methods": merchant.supported_payment_methods,
                        "is_active": merchant.is_active
                    })

            return {
                "success": True,
                "operators": operators,
                "total_operators": len(operators)
            }
        else:
            return {"error": "Real Bemobi integration not implemented for operators"}

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

