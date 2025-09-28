"""
PagSeguro Payment Gateway Tool for sofIA

This tool provides integration with PagSeguro (PagBank) payment gateway for processing
WhatsApp payments through sofIA agent with AP2 protocol compliance.

Follows the same patterns as the existing BEMOBI integration.
"""

import os
import json
import requests
import hashlib
import hmac
import base64
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PagSeguroConfig:
    """Configuration for PagSeguro integration"""
    client_id: str
    client_secret: str
    access_token: str
    environment: str = "sandbox"
    base_url: str = "https://sandbox.api.pagseguro.com"
    webhook_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'PagSeguroConfig':
        return cls(
            client_id=os.getenv("PAGSEGURO_CLIENT_ID"),
            client_secret=os.getenv("PAGSEGURO_CLIENT_SECRET"),
            access_token=os.getenv("PAGSEGURO_ACCESS_TOKEN"),
            environment=os.getenv("PAGSEGURO_ENVIRONMENT", "sandbox"),
            base_url=os.getenv("PAGSEGURO_BASE_URL", "https://sandbox.api.pagseguro.com"),
            webhook_url=os.getenv("PAGSEGURO_WEBHOOK_URL")
        )


@dataclass
class PagSeguroMerchant:
    """PagSeguro merchant configuration"""
    merchant_id: str
    store_name: str
    currency: str = "BRL"
    api_key: str = None
    supported_payment_methods: List[str] = None
    
    def __post_init__(self):
        if self.supported_payment_methods is None:
            self.supported_payment_methods = ["credit_card", "debit_card", "pix", "boleto"]


class PagSeguroPaymentProcessor:
    """Handles payment processing through PagSeguro gateway"""
    
    def __init__(self, config: PagSeguroConfig):
        self.config = config
        self.merchants: Dict[str, PagSeguroMerchant] = {}
        
        if not self.config.access_token:
            raise ValueError("PagSeguro access token is required")
    
    def add_merchant(self, merchant: PagSeguroMerchant):
        """Add a merchant to the PagSeguro processor"""
        self.merchants[merchant.merchant_id] = merchant
    
    def get_merchant(self, merchant_id: str) -> Optional[PagSeguroMerchant]:
        """Get merchant configuration by ID"""
        return self.merchants.get(merchant_id)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for PagSeguro API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}",
            "Accept": "application/vnd.pagseguro.com.br.v1+json;charset=ISO-8859-1"
        }
    
    async def create_payment_intent(self, merchant_id: str, amount: float,
                                  currency: str, description: str, 
                                  customer_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a payment intent with PagSeguro"""
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        headers = self._get_headers()
        
        # PagSeguro uses centavos (multiply by 100)
        amount_centavos = int(amount * 100)
        
        payload = {
            "reference_id": f"sofia-{merchant_id}-{datetime.now(timezone.utc).timestamp()}",
            "description": description,
            "amount": {
                "value": amount_centavos,
                "currency": currency
            },
            "payment_method": {
                "type": "CREDIT_CARD",
                "installments": 1,
                "capture": True,
                "soft_descriptor": merchant.store_name[:13]  # PagSeguro limit
            },
            "notification_urls": [
                f"{self.config.webhook_url}/pagseguro"
            ] if self.config.webhook_url else [],
            "metadata": {
                "source": "sofia_whatsapp",
                "merchant_id": merchant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add customer data if provided (required for some payment methods)
        if customer_data:
            payload["customer"] = {
                "name": customer_data.get("name", ""),
                "email": customer_data.get("email", ""),
                "tax_id": customer_data.get("cpf", ""),
                "phone": {
                    "country": "+55",
                    "area": customer_data.get("phone_area", "11"),
                    "number": customer_data.get("phone_number", ""),
                    "type": "MOBILE"
                }
            }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/orders",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"PagSeguro payment intent request: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "reference_id": result.get("reference_id"),
                    "status": result.get("status"),
                    "amount": amount,
                    "currency": currency,
                    "created_at": result.get("created_at"),
                    "links": result.get("links", [])
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"PagSeguro payment intent creation failed: {response.status_code}",
                    "details": error_data.get("error_messages", []),
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            logger.error(f"PagSeguro API request failed: {str(e)}")
            return {"error": f"PagSeguro payment intent creation failed: {str(e)}"}
    
    async def process_payment(self, order_id: str, payment_method: str,
                            payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through PagSeguro using tokenized data"""
        headers = self._get_headers()
        
        # Map payment method to PagSeguro format
        pagseguro_payment_method = self._map_payment_method(payment_method, payment_data)
        
        if "error" in pagseguro_payment_method:
            return pagseguro_payment_method
        
        payload = {
            "reference_id": f"payment-{order_id}-{datetime.now(timezone.utc).timestamp()}",
            "payment_method": pagseguro_payment_method,
            "metadata": {
                "source": "sofia_whatsapp",
                "original_order_id": order_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/orders/{order_id}/pay",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"PagSeguro payment processing: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "status": result.get("status"),
                    "amount": result.get("amount", {}).get("value", 0) / 100,  # Convert from centavos
                    "currency": result.get("amount", {}).get("currency", "BRL"),
                    "payment_method": payment_method,
                    "transaction_id": result.get("id"),
                    "created_at": result.get("created_at"),
                    "authorization_code": result.get("authorization_code")
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"PagSeguro payment processing failed: {response.status_code}",
                    "details": error_data.get("error_messages", []),
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            logger.error(f"PagSeguro payment processing failed: {str(e)}")
            return {"error": f"PagSeguro payment processing failed: {str(e)}"}
    
    def _map_payment_method(self, payment_method: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map AP2 payment method to PagSeguro format"""
        
        if payment_method.lower() in ["credit_card", "basic-card"]:
            # Handle tokenized credit card payment
            if "token" not in payment_data:
                return {"error": "Credit card token is required"}
            
            return {
                "type": "CREDIT_CARD",
                "installments": payment_data.get("installments", 1),
                "capture": True,
                "card": {
                    "encrypted": payment_data["token"],  # Use tokenized card data
                    "security_code": payment_data.get("cvv_token"),  # Tokenized CVV
                    "holder": {
                        "name": payment_data.get("holder_name", "")
                    }
                }
            }
        
        elif payment_method.lower() == "debit_card":
            if "token" not in payment_data:
                return {"error": "Debit card token is required"}
            
            return {
                "type": "DEBIT_CARD",
                "capture": True,
                "card": {
                    "encrypted": payment_data["token"],
                    "security_code": payment_data.get("cvv_token"),
                    "holder": {
                        "name": payment_data.get("holder_name", "")
                    }
                }
            }
        
        elif payment_method.lower() == "pix":
            return {
                "type": "PIX",
                "pix": {
                    "expiration_date": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
                }
            }
        
        elif payment_method.lower() == "boleto":
            return {
                "type": "BOLETO",
                "boleto": {
                    "due_date": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "instruction_lines": {
                        "line_1": "Pagamento processado via sofIA",
                        "line_2": "Não receber após o vencimento"
                    }
                }
            }
        
        else:
            return {"error": f"Unsupported payment method: {payment_method}"}
    
    async def get_payment_status(self, order_id: str) -> Dict[str, Any]:
        """Get payment status from PagSeguro"""
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f"{self.config.base_url}/orders/{order_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "status": result.get("status"),
                    "amount": result.get("amount", {}).get("value", 0) / 100,
                    "currency": result.get("amount", {}).get("currency", "BRL"),
                    "created_at": result.get("created_at"),
                    "paid_at": result.get("paid_at"),
                    "charges": result.get("charges", [])
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"PagSeguro status check failed: {response.status_code}",
                    "details": error_data.get("error_messages", [])
                }
                
        except requests.RequestException as e:
            logger.error(f"PagSeguro status check failed: {str(e)}")
            return {"error": f"PagSeguro status check failed: {str(e)}"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify PagSeguro webhook signature"""
        if not self.config.client_secret:
            return False
        
        try:
            # PagSeguro uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.config.client_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False


class PagSeguroTool:
    """Tool for handling PagSeguro payment gateway operations with AP2 compliance"""

    def __init__(self):
        self.name = "pagseguro_payment"
        self.description = "Process payments through PagSeguro (PagBank) payment gateway for WhatsApp transactions with AP2 protocol compliance"
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
                        "get_payment_methods"
                    ],
                    "description": "The PagSeguro operation to perform"
                },
                "merchant_id": {
                    "type": "string",
                    "description": "PagSeguro merchant ID"
                },
                "amount": {
                    "type": "number",
                    "description": "Payment amount in BRL"
                },
                "currency": {
                    "type": "string",
                    "description": "Payment currency (default: BRL)",
                    "default": "BRL"
                },
                "description": {
                    "type": "string",
                    "description": "Payment description"
                },
                "order_id": {
                    "type": "string",
                    "description": "PagSeguro order ID"
                },
                "payment_method": {
                    "type": "string",
                    "enum": ["credit_card", "debit_card", "pix", "boleto", "basic-card"],
                    "description": "Payment method"
                },
                "payment_data": {
                    "type": "object",
                    "description": "Tokenized payment method data from AP2"
                },
                "customer_data": {
                    "type": "object",
                    "description": "Customer information for payment processing"
                },
                "user_id": {
                    "type": "string",
                    "description": "User ID for payment tracking"
                }
            },
            "required": ["operation"]
        }

        # Initialize PagSeguro processor
        self.use_mock = os.getenv("PAGSEGURO_USE_MOCK", "true").lower() == "true"
        
        if not self.use_mock:
            try:
                self.config = PagSeguroConfig.from_env()
                self.processor = PagSeguroPaymentProcessor(self.config)
                self._add_demo_merchants()
            except Exception as e:
                logger.error(f"Failed to initialize PagSeguro processor: {str(e)}")
                self.use_mock = True
        
        if self.use_mock:
            logger.info("Using PagSeguro mock mode for development")
    
    def _add_demo_merchants(self):
        """Add demo merchants for testing"""
        demo_merchants = [
            PagSeguroMerchant(
                merchant_id="pagseguro_demo_001",
                store_name="Loja Demo SP",
                currency="BRL",
                supported_payment_methods=["credit_card", "debit_card", "pix", "boleto"]
            ),
            PagSeguroMerchant(
                merchant_id="pagseguro_demo_002",
                store_name="E-commerce RJ",
                currency="BRL", 
                supported_payment_methods=["credit_card", "pix"]
            )
        ]
        
        for merchant in demo_merchants:
            self.processor.add_merchant(merchant)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute PagSeguro operation with AP2 compliance"""
        operation = kwargs.get("operation")
        
        try:
            if self.use_mock:
                return await self._execute_mock_operation(operation, **kwargs)
            
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
            elif operation == "get_payment_methods":
                return await self._get_payment_methods(**kwargs)
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"PagSeguro operation failed: {str(e)}")
            return {"error": f"PagSeguro operation failed: {str(e)}"}
    
    async def _execute_mock_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute mock operations for development"""
        if operation == "create_payment_intent":
            return {
                "success": True,
                "id": f"MOCK_ORDER_{datetime.now(timezone.utc).timestamp()}",
                "reference_id": f"sofia-mock-{kwargs.get('merchant_id', 'demo')}",
                "status": "WAITING",
                "amount": kwargs.get("amount", 0),
                "currency": kwargs.get("currency", "BRL"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "mock": True
            }
        
        elif operation == "process_payment":
            return {
                "success": True,
                "id": f"MOCK_PAYMENT_{datetime.now(timezone.utc).timestamp()}",
                "status": "PAID",
                "amount": 25.99,  # Mock amount
                "currency": "BRL",
                "payment_method": kwargs.get("payment_method", "credit_card"),
                "transaction_id": f"TXN_{datetime.now(timezone.utc).timestamp()}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "authorization_code": "MOCK_AUTH_123456",
                "mock": True
            }
        
        elif operation == "get_payment_status":
            return {
                "success": True,
                "id": kwargs.get("order_id", "MOCK_ORDER"),
                "status": "PAID",
                "amount": 25.99,
                "currency": "BRL",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "mock": True
            }
        
        else:
            return {"error": f"Mock operation {operation} not implemented"}
    
    async def _create_payment_intent(self, merchant_id: str, amount: float,
                                   description: str, currency: str = "BRL",
                                   customer_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Create payment intent with PagSeguro"""
        result = await self.processor.create_payment_intent(
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            description=description,
            customer_data=customer_data
        )
        
        return result
    
    async def _process_payment(self, order_id: str, payment_method: str,
                             payment_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process payment through PagSeguro"""
        result = await self.processor.process_payment(
            order_id=order_id,
            payment_method=payment_method,
            payment_data=payment_data
        )
        
        return result
    
    async def _get_payment_status(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Get payment status from PagSeguro"""
        result = await self.processor.get_payment_status(order_id)
        return result
    
    async def _add_merchant(self, merchant_id: str, store_name: str,
                          currency: str = "BRL", **kwargs) -> Dict[str, Any]:
        """Add a new merchant to PagSeguro processor"""
        merchant = PagSeguroMerchant(
            merchant_id=merchant_id,
            store_name=store_name,
            currency=currency,
            supported_payment_methods=kwargs.get("supported_payment_methods", 
                                                ["credit_card", "debit_card", "pix", "boleto"])
        )
        
        self.processor.add_merchant(merchant)
        
        return {
            "success": True,
            "merchant_id": merchant_id,
            "store_name": store_name,
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
            "currency": merchant.currency,
            "supported_payment_methods": merchant.supported_payment_methods
        }
    
    async def _get_payment_methods(self, **kwargs) -> Dict[str, Any]:
        """Get available payment methods for PagSeguro"""
        return {
            "success": True,
            "payment_methods": [
                {
                    "method": "credit_card",
                    "name": "Cartão de Crédito",
                    "description": "Visa, Mastercard, Elo, American Express",
                    "supports_installments": True
                },
                {
                    "method": "debit_card", 
                    "name": "Cartão de Débito",
                    "description": "Débito à vista",
                    "supports_installments": False
                },
                {
                    "method": "pix",
                    "name": "PIX",
                    "description": "Pagamento instantâneo via PIX",
                    "supports_installments": False
                },
                {
                    "method": "boleto",
                    "name": "Boleto Bancário",
                    "description": "Boleto com vencimento em 3 dias",
                    "supports_installments": False
                }
            ],
            "currency": "BRL",
            "country": "BR"
        }


# Initialize tool instance
_pagseguro_tool = PagSeguroTool()


def pagseguro_tool(**kwargs):
    """PagSeguro payment tool function."""
    return _pagseguro_tool.execute(**kwargs)
