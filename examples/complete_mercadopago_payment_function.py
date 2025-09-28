"""
Complete Mercado Pago Payment Function with AP2 Protocol

This is the main function you should use to process payments with Mercado Pago
after receiving tokenized payment credentials from the AP2 protocol.

This function handles the complete payment flow:
1. Receives tokenized payment data from AP2
2. Creates Mercado Pago payment request
3. Processes payment through Mercado Pago API
4. Returns structured response with status
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MercadoPagoPaymentProcessor:
    """
    Production-ready Mercado Pago payment processor for AP2 protocol integration
    """
    
    def __init__(self):
        """Initialize with environment-based configuration"""
        self.access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        self.public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
        self.client_id = os.getenv("MERCADOPAGO_CLIENT_ID")
        self.client_secret = os.getenv("MERCADOPAGO_CLIENT_SECRET")
        self.environment = os.getenv("MERCADOPAGO_ENVIRONMENT", "sandbox")
        
        # Mercado Pago uses the same base URL for sandbox and production
        # The environment is determined by the credentials used
        self.base_url = "https://api.mercadopago.com"
        
        if not self.access_token:
            raise ValueError("MERCADOPAGO_ACCESS_TOKEN environment variable is required")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for Mercado Pago API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "X-Idempotency-Key": f"sofia-{datetime.now(timezone.utc).timestamp()}"
        }
    
    def process_ap2_payment(self, 
                           tokenized_payment_data: Dict[str, Any],
                           transaction_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process payment using tokenized data from AP2 protocol
        
        Args:
            tokenized_payment_data: Tokenized payment credentials from AP2
                Example for credit card:
                {
                    "method": "credit_card",
                    "token": "card_token_123456789",
                    "installments": 1,
                    "issuer_id": "25",
                    "security_code": "123"
                }
            
            transaction_details: Transaction information
                {
                    "amount": 25.90,
                    "currency": "BRL", 
                    "description": "Purchase via WhatsApp",
                    "external_reference": "sofia_txn_123",
                    "customer": {
                        "name": "João",
                        "surname": "da Silva",
                        "email": "joao@email.com",
                        "cpf": "12345678901",
                        "phone": "11987654321"
                    }
                }
        
        Returns:
            Dict with payment result:
            {
                "success": True/False,
                "transaction_id": "123456789",
                "status": "approved"/"rejected"/"pending",
                "status_detail": "accredited"/"cc_rejected_other_reason",
                "amount": 25.90,
                "currency": "BRL",
                "payment_method_id": "visa",
                "authorization_code": "AUTH123",
                "created_at": "2024-01-01T10:00:00Z",
                "error": "Error message if failed"
            }
        """
        
        try:
            logger.info(f"Processing AP2 payment: {transaction_details.get('external_reference')}")
            
            # Step 1: Create payment with Mercado Pago
            payment_result = self._create_payment(tokenized_payment_data, transaction_details)
            if "error" in payment_result:
                return payment_result
            
            logger.info(f"Mercado Pago payment created: {payment_result['id']}")
            
            # Step 2: Return structured response
            return {
                "success": True,
                "transaction_id": str(payment_result["id"]),
                "status": self._normalize_status(payment_result["status"]),
                "status_detail": payment_result.get("status_detail", ""),
                "amount": payment_result.get("transaction_amount", 0),
                "currency": payment_result.get("currency_id", "BRL"),
                "payment_method": tokenized_payment_data.get("method", "unknown"),
                "payment_method_id": payment_result.get("payment_method_id", ""),
                "authorization_code": payment_result.get("authorization_code"),
                "created_at": payment_result.get("date_created", datetime.now(timezone.utc).isoformat()),
                "point_of_interaction": payment_result.get("point_of_interaction", {}),
                "mercadopago_response": payment_result  # Full response for debugging
            }
            
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return {
                "success": False,
                "error": f"Payment processing failed: {str(e)}",
                "error_type": "processing_error"
            }
    
    def _create_payment(self, tokenized_payment_data: Dict[str, Any], 
                       transaction_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment with Mercado Pago"""
        headers = self._get_headers()
        
        # Map payment method to Mercado Pago format
        payment_method_data = self._map_tokenized_data(tokenized_payment_data)
        if "error" in payment_method_data:
            return payment_method_data
        
        # Build payment payload
        payload = {
            "transaction_amount": transaction_details["amount"],
            "description": transaction_details.get("description", "WhatsApp Purchase"),
            "external_reference": transaction_details.get("external_reference", f"sofia_{int(datetime.now().timestamp())}"),
            "notification_url": os.getenv("MERCADOPAGO_WEBHOOK_URL", ""),
            "metadata": {
                "source": "sofia_whatsapp",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Add payment method specific data
        payload.update(payment_method_data)
        
        # Add customer data if provided
        if "customer" in transaction_details:
            customer = transaction_details["customer"]
            payload["payer"] = {
                "first_name": customer.get("name", ""),
                "last_name": customer.get("surname", ""),
                "email": customer.get("email", ""),
                "phone": {
                    "area_code": customer.get("phone", "")[:2] if customer.get("phone") else "11",
                    "number": customer.get("phone", "")[2:] if customer.get("phone") else "999999999"
                },
                "identification": {
                    "type": "CPF",
                    "number": customer.get("cpf", "")
                }
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/payments",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Payment creation response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Payment creation failed: {response.status_code}",
                    "error_details": error_data.get("message", "Unknown error"),
                    "status_code": response.status_code,
                    "mercadopago_response": error_data
                }
                
        except requests.RequestException as e:
            return {"error": f"Payment creation request failed: {str(e)}"}
    
    def _map_tokenized_data(self, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map AP2 tokenized data to Mercado Pago payment format"""
        
        payment_method = tokenized_data.get("method", "").lower()
        
        if payment_method in ["credit_card", "basic-card"]:
            if "token" not in tokenized_data:
                return {"error": "Credit card token is required"}
            
            return {
                "payment_method_id": tokenized_data.get("payment_method_id", "visa"),
                "token": tokenized_data["token"],
                "installments": tokenized_data.get("installments", 1),
                "issuer_id": tokenized_data.get("issuer_id", "25")  # Default to Banco do Brasil
            }
        
        elif payment_method == "debit_card":
            if "token" not in tokenized_data:
                return {"error": "Debit card token is required"}
            
            return {
                "payment_method_id": tokenized_data.get("payment_method_id", "debvisa"),
                "token": tokenized_data["token"],
                "issuer_id": tokenized_data.get("issuer_id", "25")
            }
        
        elif payment_method == "pix":
            return {
                "payment_method_id": "pix"
            }
        
        elif payment_method == "boleto":
            return {
                "payment_method_id": "bolbradesco"  # Can be other boleto types
            }
        
        else:
            return {"error": f"Unsupported payment method: {payment_method}"}
    
    def _normalize_status(self, mercadopago_status: str) -> str:
        """Normalize Mercado Pago status to standard format"""
        status_mapping = {
            "pending": "pending",
            "approved": "approved", 
            "authorized": "approved",
            "in_process": "processing",
            "in_mediation": "processing",
            "rejected": "denied",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "charged_back": "refunded"
        }
        return status_mapping.get(mercadopago_status.lower(), mercadopago_status.lower())
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get current payment status from Mercado Pago"""
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f"{self.base_url}/v1/payments/{payment_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "status": self._normalize_status(result.get("status", "")),
                    "status_detail": result.get("status_detail", ""),
                    "amount": result.get("transaction_amount", 0),
                    "currency": result.get("currency_id", "BRL"),
                    "payment_method_id": result.get("payment_method_id", ""),
                    "created_at": result.get("date_created"),
                    "approved_at": result.get("date_approved"),
                    "last_modified": result.get("date_last_updated")
                }
            else:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.status_code}"
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Status check request failed: {str(e)}"
            }


# ==========================================
# MAIN FUNCTION FOR YOUR INTEGRATION
# ==========================================

def process_mercadopago_payment_with_ap2_tokens(tokenized_payment_data: Dict[str, Any],
                                               transaction_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    MAIN FUNCTION: Process Mercado Pago payment with tokenized data from AP2 protocol
    
    This is the function you should call from your sofIA agent after receiving
    tokenized payment credentials and transaction details from the AP2 protocol.
    
    Args:
        tokenized_payment_data: Tokenized payment data from AP2
            {
                "method": "credit_card",           # Payment method
                "token": "card_token_123",         # Tokenized card data
                "installments": 1,                 # Number of installments
                "issuer_id": "25",                 # Bank issuer ID
                "payment_method_id": "visa"        # Card brand
            }
        
        transaction_details: Transaction information
            {
                "amount": 29.90,                   # Amount in BRL
                "currency": "BRL",                 # Currency code
                "description": "Coffee purchase",  # Purchase description
                "external_reference": "sofia_123", # Your internal reference
                "customer": {                      # Customer data (required)
                    "name": "João",
                    "surname": "da Silva",
                    "email": "joao@email.com", 
                    "cpf": "12345678901",
                    "phone": "11987654321"
                }
            }
    
    Returns:
        {
            "success": True,                       # Payment success/failure
            "transaction_id": "123456789",         # Mercado Pago payment ID
            "status": "approved",                  # Payment status
            "status_detail": "accredited",         # Detailed status
            "amount": 29.90,                       # Processed amount
            "currency": "BRL",                     # Currency
            "payment_method_id": "visa",           # Payment method used
            "authorization_code": "AUTH123",       # Authorization code
            "created_at": "2024-01-01T10:00:00Z", # Transaction timestamp
            "error": "Error message"               # Error if failed
        }
    """
    
    # Initialize processor
    processor = MercadoPagoPaymentProcessor()
    
    # Process payment
    result = processor.process_ap2_payment(tokenized_payment_data, transaction_details)
    
    # Log result for monitoring
    logger.info(f"Payment result: {result.get('success', False)} - {result.get('status', 'unknown')}")
    
    return result


# ==========================================
# USAGE EXAMPLES
# ==========================================

def example_credit_card_payment():
    """Example: Process credit card payment with tokenized data"""
    
    # Tokenized payment data from AP2 protocol
    tokenized_data = {
        "method": "credit_card",
        "token": "card_token_1234567890abcdef",  # From Mercado Pago tokenization
        "installments": 3,                       # 3x installments
        "issuer_id": "25",                       # Banco do Brasil
        "payment_method_id": "visa"              # Visa card
    }
    
    # Transaction details
    transaction_details = {
        "amount": 89.90,                         # R$ 89.90
        "currency": "BRL",
        "description": "WhatsApp purchase - Premium Coffee",
        "external_reference": "sofia_coffee_001",
        "customer": {
            "name": "João",
            "surname": "da Silva",
            "email": "joao.silva@email.com",
            "cpf": "12345678901",
            "phone": "11987654321"
        }
    }
    
    # Process payment
    result = process_mercadopago_payment_with_ap2_tokens(tokenized_data, transaction_details)
    
    # Handle result
    if result["success"]:
        print(f"✅ Payment approved!")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Status Detail: {result['status_detail']}")
        print(f"   Amount: R$ {result['amount']:.2f}")
        print(f"   Payment Method: {result['payment_method_id']}")
    else:
        print(f"❌ Payment failed: {result['error']}")
    
    return result


def example_pix_payment():
    """Example: Process PIX payment"""
    
    # PIX payment data
    tokenized_data = {
        "method": "pix"
    }
    
    # Transaction details
    transaction_details = {
        "amount": 25.50,
        "currency": "BRL", 
        "description": "WhatsApp purchase - Quick Lunch",
        "external_reference": "sofia_lunch_002",
        "customer": {
            "name": "João",
            "surname": "da Silva",
            "email": "joao@email.com",
            "cpf": "12345678901",
            "phone": "11987654321"
        }
    }
    
    # Process payment
    result = process_mercadopago_payment_with_ap2_tokens(tokenized_data, transaction_details)
    
    if result["success"]:
        print(f"✅ PIX payment created!")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Status: {result['status']}")
        
        # PIX payments usually return QR code data
        point_of_interaction = result.get("point_of_interaction", {})
        if "transaction_data" in point_of_interaction:
            print(f"   🔗 PIX QR Code: {point_of_interaction['transaction_data']['qr_code']}")
            print(f"   📋 PIX Code: {point_of_interaction['transaction_data']['qr_code_base64']}")
    
    return result


def example_error_handling():
    """Example: How to handle different error scenarios"""
    
    # Invalid tokenized data (missing token)
    invalid_data = {
        "method": "credit_card",
        # "token": "missing_token",  # This will cause an error
        "installments": 1
    }
    
    transaction_details = {
        "amount": 50.00,
        "currency": "BRL",
        "description": "Test payment",
        "external_reference": "test_001"
    }
    
    result = process_mercadopago_payment_with_ap2_tokens(invalid_data, transaction_details)
    
    # Handle different error types
    if not result["success"]:
        error_type = result.get("error_type", "unknown")
        
        if error_type == "processing_error":
            print("🔧 Processing error - check logs and retry")
        elif "token" in result.get("error", "").lower():
            print("🔑 Token error - request new tokenization")
        elif result.get("status_code") == 422:
            print("📝 Validation error - check customer data")
        elif result.get("status_code") == 401:
            print("🔐 Authentication error - check access token")
        else:
            print(f"❌ Unknown error: {result['error']}")


if __name__ == "__main__":
    """
    Test the Mercado Pago integration
    
    Make sure to set these environment variables:
    - MERCADOPAGO_ACCESS_TOKEN
    - MERCADOPAGO_PUBLIC_KEY  
    - MERCADOPAGO_CLIENT_ID (optional)
    - MERCADOPAGO_CLIENT_SECRET (optional)
    - MERCADOPAGO_ENVIRONMENT (sandbox/production)
    """
    
    print("🏦 Mercado Pago Payment Processing Test")
    print("=" * 50)
    
    # Test credit card payment
    print("\n💳 Testing Credit Card Payment...")
    credit_result = example_credit_card_payment()
    
    # Test PIX payment  
    print("\n🏦 Testing PIX Payment...")
    pix_result = example_pix_payment()
    
    # Test error handling
    print("\n❌ Testing Error Handling...")
    example_error_handling()
    
    print("\n🎉 Mercado Pago integration test complete!")
