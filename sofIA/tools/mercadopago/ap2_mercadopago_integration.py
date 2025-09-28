"""
AP2 Protocol Integration with Mercado Pago

This module demonstrates how to integrate Mercado Pago payment processing
with the AP2 protocol for secure WhatsApp payments through sofIA.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..ap2_protocol.ap2_core import AP2PaymentAgent, PaymentResponse
from ..ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount
from .mercadopago_tool import MercadoPagoTool, MercadoPagoConfig


@dataclass
class AP2MercadoPagoTransaction:
    """Represents a complete AP2-MercadoPago transaction"""
    intent_id: str
    cart_id: str
    mercadopago_preference_id: str
    mercadopago_payment_id: str
    ap2_payment_mandate_id: str
    user_id: str
    amount: float
    currency: str
    status: str
    created_at: str
    payment_method: str


class AP2MercadoPagoIntegration:
    """Main integration class for AP2 protocol and Mercado Pago payments"""
    
    def __init__(self, mercadopago_config: MercadoPagoConfig = None):
        # Initialize AP2 payment agent
        self.ap2_agent = AP2PaymentAgent(
            agent_id="sofia-mercadopago-agent",
            merchant_id="mercadopago-gateway"
        )
        
        # Initialize Mercado Pago tool
        self.mercadopago_tool = MercadoPagoTool()
        
        # Transaction tracking
        self.active_transactions: Dict[str, AP2MercadoPagoTransaction] = {}
    
    async def process_whatsapp_payment_flow(self, user_message: str, user_id: str,
                                          merchant_id: str = "mercadopago_demo_001") -> Dict[str, Any]:
        """
        Process complete WhatsApp payment flow using AP2 protocol and Mercado Pago
        
        This is the main function that coordinates between AP2 mandates and Mercado Pago payments.
        """
        try:
            # Step 1: Create AP2 Intent Mandate from user message
            print(f"🔷 Step 1: Creating AP2 Intent Mandate for user: {user_id}")
            
            intent_mandate = self.ap2_agent.create_intent_mandate(
                user_message=user_message,
                user_id=user_id,
                merchants=[merchant_id],
                requires_confirmation=True
            )
            
            intent_id = f"intent-{user_id}-{datetime.now(timezone.utc).timestamp()}"
            print(f"✅ Intent Mandate created: {intent_id}")
            
            # Step 2: Parse user intent and create payment items
            payment_items = self._parse_payment_intent(user_message)
            if not payment_items:
                return {
                    "success": False,
                    "error": "Could not understand what you want to buy",
                    "suggestion": "Please be more specific about the product and price"
                }
            
            total_amount = sum(item.amount.value for item in payment_items)
            currency = payment_items[0].amount.currency
            
            print(f"💰 Parsed payment: {currency} {total_amount:.2f}")
            
            # Step 3: Create Mercado Pago payment preference
            print(f"🔷 Step 3: Creating Mercado Pago payment preference")
            
            mercadopago_result = await self.mercadopago_tool.execute(
                operation="create_payment_intent",
                merchant_id=merchant_id,
                amount=total_amount,
                currency=currency,
                description=f"WhatsApp purchase via sofIA: {user_message[:50]}...",
                customer_data={
                    "name": f"WhatsApp User",
                    "surname": f"ID {user_id[-4:]}",
                    "email": f"user{user_id[-4:]}@whatsapp.com",
                    "cpf": "11111111111",  # Demo CPF
                    "phone_area": "11",
                    "phone_number": "999999999",
                    "address": {
                        "street": "Rua Demo",
                        "number": "123",
                        "zip_code": "01234567"
                    }
                }
            )
            
            if not mercadopago_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to create Mercado Pago preference: {mercadopago_result.get('error')}",
                    "details": mercadopago_result
                }
            
            preference_id = mercadopago_result["id"]
            print(f"✅ Mercado Pago preference created: {preference_id}")
            
            # Step 4: Create AP2 Cart Mandate
            print(f"🔷 Step 4: Creating AP2 Cart Mandate")
            
            cart_mandate = self.ap2_agent.create_cart_mandate(
                intent_id=intent_id,
                items=payment_items,
                payment_methods=[
                    {
                        "supported_methods": "basic-card",
                        "data": {"networks": ["visa", "mastercard", "elo"], "available": True}
                    },
                    {
                        "supported_methods": "pix",
                        "data": {"type": "pix", "available": True, "instant": True}
                    },
                    {
                        "supported_methods": "boleto",
                        "data": {"type": "boleto", "available": True, "due_days": 3}
                    }
                ]
            )
            
            cart_id = cart_mandate.contents.id
            print(f"✅ Cart Mandate created: {cart_id}")
            
            # Step 5: Store transaction for later completion
            transaction = AP2MercadoPagoTransaction(
                intent_id=intent_id,
                cart_id=cart_id,
                mercadopago_preference_id=preference_id,
                mercadopago_payment_id="",  # Will be set when payment is processed
                ap2_payment_mandate_id="",  # Will be set when payment is confirmed
                user_id=user_id,
                amount=total_amount,
                currency=currency,
                status="waiting_payment",
                created_at=datetime.now(timezone.utc).isoformat(),
                payment_method=""  # Will be set when user chooses
            )
            
            self.active_transactions[cart_id] = transaction
            
            return {
                "success": True,
                "intent_id": intent_id,
                "cart_id": cart_id,
                "mercadopago_preference_id": preference_id,
                "checkout_url": mercadopago_result.get("init_point"),
                "total_amount": total_amount,
                "currency": currency,
                "payment_items": [
                    {
                        "label": item.label,
                        "amount": {"currency": item.amount.currency, "value": item.amount.value}
                    } for item in payment_items
                ],
                "available_payment_methods": ["credit_card", "debit_card", "pix", "boleto"],
                "next_step": "payment_method_selection",
                "message": f"Ready to process payment of {currency} {total_amount:.2f}. Choose your payment method!",
                "user_instructions": {
                    "credit_card": "Reply 'credit card' to pay with credit card",
                    "debit_card": "Reply 'debit card' to pay with debit card", 
                    "pix": "Reply 'pix' for instant PIX payment",
                    "boleto": "Reply 'boleto' for bank slip payment"
                }
            }
            
        except Exception as e:
            print(f"❌ Payment flow error: {str(e)}")
            return {
                "success": False,
                "error": f"Payment flow processing failed: {str(e)}"
            }
    
    async def complete_payment(self, cart_id: str, payment_method: str, 
                             tokenized_payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Complete payment using AP2 protocol and Mercado Pago
        
        This function handles the final payment processing with tokenized data.
        """
        try:
            # Get transaction
            transaction = self.active_transactions.get(cart_id)
            if not transaction:
                return {"success": False, "error": f"Transaction {cart_id} not found"}
            
            print(f"🔷 Completing payment for cart: {cart_id}")
            print(f"💳 Payment method: {payment_method}")
            
            # Prepare payment data based on method
            if not tokenized_payment_data:
                tokenized_payment_data = self._generate_mock_tokenized_data(payment_method)
            
            # Step 1: Process payment through Mercado Pago
            print(f"🔷 Step 1: Processing payment through Mercado Pago")
            
            payment_result = await self.mercadopago_tool.execute(
                operation="process_payment",
                preference_id=transaction.mercadopago_preference_id,
                payment_method=payment_method,
                payment_data=tokenized_payment_data
            )
            
            if not payment_result.get("success"):
                return {
                    "success": False,
                    "error": f"Mercado Pago payment failed: {payment_result.get('error')}",
                    "details": payment_result
                }
            
            print(f"✅ Mercado Pago payment processed: {payment_result['status']}")
            
            # Step 2: Create AP2 Payment Mandate
            print(f"🔷 Step 2: Creating AP2 Payment Mandate")
            
            payment_response = PaymentResponse(
                request_id=transaction.cart_id,
                method_name=payment_method,
                details={
                    "mercadopago_payment_id": payment_result["transaction_id"],
                    "authorization_code": payment_result.get("authorization_code"),
                    "payment_method": payment_method,
                    "payment_method_id": payment_result.get("payment_method_id"),
                    "status_detail": payment_result.get("status_detail"),
                    "tokenized": True  # Indicate that sensitive data was tokenized
                }
            )
            
            payment_mandate = self.ap2_agent.create_payment_mandate(
                cart_id=transaction.cart_id,
                payment_response=payment_response,
                user_id=transaction.user_id,
                consent_proof=f"WhatsApp consent for payment {payment_result['transaction_id']}"
            )
            
            payment_mandate_id = payment_mandate.payment_mandate_contents.payment_mandate_id
            print(f"✅ AP2 Payment Mandate created: {payment_mandate_id}")
            
            # Step 3: Update transaction status
            transaction.mercadopago_payment_id = payment_result["transaction_id"]
            transaction.ap2_payment_mandate_id = payment_mandate_id
            transaction.payment_method = payment_method
            transaction.status = self._map_mercadopago_status(payment_result["status"])
            
            # Step 4: Return complete transaction result
            return {
                "success": True,
                "transaction_id": payment_result["transaction_id"],
                "mercadopago_preference_id": transaction.mercadopago_preference_id,
                "mercadopago_payment_id": payment_result["transaction_id"],
                "ap2_payment_mandate_id": payment_mandate_id,
                "status": transaction.status,
                "status_detail": payment_result.get("status_detail"),
                "amount": payment_result["amount"],
                "currency": payment_result["currency"],
                "payment_method": payment_method,
                "payment_method_id": payment_result.get("payment_method_id"),
                "authorization_code": payment_result.get("authorization_code"),
                "created_at": payment_result["created_at"],
                "ap2_compliant": True,
                "tokenized_payment": True,
                "message": self._get_status_message(transaction.status, payment_method, payment_result["amount"]),
                "point_of_interaction": payment_result.get("point_of_interaction", {})
            }
            
        except Exception as e:
            print(f"❌ Payment completion error: {str(e)}")
            return {
                "success": False,
                "error": f"Payment completion failed: {str(e)}"
            }
    
    async def get_transaction_status(self, cart_id: str) -> Dict[str, Any]:
        """Get current status of a transaction"""
        transaction = self.active_transactions.get(cart_id)
        if not transaction:
            return {"success": False, "error": f"Transaction {cart_id} not found"}
        
        # Get latest status from Mercado Pago if payment exists
        if transaction.mercadopago_payment_id:
            mercadopago_status = await self.mercadopago_tool.execute(
                operation="get_payment_status",
                payment_id=transaction.mercadopago_payment_id
            )
            
            if mercadopago_status.get("success"):
                transaction.status = self._map_mercadopago_status(mercadopago_status["status"])
        
        return {
            "success": True,
            "cart_id": cart_id,
            "mercadopago_preference_id": transaction.mercadopago_preference_id,
            "mercadopago_payment_id": transaction.mercadopago_payment_id,
            "ap2_payment_mandate_id": transaction.ap2_payment_mandate_id,
            "status": transaction.status,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "payment_method": transaction.payment_method,
            "created_at": transaction.created_at,
            "mercadopago_details": mercadopago_status if mercadopago_status.get("success") else None
        }
    
    def _parse_payment_intent(self, user_message: str) -> list[PaymentItem]:
        """Parse user message to extract payment items (simplified for demo)"""
        # In production, you'd use NLP/AI to understand user intent
        # and fetch actual products from merchant catalog
        
        message_lower = user_message.lower()
        
        # Demo items based on common requests
        demo_items = {
            "coffee": {"label": "Café Premium", "value": 8.50},
            "café": {"label": "Café Premium", "value": 8.50},
            "lunch": {"label": "Almoço Executivo", "value": 25.90},
            "almoço": {"label": "Almoço Executivo", "value": 25.90},
            "pizza": {"label": "Pizza Grande", "value": 45.00},
            "burger": {"label": "Hambúrguer Artesanal", "value": 18.90},
            "hambúrguer": {"label": "Hambúrguer Artesanal", "value": 18.90},
            "book": {"label": "Livro Digital", "value": 29.99},
            "livro": {"label": "Livro Digital", "value": 29.99},
            "celular": {"label": "Smartphone", "value": 899.90},
            "smartphone": {"label": "Smartphone", "value": 899.90},
        }
        
        for keyword, item_data in demo_items.items():
            if keyword in message_lower:
                return [PaymentItem(
                    label=item_data["label"],
                    amount=PaymentCurrencyAmount(currency="BRL", value=item_data["value"])
                )]
        
        # Default item if no specific match
        return [PaymentItem(
            label="Produto Genérico",
            amount=PaymentCurrencyAmount(currency="BRL", value=19.90)
        )]
    
    def _generate_mock_tokenized_data(self, payment_method: str) -> Dict[str, Any]:
        """Generate mock tokenized payment data for testing"""
        if payment_method in ["credit_card", "basic-card"]:
            return {
                "token": "MOCK_MP_CARD_TOKEN_123456789",
                "issuer_id": "25",  # Banco do Brasil
                "installments": 1,
                "security_code": "123"
            }
        elif payment_method == "debit_card":
            return {
                "token": "MOCK_MP_DEBIT_TOKEN_987654321",
                "issuer_id": "25",
                "security_code": "123"
            }
        elif payment_method == "pix":
            return {"pix_key": "mock_pix_key@email.com"}
        elif payment_method == "boleto":
            return {"customer_document": "11111111111"}
        else:
            return {}
    
    def _map_mercadopago_status(self, mercadopago_status: str) -> str:
        """Map Mercado Pago status to AP2 status"""
        status_mapping = {
            "pending": "pending",
            "approved": "completed",
            "authorized": "completed",
            "in_process": "processing",
            "in_mediation": "processing",
            "rejected": "failed",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "charged_back": "refunded"
        }
        return status_mapping.get(mercadopago_status.lower(), "unknown")
    
    def _get_status_message(self, status: str, payment_method: str, amount: float) -> str:
        """Get user-friendly status message"""
        if status == "completed":
            return f"✅ Pagamento aprovado! {payment_method.replace('_', ' ').title()} - R$ {amount:.2f}"
        elif status == "pending":
            if payment_method == "pix":
                return f"⏳ PIX gerado! Escaneie o QR Code para pagar R$ {amount:.2f}"
            elif payment_method == "boleto":
                return f"📄 Boleto gerado! Pague até o vencimento - R$ {amount:.2f}"
            else:
                return f"⏳ Pagamento em análise - R$ {amount:.2f}"
        elif status == "processing":
            return f"🔄 Processando pagamento - R$ {amount:.2f}"
        elif status == "failed":
            return f"❌ Pagamento recusado - R$ {amount:.2f}. Tente outro cartão."
        elif status == "cancelled":
            return f"🚫 Pagamento cancelado - R$ {amount:.2f}"
        else:
            return f"ℹ️ Status: {status} - R$ {amount:.2f}"


# Convenience function for easy integration
def create_ap2_mercadopago_integration() -> AP2MercadoPagoIntegration:
    """Create AP2-MercadoPago integration instance"""
    return AP2MercadoPagoIntegration()
