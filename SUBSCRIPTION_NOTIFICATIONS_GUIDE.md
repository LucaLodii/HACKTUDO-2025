# sofIA Subscription Notifications System

## Overview

The sofIA subscription notifications system provides proactive alerts for subscription renewals and paycheck availability. It integrates with the existing subscription management database to fetch real-time data and send personalized WhatsApp notifications to users.

## Features

### 🔔 Renewal Warnings
- **Proactive Alerts**: Automatically detects subscriptions expiring within 7 days
- **Urgency Scoring**: Prioritizes notifications based on expiry time and auto-renewal status
- **Customizable Timing**: Configurable reminder intervals (7, 3, 1 days before expiry)
- **Personalized Messages**: Tailored messages based on user preferences and subscription details

### 💰 Paycheck Availability
- **Pattern Detection**: Analyzes payment history to predict paycheck timing
- **Smart Recommendations**: Suggests optimal renewal timing based on available funds
- **Cost Analysis**: Calculates total upcoming renewal costs
- **Status Tracking**: Real-time paycheck availability status

### ⚙️ User Preferences
- **Notification Settings**: Customizable reminder preferences
- **Quiet Hours**: Configurable do-not-disturb periods
- **Language Support**: Multi-language notification support
- **Frequency Control**: Adjustable notification frequency

## Architecture

```
sofIA Notification System
├── subscription_notifications.py     # Core notification logic
├── subscription_notification_tool.py # Agent tool wrapper
├── notification_scheduler.py         # Background service
├── notification_api.py              # REST API endpoints
└── test_notifications.py            # Test suite
```

## Database Integration

The system integrates with the existing subscription management database schema:

### Key Tables
- `user_subscriptions` - Active subscriptions with expiry dates
- `users` - User information and notification preferences
- `renewal_reminders` - Scheduled reminder tracking
- `subscription_payments` - Payment history for paycheck analysis

### Key Fields
- `end_date` - Subscription expiry date
- `auto_renewal` - Auto-renewal status
- `last_renewal_reminder` - Last reminder timestamp
- `notification_preferences` - User notification settings

## API Endpoints

### Notification Status
```http
GET /notifications/status
```
Returns the current status of the notification system.

### Renewal Warnings
```http
GET /notifications/renewal-warnings?days_ahead=7
```
Checks for subscriptions needing renewal warnings.

### Paycheck Availability
```http
GET /notifications/paycheck-availability/{whatsapp_number}
```
Checks paycheck availability for a specific user.

### Send Notifications
```http
POST /notifications/send
Content-Type: application/json

{
  "whatsapp_number": "+5511999887766",
  "notification_type": "renewal_warning",
  "subscription_id": "sub-001"
}
```

### User Preferences
```http
GET /notifications/preferences/{whatsapp_number}
PUT /notifications/preferences
```

## Usage Examples

### 1. Check Renewal Warnings

```python
from sofIA.tools.subscription_notifications import subscription_notifications_tool

# Check for subscriptions expiring in the next 7 days
result = await subscription_notifications_tool(
    operation="check_renewal_warnings",
    days_ahead=7
)

if result["success"]:
    warnings = result["renewal_warnings"]
    for warning in warnings:
        print(f"Subscription {warning['id']} expires in {warning['days_until_expiry']} days")
        print(f"Urgency: {warning['warning_type']} (score: {warning['urgency_score']})")
```

### 2. Check Paycheck Availability

```python
# Check paycheck availability for a user
result = await subscription_notifications_tool(
    operation="check_paycheck_availability",
    whatsapp_number="+5511999887766"
)

if result["success"]:
    status = result["paycheck_status"]
    renewals = result["upcoming_renewals"]
    recommendations = result["recommendations"]
    
    print(f"Paycheck Status: {status}")
    print(f"Upcoming Renewals: {len(renewals)}")
    print(f"Total Cost: R$ {result['total_upcoming_cost_brl']:.2f}")
```

### 3. Send Renewal Warning

```python
# Send a renewal warning for a specific subscription
result = await subscription_notifications_tool(
    operation="send_renewal_warning",
    subscription_id="sub-001",
    notification_type="renewal_warning"
)

if result["success"]:
    message = result["warning_message"]
    whatsapp_number = result["whatsapp_number"]
    
    # Send via WhatsApp
    await whatsapp_tool(
        operation="send_message",
        phone_number=whatsapp_number,
        message=message
    )
```

### 4. Manage User Preferences

```python
# Get user preferences
preferences = await subscription_notifications_tool(
    operation="get_user_notification_preferences",
    whatsapp_number="+5511999887766"
)

# Update preferences
new_preferences = {
    "renewal_warnings": {
        "enabled": True,
        "days_ahead": [14, 7, 3, 1],
        "time_of_day": "10:00"
    },
    "paycheck_notifications": {
        "enabled": True,
        "check_frequency": "daily"
    }
}

await subscription_notifications_tool(
    operation="update_notification_preferences",
    whatsapp_number="+5511999887766",
    preferences=new_preferences
)
```

## Background Service

The notification scheduler runs as a background service to automatically check for and send notifications:

```python
from sofIA.tools.notification_scheduler import start_notification_scheduler

# Start the background service
await start_notification_scheduler()
```

### Service Features
- **Automatic Checks**: Runs every 5 minutes to check for pending notifications
- **Priority Handling**: Sends high-urgency notifications immediately
- **Error Handling**: Robust error handling and logging
- **Scalable**: Can handle multiple users and subscriptions

## Message Templates

### Renewal Warning Messages

#### Expired Subscription
```
🚨 Olá João!

Seu plano Vivo Premium 10GB EXPIROU!
💰 Renovar agora por R$ 49.90

⚠️ Seus serviços podem estar suspensos.
🔄 Digite 'RENOVAR' para renovar imediatamente.
```

#### Urgent (1 day)
```
⚠️ Olá João!

Seu plano Vivo Premium 10GB expira em 1 dia!
💰 Renovação: R$ 49.90

🚨 URGENTE: Renove hoje para evitar interrupção.
🔄 Digite 'RENOVAR' para renovar agora.
```

#### High Priority (3 days)
```
📱 Oi João!

Seu plano Vivo Premium 10GB expira em 3 dias.
💰 Renovação: R$ 49.90

🔄 Opções disponíveis:
• 'RENOVAR' - Renovar plano atual
• 'UPGRADE' - Ver planos melhores
• 'ECONOMIZAR' - Ver planos mais baratos
```

### Paycheck Notification Messages

```
💰 Olá! Análise do seu salário:

⏰ Seu salário chegará em breve (1-3 dias)

📱 Renovações próximas (1):
• Vivo Premium 10GB: R$ 49.90 (2 dias)

💳 Total: R$ 49.90

💡 Recomendações:
• ⏰ Seu salário chegará em breve. Considere aguardar para renovar.
• 📱 Configure lembretes para quando o salário estiver disponível.

🔄 Digite 'RENOVAR' para renovar agora ou 'INFO' para mais detalhes.
```

## Configuration

### Environment Variables

```bash
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# WhatsApp
WHATSAPP_APP_SECRET=your_whatsapp_secret

# Notification Settings
NOTIFICATION_CHECK_INTERVAL=300  # 5 minutes
DEFAULT_REMINDER_DAYS=7,3,1     # Days before expiry
QUIET_HOURS_START=22:00
QUIET_HOURS_END=08:00
```

### Default Preferences

```json
{
  "renewal_warnings": {
    "enabled": true,
    "days_ahead": [7, 3, 1],
    "time_of_day": "09:00",
    "language": "pt-BR"
  },
  "paycheck_notifications": {
    "enabled": true,
    "check_frequency": "daily",
    "time_of_day": "08:00"
  },
  "payment_reminders": {
    "enabled": true,
    "overdue_reminders": true,
    "frequency": "daily"
  },
  "general_preferences": {
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00"
    },
    "weekend_notifications": true
  }
}
```

## Testing

Run the test suite to verify functionality:

```bash
python test_notifications.py
```

The test suite covers:
- Renewal warning detection
- Paycheck availability analysis
- Message generation
- User preferences management
- Upcoming renewals tracking

## Integration with sofIA Agent

The notification system is integrated with the sofIA agent through the `subscription_notification_tool`:

```python
# In sofIA agent
from .tools.subscription_notification_tool import subscription_notification_tool

# Agent can now use notification operations
result = await subscription_notification_tool(
    operation="check_renewal_warnings",
    days_ahead=7
)
```

## Monitoring and Logging

The system provides comprehensive logging:

```python
import logging

logger = logging.getLogger(__name__)

# Log renewal warnings
logger.info(f"Renewal warning sent to {whatsapp_number}")

# Log paycheck notifications
logger.info(f"Paycheck notification sent to {whatsapp_number}")

# Log errors
logger.error(f"Failed to send notification: {error}")
```

## Security Considerations

- **Data Privacy**: User data is handled according to privacy regulations
- **Rate Limiting**: Prevents spam notifications
- **Authentication**: API endpoints require proper authentication
- **Audit Trail**: All notifications are logged for audit purposes

## Performance Optimization

- **Database Indexing**: Optimized queries with proper indexes
- **Caching**: Frequently accessed data is cached
- **Batch Processing**: Notifications are processed in batches
- **Async Operations**: Non-blocking async operations

## Future Enhancements

- **Machine Learning**: AI-powered paycheck prediction
- **Multi-channel**: Support for SMS, email, and push notifications
- **Advanced Analytics**: Detailed notification performance metrics
- **A/B Testing**: Message template optimization
- **Integration**: Third-party calendar and banking APIs

## Troubleshooting

### Common Issues

1. **Notifications not sending**
   - Check WhatsApp bridge connection
   - Verify user phone number format
   - Check notification preferences

2. **Database connection errors**
   - Verify Supabase credentials
   - Check network connectivity
   - Review database permissions

3. **Message formatting issues**
   - Check message templates
   - Verify user language preferences
   - Review character limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For technical support or questions about the notification system:

1. Check the test suite output
2. Review application logs
3. Verify database connectivity
4. Test with mock data first

The notification system is designed to be robust, scalable, and user-friendly, providing valuable proactive alerts to help users manage their subscriptions effectively.
