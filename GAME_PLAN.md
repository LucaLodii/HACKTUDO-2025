# sofIA Subscription Management Game Plan

## Overview
Transform sofIA from a payment-only platform to a comprehensive subscription management and renewal orchestration system for BEMOBI's telecom clients (VIVO, CLARO, OI, TIM).

## Core Business Value Proposition

### For BEMOBI
- **Subscription Lifecycle Management**: Automated handling of renewals, upgrades, downgrades
- **Proactive Customer Retention**: AI-driven renewal reminders and personalized offers
- **Reduced Churn**: Smart intervention before subscription expiry
- **Revenue Optimization**: Intelligent upselling and cross-selling opportunities

### For Telecom Operators (VIVO, CLARO, OI, TIM)
- **Customer Retention**: 90%+ reduction in involuntary churn from forgotten renewals
- **Plan Migration**: Seamless plan changes with immediate AP2 payment processing
- **Customer Satisfaction**: Proactive service through WhatsApp conversations
- **Revenue Growth**: Automated upselling to higher-tier plans

### For End Customers
- **Never Miss Renewals**: Timely reminders with one-click renewal via WhatsApp
- **Easy Plan Changes**: Natural language requests for plan upgrades/downgrades
- **Transparent Billing**: Clear information about current plans and upcoming charges
- **Instant Processing**: Immediate plan changes with AP2 payment completion

## Technical Architecture Enhancement

### Current State
- ✅ AP2 Protocol implementation
- ✅ Multi-agent orchestration (A2A)
- ✅ WhatsApp integration
- ✅ Payment processing

### Enhanced Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    sofIA Orchestrator                       │
│                  (Conversation Management)                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌────▼────┐   ┌────▼────┐
│sofIA  │    │Renewal  │   │Plan     │
│Payment│    │Agent    │   │Manager  │
│Agent  │    │         │   │Agent    │
└───┬───┘    └────┬────┘   └────┬────┘
    │             │             │
    │        ┌────▼────┐        │
    │        │Supabase │        │
    │        │Database │        │
    │        └─────────┘        │
    │                           │
┌───▼───────────────────────────▼───┐
│        AP2 Payment Engine         │
│    (Mandate + Transaction)        │
└───────────────────────────────────┘
```

## Data Model Design

### Supabase Schema
```sql
-- Telecom Operators (BEMOBI Clients)
CREATE TABLE operators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL, -- VIVO, CLARO, OI, TIM
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subscription Plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID REFERENCES operators(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL, -- monthly, weekly, daily
    features JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users (End Customers)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Active Subscriptions
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    operator_id UUID REFERENCES operators(id),
    plan_id UUID REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL, -- active, expired, cancelled, pending_renewal
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    auto_renewal BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Payment History
CREATE TABLE subscription_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES user_subscriptions(id),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'BRL',
    status VARCHAR(20) NOT NULL, -- completed, failed, pending
    ap2_mandate_id VARCHAR(100),
    ap2_transaction_id VARCHAR(100),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Renewal Reminders
CREATE TABLE renewal_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES user_subscriptions(id),
    reminder_type VARCHAR(20) NOT NULL, -- 7_day, 3_day, 1_day, expiry
    sent_at TIMESTAMP,
    response VARCHAR(20), -- renewed, declined, no_response
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Agent Capabilities Enhancement

### 1. Subscription Discovery Agent
**Purpose**: Fetch and present user's current subscriptions
**Tools**:
- `get_user_subscriptions(whatsapp_number)`
- `get_subscription_details(subscription_id)`
- `check_subscription_status(subscription_id)`

### 2. Renewal Orchestration Agent  
**Purpose**: Proactive renewal management
**Tools**:
- `check_expiring_subscriptions(days_ahead=7)`
- `send_renewal_reminder(subscription_id, reminder_type)`
- `process_renewal_payment(subscription_id, user_confirmation)`

### 3. Plan Management Agent
**Purpose**: Handle plan changes and upgrades
**Tools**:
- `get_available_plans(operator_id, current_plan_id)`
- `calculate_plan_change_cost(current_plan_id, new_plan_id)`
- `process_plan_change(subscription_id, new_plan_id)`

### 4. Enhanced sofIA Payment Agent
**Purpose**: AP2 payment processing for all subscription operations
**Enhanced Tools**:
- `create_subscription_mandate(user_info, plan_info)`
- `process_subscription_payment(subscription_id, amount)`
- `handle_plan_change_payment(subscription_id, price_difference)`

## Implementation Phases

### Phase 1: Data Foundation (Week 1)
- ✅ Design Supabase schema
- ✅ Create mock data for 4 operators (VIVO, CLARO, OI, TIM)
- ✅ Populate sample subscription plans
- ✅ Create test users with active subscriptions

### Phase 2: Subscription Management Tools (Week 1-2)
- ✅ Implement Supabase integration tools
- ✅ Build subscription discovery capabilities
- ✅ Create plan management tools
- ✅ Test basic CRUD operations

### Phase 3: Renewal Orchestration (Week 2)
- ✅ Build expiration monitoring system
- ✅ Implement reminder scheduling
- ✅ Create renewal payment flow
- ✅ Test proactive reminder system

### Phase 4: Plan Change Engine (Week 2-3)
- ✅ Implement plan comparison tools
- ✅ Build upgrade/downgrade logic
- ✅ Integrate with AP2 payment processing
- ✅ Test plan migration flows

### Phase 5: Integration & Testing (Week 3)
- ✅ End-to-end conversation testing
- ✅ Multi-agent coordination testing
- ✅ WhatsApp integration validation
- ✅ Performance and security testing

## Conversation Flow Examples

### Scenario 1: Renewal Reminder
```
Agent: Hi João! Your VIVO plan (Premium Data 10GB) expires in 3 days. 
       Would you like to renew it for R$ 49.90/month?

User: Yes, renew it

Agent: Perfect! I'll process the renewal payment now.
       [AP2 Payment Processing]
       ✅ Payment successful! Your VIVO Premium Data plan is renewed until 2025-11-27.
```

### Scenario 2: Plan Upgrade
```
User: I want to upgrade my Claro plan

Agent: You currently have Claro Basic (5GB) for R$ 29.90/month.
       Here are your upgrade options:
       
       📱 Claro Premium (10GB) - R$ 49.90/month (+R$ 20.00)
       📱 Claro Ultimate (20GB) - R$ 79.90/month (+R$ 50.00)
       
       Which would you prefer?

User: The Premium one

Agent: Great choice! The upgrade will cost an additional R$ 20.00.
       Your new plan starts immediately. Confirm payment?

User: Yes

Agent: [AP2 Payment Processing]
       ✅ Plan upgraded successfully! You now have Claro Premium (10GB).
```

### Scenario 3: Multi-Plan Management
```
User: What are my current plans?

Agent: Here are your active subscriptions:
       
       📱 VIVO Premium Data (10GB) - Expires: 2025-11-27
       📺 TIM TV Plus - Expires: 2025-12-15
       🎵 OI Music Streaming - Expires: 2025-11-30
       
       The OI Music plan expires in 4 days. Would you like to renew it?

User: Yes, but upgrade to the premium music plan

Agent: Perfect! I'll upgrade your OI Music to Premium (unlimited streaming + downloads).
       New price: R$ 19.90/month (+R$ 5.00 from current plan).
       
       Processing upgrade and renewal...
       ✅ Done! OI Music Premium renewed until 2025-12-30.
```

## Success Metrics

### Technical KPIs
- **Renewal Rate**: 95%+ of reminded users complete renewal
- **Response Time**: < 3 seconds for subscription queries
- **Payment Success**: 99%+ AP2 payment completion rate
- **Data Accuracy**: 100% sync between Supabase and agent responses

### Business KPIs
- **Churn Reduction**: 80% reduction in involuntary churn
- **Upsell Success**: 25% of users upgrade when presented with options
- **Customer Satisfaction**: 4.8+ rating for subscription management
- **Revenue Growth**: 35% increase in customer lifetime value

## Risk Mitigation

### Technical Risks
- **Database Performance**: Implement proper indexing and caching
- **AP2 Integration**: Robust error handling for payment failures
- **WhatsApp Limits**: Respect rate limits and message quotas

### Business Risks
- **User Privacy**: Implement LGPD-compliant data handling
- **Subscription Complexity**: Clear communication of plan changes
- **Payment Failures**: Graceful handling with retry mechanisms

This enhanced sofIA platform positions BEMOBI as the leading subscription orchestration provider in LATAM, combining AI conversation management with robust AP2 payment processing.
