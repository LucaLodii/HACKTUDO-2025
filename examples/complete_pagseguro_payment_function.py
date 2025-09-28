"""
Complete PagSeguro Payment Function with AP2 Protocol

This is the main function you should use to process payments with PagSeguro
after receiving tokenized payment credentials from the AP2 protocol.

This function handles the complete payment flow:
1. Receives tokenized payment data from AP2
2. Creates PagSeguro payment request
3. Processes payment through PagSeguro API
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


class PagSeguroPaymentProcessor:
    """
    Production-ready PagSeguro payment processor for AP2 protocol integration
    """
    
    def __init__(self):
        """Initialize with environment-based configuration"""
        self.access_token = os.getenv("PAGSEGURO_ACCESS_TOKEN")
        self.client_id = os.getenv("PAGSEGURO_CLIENT_ID")
        self.client_secret = os.getenv("PAGSEGURO_CLIENT_SECRET")
        self.environment = os.getenv("PAGSEGURO_ENVIRONMENT", "sandbox")
        
        # Set base URL based on environment
        if self.environment == "production":
            self.base_url = "https://api.pagseguro.com"
        else:
            self.base_url = "https://sandbox.api.pagseguro.com"
        
        if not self.access_token:
            raise ValueError("PAGSEGURO_ACCESS_TOKEN environment variable is required")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for PagSeguro API requests"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/vnd.pagseguro.com.br.v1+json;charset=ISO-8859-1"
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
                    "token": "tok_1234567890abcdef",
                    "cvv_token": "cvv_abc123", 
                    "holder_name": "JOAO DA SILVA",
                    "installments": 1
                }
            
            transaction_details: Transaction information
                {
                    "amount": 25.90,
                    "currency": "BRL", 
                    "description": "Purchase via WhatsApp",
                    "reference_id": "sofia_txn_123",
                    "customer": {
                        "name": "João da Silva",
                        "email": "joao@email.com",
                        "cpf": "12345678901",
                        "phone": "11987654321"
                    }
                }
        
        Returns:
            Dict with payment result:
            {
                "success": True/False,
                "transaction_id": "TXN_123456",
                "status": "PAID"/"DECLINED"/"PENDING",
                "amount": 25.90,
                "currency": "BRL",
                "authorization_code": "AUTH123",
                "created_at": "2024-01-01T10:00:00Z",
                "error": "Error message if failed"
            }
        """
        
        try:
            logger.info(f"Processing AP2 payment: {transaction_details.get('reference_id')}")
            
            # Step 1: Create PagSeguro order
            order_result = self._create_order(transaction_details)
            if "error" in order_result:
                return order_result
            
            order_id = order_result["id"]
            logger.info(f"PagSeguro order created: {order_id}")
            
            # Step 2: Process payment with tokenized data
            payment_result = self._process_payment_with_token(order_id, tokenized_payment_data)
            if "error" in payment_result:
                return payment_result
            
            # Step 3: Return structured response
            return {
                "success": True,
                "transaction_id": payment_result["id"],
                "pagseguro_order_id": order_id,
                "status": self._normalize_status(payment_result["status"]),
                "amount": payment_result.get("amount", {}).get("value", 0) / 100,  # Convert from centavos
                "currency": payment_result.get("amount", {}).get("currency", "BRL"),
                "payment_method": tokenized_payment_data.get("method", "unknown"),
                "authorization_code": payment_result.get("authorization_code"),
                "created_at": payment_result.get("created_at", datetime.now(timezone.utc).isoformat()),
                "pagseguro_response": payment_result  # Full response for debugging
            }
            
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return {
                "success": False,
                "error": f"Payment processing failed: {str(e)}",
                "error_type": "processing_error"
            }
    
    def _create_order(self, transaction_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create PagSeguro order"""
        headers = self._get_headers()
        
        # Convert amount to centavos (PagSeguro requirement)
        amount_centavos = int(transaction_details["amount"] * 100)
        
        payload = {
            "reference_id": transaction_details.get("reference_id", f"sofia_{int(datetime.now().timestamp())}"),
            "description": transaction_details.get("description", "WhatsApp Purchase"),
            "amount": {
                "value": amount_centavos,
                "currency": transaction_details.get("currency", "BRL")
            },
            "notification_urls": [
                os.getenv("PAGSEGURO_WEBHOOK_URL", "")
            ] if os.getenv("PAGSEGURO_WEBHOOK_URL") else []
        }
        
        # Add customer data if provided
        if "customer" in transaction_details:
            customer = transaction_details["customer"]
            payload["customer"] = {
                "name": customer.get("name", ""),
                "email": customer.get("email", ""),
                "tax_id": customer.get("cpf", ""),
                "phone": {
                    "country": "+55",
                    "area": customer.get("phone", "")[:2] if customer.get("phone") else "11",
                    "number": customer.get("phone", "")[2:] if customer.get("phone") else "999999999",
                    "type": "MOBILE"
                }
            }
        
        try:
            response = requests.post(
                f"{self.base_url}/orders",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Order creation response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Order creation failed: {response.status_code}",
                    "error_details": error_data.get("error_messages", []),
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            return {"error": f"Order creation request failed: {str(e)}"}
    
    def _process_payment_with_token(self, order_id: str, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment using tokenized payment data"""
        headers = self._get_headers()
        
        # Map payment method to PagSeguro format
        payment_method_data = self._map_tokenized_data(tokenized_data)
        if "error" in payment_method_data:
            return payment_method_data
        
        payload = {
            "reference_id": f"payment_{order_id}_{int(datetime.now().timestamp())}",
            "payment_method": payment_method_data
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/orders/{order_id}/pay",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Payment processing response: {response.status_code}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_data = response.json() if response.content else {}
                return {
                    "error": f"Payment processing failed: {response.status_code}",
                    "error_details": error_data.get("error_messages", []),
                    "status_code": response.status_code,
                    "pagseguro_response": error_data
                }
                
        except requests.RequestException as e:
            return {"error": f"Payment processing request failed: {str(e)}"}
    
    def _map_tokenized_data(self, tokenized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map AP2 tokenized data to PagSeguro payment method format"""
        
        payment_method = tokenized_data.get("method", "").lower()
        
        if payment_method in ["credit_card", "basic-card"]:
            if "token" not in tokenized_data:
                return {"error": "Credit card token is required"}
            
            return {
                "type": "CREDIT_CARD",
                "installments": tokenized_data.get("installments", 1),
                "capture": True,
                "card": {
                    "encrypted": tokenized_data["token"],
                    "security_code": tokenized_data.get("cvv_token", ""),
                    "holder": {
                        "name": tokenized_data.get("holder_name", "CARD HOLDER")
                    }
                }
            }
        
        elif payment_method == "debit_card":
            if "token" not in tokenized_data:
                return {"error": "Debit card token is required"}
            
            return {
                "type": "DEBIT_CARD",
                "capture": True,
                "card": {
                    "encrypted": tokenized_data["token"],
                    "security_code": tokenized_data.get("cvv_token", ""),
                    "holder": {
                        "name": tokenized_data.get("holder_name", "CARD HOLDER")
                    }
                }
            }
        
        elif payment_method == "pix":
            return {
                "type": "PIX",
                "pix": {
                    "expiration_date": (datetime.now(timezone.utc)).isoformat()
                }
            }
        
        elif payment_method == "boleto":
            return {
                "type": "BOLETO",
                "boleto": {
                    "due_date": (datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                    "instruction_lines": {
                        "line_1": "Pagamento processado via sofIA",
                        "line_2": "Não receber após o vencimento"
                    }
                }
            }
        
        else:
            return {"error": f"Unsupported payment method: {payment_method}"}
    
    def _normalize_status(self, pagseguro_status: str) -> str:
        """Normalize PagSeguro status to standard format"""
        status_mapping = {
            "WAITING": "pending",
            "IN_ANALYSIS": "processing",
            "PAID": "approved", 
            "AVAILABLE": "approved",
            "DECLINED": "denied",
            "CANCELLED": "cancelled"
        }
        return status_mapping.get(pagseguro_status.upper(), pagseguro_status.lower())
    
    def get_payment_status(self, order_id: str) -> Dict[str, Any]:
        """Get current payment status from PagSeguro"""
        headers = self._get_headers()
        
        try:
            response = requests.get(
                f"{self.base_url}/orders/{order_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": self._normalize_status(result.get("status", "")),
                    "amount": result.get("amount", {}).get("value", 0) / 100,
                    "currency": result.get("amount", {}).get("currency", "BRL"),
                    "created_at": result.get("created_at"),
                    "paid_at": result.get("paid_at"),
                    "charges": result.get("charges", [])
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

def process_pagseguro_payment_with_ap2_tokens(tokenized_payment_data: Dict[str, Any],
                                             transaction_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    MAIN FUNCTION: Process PagSeguro payment with tokenized data from AP2 protocol
    
    This is the function you should call from your sofIA agent after receiving
    tokenized payment credentials and transaction details from the AP2 protocol.
    
    Args:
        tokenized_payment_data: Tokenized payment data from AP2
            {
                "method": "credit_card",           # Payment method
                "token": "tok_abc123",             # Tokenized card data
                "cvv_token": "cvv_xyz789",         # Tokenized CVV
                "holder_name": "JOAO DA SILVA",    # Cardholder name
                "installments": 1                  # Number of installments
            }
        
        transaction_details: Transaction information
            {
                "amount": 29.90,                   # Amount in BRL
                "currency": "BRL",                 # Currency code
                "description": "Coffee purchase",  # Purchase description
                "reference_id": "sofia_123",       # Your internal reference
                "customer": {                      # Customer data (required)
                    "name": "João da Silva",
                    "email": "joao@email.com", 
                    "cpf": "12345678901",
                    "phone": "11987654321"
                }
            }
    
    Returns:
        {
            "success": True,                       # Payment success/failure
            "transaction_id": "TXN_123456",        # PagSeguro transaction ID
            "status": "approved",                  # Payment status
            "amount": 29.90,                       # Processed amount
            "currency": "BRL",                     # Currency
            "authorization_code": "AUTH123",       # Authorization code
            "created_at": "2024-01-01T10:00:00Z", # Transaction timestamp
            "error": "Error message"               # Error if failed
        }
    """
    
    # Initialize processor
    processor = PagSeguroPaymentProcessor()
    
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
        "token": "tok_1234567890abcdef",      # From PagSeguro tokenization
        "cvv_token": "cvv_abc123456789",      # Tokenized CVV
        "holder_name": "JOAO DA SILVA",       # Cardholder name
        "installments": 3                     # 3x installments
    }
    
    # Transaction details
    transaction_details = {
        "amount": 89.90,                      # R$ 89.90
        "currency": "BRL",
        "description": "WhatsApp purchase - Premium Coffee",
        "reference_id": "sofia_coffee_001",
        "customer": {
            "name": "João da Silva",
            "email": "joao.silva@email.com",
            "cpf": "12345678901",
            "phone": "11987654321"
        }
    }
    
    # Process payment
    result = process_pagseguro_payment_with_ap2_tokens(tokenized_data, transaction_details)
    
    # Handle result
    if result["success"]:
        print(f"✅ Payment approved!")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Amount: R$ {result['amount']:.2f}")
    else:
        print(f"❌ Payment failed: {result['error']}")
    
    return result


def example_pix_payment():
    """Example: Process PIX payment"""
    
    # PIX payment data
    tokenized_data = {
        "method": "pix",
        "pix_key": "joao@email.com",
        "pix_key_type": "email"
    }
    
    # Transaction details
    transaction_details = {
        "amount": 25.50,
        "currency": "BRL", 
        "description": "WhatsApp purchase - Quick Lunch",
        "reference_id": "sofia_lunch_002",
        "customer": {
            "name": "João da Silva",
            "email": "joao@email.com",
            "cpf": "12345678901",
            "phone": "11987654321"
        }
    }
    
    # Process payment
    result = process_pagseguro_payment_with_ap2_tokens(tokenized_data, transaction_details)
    
    return result


def example_error_handling():
    """Example: How to handle different error scenarios"""
    
    # Invalid tokenized data (missing token)
    invalid_data = {
        "method": "credit_card",
        # "token": "missing_token",  # This will cause an error
        "holder_name": "JOAO DA SILVA"
    }
    
    transaction_details = {
        "amount": 50.00,
        "currency": "BRL",
        "description": "Test payment",
        "reference_id": "test_001"
    }
    
    result = process_pagseguro_payment_with_ap2_tokens(invalid_data, transaction_details)
    
    # Handle different error types
    if not result["success"]:
        error_type = result.get("error_type", "unknown")
        
        if error_type == "processing_error":
            print("🔧 Processing error - check logs and retry")
        elif "token" in result.get("error", "").lower():
            print("🔑 Token error - request new tokenization")
        elif result.get("status_code") == 422:
            print("📝 Validation error - check customer data")
        else:
            print(f"❌ Unknown error: {result['error']}")


if __name__ == "__main__":
    """
    Test the PagSeguro integration
    
    Make sure to set these environment variables:
    - PAGSEGURO_ACCESS_TOKEN
    - PAGSEGURO_CLIENT_ID  
    - PAGSEGURO_CLIENT_SECRET
    - PAGSEGURO_ENVIRONMENT (sandbox/production)
    """
    
    print("🏦 PagSeguro Payment Processing Test")
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
    
    print("\n🎉 PagSeguro integration test complete!")
