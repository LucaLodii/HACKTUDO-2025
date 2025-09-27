"""
Test suite for subscription management features
Tests subscription discovery, renewal orchestration, and plan management
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

# Import the tools we want to test
from sofIA.tools.subscription_management import SubscriptionManagementTool
from sofIA.tools.renewal_orchestration import RenewalOrchestrationTool  
from sofIA.tools.plan_management import PlanManagementTool


class TestSubscriptionManagementTool:
    """Test subscription discovery and management"""
    
    @pytest.fixture
    def subscription_tool(self):
        """Create a subscription management tool instance"""
        tool = SubscriptionManagementTool()
        tool.mock_mode = True  # Force mock mode for testing
        return tool
    
    @pytest.mark.asyncio
    async def test_get_user_subscriptions_success(self, subscription_tool):
        """Test successful retrieval of user subscriptions"""
        result = await subscription_tool.execute(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        
        assert result["success"] is True
        assert "subscriptions" in result
        assert result["count"] >= 0
        
        if result["subscriptions"]:
            subscription = result["subscriptions"][0]
            assert "id" in subscription
            assert "operators" in subscription
            assert "subscription_plans" in subscription
    
    @pytest.mark.asyncio
    async def test_get_user_subscriptions_no_number(self, subscription_tool):
        """Test error when WhatsApp number is not provided"""
        result = await subscription_tool.execute(
            operation="get_user_subscriptions"
        )
        
        assert result["success"] is False
        assert "WhatsApp number is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_subscription_details(self, subscription_tool):
        """Test getting detailed subscription information"""
        result = await subscription_tool.execute(
            operation="get_subscription_details",
            subscription_id="sub-001"
        )
        
        assert result["success"] is True
        assert "subscription" in result
        
        subscription = result["subscription"]
        assert "id" in subscription
        assert "time_until_expiry_days" in subscription
        assert "is_expiring_soon" in subscription
    
    @pytest.mark.asyncio
    async def test_check_expiring_subscriptions(self, subscription_tool):
        """Test monitoring expiring subscriptions"""
        result = await subscription_tool.execute(
            operation="check_expiring_subscriptions",
            days_ahead=7
        )
        
        assert result["success"] is True
        assert "expiring_subscriptions" in result
        assert "days_ahead" in result
        assert result["days_ahead"] == 7
    
    @pytest.mark.asyncio
    async def test_get_available_plans(self, subscription_tool):
        """Test getting available plans for an operator"""
        result = await subscription_tool.execute(
            operation="get_available_plans",
            operator_id="vivo-op"
        )
        
        assert result["success"] is True
        assert "plans" in result
        assert result["count"] >= 0
    
    @pytest.mark.asyncio
    async def test_calculate_plan_change_cost(self, subscription_tool):
        """Test calculating cost difference between plans"""
        result = await subscription_tool.execute(
            operation="calculate_plan_change_cost",
            current_plan_id="vivo-001",
            new_plan_id="vivo-002"
        )
        
        assert result["success"] is True
        assert "current_plan" in result
        assert "new_plan" in result
        assert "price_difference_cents" in result
        assert "is_upgrade" in result or "is_downgrade" in result


class TestRenewalOrchestrationTool:
    """Test renewal monitoring and reminder system"""
    
    @pytest.fixture
    def renewal_tool(self):
        """Create a renewal orchestration tool instance"""
        tool = RenewalOrchestrationTool()
        tool.mock_mode = True  # Force mock mode for testing
        return tool
    
    @pytest.mark.asyncio
    async def test_check_renewal_queue(self, renewal_tool):
        """Test checking the renewal queue for upcoming expirations"""
        result = await renewal_tool.execute(
            operation="check_renewal_queue",
            days_ahead=7
        )
        
        assert result["success"] is True
        assert "renewal_queue" in result
        
        queue = result["renewal_queue"]
        assert "seven_day_reminders" in queue
        assert "three_day_reminders" in queue
        assert "one_day_reminders" in queue
        assert "total_pending" in queue
    
    @pytest.mark.asyncio
    async def test_schedule_reminder(self, renewal_tool):
        """Test scheduling a renewal reminder"""
        result = await renewal_tool.execute(
            operation="schedule_reminder",
            subscription_id="sub-001",
            reminder_type="3_day"
        )
        
        assert result["success"] is True
        assert "reminder" in result
        assert "scheduled_for" in result
        
        reminder = result["reminder"]
        assert reminder["subscription_id"] == "sub-001"
        assert reminder["reminder_type"] == "3_day"
    
    @pytest.mark.asyncio
    async def test_send_renewal_reminder(self, renewal_tool):
        """Test generating a renewal reminder message"""
        result = await renewal_tool.execute(
            operation="send_renewal_reminder",
            subscription_id="sub-001"
        )
        
        assert result["success"] is True
        assert "subscription" in result
        assert "reminder_message" in result
        assert "urgency" in result
        assert "whatsapp_number" in result
        
        # Check message content
        message = result["reminder_message"]
        assert "João Silva" in message or "plano" in message
        assert "R$" in message  # Should contain price information
    
    @pytest.mark.asyncio
    async def test_process_renewal_response(self, renewal_tool):
        """Test processing user response to renewal reminder"""
        result = await renewal_tool.execute(
            operation="process_renewal_response",
            reminder_id="reminder-001",
            user_response="renewed"
        )
        
        assert result["success"] is True
        assert "user_response" in result
        assert "next_action" in result
        assert result["user_response"] == "renewed"
        assert result["next_action"] == "payment_processing"
    
    @pytest.mark.asyncio
    async def test_calculate_renewal_cost(self, renewal_tool):
        """Test calculating renewal cost for a subscription"""
        result = await renewal_tool.execute(
            operation="calculate_renewal_cost",
            subscription_id="sub-001"
        )
        
        assert result["success"] is True
        assert "renewal_cost_cents" in result
        assert "renewal_cost_brl" in result
        assert "billing_cycle" in result
        assert result["currency"] == "BRL"
    
    @pytest.mark.asyncio
    async def test_get_pending_reminders(self, renewal_tool):
        """Test getting pending reminders that need to be sent"""
        result = await renewal_tool.execute(
            operation="get_pending_reminders"
        )
        
        assert result["success"] is True
        assert "pending_reminders" in result
        assert "count" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_mark_reminder_sent(self, renewal_tool):
        """Test marking a reminder as sent"""
        result = await renewal_tool.execute(
            operation="mark_reminder_sent",
            reminder_id="reminder-001",
            message_id="wa_msg_123"
        )
        
        assert result["success"] is True
        assert "reminder_id" in result
        assert "message_id" in result
        assert "sent_at" in result


class TestPlanManagementTool:
    """Test plan upgrade/downgrade functionality"""
    
    @pytest.fixture
    def plan_tool(self):
        """Create a plan management tool instance"""
        tool = PlanManagementTool()
        tool.mock_mode = True  # Force mock mode for testing
        return tool
    
    @pytest.mark.asyncio
    async def test_get_plan_options(self, plan_tool):
        """Test getting plan options for an operator"""
        result = await plan_tool.execute(
            operation="get_plan_options",
            operator_id="vivo-op",
            current_plan_id="plan-basic"
        )
        
        assert result["success"] is True
        assert "current_plan" in result
        assert "upgrade_options" in result
        assert "downgrade_options" in result
        assert "all_plans" in result
    
    @pytest.mark.asyncio
    async def test_compare_plans(self, plan_tool):
        """Test detailed plan comparison"""
        result = await plan_tool.execute(
            operation="compare_plans",
            current_plan_id="plan-basic",
            new_plan_id="plan-premium"
        )
        
        assert result["success"] is True
        assert "comparison" in result
        
        comparison = result["comparison"]
        assert "current_plan" in comparison
        assert "new_plan" in comparison
        assert "price_difference" in comparison
        assert "migration_type" in comparison
        assert "features_gained" in comparison
    
    @pytest.mark.asyncio
    async def test_calculate_migration_cost(self, plan_tool):
        """Test calculating cost for plan migration"""
        result = await plan_tool.execute(
            operation="calculate_migration_cost",
            subscription_id="sub-001",
            new_plan_id="plan-premium"
        )
        
        assert result["success"] is True
        assert "cost_breakdown" in result
        
        breakdown = result["cost_breakdown"]
        assert "price_difference_brl" in breakdown
        assert "immediate_cost_brl" in breakdown
        assert "migration_type" in breakdown
    
    @pytest.mark.asyncio
    async def test_validate_plan_change(self, plan_tool):
        """Test validating a plan change"""
        result = await plan_tool.execute(
            operation="validate_plan_change",
            subscription_id="sub-001",
            new_plan_id="plan-premium"
        )
        
        assert result["success"] is True
        assert "valid" in result
        assert "reason" in result
    
    @pytest.mark.asyncio
    async def test_prepare_plan_migration(self, plan_tool):
        """Test preparing plan migration data"""
        result = await plan_tool.execute(
            operation="prepare_plan_migration",
            subscription_id="sub-001",
            new_plan_id="plan-premium",
            migration_type="upgrade"
        )
        
        assert result["success"] is True
        assert "migration_data" in result
        
        migration_data = result["migration_data"]
        assert "subscription_id" in migration_data
        assert "new_plan_id" in migration_data
        assert "migration_type" in migration_data
        assert "requires_payment" in migration_data
        assert "ap2_ready" in migration_data
    
    @pytest.mark.asyncio
    async def test_execute_plan_change(self, plan_tool):
        """Test executing a plan change"""
        # Test without payment (downgrade scenario)
        result = await plan_tool.execute(
            operation="execute_plan_change",
            subscription_id="sub-001",
            new_plan_id="plan-basic"
        )
        
        assert result["success"] is True
        assert "subscription_updated" in result
        assert "migration_completed" in result
        assert "executed_at" in result
    
    @pytest.mark.asyncio
    async def test_get_migration_history(self, plan_tool):
        """Test getting plan migration history"""
        result = await plan_tool.execute(
            operation="get_migration_history",
            whatsapp_number="+5511999887766"
        )
        
        assert result["success"] is True
        assert "migration_history" in result
        assert "count" in result


class TestSubscriptionIntegration:
    """Integration tests across all subscription management tools"""
    
    @pytest.fixture
    def all_tools(self):
        """Create instances of all subscription tools"""
        subscription_tool = SubscriptionManagementTool()
        renewal_tool = RenewalOrchestrationTool()
        plan_tool = PlanManagementTool()
        
        # Force mock mode for all tools
        subscription_tool.mock_mode = True
        renewal_tool.mock_mode = True
        plan_tool.mock_mode = True
        
        return {
            "subscription": subscription_tool,
            "renewal": renewal_tool,
            "plan": plan_tool
        }
    
    @pytest.mark.asyncio
    async def test_complete_renewal_flow(self, all_tools):
        """Test complete renewal flow from detection to payment"""
        subscription_tool = all_tools["subscription"]
        renewal_tool = all_tools["renewal"]
        
        # 1. Check for expiring subscriptions
        expiring_result = await subscription_tool.execute(
            operation="check_expiring_subscriptions",
            days_ahead=3
        )
        assert expiring_result["success"] is True
        
        # 2. Schedule a reminder
        reminder_result = await renewal_tool.execute(
            operation="schedule_reminder",
            subscription_id="sub-001",
            reminder_type="3_day"
        )
        assert reminder_result["success"] is True
        
        # 3. Generate renewal message
        message_result = await renewal_tool.execute(
            operation="send_renewal_reminder",
            subscription_id="sub-001"
        )
        assert message_result["success"] is True
        assert "reminder_message" in message_result
        
        # 4. Process user response
        response_result = await renewal_tool.execute(
            operation="process_renewal_response",
            reminder_id="reminder-001",
            user_response="renewed"
        )
        assert response_result["success"] is True
        assert response_result["next_action"] == "payment_processing"
    
    @pytest.mark.asyncio
    async def test_complete_upgrade_flow(self, all_tools):
        """Test complete plan upgrade flow"""
        subscription_tool = all_tools["subscription"]
        plan_tool = all_tools["plan"]
        
        # 1. Get user's current subscriptions
        subscriptions_result = await subscription_tool.execute(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        assert subscriptions_result["success"] is True
        
        # 2. Get plan options
        plan_options_result = await plan_tool.execute(
            operation="get_plan_options",
            operator_id="vivo-op",
            current_plan_id="plan-basic"
        )
        assert plan_options_result["success"] is True
        
        # 3. Compare plans
        comparison_result = await plan_tool.execute(
            operation="compare_plans",
            current_plan_id="plan-basic",
            new_plan_id="plan-premium"
        )
        assert comparison_result["success"] is True
        
        # 4. Calculate costs
        cost_result = await plan_tool.execute(
            operation="calculate_migration_cost",
            subscription_id="sub-001",
            new_plan_id="plan-premium"
        )
        assert cost_result["success"] is True
        
        # 5. Execute plan change
        execution_result = await plan_tool.execute(
            operation="execute_plan_change",
            subscription_id="sub-001",
            new_plan_id="plan-premium"
        )
        assert execution_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_multi_subscription_management(self, all_tools):
        """Test managing multiple subscriptions for one user"""
        subscription_tool = all_tools["subscription"]
        renewal_tool = all_tools["renewal"]
        
        # Get all user subscriptions
        result = await subscription_tool.execute(
            operation="get_user_subscriptions",
            whatsapp_number="+5511999887766"
        )
        assert result["success"] is True
        
        # Check renewal queue for multiple subscriptions
        queue_result = await renewal_tool.execute(
            operation="check_renewal_queue",
            days_ahead=30  # Look further ahead for multiple subscriptions
        )
        assert queue_result["success"] is True
        
        # Get renewal history
        history_result = await renewal_tool.execute(
            operation="get_renewal_history",
            whatsapp_number="+5511999887766"
        )
        assert history_result["success"] is True


class TestErrorHandling:
    """Test error handling across subscription tools"""
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test handling of invalid operations"""
        tool = SubscriptionManagementTool()
        tool.mock_mode = True
        
        result = await tool.execute(operation="invalid_operation")
        assert result["success"] is False
        assert "Unknown operation" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_required_parameters(self):
        """Test handling of missing required parameters"""
        tool = SubscriptionManagementTool()
        tool.mock_mode = True
        
        # Test missing WhatsApp number
        result = await tool.execute(operation="get_user_subscriptions")
        assert result["success"] is False
        assert "required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_renewal_tool_error_handling(self):
        """Test renewal tool error handling"""
        tool = RenewalOrchestrationTool()
        tool.mock_mode = True
        
        # Test missing subscription ID
        result = await tool.execute(operation="send_renewal_reminder")
        assert result["success"] is False
        assert "required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_plan_tool_error_handling(self):
        """Test plan management tool error handling"""
        tool = PlanManagementTool()
        tool.mock_mode = True
        
        # Test missing plan IDs
        result = await tool.execute(operation="compare_plans")
        assert result["success"] is False
        assert "required" in result["error"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
