"""
Subscription Management Tool for sofIA Agent
Handles subscription discovery, renewal monitoring, and plan management via Supabase
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from supabase import create_client, Client
from postgrest import APIError

logger = logging.getLogger(__name__)


class SubscriptionManagementTool:
    """Tool for comprehensive subscription lifecycle management"""
    
    def __init__(self):
        self.name = "subscription_management"
        self.description = "Comprehensive subscription lifecycle management including discovery, renewals, and plan changes"
        
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
                        "get_user_subscriptions",
                        "get_subscription_details", 
                        "check_expiring_subscriptions",
                        "get_available_plans",
                        "calculate_plan_change_cost",
                        "get_operators",
                        "get_plan_comparison",
                        "get_subscription_by_id"
                    ],
                    "description": "Operation to perform"
                },
                "whatsapp_number": {
                    "type": "string",
                    "description": "WhatsApp number of the user (required for user-specific operations)"
                },
                "subscription_id": {
                    "type": "string", 
                    "description": "Subscription ID for specific subscription operations"
                },
                "operator_id": {
                    "type": "string",
                    "description": "Operator ID for plan-related operations"
                },
                "current_plan_id": {
                    "type": "string",
                    "description": "Current plan ID for comparison operations"
                },
                "new_plan_id": {
                    "type": "string",
                    "description": "New plan ID for cost calculation"
                },
                "days_ahead": {
                    "type": "integer",
                    "default": 7,
                    "description": "Number of days ahead to check for expiring subscriptions"
                }
            },
            "required": ["operation"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute subscription management operations"""
        operation = kwargs.get("operation")
        
        try:
            if operation == "get_user_subscriptions":
                return await self._get_user_subscriptions(kwargs.get("whatsapp_number"))
            elif operation == "get_subscription_details":
                return await self._get_subscription_details(kwargs.get("subscription_id"))
            elif operation == "check_expiring_subscriptions":
                return await self._check_expiring_subscriptions(kwargs.get("days_ahead", 7))
            elif operation == "get_available_plans":
                return await self._get_available_plans(kwargs.get("operator_id"))
            elif operation == "calculate_plan_change_cost":
                return await self._calculate_plan_change_cost(
                    kwargs.get("current_plan_id"),
                    kwargs.get("new_plan_id")
                )
            elif operation == "get_operators":
                return await self._get_operators()
            elif operation == "get_plan_comparison":
                return await self._get_plan_comparison(
                    kwargs.get("operator_id"),
                    kwargs.get("current_plan_id")
                )
            elif operation == "get_subscription_by_id":
                return await self._get_subscription_by_id(kwargs.get("subscription_id"))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Subscription management operation failed: {e}")
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    async def _get_user_subscriptions(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get all subscriptions for a user by WhatsApp number"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_user_subscriptions(whatsapp_number)
        
        try:
            # Get user by WhatsApp number
            user_response = self.supabase.table("users").select("id").eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {
                    "success": True,
                    "subscriptions": [],
                    "message": "No user found with this WhatsApp number"
                }
            
            user_id = user_response.data[0]["id"]
            
            # Get subscriptions with operator and plan details
            subscriptions_response = self.supabase.table("user_subscriptions").select("""
                id,
                status,
                start_date,
                end_date,
                auto_renewal,
                subscription_external_id,
                operators (
                    id,
                    name,
                    display_name,
                    logo_url,
                    brand_color
                ),
                subscription_plans (
                    id,
                    name,
                    description,
                    price_cents,
                    billing_cycle,
                    data_limit_gb,
                    voice_minutes,
                    sms_count,
                    features
                )
            """).eq("user_id", user_id).eq("status", "active").execute()
            
            return {
                "success": True,
                "subscriptions": subscriptions_response.data,
                "count": len(subscriptions_response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific subscription"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_subscription_details(subscription_id)
        
        try:
            response = self.supabase.table("user_subscriptions").select("""
                id,
                status,
                start_date,
                end_date,
                auto_renewal,
                subscription_external_id,
                metadata,
                users (
                    whatsapp_number,
                    full_name,
                    email
                ),
                operators (
                    id,
                    name,
                    display_name,
                    logo_url,
                    brand_color
                ),
                subscription_plans (
                    id,
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
                )
            """).eq("id", subscription_id).execute()
            
            if not response.data:
                return {"success": False, "error": "Subscription not found"}
            
            subscription = response.data[0]
            
            # Calculate time until expiry
            end_date = datetime.fromisoformat(subscription["end_date"].replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            time_until_expiry = end_date - now
            
            subscription["time_until_expiry_days"] = time_until_expiry.days
            subscription["time_until_expiry_hours"] = time_until_expiry.total_seconds() / 3600
            subscription["is_expiring_soon"] = time_until_expiry.days <= 7
            subscription["is_expired"] = time_until_expiry.days < 0
            
            return {
                "success": True,
                "subscription": subscription
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _check_expiring_subscriptions(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Check for subscriptions expiring within specified days"""
        if self.mock_mode:
            return self._get_mock_expiring_subscriptions(days_ahead)
        
        try:
            # Calculate the date range
            now = datetime.now()
            future_date = now + timedelta(days=days_ahead)
            
            response = self.supabase.table("user_subscriptions").select("""
                id,
                status,
                end_date,
                auto_renewal,
                users (
                    whatsapp_number,
                    full_name
                ),
                operators (
                    name,
                    display_name
                ),
                subscription_plans (
                    name,
                    price_cents,
                    billing_cycle
                )
            """).eq("status", "active").gte("end_date", now.isoformat()).lte("end_date", future_date.isoformat()).execute()
            
            # Sort by expiry date
            expiring_subscriptions = sorted(response.data, key=lambda x: x["end_date"])
            
            return {
                "success": True,
                "expiring_subscriptions": expiring_subscriptions,
                "count": len(expiring_subscriptions),
                "days_ahead": days_ahead
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_available_plans(self, operator_id: str) -> Dict[str, Any]:
        """Get all available plans for an operator"""
        if not operator_id:
            return {"success": False, "error": "Operator ID is required"}
        
        if self.mock_mode:
            return self._get_mock_available_plans(operator_id)
        
        try:
            response = self.supabase.table("subscription_plans").select("*").eq("operator_id", operator_id).eq("is_active", True).order("price_cents").execute()
            
            return {
                "success": True,
                "plans": response.data,
                "count": len(response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _calculate_plan_change_cost(self, current_plan_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Calculate the cost difference for changing plans"""
        if not current_plan_id or not new_plan_id:
            return {"success": False, "error": "Both current and new plan IDs are required"}
        
        if self.mock_mode:
            return self._get_mock_plan_change_cost(current_plan_id, new_plan_id)
        
        try:
            # Get both plans
            plans_response = self.supabase.table("subscription_plans").select("id, name, price_cents, billing_cycle, data_limit_gb").in_("id", [current_plan_id, new_plan_id]).execute()
            
            if len(plans_response.data) != 2:
                return {"success": False, "error": "One or both plans not found"}
            
            current_plan = next(p for p in plans_response.data if p["id"] == current_plan_id)
            new_plan = next(p for p in plans_response.data if p["id"] == new_plan_id)
            
            price_difference = new_plan["price_cents"] - current_plan["price_cents"]
            
            return {
                "success": True,
                "current_plan": current_plan,
                "new_plan": new_plan,
                "price_difference_cents": price_difference,
                "price_difference_brl": price_difference / 100,
                "is_upgrade": price_difference > 0,
                "is_downgrade": price_difference < 0,
                "is_same_price": price_difference == 0
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_operators(self) -> Dict[str, Any]:
        """Get all active operators"""
        if self.mock_mode:
            return self._get_mock_operators()
        
        try:
            response = self.supabase.table("operators").select("*").eq("is_active", True).order("name").execute()
            
            return {
                "success": True,
                "operators": response.data,
                "count": len(response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_plan_comparison(self, operator_id: str, current_plan_id: str) -> Dict[str, Any]:
        """Get plan comparison for upgrade/downgrade options"""
        if not operator_id or not current_plan_id:
            return {"success": False, "error": "Operator ID and current plan ID are required"}
        
        try:
            # Get current plan
            current_plan_response = self.supabase.table("subscription_plans").select("*").eq("id", current_plan_id).execute()
            if not current_plan_response.data:
                return {"success": False, "error": "Current plan not found"}
            
            current_plan = current_plan_response.data[0]
            
            # Get all plans for the operator
            all_plans_response = self.supabase.table("subscription_plans").select("*").eq("operator_id", operator_id).eq("is_active", True).order("price_cents").execute()
            
            upgrade_options = []
            downgrade_options = []
            
            for plan in all_plans_response.data:
                if plan["id"] == current_plan_id:
                    continue
                
                if plan["price_cents"] > current_plan["price_cents"]:
                    upgrade_options.append({
                        **plan,
                        "price_difference_cents": plan["price_cents"] - current_plan["price_cents"],
                        "price_difference_brl": (plan["price_cents"] - current_plan["price_cents"]) / 100
                    })
                elif plan["price_cents"] < current_plan["price_cents"]:
                    downgrade_options.append({
                        **plan,
                        "price_difference_cents": plan["price_cents"] - current_plan["price_cents"],
                        "price_difference_brl": (plan["price_cents"] - current_plan["price_cents"]) / 100
                    })
            
            return {
                "success": True,
                "current_plan": current_plan,
                "upgrade_options": upgrade_options,
                "downgrade_options": downgrade_options,
                "can_upgrade": len(upgrade_options) > 0,
                "can_downgrade": len(downgrade_options) > 0
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_subscription_by_id(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription by ID with minimal details"""
        return await self._get_subscription_details(subscription_id)

    # Mock data methods for testing without Supabase
    def _get_mock_user_subscriptions(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock data for user subscriptions"""
        mock_subscriptions = {
            "+5511999887766": [  # João Silva Santos
                {
                    "id": "sub-001",
                    "status": "active",
                    "start_date": "2025-01-01T00:00:00Z",
                    "end_date": "2025-01-31T00:00:00Z",
                    "auto_renewal": True,
                    "operators": {
                        "id": "vivo-op",
                        "name": "VIVO",
                        "display_name": "Vivo",
                        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Vivo_logo.svg/200px-Vivo_logo.svg.png",
                        "brand_color": "#8B2797"
                    },
                    "subscription_plans": {
                        "id": "vivo-002",
                        "name": "Vivo Premium 10GB",
                        "description": "Plano premium com 10GB de internet",
                        "price_cents": 4990,
                        "billing_cycle": "monthly",
                        "data_limit_gb": 10,
                        "voice_minutes": -1,
                        "sms_count": -1,
                        "features": {"unlimited_calls": True, "whatsapp_free": True}
                    }
                }
            ],
            "+5511888776655": [  # Maria Oliveira Costa
                {
                    "id": "sub-002",
                    "status": "active",
                    "start_date": "2025-01-05T00:00:00Z",
                    "end_date": "2025-02-05T00:00:00Z",
                    "auto_renewal": True,
                    "operators": {
                        "id": "claro-op",
                        "name": "CLARO",
                        "display_name": "Claro",
                        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Claro.svg/200px-Claro.svg.png",
                        "brand_color": "#E61E24"
                    },
                    "subscription_plans": {
                        "id": "claro-002",
                        "name": "Claro Smart 8GB",
                        "description": "Plano inteligente com 8GB",
                        "price_cents": 3990,
                        "billing_cycle": "monthly",
                        "data_limit_gb": 8,
                        "voice_minutes": -1,
                        "sms_count": 200,
                        "features": {"unlimited_calls": True, "social_media_free": True}
                    }
                }
            ]
        }
        
        subscriptions = mock_subscriptions.get(whatsapp_number, [])
        return {
            "success": True,
            "subscriptions": subscriptions,
            "count": len(subscriptions)
        }

    def _get_mock_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Mock subscription details"""
        return {
            "success": True,
            "subscription": {
                "id": subscription_id,
                "status": "active",
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-01-31T00:00:00Z",
                "auto_renewal": True,
                "time_until_expiry_days": 3,
                "time_until_expiry_hours": 72,
                "is_expiring_soon": True,
                "is_expired": False,
                "operators": {
                    "name": "VIVO",
                    "display_name": "Vivo"
                },
                "subscription_plans": {
                    "name": "Vivo Premium 10GB",
                    "price_cents": 4990,
                    "billing_cycle": "monthly"
                }
            }
        }

    def _get_mock_expiring_subscriptions(self, days_ahead: int) -> Dict[str, Any]:
        """Mock expiring subscriptions"""
        return {
            "success": True,
            "expiring_subscriptions": [
                {
                    "id": "sub-004",
                    "end_date": "2025-01-29T00:00:00Z",
                    "users": {
                        "whatsapp_number": "+5511666554433",
                        "full_name": "Ana Paula Ferreira"
                    },
                    "operators": {
                        "name": "OI",
                        "display_name": "Oi"
                    },
                    "subscription_plans": {
                        "name": "Oi Total 12GB",
                        "price_cents": 5990,
                        "billing_cycle": "monthly"
                    }
                }
            ],
            "count": 1,
            "days_ahead": days_ahead
        }

    def _get_mock_available_plans(self, operator_id: str) -> Dict[str, Any]:
        """Mock available plans"""
        plans = {
            "vivo-op": [
                {"id": "vivo-001", "name": "Vivo Basic 5GB", "price_cents": 2990, "data_limit_gb": 5},
                {"id": "vivo-002", "name": "Vivo Premium 10GB", "price_cents": 4990, "data_limit_gb": 10},
                {"id": "vivo-003", "name": "Vivo Ultimate 20GB", "price_cents": 7990, "data_limit_gb": 20}
            ]
        }
        
        operator_plans = plans.get(operator_id, [])
        return {
            "success": True,
            "plans": operator_plans,
            "count": len(operator_plans)
        }

    def _get_mock_plan_change_cost(self, current_plan_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Mock plan change cost calculation"""
        return {
            "success": True,
            "current_plan": {"id": current_plan_id, "name": "Current Plan", "price_cents": 4990},
            "new_plan": {"id": new_plan_id, "name": "New Plan", "price_cents": 7990},
            "price_difference_cents": 3000,
            "price_difference_brl": 30.00,
            "is_upgrade": True,
            "is_downgrade": False,
            "is_same_price": False
        }

    def _get_mock_operators(self) -> Dict[str, Any]:
        """Mock operators data"""
        return {
            "success": True,
            "operators": [
                {"id": "vivo-op", "name": "VIVO", "display_name": "Vivo", "brand_color": "#8B2797"},
                {"id": "claro-op", "name": "CLARO", "display_name": "Claro", "brand_color": "#E61E24"},
                {"id": "oi-op", "name": "OI", "display_name": "Oi", "brand_color": "#F9B233"},
                {"id": "tim-op", "name": "TIM", "display_name": "TIM", "brand_color": "#1E3A96"}
            ],
            "count": 4
        }


# Tool instance for agent integration
subscription_management_tool = SubscriptionManagementTool()
