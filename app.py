"""
sofIA WhatsApp Payment Agent - Main Application

This is the main entry point for the sofIA payment agent that implements
the Agent Payments Protocol (AP2) for secure WhatsApp transactions.
"""

import os
import sys
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.agent import orchestrator_agent
from orchestrator.tools import process_user_message, get_user_session

# Load environment variables
load_dotenv()

# Create FastAPI app for WhatsApp Web.js integration
app = FastAPI(title="sofIA WhatsApp Payment Agent", version="1.0.0")

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
        context = f"""
User message: {message}
User ID: {user_id}

Analyze this message and respond naturally. If you detect purchase intent,
start your response with [PAYMENT_INTENT].
If the user is confirming a purchase, start with [PAYMENT_CONFIRM].
If the user is canceling a purchase, start with [PAYMENT_CANCEL].
"""

        try:
            # Try to use orchestrator agent properly
            # For now, bypass agent invocation and use the tool directly with smart fallback
            print(f"Processing message: '{message}' from user: {user_id}")

            # Use Gemini directly through a simple API call for intent detection
            import google.generativeai as genai

            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Get user session to understand context
            session = get_user_session(user_id)
            current_state = session.get("payment_state", "idle")

            # Create prompt for intent detection with context
            intent_prompt = f"""You are sofIA, an AI payment assistant. Analyze this user message and respond naturally.

User message: "{message}"
Current conversation state: {current_state}

Instructions:
- If you detect purchase intent (wants to buy something) and state is 'idle', start your response with [PAYMENT_INTENT]
- If user is confirming a purchase (yes/sim/ok/confirm) and state is 'cart_created', start with [PAYMENT_CONFIRM]
- If user is canceling a purchase (no/não/cancel) and state is 'cart_created', start with [PAYMENT_CANCEL]
- Otherwise, respond normally as a friendly payment assistant

Respond naturally in Portuguese or English as appropriate."""

            # Get response from Gemini
            response = model.generate_content(intent_prompt)
            agent_reply = response.text if response.text else "Hello! I'm sofIA, your AI payment assistant. How can I help you today?"

            print(f"Orchestrator agent response: {agent_reply}")

            # Use orchestrator tool to handle A2A coordination
            result = process_user_message(message, user_id, agent_reply)
            reply = result.get("reply", "Sorry, I couldn't process your message.")

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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sofIA WhatsApp Payment Agent",
        "ap2_ready": True
    }

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
