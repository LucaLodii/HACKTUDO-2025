# sofIA Multi-Agent Payment System - Product Requirements Document (PRD)

## Executive Summary

**Product Name:** sofIA (Smart Orchestrated Financial Intelligence Agent)  
**Target Customer:** BEMOBI (Mobile Payment Gateway Provider)  
**Hackathon Project:** HACKTUDO 2025  
**Protocol Compliance:** [AP2 (Agent Payments Protocol)](https://github.com/google-agentic-commerce/AP2)  
**Delivery Channel:** WhatsApp Business Integration  
**Core Business Model:** Multi-Agent Payment Orchestration Platform

sofIA is a revolutionary multi-agent payment orchestration system that enables BEMOBI's merchants across LATAM, Africa, and Asia to process secure, conversational payments through WhatsApp. The system implements Google's AP2 Protocol for cryptographic mandate verification, combining intelligent conversation management, automated payment processing, and seamless merchant integration with real-time payment gateway operations.

---

## 1. Product Intent & Vision

### 1.1 Problem Statement
BEMOBI's merchants across LATAM, Africa, and Asia face significant challenges in payment processing:
- **High Checkout Abandonment**: 70-80% of customers abandon traditional checkout processes
- **Complex Payment Integration**: Technical barriers prevent SMBs from implementing modern payment solutions
- **Fragmented Customer Experience**: Multiple touchpoints for payment operations across different systems
- **Limited Conversational Commerce**: No natural language payment processing capabilities
- **Regional Payment Complexity**: Difficult to support diverse payment methods across different markets
- **Security Concerns**: Merchants struggle with PCI compliance and fraud prevention
- **Support Overhead**: High customer support costs for payment-related inquiries

### 1.2 Solution Vision
sofIA creates a **"Conversational Payment Revolution"** where:
- Customers complete purchases through natural WhatsApp conversations without app downloads
- AI agents handle complete payment flows with AP2-compliant security
- Multi-agent orchestration enables seamless merchant integration across regions
- AP2 Protocol ensures cryptographic mandate verification and audit trails
- Regional payment methods are automatically routed through BEMOBI's gateway
- Merchants get instant setup with minimal technical requirements
- BEMOBI becomes the leading conversational commerce platform for emerging markets

### 1.3 Value Proposition
**For BEMOBI:**
- New revenue stream through WhatsApp commerce platform
- Competitive differentiation in conversational payments
- Reduced support costs through automated AI agent interactions
- Enhanced merchant acquisition through superior payment UX

**For BEMOBI's Merchants:**
- 90%+ reduction in checkout abandonment through WhatsApp integration
- AP2-compliant security and audit trails for all transactions
- Native WhatsApp integration without technical complexity
- Automated customer service through AI agents
- Multi-region payment method support

**For End Customers:**
- Seamless purchase experience within WhatsApp without app downloads
- Secure transactions with AP2 protocol and cryptographic signatures
- Natural language payment processing
- Instant payment confirmation and real-time status updates
- No complex interfaces or technical knowledge required

---

## 2. Product Requirements

### 2.1 Functional Requirements

#### 2.1.1 Core Multi-Agent Architecture
- **Orchestrator Agent**: Manages conversation flow, intent detection, and coordinates specialized tools
- **sofIA Agent**: Handles AP2 protocol compliance, payment processing, and transaction orchestration
- **Payment Processing Tool**: Comprehensive payment flow management and transaction processing
- **Merchant Management Tool**: Handles merchant onboarding, configuration, and payment method setup
- **Regional Payment Tool**: Manages region-specific payment methods and currency conversion
- **AP2 Protocol Tools**: Complete AP2 implementation for secure payment mandates
- **BEMOBI Integration Tool**: Manages payment gateway operations and webhook handling
- **WhatsApp Integration**: Node.js bridge using WhatsApp Web.js for message handling

#### 2.1.2 AP2 Protocol Compliance
- **Intent Mandates**: Capture user purchase intent with natural language processing
- **Cart Mandates**: Create cryptographically signed payment carts with product details
- **Payment Mandates**: Execute payments with full audit trails and mandate verification
- **Signature Verification**: RSA-2048 digital signatures for all payment transactions
- **Credential Management**: Verifiable credentials for user authorization and payment ownership
- **Transaction Ledger**: Complete audit trail of all payment operations and transactions

#### 2.1.3 WhatsApp Integration
- **Natural Language Processing**: Understand payment intents in multiple languages
- **Conversation Management**: Maintain context across multi-turn payment conversations
- **Rich Media Support**: Handle product images, documents, and payment confirmations
- **Proactive Messaging**: Send payment confirmations and transaction updates
- **Real-time Messaging**: Instant response and payment status updates
- **Session Persistence**: Maintain user payment context across conversations

#### 2.1.4 BEMOBI Payment Gateway Integration
- **Multi-Merchant Support**: Handle multiple merchants across LATAM, Africa, and Asia simultaneously
- **Merchant Configuration**: Sync and manage merchant settings and payment methods
- **Regional Compliance**: Support local financial regulations and payment methods
- **Currency Support**: Handle BRL, NGN, THB, USD, and 15+ regional currencies
- **Payment Method Variety**: Support PIX, cards, Boleto, Mobile Money, Digital Wallets
- **Webhook Integration**: Real-time payment status updates and transaction confirmations

#### 2.1.5 Payment Processing Capabilities
- **Transaction Processing**: Real-time payment processing with AP2 mandate verification
- **Payment Method Detection**: Automatic detection and routing of regional payment methods
- **Currency Conversion**: Real-time currency conversion for multi-region transactions
- **Fraud Detection**: AI-powered fraud detection and risk assessment
- **Payment Confirmation**: Instant payment confirmations with transaction details
- **Multi-Merchant Support**: Handle payments across multiple merchants simultaneously
- **Refund Processing**: Automated refund processing with AP2 compliance
- **Transaction Analytics**: Track payment patterns and success rates for optimization

#### 2.1.6 Agent-to-Agent Communication (A2A)
- **Structured A2A Messages**: Standardized communication between payment processing agents
- **Context Preservation**: Maintain payment and user context across agent interactions
- **Error Handling**: Graceful failure recovery and retry mechanisms for payment operations
- **Audit Logging**: Complete trail of all A2A communications and payment transactions

### 2.2 Non-Functional Requirements

#### 2.2.1 Performance
- **Response Time**: < 2 seconds for agent responses
- **Throughput**: Support 1000+ concurrent conversations
- **Availability**: 99.9% uptime for payment processing
- **Scalability**: Auto-scale based on demand

#### 2.2.2 Security
- **AP2 Protocol Security**: Full cryptographic mandate verification
- **Data Encryption**: End-to-end encryption for all sensitive data
- **Access Control**: Role-based access for different agent types
- **Audit Compliance**: Complete transaction audit trails
- **Fraud Prevention**: Real-time fraud detection and prevention

#### 2.2.3 Reliability
- **Fault Tolerance**: Graceful handling of agent failures
- **Data Consistency**: Ensure transaction integrity across agents
- **Backup & Recovery**: Automated backup and disaster recovery
- **Monitoring**: Real-time system health monitoring

#### 2.2.4 Compliance
- **AP2 Protocol**: Full compliance with Google's Agent Payments Protocol
- **PCI DSS**: Payment card industry security standards
- **Regional Regulations**: Compliance with local financial regulations
- **Data Privacy**: GDPR and regional privacy law compliance

---

## 3. Technical Architecture

### 3.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    WhatsApp Interface                       │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │   WhatsApp  │◄──►│ Node.js      │◄──►│ Python      │   │
│  │   Web.js    │    │ Bridge       │    │ sofIA API   │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Multi-Agent Orchestration Layer              │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │ Orchestrator│◄──►│ sofIA Payment│◄──►│ BEMOBI      │   │
│  │ Agent       │    │ Agent        │    │ Integration │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AP2 Protocol Layer                       │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │ Intent      │    │ Cart         │    │ Payment     │   │
│  │ Mandates    │    │ Mandates     │    │ Mandates    │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   BEMOBI Payment Gateway                    │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │ LATAM       │    │ Africa       │    │ Asia        │   │
│  │ Merchants   │    │ Merchants    │    │ Merchants   │   │
│  └─────────────┘    └──────────────┘    └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Architecture

#### 3.2.1 Orchestrator Agent
- **Role**: Main conversation coordinator and tool orchestrator
- **Technology**: Google ADK with Gemini 2.5 Flash
- **Responsibilities**:
  - Natural language understanding and intent detection
  - Subscription-related conversation management
  - Tool coordination for subscription operations
  - Session state management and user context preservation

#### 3.2.2 sofIA Agent
- **Role**: Subscription operations and AP2 Protocol compliance
- **Technology**: Google ADK with specialized subscription and AP2 tools
- **Responsibilities**:
  - Subscription management tool integration
  - Plan management and migration orchestration
  - Renewal orchestration and automated processing
  - AP2 mandate creation for subscription-related payments
  - Cryptographic signature generation and verification

#### 3.2.3 Subscription Management Tool
- **Role**: Complete subscription lifecycle management
- **Technology**: Python with Supabase integration
- **Responsibilities**:
  - User subscription discovery across operators
  - Subscription status monitoring and expiration tracking
  - Multi-operator subscription data synchronization
  - Subscription details and history management

#### 3.2.4 Plan Management Tool
- **Role**: Subscription plan operations and migration
- **Technology**: Python with Supabase and AP2 integration
- **Responsibilities**:
  - Plan comparison and cost calculation
  - Upgrade/downgrade validation and processing
  - Prorated cost calculations for plan changes
  - Plan recommendation engine based on usage patterns

#### 3.2.5 Renewal Orchestration Tool
- **Role**: Proactive renewal management and automation
- **Technology**: Python with Supabase and messaging integration
- **Responsibilities**:
  - Expiration monitoring and renewal queue management
  - Intelligent reminder scheduling (7-day, 3-day, 1-day alerts)
  - Personalized renewal message generation
  - Renewal response processing and follow-up automation

#### 3.2.6 WhatsApp Integration
- **Role**: WhatsApp Web.js bridge communication
- **Technology**: Node.js with WhatsApp Web.js library
- **Responsibilities**:
  - Message sending and receiving via WhatsApp Web
  - Personal WhatsApp account integration (no Business API required)
  - Real-time message processing and response delivery
  - Session management and QR code authentication

### 3.3 AP2 Protocol Implementation

#### 3.3.1 Mandate Types
1. **Intent Mandate**: Captures user purchase intent with natural language authorization
2. **Cart Mandate**: Cryptographically signed merchant cart with guaranteed pricing
3. **Payment Mandate**: User-authorized payment with complete audit trail

#### 3.3.2 Security Features
- **RSA-2048 Digital Signatures**: All mandates cryptographically signed
- **JWT Tokens**: Time-limited authorization tokens (15-minute cart expiry)
- **Verifiable Credentials**: Non-repudiable user authorization
- **Audit Trails**: Complete transaction history with timestamps

#### 3.3.3 Agent-to-Agent Communication
- **Structured Messages**: JSON-based A2A message format
- **Context Preservation**: Transaction context maintained across agents
- **Error Handling**: Graceful failure recovery and retry logic
- **Logging**: Complete A2A communication audit trail

---

## 4. User Experience Flow

### 4.1 Customer Journey

#### 4.1.1 Product Discovery
```
Customer: "I want to buy a coffee"
Orchestrator Agent: Analyzes intent → Uses payment_processing_tool
Payment Processing Tool: Fetches product catalog and pricing
Response: "☕ Great! Here are our coffee options:

🟢 Espresso - R$ 8,90
🟢 Cappuccino - R$ 12,90
🟢 Latte - R$ 14,90

Which would you like to order?"
```

#### 4.1.2 Payment Processing
```
Customer: "I'll take the cappuccino"
sofIA Agent: Creates AP2 Intent Mandate
Response: "☕ Cappuccino - R$ 12,90

💳 How would you like to pay?
• PIX (instant)
• Credit Card
• Boleto

Please choose your payment method."

Customer: "PIX"
sofIA Agent: Creates AP2 Cart Mandate with PIX details
Response: "🔐 Creating secure payment mandate...
✅ PIX payment ready! Please complete in your banking app."
```

#### 4.1.3 Payment Confirmation
```
Customer: "Payment completed"
BEMOBI Integration Tool: Verifies payment with gateway
sofIA Agent: Creates AP2 Payment Mandate
Response: "✅ Payment confirmed!
🔐 Processed via AP2 Protocol
☕ Your cappuccino will be ready in 5 minutes
📱 Order #12345 - Thank you!"
```

### 4.2 Merchant Configuration

#### 4.2.1 BEMOBI Merchant Onboarding
- **Merchant Registration**: Simple form-based merchant setup
- **Payment Method Configuration**: Enable/disable payment methods per region
- **Product Catalog Integration**: Connect existing product databases
- **Webhook Configuration**: Set up real-time transaction notifications

#### 4.2.2 Regional Customization
- **LATAM**: PIX, Boleto, Credit/Debit Cards
- **Africa**: Bank transfers, Mobile money, Cards
- **Asia**: Local payment methods, Digital wallets, Cards

---

## 5. Implementation Roadmap

### 5.1 Phase 1: Core AP2 Implementation (Week 1-2)
- [x] AP2 Protocol core implementation
- [x] Orchestrator and sofIA agent architecture
- [x] WhatsApp Web.js bridge integration
- [x] Multi-agent orchestration framework
- [x] Basic payment processing tool
- [x] BEMOBI integration tool foundation
- [x] Mock data integration for testing

### 5.2 Phase 2: BEMOBI Integration (Week 3-4)
- [ ] BEMOBI API integration tool development
- [ ] Multi-merchant configuration system
- [ ] Regional payment method routing
- [ ] Webhook handling and status updates
- [ ] Merchant onboarding flow
- [ ] Multi-language support (Portuguese/English/Spanish)
- [ ] Payment analytics and reporting

### 5.3 Phase 3: Production Readiness (Week 5-6)
- [ ] WhatsApp Business API integration (upgrade from Web.js)
- [ ] Advanced security hardening and AP2 compliance testing
- [ ] Performance optimization for payment processing
- [ ] Comprehensive monitoring and alerting system
- [ ] Payment data backup and recovery systems
- [ ] BEMOBI merchant pilot program setup

### 5.4 Phase 4: Scale and Launch (Week 7-8)
- [ ] Multi-region deployment across LATAM, Africa, Asia
- [ ] Merchant training and integration support
- [ ] Customer onboarding and migration tools
- [ ] Advanced analytics dashboard for merchants
- [ ] Go-to-market strategy execution with BEMOBI
- [ ] Post-launch payment optimization and fraud prevention

---

## 6. Technical Specifications

### 6.1 Technology Stack

#### 6.1.1 Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI for REST API
- **Agent Framework**: Google ADK (Agent Development Kit)
- **AI Model**: Gemini 2.5 Flash
- **Package Manager**: uv for dependency management

#### 6.1.2 WhatsApp Integration
- **Bridge**: Node.js with WhatsApp Web.js
- **Communication**: HTTP REST API between bridge and Python backend
- **Session Management**: In-memory with Redis for production

#### 6.1.3 AP2 Protocol
- **Implementation**: Custom Python implementation following AP2 specification
- **Cryptography**: RSA-2048 for digital signatures
- **Tokens**: JWT for authorization tokens
- **Storage**: JSON-based mandate storage with encryption

#### 6.1.4 Database & Storage
- **Database**: Supabase (PostgreSQL) for subscription data management
- **Tables**: users, operators, subscription_plans, user_subscriptions, renewal_reminders, subscription_payments
- **Real-time**: Supabase real-time subscriptions for live data updates
- **Authentication**: Supabase Auth for user management and session handling
- **API**: Supabase REST API and PostgreSQL functions for complex queries

#### 6.1.5 BEMOBI Integration
- **Payment Gateway**: BEMOBI API integration for telecom operator payments
- **Authentication**: API key-based authentication with fallback to mock mode
- **Webhook Handling**: Real-time payment status updates and subscription confirmations
- **Error Handling**: Comprehensive error handling with retry logic and graceful degradation

### 6.2 Infrastructure Requirements

#### 6.2.1 Development Environment
- **Local Development**: Docker Compose setup
- **Testing**: pytest with comprehensive test coverage
- **Code Quality**: Black, flake8, mypy for code standards
- **Documentation**: Sphinx for API documentation

#### 6.2.2 Production Environment
- **Containerization**: Docker containers for all services
- **Orchestration**: Kubernetes for production deployment
- **Load Balancing**: Nginx for request routing
- **Monitoring**: Prometheus and Grafana for metrics
- **Logging**: Structured logging with ELK stack

#### 6.2.3 Security Infrastructure
- **SSL/TLS**: End-to-end encryption for all communications
- **Secrets Management**: HashiCorp Vault for API keys and certificates
- **Network Security**: VPC with private subnets
- **Access Control**: RBAC with multi-factor authentication

---

## 7. Business Model & Monetization

### 7.1 Revenue Streams for BEMOBI

#### 7.1.1 Platform Licensing
- **Setup Fee**: One-time setup fee for sofIA platform integration
- **Monthly Subscription**: Tiered pricing based on transaction volume
- **Per-Transaction Fee**: Small percentage fee on each processed transaction

#### 7.1.2 Value-Added Services
- **Merchant Onboarding**: Professional services for merchant setup
- **Custom Integration**: Tailored integration for large merchants
- **Support & Training**: Premium support and training packages
- **Analytics & Reporting**: Advanced analytics and reporting dashboards

### 7.2 Pricing Strategy

#### 7.2.1 Tiered Pricing Model
- **Starter**: Up to 1,000 transactions/month - $99/month
- **Professional**: Up to 10,000 transactions/month - $499/month
- **Enterprise**: Unlimited transactions - Custom pricing

#### 7.2.2 Transaction Fees
- **Standard**: 2.9% + $0.30 per transaction
- **High-Volume**: Volume discounts for 10,000+ transactions/month
- **Regional**: Custom rates for specific regions (LATAM, Africa, Asia)

---

## 8. Risk Assessment & Mitigation

### 8.1 Technical Risks

#### 8.1.1 AP2 Protocol Compliance
- **Risk**: AP2 specification changes or compliance issues
- **Mitigation**: Continuous monitoring of AP2 updates, comprehensive testing
- **Contingency**: Fallback to standard payment protocols if needed

#### 8.1.2 WhatsApp API Changes
- **Risk**: WhatsApp Web.js API changes or restrictions
- **Mitigation**: Official WhatsApp Business API integration as backup
- **Contingency**: Alternative messaging platforms (Telegram, Signal)

#### 8.1.3 BEMOBI API Dependencies
- **Risk**: BEMOBI API changes or downtime
- **Mitigation**: Robust error handling, multiple API endpoints
- **Contingency**: Direct payment gateway integrations as backup

### 8.2 Business Risks

#### 8.2.1 Market Adoption
- **Risk**: Slow adoption by BEMOBI's merchant base
- **Mitigation**: Comprehensive pilot program, merchant incentives
- **Contingency**: Direct-to-merchant sales strategy

#### 8.2.2 Regulatory Compliance
- **Risk**: Changes in financial regulations across regions
- **Mitigation**: Legal review in all target regions, compliance monitoring
- **Contingency**: Region-specific compliance adaptations

#### 8.2.3 Competition
- **Risk**: Competitors launching similar solutions
- **Mitigation**: First-mover advantage, continuous innovation
- **Contingency**: Focus on AP2 protocol compliance as differentiator

---

## 9. Success Metrics & KPIs

### 9.1 Technical Metrics
- **System Uptime**: 99.9% availability target
- **Response Time**: < 2 seconds average response time
- **Error Rate**: < 0.1% transaction failure rate
- **AP2 Compliance**: 100% mandate verification success rate

### 9.2 Business Metrics
- **Merchant Adoption**: 50+ merchants onboarded in first 6 months
- **Transaction Volume**: $1M+ monthly processed transactions
- **Checkout Abandonment Reduction**: 90%+ reduction in checkout abandonment
- **Payment Success Rate**: 99%+ successful payment completion rate
- **Customer Satisfaction**: 4.5+ star rating from merchants

### 9.3 Payment Processing Metrics
- **Payment Success Rate**: 99%+ successful payment completions through WhatsApp
- **Response Time**: < 2 seconds average payment processing time
- **Payment Method Coverage**: 95%+ of regional payment methods supported
- **Fraud Detection**: < 0.1% false positive rate in fraud detection
- **AP2 Compliance**: 100% mandate verification success rate
- **Customer Support Reduction**: 60%+ reduction in payment-related support tickets

---

## 10. Go-to-Market Strategy

### 10.1 Target Market Segments

#### 10.1.1 Primary: BEMOBI's Existing Merchants
- **SMBs in LATAM**: Cafes, restaurants, small retailers
- **E-commerce in Africa**: Online stores, digital services
- **Mobile-first businesses in Asia**: Apps, digital content

#### 10.1.2 Secondary: New Market Expansion
- **WhatsApp-first businesses**: Companies already using WhatsApp for sales
- **Digital natives**: Startups and tech companies
- **Traditional businesses**: Brick-and-mortar stores going digital

### 10.2 Launch Strategy

#### 10.2.1 Pilot Program
- **Phase 1**: 5 select BEMOBI merchants for 30-day pilot
- **Phase 2**: 25 merchants across all regions for 60-day pilot
- **Phase 3**: Full rollout to BEMOBI's entire merchant base

#### 10.2.2 Marketing Approach
- **BEMOBI Partnership**: Joint marketing and sales efforts
- **Case Studies**: Success stories from pilot merchants
- **Demo Environment**: Interactive demos for potential merchants
- **Conference Presence**: Fintech and payments industry events

### 10.3 Support Strategy

#### 10.3.1 Merchant Onboarding
- **Technical Integration**: Dedicated integration specialists for merchant API connections
- **Payment Data Migration**: Seamless migration of existing payment systems
- **Training Programs**: Comprehensive training for merchant teams
- **24/7 Support**: Round-the-clock technical support for payment processing

#### 10.3.2 Customer Success
- **Payment Analytics Dashboard**: Real-time payment metrics and success analysis
- **Payment Optimization**: AI-powered recommendations for improving payment success rates
- **A/B Testing**: Continuous optimization of payment flows and messaging
- **Merchant Feedback Loops**: Regular feedback collection from merchants and customers

---

## 11. Conclusion

sofIA represents a transformative opportunity for BEMOBI to lead the conversational commerce revolution in emerging markets. By implementing Google's AP2 Protocol and creating a sophisticated multi-agent payment orchestration system, we can provide BEMOBI's merchants with a competitive advantage that significantly reduces checkout abandonment while improving customer experience.

The combination of:
- **Intelligent Payment Processing** with AP2-compliant mandate verification
- **Multi-Agent Orchestration** for seamless payment flow management
- **Regional Payment Support** with automatic currency and method routing
- **WhatsApp Integration** for natural, conversational payment processing
- **AP2 Protocol compliance** for secure, auditable payment transactions

Creates a unique value proposition that positions BEMOBI as the leading conversational commerce platform for merchants in LATAM, Africa, and Asia, with potential expansion to other payment-intensive industries.

This PRD serves as the foundation for building a production-ready payment orchestration system that can scale from pilot programs with select merchants to comprehensive deployments across BEMOBI's entire merchant base, driving significant revenue growth and customer satisfaction while revolutionizing how customers make payments through WhatsApp.

---

**Document Version**: 3.0 (Updated to reflect payment orchestration focus)
**Last Updated**: January 2025
**Next Review**: February 2025
**Approved By**: HACKTUDO 2025 Development Team
**Major Changes**: Pivoted from subscription management to payment orchestration with BEMOBI integration
