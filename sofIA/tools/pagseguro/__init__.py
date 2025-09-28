"""
PagSeguro Payment Gateway Integration for sofIA

This module provides PagSeguro (PagBank) payment processing capabilities
for the sofIA WhatsApp payment agent with full AP2 protocol compliance.
"""

from .pagseguro_tool import pagseguro_tool, PagSeguroTool, PagSeguroConfig, PagSeguroMerchant

__all__ = ["pagseguro_tool", "PagSeguroTool", "PagSeguroConfig", "PagSeguroMerchant"]
