"""
Bemobi Integration for sofIA Agent

This module handles the integration between sofIA agent and Bemobi payment gateway,
providing seamless WhatsApp payment processing for emerging markets.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass

from .bemobi_tool import BemobiPaymentProcessor, BemobiMerchant
from ..ap2_protocol.ap2_core import AP2PaymentAgent


@dataclass
class SofiaBemobiConfig:
    """Configuration for sofIA-Bemobi integration"""
    bemobi_api_key: str
    bemobi_secret_key: str
    bemobi_base_url: str = "https://api.bemobi.com/v1"
    region: str = "latam"
    supported_currencies: List[str] = None
    webhook_base_url: str = None
    
    def __post_init__(self):
        if self.supported_currencies is None:
            if self.region == "latam":
                self.supported_currencies = ["BRL", "ARS", "CLP", "COP", "MXN"]
            elif self.region == "africa":
                self.supported_currencies = ["NGN", "ZAR", "KES", "GHS", "EGP"]
            elif self.region == "asia":
                self.supported_currencies = ["THB", "IDR", "VND", "PHP", "MYR"]


class SofiaBemobiIntegration:
    """Main integration class for sofIA and Bemobi"""
    
    def __init__(self, config: SofiaBemobiConfig):
        self.config = config
        self.ap2_agent = AP2PaymentAgent(
            agent_id="sofia-bemobi-agent",
            merchant_id="bemobi-gateway"
        )
        
        # Initialize Bemobi processor
        bemobi_config = {
            "api_key": config.bemobi_api_key,
            "secret_key": config.bemobi_secret_key,
            "base_url": config.bemobi_base_url,
            "region": config.region
        }
        self.bemobi_processor = BemobiPaymentProcessor(bemobi_config)
        
        # Merchant registry
        self.registered_merchants: Dict[str, Dict[str, Any]] = {}
    
    async def register_merchant(self, merchant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new merchant with sofIA-Bemobi integration"""
        try:
            merchant = BemobiMerchant(
                merchant_id=merchant_data["merchant_id"],
                store_name=merchant_data["store_name"],
                region=self.config.region,
                currency=merchant_data["currency"],
                api_key=merchant_data["api_key"],
                webhook_url=f"{self.config.webhook_base_url}/webhooks/{merchant_data['merchant_id']}"
            )
            
            self.bemobi_processor.add_merchant(merchant)
            
            # Store merchant info
            self.registered_merchants[merchant_data["merchant_id"]] = {
                "merchant": merchant,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "whatsapp_enabled": True
            }
            
            return {
                "success": True,
                "merchant_id": merchant_data["merchant_id"],
                "store_name": merchant_data["store_name"],
                "region": self.config.region,
                "currency": merchant_data["currency"],
                "whatsapp_payments_enabled": True,
                "message": f"Merchant {merchant_data['store_name']} registered successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Merchant registration failed: {str(e)}"
            }
    
    async def process_whatsapp_payment_flow(self, user_message: str, user_id: str,
                                          merchant_id: str) -> Dict[str, Any]:
        """Process complete WhatsApp payment flow through sofIA and Bemobi"""
        try:
            # Step 1: Create AP2 Intent Mandate
            intent_mandate = self.ap2_agent.create_intent_mandate(
                user_message=user_message,
                user_id=user_id,
                merchants=[merchant_id],
                requires_confirmation=True
            )
            
            intent_id = f"intent-{user_id}-{datetime.now(timezone.utc).timestamp()}"
            
            # Step 2: Parse user intent and create payment items
            payment_items = await self._parse_payment_intent(user_message, merchant_id)
            
            if not payment_items:
                return {
                    "success": False,
                    "error": "Could not parse payment intent from user message",
                    "suggestion": "Please provide more specific details about what you want to buy"
                }
            
            # Step 3: Create Bemobi payment intent
            total_amount = sum(item["amount"]["value"] for item in payment_items)
            currency = payment_items[0]["amount"]["currency"]
            
            bemobi_intent = await self.bemobi_processor.create_payment_intent(
                merchant_id=merchant_id,
                amount=total_amount,
                currency=currency,
                description=f"WhatsApp purchase via sofIA: {user_message[:50]}..."
            )
            
            if "error" in bemobi_intent:
                return bemobi_intent
            
            # Step 4: Create AP2 Cart Mandate
            from ..ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount
            
            ap2_items = []
            for item in payment_items:
                ap2_items.append(PaymentItem(
                    label=item["label"],
                    amount=PaymentCurrencyAmount(
                        currency=item["amount"]["currency"],
                        value=item["amount"]["value"]
                    )
                ))
            
            cart_mandate = self.ap2_agent.create_cart_mandate(
                intent_id=intent_id,
                items=ap2_items
            )
            
            return {
                "success": True,
                "intent_mandate_id": intent_id,
                "cart_mandate_id": cart_mandate.contents.id,
                "bemobi_payment_intent_id": bemobi_intent["id"],
                "total_amount": total_amount,
                "currency": currency,
                "payment_items": payment_items,
                "merchant_id": merchant_id,
                "next_step": "payment_method_selection",
                "message": f"Ready to process payment of {currency} {total_amount:.2f}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Payment flow processing failed: {str(e)}"
            }
    
    async def complete_payment(self, payment_intent_id: str, payment_method: str,
                             payment_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Complete payment through Bemobi and create final AP2 mandate"""
        try:
            # Process payment through Bemobi
            payment_result = await self.bemobi_processor.process_payment(
                payment_intent_id=payment_intent_id,
                payment_method=payment_method,
                payment_data=payment_data
            )
            
            if "error" in payment_result:
                return payment_result
            
            # Create AP2 Payment Mandate
            from ..ap2_protocol.types.payment_request import PaymentResponse
            
            payment_response = PaymentResponse(
                request_id=payment_intent_id,
                method_name=payment_method,
                details=payment_data
            )
            
            # Note: In a real implementation, you'd need the cart_id from the previous step
            # For demo purposes, we'll create a placeholder
            payment_mandate = self.ap2_agent.create_payment_mandate(
                cart_id=payment_intent_id,  # Using payment_intent_id as cart_id for demo
                payment_response=payment_response,
                user_id=user_id
            )
            
            return {
                "success": True,
                "payment_id": payment_result["id"],
                "transaction_id": payment_result.get("transaction_id"),
                "status": payment_result["status"],
                "amount": payment_result["amount"],
                "currency": payment_result["currency"],
                "payment_method": payment_method,
                "payment_mandate_id": payment_mandate.payment_mandate_contents.payment_mandate_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Payment completed successfully!"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Payment completion failed: {str(e)}"
            }
    
    async def _parse_payment_intent(self, user_message: str, merchant_id: str) -> List[Dict[str, Any]]:
        """Parse user message to extract payment items"""
        # This is a simplified parser - in production, you'd use NLP/AI
        # to understand user intent and fetch actual products from merchant catalog
        
        merchant = self.bemobi_processor.get_merchant(merchant_id)
        if not merchant:
            return []
        
        # Demo payment items based on common requests
        demo_items = {
            "coffee": {"label": "Coffee", "value": 5.50},
            "lunch": {"label": "Lunch", "value": 12.00},
            "electronics": {"label": "Electronics", "value": 299.99},
            "clothing": {"label": "Clothing", "value": 45.00},
            "groceries": {"label": "Groceries", "value": 35.50}
        }
        
        message_lower = user_message.lower()
        for keyword, item_data in demo_items.items():
            if keyword in message_lower:
                return [{
                    "label": item_data["label"],
                    "amount": {
                        "currency": merchant.currency,
                        "value": item_data["value"]
                    }
                }]
        
        # Default item if no specific match
        return [{
            "label": "General Purchase",
            "amount": {
                "currency": merchant.currency,
                "value": 25.00
            }
        }]
    
    async def get_merchant_payment_methods(self, merchant_id: str) -> Dict[str, Any]:
        """Get available payment methods for a merchant"""
        merchant = self.bemobi_processor.get_merchant(merchant_id)
        if not merchant:
            return {"error": f"Merchant {merchant_id} not found"}
        
        # Regional payment methods
        regional_methods = {
            "latam": ["card", "pix", "boleto", "bank_transfer"],
            "africa": ["card", "bank_transfer", "mobile_money"],
            "asia": ["card", "bank_transfer", "wallet"]
        }
        
        available_methods = regional_methods.get(self.config.region, ["card"])
        
        return {
            "success": True,
            "merchant_id": merchant_id,
            "region": self.config.region,
            "currency": merchant.currency,
            "available_payment_methods": available_methods,
            "recommended_method": available_methods[0]
        }


def create_sofia_bemobi_integration() -> SofiaBemobiIntegration:
    """Create sofIA-Bemobi integration instance"""
    config = SofiaBemobiConfig(
        bemobi_api_key=os.getenv("BEMOBI_API_KEY", "demo_api_key"),
        bemobi_secret_key=os.getenv("BEMOBI_SECRET_KEY", "demo_secret_key"),
        bemobi_base_url=os.getenv("BEMOBI_BASE_URL", "https://api.bemobi.com/v1"),
        region=os.getenv("BEMOBI_REGION", "latam"),
        webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    )
    
    return SofiaBemobiIntegration(config)

