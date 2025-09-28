"""
Notification API for sofIA
REST API endpoints for subscription notifications and paycheck alerts
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import logging

from sofIA.tools.subscription_notifications import subscription_notifications_tool
from sofIA.tools.notification_scheduler import (
    send_immediate_notification,
    get_notification_status
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="sofIA Notification API",
    description="API for subscription notifications and paycheck alerts",
    version="1.0.0"
)


class NotificationRequest(BaseModel):
    whatsapp_number: str
    notification_type: str
    subscription_id: Optional[str] = None
    message: Optional[str] = None


class RenewalWarningRequest(BaseModel):
    subscription_id: str
    notification_type: str = "renewal_warning"


class PaycheckNotificationRequest(BaseModel):
    whatsapp_number: str


class NotificationPreferencesRequest(BaseModel):
    whatsapp_number: str
    preferences: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "sofIA Notification API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/notifications/status",
            "/notifications/renewal-warnings",
            "/notifications/paycheck-availability",
            "/notifications/send",
            "/notifications/preferences",
            "/notifications/history"
        ]
    }


@app.get("/notifications/status")
async def get_status():
    """Get notification system status"""
    try:
        status = await get_notification_status()
        return {
            "success": True,
            "status": status,
            "timestamp": status.get("last_check")
        }
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/renewal-warnings")
async def check_renewal_warnings(days_ahead: int = 7):
    """Check for subscriptions that need renewal warnings"""
    try:
        result = await subscription_notifications_tool(
            operation="check_renewal_warnings",
            days_ahead=days_ahead
        )
        
        if result.get("success"):
            return {
                "success": True,
                "renewal_warnings": result.get("renewal_warnings", []),
                "count": result.get("count", 0),
                "days_ahead": days_ahead
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error checking renewal warnings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/paycheck-availability/{whatsapp_number}")
async def check_paycheck_availability(whatsapp_number: str):
    """Check paycheck availability for a user"""
    try:
        result = await subscription_notifications_tool(
            operation="check_paycheck_availability",
            whatsapp_number=whatsapp_number
        )
        
        if result.get("success"):
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "paycheck_analysis": result.get("paycheck_analysis"),
                "upcoming_renewals": result.get("upcoming_renewals", []),
                "paycheck_status": result.get("paycheck_status"),
                "recommendations": result.get("recommendations", [])
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error checking paycheck availability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/send")
async def send_notification(request: NotificationRequest, background_tasks: BackgroundTasks):
    """Send a notification to a user"""
    try:
        # Send notification in background
        background_tasks.add_task(
            send_immediate_notification,
            request.whatsapp_number,
            request.notification_type,
            subscription_id=request.subscription_id,
            message=request.message
        )
        
        return {
            "success": True,
            "message": f"Notification queued for {request.whatsapp_number}",
            "notification_type": request.notification_type
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/renewal-warning")
async def send_renewal_warning(request: RenewalWarningRequest, background_tasks: BackgroundTasks):
    """Send a renewal warning for a specific subscription"""
    try:
        # Get subscription details first
        subscription_result = await subscription_notifications_tool(
            operation="send_renewal_warning",
            subscription_id=request.subscription_id,
            notification_type=request.notification_type
        )
        
        if subscription_result.get("success"):
            whatsapp_number = subscription_result.get("whatsapp_number")
            
            # Send notification in background
            background_tasks.add_task(
                send_immediate_notification,
                whatsapp_number,
                "renewal_warning",
                subscription_id=request.subscription_id
            )
            
            return {
                "success": True,
                "message": f"Renewal warning queued for {whatsapp_number}",
                "subscription_id": request.subscription_id,
                "warning_message": subscription_result.get("warning_message")
            }
        else:
            raise HTTPException(status_code=400, detail=subscription_result.get("error"))
            
    except Exception as e:
        logger.error(f"Error sending renewal warning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/paycheck-notification")
async def send_paycheck_notification(request: PaycheckNotificationRequest, background_tasks: BackgroundTasks):
    """Send paycheck availability notification"""
    try:
        # Send notification in background
        background_tasks.add_task(
            send_immediate_notification,
            request.whatsapp_number,
            "paycheck_notification"
        )
        
        return {
            "success": True,
            "message": f"Paycheck notification queued for {request.whatsapp_number}"
        }
        
    except Exception as e:
        logger.error(f"Error sending paycheck notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/preferences/{whatsapp_number}")
async def get_notification_preferences(whatsapp_number: str):
    """Get user's notification preferences"""
    try:
        result = await subscription_notifications_tool(
            operation="get_user_notification_preferences",
            whatsapp_number=whatsapp_number
        )
        
        if result.get("success"):
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "preferences": result.get("preferences"),
                "user_name": result.get("user_name")
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/notifications/preferences")
async def update_notification_preferences(request: NotificationPreferencesRequest):
    """Update user's notification preferences"""
    try:
        result = await subscription_notifications_tool(
            operation="update_notification_preferences",
            whatsapp_number=request.whatsapp_number,
            preferences=request.preferences
        )
        
        if result.get("success"):
            return {
                "success": True,
                "whatsapp_number": request.whatsapp_number,
                "updated_preferences": result.get("updated_preferences"),
                "updated_at": result.get("updated_at")
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/history/{whatsapp_number}")
async def get_notification_history(whatsapp_number: str):
    """Get user's notification history"""
    try:
        result = await subscription_notifications_tool(
            operation="get_notification_history",
            whatsapp_number=whatsapp_number
        )
        
        if result.get("success"):
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "notification_history": result.get("notification_history", []),
                "count": result.get("count", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/upcoming-renewals/{whatsapp_number}")
async def get_upcoming_renewals(whatsapp_number: str):
    """Get upcoming renewals for a user"""
    try:
        result = await subscription_notifications_tool(
            operation="get_upcoming_renewals",
            whatsapp_number=whatsapp_number
        )
        
        if result.get("success"):
            return {
                "success": True,
                "whatsapp_number": whatsapp_number,
                "upcoming_renewals": result.get("upcoming_renewals", []),
                "count": result.get("count", 0),
                "total_cost_brl": result.get("total_cost_brl", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error getting upcoming renewals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sofIA Notification API",
        "timestamp": "2025-01-27T00:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
