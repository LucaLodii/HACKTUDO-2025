"""
Mock BEMOBI Implementation for sofIA Agent

This module provides a mock implementation of BEMOBI payment gateway for hackathon
demonstration purposes. It simulates real BEMOBI API responses and behavior.
"""

import os
import json
import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .bemobi_tool import BemobiMerchant


class MockPaymentStatus(Enum):
    """Mock payment statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class MockPaymentIntent:
    """Mock payment intent data"""
    id: str
    merchant_id: str
    amount: float
    currency: str
    description: str
    status: str
    created_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]


@dataclass
class MockPayment:
    """Mock payment data"""
    id: str
    payment_intent_id: str
    amount: float
    currency: str
    status: MockPaymentStatus
    payment_method: str
    transaction_id: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None


class MockBemobiProcessor:
    """Mock BEMOBI payment processor for hackathon demo"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://api.bemobi.com/v1")
        self.api_key = config.get("api_key", "mock_api_key")
        self.secret_key = config.get("secret_key", "mock_secret_key")
        self.region = config.get("region", "latam")
        self.merchants: Dict[str, BemobiMerchant] = {}
        
        # Mock data storage
        self.payment_intents: Dict[str, MockPaymentIntent] = {}
        self.payments: Dict[str, MockPayment] = {}
        
        # Mock configuration
        self.mock_mode = os.getenv("BEMOBI_MOCK_MODE", "true").lower() == "true"
        self.mock_delay = float(os.getenv("BEMOBI_MOCK_DELAY", "0.5"))  # seconds
        self.mock_failure_rate = float(os.getenv("BEMOBI_MOCK_FAILURE_RATE", "0.05"))  # 5% failure rate
        
        print(f"🔧 Mock BEMOBI Processor initialized - Region: {self.region}, Mock Mode: {self.mock_mode}")
    
    def add_merchant(self, merchant: BemobiMerchant):
        """Add a merchant to the mock processor"""
        self.merchants[merchant.merchant_id] = merchant
        print(f"🏪 Mock merchant added: {merchant.store_name} ({merchant.merchant_id})")
    
    def get_merchant(self, merchant_id: str) -> Optional[BemobiMerchant]:
        """Get merchant configuration by ID"""
        return self.merchants.get(merchant_id)
    
    async def _simulate_api_delay(self):
        """Simulate API response delay"""
        if self.mock_delay > 0:
            await asyncio.sleep(self.mock_delay)
    
    async def _should_fail(self) -> bool:
        """Determine if this request should fail (for testing error handling)"""
        return random.random() < self.mock_failure_rate
    
    async def create_payment_intent(self, merchant_id: str, amount: float, 
                                  currency: str, description: str) -> Dict[str, Any]:
        """Create a mock payment intent"""
        await self._simulate_api_delay()
        
        # Check if merchant exists
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        # Simulate failure
        if await self._should_fail():
            return {"error": "Mock API failure: Payment intent creation failed"}
        
        # Create mock payment intent
        intent_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)
        
        mock_intent = MockPaymentIntent(
            id=intent_id,
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            description=description,
            status="requires_payment_method",
            created_at=now,
            expires_at=expires_at,
            metadata={
                "source": "sofia_whatsapp",
                "region": self.region,
                "mock": True
            }
        )
        
        self.payment_intents[intent_id] = mock_intent
        
        print(f"💳 Mock payment intent created: {intent_id} - {currency} {amount:.2f}")
        
        return {
            "id": intent_id,
            "client_secret": f"pi_mock_{intent_id}_secret",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
            "merchant_id": merchant_id,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "metadata": mock_intent.metadata
        }
    
    async def process_payment(self, payment_intent_id: str, payment_method: str,
                            payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process mock payment"""
        await self._simulate_api_delay()
        
        # Check if payment intent exists
        intent = self.payment_intents.get(payment_intent_id)
        if not intent:
            return {"error": f"Payment intent {payment_intent_id} not found"}
        
        # Check if expired
        if datetime.now(timezone.utc) > intent.expires_at:
            return {"error": "Payment intent has expired"}
        
        # Simulate failure
        if await self._should_fail():
            return {"error": "Mock API failure: Payment processing failed"}
        
        # Create mock payment
        payment_id = f"pay_mock_{uuid.uuid4().hex[:16]}"
        transaction_id = f"txn_mock_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        mock_payment = MockPayment(
            id=payment_id,
            payment_intent_id=payment_intent_id,
            amount=intent.amount,
            currency=intent.currency,
            status=MockPaymentStatus.SUCCEEDED,
            payment_method=payment_method,
            transaction_id=transaction_id,
            created_at=now,
            processed_at=now
        )
        
        self.payments[payment_id] = mock_payment
        
        # Update intent status
        intent.status = "succeeded"
        
        print(f"✅ Mock payment processed: {payment_id} - {intent.currency} {intent.amount:.2f} via {payment_method}")
        
        return {
            "id": payment_id,
            "status": "succeeded",
            "amount": intent.amount,
            "currency": intent.currency,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "created_at": now.isoformat(),
            "processed_at": now.isoformat(),
            "metadata": {
                "source": "sofia_whatsapp",
                "region": self.region,
                "mock": True
            }
        }
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get mock payment status"""
        await self._simulate_api_delay()
        
        payment = self.payments.get(payment_id)
        if not payment:
            return {"error": f"Payment {payment_id} not found"}
        
        return {
            "id": payment_id,
            "status": payment.status.value,
            "amount": payment.amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at.isoformat(),
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
            "failure_reason": payment.failure_reason,
            "metadata": {
                "source": "sofia_whatsapp",
                "region": self.region,
                "mock": True
            }
        }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Mock webhook signature verification"""
        # In mock mode, always return True for demo purposes
        if self.mock_mode:
            return True
        
        # Real implementation would verify HMAC signature
        expected_signature = f"mock_signature_{hash(payload) % 10000}"
        return signature == expected_signature
    
    def get_mock_statistics(self) -> Dict[str, Any]:
        """Get mock processor statistics for demo"""
        return {
            "total_intents": len(self.payment_intents),
            "total_payments": len(self.payments),
            "successful_payments": len([p for p in self.payments.values() if p.status == MockPaymentStatus.SUCCEEDED]),
            "failed_payments": len([p for p in self.payments.values() if p.status == MockPaymentStatus.FAILED]),
            "total_merchants": len(self.merchants),
            "region": self.region,
            "mock_mode": self.mock_mode,
            "mock_delay": self.mock_delay,
            "mock_failure_rate": self.mock_failure_rate
        }


class MockBemobiTool:
    """Mock BEMOBI tool for hackathon demonstration"""
    
    def __init__(self):
        self.name = "mock_bemobi_payment"
        self.description = "Mock BEMOBI payment gateway for WhatsApp transactions (hackathon demo)"
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
                        "get_mock_statistics"
                    ],
                    "description": "The mock BEMOBI operation to perform"
                },
                "merchant_id": {
                    "type": "string",
                    "description": "BEMOBI merchant ID"
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
                    "enum": ["card", "pix", "boleto", "bank_transfer", "mobile_money"],
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
        
        # Initialize mock processor
        mock_config = {
            "api_key": os.getenv("BEMOBI_API_KEY", "mock_api_key"),
            "secret_key": os.getenv("BEMOBI_SECRET_KEY", "mock_secret_key"),
            "base_url": os.getenv("BEMOBI_BASE_URL", "https://api.bemobi.com/v1"),
            "region": os.getenv("BEMOBI_REGION", "latam")
        }
        
        self.processor = MockBemobiProcessor(mock_config)
        
        # Add demo merchants
        self._add_demo_merchants()
    
    def _add_demo_merchants(self):
        """Add demo merchants for hackathon"""
        demo_merchants = [
            BemobiMerchant(
                merchant_id="bemobi_demo_001",
                store_name="Café do João",
                region="latam",
                currency="BRL",
                api_key="demo_api_key_001",
                supported_payment_methods=["card", "pix", "boleto"]
            ),
            BemobiMerchant(
                merchant_id="bemobi_demo_002", 
                store_name="Tech Store Lagos",
                region="africa",
                currency="NGN",
                api_key="demo_api_key_002",
                supported_payment_methods=["card", "bank_transfer", "mobile_money"]
            ),
            BemobiMerchant(
                merchant_id="bemobi_demo_003",
                store_name="Bangkok Electronics",
                region="asia", 
                currency="THB",
                api_key="demo_api_key_003",
                supported_payment_methods=["card", "bank_transfer"]
            ),
            BemobiMerchant(
                merchant_id="bemobi_demo_004",
                store_name="Mercado Central",
                region="latam",
                currency="BRL", 
                api_key="demo_api_key_004",
                supported_payment_methods=["pix", "boleto", "card"]
            )
        ]
        
        for merchant in demo_merchants:
            self.processor.add_merchant(merchant)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute mock BEMOBI operation"""
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
            elif operation == "get_mock_statistics":
                return await self._get_mock_statistics(**kwargs)
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"error": f"Mock BEMOBI operation failed: {str(e)}"}
    
    async def _create_payment_intent(self, merchant_id: str, amount: float,
                                   currency: str, description: str, **kwargs) -> Dict[str, Any]:
        """Create mock payment intent"""
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
            "merchant_id": merchant_id,
            "mock": True
        }
    
    async def _process_payment(self, payment_intent_id: str, payment_method: str,
                             payment_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process mock payment"""
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
            "transaction_id": result.get("transaction_id"),
            "mock": True
        }
    
    async def _get_payment_status(self, payment_id: str, **kwargs) -> Dict[str, Any]:
        """Get mock payment status"""
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
            "processed_at": result.get("processed_at"),
            "failure_reason": result.get("failure_reason"),
            "mock": True
        }
    
    async def _add_merchant(self, merchant_id: str, store_name: str, region: str,
                          currency: str, api_key: str, **kwargs) -> Dict[str, Any]:
        """Add a new merchant to mock processor"""
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
            "message": f"Mock merchant {store_name} added successfully",
            "mock": True
        }
    
    async def _get_merchant_info(self, merchant_id: str, **kwargs) -> Dict[str, Any]:
        """Get mock merchant information"""
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
            "webhook_url": merchant.webhook_url,
            "mock": True
        }
    
    async def _get_mock_statistics(self, **kwargs) -> Dict[str, Any]:
        """Get mock processor statistics"""
        stats = self.processor.get_mock_statistics()
        return {
            "success": True,
            "statistics": stats,
            "mock": True
        }


# Initialize mock tool instance
_mock_bemobi_tool = MockBemobiTool()


def mock_bemobi_tool(**kwargs):
    """Mock BEMOBI payment tool function."""
    return _mock_bemobi_tool.execute(**kwargs)
