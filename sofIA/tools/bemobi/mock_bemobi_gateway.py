"""
Mock Bemobi Gateway for White-label sofIA Implementation

This module simulates Bemobi API responses using database-stored merchant credentials.
Each telecom operator (VIVO, CLARO, OI, TIM) gets its own mock merchant environment.
"""

import asyncio
import json
import random
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import uuid


@dataclass
class MockMerchantConfig:
    """Mock merchant configuration from database"""
    operator_id: str
    operator_name: str
    mock_merchant_id: str
    mock_api_key: str
    mock_secret_key: str
    sofia_agent_id: str
    sofia_agent_name: str
    supported_payment_methods: List[str]
    mock_success_rate: float
    mock_processing_delay_ms: int
    is_active: bool


class MockBemobiGateway:
    """Mock Bemobi Gateway that simulates API responses per merchant"""

    def __init__(self, db_connection_string: str = None):
        self.merchants: Dict[str, MockMerchantConfig] = {}
        self.payment_intents: Dict[str, Dict] = {}
        self.transactions: Dict[str, Dict] = {}
        self.db_connection = db_connection_string

    async def load_merchants_from_database(self) -> Dict[str, Any]:
        """Load merchant configurations from database"""
        try:
            # In a real implementation, this would connect to PostgreSQL
            # For demo, we'll simulate the database response
            mock_merchants = [
                {
                    "operator_id": "11111111-1111-1111-1111-111111111111",
                    "operator_name": "VIVO",
                    "mock_merchant_id": "MOCK_VIVO_MERCHANT_001",
                    "mock_api_key": "mock_vivo_api_key_123456789",
                    "mock_secret_key": "mock_vivo_secret_987654321",
                    "sofia_agent_id": "sofia-vivo-agent",
                    "sofia_agent_name": "sofIA VIVO Payment Agent",
                    "supported_payment_methods": ["PIX", "CARD", "BOLETO", "VIVO_WALLET"],
                    "mock_success_rate": 0.97,
                    "mock_processing_delay_ms": 1500,
                    "is_active": True
                },
                {
                    "operator_id": "22222222-2222-2222-2222-222222222222",
                    "operator_name": "CLARO",
                    "mock_merchant_id": "MOCK_CLARO_MERCHANT_002",
                    "mock_api_key": "mock_claro_api_key_abcdef123",
                    "mock_secret_key": "mock_claro_secret_fedcba987",
                    "sofia_agent_id": "sofia-claro-agent",
                    "sofia_agent_name": "sofIA CLARO Payment Agent",
                    "supported_payment_methods": ["PIX", "CARD", "BOLETO", "CLARO_PAY"],
                    "mock_success_rate": 0.94,
                    "mock_processing_delay_ms": 2200,
                    "is_active": True
                },
                {
                    "operator_id": "33333333-3333-3333-3333-333333333333",
                    "operator_name": "OI",
                    "mock_merchant_id": "MOCK_OI_MERCHANT_003",
                    "mock_api_key": "mock_oi_api_key_123abc456",
                    "mock_secret_key": "mock_oi_secret_789fed654",
                    "sofia_agent_id": "sofia-oi-agent",
                    "sofia_agent_name": "sofIA OI Payment Agent",
                    "supported_payment_methods": ["PIX", "CARD", "BOLETO", "OI_MONEY"],
                    "mock_success_rate": 0.92,
                    "mock_processing_delay_ms": 2500,
                    "is_active": True
                },
                {
                    "operator_id": "44444444-4444-4444-4444-444444444444",
                    "operator_name": "TIM",
                    "mock_merchant_id": "MOCK_TIM_MERCHANT_004",
                    "mock_api_key": "mock_tim_api_key_def789123",
                    "mock_secret_key": "mock_tim_secret_321abc654",
                    "sofia_agent_id": "sofia-tim-agent",
                    "sofia_agent_name": "sofIA TIM Payment Agent",
                    "supported_payment_methods": ["PIX", "CARD", "BOLETO", "TIM_PAY"],
                    "mock_success_rate": 0.96,
                    "mock_processing_delay_ms": 1800,
                    "is_active": True
                }
            ]

            for merchant_data in mock_merchants:
                merchant = MockMerchantConfig(**merchant_data)
                self.merchants[merchant.mock_merchant_id] = merchant

            return {
                "success": True,
                "merchants_loaded": len(self.merchants),
                "active_merchants": [m.sofia_agent_name for m in self.merchants.values() if m.is_active]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load merchants: {str(e)}"
            }

    async def get_merchant_by_operator(self, operator_name: str) -> Optional[MockMerchantConfig]:
        """Get merchant configuration by operator name"""
        for merchant in self.merchants.values():
            if merchant.operator_name.upper() == operator_name.upper():
                return merchant
        return None

    async def get_merchant_by_id(self, merchant_id: str) -> Optional[MockMerchantConfig]:
        """Get merchant configuration by merchant ID"""
        return self.merchants.get(merchant_id)

    async def create_payment_intent(self, merchant_id: str, amount: float,
                                  currency: str = "BRL", description: str = "",
                                  user_id: str = None) -> Dict[str, Any]:
        """Create a mock payment intent"""
        merchant = await self.get_merchant_by_id(merchant_id)
        if not merchant:
            return {
                "error": f"Merchant {merchant_id} not found",
                "error_code": "MERCHANT_NOT_FOUND"
            }

        if not merchant.is_active:
            return {
                "error": f"Merchant {merchant_id} is not active",
                "error_code": "MERCHANT_INACTIVE"
            }

        # Simulate processing delay
        await asyncio.sleep(merchant.mock_processing_delay_ms / 1000)

        # Generate mock payment intent
        intent_id = f"{merchant.operator_name.lower()}_intent_{uuid.uuid4().hex[:8]}"

        payment_intent = {
            "id": intent_id,
            "merchant_id": merchant_id,
            "operator": merchant.operator_name,
            "amount": amount,
            "currency": currency,
            "description": description,
            "status": "created",
            "supported_payment_methods": merchant.supported_payment_methods,
            "expires_at": (datetime.now(timezone.utc).timestamp() + 900),  # 15 minutes
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "metadata": {
                "sofia_agent_id": merchant.sofia_agent_id,
                "operator_code": merchant.operator_name,
                "mock_intent": True
            }
        }

        self.payment_intents[intent_id] = payment_intent

        return {
            "success": True,
            "payment_intent": payment_intent,
            "next_action": "select_payment_method"
        }

    async def process_payment(self, intent_id: str, payment_method: str,
                            payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a mock payment"""
        intent = self.payment_intents.get(intent_id)
        if not intent:
            return {
                "error": f"Payment intent {intent_id} not found",
                "error_code": "INTENT_NOT_FOUND"
            }

        merchant = await self.get_merchant_by_id(intent["merchant_id"])
        if not merchant:
            return {
                "error": f"Merchant not found for intent {intent_id}",
                "error_code": "MERCHANT_NOT_FOUND"
            }

        # Check if payment method is supported
        if payment_method not in merchant.supported_payment_methods:
            return {
                "error": f"Payment method {payment_method} not supported by {merchant.operator_name}",
                "error_code": "PAYMENT_METHOD_NOT_SUPPORTED",
                "supported_methods": merchant.supported_payment_methods
            }

        # Simulate processing delay
        await asyncio.sleep(merchant.mock_processing_delay_ms / 1000)

        # Simulate success/failure based on merchant's success rate
        is_successful = random.random() < merchant.mock_success_rate

        transaction_id = f"{merchant.operator_name.lower()}_txn_{uuid.uuid4().hex[:8]}"

        if is_successful:
            transaction = {
                "id": transaction_id,
                "intent_id": intent_id,
                "merchant_id": intent["merchant_id"],
                "operator": merchant.operator_name,
                "amount": intent["amount"],
                "currency": intent["currency"],
                "payment_method": payment_method,
                "status": "completed",
                "gateway_reference": f"{merchant.operator_name}_GW_{uuid.uuid4().hex[:6].upper()}",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "receipt_data": {
                    "transaction_id": transaction_id,
                    "operator": merchant.operator_name,
                    "payment_method": payment_method,
                    "amount": f"{intent['currency']} {intent['amount']:.2f}",
                    "status": "Approved",
                    "authorization_code": f"AUTH_{uuid.uuid4().hex[:6].upper()}"
                }
            }

            # Update intent status
            intent["status"] = "completed"
            intent["transaction_id"] = transaction_id

            self.transactions[transaction_id] = transaction

            return {
                "success": True,
                "transaction": transaction,
                "message": f"Payment processed successfully by {merchant.operator_name}"
            }
        else:
            # Simulate different failure reasons
            failure_reasons = [
                ("INSUFFICIENT_FUNDS", "Insufficient funds in account"),
                ("CARD_DECLINED", "Card was declined by issuer"),
                ("NETWORK_ERROR", "Network connection error"),
                ("EXPIRED_PAYMENT_METHOD", "Payment method has expired")
            ]

            error_code, error_message = random.choice(failure_reasons)

            transaction = {
                "id": transaction_id,
                "intent_id": intent_id,
                "merchant_id": intent["merchant_id"],
                "operator": merchant.operator_name,
                "amount": intent["amount"],
                "currency": intent["currency"],
                "payment_method": payment_method,
                "status": "failed",
                "error_code": error_code,
                "error_message": error_message,
                "failed_at": datetime.now(timezone.utc).isoformat()
            }

            # Update intent status
            intent["status"] = "failed"
            intent["error_code"] = error_code
            intent["error_message"] = error_message

            self.transactions[transaction_id] = transaction

            return {
                "success": False,
                "error": error_message,
                "error_code": error_code,
                "transaction": transaction,
                "retry_allowed": error_code in ["NETWORK_ERROR", "INSUFFICIENT_FUNDS"]
            }

    async def get_payment_methods(self, merchant_id: str) -> Dict[str, Any]:
        """Get available payment methods for a merchant"""
        merchant = await self.get_merchant_by_id(merchant_id)
        if not merchant:
            return {
                "error": f"Merchant {merchant_id} not found",
                "error_code": "MERCHANT_NOT_FOUND"
            }

        # Create detailed payment method information
        payment_methods = []
        for method in merchant.supported_payment_methods:
            method_info = {
                "method": method,
                "display_name": self._get_payment_method_display_name(method, merchant.operator_name),
                "description": self._get_payment_method_description(method, merchant.operator_name),
                "fee_percentage": self._get_payment_method_fee(method),
                "processing_time": self._get_payment_method_processing_time(method)
            }
            payment_methods.append(method_info)

        return {
            "success": True,
            "merchant_id": merchant_id,
            "operator": merchant.operator_name,
            "payment_methods": payment_methods,
            "default_currency": "BRL"
        }

    def _get_payment_method_display_name(self, method: str, operator: str) -> str:
        """Get display name for payment method"""
        display_names = {
            "PIX": "PIX",
            "CARD": "Cartão de Crédito/Débito",
            "BOLETO": "Boleto Bancário",
            "VIVO_WALLET": "Vivo Money",
            "CLARO_PAY": "Claro Pay",
            "OI_MONEY": "Oi Money",
            "TIM_PAY": "TIM Pay"
        }
        return display_names.get(method, method)

    def _get_payment_method_description(self, method: str, operator: str) -> str:
        """Get description for payment method"""
        descriptions = {
            "PIX": "Pagamento instantâneo via PIX",
            "CARD": "Pagamento com cartão de crédito ou débito",
            "BOLETO": "Boleto bancário com vencimento em 3 dias úteis",
            "VIVO_WALLET": "Carteira digital Vivo Money",
            "CLARO_PAY": "Pagamento via conta Claro",
            "OI_MONEY": "Carteira digital Oi Money",
            "TIM_PAY": "Pagamento via conta TIM"
        }
        return descriptions.get(method, f"Pagamento via {method}")

    def _get_payment_method_fee(self, method: str) -> float:
        """Get fee percentage for payment method"""
        fees = {
            "PIX": 0.0,
            "CARD": 2.5,
            "BOLETO": 1.0,
            "VIVO_WALLET": 0.5,
            "CLARO_PAY": 0.5,
            "OI_MONEY": 0.5,
            "TIM_PAY": 0.5
        }
        return fees.get(method, 1.0)

    def _get_payment_method_processing_time(self, method: str) -> str:
        """Get processing time for payment method"""
        times = {
            "PIX": "Instantâneo",
            "CARD": "2-3 segundos",
            "BOLETO": "1-2 dias úteis",
            "VIVO_WALLET": "Instantâneo",
            "CLARO_PAY": "Instantâneo",
            "OI_MONEY": "Instantâneo",
            "TIM_PAY": "Instantâneo"
        }
        return times.get(method, "1-2 minutos")

    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get status of a transaction"""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return {
                "error": f"Transaction {transaction_id} not found",
                "error_code": "TRANSACTION_NOT_FOUND"
            }

        return {
            "success": True,
            "transaction": transaction
        }


# Global instance for the application
mock_bemobi_gateway = MockBemobiGateway()


async def initialize_mock_gateway():
    """Initialize the mock gateway with merchant data"""
    result = await mock_bemobi_gateway.load_merchants_from_database()
    return result


# Convenience functions for integration
async def get_merchant_for_operator(operator_name: str) -> Optional[MockMerchantConfig]:
    """Get merchant configuration for an operator"""
    return await mock_bemobi_gateway.get_merchant_by_operator(operator_name)


async def create_operator_payment_intent(operator_name: str, amount: float,
                                       description: str, user_id: str = None) -> Dict[str, Any]:
    """Create payment intent for a specific operator"""
    merchant = await get_merchant_for_operator(operator_name)
    if not merchant:
        return {
            "error": f"No merchant configuration found for operator {operator_name}",
            "error_code": "OPERATOR_NOT_CONFIGURED"
        }

    return await mock_bemobi_gateway.create_payment_intent(
        merchant_id=merchant.mock_merchant_id,
        amount=amount,
        description=description,
        user_id=user_id
    )


async def process_operator_payment(intent_id: str, payment_method: str,
                                 payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment for any operator"""
    return await mock_bemobi_gateway.process_payment(intent_id, payment_method, payment_data)