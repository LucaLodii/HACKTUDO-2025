"""
WhatsApp Webhook Handler

Handles incoming WhatsApp webhooks and processes them through the sofIA agent.
"""

import os
import json
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from sofIA.agent import create_sofia_agent


class WhatsAppWebhookHandler:
    """Handles WhatsApp webhook events and processes them through the sofIA agent."""
    
    def __init__(self):
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")
        self.agent = create_sofia_agent()
        
        # Initialize FastAPI app
        self.app = FastAPI(title="sofIA WhatsApp Webhook Handler")
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
            if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
                return int(hub_challenge)
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
            return {"status": "healthy", "service": "sofIA WhatsApp Webhook Handler"}
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        if not signature.startswith("sha256="):
            return False
        
        if not self.app_secret:
            return True  # Skip verification if no app secret
        
        expected_signature = hmac.new(
            self.app_secret.encode(),
            json.dumps(payload, separators=(',', ':')).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(
            f"sha256={expected_signature}",
            signature
        )
    
    async def _process_webhook(self, webhook_data: Dict[str, Any]):
        """Process incoming WhatsApp webhook through the sofIA agent."""
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
        """Process individual WhatsApp message through the sofIA agent."""
        try:
            from_number = message.get("from")
            message_text = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            if not message_text or not from_number:
                return
            
            # Process message through the sofIA agent
            # This would involve calling the agent with the user's message
            # and using the WhatsApp tool to send responses
            
            print(f"Processing message from {from_number}: {message_text}")
            
            # For now, just log the message
            # In a full implementation, you would:
            # 1. Call the agent with the user's message
            # 2. The agent would use the AP2 tool to create mandates
            # 3. The agent would use the WhatsApp tool to send responses
            
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the webhook server."""
        uvicorn.run(self.app, host=host, port=port)


def create_webhook_handler() -> WhatsAppWebhookHandler:
    """Create and configure WhatsApp webhook handler."""
    return WhatsAppWebhookHandler()
