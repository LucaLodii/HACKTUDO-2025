# Quick Supabase Setup for sofIA

## 🚀 3-Step Setup

### Step 1: Open Supabase
1. Go to: https://supabase.com
2. Sign in to your account
3. Open your project: https://nknnxwqhpsgfiivnilmy.supabase.co

### Step 2: Run SQL Schema
1. Click **"SQL Editor"** in the left sidebar
2. Click **"New Query"**
3. Copy the **entire contents** of `supabase_schema.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or press Ctrl+Enter)

### Step 3: Test Connection
Run this command in your terminal:
```bash
python test_supabase_connection.py
```

## ✅ What You'll See

After running the schema, you should see:
- 4 tables created successfully
- Sample data inserted
- Indexes created for performance

## 🔧 If You Get Errors

**Permission Error:**
```sql
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
```

**Table Already Exists:**
- This is normal, the schema uses `CREATE TABLE IF NOT EXISTS`

## 🎯 Next Steps

Once the schema is created:
1. Run `python test_supabase_connection.py` - should show ✅
2. Run `python app.py demo` - will use real Supabase memory
3. Check Supabase dashboard to see data being stored

## 📊 What the Memory System Will Do

- 🧠 **Remember conversations** across sessions
- ⚙️ **Store user preferences** (language, payment methods)
- 💳 **Track transaction history** for personalized responses
- 🤖 **Provide AI context** for better responses

**Total setup time: 2-3 minutes** ⏱️
