# Supabase Setup Guide for sofIA Memory System

## Step 1: Access Your Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Navigate to your project: `https://nknnxwqhpsgfiivnilmy.supabase.co`
3. Click on "SQL Editor" in the left sidebar

## Step 2: Create Database Schema

Copy and paste the entire contents of `supabase_schema.sql` into the SQL Editor and click "Run".

This will create:
- ✅ `conversations` table for chat history
- ✅ `user_preferences` table for user settings
- ✅ `transactions` table for payment history
- ✅ `memory_summaries` table for AI context caching
- ✅ Indexes for performance
- ✅ Sample data for testing

## Step 3: Verify Tables Created

Run this query to verify all tables were created:

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('conversations', 'user_preferences', 'transactions', 'memory_summaries');
```

You should see all 4 tables listed.

## Step 4: Test Sample Data

Run this query to see the sample data:

```sql
SELECT * FROM conversations LIMIT 5;
SELECT * FROM user_preferences LIMIT 5;
SELECT * FROM transactions LIMIT 5;
```

## Step 5: Test Connection from sofIA

Once the schema is created, the sofIA system will automatically connect to Supabase and use real persistent storage instead of mock memory.

## Troubleshooting

### If you get permission errors:
```sql
-- Grant permissions (run as superuser)
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
```

### If tables already exist:
The schema uses `CREATE TABLE IF NOT EXISTS` so it's safe to run multiple times.

### If you want to start fresh:
```sql
-- Drop tables (be careful!)
DROP TABLE IF EXISTS memory_summaries CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
```

## Next Steps

After setting up the schema:
1. Run `python app.py demo` to test the memory system
2. Check Supabase dashboard to see data being stored
3. Test conversation persistence across sessions
4. Verify user preferences and transaction history

The memory system will now provide:
- 🧠 Persistent conversation history
- ⚙️ User preference storage
- 💳 Transaction history tracking
- 🤖 AI context for personalized responses
