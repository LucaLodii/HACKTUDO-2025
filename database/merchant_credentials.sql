-- Merchant Credentials for White-label sofIA Mock Implementation
-- Simulates Bemobi merchant credentials for each telecom operator

CREATE TABLE IF NOT EXISTS merchant_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    -- Mock Bemobi Credentials (for simulation)
    mock_merchant_id VARCHAR(50) NOT NULL UNIQUE,
    mock_api_key VARCHAR(100) NOT NULL,
    mock_secret_key VARCHAR(100) NOT NULL,
    -- sofIA Agent Configuration
    sofia_agent_id VARCHAR(50) NOT NULL UNIQUE,
    sofia_agent_name VARCHAR(100) NOT NULL,
    -- Payment Configuration
    supported_payment_methods JSONB DEFAULT '["PIX", "CARD", "BOLETO"]',
    default_currency VARCHAR(3) DEFAULT 'BRL',
    -- Mock Configuration
    mock_success_rate DECIMAL(3,2) DEFAULT 0.95, -- 95% success rate
    mock_processing_delay_ms INTEGER DEFAULT 2000, -- 2 second delay
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(operator_id)
);

-- Insert mock credentials for each telecom operator
INSERT INTO merchant_credentials (
    operator_id,
    mock_merchant_id,
    mock_api_key,
    mock_secret_key,
    sofia_agent_id,
    sofia_agent_name,
    supported_payment_methods,
    mock_success_rate,
    mock_processing_delay_ms
) VALUES
    -- VIVO Mock Credentials
    (
        '11111111-1111-1111-1111-111111111111',
        'MOCK_VIVO_MERCHANT_001',
        'mock_vivo_api_key_123456789',
        'mock_vivo_secret_987654321',
        'sofia-vivo-agent',
        'sofIA VIVO Payment Agent',
        '["PIX", "CARD", "BOLETO", "VIVO_WALLET"]',
        0.97,
        1500
    ),

    -- CLARO Mock Credentials
    (
        '22222222-2222-2222-2222-222222222222',
        'MOCK_CLARO_MERCHANT_002',
        'mock_claro_api_key_abcdef123',
        'mock_claro_secret_fedcba987',
        'sofia-claro-agent',
        'sofIA CLARO Payment Agent',
        '["PIX", "CARD", "BOLETO", "CLARO_PAY"]',
        0.94,
        2200
    ),

    -- OI Mock Credentials
    (
        '33333333-3333-3333-3333-333333333333',
        'MOCK_OI_MERCHANT_003',
        'mock_oi_api_key_123abc456',
        'mock_oi_secret_789fed654',
        'sofia-oi-agent',
        'sofIA OI Payment Agent',
        '["PIX", "CARD", "BOLETO", "OI_MONEY"]',
        0.92,
        2500
    ),

    -- TIM Mock Credentials
    (
        '44444444-4444-4444-4444-444444444444',
        'MOCK_TIM_MERCHANT_004',
        'mock_tim_api_key_def789123',
        'mock_tim_secret_321abc654',
        'sofia-tim-agent',
        'sofIA TIM Payment Agent',
        '["PIX", "CARD", "BOLETO", "TIM_PAY"]',
        0.96,
        1800
    );

-- Create indexes
CREATE INDEX idx_merchant_credentials_operator_id ON merchant_credentials(operator_id);
CREATE INDEX idx_merchant_credentials_merchant_id ON merchant_credentials(mock_merchant_id);
CREATE INDEX idx_merchant_credentials_sofia_agent_id ON merchant_credentials(sofia_agent_id);

-- Enable RLS
ALTER TABLE merchant_credentials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access for merchant credentials" ON merchant_credentials FOR SELECT USING (true);

-- Create trigger
CREATE TRIGGER update_merchant_credentials_updated_at BEFORE UPDATE ON merchant_credentials
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- View for easy access
CREATE VIEW merchant_overview AS
SELECT
    o.name as operator_code,
    o.display_name as operator_name,
    mc.mock_merchant_id,
    mc.sofia_agent_id,
    mc.sofia_agent_name,
    mc.supported_payment_methods,
    mc.mock_success_rate,
    mc.mock_processing_delay_ms,
    mc.is_active,
    COUNT(sp.id) as available_plans
FROM merchant_credentials mc
JOIN operators o ON mc.operator_id = o.id
LEFT JOIN subscription_plans sp ON o.id = sp.operator_id AND sp.is_active = true
WHERE mc.is_active = true
GROUP BY o.name, o.display_name, mc.mock_merchant_id, mc.sofia_agent_id,
         mc.sofia_agent_name, mc.supported_payment_methods, mc.mock_success_rate,
         mc.mock_processing_delay_ms, mc.is_active
ORDER BY o.name;