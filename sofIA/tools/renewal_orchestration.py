"""
Renewal Orchestration Tool for sofIA Agent
Handles proactive renewal monitoring, reminder scheduling, and renewal payment processing
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from supabase import create_client, Client
from postgrest import APIError

logger = logging.getLogger(__name__)


class RenewalOrchestrationTool:
    """Tool for proactive subscription renewal management and payment processing"""
    
    def __init__(self):
        self.name = "renewal_orchestration"
        self.description = "Proactive renewal monitoring, reminder scheduling, and renewal payment processing"
        
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
                        "check_renewal_queue",
                        "schedule_reminder",
                        "send_renewal_reminder",
                        "process_renewal_response",
                        "calculate_renewal_cost",
                        "get_renewal_history",
                        "get_pending_reminders",
                        "mark_reminder_sent",
                        "update_reminder_response"
                    ],
                    "description": "Renewal operation to perform"
                },
                "subscription_id": {
                    "type": "string",
                    "description": "Subscription ID for renewal operations"
                },
                "whatsapp_number": {
                    "type": "string",
                    "description": "WhatsApp number for user-specific operations"
                },
                "reminder_type": {
                    "type": "string",
                    "enum": ["7_day", "3_day", "1_day", "expiry", "overdue"],
                    "description": "Type of renewal reminder"
                },
                "user_response": {
                    "type": "string",
                    "enum": ["renewed", "declined", "ignored", "deferred"],
                    "description": "User response to renewal reminder"
                },
                "message_id": {
                    "type": "string",
                    "description": "WhatsApp message ID for tracking"
                },
                "reminder_id": {
                    "type": "string",
                    "description": "Reminder ID for updates"
                },
                "days_ahead": {
                    "type": "integer",
                    "default": 7,
                    "description": "Days ahead to check for renewals"
                }
            },
            "required": ["operation"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute renewal orchestration operations"""
        operation = kwargs.get("operation")
        
        try:
            if operation == "check_renewal_queue":
                return await self._check_renewal_queue(kwargs.get("days_ahead", 7))
            elif operation == "schedule_reminder":
                return await self._schedule_reminder(
                    kwargs.get("subscription_id"),
                    kwargs.get("reminder_type")
                )
            elif operation == "send_renewal_reminder":
                return await self._send_renewal_reminder(kwargs.get("subscription_id"))
            elif operation == "process_renewal_response":
                return await self._process_renewal_response(
                    kwargs.get("reminder_id"),
                    kwargs.get("user_response")
                )
            elif operation == "calculate_renewal_cost":
                return await self._calculate_renewal_cost(kwargs.get("subscription_id"))
            elif operation == "get_renewal_history":
                return await self._get_renewal_history(kwargs.get("whatsapp_number"))
            elif operation == "get_pending_reminders":
                return await self._get_pending_reminders()
            elif operation == "mark_reminder_sent":
                return await self._mark_reminder_sent(
                    kwargs.get("reminder_id"),
                    kwargs.get("message_id")
                )
            elif operation == "update_reminder_response":
                return await self._update_reminder_response(
                    kwargs.get("reminder_id"),
                    kwargs.get("user_response")
                )
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            logger.error(f"Renewal orchestration operation failed: {e}")
            return {"success": False, "error": f"Operation failed: {str(e)}"}

    async def _check_renewal_queue(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Check for subscriptions that need renewal reminders"""
        if self.mock_mode:
            return self._get_mock_renewal_queue(days_ahead)
        
        try:
            # Get subscriptions expiring in the specified timeframe
            now = datetime.now()
            future_date = now + timedelta(days=days_ahead)
            
            # Check for subscriptions that need 7-day reminders
            seven_day_target = now + timedelta(days=7)
            seven_day_start = seven_day_target - timedelta(hours=1)
            seven_day_end = seven_day_target + timedelta(hours=1)
            
            # Check for subscriptions that need 3-day reminders
            three_day_target = now + timedelta(days=3)
            three_day_start = three_day_target - timedelta(hours=1)
            three_day_end = three_day_target + timedelta(hours=1)
            
            # Check for subscriptions that need 1-day reminders
            one_day_target = now + timedelta(days=1)
            one_day_start = one_day_target - timedelta(hours=1)
            one_day_end = one_day_target + timedelta(hours=1)
            
            # Check for expired subscriptions
            expired_subscriptions = self.supabase.table("user_subscriptions").select("""
                id,
                end_date,
                auto_renewal,
                users (whatsapp_number, full_name),
                operators (name, display_name),
                subscription_plans (name, price_cents)
            """).eq("status", "active").lt("end_date", now.isoformat()).execute()
            
            renewal_queue = {
                "seven_day_reminders": [],
                "three_day_reminders": [],
                "one_day_reminders": [],
                "expired_subscriptions": expired_subscriptions.data,
                "total_pending": 0
            }
            
            # Check each timeframe
            for reminder_type, start_time, end_time in [
                ("7_day", seven_day_start, seven_day_end),
                ("3_day", three_day_start, three_day_end),
                ("1_day", one_day_start, one_day_end)
            ]:
                subscriptions = self.supabase.table("user_subscriptions").select("""
                    id,
                    end_date,
                    auto_renewal,
                    users (whatsapp_number, full_name),
                    operators (name, display_name),
                    subscription_plans (name, price_cents, billing_cycle)
                """).eq("status", "active").gte("end_date", start_time.isoformat()).lte("end_date", end_time.isoformat()).execute()
                
                # Filter out subscriptions that already have reminders scheduled
                for subscription in subscriptions.data:
                    existing_reminder = self.supabase.table("renewal_reminders").select("id").eq("subscription_id", subscription["id"]).eq("reminder_type", reminder_type).execute()
                    
                    if not existing_reminder.data:  # No reminder exists yet
                        key = f"{reminder_type.replace('_', '_day_')}_reminders"
                        if key in renewal_queue:
                            renewal_queue[key].append(subscription)
            
            renewal_queue["total_pending"] = (
                len(renewal_queue["seven_day_reminders"]) +
                len(renewal_queue["three_day_reminders"]) +
                len(renewal_queue["one_day_reminders"]) +
                len(renewal_queue["expired_subscriptions"])
            )
            
            return {
                "success": True,
                "renewal_queue": renewal_queue,
                "timestamp": now.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _schedule_reminder(self, subscription_id: str, reminder_type: str) -> Dict[str, Any]:
        """Schedule a renewal reminder for a subscription"""
        if not subscription_id or not reminder_type:
            return {"success": False, "error": "Subscription ID and reminder type are required"}
        
        if self.mock_mode:
            return self._get_mock_schedule_reminder(subscription_id, reminder_type)
        
        try:
            # Get subscription details
            subscription = self.supabase.table("user_subscriptions").select("end_date").eq("id", subscription_id).execute()
            
            if not subscription.data:
                return {"success": False, "error": "Subscription not found"}
            
            end_date = datetime.fromisoformat(subscription.data[0]["end_date"].replace('Z', '+00:00'))
            
            # Calculate when to send the reminder
            reminder_schedule = {
                "7_day": end_date - timedelta(days=7),
                "3_day": end_date - timedelta(days=3),
                "1_day": end_date - timedelta(days=1),
                "expiry": end_date,
                "overdue": end_date + timedelta(days=1)
            }
            
            scheduled_for = reminder_schedule.get(reminder_type)
            if not scheduled_for:
                return {"success": False, "error": f"Invalid reminder type: {reminder_type}"}
            
            # Create reminder record
            reminder_data = {
                "subscription_id": subscription_id,
                "reminder_type": reminder_type,
                "scheduled_for": scheduled_for.isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("renewal_reminders").insert(reminder_data).execute()
            
            return {
                "success": True,
                "reminder": result.data[0] if result.data else reminder_data,
                "scheduled_for": scheduled_for.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _send_renewal_reminder(self, subscription_id: str) -> Dict[str, Any]:
        """Prepare renewal reminder message for a subscription"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_renewal_reminder(subscription_id)
        
        try:
            # Get subscription with all details for the reminder
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
            time_until_expiry = end_date - now
            
            # Determine urgency level
            days_until_expiry = time_until_expiry.days
            if days_until_expiry < 0:
                urgency = "expired"
            elif days_until_expiry <= 1:
                urgency = "urgent"
            elif days_until_expiry <= 3:
                urgency = "high"
            else:
                urgency = "normal"
            
            # Create reminder message
            plan_name = subscription["subscription_plans"]["name"]
            operator_name = subscription["operators"]["display_name"]
            price_brl = subscription["subscription_plans"]["price_cents"] / 100
            
            message = self._generate_renewal_message(
                subscription["users"]["full_name"],
                operator_name,
                plan_name,
                price_brl,
                days_until_expiry,
                urgency
            )
            
            return {
                "success": True,
                "subscription": subscription,
                "reminder_message": message,
                "urgency": urgency,
                "days_until_expiry": days_until_expiry,
                "whatsapp_number": subscription["users"]["whatsapp_number"],
                "auto_renewal_enabled": subscription["auto_renewal"]
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _process_renewal_response(self, reminder_id: str, user_response: str) -> Dict[str, Any]:
        """Process user response to a renewal reminder"""
        if not reminder_id or not user_response:
            return {"success": False, "error": "Reminder ID and user response are required"}
        
        if self.mock_mode:
            return self._get_mock_renewal_response(reminder_id, user_response)
        
        try:
            # Update reminder with user response
            update_data = {
                "user_response": user_response,
                "response_received_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("renewal_reminders").update(update_data).eq("id", reminder_id).execute()
            
            if not result.data:
                return {"success": False, "error": "Reminder not found"}
            
            # Get subscription details for further processing
            reminder = result.data[0]
            subscription_response = self.supabase.table("user_subscriptions").select("""
                id,
                users (whatsapp_number, full_name),
                operators (display_name),
                subscription_plans (name, price_cents)
            """).eq("id", reminder["subscription_id"]).execute()
            
            subscription = subscription_response.data[0] if subscription_response.data else None
            
            # Determine next action based on response
            next_action = self._determine_next_action(user_response)
            
            return {
                "success": True,
                "reminder": reminder,
                "subscription": subscription,
                "user_response": user_response,
                "next_action": next_action,
                "processed_at": datetime.now().isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _calculate_renewal_cost(self, subscription_id: str) -> Dict[str, Any]:
        """Calculate the cost for renewing a subscription"""
        if not subscription_id:
            return {"success": False, "error": "Subscription ID is required"}
        
        if self.mock_mode:
            return self._get_mock_renewal_cost(subscription_id)
        
        try:
            subscription_response = self.supabase.table("user_subscriptions").select("""
                id,
                subscription_plans (
                    name,
                    price_cents,
                    billing_cycle
                ),
                operators (display_name)
            """).eq("id", subscription_id).execute()
            
            if not subscription_response.data:
                return {"success": False, "error": "Subscription not found"}
            
            subscription = subscription_response.data[0]
            plan = subscription["subscription_plans"]
            
            return {
                "success": True,
                "subscription_id": subscription_id,
                "plan_name": plan["name"],
                "operator": subscription["operators"]["display_name"],
                "renewal_cost_cents": plan["price_cents"],
                "renewal_cost_brl": plan["price_cents"] / 100,
                "billing_cycle": plan["billing_cycle"],
                "currency": "BRL"
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_renewal_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Get renewal history for a user"""
        if not whatsapp_number:
            return {"success": False, "error": "WhatsApp number is required"}
        
        if self.mock_mode:
            return self._get_mock_renewal_history(whatsapp_number)
        
        try:
            # Get user ID
            user_response = self.supabase.table("users").select("id").eq("whatsapp_number", whatsapp_number).execute()
            
            if not user_response.data:
                return {"success": False, "error": "User not found"}
            
            user_id = user_response.data[0]["id"]
            
            # Get renewal history
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
            """).eq("user_subscriptions.user_id", user_id).order("created_at", desc=True).limit(10).execute()
            
            return {
                "success": True,
                "renewal_history": history_response.data,
                "count": len(history_response.data)
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _get_pending_reminders(self) -> Dict[str, Any]:
        """Get all pending reminders that need to be sent"""
        if self.mock_mode:
            return self._get_mock_pending_reminders()
        
        try:
            now = datetime.now()
            
            pending_response = self.supabase.table("renewal_reminders").select("""
                id,
                subscription_id,
                reminder_type,
                scheduled_for,
                user_subscriptions (
                    users (whatsapp_number, full_name),
                    operators (display_name),
                    subscription_plans (name, price_cents)
                )
            """).is_("sent_at", "null").lte("scheduled_for", now.isoformat()).execute()
            
            return {
                "success": True,
                "pending_reminders": pending_response.data,
                "count": len(pending_response.data),
                "timestamp": now.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _mark_reminder_sent(self, reminder_id: str, message_id: str) -> Dict[str, Any]:
        """Mark a reminder as sent with WhatsApp message ID"""
        if not reminder_id:
            return {"success": False, "error": "Reminder ID is required"}
        
        try:
            update_data = {
                "sent_at": datetime.now().isoformat(),
                "message_id": message_id,
                "updated_at": datetime.now().isoformat()
            }
            
            if not self.mock_mode:
                result = self.supabase.table("renewal_reminders").update(update_data).eq("id", reminder_id).execute()
                
                if not result.data:
                    return {"success": False, "error": "Reminder not found"}
            
            return {
                "success": True,
                "reminder_id": reminder_id,
                "message_id": message_id,
                "sent_at": update_data["sent_at"]
            }
            
        except APIError as e:
            logger.error(f"Supabase API error: {e}")
            return {"success": False, "error": f"Database error: {str(e)}"}

    async def _update_reminder_response(self, reminder_id: str, user_response: str) -> Dict[str, Any]:
        """Update reminder with user response"""
        return await self._process_renewal_response(reminder_id, user_response)

    def _generate_renewal_message(self, user_name: str, operator: str, plan_name: str, price_brl: float, days_until_expiry: int, urgency: str) -> str:
        """Generate a personalized renewal reminder message"""
        
        if urgency == "expired":
            message = f"🚨 Olá {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} expirou!\n"
            message += f"💰 Renovar agora por R$ {price_brl:.2f}\n\n"
            message += "🔄 Gostaria de renovar seu plano?\n\n"
            message += "Digite 'SIM' para renovar ou 'INFO' para ver outras opções."
        elif urgency == "urgent":
            message = f"⚠️ Olá {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} expira em {days_until_expiry} dia(s)!\n"
            message += f"💰 Renove por R$ {price_brl:.2f}\n\n"
            message += "🔄 Quer renovar agora?\n\n"
            message += "Digite 'SIM' para renovar ou 'MUDAR' para ver outros planos."
        elif urgency == "high":
            message = f"📱 Oi {user_name}!\n\n"
            message += f"Seu plano {operator} {plan_name} expira em {days_until_expiry} dias.\n"
            message += f"💰 Renovação: R$ {price_brl:.2f}\n\n"
            message += "🔄 Gostaria de renovar?\n\n"
            message += "Digite 'SIM' para renovar, 'UPGRADE' para melhorar o plano ou 'DEPOIS' para ser lembrado novamente."
        else:  # normal
            message = f"📱 Olá {user_name}!\n\n"
            message += f"Lembrete: Seu plano {operator} {plan_name} expira em {days_until_expiry} dias.\n"
            message += f"💰 Valor da renovação: R$ {price_brl:.2f}\n\n"
            message += "Opções disponíveis:\n"
            message += "🔄 'RENOVAR' - Manter o plano atual\n"
            message += "⬆️ 'UPGRADE' - Ver planos melhores\n"
            message += "⬇️ 'ECONOMIZAR' - Ver planos mais baratos\n"
            message += "⏰ 'DEPOIS' - Lembrar mais tarde"
        
        return message

    def _determine_next_action(self, user_response: str) -> str:
        """Determine the next action based on user response"""
        response_actions = {
            "renewed": "payment_processing",
            "declined": "plan_alternatives",
            "ignored": "follow_up_reminder",
            "deferred": "schedule_follow_up"
        }
        return response_actions.get(user_response, "manual_review")

    # Mock data methods for testing
    def _get_mock_renewal_queue(self, days_ahead: int) -> Dict[str, Any]:
        """Mock renewal queue data"""
        return {
            "success": True,
            "renewal_queue": {
                "seven_day_reminders": [
                    {
                        "id": "sub-002",
                        "end_date": "2025-02-05T00:00:00Z",
                        "users": {"whatsapp_number": "+5511888776655", "full_name": "Maria Oliveira Costa"},
                        "operators": {"display_name": "Claro"},
                        "subscription_plans": {"name": "Claro Smart 8GB", "price_cents": 3990}
                    }
                ],
                "three_day_reminders": [
                    {
                        "id": "sub-001",
                        "end_date": "2025-01-31T00:00:00Z",
                        "users": {"whatsapp_number": "+5511999887766", "full_name": "João Silva Santos"},
                        "operators": {"display_name": "Vivo"},
                        "subscription_plans": {"name": "Vivo Premium 10GB", "price_cents": 4990}
                    }
                ],
                "one_day_reminders": [],
                "expired_subscriptions": [],
                "total_pending": 2
            },
            "timestamp": datetime.now().isoformat()
        }

    def _get_mock_schedule_reminder(self, subscription_id: str, reminder_type: str) -> Dict[str, Any]:
        """Mock schedule reminder response"""
        return {
            "success": True,
            "reminder": {
                "id": f"reminder-{subscription_id}-{reminder_type}",
                "subscription_id": subscription_id,
                "reminder_type": reminder_type,
                "scheduled_for": (datetime.now() + timedelta(days=1)).isoformat()
            },
            "scheduled_for": (datetime.now() + timedelta(days=1)).isoformat()
        }

    def _get_mock_renewal_reminder(self, subscription_id: str) -> Dict[str, Any]:
        """Mock renewal reminder data"""
        return {
            "success": True,
            "subscription": {
                "id": subscription_id,
                "users": {"whatsapp_number": "+5511999887766", "full_name": "João Silva"},
                "operators": {"display_name": "Vivo"},
                "subscription_plans": {"name": "Vivo Premium 10GB", "price_cents": 4990}
            },
            "reminder_message": "📱 Olá João Silva!\n\nSeu plano Vivo Premium 10GB expira em 3 dias.\n💰 Renovação: R$ 49.90\n\n🔄 Gostaria de renovar?",
            "urgency": "high",
            "days_until_expiry": 3,
            "whatsapp_number": "+5511999887766",
            "auto_renewal_enabled": True
        }

    def _get_mock_renewal_response(self, reminder_id: str, user_response: str) -> Dict[str, Any]:
        """Mock renewal response processing"""
        return {
            "success": True,
            "reminder": {"id": reminder_id, "user_response": user_response},
            "subscription": {"id": "sub-001"},
            "user_response": user_response,
            "next_action": self._determine_next_action(user_response),
            "processed_at": datetime.now().isoformat()
        }

    def _get_mock_renewal_cost(self, subscription_id: str) -> Dict[str, Any]:
        """Mock renewal cost calculation"""
        return {
            "success": True,
            "subscription_id": subscription_id,
            "plan_name": "Vivo Premium 10GB",
            "operator": "Vivo",
            "renewal_cost_cents": 4990,
            "renewal_cost_brl": 49.90,
            "billing_cycle": "monthly",
            "currency": "BRL"
        }

    def _get_mock_renewal_history(self, whatsapp_number: str) -> Dict[str, Any]:
        """Mock renewal history"""
        return {
            "success": True,
            "renewal_history": [
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

    def _get_mock_pending_reminders(self) -> Dict[str, Any]:
        """Mock pending reminders"""
        return {
            "success": True,
            "pending_reminders": [
                {
                    "id": "reminder-pending-001",
                    "subscription_id": "sub-001",
                    "reminder_type": "3_day",
                    "scheduled_for": datetime.now().isoformat(),
                    "user_subscriptions": {
                        "users": {"whatsapp_number": "+5511999887766", "full_name": "João Silva"},
                        "operators": {"display_name": "Vivo"},
                        "subscription_plans": {"name": "Vivo Premium 10GB", "price_cents": 4990}
                    }
                }
            ],
            "count": 1,
            "timestamp": datetime.now().isoformat()
        }


# Tool instance for agent integration
renewal_orchestration_tool = RenewalOrchestrationTool()
