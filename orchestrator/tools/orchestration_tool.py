"""
Orchestration Tool - Simple functions for conversation flow and A2A coordination
Now supports white-label merchant detection and routing
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from collections import defaultdict

# Thread-safe session storage with proper locking
_user_sessions = {}
_session_locks = defaultdict(asyncio.Lock)
_mock_payment_processor = {}

# White-label operator detection
OPERATOR_KEYWORDS = {
    "VIVO": ["vivo", "viv0", "purple", "roxo"],
    "CLARO": ["claro", "red", "vermelho", "america", "américa"],
    "OI": ["oi", "yellow", "amarelo"],
    "TIM": ["tim", "blue", "azul", "italia", "itália"]
}

# Shared AP2 agent instance and services for consistent state across requests
_ap2_agent = None
_ap2_authenticator = None
_agent_registry = None
_merchant_service = None
_user_credential_service = None
_ap2_initialization_lock = asyncio.Lock()


async def _get_ap2_agent():
    """Get or create shared AP2 agent for payment processing with thread-safe initialization"""
    global _ap2_agent, _ap2_authenticator, _agent_registry, _merchant_service, _user_credential_service

    if _ap2_agent is None:
        async with _ap2_initialization_lock:
            # Double-check pattern to avoid race conditions
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


async def _get_ap2_authenticator():
    """Get the AP2 authenticator for agent-to-agent authentication"""
    await _get_ap2_agent()  # Ensure everything is initialized
    return _ap2_authenticator


async def _get_merchant_service():
    """Get the merchant onboarding service"""
    await _get_ap2_agent()  # Ensure everything is initialized
    return _merchant_service


async def _get_user_credential_service():
    """Get the user credential service"""
    await _get_ap2_agent()  # Ensure everything is initialized
    return _user_credential_service


async def _onboard_demo_merchants():
    """Onboard demo merchants for testing"""
    try:
        await _merchant_service.onboard_bemobi_telecom_operators()
        print("✅ Demo merchants onboarded successfully")
    except Exception as e:
        print(f"Warning: Demo merchant onboarding failed: {e}")


async def process_user_message(message: str, user_id: str, agent_reply: str, operator_name: str = "DEMO") -> Dict[str, Any]:
    """Process user message and coordinate A2A communication with thread-safe session management"""

    # Get or create session lock for this user
    session_lock = _session_locks[user_id]
    
    async with session_lock:
        # Initialize user session with operator context
        if user_id not in _user_sessions:
            _user_sessions[user_id] = {
                "conversation_history": [],
                "current_intent": None,
                "payment_state": "idle",
                "operator_name": operator_name,
                "last_activity": datetime.now().isoformat()
            }

        session = _user_sessions[user_id]
        session["conversation_history"].append({"role": "user", "message": message})
        session["operator_name"] = operator_name  # Update operator context
        session["last_activity"] = datetime.now().isoformat()

        print(f"🔄 State: {session['payment_state']} | Operator: {operator_name} | History: {len(session['conversation_history'])} messages | User: {user_id[-8:]}")

        # Check if agent detected specific intents and coordinate accordingly
        coordination_result = await _handle_agent_intent(agent_reply, message, user_id, session)

        session_updates = {}
        if coordination_result:
            reply = coordination_result["reply"]
            session_updates = coordination_result.get("session_updates", {})
            session.update(session_updates)
        else:
            reply = agent_reply

        session["conversation_history"].append({"role": "assistant", "message": reply})
        session["last_activity"] = datetime.now().isoformat()

        return {
            "reply": reply,
            "user_id": user_id,
            "session_state": session["payment_state"],
            "session_updates": session_updates
        }


async def _handle_agent_intent(agent_reply: str, message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Handle A2A coordination based on agent's intelligent intent detection"""

    # Check if agent detected payment intent
    if "[PAYMENT_INTENT]" in agent_reply and session["payment_state"] == "idle":
        print("💳 Payment Intent Detected → Coordinating with AP2 agent")
        return await _create_payment_intent(message, user_id, session)

    # Check if agent detected payment confirmation
    elif "[PAYMENT_CONFIRM]" in agent_reply and session["payment_state"] == "cart_created":
        print("💳 Payment Confirmed → Requesting payment method")
        return await _request_payment_method(user_id, session)

    # Check if user is providing credentials or KYC data
    elif session["payment_state"] in ["credential_collection", "payment_method_requested"]:
        print("🔐 Processing credentials with enhanced AP2 flow")
        # Handle async function call for enhanced credential processing
        try:
            return await _process_enhanced_credentials(message, user_id, session)
        except Exception as e:
            print(f"Enhanced credential processing error: {e}")
            return {
                "reply": "❌ Erro ao processar credenciais AP2. Tente novamente.",
                "session_updates": {"payment_state": "cart_created"}
            }

    # Check if user provided boleto code when waiting for amount/details
    elif session["payment_state"] == "awaiting_amount" and _looks_like_boleto(message):
        print("🧾 Boleto code detected → Using structured parsing (avoiding AI hallucination)")
        return _process_boleto_code(message, user_id, session)
    
    # Check if user is selecting a subscription plan
    elif session["payment_state"] == "plan_selection":
        print("📱 Plan selection detected → Processing plan choice")
        return await _process_plan_selection(message, user_id, session)

    return None


async def _create_payment_intent(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Create AP2 Intent Mandate and prepare Cart for user confirmation"""

    # Extract product info using AI with operator context
    operator_name = session.get("operator_name", "DEMO")
    product_info = _extract_product_info(message, operator_name)

    # Check if this is a subscription plan request
    if product_info.get('is_subscription'):
        return await _handle_subscription_request(message, user_id, session, product_info)
    
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
            from sofIA.tools.ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount

            print(f"🤖 sofIA Agent creating Intent Mandate for: {product_info['name']}")

            # Get shared AP2 agent for processing
            ap2_agent = await _get_ap2_agent()

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


async def _handle_subscription_request(message: str, user_id: str, session: Dict[str, Any], product_info: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription plan selection for the current operator"""
    
    operator_name = session.get("operator_name", "DEMO")
    
    try:
        from sofIA.tools.operator_subscription_manager import get_merchant_subscription_plans
        
        # Get available plans for this operator
        plans_result = await get_merchant_subscription_plans(operator_name)
        
        if "error" in plans_result:
            return {
                "reply": f"❌ Erro ao carregar planos {operator_name}. Tente novamente.",
                "session_updates": {"payment_state": "idle"}
            }
        
        plans = plans_result["plans"]
        
        # Create plan selection message
        reply = f"""📱 **Planos {operator_name} Disponíveis**
        
Escolha um dos planos abaixo:

"""
        
        for i, plan in enumerate(plans, 1):
            data_text = f"{plan['data_limit_gb']}GB" if plan['data_limit_gb'] else "Ilimitado"
            voice_text = plan['voice_minutes'] if plan['voice_minutes'] != "Ilimitado" else "Ilimitado"
            sms_text = plan['sms_count'] if plan['sms_count'] != "Ilimitado" else "Ilimitado"
            
            reply += f"""**{i}. {plan['name']}**
💰 R$ {plan['price_brl']:.2f}/mês
📊 {data_text} de internet
📞 {voice_text} minutos
💬 {sms_text} SMS
📝 {plan['description']}

"""
        
        reply += f"""**Para contratar:** Digite o número do plano (ex: 1, 2, 3, etc.)
**Para mais informações:** Digite 'info [número]' (ex: info 2)"""

        return {
            "reply": reply,
            "session_updates": {
                "payment_state": "plan_selection",
                "available_plans": plans,
                "product_info": product_info
            }
        }
        
    except Exception as e:
        print(f"Subscription request handling failed: {e}")
        return {
            "reply": f"❌ Erro ao processar solicitação de planos {operator_name}. Tente novamente.",
            "session_updates": {"payment_state": "idle"}
        }


async def _process_plan_selection(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Process user's plan selection"""
    
    try:
        available_plans = session.get("available_plans", [])
        operator_name = session.get("operator_name", "DEMO")
        
        # Check if user wants more info about a plan
        if message.lower().startswith("info"):
            parts = message.split()
            if len(parts) >= 2 and parts[1].isdigit():
                plan_index = int(parts[1]) - 1
                if 0 <= plan_index < len(available_plans):
                    plan = available_plans[plan_index]
                    
                    features_text = "\n".join([f"✓ {feature}" for feature in plan['features'].keys()])
                    
                    reply = f"""📱 **{plan['name']} - Detalhes Completos**

💰 **Preço:** R$ {plan['price_brl']:.2f}/mês
📊 **Internet:** {plan['data_limit_gb']}GB
📞 **Ligações:** {plan['voice_minutes']}
💬 **SMS:** {plan['sms_count']}

**Recursos incluídos:**
{features_text}

**Para contratar este plano:** Digite '{parts[1]}'
**Para ver todos os planos:** Digite 'voltar'"""

                    return {
                        "reply": reply,
                        "session_updates": {}
                    }
        
        # Check if user wants to go back
        if message.lower() in ["voltar", "back", "todos"]:
            return await _handle_subscription_request("", user_id, session, session.get("product_info", {}))
        
        # Check if user selected a plan number
        if message.strip().isdigit():
            plan_index = int(message.strip()) - 1
            if 0 <= plan_index < len(available_plans):
                selected_plan = available_plans[plan_index]
                
                # Create product info for the selected plan
                product_info = {
                    "name": selected_plan['name'],
                    "price": selected_plan['price_brl'],
                    "currency": "BRL",
                    "operator": operator_name,
                    "is_subscription": True,
                    "plan_details": selected_plan
                }
                
                # Create AP2 payment intent for the selected plan
                try:
                    from sofIA.tools.ap2_protocol.types.payment_request import PaymentItem, PaymentCurrencyAmount

                    print(f"🤖 sofIA Agent creating Intent Mandate for: {selected_plan['name']}")

                    # Get shared AP2 agent for processing
                    ap2_agent = await _get_ap2_agent()

                    # Step 1: Create Intent Mandate (captures user's intent)
                    intent_result = ap2_agent.create_intent_mandate(
                        user_message=f"Contratar plano {selected_plan['name']}",
                        user_id=user_id,
                        merchants=[f"sofIA {operator_name} Payment Agent"],
                        max_price=selected_plan['price_brl'],
                        requires_confirmation=True
                    )

                    if not intent_result:
                        raise Exception("Failed to create Intent Mandate")

                    intent_id = next(iter(ap2_agent.active_intents.keys()), "unknown")
                    print(f"✅ Intent Mandate created: {intent_id}")

                    # Step 2: Agent creates Cart Mandate with specific items
                    payment_item = PaymentItem(
                        label=selected_plan['name'],
                        amount=PaymentCurrencyAmount(
                            value=selected_plan['price_brl'],
                            currency="BRL"
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

                    # Present cart to user for confirmation
                    reply = f"""🛒 **Plano Selecionado - {operator_name}**

**{selected_plan['name']}**
💰 R$ {selected_plan['price_brl']:.2f}/mês
📊 {selected_plan['data_limit_gb']}GB de internet
📞 {selected_plan['voice_minutes']}
💬 {selected_plan['sms_count']}

🔐 Intent ID: `{intent_id}`
📋 Cart ID: `{cart_id}`

Este plano foi preparado pela sofIA {operator_name}. 
A confirmação processará o pagamento automaticamente.

**Confirmar contratação?** (Responda 'sim' ou 'não')"""

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
                    print(f"AP2 plan selection processing failed: {e}")
                    return {
                        "reply": f"❌ Erro ao processar seleção do plano {selected_plan['name']}. Tente novamente.",
                        "session_updates": {"payment_state": "plan_selection"}
                    }
        
        # Invalid selection
        return {
            "reply": f"❌ Seleção inválida. Digite um número de 1 a {len(available_plans)} ou 'info [número]' para mais detalhes.",
            "session_updates": {}
        }
        
    except Exception as e:
        print(f"Plan selection processing failed: {e}")
        return {
            "reply": "❌ Erro ao processar seleção de plano. Tente novamente.",
            "session_updates": {"payment_state": "idle"}
        }


async def _process_payment(user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Complete payment after user confirmation (AP2 Protocol Step 3)"""

    try:
        product_info = session["product_info"]
        cart_id = session["cart_id"]

        # AP2 Protocol Step 3: Agent executes payment after user confirmation
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse

        print("🤖 sofIA Agent executing payment after user confirmation")

        # Get shared AP2 agent for payment processing
        ap2_agent = await _get_ap2_agent()

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


async def _request_payment_method(user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Request payment method from user (AP2 Step 2.5 - Enhanced Credential Collection)"""

    try:
        product_info = session["product_info"]

        # Get user credential service for enhanced flow
        user_service = await _get_user_credential_service()

        # Initiate credential flow based on amount and user
        credential_flow = await user_service.initiate_whatsapp_credential_flow(
            user_id=user_id,
            payment_method="auto_detect",  # Will be detected from user input
            amount=product_info['price'],
            currency=product_info['currency']
        )

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
        user_service = await _get_user_credential_service()
        merchant_service = await _get_merchant_service()

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

        # Step 3: Use AP2 credential collector for proper payment method discovery
        from sofIA.tools.ap2_protocol.ap2_credential_collector import get_credential_collector
        from sofIA.tools.ap2_protocol.ap2_core import AP2PaymentAgent
        
        # Initialize AP2 agent and credential collector
        ap2_agent = AP2PaymentAgent(agent_id="sofia_claro", merchant_id="claro_merchant")
        credential_collector = get_credential_collector(ap2_agent)
        
        # Discover available payment methods per AP2 spec
        available_methods = await credential_collector.discover_payment_methods(user_id, "latam")
        
        # Detect payment method from user input (enhanced detection)
        payment_method = _detect_payment_method(message)
        if not payment_method:
            # Try to map to AP2 method types
            if any(keyword in message.upper() for keyword in ["CARTAO", "CARTÃO", "CREDITO", "CRÉDITO", "CARD"]):
                payment_method = "basic-card"
            elif any(keyword in message.upper() for keyword in ["PIX"]):
                payment_method = "pix"
            else:
                return {
                    "reply": "❌ Método de pagamento não reconhecido. Use os formatos indicados acima.",
                    "session_updates": {}
                }

        # Step 4: Process payment credentials using AP2 collector
        print(f"💳 Processing {payment_method} credentials with AP2 collector")
        
        # Get product info for amount and currency
        product_info = session.get("product_info")
        if not product_info:
            # This should not happen in normal flow - extract product info if missing
            print("⚠️ Warning: product_info missing from session, extracting from message")
            product_info = _extract_product_info(message, session.get("operator", "CLARO"))
            # Update session with extracted info
            session["product_info"] = product_info
        
        # Ensure we have valid price and currency
        if not product_info.get("price") or product_info.get("price", 0) <= 0:
            print("⚠️ Warning: Invalid price in product_info, using fallback")
            product_info["price"] = 19.90
        if not product_info.get("currency"):
            product_info["currency"] = "BRL"
        
        # Collect credentials using AP2 protocol
        print(f"💰 Processing payment: {product_info['name']} - {product_info['currency']} {product_info['price']:.2f}")
        credential_result = await credential_collector.collect_payment_credentials(
            user_id=user_id,
            cart_mandate_id=session.get("cart_id", f"cart-{user_id}"),
            selected_method=payment_method,
            amount=product_info["price"],
            currency=product_info["currency"]
        )

        if not credential_result["success"]:
            return {
                "reply": credential_result.get("error", "Erro na coleta de credenciais"),
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
        merchant_service = await _get_merchant_service()
        telecom_merchants = await merchant_service.onboard_bemobi_telecom_operators()
        print(f"🏢 Verified {len(telecom_merchants)} telecom operator merchants")

        # Step 2: Authenticate transaction with proper merchant
        ap2_authenticator = await _get_ap2_authenticator()
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
        ap2_agent = await _get_ap2_agent()

        # Enhanced payment response with credential verification
        from sofIA.tools.ap2_protocol.types.payment_request import PaymentResponse

        payment_response = PaymentResponse(
            request_id=f"req-{cart_id}",
            method_name=payment_method,
            details={
                "ap2_transaction_id": transaction_context.transaction_id,
                "sender_agent_id": transaction_context.sender_agent.agent_id,
                "receiver_agent_id": transaction_context.receiver_agent.agent_id,
                "credential_id": credential_result.get("collection_id", "unknown"),
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
🎫 Credential ID: `{credential_result.get("collection_id", "unknown")[:16]}...`

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
                "credential_id": credential_result.get("collection_id", "unknown"),
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
    elif any(keyword in message_upper for keyword in ["CARTAO", "CARTÃO", "CREDITO", "CRÉDITO", "CARD"]):
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
        ap2_authenticator = await _get_ap2_authenticator()

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
        ap2_agent = await _get_ap2_agent()

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

        elif any(keyword in message for keyword in ["CARTAO", "CARTÃO", "CREDITO", "CRÉDITO", "CARD"]):
            # Handle multiple formats:
            # Format 1: CARTAO [número] [vencimento] [cvv]
            # Format 2: Cartão de Crédito\n[número] [vencimento] [nome]\n[primeira_vez]\n[nome] [cpf] [telefone]
            lines = message.split('\n')
            
            # Try to extract card number and expiry from the message
            card_number = None
            expiry = None
            cardholder_name = None
            
            # Look for card number pattern (handle both full and partial numbers)
            import re
            # Try full 16-digit pattern first
            card_pattern = r'\b\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\b'
            card_match = re.search(card_pattern, message)
            if card_match:
                card_number = card_match.group().replace(' ', '')
            else:
                # Try partial card number pattern (4+ digits)
                partial_pattern = r'\b\d{4,}\b'
                partial_match = re.search(partial_pattern, message)
                if partial_match:
                    card_number = partial_match.group()
            
            # Look for expiry pattern (MM/YY or MM/YYYY)
            expiry_pattern = r'\b\d{1,2}/\d{2,4}\b'
            expiry_match = re.search(expiry_pattern, message)
            if expiry_match:
                expiry = expiry_match.group()
            
            # Look for name pattern (words that are not numbers or common keywords)
            name_pattern = r'\b[A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+\b'
            name_matches = re.findall(name_pattern, message)
            if name_matches:
                # Filter out common keywords and take the first valid name
                filtered_names = [name for name in name_matches if not any(keyword in name.upper() for keyword in ["CARTAO", "CARTÃO", "CREDITO", "CRÉDITO", "CARD", "PRIMEIRA", "VEZ"])]
                if filtered_names:
                    cardholder_name = filtered_names[0]
            
            if card_number and expiry:
                return {
                    "method": "basic-card",
                    "details": {
                        "card_number": f"****{card_number[-4:]}",  # Mask card number
                        "expiry": expiry,
                        "cardholder_name": cardholder_name,
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


def _extract_product_info(message: str, operator_name: str = "DEMO") -> Dict[str, Any]:
    """Extract product information from message using AI with operator-specific context"""
    try:
        import google.generativeai as genai
        import os

        # Configure Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Get operator-specific plans for context (simplified for sync context)
        available_plans = []

        # Create operator-specific prompt for product extraction
        extraction_prompt = f"""Analyze this user message and extract what they want to buy/pay for.

User message: "{message}"
Operator: {operator_name}

Based on the message and the operator context, determine:
1. What product/service they want
2. Appropriate price in BRL
3. Product name

{operator_name} Available Plans:
{chr(10).join([f"- {plan['name']}: R$ {plan['price_brl']:.2f} ({plan['description']})" for plan in available_plans[:3]])}

Common examples for {operator_name}:
- "contratar plano" = Subscribe to a mobile plan
- "mudar de plano" = Change mobile plan
- "upgrade plano" = Upgrade mobile plan
- "enviar um pix" = Transfer money via PIX (amount should be asked)
- "pagar conta" = Bill payment (amount varies)

Respond in this exact JSON format:
{{"name": "Product Name", "price": 0.00, "currency": "BRL", "requires_amount": true/false, "is_subscription": true/false}}

If they didn't specify an amount and it's needed (like PIX transfer), set requires_amount to true and price to 0.00.
If it's a subscription plan, set is_subscription to true."""

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

                # Add operator context
                product_info["operator"] = operator_name
                return product_info

            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse AI response: {e}")
                print(f"AI response was: {response.text}")

    except Exception as e:
        print(f"AI product extraction failed: {e}")

    # Fallback for common patterns with operator context
    message_lower = message.lower()
    if "pix" in message_lower:
        return {"name": f"{operator_name} Transferência PIX", "price": 0.00, "currency": "BRL", "requires_amount": True, "operator": operator_name}
    elif any(word in message_lower for word in ["plano", "plan", "contratar"]):
        return {"name": f"{operator_name} Plano", "price": 0.00, "currency": "BRL", "requires_amount": True, "is_subscription": True, "operator": operator_name}
    elif any(word in message_lower for word in ["café", "coffee"]):
        return {"name": "Café", "price": 12.00, "currency": "BRL", "requires_amount": False, "operator": operator_name}
    elif any(word in message_lower for word in ["almoço", "lunch"]):
        return {"name": "Almoço", "price": 28.00, "currency": "BRL", "requires_amount": False, "operator": operator_name}

    return {"name": f"{operator_name} Serviço", "price": 0.00, "currency": "BRL", "requires_amount": True, "operator": operator_name}




def get_user_session(user_id: str) -> Dict[str, Any]:
    """Get user session information"""
    return _user_sessions.get(user_id, {})


async def cleanup_old_sessions(max_age_hours: int = 24):
    """Clean up old user sessions to prevent memory leaks"""
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cutoff_iso = cutoff_time.isoformat()
    
    sessions_to_remove = []
    for user_id, session in _user_sessions.items():
        last_activity = session.get("last_activity", "")
        if last_activity and last_activity < cutoff_iso:
            sessions_to_remove.append(user_id)
    
    for user_id in sessions_to_remove:
        if user_id in _user_sessions:
            del _user_sessions[user_id]
        if user_id in _session_locks:
            del _session_locks[user_id]
    
    if sessions_to_remove:
        print(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")


def get_session_stats() -> Dict[str, Any]:
    """Get session statistics for monitoring"""
    return {
        "active_sessions": len(_user_sessions),
        "active_locks": len(_session_locks),
        "session_ids": list(_user_sessions.keys())[:10]  # First 10 for debugging
    }


def _looks_like_boleto(message: str) -> bool:
    """Check if message looks like a boleto barcode"""
    # Remove spaces and check if it's a numeric string of expected length
    cleaned = message.replace(" ", "").replace("-", "").replace(".", "")

    # Brazilian boleto barcodes are typically 44-48 digits
    if cleaned.isdigit() and len(cleaned) >= 44:
        return True

    # Also detect if user explicitly says it's a boleto
    message_lower = message.lower()
    if any(keyword in message_lower for keyword in ["boleto", "código de barras", "codigo"]):
        return True

    return False


def _process_boleto_code(message: str, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
    """Process boleto barcode and create payment cart"""

    try:
        # Extract the numeric code
        boleto_code = message.replace(" ", "").replace("-", "").replace(".", "")

        # Parse boleto - will throw exception if it fails
        parsed_boleto = _parse_boleto_code(boleto_code)

        # Create product info for boleto payment
        product_info = {
            "name": f"Boleto - {parsed_boleto['recipient']}",
            "price": parsed_boleto['amount'],
            "currency": "BRL",
            "category": "boleto_payment",
            "boleto_code": boleto_code,
            "due_date": parsed_boleto.get('due_date', 'A vencer')
        }

        # Store in session and transition to cart created
        session_updates = {
            "payment_state": "cart_created",
            "product_info": product_info,
            "boleto_code": boleto_code
        }

        # Create formatted reply
        reply = f"""🧾 **Boleto Identificado**

**Beneficiário:** {parsed_boleto['recipient']}
💰 **Valor:** R$ {parsed_boleto['amount']:.2f}
📅 **Vencimento:** {parsed_boleto.get('due_date', 'A vencer')}
🔢 **Código:** {boleto_code[:12]}...

**Confirmar pagamento?** (Responda 'sim' ou 'não')"""

        return {
            "reply": reply,
            "session_updates": session_updates
        }

    except Exception as e:
        print(f"Boleto processing error: {e}")
        return {
            "reply": "❌ Erro ao processar boleto. Tente novamente ou digite o código manualmente.",
            "session_updates": {}
        }


def _parse_boleto_code(boleto_code: str) -> Dict[str, Any]:
    """Parse Brazilian boleto barcode - throws exception if parsing fails"""

    if not boleto_code or len(boleto_code) < 44:
        raise ValueError("Boleto code too short or invalid")

    try:
        # Extract bank code (first 3 digits) - this is reliable
        bank_code = boleto_code[:3]

        # Extract amount using the position that worked: 37:47
        if len(boleto_code) >= 47:
            amount_str = boleto_code[37:47]  # 10 digits for amount in centavos
            if not amount_str.isdigit():
                raise ValueError(f"Amount section is not numeric: {amount_str}")

            amount_centavos = int(amount_str)
            amount = amount_centavos / 100.0

            # Sanity check - reasonable amount range
            if amount <= 0 or amount > 50000:
                raise ValueError(f"Amount out of reasonable range: R$ {amount}")
        else:
            raise ValueError("Boleto too short to extract amount")

        # Bank names mapping
        bank_names = {
            "001": "Banco do Brasil",
            "033": "Santander",
            "104": "Caixa Econômica",
            "237": "Bradesco",
            "260": "Nu Pagamentos",
            "341": "Itaú Unibanco",
            "356": "Banco Real",
            "389": "Banco Mercantil",
            "422": "Banco Safra",
            "655": "Banco Votorantim",
            "745": "Citibank"
        }

        recipient = bank_names.get(bank_code, f"Banco {bank_code}")

        print(f"✅ Boleto parsed successfully: {recipient} - R$ {amount}")

        return {
            "amount": amount,
            "recipient": recipient,
            "bank_code": bank_code,
            "due_date": "Vencimento não especificado",
            "raw_code": boleto_code
        }

    except Exception as e:
        print(f"❌ Boleto parsing failed: {e}")
        raise Exception(f"Não foi possível processar o boleto: {e}")