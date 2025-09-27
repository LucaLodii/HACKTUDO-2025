"""
Plan Management Tool for sofIA Agent
Handles plan upgrades, downgrades, and migrations with AP2 payment integration
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from supabase import create_client, Client
from postgrest import APIError

logger = logging.getLogger(__name__)


class PlanManagementTool:
    """Tool for subscription plan management and migration with AP2 payment processing"""
    
    def __init__(self):
        self.name = "plan_management"
        self.description = "Subscription plan management including upgrades, downgrades, and migrations with AP2 payment processing"
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found. Using mock data mode.")
            self.supabase = None
            self.mock_mode = True
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.mock_mode = False
        
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "get_plan_options",
                        "compare_plans",
                        "calculate_migration_cost",
                        "validate_plan_change",
                        "prepare_plan_migration",
                        "execute_plan_change",
                        "get_migration_history",
                        "rollback_plan_change",
                        "get_plan_recommendations"
                    ],
                    "description": "Plan management operation to perform"
                },
                "subscription_id": {
                    "type": "string",
                    "description": "Subscription ID for plan changes"
                },
                "current_plan_id": {
                    "type": "string",
                    "description": "Current plan ID for comparisons"
                },
                "new_plan_id": {
                    "type": "string",
                    "description": "New plan ID for migration"
                },
                "operator_id": {
                    "type": "string",
                    "description": "Operator ID for plan options"
                },
                "whatsapp_number": {
                    "type": "string",
                    "description": "WhatsApp number for user-specific operations"
                },
                "migration_type": {
                    "type": "string",
                    "enum": ["upgrade", "downgrade", "lateral"],
                    "description": "Type of plan migration"
                },
                "effective_date": {
                    "type": "string",
                    "description": "When the plan change should take effect (ISO date)"
                },
                "ap2_payment_data": {
                    "type": "object",
                    "description": "AP2 payment data for plan change processing"
                }
            },
            "required": ["operation"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute plan management operations"""
        operation = kwargs.get("operation")
        
        try:
            if operation == "get_plan_options":
                return await self._get_plan_options(
                    kwargs.get("operator_id"),
                    kwargs.get("current_plan_id")
                )
            elif operation == "compare_plans":
                return await self._compare_plans(
                    kwargs.get("current_plan_id"),
                    kwargs.get("new_plan_id")
                )
            elif operation == "calculate_migration_cost":
                return await self._calculate_migration_cost(
                    kwargs.get("subscription_id"),
                    kwargs.get("new_plan_id"),
                    kwargs.get("effective_date")
                )
            elif operation == "validate_plan_change":
                return await self._validate_plan_change(
                    kwargs.get("subscription_id"),
                    kwargs.get("new_plan_id")
                )
            elif operation == "prepare_plan_migration":
                return await self._prepare_plan_migration(
                    kwargs.get("subscription_id"),
                    kwargs.get("new_plan_id"),
                    kwargs.get("migration_type")
                )
            elif operation == "execute_plan_change":
                return await self._execute_plan_change(
                    kwargs.get("subscription_id"),
                    kwargs.get("new_plan_id"),
                    kwargs.get("ap2_payment_data")
                )
            elif operation == "get_migration_history":
                return await self._get_migration_history(kwargs.get("whatsapp_number"))
            elif operation == "rollback_plan_change":
                return await self._rollback_plan_change(kwargs.get("subscription_id"))
            elif operation == "get_plan_recommendations":
                return await self._get_plan_recommendations(kwargs.get("subscription_id"))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Plan management operation failed: {e}")
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    async def _get_plan_options(self, operator_id: str, current_plan_id: str = None) -> Dict[str, Any]:
        """Get available plan options for an operator"""
        if not operator_id:
            return {"success": False, "error": "Operator ID is required"}
        
        if self.mock_mode:
            return self._get_mock_plan_options(operator_id, current_plan_id)
        
        try:
            # Get all active plans for the operator
            plans_response = self.supabase.table("subscription_plans").select("""
                id,
                plan_code,
                name,
                description,
                price_cents,
                billing_cycle,
                data_limit_gb,
                voice_minutes,
                sms_count,
                features,
                can_upgrade_to,
                can_downgrade_to
            """).eq("operator_id", operator_id).eq("is_active", True).order("price_cents").execute()
            
            plans = plans_response.data
            
            # If current plan is provided, categorize options
            if current_plan_id:
                current_plan = next((p for p in plans if p["id"] == current_plan_id), None)
                if current_plan:
                    upgrade_options = [p for p in plans if p["price_cents"] > current_plan["price_cents"]]
                    downgrade_options = [p for p in plans if p["price_cents"] < current_plan["price_cents"]]
                    lateral_options = [p for p in plans if p["price_cents"] == current_plan["price_cents"] and p["id"] != current_plan_id]
                    
                    return {
                        "success": True,
                        "current_plan": current_plan,
                        "upgrade_options": upgrade_options,
                        "downgrade_options": downgrade_options,
                        "lateral_options": lateral_options,
                        "all_plans": plans
                    }
            
            return {
                "success": True,
                "plans": plans,
                "count": len(plans)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _compare_plans(self, current_plan_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Compare two plans in detail"""
        if not current_plan_id or not new_plan_id:
            return {"success": False, "error": "Both plan IDs are required"}
        
        if self.mock_mode:
            return self._get_mock_plan_comparison(current_plan_id, new_plan_id)
        
        try:
            # Get both plans
            plans_response = self.supabase.table("subscription_plans").select("""
                id,
                name,
                description,
                price_cents,
                billing_cycle,
                data_limit_gb,
                voice_minutes,
                sms_count,
                features
            """).in_("id", [current_plan_id, new_plan_id]).execute()
            
            if len(plans_response.data) != 2:
                return {"success": False, "error": "One or both plans not found"}
            
            current_plan = next(p for p in plans_response.data if p["id"] == current_plan_id)
            new_plan = next(p for p in plans_response.data if p["id"] == new_plan_id)
            
            # Calculate differences
            price_diff = new_plan["price_cents"] - current_plan["price_cents"]
            data_diff = (new_plan.get("data_limit_gb", 0) or 0) - (current_plan.get("data_limit_gb", 0) or 0)
            
            # Feature comparison
            current_features = current_plan.get("features", {})
            new_features = new_plan.get("features", {})
            
            features_gained = []
            features_lost = []
            
            for feature, enabled in new_features.items():
                if enabled and not current_features.get(feature, False):
                    features_gained.append(feature)
            
            for feature, enabled in current_features.items():
                if enabled and not new_features.get(feature, False):
                    features_lost.append(feature)
            
            comparison = {
                "current_plan": current_plan,
                "new_plan": new_plan,
                "price_difference": {
                    "cents": price_diff,
                    "brl": price_diff / 100,
                    "percentage": (price_diff / current_plan["price_cents"]) * 100 if current_plan["price_cents"] > 0 else 0
                },
                "data_difference_gb": data_diff,
                "features_gained": features_gained,
                "features_lost": features_lost,
                "migration_type": "upgrade" if price_diff > 0 else "downgrade" if price_diff < 0 else "lateral",
                "is_better_value": self._calculate_value_score(new_plan) > self._calculate_value_score(current_plan)
            }
            
            return {
                "success": True,
                "comparison": comparison
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _calculate_migration_cost(self, subscription_id: str, new_plan_id: str, effective_date: str = None) -> Dict[str, Any]:
        """Calculate the cost for migrating to a new plan"""
        if not subscription_id or not new_plan_id:
            return {"success": False, "error": "Subscription ID and new plan ID are required"}
        
        if self.mock_mode:
            return self._get_mock_migration_cost(subscription_id, new_plan_id)
        
        try:
            # Get current subscription details
            subscription_response = self.supabase.table("user_subscriptions").select("""
                id,
                start_date,
                end_date,
                subscription_plans (
                    id,
                    name,
                    price_cents,
                    billing_cycle
                )
            """).eq("id", subscription_id).execute()
            
            if not subscription_response.data:
                return {"success": False, "error": "Subscription not found"}
            
            subscription = subscription_response.data[0]
            current_plan = subscription["subscription_plans"]
            
            # Get new plan details
            new_plan_response = self.supabase.table("subscription_plans").select("""
                id,
                name,
                price_cents,
                billing_cycle
            """).eq("id", new_plan_id).execute()
            
            if not new_plan_response.data:
                return {"success": False, "error": "New plan not found"}
            
            new_plan = new_plan_response.data[0]
            
            # Calculate costs
            current_price = current_plan["price_cents"]
            new_price = new_plan["price_cents"]
            price_difference = new_price - current_price
            
            # Calculate prorated costs if changing mid-cycle
            end_date = datetime.fromisoformat(subscription["end_date"].replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            
            if effective_date:
                effective_dt = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
            else:
                effective_dt = now
            
            days_remaining = (end_date - effective_dt).days
            total_cycle_days = 30  # Assuming monthly billing
            
            if days_remaining > 0:
                prorated_current = (current_price * days_remaining) // total_cycle_days
                prorated_new = (new_price * days_remaining) // total_cycle_days
                immediate_cost = max(0, prorated_new - prorated_current)
            else:
                immediate_cost = max(0, price_difference)
            
            cost_breakdown = {
                "current_plan": current_plan,
                "new_plan": new_plan,
                "price_difference_cents": price_difference,
                "price_difference_brl": price_difference / 100,
                "immediate_cost_cents": immediate_cost,
                "immediate_cost_brl": immediate_cost / 100,
                "days_remaining_in_cycle": max(0, days_remaining),
                "next_cycle_cost_cents": new_price,
                "next_cycle_cost_brl": new_price / 100,
                "migration_type": "upgrade" if price_difference > 0 else "downgrade" if price_difference < 0 else "lateral",
                "effective_date": effective_dt.isoformat()
            }
            
            return {
                "success": True,
                "cost_breakdown": cost_breakdown
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _validate_plan_change(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Validate if a plan change is allowed"""
        if not subscription_id or not new_plan_id:
            return {"success": False, "error": "Subscription ID and new plan ID are required"}
        
        if self.mock_mode:
            return self._get_mock_plan_validation(subscription_id, new_plan_id)
        
        try:
            # Get subscription and current plan
            subscription_response = self.supabase.table("user_subscriptions").select("""
                id,
                status,
                operator_id,
                plan_id,
                subscription_plans (
                    can_upgrade_to,
                    can_downgrade_to
                )
            """).eq("id", subscription_id).execute()
            
            if not subscription_response.data:
                return {"success": False, "error": "Subscription not found"}
            
            subscription = subscription_response.data[0]
            
            # Check if subscription is active
            if subscription["status"] != "active":
                return {
                    "success": False,
                    "valid": False,
                    "reason": f"Subscription status is {subscription['status']}, must be active for plan changes"
                }
            
            # Get new plan details
            new_plan_response = self.supabase.table("subscription_plans").select("""
                id,
                operator_id,
                is_active
            """).eq("id", new_plan_id).execute()
            
            if not new_plan_response.data:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "New plan not found"
                }
            
            new_plan = new_plan_response.data[0]
            
            # Check if new plan is active
            if not new_plan["is_active"]:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "New plan is not active"
                }
            
            # Check if plan belongs to same operator
            if subscription["operator_id"] != new_plan["operator_id"]:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "Cannot change to a plan from a different operator"
                }
            
            # Check if changing to the same plan
            if subscription["plan_id"] == new_plan_id:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "Cannot change to the same plan"
                }
            
            # Additional business rules can be added here
            # For now, allow all valid plan changes within the same operator
            
            return {
                "success": True,
                "valid": True,
                "reason": "Plan change is valid"
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _prepare_plan_migration(self, subscription_id: str, new_plan_id: str, migration_type: str = None) -> Dict[str, Any]:
        """Prepare all data needed for plan migration"""
        if not subscription_id or not new_plan_id:
            return {"success": False, "error": "Subscription ID and new plan ID are required"}
        
        try:
            # Validate the plan change
            validation_result = await self._validate_plan_change(subscription_id, new_plan_id)
            if not validation_result.get("valid", False):
                return validation_result
            
            # Get cost breakdown
            cost_result = await self._calculate_migration_cost(subscription_id, new_plan_id)
            if not cost_result.get("success", False):
                return cost_result
            
            # Get plan comparison
            subscription_response = self.supabase.table("user_subscriptions").select("plan_id").eq("id", subscription_id).execute()
            current_plan_id = subscription_response.data[0]["plan_id"] if subscription_response.data else None
            
            if current_plan_id:
                comparison_result = await self._compare_plans(current_plan_id, new_plan_id)
            else:
                comparison_result = {"success": False, "error": "Current plan not found"}
            
            migration_data = {
                "subscription_id": subscription_id,
                "new_plan_id": new_plan_id,
                "migration_type": migration_type or cost_result["cost_breakdown"]["migration_type"],
                "validation": validation_result,
                "cost_breakdown": cost_result.get("cost_breakdown", {}),
                "plan_comparison": comparison_result.get("comparison", {}),
                "prepared_at": datetime.now().isoformat(),
                "requires_payment": cost_result["cost_breakdown"]["immediate_cost_cents"] > 0,
                "ap2_ready": True
            }
            
            return {
                "success": True,
                "migration_data": migration_data
            }
            
        except Exception as e:
            logger.error(f"Plan migration preparation failed: {e}")
            return {"success": False, "error": f"Preparation failed: {str(e)}"}

    async def _execute_plan_change(self, subscription_id: str, new_plan_id: str, ap2_payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the plan change with AP2 payment processing"""
        if not subscription_id or not new_plan_id:
            return {"success": False, "error": "Subscription ID and new plan ID are required"}
        
        if self.mock_mode:
            return self._get_mock_plan_execution(subscription_id, new_plan_id)
        
        try:
            # Prepare migration data
            preparation_result = await self._prepare_plan_migration(subscription_id, new_plan_id)
            if not preparation_result.get("success", False):
                return preparation_result
            
            migration_data = preparation_result["migration_data"]
            
            # If payment is required, process it
            if migration_data["requires_payment"]:
                if not ap2_payment_data:
                    return {
                        "success": False,
                        "error": "Payment data required for plan upgrade",
                        "payment_required": True,
                        "amount_cents": migration_data["cost_breakdown"]["immediate_cost_cents"]
                    }
                
                # Here we would integrate with the AP2 payment tool
                # For now, simulate payment processing
                payment_result = await self._process_plan_change_payment(
                    subscription_id,
                    migration_data["cost_breakdown"]["immediate_cost_cents"],
                    ap2_payment_data
                )
                
                if not payment_result.get("success", False):
                    return payment_result
            
            # Update subscription with new plan
            update_data = {
                "plan_id": new_plan_id,
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("user_subscriptions").update(update_data).eq("id", subscription_id).execute()
            
            if not result.data:
                return {"success": False, "error": "Failed to update subscription"}
            
            # Record the plan change
            if migration_data["requires_payment"]:
                payment_record = {
                    "subscription_id": subscription_id,
                    "payment_type": migration_data["migration_type"],
                    "amount_cents": migration_data["cost_breakdown"]["immediate_cost_cents"],
                    "currency": "BRL",
                    "status": "completed",
                    "payment_method": ap2_payment_data.get("payment_method", "AP2") if ap2_payment_data else "AP2",
                    "ap2_mandate_id": ap2_payment_data.get("mandate_id") if ap2_payment_data else None,
                    "ap2_transaction_id": ap2_payment_data.get("transaction_id") if ap2_payment_data else None,
                    "processed_at": datetime.now().isoformat()
                }
                
                self.supabase.table("subscription_payments").insert(payment_record).execute()
            
            return {
                "success": True,
                "subscription_updated": result.data[0],
                "migration_completed": True,
                "migration_type": migration_data["migration_type"],
                "cost_breakdown": migration_data["cost_breakdown"],
                "executed_at": datetime.now().isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _process_plan_change_payment(self, subscription_id: str, amount_cents: int, ap2_payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment for plan change using AP2 protocol"""
        # This would integrate with the AP2 payment tool
        # For now, simulate successful payment
        return {
            "success": True,
            "payment_id": f"ap2_payment_{subscription_id}_{datetime.now().timestamp()}",
            "amount_cents": amount_cents,
            "currency": "BRL",
            "status": "completed",
            "ap2_mandate_id": ap2_payment_data.get("mandate_id"),
            "ap2_transaction_id": ap2_payment_data.get("transaction_id")
        }

    async def _get_migration_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get plan migration history for a user"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_migration_history(whatsapp_number)
        
        try:
            # Get user ID
            user_response = self.supabase.table("users").select("id").eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user_id = user_response.data[0]["id"]
            
            # Get migration history from payments
            history_response = self.supabase.table("subscription_payments").select("""
                id,
                payment_type,
                amount_cents,
                status,
                processed_at,
                user_subscriptions (
                    operators (display_name),
                    subscription_plans (name)
                )
            """).in_("payment_type", ["upgrade", "downgrade"]).eq("user_subscriptions.user_id", user_id).order("processed_at", desc=True).limit(10).execute()
            
            return {
                "success": True,
                "migration_history": history_response.data,
                "count": len(history_response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _rollback_plan_change(self, subscription_id: str) -> Dict[str, Any]:
        """Rollback a recent plan change (if applicable)"""
        # This is a complex operation that would require careful implementation
        # For now, return a placeholder
        return {
            "success": False,
            "error": "Plan rollback not implemented yet"
        }

    async def _get_plan_recommendations(self, subscription_id: str) -> Dict[str, Any]:
        """Get AI-powered plan recommendations based on usage patterns"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_plan_recommendations(subscription_id)
        
        # This would analyze usage patterns and recommend optimal plans
        # For now, return basic recommendations
        return {
            "success": True,
            "recommendations": [
                {
                    "plan_id": "recommended-plan-1",
                    "reason": "Better value for your usage pattern",
                    "savings_potential_brl": 15.00,
                    "confidence_score": 0.85
                }
            ]
        }

    def _calculate_value_score(self, plan: Dict[str, Any]) -> float:
        """Calculate a value score for a plan based on features and price"""
        score = 0.0
        
        # Base score from data
        data_gb = plan.get("data_limit_gb", 0) or 0
        score += data_gb * 10  # 10 points per GB
        
        # Features scoring
        features = plan.get("features", {})
        if features.get("unlimited_calls"):
            score += 50
        if features.get("unlimited_sms"):
            score += 20
        if features.get("social_media_free"):
            score += 30
        if features.get("streaming_free"):
            score += 40
        
        # Adjust for price (value = features / price)
        price_brl = plan["price_cents"] / 100
        if price_brl > 0:
            score = score / price_brl * 10
        
        return score

    # Mock data methods for testing
    def _get_mock_plan_options(self, operator_id: str, current_plan_id: str = None) -> Dict[str, Any]:
        """Mock plan options data"""
        mock_plans = [
            {"id": "plan-basic", "name": "Basic 5GB", "price_cents": 2990, "data_limit_gb": 5},
            {"id": "plan-premium", "name": "Premium 10GB", "price_cents": 4990, "data_limit_gb": 10},
            {"id": "plan-ultimate", "name": "Ultimate 20GB", "price_cents": 7990, "data_limit_gb": 20}
        ]
        
        if current_plan_id == "plan-basic":
            return {
                "success": True,
                "current_plan": mock_plans[0],
                "upgrade_options": mock_plans[1:],
                "downgrade_options": [],
                "lateral_options": [],
                "all_plans": mock_plans
            }
        
        return {
            "success": True,
            "plans": mock_plans,
            "count": len(mock_plans)
        }

    def _get_mock_plan_comparison(self, current_plan_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Mock plan comparison data"""
        return {
            "success": True,
            "comparison": {
                "current_plan": {"id": current_plan_id, "name": "Current Plan", "price_cents": 2990},
                "new_plan": {"id": new_plan_id, "name": "New Plan", "price_cents": 4990},
                "price_difference": {"cents": 2000, "brl": 20.00, "percentage": 66.89},
                "data_difference_gb": 5,
                "features_gained": ["unlimited_sms", "social_media_free"],
                "features_lost": [],
                "migration_type": "upgrade",
                "is_better_value": True
            }
        }

    def _get_mock_migration_cost(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Mock migration cost data"""
        return {
            "success": True,
            "cost_breakdown": {
                "price_difference_cents": 2000,
                "price_difference_brl": 20.00,
                "immediate_cost_cents": 1500,
                "immediate_cost_brl": 15.00,
                "days_remaining_in_cycle": 20,
                "next_cycle_cost_cents": 4990,
                "next_cycle_cost_brl": 49.90,
                "migration_type": "upgrade"
            }
        }

    def _get_mock_plan_validation(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Mock plan validation data"""
        return {
            "success": True,
            "valid": True,
            "reason": "Plan change is valid"
        }

    def _get_mock_plan_execution(self, subscription_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Mock plan execution data"""
        return {
            "success": True,
            "subscription_updated": {"id": subscription_id, "plan_id": new_plan_id},
            "migration_completed": True,
            "migration_type": "upgrade",
            "executed_at": datetime.now().isoformat()
        }

    def _get_mock_migration_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock migration history data"""
        return {
            "success": True,
            "migration_history": [
                {
                    "id": "payment-001",
                    "payment_type": "upgrade",
                    "amount_cents": 2000,
                    "status": "completed",
                    "processed_at": "2025-01-15T10:00:00Z"
                }
            ],
            "count": 1
        }

    def _get_mock_plan_recommendations(self, subscription_id: str) -> Dict[str, Any]:
        """Mock plan recommendations"""
        return {
            "success": True,
            "recommendations": [
                {
                    "plan_id": "plan-premium",
                    "plan_name": "Premium 10GB",
                    "reason": "Better value for your usage pattern",
                    "savings_potential_brl": 15.00,
                    "confidence_score": 0.85
                }
            ]
        }


# Tool instance for agent integration
plan_management_tool = PlanManagementTool()
