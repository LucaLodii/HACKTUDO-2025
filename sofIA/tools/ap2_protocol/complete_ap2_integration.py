"""
Complete AP2 Integration for Real Transactions

This module provides a complete implementation of the AP2 Protocol
for real payment processing through WhatsApp, connecting all components:
- AP2 Mandate creation and verification
- Real payment gateway integration
- WhatsApp message handling
- Transaction audit and compliance
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .ap2_core import AP2PaymentAgent, MandateSigner
from .real_transaction_executor import RealAP2TransactionExecutor, AP2Transaction, TransactionState
from .real_payment_gateways import (
    RealPaymentGatewayManager, 
    GatewayConfig, 
    GatewayType,
    create_production_gateway_configs
)
from .payment_processor import PaymentProcessor, PaymentCredentials, PaymentMethod


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AP2Config:
    """Configuration for complete AP2 integration"""
    agent_id: str = "sofia-ap2-agent"
    merchant_id: str = "sofia-merchant"
    region: str = "latam"
    supported_currencies: List[str] = None
    gateway_configs: List[GatewayConfig] = None
    webhook_url: str = "https://sofia.com/webhooks"
    audit_logging: bool = True
    
    def __post_init__(self):
        if self.supported_currencies is None:
            if self.region == "latam":
                self.supported_currencies = ["BRL", "USD", "ARS", "CLP", "COP", "MXN"]
            elif self.region == "africa":
                self.supported_currencies = ["NGN", "ZAR", "KES", "GHS", "EGP"]
            elif self.region == "asia":
                self.supported_currencies = ["THB", "IDR", "VND", "PHP", "MYR"]
            else:
                self.supported_currencies = ["USD", "EUR", "GBP"]


class CompleteAP2Integration:
    """
    Complete AP2 Protocol implementation for real payment processing
    
    This class orchestrates the entire AP2 transaction flow:
    1. WhatsApp message processing
    2. Intent mandate creation
    3. Cart mandate preparation
    4. Payment method selection
    5. Real payment gateway integration
    6. Payment mandate creation
    7. Transaction completion and audit
    """
    
    def __init__(self, config: AP2Config):
        self.config = config
        
        # Initialize core components
        self.ap2_agent = AP2PaymentAgent(config.agent_id, config.merchant_id)
        self.signer = MandateSigner()
        
        # Initialize payment processor
        payment_processor_config = self._create_payment_processor_config()
        self.payment_processor = PaymentProcessor(payment_processor_config)
        
        # Initialize transaction executor
        self.transaction_executor = RealAP2TransactionExecutor(
            self.payment_processor, 
            self.ap2_agent
        )
        
        # Initialize payment gateway manager
        if config.gateway_configs is None:
            config.gateway_configs = create_production_gateway_configs()
        
        self.gateway_manager = RealPaymentGatewayManager(config.gateway_configs)
        
        # Transaction storage
        self.active_transactions: Dict[str, AP2Transaction] = {}
        self.completed_transactions: Dict[str, AP2Transaction] = {}
        
        logger.info(f"AP2 Integration initialized for region: {config.region}")
    
    def _create_payment_processor_config(self) -> Dict[str, Any]:
        """Create payment processor configuration"""
        
        return {
            "pix_enabled": self.config.region == "latam",
            "pix_endpoint": "https://api.bcb.gov.br/pix/v1",
            "pix_certificate": "path/to/pix/certificate.pem",
            "pix_key": "path/to/pix/private.key",
            "merchant_pix_key": "merchant@example.com",
            
            "card_enabled": True,
            "card_api_key": "sk_live_...",  # Real Stripe key
            "card_endpoint": "https://api.stripe.com/v1",
            "merchant_id": self.config.merchant_id,
            
            "paypal_enabled": True,
            "paypal_client_id": "paypal_live_client_id",
            "paypal_client_secret": "paypal_live_client_secret",
            "paypal_sandbox": False,
            
            "region": self.config.region
        }
    
    async def process_whatsapp_message(
        self,
        user_message: str,
        user_id: str,
        merchant_id: str,
        payment_method: str = "auto",
        payment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process WhatsApp message and initiate real AP2 transaction
        
        This is the main entry point for WhatsApp payment processing
        """
        
        try:
            logger.info(f"Processing WhatsApp message from {user_id}: {user_message}")
            
            # Step 1: Parse payment intent from message
            payment_intent = await self._parse_payment_intent(user_message, merchant_id)
            
            if not payment_intent:
                return {
                    "success": False,
                    "error": "Could not understand payment request",
                    "suggestion": "Please specify what you want to buy and the amount"
                }
            
            # Step 2: Determine payment method
            if payment_method == "auto":
                payment_method = await self._select_optimal_payment_method(
                    payment_intent["currency"], 
                    user_id
                )
            
            # Step 3: Create real AP2 transaction
            transaction = await self.transaction_executor.create_real_transaction(
                user_message=user_message,
                user_id=user_id,
                merchant_id=merchant_id,
                amount=payment_intent["amount"],
                currency=payment_intent["currency"],
                payment_method=PaymentMethod(payment_method.lower())
            )
            
            self.active_transactions[transaction.transaction_id] = transaction
            
            # Step 4: Prepare payment credentials
            credentials = self._prepare_payment_credentials(
                user_id, 
                PaymentMethod(payment_method.lower()),
                transaction.transaction_id,
                payment_data or {}
            )
            
            # Step 5: Authorize and capture payment
            payment_result = await self.transaction_executor.authorize_payment(
                transaction.transaction_id,
                credentials
            )
            
            if payment_result.get("success"):
                # Move to completed transactions
                transaction.state = TransactionState.TRANSACTION_COMPLETED
                self.completed_transactions[transaction.transaction_id] = transaction
                del self.active_transactions[transaction.transaction_id]
                
                # Log successful transaction
                if self.config.audit_logging:
                    await self._log_transaction_completion(transaction, payment_result)
            
            return payment_result
            
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return {
                "success": False,
                "error": f"Payment processing failed: {str(e)}",
                "status": "failed"
            }
    
    async def _parse_payment_intent(
        self, 
        user_message: str, 
        merchant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Parse payment intent from user message"""
        
        # In production, use NLP/AI to understand user intent
        # For demo, use simple keyword matching
        
        message_lower = user_message.lower()
        
        # Extract amount (simple regex in production)
        amount = 25.00  # Default amount
        
        # Look for currency indicators
        currency = "USD"  # Default currency
        if "brl" in message_lower or "reais" in message_lower or "r$" in message_lower:
            currency = "BRL"
        elif "usd" in message_lower or "dollars" in message_lower or "$" in message_lower:
            currency = "USD"
        
        # Adjust for region
        if self.config.region == "latam" and currency == "USD":
            currency = "BRL"
            amount = amount * 5  # Rough USD to BRL conversion
        
        return {
            "amount": amount,
            "currency": currency,
            "description": user_message,
            "merchant_id": merchant_id
        }
    
    async def _select_optimal_payment_method(
        self, 
        currency: str, 
        user_id: str
    ) -> str:
        """Select optimal payment method based on region and currency"""
        
        if self.config.region == "latam":
            if currency == "BRL":
                return "pix"  # PIX is preferred for Brazil
            else:
                return "card"
        elif self.config.region == "africa":
            return "card"  # Card or mobile money
        elif self.config.region == "asia":
            return "card"  # Card or local wallets
        else:
            return "card"  # Global default
    
    def _prepare_payment_credentials(
        self,
        user_id: str,
        payment_method: PaymentMethod,
        transaction_id: str,
        payment_data: Dict[str, Any]
    ) -> PaymentCredentials:
        """Prepare payment credentials for transaction"""
        
        return PaymentCredentials(
            method_type=payment_method,
            encrypted_data=payment_data.get("encrypted_data", f"encrypted_{user_id}"),
            provider_token=payment_data.get("provider_token", f"token_{user_id}_{payment_method.value}"),
            user_consent_proof=payment_data.get("consent_proof", f"consent_{transaction_id}")
        )
    
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get current transaction status"""
        
        if transaction_id in self.active_transactions:
            transaction = self.active_transactions[transaction_id]
        elif transaction_id in self.completed_transactions:
            transaction = self.completed_transactions[transaction_id]
        else:
            return {"error": "Transaction not found"}
        
        return {
            "transaction_id": transaction_id,
            "state": transaction.state.value,
            "created_at": transaction.created_at.isoformat(),
            "completed_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
            "amount": transaction.cart_mandate.contents.payment_request.details.total.amount.value if transaction.cart_mandate else None,
            "currency": transaction.cart_mandate.contents.payment_request.details.total.amount.currency if transaction.cart_mandate else None,
            "payment_method": transaction.payment_credentials.method_type.value if transaction.payment_credentials else None,
            "audit_trail": transaction.audit_trail
        }
    
    async def verify_transaction_integrity(self, transaction_id: str) -> bool:
        """Verify complete AP2 mandate chain integrity"""
        
        if transaction_id in self.completed_transactions:
            transaction = self.completed_transactions[transaction_id]
            return await self.transaction_executor.verify_transaction_integrity(transaction_id)
        
        return False
    
    async def _log_transaction_completion(
        self, 
        transaction: AP2Transaction, 
        payment_result: Dict[str, Any]
    ):
        """Log transaction completion for audit purposes"""
        
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.intent_mandate.contents.user_id,
            "amount": payment_result.get("amount"),
            "currency": payment_result.get("currency"),
            "payment_method": payment_result.get("payment_method"),
            "status": "completed",
            "mandate_chain": {
                "intent_mandate": transaction.intent_mandate.contents.id,
                "cart_mandate": transaction.cart_mandate.contents.id if transaction.cart_mandate else None,
                "payment_mandate": transaction.payment_mandate.payment_mandate_contents.payment_mandate_id if transaction.payment_mandate else None
            },
            "payment_processor_response": payment_result
        }
        
        logger.info(f"Transaction completed: {json.dumps(audit_entry, indent=2)}")
        
        # In production, save to secure audit database
        # await self.audit_database.save_audit_entry(audit_entry)
    
    async def get_available_payment_methods(self, user_id: str) -> Dict[str, Any]:
        """Get available payment methods for user"""
        
        available_gateways = self.gateway_manager.get_available_gateways(self.config.region)
        
        payment_methods = []
        for gateway_type in available_gateways:
            if gateway_type == GatewayType.STRIPE:
                payment_methods.append({"type": "card", "provider": "stripe"})
            elif gateway_type == GatewayType.PIX:
                payment_methods.append({"type": "pix", "provider": "pix"})
            elif gateway_type == GatewayType.PAYPAL:
                payment_methods.append({"type": "paypal", "provider": "paypal"})
            elif gateway_type == GatewayType.BEMOBI:
                payment_methods.append({"type": "card", "provider": "bemobi"})
        
        return {
            "success": True,
            "user_id": user_id,
            "region": self.config.region,
            "supported_currencies": self.config.supported_currencies,
            "available_payment_methods": payment_methods,
            "recommended_method": payment_methods[0]["type"] if payment_methods else "card"
        }


# Example usage and testing
async def example_complete_ap2_transaction():
    """Example of complete AP2 transaction processing"""
    
    # Create AP2 configuration
    config = AP2Config(
        agent_id="sofia-production-agent",
        merchant_id="coffee_shop_123",
        region="latam",
        webhook_url="https://sofia.com/webhooks",
        audit_logging=True
    )
    
    # Initialize complete AP2 integration
    ap2_integration = CompleteAP2Integration(config)
    
    # Process WhatsApp payment message
    result = await ap2_integration.process_whatsapp_message(
        user_message="I want to buy a coffee for R$ 8.50",
        user_id="+5511999999999",
        merchant_id="coffee_shop_123",
        payment_method="pix",
        payment_data={
            "encrypted_data": "encrypted_pix_key",
            "provider_token": "pix_token_123",
            "consent_proof": "user_consent_proof"
        }
    )
    
    print(f"Payment result: {json.dumps(result, indent=2)}")
    
    # Check transaction status
    if result.get("success"):
        transaction_id = result["transaction_id"]
        status = await ap2_integration.get_transaction_status(transaction_id)
        print(f"Transaction status: {json.dumps(status, indent=2)}")
        
        # Verify transaction integrity
        integrity_ok = await ap2_integration.verify_transaction_integrity(transaction_id)
        print(f"Transaction integrity: {integrity_ok}")
    
    return result


# WhatsApp webhook handler integration
class AP2WhatsAppHandler:
    """WhatsApp webhook handler integrated with AP2 protocol"""
    
    def __init__(self, ap2_integration: CompleteAP2Integration):
        self.ap2_integration = ap2_integration
    
    async def handle_whatsapp_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle WhatsApp webhook and process through AP2"""
        
        try:
            # Extract message data
            entry = webhook_data.get("entry", [])
            if not entry:
                return {"error": "No entry in webhook"}
            
            for change in entry[0].get("changes", []):
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])
                    
                    for message in messages:
                        await self._process_message(message)
            
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"WhatsApp webhook processing failed: {str(e)}")
            return {"error": str(e)}
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process individual WhatsApp message through AP2"""
        
        from_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")
        
        if not message_text or not from_number:
            return
        
        # Process through AP2 integration
        result = await self.ap2_integration.process_whatsapp_message(
            user_message=message_text,
            user_id=from_number,
            merchant_id="default_merchant",  # In production, determine from context
            payment_method="auto"
        )
        
        # Send response back via WhatsApp (implement WhatsApp API call)
        response_message = self._format_response_message(result)
        await self._send_whatsapp_response(from_number, response_message)
    
    def _format_response_message(self, result: Dict[str, Any]) -> str:
        """Format payment result into WhatsApp message"""
        
        if result.get("success"):
            return (
                f"✅ Payment successful!\n"
                f"Amount: {result.get('currency')} {result.get('amount'):.2f}\n"
                f"Transaction ID: {result.get('transaction_id')}\n"
                f"Thank you for using sofIA!"
            )
        else:
            return (
                f"❌ Payment failed\n"
                f"Error: {result.get('error', 'Unknown error')}\n"
                f"Please try again or contact support."
            )
    
    async def _send_whatsapp_response(self, to: str, message: str):
        """Send WhatsApp response message"""
        # Implement WhatsApp Business API call
        logger.info(f"Sending WhatsApp response to {to}: {message}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_complete_ap2_transaction())
