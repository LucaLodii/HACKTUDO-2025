"""
AP2 Mandate Types

This module contains the mandate type definitions for the Agent Payments Protocol (AP2)
following the official specification.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import datetime

if TYPE_CHECKING:
    from .payment_request import PaymentRequest


class IntentMandate(BaseModel):
    """Intent Mandate per AP2 specification"""
    id: str  # Intent mandate ID
    user_cart_confirmation_required: bool
    natural_language_description: str
    merchants: Optional[List[str]] = None
    intent_expiry: str
    user_id: str  # AP2 spec requires user_id
    max_amount: Optional[float] = None
    user_credential_id: Optional[str] = None


class CartContents(BaseModel):
    """Cart Contents per AP2 specification"""
    id: str
    user_cart_confirmation_required: bool
    payment_request: "PaymentRequest"
    cart_expiry: str
    merchant_name: str
    user_id: str  # AP2 spec requires user_id


class CartMandate(BaseModel):
    """Cart Mandate per AP2 specification"""
    contents: CartContents
    merchant_authorization: str


class PaymentMandateContents(BaseModel):
    """Payment Mandate Contents per AP2 specification"""
    payment_mandate_id: str
    payment_details_id: str
    payment_details_total: "PaymentItem"
    payment_response: "PaymentResponse"
    merchant_agent: str
    timestamp: str
    user_id: str  # AP2 spec requires user_id
    user_credential_id: Optional[str] = None


class PaymentMandate(BaseModel):
    """Payment Mandate per AP2 specification"""
    payment_mandate_contents: PaymentMandateContents
    user_authorization: str
