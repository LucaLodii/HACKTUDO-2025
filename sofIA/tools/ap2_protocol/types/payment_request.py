"""
AP2 Payment Request Types

This module contains the payment request type definitions for the Agent Payments Protocol (AP2)
following the official specification.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PaymentCurrencyAmount(BaseModel):
    """Payment currency amount per AP2 specification"""
    currency: str
    value: float


class PaymentItem(BaseModel):
    """Payment item per AP2 specification"""
    label: str
    amount: PaymentCurrencyAmount


class PaymentDetails(BaseModel):
    """Payment details per AP2 specification"""
    id: str
    display_items: List[PaymentItem]
    total: PaymentItem


class PaymentMethodData(BaseModel):
    """Payment method data per AP2 specification"""
    supported_methods: str  # AP2 spec expects string, not list
    data: Dict[str, Any]


class PaymentRequest(BaseModel):
    """Payment request per AP2 specification"""
    method_data: List[PaymentMethodData]
    details: PaymentDetails
    options: Optional[Dict[str, Any]] = None
    shipping_address: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Payment response per AP2 specification"""
    request_id: str
    method_name: str
    details: Dict[str, Any]
