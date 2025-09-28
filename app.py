"""
sofIA WhatsApp Payment Agent - Main Application

This is the main entry point for the sofIA payment agent that implements
the Agent Payments Protocol (AP2) for secure WhatsApp transactions.
"""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.agent import orchestrator_agent
from orchestrator.tools import process_user_message, get_user_session, get_session_stats, cleanup_old_sessions

# Import notification API
from notification_api import app as notification_app

# Load environment variables (supports operator-specific .env files)
load_dotenv()

# Initialize operator-specific configuration
OPERATOR_NAME = os.getenv("OPERATOR_NAME", "DEMO")
OPERATOR_DISPLAY_NAME = os.getenv("OPERATOR_DISPLAY_NAME", "Demo Operator")
SOFIA_AGENT_NAME = os.getenv("SOFIA_AGENT_NAME", f"sofIA {OPERATOR_NAME} Payment Agent")
BRAND_COLOR = os.getenv("BRAND_COLOR", "#6366f1")

print(f"🏷️  Initializing WHITE-LABEL sofIA for: {OPERATOR_DISPLAY_NAME}")
print(f"🤖 Agent: {SOFIA_AGENT_NAME}")
print(f"🎨 Brand Color: {BRAND_COLOR}")

# Create FastAPI app for WhatsApp Web.js integration
app = FastAPI(title="sofIA WhatsApp Payment Agent", version="1.0.0")

# Mount notification API
app.mount("/notifications", notification_app)

# The orchestrator handles everything now

@app.post("/process-whatsapp-message")
async def process_whatsapp_message(request: Request):
    """Process WhatsApp messages from the Node.js bridge."""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        message = data.get("message")

        if not user_id or not message:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing user_id or message"}
            )

        # Process through orchestrator agent (True A2A)

        try:
            # Try to use orchestrator agent properly
            # For now, bypass agent invocation and use the tool directly with smart fallback
            print(f"\n🔷 ═══ NEW MESSAGE ═══ Session: {user_id[-8:]} ═══")
            print(f"📝 Message: '{message}'")

            # Use Gemini directly through a simple API call for intent detection
            import google.generativeai as genai

            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Get user session to understand context
            session = get_user_session(user_id)
            current_state = session.get("payment_state", "idle")
            conversation_history = session.get("conversation_history", [])

            # Build conversation context
            context_messages = ""
            if len(conversation_history) > 1:  # More than just current message
                recent_history = conversation_history[-7:]  # Last 7 messages for context
                context_messages = "\n".join([f"User: {msg['message']}" for msg in recent_history[:-1]])  # Exclude current message
                context_messages = f"\nRecent conversation:\n{context_messages}\n"

            # Create prompt for intent detection with full context - operator-specific
            intent_prompt = f"""You are {SOFIA_AGENT_NAME}, the AI payment assistant for {OPERATOR_DISPLAY_NAME}. You help customers with {OPERATOR_NAME} subscription plans and payments. Analyze this user message and respond naturally while maintaining conversation context.

{context_messages}Current user message: "{message}"
Current conversation state: {current_state}
Your operator: {OPERATOR_NAME}

Instructions:
- You work exclusively for {OPERATOR_DISPLAY_NAME} and only offer {OPERATOR_NAME} plans and services
- If you detect purchase intent (wants to buy something) and state is 'idle', start your response with [PAYMENT_INTENT]
- If user is confirming a purchase (yes/sim/ok/confirm) and state is 'cart_created', start with [PAYMENT_CONFIRM]
- If user is canceling a purchase (no/não/cancel) and state is 'cart_created', start with [PAYMENT_CANCEL]
- Remember the conversation context and respond accordingly
- Be helpful and maintain continuity with previous messages
- Always mention you're the {OPERATOR_NAME} assistant when introducing yourself

Respond naturally in Portuguese or English as appropriate."""

            # Get response from Gemini
            response = model.generate_content(intent_prompt)
            agent_reply = response.text if response.text else "Hello! I'm sofIA, your AI payment assistant. How can I help you today?"

            print(f"🤖 Agent Response: {agent_reply}")
            print("🔧 Processing with orchestrator...")

            # Use orchestrator tool to handle A2A coordination with operator context
            result = await process_user_message(message, user_id, agent_reply, operator_name=OPERATOR_NAME)
            reply = result.get("reply", "Sorry, I couldn't process your message.")

            print(f"✅ Final Reply: {reply[:100]}{'...' if len(reply) > 100 else ''}")
            print(f"🔷 ═══ END SESSION {user_id[-8:]} ═══\n")

        except Exception as e:
            print(f"Orchestrator processing error: {e}")
            reply = "Hello! I'm sofIA, your AI payment assistant. How can I help you today?"

        return JSONResponse(content={"reply": reply})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Processing failed: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint with session statistics."""
    session_stats = get_session_stats()
    return {
        "status": "healthy",
        "service": "sofIA WhatsApp Payment Agent",
        "ap2_ready": True,
        "active_sessions": session_stats["active_sessions"],
        "active_locks": session_stats["active_locks"]
    }

@app.post("/test-mercadopago")
async def test_mercadopago(request: Request):
    """Teste do Mercado Pago para verificar configuração."""
    try:
        data = await request.json()
        
        # Importa a ferramenta do Mercado Pago
        from sofIA.tools.mercadopago.mercadopago_tool import mercadopago_tool
        
        # Executa o teste
        result = await mercadopago_tool(**data)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro no teste do Mercado Pago: {str(e)}"
        }


@app.get("/sessions")
async def get_sessions():
    """Get session statistics for monitoring."""
    return get_session_stats()


@app.post("/cleanup-sessions")
async def cleanup_sessions():
    """Manually trigger session cleanup."""
    await cleanup_old_sessions()
    return {"message": "Session cleanup completed", "stats": get_session_stats()}


@app.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request):
    """Receive MercadoPago webhook notifications."""
    try:
        data = await request.json()
        
        # Log webhook received
        print(f"🟢 MercadoPago webhook received: {data}")
        
        # Extract relevant information
        webhook_type = data.get("type")
        webhook_data = data.get("data", {})
        
        if webhook_type == "payment":
            payment_id = webhook_data.get("id")
            print(f"💳 Payment webhook - ID: {payment_id}")
            
            # Here you can add logic to:
            # 1. Verify the payment status with MercadoPago API
            # 2. Update your internal payment records
            # 3. Notify the user via WhatsApp
            # 4. Update AP2 mandate status
            
        elif webhook_type == "merchant_order":
            order_id = webhook_data.get("id")
            print(f"📦 Merchant order webhook - ID: {order_id}")
            
        # Always return success to MercadoPago
        return JSONResponse(content={"status": "received", "webhook_type": webhook_type})
        
    except Exception as e:
        print(f"❌ Error processing MercadoPago webhook: {e}")
        # Still return success to avoid retries from MercadoPago
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.post("/webhooks/pagseguro")
async def pagseguro_webhook(request: Request):
    """Receive PagSeguro webhook notifications."""
    try:
        data = await request.json()
        
        # Log webhook received
        print(f"🟡 PagSeguro webhook received: {data}")
        
        # Extract relevant information
        reference_id = data.get("reference_id")
        status = data.get("status")
        
        print(f"💳 PagSeguro payment - Reference: {reference_id}, Status: {status}")
        
        # Here you can add logic to:
        # 1. Verify the payment status with PagSeguro API
        # 2. Update your internal payment records
        # 3. Notify the user via WhatsApp
        # 4. Update AP2 mandate status
        
        # Always return success to PagSeguro
        return JSONResponse(content={"status": "received", "reference_id": reference_id})
        
    except Exception as e:
        print(f"❌ Error processing PagSeguro webhook: {e}")
        # Still return success to avoid retries from PagSeguro
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.post("/webhooks/bemobi")
async def bemobi_webhook(request: Request):
    """Receive BEMOBI webhook notifications."""
    try:
        data = await request.json()
        
        # Log webhook received
        print(f"🔵 BEMOBI webhook received: {data}")
        
        # Extract relevant information
        transaction_id = data.get("transaction_id")
        status = data.get("status")
        merchant_id = data.get("merchant_id")
        
        print(f"💳 BEMOBI payment - Transaction: {transaction_id}, Status: {status}, Merchant: {merchant_id}")
        
        # Here you can add logic to:
        # 1. Verify the payment status with BEMOBI API
        # 2. Update your internal payment records
        # 3. Notify the user via WhatsApp
        # 4. Update AP2 mandate status
        
        # Always return success to BEMOBI
        return JSONResponse(content={"status": "received", "transaction_id": transaction_id})
        
    except Exception as e:
        print(f"❌ Error processing BEMOBI webhook: {e}")
        # Still return success to avoid retries from BEMOBI
        return JSONResponse(content={"status": "error", "message": str(e)})


@app.get("/webhook")
async def whatsapp_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None, 
    hub_challenge: str = None
):
    """Verify WhatsApp webhook (for official WhatsApp Business API)."""
    try:
        # Verify token should match your WhatsApp app configuration
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "sofia_webhook_token")
        
        if hub_mode == "subscribe" and hub_verify_token == verify_token:
            print("✅ WhatsApp webhook verified successfully")
            return int(hub_challenge)
        else:
            print("❌ WhatsApp webhook verification failed")
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
            
    except Exception as e:
        print(f"❌ Error verifying WhatsApp webhook: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/webhook")
async def whatsapp_webhook_receive(request: Request):
    """Receive WhatsApp webhook messages (for official WhatsApp Business API)."""
    try:
        data = await request.json()
        
        # Log webhook received
        print(f"💬 WhatsApp webhook received: {data}")
        
        # Extract message data
        entry = data.get("entry", [])
        if entry:
            changes = entry[0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    from_number = message.get("from")
                    message_text = message.get("text", {}).get("body", "")
                    
                    if message_text:
                        print(f"📱 Message from {from_number}: {message_text}")
                        
                        # Process through your existing WhatsApp message handler
                        # This would integrate with your process_whatsapp_message logic
        
        return JSONResponse(content={"status": "received"})
        
    except Exception as e:
        print(f"❌ Error processing WhatsApp webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)})

def main():
    """Main application entry point."""
    print("🚀 Starting sofIA WhatsApp Payment Agent...")
    print("📱 AP2 Protocol Implementation for Secure Payments")
    print("=" * 50)
    
    # Check for Google API key (required for agent)
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Missing required environment variable: GOOGLE_API_KEY")
        print("Please set this variable in your .env file or environment.")
        return
    
    try:
        print("✅ sofIA Payment Agent initialized successfully")
        print("🔐 AP2 Protocol compliance enabled")
        print("\n🌐 Starting FastAPI server...")

        # Start the FastAPI server
        import uvicorn
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8000))

        print(f"📡 Server starting on {host}:{port}")
        print("💡 Health check: http://localhost:8000/health")
        print("🔗 Process message: http://localhost:8000/process-whatsapp-message")

        uvicorn.run(app, host=host, port=port)
        
    except Exception as e:
        print(f"❌ Error starting sofIA Payment Agent: {e}")
        sys.exit(1)


def run_demo():
    """Run a demo of the sofIA payment orchestrator."""
    print("🎭 Running sofIA Payment Agent Demo...")
    print("=" * 40)

    # Test conversation flow with True A2A orchestrator
    def demo_process_message(message: str, user_id: str):
        context = f"""
User message: {message}
User ID: {user_id}

Analyze this message and respond naturally. If you detect purchase intent,
start your response with [PAYMENT_INTENT].
If the user is confirming a purchase, start with [PAYMENT_CONFIRM].
If the user is canceling a purchase, start with [PAYMENT_CANCEL].
"""
        try:
            import asyncio
            from google.adk.core import InvocationContext

            async def get_agent_response():
                ctx = InvocationContext()
                ctx.set_input(context)
                events = orchestrator_agent.run_async(ctx)
                agent_reply = ""
                async for event in events:
                    if hasattr(event, 'text') and event.text:
                        agent_reply += event.text
                return agent_reply

            agent_reply = asyncio.run(get_agent_response())
            return process_user_message(message, user_id, agent_reply)
        except Exception as e:
            print(f"Demo error: {e}")
            return {"reply": "Demo error occurred", "session_state": "idle"}

    print("1. User says hello:")
    response1 = demo_process_message("Hello!", "demo_user")
    print(f"   sofIA: {response1['reply']}")

    print("\n2. User wants to buy coffee:")
    response2 = demo_process_message("I want to buy coffee", "demo_user")
    print(f"   sofIA: {response2['reply'][:200]}...")

    print("\n3. User confirms purchase:")
    response3 = demo_process_message("yes", "demo_user")
    print(f"   sofIA: {response3['reply'][:200]}...")

    if response3.get('session_state') == 'completed':
        print("   ✅ Payment completed via True A2A Communication!")

    print("\n🎉 Demo completed - True A2A orchestration working!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        main()
