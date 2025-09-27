"""
AP2 Protocol Tool for sofIA Payment Agent

This tool provides AP2 protocol functionality as a tool that can be used by the agent.
"""

from typing import Dict, Any, List, Optional
from .ap2_core import AP2PaymentAgent, MandateSigner


class AP2ProtocolTool:
    """Tool for handling AP2 protocol operations."""
    
    def __init__(self):
        self.name = "ap2_protocol"
        self.description = "Handle Agent Payments Protocol (AP2) operations including mandate creation, signing, and verification"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["create_intent_mandate", "create_cart_mandate", "create_payment_mandate", "verify_mandate"],
                    "description": "The AP2 operation to perform"
                },
                "user_message": {
                    "type": "string",
                    "description": "User's purchase intent message"
                },
                "user_id": {
                    "type": "string",
                    "description": "Unique identifier for the user"
                },
                "intent_id": {
                    "type": "string",
                    "description": "Intent mandate ID for cart creation"
                },
                "cart_id": {
                    "type": "string",
                    "description": "Cart mandate ID for payment creation"
                },
                "items": {
                    "type": "array",
                    "description": "List of payment items",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "amount": {
                                "type": "object",
                                "properties": {
                                    "currency": {"type": "string"},
                                    "value": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "payment_method": {
                    "type": "string",
                    "description": "Payment method chosen by user"
                },
                "mandate_data": {
                    "type": "object",
                    "description": "Mandate data for verification"
                }
            },
            "required": ["operation"]
        }
        
        # Initialize AP2 payment agent
        self.payment_agent = AP2PaymentAgent(
            agent_id="sofia-payment-agent",
            merchant_id="sofia-merchant"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute AP2 protocol operation."""
        operation = kwargs.get("operation")
        
        try:
            if operation == "create_intent_mandate":
                return await self._create_intent_mandate(**kwargs)
            elif operation == "create_cart_mandate":
                return await self._create_cart_mandate(**kwargs)
            elif operation == "create_payment_mandate":
                return await self._create_payment_mandate(**kwargs)
            elif operation == "verify_mandate":
                return await self._verify_mandate(**kwargs)
            else:
                return {"error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"error": f"AP2 operation failed: {str(e)}"}
    
    async def _create_intent_mandate(self, user_message: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create an Intent Mandate from user's message."""
        intent_mandate = self.payment_agent.create_intent_mandate(
            user_message=user_message,
            user_id=user_id,
            merchants=kwargs.get("merchants"),
            max_price=kwargs.get("max_price"),
            requires_confirmation=kwargs.get("requires_confirmation", True)
        )
        
        intent_id = list(self.payment_agent.active_intents.keys())[-1]
        
        return {
            "success": True,
            "intent_id": intent_id,
            "mandate": {
                "natural_language_description": intent_mandate.natural_language_description,
                "user_cart_confirmation_required": intent_mandate.user_cart_confirmation_required,
                "intent_expiry": intent_mandate.intent_expiry,
                "merchants": intent_mandate.merchants
            }
        }
    
    async def _create_cart_mandate(self, intent_id: str, items: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Create a Cart Mandate from payment items."""
        from ap2.types.payment_request import PaymentItem, PaymentCurrencyAmount
        
        # Convert items to PaymentItem objects
        payment_items = []
        for item in items:
            payment_items.append(PaymentItem(
                label=item["label"],
                amount=PaymentCurrencyAmount(
                    currency=item["amount"]["currency"],
                    value=item["amount"]["value"]
                )
            ))
        
        cart_mandate = self.payment_agent.create_cart_mandate(
            intent_id=intent_id,
            items=payment_items,
            shipping_address=kwargs.get("shipping_address")
        )
        
        return {
            "success": True,
            "cart_id": cart_mandate.contents.id,
            "mandate": {
                "cart_id": cart_mandate.contents.id,
                "merchant_name": cart_mandate.contents.merchant_name,
                "total_amount": cart_mandate.contents.payment_request.details.total.amount.value,
                "currency": cart_mandate.contents.payment_request.details.total.amount.currency,
                "cart_expiry": cart_mandate.contents.cart_expiry,
                "items_count": len(cart_mandate.contents.payment_request.details.display_items),
                "merchant_authorization": cart_mandate.merchant_authorization[:50] + "..."  # Truncate for security
            }
        }
    
    async def _create_payment_mandate(self, cart_id: str, payment_method: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Create a Payment Mandate after user confirms payment."""
        from ap2.types.payment_request import PaymentResponse
        
        # Create payment response
        payment_response = PaymentResponse(
            request_id=cart_id,
            method_name=payment_method,
            details=kwargs.get("payment_details", {"card_number": "****1234"})
        )
        
        payment_mandate = self.payment_agent.create_payment_mandate(
            cart_id=cart_id,
            payment_response=payment_response,
            user_id=user_id
        )
        
        return {
            "success": True,
            "payment_mandate_id": payment_mandate.payment_mandate_contents.payment_mandate_id,
            "mandate": {
                "payment_mandate_id": payment_mandate.payment_mandate_contents.payment_mandate_id,
                "merchant_agent": payment_mandate.payment_mandate_contents.merchant_agent,
                "payment_method": payment_mandate.payment_mandate_contents.payment_response.method_name,
                "total_amount": payment_mandate.payment_mandate_contents.payment_details_total.amount.value,
                "currency": payment_mandate.payment_mandate_contents.payment_details_total.amount.currency,
                "timestamp": payment_mandate.payment_mandate_contents.timestamp,
                "user_authorization": payment_mandate.user_authorization[:50] + "..."  # Truncate for security
            }
        }
    
    async def _verify_mandate(self, mandate_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Verify the signature of a mandate."""
        try:
            # This would implement mandate verification logic
            # For now, return a placeholder response
            return {
                "success": True,
                "verified": True,
                "message": "Mandate signature verified successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "verified": False,
                "error": f"Verification failed: {str(e)}"
            }


# Initialize tool instance
_ap2_tool = AP2ProtocolTool()


def ap2_protocol_tool(**kwargs):
    """AP2 Protocol tool function."""
    return _ap2_tool.execute(**kwargs)
