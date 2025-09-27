"""
WhatsApp Business API Integration for sofIA Payment Agent

This module handles WhatsApp webhooks, message processing, and responses
for the AP2-compliant payment agent.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import requests
from dotenv import load_dotenv

from .ap2_core import AP2PaymentAgent, WhatsAppPaymentFlow

# Load environment variables
load_dotenv()

class WhatsAppAPI:
    """Handles WhatsApp Business API interactions."""
    
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        if not all([self.access_token, self.phone_number_id, self.verify_token]):
            raise ValueError("Missing required WhatsApp API environment variables")
    
    def send_message(self, to: str, message: str, message_type: str = "text") -> bool:
        """Send a message via WhatsApp Business API."""
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": message_type,
            "text": {"body": message} if message_type == "text" else message
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to send WhatsApp message: {e}")
            return False
    
    def send_template_message(
        self, 
        to: str, 
        template_name: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send a WhatsApp template message."""
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": str(param)}
                            for param in (parameters or {}).values()
                        ]
                    }
                ] if parameters else []
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to send WhatsApp template message: {e}")
            return False
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify WhatsApp webhook during setup."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None


class WhatsAppPaymentBot:
    """Main WhatsApp bot for payment processing."""
    
    def __init__(self):
        self.whatsapp_api = WhatsAppAPI()
        self.payment_agent = AP2PaymentAgent(
            agent_id="sofia-whatsapp-payment-agent",
            merchant_id="sofia-merchant"
        )
        self.payment_flow = WhatsAppPaymentFlow(self.payment_agent)
        
        # Initialize FastAPI app
        self.app = FastAPI(title="sofIA WhatsApp Payment Agent")
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up FastAPI routes for WhatsApp webhooks."""
        
        @self.app.get("/webhook")
        async def verify_webhook(
            hub_mode: str = None,
            hub_verify_token: str = None,
            hub_challenge: str = None
        ):
            """Verify WhatsApp webhook."""
            result = self.whatsapp_api.verify_webhook(
                hub_mode, hub_verify_token, hub_challenge
            )
            
            if result:
                return int(result)
            else:
                raise HTTPException(status_code=403, detail="Forbidden")
        
        @self.app.post("/webhook")
        async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
            """Receive WhatsApp webhook messages."""
            try:
                body = await request.json()
                
                # Verify webhook signature (optional but recommended)
                signature = request.headers.get("X-Hub-Signature-256", "")
                if not self._verify_signature(body, signature):
                    raise HTTPException(status_code=403, detail="Invalid signature")
                
                # Process webhook in background
                background_tasks.add_task(self._process_webhook, body)
                
                return JSONResponse(content={"status": "ok"})
                
            except Exception as e:
                print(f"Error processing webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "sofIA WhatsApp Payment Agent"}
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        if not signature.startswith("sha256="):
            return False
        
        app_secret = os.getenv("WHATSAPP_APP_SECRET")
        if not app_secret:
            return True  # Skip verification if no app secret
        
        expected_signature = hmac.new(
            app_secret.encode(),
            json.dumps(payload, separators=(',', ':')).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
    
    async def _process_webhook(self, webhook_data: Dict[str, Any]):
        """Process incoming WhatsApp webhook."""
        try:
            # Extract message data from webhook
            entry = webhook_data.get("entry", [])
            if not entry:
                return
            
            for change in entry[0].get("changes", []):
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])
                    
                    for message in messages:
                        await self._process_message(message)
                        
        except Exception as e:
            print(f"Error processing webhook: {e}")
    
    async def _process_message(self, message: Dict[str, Any]):
        """Process individual WhatsApp message."""
        try:
            from_number = message.get("from")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            if not message_text or not from_number:
                return
            
            # Process message through payment flow
            response = self.payment_flow.handle_webhook({
                "from": from_number,
                "text": {"body": message_text},
                "id": message_id
            })
            
            # Send response back to user
            await self._send_response(from_number, response)
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    async def _send_response(self, to: str, response: Dict[str, Any]):
        """Send response message to user."""
        try:
            message = response.get("message", "I'm here to help with your payment needs!")
            
            # Add context based on response type
            if response.get("type") == "intent_created":
                message += "\n\nI'm searching for the best options for you. Please wait..."
            
            elif response.get("type") == "cart_ready":
                message += f"\n\nCart ID: {response.get('cart_id', 'N/A')}"
                message += "\n\nType 'confirm' to proceed with payment."
            
            elif response.get("type") == "payment_complete":
                message += f"\n\nPayment Mandate ID: {response.get('payment_mandate_id', 'N/A')}"
                message += "\n\nThank you for using sofIA Payment Agent!"
            
            # Send message via WhatsApp
            success = self.whatsapp_api.send_message(to, message)
            
            if not success:
                print(f"Failed to send response to {to}")
                
        except Exception as e:
            print(f"Error sending response: {e}")
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server."""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)


# Environment variables required:
# WHATSAPP_ACCESS_TOKEN - Your WhatsApp Business API access token
# WHATSAPP_PHONE_NUMBER_ID - Your WhatsApp Business phone number ID
# WHATSAPP_VERIFY_TOKEN - Token for webhook verification
# WHATSAPP_APP_SECRET - App secret for signature verification (optional)

def create_whatsapp_bot() -> WhatsAppPaymentBot:
    """Create and configure WhatsApp payment bot."""
    return WhatsAppPaymentBot()
