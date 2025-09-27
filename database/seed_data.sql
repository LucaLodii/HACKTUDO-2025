-- sofIA Subscription Management Seed Data
-- Mock data for BEMOBI telecom operators and subscription plans

-- Clear existing data
TRUNCATE TABLE renewal_reminders CASCADE;
TRUNCATE TABLE subscription_payments CASCADE;
TRUNCATE TABLE user_subscriptions CASCADE;
TRUNCATE TABLE subscription_plans CASCADE;
TRUNCATE TABLE operators CASCADE;
TRUNCATE TABLE users CASCADE;

-- Insert Brazilian Telecom Operators
INSERT INTO operators (id, name, display_name, logo_url, brand_color, is_active) VALUES
    ('11111111-1111-1111-1111-111111111111', 'VIVO', 'Vivo', 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Vivo_logo.svg/200px-Vivo_logo.svg.png', '#8B2797', true),
    ('22222222-2222-2222-2222-222222222222', 'CLARO', 'Claro', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Claro.svg/200px-Claro.svg.png', '#E61E24', true),
    ('33333333-3333-3333-3333-333333333333', 'OI', 'Oi', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Oi_logo.svg/200px-Oi_logo.svg.png', '#F9B233', true),
    ('44444444-4444-4444-4444-444444444444', 'TIM', 'TIM', 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/TIM_logo_2016.svg/200px-TIM_logo_2016.svg.png', '#1E3A96', true);

-- Insert VIVO Subscription Plans
INSERT INTO subscription_plans (id, operator_id, plan_code, name, description, price_cents, billing_cycle, data_limit_gb, voice_minutes, sms_count, features, can_upgrade_to, can_downgrade_to) VALUES
    -- VIVO Plans
    ('vivo-001', '11111111-1111-1111-1111-111111111111', 'VIVO_BASIC_5GB', 'Vivo Basic 5GB', 'Plano básico com 5GB de internet, ligações ilimitadas e 100 SMS', 2990, 'monthly', 5, -1, 100, '{"unlimited_calls": true, "whatsapp_free": true, "social_media_free": false}', '["vivo-002", "vivo-003"]', '[]'),
    ('vivo-002', '11111111-1111-1111-1111-111111111111', 'VIVO_PREMIUM_10GB', 'Vivo Premium 10GB', 'Plano premium com 10GB de internet, ligações ilimitadas e SMS ilimitados', 4990, 'monthly', 10, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true}', '["vivo-003", "vivo-004"]', '["vivo-001"]'),
    ('vivo-003', '11111111-1111-1111-1111-111111111111', 'VIVO_ULTIMATE_20GB', 'Vivo Ultimate 20GB', 'Plano ultimate com 20GB de internet, ligações e SMS ilimitados, apps grátis', 7990, 'monthly', 20, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "streaming_free": true}', '["vivo-004"]', '["vivo-001", "vivo-002"]'),
    ('vivo-004', '11111111-1111-1111-1111-111111111111', 'VIVO_INFINITY_50GB', 'Vivo Infinity 50GB', 'Plano infinity com 50GB de internet, tudo ilimitado e apps premium', 12990, 'monthly', 50, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "streaming_free": true, "gaming_free": true}', '[]', '["vivo-001", "vivo-002", "vivo-003"]'),

    -- CLARO Plans
    ('claro-001', '22222222-2222-2222-2222-222222222222', 'CLARO_EASY_3GB', 'Claro Easy 3GB', 'Plano econômico com 3GB de internet e ligações limitadas', 1990, 'monthly', 3, 300, 50, '{"unlimited_calls": false, "whatsapp_free": true}', '["claro-002", "claro-003"]', '[]'),
    ('claro-002', '22222222-2222-2222-2222-222222222222', 'CLARO_SMART_8GB', 'Claro Smart 8GB', 'Plano inteligente com 8GB de internet e ligações ilimitadas', 3990, 'monthly', 8, -1, 200, '{"unlimited_calls": true, "whatsapp_free": true, "social_media_free": true}', '["claro-003", "claro-004"]', '["claro-001"]'),
    ('claro-003', '22222222-2222-2222-2222-222222222222', 'CLARO_POWER_15GB', 'Claro Power 15GB', 'Plano poderoso com 15GB de internet e recursos premium', 6990, 'monthly', 15, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "netflix_included": true}', '["claro-004"]', '["claro-001", "claro-002"]'),
    ('claro-004', '22222222-2222-2222-2222-222222222222', 'CLARO_UNLIMITED', 'Claro Unlimited', 'Plano ilimitado com 30GB e todos os benefícios', 9990, 'monthly', 30, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "netflix_included": true, "spotify_included": true}', '[]', '["claro-001", "claro-002", "claro-003"]'),

    -- OI Plans
    ('oi-001', '33333333-3333-3333-3333-333333333333', 'OI_SIMPLES_2GB', 'Oi Simples 2GB', 'Plano simples com 2GB de internet básica', 1590, 'monthly', 2, 200, 30, '{"unlimited_calls": false, "whatsapp_free": true}', '["oi-002", "oi-003"]', '[]'),
    ('oi-002', '33333333-3333-3333-3333-333333333333', 'OI_CONECTA_6GB', 'Oi Conecta 6GB', 'Plano conectado com 6GB de internet e apps grátis', 2990, 'monthly', 6, -1, 150, '{"unlimited_calls": true, "whatsapp_free": true, "social_media_free": true}', '["oi-003", "oi-004"]', '["oi-001"]'),
    ('oi-003', '33333333-3333-3333-3333-333333333333', 'OI_TOTAL_12GB', 'Oi Total 12GB', 'Plano total com 12GB de internet e entretenimento', 5990, 'monthly', 12, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "music_streaming": true}', '["oi-004"]', '["oi-001", "oi-002"]'),
    ('oi-004', '33333333-3333-3333-3333-333333333333', 'OI_PREMIUM_25GB', 'Oi Premium 25GB', 'Plano premium com 25GB e benefícios exclusivos', 8990, 'monthly', 25, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "music_streaming": true, "video_streaming": true}', '[]', '["oi-001", "oi-002", "oi-003"]'),

    -- TIM Plans
    ('tim-001', '44444444-4444-4444-4444-444444444444', 'TIM_LIGHT_4GB', 'TIM Light 4GB', 'Plano leve com 4GB de internet e comunicação básica', 2490, 'monthly', 4, 250, 80, '{"unlimited_calls": false, "whatsapp_free": true, "social_media_free": false}', '["tim-002", "tim-003"]', '[]'),
    ('tim-002', '44444444-4444-4444-4444-444444444444', 'TIM_FLEX_9GB', 'TIM Flex 9GB', 'Plano flexível com 9GB de internet e apps inclusos', 4490, 'monthly', 9, -1, 300, '{"unlimited_calls": true, "whatsapp_free": true, "social_media_free": true, "telegram_free": true}', '["tim-003", "tim-004"]', '["tim-001"]'),
    ('tim-003', '44444444-4444-4444-4444-444444444444', 'TIM_BLACK_18GB', 'TIM Black 18GB', 'Plano black com 18GB e entretenimento premium', 7490, 'monthly', 18, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "netflix_tim": true, "paramount_plus": true}', '["tim-004"]', '["tim-001", "tim-002"]'),
    ('tim-004', '44444444-4444-4444-4444-444444444444', 'TIM_BLACK_FAMILIA_60GB', 'TIM Black Família 60GB', 'Plano família com 60GB compartilhados e benefícios completos', 11990, 'monthly', 60, -1, -1, '{"unlimited_calls": true, "unlimited_sms": true, "whatsapp_free": true, "social_media_free": true, "netflix_tim": true, "paramount_plus": true, "deezer_premium": true, "family_sharing": true}', '[]', '["tim-001", "tim-002", "tim-003"]');

-- Insert Sample Users
INSERT INTO users (id, whatsapp_number, full_name, email, preferred_language, timezone) VALUES
    ('user-001', '+5511999887766', 'João Silva Santos', 'joao.silva@email.com', 'pt-BR', 'America/Sao_Paulo'),
    ('user-002', '+5511888776655', 'Maria Oliveira Costa', 'maria.oliveira@email.com', 'pt-BR', 'America/Sao_Paulo'),
    ('user-003', '+5511777665544', 'Carlos Eduardo Lima', 'carlos.lima@email.com', 'pt-BR', 'America/Sao_Paulo'),
    ('user-004', '+5511666554433', 'Ana Paula Ferreira', 'ana.ferreira@email.com', 'pt-BR', 'America/Sao_Paulo'),
    ('user-005', '+5511555443322', 'Roberto Machado', 'roberto.machado@email.com', 'pt-BR', 'America/Sao_Paulo');

-- Insert Sample Active Subscriptions
INSERT INTO user_subscriptions (id, user_id, operator_id, plan_id, subscription_external_id, status, start_date, end_date, auto_renewal) VALUES
    -- João Silva Santos - VIVO Premium (expires in 3 days)
    ('sub-001', 'user-001', '11111111-1111-1111-1111-111111111111', 'vivo-002', 'VIVO_SUB_001', 'active', NOW() - INTERVAL '27 days', NOW() + INTERVAL '3 days', true),
    
    -- Maria Oliveira Costa - CLARO Smart (expires in 7 days)  
    ('sub-002', 'user-002', '22222222-2222-2222-2222-222222222222', 'claro-002', 'CLARO_SUB_002', 'active', NOW() - INTERVAL '23 days', NOW() + INTERVAL '7 days', true),
    
    -- Carlos Eduardo Lima - TIM Black (expires in 15 days)
    ('sub-003', 'user-003', '44444444-4444-4444-4444-444444444444', 'tim-003', 'TIM_SUB_003', 'active', NOW() - INTERVAL '15 days', NOW() + INTERVAL '15 days', true),
    
    -- Ana Paula Ferreira - OI Total (expires in 1 day - urgent!)
    ('sub-004', 'user-004', '33333333-3333-3333-3333-333333333333', 'oi-003', 'OI_SUB_004', 'active', NOW() - INTERVAL '29 days', NOW() + INTERVAL '1 day', true),
    
    -- Roberto Machado - Multiple subscriptions
    ('sub-005', 'user-005', '11111111-1111-1111-1111-111111111111', 'vivo-001', 'VIVO_SUB_005', 'active', NOW() - INTERVAL '10 days', NOW() + INTERVAL '20 days', true),
    ('sub-006', 'user-005', '44444444-4444-4444-4444-444444444444', 'tim-002', 'TIM_SUB_006', 'active', NOW() - INTERVAL '5 days', NOW() + INTERVAL '25 days', false); -- Auto-renewal disabled

-- Insert Sample Payment History
INSERT INTO subscription_payments (id, subscription_id, payment_type, amount_cents, currency, status, payment_method, ap2_mandate_id, ap2_transaction_id, gateway_transaction_id, processed_at) VALUES
    -- Recent successful payments
    ('pay-001', 'sub-001', 'renewal', 4990, 'BRL', 'completed', 'PIX', 'ap2_mandate_001', 'ap2_txn_001', 'vivo_gw_001', NOW() - INTERVAL '27 days'),
    ('pay-002', 'sub-002', 'renewal', 3990, 'BRL', 'completed', 'CARD', 'ap2_mandate_002', 'ap2_txn_002', 'claro_gw_002', NOW() - INTERVAL '23 days'),
    ('pay-003', 'sub-003', 'renewal', 7490, 'BRL', 'completed', 'PIX', 'ap2_mandate_003', 'ap2_txn_003', 'tim_gw_003', NOW() - INTERVAL '15 days'),
    ('pay-004', 'sub-004', 'renewal', 5990, 'BRL', 'completed', 'BOLETO', 'ap2_mandate_004', 'ap2_txn_004', 'oi_gw_004', NOW() - INTERVAL '29 days'),
    ('pay-005', 'sub-005', 'initial', 2990, 'BRL', 'completed', 'PIX', 'ap2_mandate_005', 'ap2_txn_005', 'vivo_gw_005', NOW() - INTERVAL '10 days'),
    ('pay-006', 'sub-006', 'initial', 4490, 'BRL', 'completed', 'CARD', 'ap2_mandate_006', 'ap2_txn_006', 'tim_gw_006', NOW() - INTERVAL '5 days'),
    
    -- Some failed payments for testing
    ('pay-007', 'sub-001', 'upgrade', 2000, 'BRL', 'failed', 'CARD', 'ap2_mandate_007', 'ap2_txn_007', 'vivo_gw_007', NOW() - INTERVAL '5 days'),
    ('pay-008', 'sub-002', 'renewal', 3990, 'BRL', 'pending', 'PIX', 'ap2_mandate_008', NULL, NULL, NULL);

-- Insert Sample Renewal Reminders
INSERT INTO renewal_reminders (id, subscription_id, reminder_type, scheduled_for, sent_at, message_id, user_response, response_received_at) VALUES
    -- Already sent reminders
    ('reminder-001', 'sub-001', '7_day', NOW() - INTERVAL '4 days', NOW() - INTERVAL '4 days', 'wa_msg_001', 'ignored', NULL),
    ('reminder-002', 'sub-002', '7_day', NOW(), NOW() - INTERVAL '1 hour', 'wa_msg_002', 'deferred', NOW() - INTERVAL '30 minutes'),
    ('reminder-003', 'sub-004', '3_day', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', 'wa_msg_003', 'ignored', NULL),
    ('reminder-004', 'sub-004', '1_day', NOW(), NOW() - INTERVAL '2 hours', 'wa_msg_004', NULL, NULL),
    
    -- Scheduled reminders (not sent yet)
    ('reminder-005', 'sub-001', '3_day', NOW() + INTERVAL '6 hours', NULL, NULL, NULL, NULL),
    ('reminder-006', 'sub-003', '7_day', NOW() + INTERVAL '8 days', NULL, NULL, NULL, NULL),
    ('reminder-007', 'sub-005', '7_day', NOW() + INTERVAL '13 days', NULL, NULL, NULL, NULL);

-- Update sequences to avoid conflicts
SELECT setval('operators_id_seq', (SELECT MAX(id) FROM operators) + 1, false);
SELECT setval('subscription_plans_id_seq', (SELECT MAX(id) FROM subscription_plans) + 1, false);
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users) + 1, false);
SELECT setval('user_subscriptions_id_seq', (SELECT MAX(id) FROM user_subscriptions) + 1, false);
SELECT setval('subscription_payments_id_seq', (SELECT MAX(id) FROM subscription_payments) + 1, false);
SELECT setval('renewal_reminders_id_seq', (SELECT MAX(id) FROM renewal_reminders) + 1, false);

-- Verification queries
SELECT 'Operators Count' as metric, COUNT(*) as value FROM operators
UNION ALL
SELECT 'Subscription Plans Count', COUNT(*) FROM subscription_plans
UNION ALL  
SELECT 'Users Count', COUNT(*) FROM users
UNION ALL
SELECT 'Active Subscriptions Count', COUNT(*) FROM user_subscriptions WHERE status = 'active'
UNION ALL
SELECT 'Completed Payments Count', COUNT(*) FROM subscription_payments WHERE status = 'completed'
UNION ALL
SELECT 'Scheduled Reminders Count', COUNT(*) FROM renewal_reminders WHERE sent_at IS NULL;

-- Show subscriptions expiring in the next 7 days
SELECT 
    u.full_name,
    u.whatsapp_number,
    o.display_name as operator,
    sp.name as plan,
    us.end_date,
    us.end_date - NOW() as time_until_expiry
FROM user_subscriptions us
JOIN users u ON us.user_id = u.id
JOIN operators o ON us.operator_id = o.id
JOIN subscription_plans sp ON us.plan_id = sp.id
WHERE us.status = 'active'
AND us.end_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
ORDER BY us.end_date ASC;
