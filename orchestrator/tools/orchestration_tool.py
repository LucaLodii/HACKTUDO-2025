"""
Orchestration Tool - Simple functions for conversation flow and A2A coordination
"""

from typing import Dict, Any
from datetime import datetime


# Global session storage (in production, use proper session management)
_user_sessions = {}
_mock_payment_processor = {}


def process_user_message(message: str, user_id: str, agent_reply: str) -> Dict[str, Any]:
    """Process user message and coordinate A2A communication"""

    # Initialize user session
    if user_id not in _user_sessions:
        _user_sessions[user_id] = {
            "conversation_history": [],
            "current_intent": None,
            "payment_state": "idle"
        }

    session = _user_sessions[user_id]
    session["conversation_history"].append({"role": "user", "message": message})

    print(f"💬 Processing message: '{message}' from user: {user_id}")
    print(f"🔄 Current state: {session['payment_state']}")

    # Check if agent detected specific intents and coordinate accordingly
    coordination_result = _handle_agent_intent(agent_reply, message, user_id, session)

    if coordination_result:
        reply = coordination_result["reply"]
        session.update(coordination_result.get("session_updates", {}))
    else:
        reply = agent_reply

    session["conversation_history"].append({"role": "assistant", "message": reply})

    return {
        "reply": reply,
        "user_id": user_id,
        "session_state": session["payment_state"]
    }


def _handle_agent_intent(agent_reply: str, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Handle A2A coordination based on agent's intelligent intent detection"""

    # Check if agent detected payment intent
    if "[PAYMENT_INTENT]" in agent_reply and session["payment_state"] == "idle":
        print("💳 Agent detected payment intent - coordinating with AP2 agent!")
        return _create_payment_intent(message, user_id, session)

    # Check if agent detected payment confirmation
    elif "[PAYMENT_CONFIRM]" in agent_reply and session["payment_state"] == "intent_created":
        print("✅ Agent detected payment confirmation - coordinating payment processing!")
        return _process_payment(user_id, session)
    
    return None


def _create_payment_intent(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Create payment intent via true A2A coordination with sofIA agent"""

    # Extract product info
    product_info = _extract_product_info(message)

    # TRUE A2A: Call sofIA agent to handle payment processing
    try:
        # Import sofIA agent for A2A communication
        from sofIA.agent import root_agent

        # Create A2A request context for sofIA agent
        a2a_context = f"""
Agent-to-Agent Request from Orchestrator:

User wants to purchase: {message}
User ID: {user_id}
Product: {product_info['name']}
Price: {product_info['currency']} {product_info['price']:.2f}

Please create an AP2 Intent Mandate for this purchase request and return the intent ID.
Use your AP2 protocol tools to process this payment intent.
"""

        # Call sofIA agent via A2A
        sofia_response = root_agent.run(a2a_context)
        sofia_reply = sofia_response.text if hasattr(sofia_response, 'text') else str(sofia_response)

        print(f"🤖 A2A Response from sofIA agent: {sofia_reply}")

        # Parse sofIA agent response (in real implementation, use structured response)
        # For now, create the session updates based on successful A2A call
        session_updates = {
            "payment_state": "intent_created",
            "current_intent": f"a2a_intent_{datetime.now().timestamp()}",
            "product_info": product_info,
            "sofia_response": sofia_reply
        }

        reply = f"""Perfect! I coordinated with sofIA agent for your purchase:

🛍️ **{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}

✅ sofIA Agent Response: {sofia_reply[:200]}...

Your secure payment is ready via AP2 protocol through A2A coordination.

Would you like to confirm this purchase? (Reply 'yes' or 'no')"""

        return {
            "reply": reply,
            "session_updates": session_updates
        }

    except Exception as e:
        print(f"A2A coordination with sofIA agent failed: {e}")
        return {
            "reply": "Sorry, I had trouble coordinating with the payment agent. Let me try again.",
            "session_updates": {"payment_state": "idle"}
        }


def _process_payment(user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment via true A2A coordination with sofIA agent"""

    try:
        product_info = session["product_info"]
        intent_id = session["current_intent"]

        # TRUE A2A: Call sofIA agent to complete payment processing
        from sofIA.agent import root_agent

        # Create A2A request for payment completion
        a2a_payment_context = f"""
Agent-to-Agent Payment Request from Orchestrator:

Complete payment processing for:
User ID: {user_id}
Intent ID: {intent_id}
Product: {product_info['name']}
Amount: {product_info['currency']} {product_info['price']:.2f}

Please process this payment using your AP2 protocol tools and create the final Payment Mandate.
Return the transaction details.
"""

        # Call sofIA agent for payment completion
        sofia_payment_response = root_agent.run(a2a_payment_context)
        sofia_payment_reply = sofia_payment_response.text if hasattr(sofia_payment_response, 'text') else str(sofia_payment_response)

        print(f"🤖 A2A Payment Response from sofIA agent: {sofia_payment_reply}")

        # Generate transaction ID for demo
        transaction_id = f"a2a_txn_{datetime.now().timestamp()}"

        session_updates = {
            "payment_state": "completed",
            "transaction_id": transaction_id,
            "sofia_payment_response": sofia_payment_reply
        }

        reply = f"""✅ **Payment Successful via A2A Coordination!**

Transaction ID: `{transaction_id}`
Amount: {product_info['currency']} {product_info['price']:.2f}
Status: Completed

🤖 sofIA Agent Processing: {sofia_payment_reply[:150]}...

🔐 Secured by AP2 Protocol
🤝 Processed via Agent-to-Agent Communication

Thank you for using sofIA! Is there anything else I can help you with?"""

        return {
            "reply": reply,
            "session_updates": session_updates
        }

    except Exception as e:
        print(f"A2A payment coordination error: {e}")
        return {
            "reply": "❌ Sorry, there was an error coordinating payment with sofIA agent. Please try again.",
            "session_updates": {}
        }


def _extract_product_info(message: str) -> Dict[str, Any]:
    """Extract product information from message"""
    products = {
        "coffee": {"name": "Premium Coffee", "price": 15.50, "currency": "BRL"},
        "café": {"name": "Café Premium", "price": 15.50, "currency": "BRL"},
        "lunch": {"name": "Lunch Combo", "price": 25.00, "currency": "BRL"},
        "almoço": {"name": "Combo Almoço", "price": 25.00, "currency": "BRL"},
        "phone": {"name": "Smartphone", "price": 899.99, "currency": "BRL"},
        "celular": {"name": "Smartphone", "price": 899.99, "currency": "BRL"},
    }

    message_lower = message.lower()
    for keyword, product in products.items():
        if keyword in message_lower:
            return product

    return {"name": "General Item", "price": 20.00, "currency": "BRL"}


def _create_mock_payment_intent(amount: float, currency: str, description: str) -> Dict[str, Any]:
    """Create mock payment intent"""
    intent_id = f"bemobi_{datetime.now().timestamp()}"

    _mock_payment_processor[intent_id] = {
        "id": intent_id,
        "amount": amount,
        "currency": currency,
        "description": description,
        "status": "pending"
    }

    return {
        "success": True,
        "payment_intent_id": intent_id,
        "amount": amount,
        "currency": currency
    }


def _process_mock_payment(payment_intent_id: str, payment_method: str) -> Dict[str, Any]:
    """Process mock payment"""
    if payment_intent_id not in _mock_payment_processor:
        return {"success": False, "error": "Payment intent not found"}

    transaction = _mock_payment_processor[payment_intent_id]
    transaction["status"] = "completed"
    transaction["payment_method"] = payment_method

    return {
        "success": True,
        "transaction_id": f"txn_{payment_intent_id}",
        "status": "completed",
        "amount": transaction["amount"],
        "currency": transaction["currency"]
    }


def get_user_session(user_id: str) -> Dict[str, Any]:
    """Get user session information"""
    return _user_sessions.get(user_id, {})