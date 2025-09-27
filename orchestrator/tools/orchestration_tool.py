"""
Orchestration Tool - Simple functions for conversation flow and A2A coordination
"""

from typing import Dict, Any
from datetime import datetime

# Import memory system
from sofIA.memory import SupabaseMemoryManager

# Initialize memory manager
memory_manager = SupabaseMemoryManager()

# Global session storage (in production, use proper session management)
_user_sessions = {}
_mock_payment_processor = {}

# Shared AP2 agent instance for consistent state across requests
_ap2_agent = None

def _get_ap2_agent():
    """Get or create shared AP2 agent instance"""
    global _ap2_agent
    if _ap2_agent is None:
        from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
        _ap2_agent = AP2PaymentAgent(
            agent_id="sofia_orchestrator",
            merchant_id="demo_merchant"
        )
    return _ap2_agent


def process_user_message(message: str, user_id: str, agent_reply: str) -> Dict[str, Any]:
    """Process user message and coordinate A2A communication with memory"""

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

    # Get memory context for enhanced AI understanding
    try:
        memory_context = memory_manager.get_memory_summary(user_id)
        print(f"🧠 Memory context: {memory_context}")
    except Exception as e:
        print(f"⚠️ Memory context error: {e}")
        memory_context = "No memory context available."

    # Check if agent detected specific intents and coordinate accordingly
    coordination_result = _handle_agent_intent(agent_reply, message, user_id, session)

    if coordination_result:
        reply = coordination_result["reply"]
        session.update(coordination_result.get("session_updates", {}))
    else:
        reply = agent_reply

    session["conversation_history"].append({"role": "assistant", "message": reply})

    # Save conversation to persistent memory
    try:
        context_data = {
            "session_id": session.get("session_id"),
            "payment_state": session["payment_state"],
            "memory_context": memory_context
        }
        memory_manager.save_conversation(user_id, message, reply, context_data)
        print(f"💾 Conversation saved to memory for user {user_id}")
    except Exception as e:
        print(f"⚠️ Failed to save conversation to memory: {e}")

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
    elif "[PAYMENT_CONFIRM]" in agent_reply and session["payment_state"] == "cart_created":
        print("✅ Agent detected payment confirmation - sofIA executing payment!")
        return _process_payment(user_id, session)
    
    return None


def _create_payment_intent(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Create AP2 Intent Mandate and prepare Cart for user confirmation"""

    # Extract product info using AI
    product_info = _extract_product_info(message)

    # Check if amount is required but not provided
    if product_info.get('requires_amount') and product_info.get('price', 0) == 0:
        return {
            "reply": f"Para fazer a {product_info['name']}, preciso saber o valor. Qual o valor que você gostaria de transferir?",
            "session_updates": {
                "payment_state": "awaiting_amount",
                "product_info": product_info
            }
        }

    # AP2 Protocol Step 1: Create Intent Mandate
    try:
        from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
        from ap2.types.payment_request import PaymentItem, PaymentCurrencyAmount

        print(f"🤖 sofIA Agent creating Intent Mandate for: {product_info['name']}")

        # Get shared AP2 agent for processing
        ap2_agent = _get_ap2_agent()

        # Step 1: Create Intent Mandate (captures user's intent)
        intent_result = ap2_agent.create_intent_mandate(
            user_message=message,
            user_id=user_id,
            merchants=["sofIA Payment Agent"],
            max_price=product_info['price'],
            requires_confirmation=True  # User must confirm cart
        )

        if not intent_result:
            raise Exception("Failed to create Intent Mandate")

        intent_id = next(iter(ap2_agent.active_intents.keys()), "unknown")
        print(f"✅ Intent Mandate created: {intent_id}")

        # Step 2: Agent creates Cart Mandate with specific items (per AP2 protocol)
        payment_item = PaymentItem(
            label=product_info['name'],
            amount=PaymentCurrencyAmount(
                value=product_info['price'],
                currency=product_info['currency']
            )
        )

        cart_result = ap2_agent.create_cart_mandate(
            intent_id=intent_id,
            items=[payment_item]
        )

        if not cart_result:
            raise Exception("Failed to create Cart Mandate")

        cart_id = next(iter(ap2_agent.active_carts.keys()), "unknown")
        print(f"✅ Cart Mandate created: {cart_id}")

        # Present cart to user for confirmation (AP2 protocol requirement)
        reply = f"""🛒 **Carrinho preparado pela sofIA**

**{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}

🔐 Intent ID: `{intent_id}`
📋 Cart ID: `{cart_id}`

Este carrinho foi criado com base na sua solicitação. A sofIA pode processar o pagamento automaticamente após sua confirmação.

**Confirmar compra?** (Responda 'sim' ou 'não')"""

        return {
            "reply": reply,
            "session_updates": {
                "payment_state": "cart_created",
                "intent_id": intent_id,
                "cart_id": cart_id,
                "product_info": product_info
            }
        }

    except Exception as e:
        print(f"AP2 Intent/Cart creation failed: {e}")
        return {
            "reply": f"Desculpe, houve um problema ao preparar o pagamento para {product_info['name']}. Tente novamente.",
            "session_updates": {"payment_state": "idle"}
        }


def _process_payment(user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Complete payment after user confirmation (AP2 Protocol Step 3)"""

    try:
        product_info = session["product_info"]
        cart_id = session["cart_id"]

        # AP2 Protocol Step 3: Agent executes payment after user confirmation
        from ap2.types.payment_request import PaymentResponse

        print("🤖 sofIA Agent executing payment after user confirmation")

        # Get shared AP2 agent for payment processing
        ap2_agent = _get_ap2_agent()

        # Create payment response (agent handles payment execution)
        payment_response = PaymentResponse(
            request_id=f"req-{cart_id}",
            method_name="sofIA_agent_payment"
        )

        # Step 3: Create Payment Mandate (agent executes the payment)
        payment_result = ap2_agent.create_payment_mandate(
            cart_id=cart_id,
            payment_response=payment_response,
            user_id=user_id
        )

        if not payment_result:
            raise Exception("Payment Mandate creation failed")

        # Generate transaction ID
        transaction_id = f"sofia_txn_{datetime.now().timestamp()}"

        print(f"✅ Payment executed successfully by sofIA Agent")

        # Save transaction to memory
        try:
            transaction_data = {
                "transaction_id": transaction_id,
                "amount": product_info['price'],
                "currency": product_info['currency'],
                "product": product_info['name'],
                "status": "completed",
                "payment_method": "sofIA",
                "session_id": session.get("session_id")
            }
            memory_manager.save_transaction(user_id, transaction_data)
            print(f"💾 Transaction saved to memory: {transaction_id}")
        except Exception as e:
            print(f"⚠️ Failed to save transaction to memory: {e}")

        # Success response - payment completed by agent
        reply = f"""✅ **Pagamento concluído com sucesso!**

**{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}

🔐 Transaction ID: `{transaction_id}`
🤖 Executado pela sofIA via protocolo AP2
📱 Status: Concluído

Obrigada por usar a sofIA! Posso ajudar com mais alguma coisa?"""

        return {
            "reply": reply,
            "session_updates": {
                "payment_state": "completed",
                "transaction_id": transaction_id
            }
        }

    except Exception as e:
        print(f"Payment execution failed: {e}")
        return {
            "reply": "❌ Houve um erro ao processar o pagamento. Tente novamente.",
            "session_updates": {"payment_state": "idle"}
        }


def _extract_product_info(message: str) -> Dict[str, Any]:
    """Extract product information from message using AI"""
    try:
        import google.generativeai as genai
        import os

        # Configure Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Create prompt for product extraction
        extraction_prompt = f"""Analyze this user message and extract what they want to buy/pay for.

User message: "{message}"

Based on the message, determine:
1. What product/service they want
2. Appropriate price in BRL
3. Product name

Common examples:
- "enviar um pix" = Transfer money via PIX (amount should be asked)
- "comprar café" = Coffee (~R$ 8-15)
- "pagar almoço" = Lunch (~R$ 25-35)
- "comprar celular" = Phone (~R$ 800-2000)
- "pagar conta" = Bill payment (amount varies)

Respond in this exact JSON format:
{{"name": "Product Name", "price": 0.00, "currency": "BRL", "requires_amount": true/false}}

If they didn't specify an amount and it's needed (like PIX transfer), set requires_amount to true and price to 0.00."""

        # Get response from Gemini
        response = model.generate_content(extraction_prompt)

        if response.text:
            import json
            # Try to parse JSON response
            try:
                # Clean the response to extract JSON
                response_text = response.text.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].strip()

                product_info = json.loads(response_text)

                # Ensure required fields
                if not all(key in product_info for key in ["name", "price", "currency"]):
                    raise ValueError("Missing required fields")

                return product_info

            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse AI response: {e}")
                print(f"AI response was: {response.text}")

    except Exception as e:
        print(f"AI product extraction failed: {e}")

    # Fallback for common patterns
    message_lower = message.lower()
    if "pix" in message_lower:
        return {"name": "Transferência PIX", "price": 0.00, "currency": "BRL", "requires_amount": True}
    elif any(word in message_lower for word in ["café", "coffee"]):
        return {"name": "Café", "price": 12.00, "currency": "BRL", "requires_amount": False}
    elif any(word in message_lower for word in ["almoço", "lunch"]):
        return {"name": "Almoço", "price": 28.00, "currency": "BRL", "requires_amount": False}

    return {"name": "Serviço", "price": 0.00, "currency": "BRL", "requires_amount": True}




def get_user_session(user_id: str) -> Dict[str, Any]:
    """Get user session information"""
    return _user_sessions.get(user_id, {})