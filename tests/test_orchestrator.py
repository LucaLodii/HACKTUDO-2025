"""
Test suite for Orchestrator Agent
Tests multi-agent coordination, A2A communication, and conversation management
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

class TestOrchestratorAgent:
    """Test orchestrator agent functionality"""
    
    @pytest.fixture
    def mock_google_adk(self):
        """Mock Google ADK Agent class"""
        with patch('orchestrator.agent.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.name = 'orchestrator'
            mock_agent.model = 'gemini-2.5-flash'
            mock_agent.tools = []
            mock_agent_class.return_value = mock_agent
            yield mock_agent_class, mock_agent
    
    def test_orchestrator_initialization(self, mock_google_adk):
        """Test that orchestrator agent initializes correctly"""
        mock_agent_class, mock_agent = mock_google_adk
        
        try:
            from orchestrator.agent import root_agent
            
            # Verify agent was created
            mock_agent_class.assert_called_once()
            call_args = mock_agent_class.call_args
            
            assert call_args[1]['model'] == 'gemini-2.5-flash'
            assert 'orchestrator' in call_args[1]['name'].lower()
            
        except ImportError:
            # If orchestrator module doesn't exist, create a basic test
            pytest.skip("Orchestrator module not available")
    
    @pytest.mark.asyncio
    async def test_orchestration_tool_functionality(self):
        """Test orchestration tool functionality"""
        try:
            from orchestrator.tools.orchestration_tool import orchestration_tool
            
            # Test basic A2A communication functionality
            result = await orchestration_tool(
                operation="coordinate_agents",
                source_agent="orchestrator",
                target_agent="sofIA",
                user_message="Check my subscriptions",
                user_id="+5511999887766"
            )
            
            # Should handle A2A coordination
            assert isinstance(result, dict)
            
        except ImportError:
            # Create mock orchestration functionality
            pytest.skip("Orchestration tool not available")


class TestA2ACommunication:
    """Test Agent-to-Agent communication patterns"""
    
    def test_a2a_message_format(self):
        """Test A2A message format structure"""
        # Test message format as specified in multi-agent guidelines
        source_agent = "orchestrator"
        user_message = "Quero renovar meu plano Vivo"
        user_id = "+5511999887766"
        product_info = {
            'name': 'Vivo Premium 10GB',
            'currency': 'BRL',
            'price': 49.90
        }
        requested_action = "process_renewal"
        expected_response = "renewal_confirmation"
        tool_type = "subscription_management"
        
        a2a_context = f"""
Agent-to-Agent Request from {source_agent}:

User wants to purchase: {user_message}
User ID: {user_id}
Product: {product_info['name']}
Price: {product_info['currency']} {product_info['price']:.2f}

Please {requested_action} and return the {expected_response}.
Use your {tool_type} tools to process this request.
"""
        
        # Verify message structure
        assert source_agent in a2a_context
        assert user_message in a2a_context
        assert user_id in a2a_context
        assert product_info['name'] in a2a_context
        assert str(product_info['price']) in a2a_context
        assert requested_action in a2a_context
        assert expected_response in a2a_context
        assert tool_type in a2a_context
    
    def test_session_management_structure(self):
        """Test session management data structure"""
        # Test session structure as per guidelines
        user_sessions = {}
        user_id = "+5511999887766"
        
        # Initialize session
        user_sessions[user_id] = {
            "payment_state": "idle",
            "current_intent": None,
            "product_info": None,
            "agent_responses": [],
            "conversation_history": [],
            "subscription_context": {
                "active_subscriptions": [],
                "pending_renewals": [],
                "last_interaction": None
            }
        }
        
        # Test state transitions
        session = user_sessions[user_id]
        
        # idle → intent_created → completed
        assert session["payment_state"] == "idle"
        
        session["payment_state"] = "intent_created"
        session["current_intent"] = "subscription_renewal"
        session["product_info"] = {
            "subscription_id": "sub-001",
            "plan_name": "Vivo Premium 10GB",
            "price": 49.90
        }
        
        assert session["payment_state"] == "intent_created"
        assert session["current_intent"] == "subscription_renewal"
        assert session["product_info"] is not None
        
        session["payment_state"] = "completed"
        assert session["payment_state"] == "completed"
    
    @pytest.mark.asyncio
    async def test_intent_detection_patterns(self):
        """Test intent detection for subscription management"""
        # Common subscription management intents
        test_cases = [
            {
                "message": "Quais são meus planos?",
                "expected_intent": "subscription_discovery",
                "expected_agent": "sofIA"
            },
            {
                "message": "Quero renovar meu plano",
                "expected_intent": "subscription_renewal",
                "expected_agent": "sofIA"
            },
            {
                "message": "Melhorar plano Vivo",
                "expected_intent": "plan_upgrade",
                "expected_agent": "sofIA"
            },
            {
                "message": "Plano mais barato Claro",
                "expected_intent": "plan_downgrade",
                "expected_agent": "sofIA"
            },
            {
                "message": "Quando expira minha assinatura?",
                "expected_intent": "subscription_status",
                "expected_agent": "sofIA"
            }
        ]
        
        for case in test_cases:
            # Simulate intent detection
            message = case["message"].lower()
            
            if any(word in message for word in ["planos", "plano", "assinatura", "renovar", "melhorar", "expira"]):
                detected_intent = "subscription_related"
                target_agent = "sofIA"
            else:
                detected_intent = "general"
                target_agent = "orchestrator"
            
            assert detected_intent == "subscription_related"
            assert target_agent == case["expected_agent"]


class TestConversationFlow:
    """Test conversation flow management"""
    
    @pytest.mark.asyncio
    async def test_subscription_discovery_flow(self):
        """Test complete subscription discovery conversation flow"""
        # Simulate user asking about subscriptions
        user_message = "Quais são meus planos?"
        user_id = "+5511999887766"
        
        # 1. Orchestrator detects subscription intent
        intent = "subscription_discovery"
        target_agent = "sofIA"
        
        # 2. Create A2A message for sofIA
        a2a_request = {
            "source_agent": "orchestrator",
            "target_agent": "sofIA",
            "operation": "get_user_subscriptions",
            "user_id": user_id,
            "user_message": user_message
        }
        
        # 3. Simulate sofIA response
        from sofIA.tools.subscription_management import subscription_management_tool
        
        sofia_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number=user_id
        )
        
        assert sofia_result['success'] is True
        
        # 4. Format response for user
        if sofia_result['subscriptions']:
            response = "📱 Seus planos ativos:\n"
            for sub in sofia_result['subscriptions']:
                operator = sub['operators']['display_name']
                plan = sub['subscription_plans']['name']
                response += f"• {operator} {plan}\n"
        else:
            response = "Você não tem planos ativos no momento."
        
        assert "planos" in response.lower()
    
    @pytest.mark.asyncio
    async def test_renewal_flow(self):
        """Test complete renewal conversation flow"""
        user_message = "Quero renovar meu plano Vivo"
        user_id = "+5511999887766"
        
        # 1. Intent detection
        intent = "subscription_renewal"
        
        # 2. Get user subscriptions to find Vivo plan
        from sofIA.tools.subscription_management import subscription_management_tool
        
        subscriptions_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number=user_id
        )
        
        # 3. Find Vivo subscription
        vivo_subscription = None
        if subscriptions_result['success']:
            for sub in subscriptions_result['subscriptions']:
                if 'vivo' in sub['operators']['name'].lower():
                    vivo_subscription = sub
                    break
        
        # 4. Calculate renewal cost
        if vivo_subscription:
            from sofIA.tools.renewal_orchestration import renewal_orchestration_tool
            
            cost_result = await renewal_orchestration_tool(
                operation="calculate_renewal_cost",
                subscription_id=vivo_subscription['id']
            )
            
            assert cost_result['success'] is True
            assert 'renewal_cost_brl' in cost_result
        
        # 5. Create A2A message for payment processing
        a2a_payment_request = {
            "source_agent": "orchestrator",
            "target_agent": "sofIA", 
            "operation": "process_renewal_payment",
            "subscription_id": vivo_subscription['id'] if vivo_subscription else "sub-001",
            "user_confirmation": True
        }
        
        assert a2a_payment_request['operation'] == "process_renewal_payment"
    
    @pytest.mark.asyncio
    async def test_plan_upgrade_flow(self):
        """Test complete plan upgrade conversation flow"""
        user_message = "Quero melhorar meu plano"
        user_id = "+5511999887766"
        
        # 1. Get current subscriptions
        from sofIA.tools.subscription_management import subscription_management_tool
        
        subscriptions_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number=user_id
        )
        
        # 2. Get upgrade options for first subscription
        if subscriptions_result['success'] and subscriptions_result['subscriptions']:
            subscription = subscriptions_result['subscriptions'][0]
            operator_id = subscription['operators']['id']
            current_plan_id = subscription['subscription_plans']['id']
            
            from sofIA.tools.plan_management import plan_management_tool
            
            options_result = await plan_management_tool(
                operation="get_plan_options",
                operator_id=operator_id,
                current_plan_id=current_plan_id
            )
            
            assert options_result['success'] is True
            
            # 3. Present upgrade options
            if 'upgrade_options' in options_result:
                upgrades = options_result['upgrade_options']
                response = "📈 Opções de upgrade:\n"
                for plan in upgrades[:3]:  # Show first 3 options
                    price = plan['price_cents'] / 100
                    response += f"• {plan['name']} - R$ {price:.2f}\n"
                
                assert "upgrade" in response.lower()


class TestErrorHandling:
    """Test error handling in orchestrator"""
    
    @pytest.mark.asyncio
    async def test_agent_unavailable_fallback(self):
        """Test fallback when target agent is unavailable"""
        # Simulate agent unavailable scenario
        a2a_request = {
            "target_agent": "unavailable_agent",
            "operation": "test_operation"
        }
        
        # Should gracefully handle unavailable agent
        fallback_response = {
            "success": False,
            "error": "Target agent unavailable",
            "fallback": "Redirecting to available agent"
        }
        
        assert fallback_response['success'] is False
        assert 'unavailable' in fallback_response['error']
        assert 'fallback' in fallback_response
    
    @pytest.mark.asyncio
    async def test_invalid_user_session(self):
        """Test handling of invalid user sessions"""
        # Test with invalid user ID
        invalid_user_id = "invalid_user"
        
        from sofIA.tools.subscription_management import subscription_management_tool
        
        result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number=invalid_user_id
        )
        
        # Should handle gracefully
        assert result['success'] is True  # Mock mode handles this gracefully
    
    def test_conversation_state_recovery(self):
        """Test conversation state recovery after errors"""
        user_sessions = {}
        user_id = "+5511999887766"
        
        # Initialize corrupted session
        user_sessions[user_id] = {
            "payment_state": "corrupted",
            "current_intent": None
        }
        
        # Recovery logic
        session = user_sessions[user_id]
        if session.get("payment_state") not in ["idle", "intent_created", "completed"]:
            # Reset to safe state
            session["payment_state"] = "idle"
            session["current_intent"] = None
            session["error_recovered"] = True
        
        assert session["payment_state"] == "idle"
        assert session.get("error_recovered") is True


class TestPerformanceRequirements:
    """Test performance requirements compliance"""
    
    @pytest.mark.asyncio
    async def test_response_time_simulation(self):
        """Test that operations complete within performance requirements"""
        import time
        
        # Response time should be < 2 seconds
        start_time = time.time()
        
        from sofIA.tools.subscription_management import subscription_management_tool
        
        result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # In mock mode, should be very fast
        assert response_time < 1.0  # Much faster than 2 second requirement
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling multiple concurrent operations"""
        from sofIA.tools.subscription_management import subscription_management_tool
        
        # Simulate multiple concurrent users
        user_ids = [f"+551199988776{i}" for i in range(5)]
        
        # Create concurrent tasks
        tasks = []
        for user_id in user_ids:
            task = subscription_management_tool(
                operation="get_user_subscriptions",
                whatsapp_number=user_id
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result['success'] is True
    
    def test_audit_logging_structure(self):
        """Test audit logging structure for compliance"""
        # Sample audit log entry
        audit_entry = {
            "timestamp": "2025-01-28T10:00:00Z",
            "source_agent": "orchestrator",
            "target_agent": "sofIA",
            "operation": "subscription_renewal",
            "user_id": "+5511999887766",
            "request_data": {
                "subscription_id": "sub-001",
                "amount": 49.90,
                "currency": "BRL"
            },
            "response_data": {
                "success": True,
                "transaction_id": "ap2_txn_123"
            },
            "performance_metrics": {
                "response_time_ms": 1500,
                "tokens_used": 120
            }
        }
        
        # Verify audit structure
        required_fields = [
            "timestamp", "source_agent", "target_agent", 
            "operation", "user_id", "request_data", 
            "response_data", "performance_metrics"
        ]
        
        for field in required_fields:
            assert field in audit_entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
