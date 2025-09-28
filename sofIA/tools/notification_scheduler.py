"""
Notification Scheduler Service for sofIA
Background service for proactive subscription notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os

from .subscription_notifications import subscription_notifications_tool
from .whatsapp.whatsapp_tool import whatsapp_tool

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """Background service for scheduling and sending subscription notifications"""
    
    def __init__(self):
        self.name = "notification_scheduler"
        self.description = "Background service for proactive subscription notifications"
        self.is_running = False
        self.check_interval = 300  # 5 minutes
        self.notification_tool = subscription_notifications_tool
        self.whatsapp_tool = whatsapp_tool
        
    async def start(self):
        """Start the notification scheduler service"""
        if self.is_running:
            logger.warning("Notification scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting notification scheduler service")
        
        try:
            while self.is_running:
                await self._check_and_send_notifications()
                await asyncio.sleep(self.check_interval)
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}")
        finally:
            self.is_running = False
            logger.info("Notification scheduler service stopped")
    
    async def stop(self):
        """Stop the notification scheduler service"""
        self.is_running = False
        logger.info("Stopping notification scheduler service")
    
    async def _check_and_send_notifications(self):
        """Check for pending notifications and send them"""
        try:
            # Check for renewal warnings
            renewal_warnings = await self.notification_tool(
                operation="check_renewal_warnings",
                days_ahead=7
            )
            
            if renewal_warnings.get("success") and renewal_warnings.get("renewal_warnings"):
                await self._process_renewal_warnings(renewal_warnings["renewal_warnings"])
            
            # Check for paycheck availability notifications
            await self._check_paycheck_notifications()
            
        except Exception as e:
            logger.error(f"Error checking notifications: {e}")
    
    async def _process_renewal_warnings(self, warnings: List[Dict[str, Any]]):
        """Process renewal warnings and send notifications"""
        for warning in warnings:
            try:
                subscription_id = warning["id"]
                whatsapp_number = warning["users"]["whatsapp_number"]
                urgency_score = warning.get("urgency_score", 0)
                
                # Only send high priority warnings automatically
                if urgency_score >= 8:  # High urgency threshold
                    await self._send_renewal_warning(subscription_id, whatsapp_number)
                    
            except Exception as e:
                logger.error(f"Error processing renewal warning: {e}")
    
    async def _send_renewal_warning(self, subscription_id: str, whatsapp_number: str):
        """Send a renewal warning notification"""
        try:
            # Get the warning message
            warning_result = await self.notification_tool(
                operation="send_renewal_warning",
                subscription_id=subscription_id,
                notification_type="renewal_warning"
            )
            
            if warning_result.get("success"):
                message = warning_result["warning_message"]
                
                # Send via WhatsApp
                whatsapp_result = await self.whatsapp_tool(
                    operation="send_message",
                    phone_number=whatsapp_number,
                    message=message
                )
                
                if whatsapp_result.get("success"):
                    logger.info(f"Renewal warning sent to {whatsapp_number}")
                else:
                    logger.error(f"Failed to send WhatsApp message to {whatsapp_number}: {whatsapp_result.get('error')}")
            else:
                logger.error(f"Failed to generate renewal warning for subscription {subscription_id}: {warning_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending renewal warning: {e}")
    
    async def _check_paycheck_notifications(self):
        """Check for paycheck availability and send notifications"""
        try:
            # Get all active users (in a real implementation, you'd query the database)
            # For now, we'll use a mock approach
            active_users = await self._get_active_users()
            
            for user in active_users:
                whatsapp_number = user["whatsapp_number"]
                
                # Check paycheck availability
                paycheck_result = await self.notification_tool(
                    operation="check_paycheck_availability",
                    whatsapp_number=whatsapp_number
                )
                
                if paycheck_result.get("success"):
                    paycheck_status = paycheck_result["paycheck_status"]
                    
                    # Send notification if paycheck is available or soon
                    if paycheck_status in ["available", "soon"]:
                        await self._send_paycheck_notification(whatsapp_number)
                        
        except Exception as e:
            logger.error(f"Error checking paycheck notifications: {e}")
    
    async def _send_paycheck_notification(self, whatsapp_number: str):
        """Send paycheck availability notification"""
        try:
            # Get the paycheck notification message
            notification_result = await self.notification_tool(
                operation="send_paycheck_notification",
                whatsapp_number=whatsapp_number
            )
            
            if notification_result.get("success"):
                message = notification_result["notification_message"]
                
                # Send via WhatsApp
                whatsapp_result = await self.whatsapp_tool(
                    operation="send_message",
                    phone_number=whatsapp_number,
                    message=message
                )
                
                if whatsapp_result.get("success"):
                    logger.info(f"Paycheck notification sent to {whatsapp_number}")
                else:
                    logger.error(f"Failed to send WhatsApp message to {whatsapp_number}: {whatsapp_result.get('error')}")
            else:
                logger.error(f"Failed to generate paycheck notification for {whatsapp_number}: {notification_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending paycheck notification: {e}")
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get list of active users (mock implementation)"""
        # In a real implementation, this would query the database
        # For now, return mock data
        return [
            {"whatsapp_number": "+5511999887766", "full_name": "João Silva Santos"},
            {"whatsapp_number": "+5511888776655", "full_name": "Maria Oliveira Costa"},
            {"whatsapp_number": "+5511666554433", "full_name": "Ana Paula Ferreira"}
        ]
    
    async def send_immediate_notification(self, whatsapp_number: str, notification_type: str, **kwargs) -> Dict[str, Any]:
        """Send an immediate notification to a user"""
        try:
            if notification_type == "renewal_warning":
                subscription_id = kwargs.get("subscription_id")
                if not subscription_id:
                    return {"success": False, "error": "Subscription ID required for renewal warning"}
                
                await self._send_renewal_warning(subscription_id, whatsapp_number)
                return {"success": True, "message": "Renewal warning sent"}
                
            elif notification_type == "paycheck_notification":
                await self._send_paycheck_notification(whatsapp_number)
                return {"success": True, "message": "Paycheck notification sent"}
                
            else:
                return {"success": False, "error": f"Unknown notification type: {notification_type}"}
                
        except Exception as e:
            logger.error(f"Error sending immediate notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_notification_status(self) -> Dict[str, Any]:
        """Get the current status of the notification scheduler"""
        return {
            "is_running": self.is_running,
            "check_interval": self.check_interval,
            "last_check": datetime.now().isoformat(),
            "service_name": self.name
        }


# Global scheduler instance
_notification_scheduler = NotificationScheduler()


async def start_notification_scheduler():
    """Start the notification scheduler service"""
    await _notification_scheduler.start()


async def stop_notification_scheduler():
    """Stop the notification scheduler service"""
    await _notification_scheduler.stop()


async def send_immediate_notification(whatsapp_number: str, notification_type: str, **kwargs) -> Dict[str, Any]:
    """Send an immediate notification to a user"""
    return await _notification_scheduler.send_immediate_notification(whatsapp_number, notification_type, **kwargs)


async def get_notification_status() -> Dict[str, Any]:
    """Get the current status of the notification scheduler"""
    return await _notification_scheduler.get_notification_status()
