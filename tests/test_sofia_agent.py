"""
Test suite for sofIA Agent
Tests agent initialization, tool integration, and response generation
"""

import pytest
import asyncio
import importlib
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Test the sofIA agent configuration and tool integration
class TestSofIAAgent:
    """Test sofIA agent functionality"""
    
    @pytest.fixture
    def mock_google_adk(self):
        """Mock Google ADK Agent class"""
        with patch('google.adk.agents.Agent') as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent.name = 'sofIA'
            mock_agent.model = 'gemini-2.5-flash'
            mock_agent.tools = []
            mock_agent_class.return_value = mock_agent
            yield mock_agent_class, mock_agent
    
    def test_agent_initialization(self, mock_google_adk):
        """Test that sofIA agent initializes with correct configuration"""
        mock_agent_class, mock_agent = mock_google_adk
        
        # Remove the module if it was already imported
        if 'sofIA.agent' in sys.modules:
            del sys.modules['sofIA.agent']
        
        # Import after mocking to ensure the mock is used
        import sofIA.agent
        importlib.reload(sofIA.agent)
        
        # Verify agent was created with correct parameters (may be called multiple times due to imports)
        assert mock_agent_class.called
        call_args = mock_agent_class.call_args  # Gets the last call
        
        assert call_args[1]['model'] == 'gemini-2.5-flash'
        assert call_args[1]['name'] == 'sofIA'
        assert 'subscription management' in call_args[1]['description'].lower()
        assert 'tools' in call_args[1]
        
        # Verify all calls have the same parameters (consistency check)
        for call in mock_agent_class.call_args_list:
            assert call[1]['model'] == 'gemini-2.5-flash'
            assert call[1]['name'] == 'sofIA'
    
    def test_agent_tools_integration(self, mock_google_adk):
        """Test that all required tools are integrated"""
        mock_agent_class, mock_agent = mock_google_adk
        
        # Remove the module if it was already imported
        if 'sofIA.agent' in sys.modules:
            del sys.modules['sofIA.agent']
        
        import sofIA.agent
        importlib.reload(sofIA.agent)
        
        # Get the tools passed to the agent
        call_args = mock_agent_class.call_args
        tools = call_args[1]['tools']
        
        # Expected tool types
        expected_tool_names = [
            'subscription_management',
            'renewal_orchestration', 
            'plan_management'
        ]
        
        tool_names = [getattr(tool, 'name', str(tool)) for tool in tools]
        
        for expected_name in expected_tool_names:
            assert any(expected_name in tool_name for tool_name in tool_names), f"Tool {expected_name} not found"
    
    def test_agent_prompt_content(self, mock_google_adk):
        """Test that agent prompt includes subscription management instructions"""
        mock_agent_class, mock_agent = mock_google_adk
        
        from sofIA.agent import root_agent
        from sofIA.prompt import SOFIA_AGENT_PROMPT
        
        # Check prompt content
        assert 'subscription management' in SOFIA_AGENT_PROMPT.lower()
        assert 'renewal' in SOFIA_AGENT_PROMPT.lower()
        assert 'vivo' in SOFIA_AGENT_PROMPT.lower()
        assert 'claro' in SOFIA_AGENT_PROMPT.lower()
        assert 'ap2' in SOFIA_AGENT_PROMPT.lower()
        assert 'whatsapp' in SOFIA_AGENT_PROMPT.lower()
    
    @pytest.mark.asyncio
    async def test_agent_tool_execution(self):
        """Test that agent tools can execute properly"""
        # Test subscription management tool
        from sofIA.tools.subscription_management import subscription_management_tool
        
        result = await subscription_management_tool(
            operation="get_operators"
        )
        
        assert result['success'] is True
        assert 'operators' in result
        
        # Test renewal orchestration tool
        from sofIA.tools.renewal_orchestration import renewal_orchestration_tool
        
        result = await renewal_orchestration_tool(
            operation="check_renewal_queue",
            days_ahead=7
        )
        
        assert result['success'] is True
        assert 'renewal_queue' in result
        
        # Test plan management tool
        from sofIA.tools.plan_management import plan_management_tool
        
        result = await plan_management_tool(
            operation="get_plan_options",
            operator_id="vivo-op"
        )
        
        assert result['success'] is True
        assert 'plans' in result or 'current_plan' in result


class TestSofIAAgentPrompt:
    """Test agent prompt and conversation patterns"""
    
    def test_prompt_structure(self):
        """Test that prompt has proper structure and content"""
        from sofIA.prompt import SOFIA_AGENT_PROMPT
        
        # Check for key sections
        assert '## Subscription Management' in SOFIA_AGENT_PROMPT
        assert '## Proactive Renewal System' in SOFIA_AGENT_PROMPT
        assert '## Plan Management & Migration' in SOFIA_AGENT_PROMPT
        assert '## AP2 Payment Processing' in SOFIA_AGENT_PROMPT
        
        # Check for conversation patterns
        assert 'Renewal Reminders' in SOFIA_AGENT_PROMPT
        assert 'Plan Upgrades' in SOFIA_AGENT_PROMPT
        assert 'Multi-Subscription Management' in SOFIA_AGENT_PROMPT
    
    def test_prompt_conversation_examples(self):
        """Test that prompt includes proper Portuguese conversation examples"""
        from sofIA.prompt import SOFIA_AGENT_PROMPT
        
        # Check for Portuguese examples
        portuguese_phrases = [
            'Quais são meus planos?',
            'Quero renovar',
            'Melhorar plano',
            'Plano mais barato',
            'Quando expira?'
        ]
        
        for phrase in portuguese_phrases:
            assert phrase in SOFIA_AGENT_PROMPT
    
    def test_prompt_business_context(self):
        """Test that prompt includes proper business context"""
        from sofIA.prompt import SOFIA_AGENT_PROMPT
        
        # Check for BEMOBI context
        assert 'BEMOBI' in SOFIA_AGENT_PROMPT
        assert 'VIVO' in SOFIA_AGENT_PROMPT
        assert 'CLARO' in SOFIA_AGENT_PROMPT
        assert 'OI' in SOFIA_AGENT_PROMPT
        assert 'TIM' in SOFIA_AGENT_PROMPT
        
        # Check for business goals
        assert 'churn' in SOFIA_AGENT_PROMPT.lower()
        assert 'retention' in SOFIA_AGENT_PROMPT.lower()
        assert 'proactive' in SOFIA_AGENT_PROMPT.lower()


class TestToolIntegration:
    """Test integration between different tools"""
    
    @pytest.mark.asyncio
    async def test_subscription_to_renewal_flow(self):
        """Test flow from subscription discovery to renewal processing"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.renewal_orchestration import renewal_orchestration_tool
        
        # 1. Get user subscriptions
        subscriptions_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        
        assert subscriptions_result['success'] is True
        
        # 2. Check renewal queue
        renewal_result = await renewal_orchestration_tool(
            operation="check_renewal_queue",
            days_ahead=7
        )
        
        assert renewal_result['success'] is True
        
        # 3. Calculate renewal cost
        cost_result = await renewal_orchestration_tool(
            operation="calculate_renewal_cost",
            subscription_id="sub-001"
        )
        
        assert cost_result['success'] is True
        assert 'renewal_cost_brl' in cost_result
    
    @pytest.mark.asyncio
    async def test_subscription_to_plan_change_flow(self):
        """Test flow from subscription discovery to plan change"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.plan_management import plan_management_tool
        
        # 1. Get user subscriptions
        subscriptions_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        
        assert subscriptions_result['success'] is True
        
        # 2. Get plan options
        plans_result = await plan_management_tool(
            operation="get_plan_options",
            operator_id="vivo-op",
            current_plan_id="vivo-001"
        )
        
        assert plans_result['success'] is True
        
        # 3. Compare plans
        comparison_result = await plan_management_tool(
            operation="compare_plans",
            current_plan_id="vivo-001",
            new_plan_id="vivo-002"
        )
        
        assert comparison_result['success'] is True
        assert 'comparison' in comparison_result
    
    @pytest.mark.asyncio
    async def test_tool_error_handling_consistency(self):
        """Test that all tools handle errors consistently"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.renewal_orchestration import renewal_orchestration_tool
        from sofIA.tools.plan_management import plan_management_tool
        
        tools = [
            (subscription_management_tool, "invalid_operation"),
            (renewal_orchestration_tool, "invalid_operation"),
            (plan_management_tool, "invalid_operation")
        ]
        
        for tool, operation in tools:
            result = await tool(operation=operation)
            assert result['success'] is False
            assert 'error' in result
            assert 'Unknown operation' in result['error']


class TestMockDataConsistency:
    """Test that mock data is consistent across tools"""
    
    @pytest.mark.asyncio
    async def test_operator_data_consistency(self):
        """Test that operator data is consistent across tools"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.plan_management import plan_management_tool
        
        # Get operators from subscription tool
        operators_result = await subscription_management_tool(
            operation="get_operators"
        )
        
        assert operators_result['success'] is True
        operators = operators_result['operators']
        
        # Test that plan tool recognizes the same operators
        for operator in operators:
            operator_id = operator['id']
            plans_result = await plan_management_tool(
                operation="get_plan_options",
                operator_id=operator_id
            )
            
            # Should succeed or return empty plans, not error
            assert plans_result['success'] is True
    
    @pytest.mark.asyncio
    async def test_subscription_data_consistency(self):
        """Test that subscription data is consistent across tools"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.renewal_orchestration import renewal_orchestration_tool
        
        # Get subscriptions
        subscriptions_result = await subscription_management_tool(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        
        if subscriptions_result['success'] and subscriptions_result['subscriptions']:
            subscription_id = subscriptions_result['subscriptions'][0]['id']
            
            # Test renewal tool recognizes the same subscription
            renewal_cost_result = await renewal_orchestration_tool(
                operation="calculate_renewal_cost",
                subscription_id=subscription_id
            )
            
            assert renewal_cost_result['success'] is True
    
    @pytest.mark.asyncio
    async def test_plan_data_consistency(self):
        """Test that plan data is consistent across tools"""
        from sofIA.tools.subscription_management import subscription_management_tool
        from sofIA.tools.plan_management import plan_management_tool
        
        # Get available plans
        plans_result = await subscription_management_tool(
            operation="get_available_plans",
            operator_id="vivo-op"
        )
        
        if plans_result['success'] and plans_result.get('plans'):
            plan_ids = [plan['id'] for plan in plans_result['plans'][:2]]
            
            if len(plan_ids) >= 2:
                # Test plan management tool can compare these plans
                comparison_result = await plan_management_tool(
                    operation="compare_plans",
                    current_plan_id=plan_ids[0],
                    new_plan_id=plan_ids[1]
                )
                
                assert comparison_result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
