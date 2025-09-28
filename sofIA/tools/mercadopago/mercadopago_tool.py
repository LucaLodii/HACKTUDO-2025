"""
Mercado Pago Payment Gateway Tool for sofIA

This tool provides integration with Mercado Pago payment gateway for processing
WhatsApp payments through sofIA agent with AP2 protocol compliance.

Follows the same patterns as the PagSeguro integration but uses Mercado Pago API.
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
class MercadoPagoConfig:
    """Configuration for Mercado Pago integration"""
    access_token: str
    public_key: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    environment: str = "sandbox"
    base_url: str = "https://api.mercadopago.com"
    webhook_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'MercadoPagoConfig':
        return cls(
            access_token=os.getenv("MERCADOPAGO_ACCESS_TOKEN"),
            public_key=os.getenv("MERCADOPAGO_PUBLIC_KEY"),
            client_id=os.getenv("MERCADOPAGO_CLIENT_ID"),
            client_secret=os.getenv("MERCADOPAGO_CLIENT_SECRET"),
            environment=os.getenv("MERCADOPAGO_ENVIRONMENT", "sandbox"),
            base_url=os.getenv("MERCADOPAGO_BASE_URL", "https://api.mercadopago.com"),
            webhook_url=os.getenv("MERCADOPAGO_WEBHOOK_URL")
        )


@dataclass
class MercadoPagoMerchant:
    """Mercado Pago merchant configuration"""
    merchant_id: str
    store_name: str
    currency: str = "BRL"
    access_token: str = None
    supported_payment_methods: List[str] = None
    
    def __post_init__(self):
        if self.supported_payment_methods is None:
            self.supported_payment_methods = ["credit_card", "debit_card", "pix", "boleto"]


class MercadoPagoPaymentProcessor:
    """Handles payment processing through Mercado Pago gateway"""
    
    def __init__(self, config: MercadoPagoConfig):
        self.config = config
        self.merchants: Dict[str, MercadoPagoMerchant] = {}
        
        if not self.config.access_token:
            raise ValueError("Mercado Pago access token is required")
    
    def add_merchant(self, merchant: MercadoPagoMerchant):
        """Add a merchant to the Mercado Pago processor"""
        self.merchants[merchant.merchant_id] = merchant
    
    def get_merchant(self, merchant_id: str) -> Optional[MercadoPagoMerchant]:
        """Get merchant configuration by ID"""
        return self.merchants.get(merchant_id)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for Mercado Pago API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.access_token}",
            "X-Idempotency-Key": f"sofia-{datetime.now(timezone.utc).timestamp()}"
        }
    
    async def create_payment_intent(self, merchant_id: str, amount: float,
                                  currency: str, description: str, 
                                  customer_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a payment preference with Mercado Pago"""
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        headers = self._get_headers()
        
        # Create external reference for tracking
        external_reference = f"sofia-{merchant_id}-{datetime.now(timezone.utc).timestamp()}"
        
        # Prepare payment preference
        preference_data = {
            "items": [
                {
                    "id": f"item_{merchant_id}",
                    "title": description,
                    "description": f"Purchase via sofIA WhatsApp Agent: {description}",
                    "quantity": 1,
                    "currency_id": currency,
                    "unit_price": amount
                }
            ],
            "external_reference": external_reference,
            "notification_url": f"{self.config.webhook_url}/mercadopago" if self.config.webhook_url else None,
            "statement_descriptor": merchant.store_name[:22],  # MercadoPago limit
            "metadata": {
                "source": "sofia_whatsapp",
                "merchant_id": merchant_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "expires": True,
            "expiration_date_from": datetime.now(timezone.utc).isoformat(),
            "expiration_date_to": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        }
        
        # Add customer data if provided
        if customer_data:
            preference_data["payer"] = {
                "name": customer_data.get("name", ""),
                "surname": customer_data.get("surname", ""),
                "email": customer_data.get("email", ""),
                "phone": {
                    "area_code": customer_data.get("phone_area", "11"),
                    "number": customer_data.get("phone_number", "999999999")
                },
                "identification": {
                    "type": "CPF",
                    "number": customer_data.get("cpf", "")
                },
                "address": {
                    "street_name": customer_data.get("address", {}).get("street", ""),
                    "street_number": customer_data.get("address", {}).get("number", ""),
                    "zip_code": customer_data.get("address", {}).get("zip_code", "")
                }
            }
        
        try:
            response = requests.post(
                f"{self.config.base_url}/checkout/preferences",
                headers=headers,
                json=preference_data,
                timeout=30
            )
            
            logger.info(f"Mercado Pago preference creation: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "external_reference": result.get("external_reference"),
                    "init_point": result.get("init_point"),  # Checkout URL
                    "sandbox_init_point": result.get("sandbox_init_point"),
                    "status": "created",
                    "amount": amount,
                    "currency": currency,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "expires_at": result.get("expiration_date_to")
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Mercado Pago preference creation failed: {response.status_code}",
                    "details": error_data.get("message", "Unknown error"),
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            logger.error(f"Mercado Pago API request failed: {str(e)}")
            return {"error": f"Mercado Pago preference creation failed: {str(e)}"}
    
    async def process_payment(self, preference_id: str, payment_method: str,
                            payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment through Mercado Pago using tokenized data"""
        headers = self._get_headers()
        
        # Map payment method to Mercado Pago format
        mp_payment_data = self._map_payment_method(payment_method, payment_data)
        
        if "error" in mp_payment_data:
            return mp_payment_data
        
        # Get preference details first
        preference_response = await self._get_preference(preference_id)
        if "error" in preference_response:
            return preference_response
        
        preference = preference_response["preference"]
        
        # Create payment payload
        payment_payload = {
            "transaction_amount": preference["items"][0]["unit_price"],
            "description": preference["items"][0]["title"],
            "external_reference": preference.get("external_reference"),
            "notification_url": f"{self.config.webhook_url}/mercadopago" if self.config.webhook_url else None,
            "metadata": {
                "source": "sofia_whatsapp",
                "preference_id": preference_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add payment method specific data
        payment_payload.update(mp_payment_data)
        
        # Add payer information from preference
        if "payer" in preference:
            payment_payload["payer"] = preference["payer"]
        
        try:
            response = requests.post(
                f"{self.config.base_url}/v1/payments",
                headers=headers,
                json=payment_payload,
                timeout=30
            )
            
            logger.info(f"Mercado Pago payment processing: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "status": result.get("status"),
                    "status_detail": result.get("status_detail"),
                    "amount": result.get("transaction_amount"),
                    "currency": result.get("currency_id"),
                    "payment_method": payment_method,
                    "payment_method_id": result.get("payment_method_id"),
                    "transaction_id": str(result.get("id")),
                    "created_at": result.get("date_created"),
                    "authorization_code": result.get("authorization_code"),
                    "point_of_interaction": result.get("point_of_interaction", {})
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Mercado Pago payment processing failed: {response.status_code}",
                    "details": error_data.get("message", "Unknown error"),
                    "status_code": response.status_code,
                    "mercadopago_response": error_data
                }
                
        except requests.RequestException as e:
            logger.error(f"Mercado Pago payment processing failed: {str(e)}")
            return {"error": f"Mercado Pago payment processing failed: {str(e)}"}
    
    async def _get_preference(self, preference_id: str) -> Dict[str, Any]:
        """Get preference details from Mercado Pago"""
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f"{self.config.base_url}/checkout/preferences/{preference_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "preference": response.json()}
            else:
                return {"error": f"Failed to get preference: {response.status_code}"}
                
        except requests.RequestException as e:
            return {"error": f"Failed to get preference: {str(e)}"}
    
    def _map_payment_method(self, payment_method: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map AP2 payment method to Mercado Pago format"""
        
        if payment_method.lower() in ["credit_card", "basic-card"]:
            # Handle tokenized credit card payment
            if "token" not in payment_data:
                return {"error": "Credit card token is required"}
            
            return {
                "payment_method_id": "visa",  # This should be determined from token
                "token": payment_data["token"],
                "installments": payment_data.get("installments", 1),
                "issuer_id": payment_data.get("issuer_id"),
                "capture": True
            }
        
        elif payment_method.lower() == "debit_card":
            if "token" not in payment_data:
                return {"error": "Debit card token is required"}
            
            return {
                "payment_method_id": "debvisa",  # This should be determined from token
                "token": payment_data["token"],
                "capture": True
            }
        
        elif payment_method.lower() == "pix":
            return {
                "payment_method_id": "pix"
            }
        
        elif payment_method.lower() == "boleto":
            return {
                "payment_method_id": "bolbradesco"  # Can be other boleto types
            }
        
        else:
            return {"error": f"Unsupported payment method: {payment_method}"}
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status from Mercado Pago"""
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f"{self.config.base_url}/v1/payments/{payment_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "status": result.get("status"),
                    "status_detail": result.get("status_detail"),
                    "amount": result.get("transaction_amount"),
                    "currency": result.get("currency_id"),
                    "payment_method_id": result.get("payment_method_id"),
                    "created_at": result.get("date_created"),
                    "approved_at": result.get("date_approved"),
                    "last_modified": result.get("date_last_updated")
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Mercado Pago status check failed: {response.status_code}",
                    "details": error_data.get("message", "Unknown error")
                }
                
        except requests.RequestException as e:
            logger.error(f"Mercado Pago status check failed: {str(e)}")
            return {"error": f"Mercado Pago status check failed: {str(e)}"}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Mercado Pago webhook signature"""
        if not self.config.client_secret:
            return False
        
        try:
            # Mercado Pago uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.config.client_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False


class MercadoPagoTool:
    """Tool for handling Mercado Pago payment gateway operations with AP2 compliance"""

    def __init__(self):
        self.name = "mercadopago_payment"
        self.description = "Process payments through Mercado Pago payment gateway for WhatsApp transactions with AP2 protocol compliance"
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
                    "description": "The Mercado Pago operation to perform"
                },
                "merchant_id": {
                    "type": "string",
                    "description": "Mercado Pago merchant ID"
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
                "preference_id": {
                    "type": "string",
                    "description": "Mercado Pago preference ID"
                },
                "payment_id": {
                    "type": "string",
                    "description": "Mercado Pago payment ID"
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

        # Initialize Mercado Pago processor
        self.use_mock = os.getenv("MERCADOPAGO_USE_MOCK", "true").lower() == "true"
        
        if not self.use_mock:
            try:
                self.config = MercadoPagoConfig.from_env()
                self.processor = MercadoPagoPaymentProcessor(self.config)
                self._add_demo_merchants()
            except Exception as e:
                logger.error(f"Failed to initialize Mercado Pago processor: {str(e)}")
                self.use_mock = True
        
        if self.use_mock:
            logger.info("Using Mercado Pago mock mode for development")
    
    def _add_demo_merchants(self):
        """Add demo merchants for testing"""
        demo_merchants = [
            MercadoPagoMerchant(
                merchant_id="mercadopago_demo_001",
                store_name="Café Brasileiro",
                currency="BRL",
                access_token=self.config.access_token,
                supported_payment_methods=["credit_card", "debit_card", "pix", "boleto"]
            ),
            MercadoPagoMerchant(
                merchant_id="mercadopago_demo_002",
                store_name="Loja Online BR",
                currency="BRL",
                access_token=self.config.access_token,
                supported_payment_methods=["credit_card", "pix"]
            )
        ]
        
        for merchant in demo_merchants:
            self.processor.add_merchant(merchant)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Mercado Pago operation with AP2 compliance"""
        operation = kwargs.get("operation")
        
        try:
            if self.use_mock:
                return await self._execute_mock_operation(**kwargs)
            
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
            logger.error(f"Mercado Pago operation failed: {str(e)}")
            return {"error": f"Mercado Pago operation failed: {str(e)}"}
    
    async def _execute_mock_operation(self, **kwargs) -> Dict[str, Any]:
        """Execute mock operations for development"""
        operation = kwargs.get("operation")
        if operation == "create_payment_intent":
            return {
                "success": True,
                "id": f"MOCK_PREF_{datetime.now(timezone.utc).timestamp()}",
                "external_reference": f"sofia-mock-{kwargs.get('merchant_id', 'demo')}",
                "init_point": "https://sandbox.mercadopago.com.br/checkout/mock",
                "status": "created",
                "amount": kwargs.get("amount", 0),
                "currency": kwargs.get("currency", "BRL"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "mock": True
            }
        
        elif operation == "process_payment":
            return {
                "success": True,
                "id": f"MOCK_PAYMENT_{datetime.now(timezone.utc).timestamp()}",
                "status": "approved",
                "status_detail": "accredited",
                "amount": 25.99,  # Mock amount
                "currency": "BRL",
                "payment_method": kwargs.get("payment_method", "credit_card"),
                "payment_method_id": "visa",
                "transaction_id": f"TXN_{datetime.now(timezone.utc).timestamp()}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "authorization_code": "MOCK_AUTH_123456",
                "mock": True
            }
        
        elif operation == "get_payment_status":
            return {
                "success": True,
                "id": kwargs.get("payment_id", "MOCK_PAYMENT"),
                "status": "approved",
                "status_detail": "accredited",
                "amount": 25.99,
                "currency": "BRL",
                "payment_method_id": "visa",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "mock": True
            }
        
        else:
            return {"error": f"Mock operation {operation} not implemented"}
    
    async def _create_payment_intent(self, merchant_id: str, amount: float,
                                   description: str, currency: str = "BRL",
                                   customer_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Create payment intent with Mercado Pago"""
        result = await self.processor.create_payment_intent(
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            description=description,
            customer_data=customer_data
        )
        
        return result
    
    async def _process_payment(self, preference_id: str, payment_method: str,
                             payment_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process payment through Mercado Pago"""
        result = await self.processor.process_payment(
            preference_id=preference_id,
            payment_method=payment_method,
            payment_data=payment_data
        )
        
        return result
    
    async def _get_payment_status(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """Get payment status from Mercado Pago"""
        result = await self.processor.get_payment_status(payment_id)
        return result
    
    async def _add_merchant(self, merchant_id: str, store_name: str,
                          currency: str = "BRL", **kwargs) -> Dict[str, Any]:
        """Add a new merchant to Mercado Pago processor"""
        merchant = MercadoPagoMerchant(
            merchant_id=merchant_id,
            store_name=store_name,
            currency=currency,
            access_token=self.config.access_token,
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
        """Get available payment methods for Mercado Pago"""
        return {
            "success": True,
            "payment_methods": [
                {
                    "method": "credit_card",
                    "name": "Cartão de Crédito",
                    "description": "Visa, Mastercard, Elo, American Express",
                    "supports_installments": True,
                    "max_installments": 12
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
_mercadopago_tool = MercadoPagoTool()


def mercadopago_tool(**kwargs):
    """Mercado Pago payment tool function."""
    return _mercadopago_tool.execute(**kwargs)
