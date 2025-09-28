"""
Subscription Notifications Tool for sofIA Agent
Handles proactive subscription renewal warnings and paycheck availability notifications
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from supabase import create_client, Client
from postgrest import APIError

logger = logging.getLogger(__name__)


class SubscriptionNotificationsTool:
    """Tool for proactive subscription renewal warnings and notifications"""
    
    def __init__(self):
        self.name = "subscription_notifications"
        self.description = "Proactive subscription renewal warnings and notifications"
        
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
                        "check_renewal_warnings",
                        "send_renewal_warning",
                        "get_user_notification_preferences",
                        "update_notification_preferences",
                        "get_notification_history",
                        "schedule_renewal_reminder",
                        "check_expiring_subscriptions",
                        "get_upcoming_renewals"
                    ],
                    "description": "Notification operation to perform"
                },
                "whatsapp_number": {
                    "type": "string",
                    "description": "WhatsApp number of the user"
                },
                "subscription_id": {
                    "type": "string",
                    "description": "Subscription ID for specific operations"
                },
                "days_ahead": {
                    "type": "integer",
                    "default": 7,
                    "description": "Days ahead to check for renewals"
                },
                "notification_type": {
                    "type": "string",
                    "enum": ["renewal_warning", "paycheck_available", "expiry_reminder", "payment_due"],
                    "description": "Type of notification to send"
                },
                "preferences": {
                    "type": "object",
                    "description": "User notification preferences"
                },
                "message": {
                    "type": "string",
                    "description": "Custom message for notification"
                }
            },
            "required": ["operation"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute subscription notification operations"""
        operation = kwargs.get("operation")
        
        try:
            if operation == "check_renewal_warnings":
                return await self._check_renewal_warnings(kwargs.get("days_ahead", 7))
            elif operation == "send_renewal_warning":
                return await self._send_renewal_warning(
                    kwargs.get("subscription_id"),
                    kwargs.get("notification_type", "renewal_warning")
                )
            elif operation == "get_user_notification_preferences":
                return await self._get_user_notification_preferences(kwargs.get("whatsapp_number"))
            elif operation == "update_notification_preferences":
                return await self._update_notification_preferences(
                    kwargs.get("whatsapp_number"),
                    kwargs.get("preferences")
                )
            elif operation == "get_notification_history":
                return await self._get_notification_history(kwargs.get("whatsapp_number"))
            elif operation == "schedule_renewal_reminder":
                return await self._schedule_renewal_reminder(kwargs.get("subscription_id"))
            elif operation == "check_expiring_subscriptions":
                return await self._check_expiring_subscriptions(kwargs.get("days_ahead", 7))
            elif operation == "get_upcoming_renewals":
                return await self._get_upcoming_renewals(kwargs.get("whatsapp_number"))
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Subscription notification operation failed: {e}")
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    async def _check_renewal_warnings(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Check for subscriptions that need renewal warnings"""
        if self.mock_mode:
            return self._get_mock_renewal_warnings(days_ahead)
        
        try:
            now = datetime.now()
            future_date = now + timedelta(days=days_ahead)
            
            # Get subscriptions expiring in the specified timeframe
            response = self.supabase.table("user_subscriptions").select("""
                id,
                end_date,
                auto_renewal,
                last_renewal_reminder,
                users (
                    whatsapp_number,
                    full_name,
                    preferred_language
                ),
                operators (
                    name,
                    display_name,
                    logo_url,
                    brand_color
                ),
                subscription_plans (
                    name,
                    description,
                    price_cents,
                    billing_cycle,
                    data_limit_gb,
                    features
                )
            """).eq("status", "active").gte("end_date", now.isoformat()).lte("end_date", future_date.isoformat()).execute()
            
            # Filter subscriptions that need warnings
            warnings_needed = []
            for subscription in response.data:
                end_date = datetime.fromisoformat(subscription["end_date"].replace('Z', '+00:00'))
                days_until_expiry = (end_date - now).days
                
                # Determine if warning is needed based on timing and last reminder
                last_reminder = subscription.get("last_renewal_reminder")
                needs_warning = False
                warning_type = None
                
                if days_until_expiry <= 1 and (not last_reminder or 
                    datetime.fromisoformat(last_reminder.replace('Z', '+00:00')) < now - timedelta(hours=12)):
                    needs_warning = True
                    warning_type = "urgent"
                elif days_until_expiry <= 3 and (not last_reminder or 
                    datetime.fromisoformat(last_reminder.replace('Z', '+00:00')) < now - timedelta(days=1)):
                    needs_warning = True
                    warning_type = "high"
                elif days_until_expiry <= 7 and (not last_reminder or 
                    datetime.fromisoformat(last_reminder.replace('Z', '+00:00')) < now - timedelta(days=2)):
                    needs_warning = True
                    warning_type = "normal"
                
                if needs_warning:
                    subscription["days_until_expiry"] = days_until_expiry
                    subscription["warning_type"] = warning_type
                    subscription["urgency_score"] = self._calculate_urgency_score(days_until_expiry, subscription["auto_renewal"])
                    warnings_needed.append(subscription)
            
            # Sort by urgency
            warnings_needed.sort(key=lambda x: x["urgency_score"], reverse=True)
            
            return {
                "success": True,
                "renewal_warnings": warnings_needed,
                "count": len(warnings_needed),
                "days_ahead": days_ahead,
                "timestamp": now.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}


    async def _send_renewal_warning(self, subscription_id: str, notification_type: str = "renewal_warning") -> Dict[str, Any]:
        """Send a renewal warning notification"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_renewal_warning_message(subscription_id, notification_type)
        
        try:
            # Get subscription details
            subscription_response = self.supabase.table("user_subscriptions").select("""
                id,
                end_date,
                auto_renewal,
                users (
                    whatsapp_number,
                    full_name,
                    preferred_language
                ),
                operators (
                    name,
                    display_name,
                    logo_url,
                    brand_color
                ),
                subscription_plans (
                    name,
                    description,
                    price_cents,
                    billing_cycle,
                    data_limit_gb,
                    features
                )
            """).eq("id", subscription_id).execute()
            
            if not subscription_response.data:
                return {"success": False, "error": "Subscription not found"}
            
            subscription = subscription_response.data[0]
            
            # Calculate time until expiry
            end_date = datetime.fromisoformat(subscription["end_date"].replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            days_until_expiry = (end_date - now).days
            
            # Generate warning message
            warning_message = self._generate_renewal_warning_message(
                subscription,
                days_until_expiry,
                notification_type
            )
            
            # Update last renewal reminder timestamp
            self.supabase.table("user_subscriptions").update({
                "last_renewal_reminder": now.isoformat()
            }).eq("id", subscription_id).execute()
            
            return {
                "success": True,
                "subscription": subscription,
                "warning_message": warning_message,
                "days_until_expiry": days_until_expiry,
                "notification_type": notification_type,
                "whatsapp_number": subscription["users"]["whatsapp_number"],
                "sent_at": now.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}


    async def _get_user_notification_preferences(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get user's notification preferences"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_notification_preferences(whatsapp_number)
        
        try:
            # Get user preferences from database
            user_response = self.supabase.table("users").select("""
                id,
                whatsapp_number,
                full_name,
                notification_preferences
            """).eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user = user_response.data[0]
            preferences = user.get("notification_preferences", {})
            
            # Set default preferences if none exist
            if not preferences:
                preferences = self._get_default_notification_preferences()
            
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "preferences": preferences,
                "user_name": user.get("full_name")
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _update_notification_preferences(self, whatsapp_number: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's notification preferences"""
        if not whatsapp_number or not preferences:
            return {"success": False, "error": "WhatsApp number and preferences are required"}
        
        if self.mock_mode:
            return self._get_mock_update_preferences(whatsapp_number, preferences)
        
        try:
            # Update user preferences in database
            result = self.supabase.table("users").update({
                "notification_preferences": preferences,
                "updated_at": datetime.now().isoformat()
            }).eq("whatsapp_number", whatsapp_number).execute()
            
            if not result.data:
                return {"success": False, "error": "User not found"}
            
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "updated_preferences": preferences,
                "updated_at": datetime.now().isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_notification_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get user's notification history"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_notification_history(whatsapp_number)
        
        try:
            # Get user ID
            user_response = self.supabase.table("users").select("id").eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user_id = user_response.data[0]["id"]
            
            # Get notification history from renewal_reminders table
            history_response = self.supabase.table("renewal_reminders").select("""
                id,
                reminder_type,
                scheduled_for,
                sent_at,
                user_response,
                response_received_at,
                user_subscriptions (
                    operators (display_name),
                    subscription_plans (name)
                )
            """).eq("user_subscriptions.user_id", user_id).order("created_at", desc=True).limit(20).execute()
            
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "notification_history": history_response.data,
                "count": len(history_response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _schedule_renewal_reminder(self, subscription_id: str) -> Dict[str, Any]:
        """Schedule a renewal reminder for a subscription"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_schedule_reminder(subscription_id)
        
        try:
            # Get subscription details
            subscription_response = self.supabase.table("user_subscriptions").select("end_date").eq("id", subscription_id).execute()
            
            if not subscription_response.data:
                return {"success": False, "error": "Subscription not found"}
            
            end_date = datetime.fromisoformat(subscription_response.data[0]["end_date"].replace('Z', '+00:00'))
            
            # Schedule reminders at different intervals
            reminders = []
            reminder_schedule = {
                "7_day": end_date - timedelta(days=7),
                "3_day": end_date - timedelta(days=3),
                "1_day": end_date - timedelta(days=1),
                "expiry": end_date
            }
            
            for reminder_type, scheduled_for in reminder_schedule.items():
                # Check if reminder already exists
                existing = self.supabase.table("renewal_reminders").select("id").eq("subscription_id", subscription_id).eq("reminder_type", reminder_type).execute()
                
                if not existing.data:  # No existing reminder
                    reminder_data = {
                        "subscription_id": subscription_id,
                        "reminder_type": reminder_type,
                        "scheduled_for": scheduled_for.isoformat(),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    result = self.supabase.table("renewal_reminders").insert(reminder_data).execute()
                    if result.data:
                        reminders.append(result.data[0])
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "scheduled_reminders": reminders,
                "count": len(reminders)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _check_expiring_subscriptions(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Check for subscriptions expiring within specified days"""
        return await self._check_renewal_warnings(days_ahead)

    async def _get_upcoming_renewals(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get upcoming renewals for a user"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_upcoming_renewals(whatsapp_number)
        
        try:
            # Get user ID
            user_response = self.supabase.table("users").select("id").eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user_id = user_response.data[0]["id"]
            
            # Get upcoming renewals
            now = datetime.now()
            future_date = now + timedelta(days=30)  # Next 30 days
            
            renewals_response = self.supabase.table("user_subscriptions").select("""
                id,
                end_date,
                auto_renewal,
                operators (display_name),
                subscription_plans (name, price_cents, billing_cycle)
            """).eq("user_id", user_id).eq("status", "active").gte("end_date", now.isoformat()).lte("end_date", future_date.isoformat()).order("end_date").execute()
            
            upcoming_renewals = []
            for renewal in renewals_response.data:
                end_date = datetime.fromisoformat(renewal["end_date"].replace('Z', '+00:00'))
                days_until_expiry = (end_date - now).days
                
                upcoming_renewals.append({
                    "subscription_id": renewal["id"],
                    "operator": renewal["operators"]["display_name"],
                    "plan_name": renewal["subscription_plans"]["name"],
                    "price_cents": renewal["subscription_plans"]["price_cents"],
                    "price_brl": renewal["subscription_plans"]["price_cents"] / 100,
                    "billing_cycle": renewal["subscription_plans"]["billing_cycle"],
                    "end_date": renewal["end_date"],
                    "days_until_expiry": days_until_expiry,
                    "auto_renewal": renewal["auto_renewal"]
                })
            
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "upcoming_renewals": upcoming_renewals,
                "count": len(upcoming_renewals),
                "total_cost_cents": sum(r["price_cents"] for r in upcoming_renewals),
                "total_cost_brl": sum(r["price_brl"] for r in upcoming_renewals)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    def _calculate_urgency_score(self, days_until_expiry: int, auto_renewal: bool) -> int:
        """Calculate urgency score for renewal warning"""
        base_score = max(0, 10 - days_until_expiry)  # Higher score for closer expiry
        
        if not auto_renewal:
            base_score += 5  # Higher urgency if auto-renewal is disabled
        
        if days_until_expiry <= 0:
            base_score += 10  # Maximum urgency for expired subscriptions
        
        return min(20, base_score)  # Cap at 20


    def _generate_renewal_warning_message(self, subscription: Dict[str, Any], days_until_expiry: int, notification_type: str) -> str:
        """Generate renewal warning message"""
        user_name = subscription["users"]["full_name"] or "Cliente"
        operator = subscription["operators"]["display_name"]
        plan_name = subscription["subscription_plans"]["name"]
        price_brl = subscription["subscription_plans"]["price_cents"] / 100
        
        if days_until_expiry <= 0:
            message = f"🚨 Olá {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} EXPIROU!\n"
            message += f"💰 Renovar agora por R$ {price_brl:.2f}\n\n"
            message += "⚠️ Seus serviços podem estar suspensos.\n"
            message += "🔄 Digite 'RENOVAR' para renovar imediatamente."
        elif days_until_expiry <= 1:
            message = f"⚠️ Olá {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} expira em {days_until_expiry} dia!\n"
            message += f"💰 Renovação: R$ {price_brl:.2f}\n\n"
            message += "🚨 URGENTE: Renove hoje para evitar interrupção.\n"
            message += "🔄 Digite 'RENOVAR' para renovar agora."
        elif days_until_expiry <= 3:
            message = f"📱 Oi {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} expira em {days_until_expiry} dias.\n"
            message += f"💰 Renovação: R$ {price_brl:.2f}\n\n"
            message += "🔄 Opções disponíveis:\n"
            message += "• 'RENOVAR' - Renovar plano atual\n"
            message += "• 'UPGRADE' - Ver planos melhores\n"
            message += "• 'ECONOMIZAR' - Ver planos mais baratos"
        else:
            message = f"📱 Olá {user_name}!\n\n"
            message += f"Lembrete: Seu plano {operator} {plan_name} expira em {days_until_expiry} dias.\n"
            message += f"💰 Valor da renovação: R$ {price_brl:.2f}\n\n"
            message += "🔄 Opções disponíveis:\n"
            message += "• 'RENOVAR' - Manter o plano atual\n"
            message += "• 'UPGRADE' - Ver planos melhores\n"
            message += "• 'ECONOMIZAR' - Ver planos mais baratos\n"
            message += "• 'DEPOIS' - Lembrar mais tarde"
        
        return message


    def _get_default_notification_preferences(self) -> Dict[str, Any]:
        """Get default notification preferences"""
        return {
            "renewal_warnings": {
                "enabled": True,
                "days_ahead": [7, 3, 1],
                "time_of_day": "09:00",
                "language": "pt-BR"
            },
            "payment_reminders": {
                "enabled": True,
                "overdue_reminders": True,
                "frequency": "daily"
            },
            "general_preferences": {
                "quiet_hours": {
                    "enabled": True,
                    "start": "22:00",
                    "end": "08:00"
                },
                "weekend_notifications": True
            }
        }

    # Mock data methods for testing
    def _get_mock_renewal_warnings(self, days_ahead: int) -> Dict[str, Any]:
        """Mock renewal warnings data"""
        return {
            "success": True,
            "renewal_warnings": [
                {
                    "id": "sub-001",
                    "end_date": "2025-01-29T00:00:00Z",
                    "days_until_expiry": 2,
                    "warning_type": "high",
                    "urgency_score": 8,
                    "auto_renewal": True,
                    "users": {
                        "whatsapp_number": "+5511999887766",
                        "full_name": "João Silva Santos",
                        "preferred_language": "pt-BR"
                    },
                    "operators": {
                        "name": "VIVO",
                        "display_name": "Vivo",
                        "brand_color": "#8B2797"
                    },
                    "subscription_plans": {
                        "name": "Vivo Premium 10GB",
                        "price_cents": 4990,
                        "billing_cycle": "monthly"
                    }
                }
            ],
            "count": 1,
            "days_ahead": days_ahead,
            "timestamp": datetime.now().isoformat()
        }


    def _get_mock_renewal_warning_message(self, subscription_id: str, notification_type: str) -> Dict[str, Any]:
        """Mock renewal warning message"""
        return {
            "success": True,
            "subscription": {
                "id": subscription_id,
                "users": {"whatsapp_number": "+5511999887766", "full_name": "João Silva"},
                "operators": {"display_name": "Vivo"},
                "subscription_plans": {"name": "Vivo Premium 10GB", "price_cents": 4990}
            },
            "warning_message": "📱 Oi João Silva!\n\nSeu plano Vivo Premium 10GB expira em 2 dias.\n💰 Renovação: R$ 49.90\n\n🔄 Opções disponíveis:\n• 'RENOVAR' - Renovar plano atual\n• 'UPGRADE' - Ver planos melhores\n• 'ECONOMIZAR' - Ver planos mais baratos",
            "days_until_expiry": 2,
            "notification_type": notification_type,
            "whatsapp_number": "+5511999887766",
            "sent_at": datetime.now().isoformat()
        }

    def _get_mock_notification_preferences(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock notification preferences"""
        return {
            "success": True,
            "whatsapp_number": whatsapp_number,
            "preferences": self._get_default_notification_preferences(),
            "user_name": "João Silva"
        }

    def _get_mock_update_preferences(self, whatsapp_number: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Mock update preferences response"""
        return {
            "success": True,
            "whatsapp_number": whatsapp_number,
            "updated_preferences": preferences,
            "updated_at": datetime.now().isoformat()
        }

    def _get_mock_notification_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock notification history"""
        return {
            "success": True,
            "whatsapp_number": whatsapp_number,
            "notification_history": [
                {
                    "id": "reminder-001",
                    "reminder_type": "7_day",
                    "sent_at": "2025-01-20T10:00:00Z",
                    "user_response": "deferred",
                    "user_subscriptions": {
                        "operators": {"display_name": "Vivo"},
                        "subscription_plans": {"name": "Vivo Premium 10GB"}
                    }
                }
            ],
            "count": 1
        }

    def _get_mock_schedule_reminder(self, subscription_id: str) -> Dict[str, Any]:
        """Mock schedule reminder response"""
        return {
            "success": True,
            "subscription_id": subscription_id,
            "scheduled_reminders": [
                {
                    "id": "reminder-001",
                    "subscription_id": subscription_id,
                    "reminder_type": "7_day",
                    "scheduled_for": (datetime.now() + timedelta(days=5)).isoformat()
                }
            ],
            "count": 1
        }

    def _get_mock_upcoming_renewals(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock upcoming renewals"""
        return {
            "success": True,
            "whatsapp_number": whatsapp_number,
            "upcoming_renewals": [
                {
                    "subscription_id": "sub-001",
                    "operator": "Vivo",
                    "plan_name": "Vivo Premium 10GB",
                    "price_cents": 4990,
                    "price_brl": 49.90,
                    "billing_cycle": "monthly",
                    "end_date": "2025-01-29T00:00:00Z",
                    "days_until_expiry": 2,
                    "auto_renewal": True
                }
            ],
            "count": 1,
            "total_cost_cents": 4990,
            "total_cost_brl": 49.90
        }


# Initialize tool instance
_subscription_notifications_tool = SubscriptionNotificationsTool()


def subscription_notifications_tool(**kwargs):
    """Subscription notifications tool function."""
    return _subscription_notifications_tool.execute(**kwargs)
