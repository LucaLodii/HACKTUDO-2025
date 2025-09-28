"""
Merchant-specific Subscription Management for White-label sofIA

This tool manages subscription plans for the current merchant/operator only,
ensuring true white-label behavior where each operator only sees their own products.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class OperatorPlan:
    """Subscription plan for a specific operator"""
    plan_id: str
    operator_id: str
    operator_name: str
    plan_code: str
    name: str
    description: str
    price_cents: int
    billing_cycle: str
    data_limit_gb: Optional[int]
    voice_minutes: Optional[int]
    sms_count: Optional[int]
    features: Dict[str, Any]
    can_upgrade_to: List[str]
    can_downgrade_to: List[str]
    is_active: bool


class MerchantSubscriptionManager:
    """Manages subscriptions for a specific merchant/operator only"""

    def __init__(self, operator_name: str):
        self.operator_name = operator_name.upper()
        self.plans = self._load_merchant_plans()

    def _load_merchant_plans(self) -> List[OperatorPlan]:
        """Load subscription plans for the current merchant's operator only"""

        # Mock data mapping - in production, this would query the database
        # filtering by the current merchant's operator_id
        all_plans_data = {
            "VIVO": [
                {
                    "plan_id": "vivo-001",
                    "operator_id": "11111111-1111-1111-1111-111111111111",
                    "operator_name": "VIVO",
                    "plan_code": "VIVO_BASIC_5GB",
                    "name": "Vivo Basic 5GB",
                    "description": "Plano básico com 5GB de internet, ligações ilimitadas e 100 SMS",
                    "price_cents": 2990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 5,
                    "voice_minutes": -1,
                    "sms_count": 100,
                    "features": {"unlimited_calls": True, "whatsapp_free": True, "social_media_free": False},
                    "can_upgrade_to": ["vivo-002", "vivo-003"],
                    "can_downgrade_to": [],
                    "is_active": True
                },
                {
                    "plan_id": "vivo-002",
                    "operator_id": "11111111-1111-1111-1111-111111111111",
                    "operator_name": "VIVO",
                    "plan_code": "VIVO_PREMIUM_10GB",
                    "name": "Vivo Premium 10GB",
                    "description": "Plano premium com 10GB de internet, ligações ilimitadas e SMS ilimitados",
                    "price_cents": 4990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 10,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True},
                    "can_upgrade_to": ["vivo-003", "vivo-004"],
                    "can_downgrade_to": ["vivo-001"],
                    "is_active": True
                },
                {
                    "plan_id": "vivo-003",
                    "operator_id": "11111111-1111-1111-1111-111111111111",
                    "operator_name": "VIVO",
                    "plan_code": "VIVO_ULTIMATE_20GB",
                    "name": "Vivo Ultimate 20GB",
                    "description": "Plano ultimate com 20GB de internet, ligações e SMS ilimitados, apps grátis",
                    "price_cents": 7990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 20,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "streaming_free": True},
                    "can_upgrade_to": ["vivo-004"],
                    "can_downgrade_to": ["vivo-001", "vivo-002"],
                    "is_active": True
                },
                {
                    "plan_id": "vivo-004",
                    "operator_id": "11111111-1111-1111-1111-111111111111",
                    "operator_name": "VIVO",
                    "plan_code": "VIVO_INFINITY_50GB",
                    "name": "Vivo Infinity 50GB",
                    "description": "Plano infinity com 50GB de internet, tudo ilimitado e apps premium",
                    "price_cents": 12990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 50,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "streaming_free": True, "gaming_free": True},
                    "can_upgrade_to": [],
                    "can_downgrade_to": ["vivo-001", "vivo-002", "vivo-003"],
                    "is_active": True
                }
            ],
            "CLARO": [
                {
                    "plan_id": "claro-001",
                    "operator_id": "22222222-2222-2222-2222-222222222222",
                    "operator_name": "CLARO",
                    "plan_code": "CLARO_EASY_3GB",
                    "name": "Claro Easy 3GB",
                    "description": "Plano econômico com 3GB de internet e ligações limitadas",
                    "price_cents": 1990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 3,
                    "voice_minutes": 300,
                    "sms_count": 50,
                    "features": {"unlimited_calls": False, "whatsapp_free": True},
                    "can_upgrade_to": ["claro-002", "claro-003"],
                    "can_downgrade_to": [],
                    "is_active": True
                },
                {
                    "plan_id": "claro-002",
                    "operator_id": "22222222-2222-2222-2222-222222222222",
                    "operator_name": "CLARO",
                    "plan_code": "CLARO_SMART_8GB",
                    "name": "Claro Smart 8GB",
                    "description": "Plano inteligente com 8GB de internet e ligações ilimitadas",
                    "price_cents": 3990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 8,
                    "voice_minutes": -1,
                    "sms_count": 200,
                    "features": {"unlimited_calls": True, "whatsapp_free": True, "social_media_free": True},
                    "can_upgrade_to": ["claro-003", "claro-004"],
                    "can_downgrade_to": ["claro-001"],
                    "is_active": True
                },
                {
                    "plan_id": "claro-003",
                    "operator_id": "22222222-2222-2222-2222-222222222222",
                    "operator_name": "CLARO",
                    "plan_code": "CLARO_POWER_15GB",
                    "name": "Claro Power 15GB",
                    "description": "Plano poderoso com 15GB de internet e recursos premium",
                    "price_cents": 6990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 15,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "netflix_included": True},
                    "can_upgrade_to": ["claro-004"],
                    "can_downgrade_to": ["claro-001", "claro-002"],
                    "is_active": True
                },
                {
                    "plan_id": "claro-004",
                    "operator_id": "22222222-2222-2222-2222-222222222222",
                    "operator_name": "CLARO",
                    "plan_code": "CLARO_UNLIMITED",
                    "name": "Claro Unlimited",
                    "description": "Plano ilimitado com 30GB e todos os benefícios",
                    "price_cents": 9990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 30,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "netflix_included": True, "spotify_included": True},
                    "can_upgrade_to": [],
                    "can_downgrade_to": ["claro-001", "claro-002", "claro-003"],
                    "is_active": True
                }
            ],
            "OI": [
                {
                    "plan_id": "oi-001",
                    "operator_id": "33333333-3333-3333-3333-333333333333",
                    "operator_name": "OI",
                    "plan_code": "OI_SIMPLES_2GB",
                    "name": "Oi Simples 2GB",
                    "description": "Plano simples com 2GB de internet básica",
                    "price_cents": 1590,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 2,
                    "voice_minutes": 200,
                    "sms_count": 30,
                    "features": {"unlimited_calls": False, "whatsapp_free": True},
                    "can_upgrade_to": ["oi-002", "oi-003"],
                    "can_downgrade_to": [],
                    "is_active": True
                },
                {
                    "plan_id": "oi-002",
                    "operator_id": "33333333-3333-3333-3333-333333333333",
                    "operator_name": "OI",
                    "plan_code": "OI_CONECTA_6GB",
                    "name": "Oi Conecta 6GB",
                    "description": "Plano conectado com 6GB de internet e apps grátis",
                    "price_cents": 2990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 6,
                    "voice_minutes": -1,
                    "sms_count": 150,
                    "features": {"unlimited_calls": True, "whatsapp_free": True, "social_media_free": True},
                    "can_upgrade_to": ["oi-003", "oi-004"],
                    "can_downgrade_to": ["oi-001"],
                    "is_active": True
                },
                {
                    "plan_id": "oi-003",
                    "operator_id": "33333333-3333-3333-3333-333333333333",
                    "operator_name": "OI",
                    "plan_code": "OI_TOTAL_12GB",
                    "name": "Oi Total 12GB",
                    "description": "Plano total com 12GB de internet e entretenimento",
                    "price_cents": 5990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 12,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "music_streaming": True},
                    "can_upgrade_to": ["oi-004"],
                    "can_downgrade_to": ["oi-001", "oi-002"],
                    "is_active": True
                },
                {
                    "plan_id": "oi-004",
                    "operator_id": "33333333-3333-3333-3333-333333333333",
                    "operator_name": "OI",
                    "plan_code": "OI_PREMIUM_25GB",
                    "name": "Oi Premium 25GB",
                    "description": "Plano premium com 25GB e benefícios exclusivos",
                    "price_cents": 8990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 25,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "music_streaming": True, "video_streaming": True},
                    "can_upgrade_to": [],
                    "can_downgrade_to": ["oi-001", "oi-002", "oi-003"],
                    "is_active": True
                }
            ],
            "TIM": [
                {
                    "plan_id": "tim-001",
                    "operator_id": "44444444-4444-4444-4444-444444444444",
                    "operator_name": "TIM",
                    "plan_code": "TIM_LIGHT_4GB",
                    "name": "TIM Light 4GB",
                    "description": "Plano leve com 4GB de internet e comunicação básica",
                    "price_cents": 2490,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 4,
                    "voice_minutes": 250,
                    "sms_count": 80,
                    "features": {"unlimited_calls": False, "whatsapp_free": True, "social_media_free": False},
                    "can_upgrade_to": ["tim-002", "tim-003"],
                    "can_downgrade_to": [],
                    "is_active": True
                },
                {
                    "plan_id": "tim-002",
                    "operator_id": "44444444-4444-4444-4444-444444444444",
                    "operator_name": "TIM",
                    "plan_code": "TIM_FLEX_9GB",
                    "name": "TIM Flex 9GB",
                    "description": "Plano flexível com 9GB de internet e apps inclusos",
                    "price_cents": 4490,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 9,
                    "voice_minutes": -1,
                    "sms_count": 300,
                    "features": {"unlimited_calls": True, "whatsapp_free": True, "social_media_free": True, "telegram_free": True},
                    "can_upgrade_to": ["tim-003", "tim-004"],
                    "can_downgrade_to": ["tim-001"],
                    "is_active": True
                },
                {
                    "plan_id": "tim-003",
                    "operator_id": "44444444-4444-4444-4444-444444444444",
                    "operator_name": "TIM",
                    "plan_code": "TIM_BLACK_18GB",
                    "name": "TIM Black 18GB",
                    "description": "Plano black com 18GB e entretenimento premium",
                    "price_cents": 7490,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 18,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "netflix_tim": True, "paramount_plus": True},
                    "can_upgrade_to": ["tim-004"],
                    "can_downgrade_to": ["tim-001", "tim-002"],
                    "is_active": True
                },
                {
                    "plan_id": "tim-004",
                    "operator_id": "44444444-4444-4444-4444-444444444444",
                    "operator_name": "TIM",
                    "plan_code": "TIM_BLACK_FAMILIA_60GB",
                    "name": "TIM Black Família 60GB",
                    "description": "Plano família com 60GB compartilhados e benefícios completos",
                    "price_cents": 11990,
                    "billing_cycle": "monthly",
                    "data_limit_gb": 60,
                    "voice_minutes": -1,
                    "sms_count": -1,
                    "features": {"unlimited_calls": True, "unlimited_sms": True, "whatsapp_free": True, "social_media_free": True, "netflix_tim": True, "paramount_plus": True, "deezer_premium": True, "family_sharing": True},
                    "can_upgrade_to": [],
                    "can_downgrade_to": ["tim-001", "tim-002", "tim-003"],
                    "is_active": True
                }
            ]
        }

        # Return only this merchant's operator plans
        operator_plans_data = all_plans_data.get(self.operator_name, [])
        return [OperatorPlan(**plan) for plan in operator_plans_data]

    async def get_available_plans(self) -> Dict[str, Any]:
        """Get all available plans for this merchant's operator"""
        active_plans = [plan for plan in self.plans if plan.is_active]

        return {
            "success": True,
            "operator": self.operator_name,
            "plans": [
                {
                    "plan_id": plan.plan_id,
                    "plan_code": plan.plan_code,
                    "name": plan.name,
                    "description": plan.description,
                    "price_brl": plan.price_cents / 100,
                    "price_cents": plan.price_cents,
                    "billing_cycle": plan.billing_cycle,
                    "data_limit_gb": plan.data_limit_gb,
                    "voice_minutes": "Ilimitado" if plan.voice_minutes == -1 else plan.voice_minutes,
                    "sms_count": "Ilimitado" if plan.sms_count == -1 else plan.sms_count,
                    "features": plan.features,
                    "can_upgrade_to": plan.can_upgrade_to,
                    "can_downgrade_to": plan.can_downgrade_to
                }
                for plan in active_plans
            ],
            "total_plans": len(active_plans)
        }

    async def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific plan from this operator"""
        for plan in self.plans:
            if plan.plan_id == plan_id:
                return {
                    "success": True,
                    "plan": {
                        "plan_id": plan.plan_id,
                        "operator": plan.operator_name,
                        "plan_code": plan.plan_code,
                        "name": plan.name,
                        "description": plan.description,
                        "price_brl": plan.price_cents / 100,
                        "price_cents": plan.price_cents,
                        "billing_cycle": plan.billing_cycle,
                        "data_limit_gb": plan.data_limit_gb,
                        "voice_minutes": "Ilimitado" if plan.voice_minutes == -1 else plan.voice_minutes,
                        "sms_count": "Ilimitado" if plan.sms_count == -1 else plan.sms_count,
                        "features": plan.features,
                        "can_upgrade_to": plan.can_upgrade_to,
                        "can_downgrade_to": plan.can_downgrade_to,
                        "is_active": plan.is_active
                    }
                }

        return {
            "error": f"Plan {plan_id} not found in {self.operator_name} catalog",
            "operator": self.operator_name
        }

    async def get_upgrade_options(self, current_plan_id: str) -> Dict[str, Any]:
        """Get available upgrade options for a current plan"""
        plan_details = await self.get_plan_details(current_plan_id)

        if "error" in plan_details:
            return plan_details

        current_plan = plan_details["plan"]
        upgrade_options = []

        for upgrade_plan_id in current_plan["can_upgrade_to"]:
            upgrade_plan = await self.get_plan_details(upgrade_plan_id)
            if "error" not in upgrade_plan:
                upgrade_plan_data = upgrade_plan["plan"]
                price_difference = upgrade_plan_data["price_cents"] - current_plan["price_cents"]

                upgrade_options.append({
                    "plan_id": upgrade_plan_data["plan_id"],
                    "name": upgrade_plan_data["name"],
                    "description": upgrade_plan_data["description"],
                    "price_brl": upgrade_plan_data["price_brl"],
                    "price_difference_brl": price_difference / 100,
                    "data_increase_gb": upgrade_plan_data["data_limit_gb"] - current_plan["data_limit_gb"] if current_plan["data_limit_gb"] else None,
                    "new_features": upgrade_plan_data["features"]
                })

        return {
            "success": True,
            "operator": self.operator_name,
            "current_plan": current_plan,
            "upgrade_options": upgrade_options,
            "total_options": len(upgrade_options)
        }

    async def get_recommended_plans(self, usage_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get recommended plans based on usage profile for this operator"""
        plans_result = await self.get_available_plans()
        plans = plans_result["plans"]

        # Simple recommendation logic based on usage profile
        if usage_profile:
            data_usage_gb = usage_profile.get("data_usage_gb", 10)
            budget_brl = usage_profile.get("budget_brl", 50)

            # Filter plans by budget and data needs
            suitable_plans = []
            for plan in plans:
                if (plan["price_brl"] <= budget_brl and
                    plan["data_limit_gb"] and plan["data_limit_gb"] >= data_usage_gb):
                    suitable_plans.append(plan)

            # Sort by value (data per real)
            suitable_plans.sort(key=lambda p: p["data_limit_gb"] / p["price_brl"], reverse=True)

            return {
                "success": True,
                "operator": self.operator_name,
                "usage_profile": usage_profile,
                "recommended_plans": suitable_plans[:3],  # Top 3 recommendations
                "total_suitable": len(suitable_plans)
            }
        else:
            # Default recommendations: most popular plans (sorted by price)
            popular_plans = sorted(plans, key=lambda p: p["price_brl"])[:3]

            return {
                "success": True,
                "operator": self.operator_name,
                "recommended_plans": popular_plans,
                "recommendation_type": "popular_plans"
            }


# Factory function to create merchant-specific managers
def create_merchant_subscription_manager(operator_name: str) -> MerchantSubscriptionManager:
    """Create a subscription manager for a specific merchant/operator"""
    return MerchantSubscriptionManager(operator_name)


# Tool functions that work with the current merchant context
async def get_merchant_subscription_plans(operator_name: str) -> Dict[str, Any]:
    """Get subscription plans for the current merchant"""
    manager = create_merchant_subscription_manager(operator_name)
    return await manager.get_available_plans()


async def get_merchant_plan_details(plan_id: str, operator_name: str) -> Dict[str, Any]:
    """Get plan details for the current merchant"""
    manager = create_merchant_subscription_manager(operator_name)
    return await manager.get_plan_details(plan_id)


async def get_merchant_upgrade_options(current_plan_id: str, operator_name: str) -> Dict[str, Any]:
    """Get upgrade options for the current merchant"""
    manager = create_merchant_subscription_manager(operator_name)
    return await manager.get_upgrade_options(current_plan_id)


async def get_merchant_plan_recommendations(operator_name: str, usage_profile: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get plan recommendations for the current merchant"""
    manager = create_merchant_subscription_manager(operator_name)
    return await manager.get_recommended_plans(usage_profile)