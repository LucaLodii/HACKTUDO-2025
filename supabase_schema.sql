-- sofIA Memory System - Supabase Database Schema
-- Run this in your Supabase SQL editor to create the required tables

-- Enable Row Level Security
ALTER DATABASE postgres SET "app.jwt_secret" TO 'your-jwt-secret';

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_message TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id TEXT,
    payment_state TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    preference_type TEXT NOT NULL,
    preference_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, preference_type)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_id TEXT UNIQUE,
    amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency TEXT NOT NULL DEFAULT 'BRL',
    product TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    payment_method TEXT NOT NULL DEFAULT 'sofIA',
    session_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Memory summaries table (for caching)
CREATE TABLE IF NOT EXISTS memory_summaries (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_type ON user_preferences(preference_type);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);

CREATE INDEX IF NOT EXISTS idx_memory_summaries_user_id ON memory_summaries(user_id);

-- Enable Row Level Security (RLS) - Optional for hackathon
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE memory_summaries ENABLE ROW LEVEL SECURITY;

-- Create policies for RLS (if enabled)
-- CREATE POLICY "Users can view their own conversations" ON conversations
--     FOR SELECT USING (auth.uid()::text = user_id);

-- CREATE POLICY "Users can insert their own conversations" ON conversations
--     FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- Create a function to clean up old data (optional)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Keep only last 100 conversations per user
    DELETE FROM conversations 
    WHERE id NOT IN (
        SELECT id FROM conversations 
        ORDER BY timestamp DESC 
        LIMIT 100
    );
    
    -- Keep only last 50 transactions per user
    DELETE FROM transactions 
    WHERE id NOT IN (
        SELECT id FROM transactions 
        ORDER BY timestamp DESC 
        LIMIT 50
    );
    
    -- Update memory summaries older than 1 hour
    DELETE FROM memory_summaries 
    WHERE last_updated < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to run cleanup (optional)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');

-- Insert some sample data for testing (optional)
INSERT INTO conversations (user_id, user_message, agent_response, context) VALUES
('demo_user_1', 'Hello sofIA!', 'Hello! I''m sofIA, your AI payment assistant. How can I help you today?', '{"payment_state": "idle"}'),
('demo_user_1', 'I want to buy coffee', 'I''d be happy to help you buy coffee! What type of coffee would you like?', '{"payment_state": "intent_created"}'),
('demo_user_2', 'Send PIX to João', 'I can help you send a PIX transfer to João. What amount would you like to send?', '{"payment_state": "awaiting_amount"}');

INSERT INTO user_preferences (user_id, preference_type, preference_value) VALUES
('demo_user_1', 'language', 'pt-BR'),
('demo_user_1', 'payment_method', 'sofIA'),
('demo_user_2', 'language', 'pt-BR'),
('demo_user_2', 'payment_method', 'PIX');

INSERT INTO transactions (user_id, transaction_id, amount, product, status) VALUES
('demo_user_1', 'txn_001', 12.50, 'Coffee', 'completed'),
('demo_user_1', 'txn_002', 28.00, 'Lunch', 'completed'),
('demo_user_2', 'txn_003', 100.00, 'PIX Transfer', 'completed');

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
