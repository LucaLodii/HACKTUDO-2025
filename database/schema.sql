-- sofIA Subscription Management Database Schema
-- Supabase PostgreSQL Schema for BEMOBI Telecom Subscription Management

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for fresh deployments)
DROP TABLE IF EXISTS renewal_reminders CASCADE;
DROP TABLE IF EXISTS subscription_payments CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS subscription_plans CASCADE;
DROP TABLE IF EXISTS operators CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Telecom Operators (BEMOBI Clients)
CREATE TABLE operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE, -- VIVO, CLARO, OI, TIM
    display_name VARCHAR(100) NOT NULL,
    logo_url TEXT,
    brand_color VARCHAR(7), -- Hex color code
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscription Plans per Operator
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    plan_code VARCHAR(50) NOT NULL, -- Unique identifier within operator
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    billing_cycle VARCHAR(20) NOT NULL CHECK (billing_cycle IN ('daily', 'weekly', 'monthly', 'yearly')),
    data_limit_gb INTEGER, -- Data allowance in GB
    voice_minutes INTEGER, -- Voice minutes included
    sms_count INTEGER, -- SMS messages included
    features JSONB DEFAULT '{}', -- Additional features as JSON
    is_active BOOLEAN DEFAULT TRUE,
    can_upgrade_to UUID[], -- Array of plan IDs this can upgrade to
    can_downgrade_to UUID[], -- Array of plan IDs this can downgrade to
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(operator_id, plan_code)
);

-- End Customers (WhatsApp Users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'pt-BR',
    timezone VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Active User Subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id) ON DELETE CASCADE,
    subscription_external_id VARCHAR(100), -- External system reference
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled', 'pending_renewal', 'suspended')),
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    auto_renewal BOOLEAN DEFAULT TRUE,
    last_renewal_reminder TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}', -- Additional subscription metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subscription Payment History
CREATE TABLE subscription_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    payment_type VARCHAR(30) NOT NULL CHECK (payment_type IN ('renewal', 'upgrade', 'downgrade', 'initial', 'refund')),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'BRL',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled', 'refunded')),
    payment_method VARCHAR(20), -- PIX, CARD, BOLETO, etc.
    -- AP2 Protocol References
    ap2_mandate_id VARCHAR(100),
    ap2_transaction_id VARCHAR(100),
    ap2_signature TEXT,
    -- External Gateway References
    gateway_transaction_id VARCHAR(100),
    gateway_reference VARCHAR(100),
    -- Timing
    processed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Renewal Reminder Management
CREATE TABLE renewal_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    reminder_type VARCHAR(20) NOT NULL CHECK (reminder_type IN ('7_day', '3_day', '1_day', 'expiry', 'overdue')),
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    message_id VARCHAR(100), -- WhatsApp message ID
    user_response VARCHAR(20) CHECK (user_response IN ('renewed', 'declined', 'ignored', 'deferred')),
    response_received_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_users_whatsapp_number ON users(whatsapp_number);
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX idx_user_subscriptions_end_date ON user_subscriptions(end_date);
CREATE INDEX idx_user_subscriptions_operator_id ON user_subscriptions(operator_id);
CREATE INDEX idx_subscription_plans_operator_id ON subscription_plans(operator_id);
CREATE INDEX idx_subscription_plans_active ON subscription_plans(is_active);
CREATE INDEX idx_subscription_payments_subscription_id ON subscription_payments(subscription_id);
CREATE INDEX idx_subscription_payments_status ON subscription_payments(status);
CREATE INDEX idx_subscription_payments_ap2_mandate_id ON subscription_payments(ap2_mandate_id);
CREATE INDEX idx_renewal_reminders_subscription_id ON renewal_reminders(subscription_id);
CREATE INDEX idx_renewal_reminders_scheduled_for ON renewal_reminders(scheduled_for);
CREATE INDEX idx_renewal_reminders_sent_at ON renewal_reminders(sent_at);

-- Row Level Security (RLS) Policies
ALTER TABLE operators ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscription_payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE renewal_reminders ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (can be customized based on requirements)
-- Allow public read access to operators and plans
CREATE POLICY "Public read access for operators" ON operators FOR SELECT USING (true);
CREATE POLICY "Public read access for subscription plans" ON subscription_plans FOR SELECT USING (true);

-- Users can only access their own data
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid()::text = id::text);

-- Users can only access their own subscriptions
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions 
    FOR SELECT USING (user_id IN (SELECT id FROM users WHERE auth.uid()::text = id::text));

-- Users can only access their own payments
CREATE POLICY "Users can view own payments" ON subscription_payments 
    FOR SELECT USING (subscription_id IN (
        SELECT id FROM user_subscriptions WHERE user_id IN (
            SELECT id FROM users WHERE auth.uid()::text = id::text
        )
    ));

-- Users can only access their own reminders
CREATE POLICY "Users can view own reminders" ON renewal_reminders 
    FOR SELECT USING (subscription_id IN (
        SELECT id FROM user_subscriptions WHERE user_id IN (
            SELECT id FROM users WHERE auth.uid()::text = id::text
        )
    ));

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_operators_updated_at BEFORE UPDATE ON operators 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_subscription_payments_updated_at BEFORE UPDATE ON subscription_payments 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_renewal_reminders_updated_at BEFORE UPDATE ON renewal_reminders 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- View for subscription management dashboard
CREATE VIEW subscription_overview AS
SELECT 
    us.id,
    u.whatsapp_number,
    u.full_name,
    o.name as operator_name,
    o.display_name as operator_display_name,
    sp.name as plan_name,
    sp.price_cents,
    sp.billing_cycle,
    sp.data_limit_gb,
    us.status,
    us.start_date,
    us.end_date,
    us.auto_renewal,
    CASE 
        WHEN us.end_date < NOW() THEN 'expired'
        WHEN us.end_date < NOW() + INTERVAL '7 days' THEN 'expiring_soon'
        WHEN us.end_date < NOW() + INTERVAL '30 days' THEN 'expiring_monthly'
        ELSE 'active'
    END as renewal_status,
    us.end_date - NOW() as time_until_expiry
FROM user_subscriptions us
JOIN users u ON us.user_id = u.id
JOIN operators o ON us.operator_id = o.id
JOIN subscription_plans sp ON us.plan_id = sp.id
WHERE us.status IN ('active', 'pending_renewal');

-- View for payment analytics
CREATE VIEW payment_analytics AS
SELECT 
    sp.payment_type,
    sp.status,
    sp.currency,
    COUNT(*) as transaction_count,
    SUM(sp.amount_cents) as total_amount_cents,
    AVG(sp.amount_cents) as avg_amount_cents,
    DATE_TRUNC('day', sp.created_at) as transaction_date
FROM subscription_payments sp
WHERE sp.created_at >= NOW() - INTERVAL '90 days'
GROUP BY sp.payment_type, sp.status, sp.currency, DATE_TRUNC('day', sp.created_at)
ORDER BY transaction_date DESC;

-- Comments for documentation
COMMENT ON TABLE operators IS 'Telecom operators that are BEMOBI clients (VIVO, CLARO, OI, TIM)';
COMMENT ON TABLE subscription_plans IS 'Available subscription plans per telecom operator';
COMMENT ON TABLE users IS 'End customers identified by WhatsApp number';
COMMENT ON TABLE user_subscriptions IS 'Active subscriptions linking users to operator plans';
COMMENT ON TABLE subscription_payments IS 'Payment history for all subscription operations with AP2 references';
COMMENT ON TABLE renewal_reminders IS 'Automated reminder system for subscription renewals';

COMMENT ON COLUMN subscription_payments.ap2_mandate_id IS 'AP2 Protocol mandate ID for cryptographic verification';
COMMENT ON COLUMN subscription_payments.ap2_transaction_id IS 'AP2 Protocol transaction ID for audit trail';
COMMENT ON COLUMN subscription_payments.ap2_signature IS 'AP2 Protocol cryptographic signature';
