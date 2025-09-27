# sofIA Memory System Setup Guide

## Overview

The sofIA Memory System provides persistent conversation and user memory using Supabase as the backend database. This allows the AI agent to remember previous conversations, user preferences, and transaction history across sessions.

## Quick Setup (Hackathon)

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### 2. Set Up Database

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `supabase_schema.sql`
4. Run the SQL to create the required tables

### 3. Configure Environment

1. Copy `env.example` to `.env`
2. Add your Supabase credentials:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

### 4. Install Dependencies

```bash
pip install supabase
# or if using uv
uv add supabase
```

### 5. Test the System

```bash
python test_memory.py
```

## Features

### Memory Types

- **Conversation Memory**: Full chat history with context
- **User Preferences**: Language, payment methods, favorite products
- **Transaction History**: Past purchases and payment patterns
- **Contextual Memory**: Current session state and ongoing transactions

### Memory Integration

- **Automatic Saving**: All conversations and transactions are automatically saved
- **Context Enhancement**: AI prompts include memory context for personalized responses
- **Persistent Storage**: Memory survives server restarts and deployments
- **Performance Optimized**: Indexed queries and efficient data retrieval

## Database Schema

### Tables Created

- `conversations` - Stores all conversation history
- `user_preferences` - Stores user preferences and settings
- `transactions` - Stores transaction history
- `memory_summaries` - Caches memory summaries for performance

### Key Features

- Automatic cleanup of old data
- Indexed queries for performance
- JSONB support for flexible context storage
- Row Level Security ready (optional)

## Usage Examples

### In Agent Code

```python
from sofIA.memory import SupabaseMemoryManager

# Initialize memory manager
memory_manager = SupabaseMemoryManager()

# Save conversation
memory_manager.save_conversation(
    user_id="user123",
    message="I want to buy coffee",
    response="I'd be happy to help! What type of coffee?",
    context={"payment_state": "intent_created"}
)

# Get memory context
context = memory_manager.get_memory_summary("user123")
print(context)  # "👤 Returning user with 5 previous messages. 💬 Recent topics: coffee, payment"
```

### Using Memory Tool

```python
from sofIA.memory import memory_tool

# Get user context
context = memory_tool.function(
    action="get_context",
    user_id="user123"
)

# Remember user preference
memory_tool.function(
    action="remember_preference",
    user_id="user123",
    preference_type="language",
    preference_value="pt-BR"
)
```

## Memory Context Examples

### New User

```
🆕 This is a new user with no previous conversation history.
```

### Returning User

```
👤 Returning user with 12 previous messages. 💬 Recent topics: coffee, pix_transfer. 💳 3 transactions, R$ 45.50 total. ⚙️ Preferences: language: pt-BR, payment_method: sofIA
```

### High-Engagement User

```
👤 Returning user with 25 previous messages. 💬 Recent topics: payment, lunch. 💳 8 transactions, R$ 156.75 total. 📊 Recent: Coffee, Lunch (R$ 28.50). ⚙️ Preferences: language: pt-BR, payment_method: PIX
```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure SUPABASE_URL and SUPABASE_ANON_KEY are set
2. **Database Connection**: Check your Supabase project is active
3. **Table Not Found**: Run the supabase_schema.sql script
4. **Permission Errors**: Check your Supabase anon key permissions

### Debug Mode

Enable debug logging by setting:

```bash
LOG_LEVEL=DEBUG
```

## Performance Notes

- Memory queries are optimized with database indexes
- Conversation history is limited to 100 messages per user
- Transaction history is limited to 50 transactions per user
- Memory summaries are cached for 1 hour
- Automatic cleanup runs daily to remove old data

## Security Considerations

- All data is stored in Supabase with proper encryption
- User data is isolated by user_id
- Sensitive information is not logged
- Row Level Security can be enabled for additional protection

## Hackathon Tips

1. **Quick Start**: Use the provided test script to verify setup
2. **Sample Data**: The schema includes sample data for testing
3. **Memory Context**: The AI will automatically use memory context in responses
4. **Debugging**: Check the console logs for memory operations
5. **Testing**: Use different user_ids to test multi-user scenarios
