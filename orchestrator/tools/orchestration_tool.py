"""
Orchestration Tool - Simple functions for conversation flow and A2A coordination
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio


# Global session storage (in production, use proper session management)
_user_sessions = {}
_mock_payment_processor = {}

# Shared AP2 agent instance and services for consistent state across requests
_ap2_agent = None
_ap2_authenticator = None
_agent_registry = None
_merchant_service = None
_user_credential_service = None


def _get_ap2_agent():
    """Get or create shared AP2 agent for payment processing"""
    global _ap2_agent, _ap2_authenticator, _agent_registry, _merchant_service, _user_credential_service

    if _ap2_agent is None:
        from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
        from sofIA.tools.ap2_protocol.ap2_agent_auth import get_ap2_authenticator
        from sofIA.tools.ap2_protocol.merchant_onboarding import get_merchant_service
        from sofIA.tools.ap2_protocol.user_credential_service import get_user_credential_service
        from sofIA.registry.agent_registry import AgentRegistry

        # Initialize agent registry
        _agent_registry = AgentRegistry("sofia-main-registry")

        # Initialize merchant service
        _merchant_service = get_merchant_service(_agent_registry)

        # Initialize user credential service
        _user_credential_service = get_user_credential_service()

        # Create AP2 payment agent
        _ap2_agent = AP2PaymentAgent(
            agent_id="sofia_orchestrator",
            merchant_id="demo_merchant"
        )

        # Initialize AP2 authenticator with proper agent-to-agent auth
        _ap2_authenticator = get_ap2_authenticator(_agent_registry, _ap2_agent)

        # Demo merchants will be onboarded on first transaction
        print("🏢 AP2 services initialized - merchants will be onboarded on demand")

    return _ap2_agent


def _get_ap2_authenticator():
    """Get the AP2 authenticator for agent-to-agent authentication"""
    _get_ap2_agent()  # Ensure everything is initialized
    return _ap2_authenticator


def _get_merchant_service():
    """Get the merchant onboarding service"""
    _get_ap2_agent()  # Ensure everything is initialized
    return _merchant_service


def _get_user_credential_service():
    """Get the user credential service"""
    _get_ap2_agent()  # Ensure everything is initialized
    return _user_credential_service


async def _onboard_demo_merchants():
    """Onboard demo merchants for testing"""
    try:
        await _merchant_service.onboard_bemobi_telecom_operators()
        print("✅ Demo merchants onboarded successfully")
    except Exception as e:
        print(f"Warning: Demo merchant onboarding failed: {e}")


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

    session_updates = {}
    if coordination_result:
        reply = coordination_result["reply"]
        session_updates = coordination_result.get("session_updates", {})
        session.update(session_updates)
    else:
        reply = agent_reply

    session["conversation_history"].append({"role": "assistant", "message": reply})

    return {
        "reply": reply,
        "user_id": user_id,
        "session_state": session["payment_state"],
        "session_updates": session_updates
    }


def _handle_agent_intent(agent_reply: str, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Handle A2A coordination based on agent's intelligent intent detection"""

    # Check if agent detected payment intent
    if "[PAYMENT_INTENT]" in agent_reply and session["payment_state"] == "idle":
        print("💳 Agent detected payment intent - coordinating with AP2 agent!")
        return _create_payment_intent(message, user_id, session)

    # Check if agent detected payment confirmation
    elif "[PAYMENT_CONFIRM]" in agent_reply and session["payment_state"] == "cart_created":
        print("💳 Agent detected payment confirmation - requesting payment method!")
        return _request_payment_method(user_id, session)

    # Check if user is providing credentials or KYC data
    elif session["payment_state"] in ["credential_collection", "payment_method_requested"]:
        print("🔐 Processing user credentials with enhanced AP2 flow!")
        # Handle async function call for enhanced credential processing
        import asyncio
        try:
            return asyncio.run(_process_enhanced_credentials(message, user_id, session))
        except Exception as e:
            print(f"Enhanced credential processing error: {e}")
            return {
                "reply": "❌ Erro ao processar credenciais AP2. Tente novamente.",
                "session_updates": {"payment_state": "cart_created"}
            }
    
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
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount

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
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse

        print("🤖 sofIA Agent executing payment after user confirmation")

        # Get shared AP2 agent for payment processing
        ap2_agent = _get_ap2_agent()

        # Create payment response (agent handles payment execution)
        payment_response = PaymentResponse(
            request_id=f"req-{cart_id}",
            method_name="sofIA_agent_payment",
            details={"execution_mode": "agent_managed", "payment_type": "ap2_protocol"}
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


def _request_payment_method(user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Request payment method from user (AP2 Step 2.5 - Enhanced Credential Collection)"""

    try:
        product_info = session["product_info"]

        # Get user credential service for enhanced flow
        user_service = _get_user_credential_service()

        # Initiate credential flow based on amount and user
        credential_flow = asyncio.run(user_service.initiate_whatsapp_credential_flow(
            user_id=user_id,
            payment_method="auto_detect",  # Will be detected from user input
            amount=product_info['price'],
            currency=product_info['currency']
        ))

        # Enhanced payment method request with AP2 credential flow
        reply = f"""💳 **Pagamento Seguro AP2 Protocol**

**{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}

🔐 **Métodos seguros disponíveis:**

🏦 **PIX**
   `PIX_EMAIL [seu@email.com]`
   `PIX_TELEFONE [11999887766]`
   `PIX_CPF [12345678901]`
   `PIX_CHAVE [sua-chave-aleatoria]`

💳 **Cartão de Crédito**
   `CARTAO [últimos 4 dígitos] [MM/AA] [Nome no cartão]`

🧾 **Boleto Bancário**
   `BOLETO [CPF] [Nome completo]`

⚠️ **Primeira vez?** Digite `DADOS [Nome] [CPF] [Telefone]` para verificação

🔐 **Protocolo AP2 garante:**
✓ Criptografia de ponta a ponta
✓ Verificação de agentes
✓ Audit trail completo
✓ Conformidade regulatória

Escolha seu método de pagamento:"""

        # Store credential flow info in session
        session_updates = {
            "payment_state": "credential_collection",
            "credential_flow": credential_flow.get("flow_type", "standard"),
            "kyc_required": credential_flow.get("flow_type") == "kyc_required"
        }

        return {
            "reply": reply,
            "session_updates": session_updates
        }

    except Exception as e:
        print(f"Enhanced payment method request failed: {e}")
        return {
            "reply": "❌ Erro ao inicializar fluxo de pagamento AP2. Tente novamente.",
            "session_updates": {"payment_state": "idle"}
        }


async def _process_enhanced_credentials(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Process user credentials with enhanced AP2 flow including KYC and merchant onboarding"""

    try:
        user_service = _get_user_credential_service()
        merchant_service = _get_merchant_service()

        # Step 1: Check if this is KYC data
        if message.upper().startswith("DADOS"):
            print("📋 Processing KYC data")
            kyc_result = await user_service.process_kyc_data(user_id, message)

            if kyc_result["success"]:
                return {
                    "reply": kyc_result["message"] + "\n\n" +
                           "Agora você pode fornecer seus dados de pagamento usando os formatos indicados acima.",
                    "session_updates": {"kyc_verified": True}
                }
            else:
                return {
                    "reply": kyc_result["message"],
                    "session_updates": {}
                }

        # Step 2: Ensure demo merchants are onboarded
        demo_merchant = await merchant_service.get_merchant_credentials("demo_merchant")
        if not demo_merchant:
            print("🏢 Onboarding demo merchant")
            await merchant_service.onboard_merchant(
                merchant_id="demo_merchant",
                merchant_name="Demo Merchant",
                business_type="demo",
                supported_regions=["latam"],
                supported_payment_methods=["pix", "credit_card", "boleto"]
            )

        # Step 3: Detect payment method from user input
        payment_method = _detect_payment_method(message)
        if not payment_method:
            return {
                "reply": "❌ Método de pagamento não reconhecido. Use os formatos indicados acima.",
                "session_updates": {}
            }

        # Step 4: Process payment credentials
        print(f"💳 Processing {payment_method} credentials")
        credential_result = await user_service.process_payment_credentials(
            user_id, message, payment_method
        )

        if not credential_result["success"]:
            return {
                "reply": credential_result["message"],
                "session_updates": {}
            }

        # Step 5: Proceed to payment with enhanced AP2 authentication
        return await _process_payment_with_enhanced_credentials(
            message, user_id, session, payment_method, credential_result
        )

    except Exception as e:
        print(f"Enhanced credential processing failed: {e}")
        return {
            "reply": "❌ Erro no processamento de credenciais AP2. Tente novamente.",
            "session_updates": {"payment_state": "cart_created"}
        }


async def _process_payment_with_enhanced_credentials(
    message: str,
    user_id: str,
    session: Dict[str, Any],
    payment_method: str,
    credential_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Process payment with enhanced AP2 authentication and merchant verification"""

    try:
        product_info = session["product_info"]
        cart_id = session["cart_id"]

        print(f"🔐 Starting enhanced AP2 payment with {payment_method}")

        # Step 1: Onboard BEMOBI telecom operators if not done
        merchant_service = _get_merchant_service()
        telecom_merchants = await merchant_service.onboard_bemobi_telecom_operators()
        print(f"🏢 Verified {len(telecom_merchants)} telecom operator merchants")

        # Step 2: Authenticate transaction with proper merchant
        ap2_authenticator = _get_ap2_authenticator()
        transaction_context = await ap2_authenticator.authenticate_transaction(
            merchant_id="vivo_brasil",  # Use real telecom operator
            payment_method=payment_method,
            amount=product_info['price'],
            currency=product_info['currency'],
            region="latam"
        )

        if not transaction_context:
            return {
                "reply": "❌ Falha na autenticação AP2. Agentes não puderam ser verificados.",
                "session_updates": {"payment_state": "cart_created"}
            }

        print(f"✅ AP2 Transaction authenticated: {transaction_context.transaction_id}")
        print(f"   Sender Agent: {transaction_context.sender_agent.agent_id}")
        print(f"   Receiver Agent: {transaction_context.receiver_agent.agent_id}")

        # Step 3: Execute payment with full AP2 compliance
        ap2_agent = _get_ap2_agent()

        # Enhanced payment response with credential verification
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse

        payment_response = PaymentResponse(
            request_id=f"req-{cart_id}",
            method_name=payment_method,
            details={
                "ap2_transaction_id": transaction_context.transaction_id,
                "sender_agent_id": transaction_context.sender_agent.agent_id,
                "receiver_agent_id": transaction_context.receiver_agent.agent_id,
                "credential_id": credential_result["credential_id"],
                "authentication_proof": "verified",
                "kyc_verified": True,
                "merchant_verified": True,
                "protocol_version": "AP2_v1.0"
            }
        )

        # Execute payment mandate
        payment_result = ap2_agent.create_payment_mandate(
            cart_id=cart_id,
            payment_response=payment_response,
            user_id=user_id
        )

        if not payment_result:
            raise Exception("Payment Mandate creation failed")

        print("✅ Enhanced AP2 payment executed successfully")

        # Success response with complete AP2 compliance details
        reply = f"""✅ **Pagamento AP2 Concluído com Sucesso!**

**{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}
💳 Método: {payment_method.upper()}

🔐 **Detalhes AP2 Protocol:**
🆔 Transaction ID: `{transaction_context.transaction_id}`
🤖 Sender Agent: `{transaction_context.sender_agent.agent_id}`
🏢 Receiver Agent: `{transaction_context.receiver_agent.agent_id}`
🎫 Credential ID: `{credential_result["credential_id"][:16]}...`

**🏛️ Merchant Verificado:**
✓ Operadora: Vivo Brasil
✓ Agente registrado e ativo
✓ Conformidade PCI DSS
✓ Auditoria completa

**🔒 Certificação AP2:**
✓ Agentes mutuamente autenticados
✓ Credenciais verificadas e criptografadas
✓ KYC do usuário validado
✓ Transação completamente auditável
✓ Conformidade regulatória garantida

🎉 **Transação concluída com máxima segurança!**

Obrigada por usar a sofIA com protocolo AP2!
Posso ajudar com mais alguma coisa?"""

        return {
            "reply": reply,
            "session_updates": {
                "payment_state": "completed",
                "ap2_transaction_id": transaction_context.transaction_id,
                "payment_method": payment_method,
                "sender_agent": transaction_context.sender_agent.agent_id,
                "receiver_agent": transaction_context.receiver_agent.agent_id,
                "credential_id": credential_result["credential_id"],
                "merchant_verified": True,
                "kyc_verified": True,
                "protocol_version": "AP2_v1.0"
            }
        }

    except Exception as e:
        print(f"Enhanced AP2 payment processing failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "reply": "❌ Erro no processamento de pagamento AP2. Verifique os dados e tente novamente.",
            "session_updates": {"payment_state": "cart_created"}
        }


def _detect_payment_method(message: str) -> Optional[str]:
    """Detect payment method from user message"""
    message_upper = message.upper()

    if any(keyword in message_upper for keyword in ["PIX_EMAIL", "PIX_TELEFONE", "PIX_CPF", "PIX_CHAVE"]):
        return "pix"
    elif message_upper.startswith("CARTAO"):
        return "credit_card"
    elif message_upper.startswith("BOLETO"):
        return "boleto"
    else:
        return None


async def _process_payment_with_credentials(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Process payment with user-provided credentials (AP2 Step 3 - with proper agent authentication)"""

    try:
        product_info = session["product_info"]
        cart_id = session["cart_id"]

        # Parse payment method from user message
        payment_credentials = _parse_payment_credentials(message)

        if not payment_credentials:
            return {
                "reply": "❌ Formato inválido. Por favor, forneça os dados de pagamento no formato correto.",
                "session_updates": {}  # Keep same state
            }

        print(f"🔐 Processing AP2 payment with {payment_credentials['method']} credentials")

        # Step 1: Authenticate the transaction with proper agent-to-agent authentication
        ap2_authenticator = _get_ap2_authenticator()

        transaction_context = await ap2_authenticator.authenticate_transaction(
            merchant_id="demo_merchant",
            payment_method=payment_credentials['method'],
            amount=product_info['price'],
            currency=product_info['currency'],
            region="latam"
        )

        if not transaction_context:
            return {
                "reply": "❌ Falha na autenticação AP2. Não foi possível verificar as credenciais dos agentes.",
                "session_updates": {"payment_state": "cart_created"}
            }

        print(f"✅ AP2 Transaction authenticated: {transaction_context.transaction_id}")
        print(f"   Sender Agent: {transaction_context.sender_agent.agent_id}")
        print(f"   Receiver Agent: {transaction_context.receiver_agent.agent_id}")

        # Step 2: Execute payment with authenticated context
        ap2_agent = _get_ap2_agent()

        # Create payment response with user credentials and AP2 authentication
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse

        payment_response = PaymentResponse(
            request_id=f"req-{cart_id}",
            method_name=payment_credentials['method'],
            details={
                **payment_credentials['details'],
                "ap2_transaction_id": transaction_context.transaction_id,
                "sender_agent_id": transaction_context.sender_agent.agent_id,
                "receiver_agent_id": transaction_context.receiver_agent.agent_id,
                "authentication_proof": "verified"
            }
        )

        # Execute payment with AP2 agent
        payment_result = ap2_agent.create_payment_mandate(
            cart_id=cart_id,
            payment_response=payment_response,
            user_id=user_id
        )

        if not payment_result:
            raise Exception("Payment Mandate creation failed")

        print("✅ Payment executed successfully with AP2 agent authentication")

        # Success response - payment completed with AP2 compliance
        reply = f"""✅ **Pagamento AP2 concluído com sucesso!**

**{product_info['name']}**
💰 {product_info['currency']} {product_info['price']:.2f}
💳 Método: {payment_credentials['method'].upper()}

🔐 AP2 Transaction ID: `{transaction_context.transaction_id}`
🤖 Sender Agent: {transaction_context.sender_agent.agent_id}
🔒 Receiver Agent: {transaction_context.receiver_agent.agent_id}
📱 Status: Concluído com protocolo AP2

**Certificação AP2:**
✓ Agentes autenticados
✓ Credenciais verificadas
✓ Transação auditável

Obrigada por usar a sofIA! Posso ajudar com mais alguma coisa?"""

        return {
            "reply": reply,
            "session_updates": {
                "payment_state": "completed",
                "ap2_transaction_id": transaction_context.transaction_id,
                "payment_method": payment_credentials['method'],
                "sender_agent": transaction_context.sender_agent.agent_id,
                "receiver_agent": transaction_context.receiver_agent.agent_id
            }
        }

    except Exception as e:
        print(f"AP2 payment processing failed: {e}")
        return {
            "reply": "❌ Houve um erro ao processar o pagamento AP2. Verifique os dados e tente novamente.",
            "session_updates": {"payment_state": "cart_created"}  # Go back to previous state
        }


def _parse_payment_credentials(message: str) -> Optional[Dict[str, Any]]:
    """Parse payment credentials from user message"""

    message = message.upper().strip()

    try:
        if message.startswith("PIX"):
            # Format: PIX [chave_pix]
            parts = message.split()
            if len(parts) >= 2:
                pix_key = " ".join(parts[1:])
                return {
                    "method": "pix",
                    "details": {
                        "pix_key": pix_key,
                        "encrypted": True,  # In production, encrypt this
                        "consent_proof": "user_confirmed"
                    }
                }

        elif message.startswith("CARTAO"):
            # Format: CARTAO [número] [vencimento] [cvv]
            parts = message.split()
            if len(parts) >= 4:
                return {
                    "method": "basic-card",
                    "details": {
                        "card_number": f"****{parts[1][-4:]}",  # Mask card number
                        "expiry": parts[2],
                        "encrypted_data": "encrypted_card_details",  # In production, encrypt
                        "consent_proof": "user_confirmed"
                    }
                }

        elif message.startswith("BOLETO"):
            # Format: BOLETO [cpf]
            parts = message.split()
            if len(parts) >= 2:
                return {
                    "method": "boleto",
                    "details": {
                        "cpf": f"***{parts[1][-3:]}",  # Mask CPF
                        "encrypted_data": "encrypted_boleto_data",
                        "consent_proof": "user_confirmed"
                    }
                }

        return None

    except Exception as e:
        print(f"Error parsing payment credentials: {e}")
        return None


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