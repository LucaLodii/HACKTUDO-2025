"""
Test script for subscription notifications functionality
Demonstrates renewal warnings and paycheck availability notifications
"""

import asyncio
import json
from datetime import datetime
from sofIA.tools.subscription_notifications import subscription_notifications_tool


async def test_renewal_warnings():
    """Test renewal warning functionality"""
    print("🔔 Testing Renewal Warnings...")
    print("=" * 50)
    
    # Check for renewal warnings
    result = await subscription_notifications_tool(
        operation="check_renewal_warnings",
        days_ahead=7
    )
    
    if result.get("success"):
        warnings = result.get("renewal_warnings", [])
        print(f"Found {len(warnings)} subscriptions needing renewal warnings:")
        
        for warning in warnings:
            print(f"\n📱 Subscription: {warning['subscription_plans']['name']}")
            print(f"   Operator: {warning['operators']['display_name']}")
            print(f"   User: {warning['users']['full_name']} ({warning['users']['whatsapp_number']})")
            print(f"   Expires in: {warning['days_until_expiry']} days")
            print(f"   Urgency: {warning['warning_type']} (score: {warning['urgency_score']})")
            print(f"   Price: R$ {warning['subscription_plans']['price_cents'] / 100:.2f}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def test_paycheck_availability():
    """Test paycheck availability functionality"""
    print("💰 Testing Paycheck Availability...")
    print("=" * 50)
    
    # Test with a mock user
    whatsapp_number = "+5511999887766"
    
    result = await subscription_notifications_tool(
        operation="check_paycheck_availability",
        whatsapp_number=whatsapp_number
    )
    
    if result.get("success"):
        analysis = result.get("paycheck_analysis", {})
        status = result.get("paycheck_status")
        renewals = result.get("upcoming_renewals", [])
        recommendations = result.get("recommendations", [])
        
        print(f"📱 User: {whatsapp_number}")
        print(f"💰 Paycheck Status: {status}")
        
        if analysis.get("pattern_detected"):
            print(f"📊 Payment Pattern Detected: Yes")
            print(f"   Average Interval: {analysis.get('average_payment_interval_days')} days")
            print(f"   Last Payment: {analysis.get('last_payment_date')}")
            print(f"   Estimated Next: {analysis.get('estimated_next_paycheck')}")
            print(f"   Confidence: {analysis.get('confidence_level')}")
        else:
            print("📊 Payment Pattern Detected: No")
        
        if renewals:
            print(f"\n📱 Upcoming Renewals ({len(renewals)}):")
            total_cost = 0
            for renewal in renewals:
                print(f"   • {renewal['operator']} {renewal['plan_name']}: R$ {renewal['cost_brl']:.2f} ({renewal['days_until_expiry']} days)")
                total_cost += renewal['cost_brl']
            print(f"   💳 Total Cost: R$ {total_cost:.2f}")
        
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"   • {rec}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def test_renewal_warning_message():
    """Test generating a renewal warning message"""
    print("📝 Testing Renewal Warning Message...")
    print("=" * 50)
    
    # Test with a mock subscription ID
    subscription_id = "sub-001"
    
    result = await subscription_notifications_tool(
        operation="send_renewal_warning",
        subscription_id=subscription_id,
        notification_type="renewal_warning"
    )
    
    if result.get("success"):
        message = result.get("warning_message")
        days_until_expiry = result.get("days_until_expiry")
        whatsapp_number = result.get("whatsapp_number")
        
        print(f"📱 WhatsApp Number: {whatsapp_number}")
        print(f"⏰ Days Until Expiry: {days_until_expiry}")
        print(f"\n📝 Generated Message:")
        print("-" * 30)
        print(message)
        print("-" * 30)
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def test_paycheck_notification_message():
    """Test generating a paycheck notification message"""
    print("💳 Testing Paycheck Notification Message...")
    print("=" * 50)
    
    # Test with a mock user
    whatsapp_number = "+5511999887766"
    
    result = await subscription_notifications_tool(
        operation="send_paycheck_notification",
        whatsapp_number=whatsapp_number
    )
    
    if result.get("success"):
        message = result.get("notification_message")
        status = result.get("paycheck_status")
        
        print(f"📱 WhatsApp Number: {whatsapp_number}")
        print(f"💰 Paycheck Status: {status}")
        print(f"\n📝 Generated Message:")
        print("-" * 30)
        print(message)
        print("-" * 30)
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def test_notification_preferences():
    """Test notification preferences functionality"""
    print("⚙️ Testing Notification Preferences...")
    print("=" * 50)
    
    whatsapp_number = "+5511999887766"
    
    # Get current preferences
    result = await subscription_notifications_tool(
        operation="get_user_notification_preferences",
        whatsapp_number=whatsapp_number
    )
    
    if result.get("success"):
        preferences = result.get("preferences", {})
        print(f"📱 User: {whatsapp_number}")
        print(f"👤 Name: {result.get('user_name', 'N/A')}")
        print(f"\n⚙️ Current Preferences:")
        print(json.dumps(preferences, indent=2))
        
        # Test updating preferences
        new_preferences = preferences.copy()
        new_preferences["renewal_warnings"]["days_ahead"] = [14, 7, 3, 1]
        new_preferences["renewal_warnings"]["time_of_day"] = "10:00"
        
        update_result = await subscription_notifications_tool(
            operation="update_notification_preferences",
            whatsapp_number=whatsapp_number,
            preferences=new_preferences
        )
        
        if update_result.get("success"):
            print(f"\n✅ Preferences updated successfully!")
            print(f"🕐 Updated at: {update_result.get('updated_at')}")
        else:
            print(f"❌ Error updating preferences: {update_result.get('error')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def test_upcoming_renewals():
    """Test getting upcoming renewals for a user"""
    print("📅 Testing Upcoming Renewals...")
    print("=" * 50)
    
    whatsapp_number = "+5511999887766"
    
    result = await subscription_notifications_tool(
        operation="get_upcoming_renewals",
        whatsapp_number=whatsapp_number
    )
    
    if result.get("success"):
        renewals = result.get("upcoming_renewals", [])
        total_cost = result.get("total_cost_brl", 0)
        
        print(f"📱 User: {whatsapp_number}")
        print(f"📅 Upcoming Renewals: {len(renewals)}")
        print(f"💳 Total Cost: R$ {total_cost:.2f}")
        
        if renewals:
            print(f"\n📋 Renewal Details:")
            for renewal in renewals:
                print(f"   • {renewal['operator']} {renewal['plan_name']}")
                print(f"     Price: R$ {renewal['price_brl']:.2f}")
                print(f"     Expires: {renewal['end_date']} ({renewal['days_until_expiry']} days)")
                print(f"     Auto-renewal: {'Yes' if renewal['auto_renewal'] else 'No'}")
                print()
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print("\n" + "=" * 50)


async def main():
    """Run all notification tests"""
    print("🚀 sofIA Subscription Notifications Test Suite")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Run all tests
        await test_renewal_warnings()
        await test_paycheck_availability()
        await test_renewal_warning_message()
        await test_paycheck_notification_message()
        await test_notification_preferences()
        await test_upcoming_renewals()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
