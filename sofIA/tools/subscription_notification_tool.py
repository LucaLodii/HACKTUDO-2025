"""
Subscription Notification Tool for sofIA Agent
Wrapper for the subscription notifications functionality
"""

from typing import Dict, Any
from .subscription_notifications import subscription_notifications_tool


class SubscriptionNotificationTool:
    """Tool for subscription notifications and renewal warnings"""
    
    def __init__(self):
        self.name = "subscription_notification_tool"
        self.description = "Proactive subscription renewal warnings and paycheck availability notifications"
        
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "check_renewal_warnings",
                        "check_paycheck_availability", 
                        "send_renewal_warning",
                        "send_paycheck_notification",
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
        return await subscription_notifications_tool(**kwargs)


# Initialize tool instance
_subscription_notification_tool = SubscriptionNotificationTool()


def subscription_notification_tool(**kwargs):
    """Subscription notification tool function."""
    return _subscription_notification_tool.execute(**kwargs)
