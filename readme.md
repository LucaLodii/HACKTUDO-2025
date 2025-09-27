# sofIA - WhatsApp Payment Agent with AP2 Protocol

An AI-powered payment agent that implements the [Agent Payments Protocol (AP2)](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol) for secure WhatsApp transactions.

## 🚀 Features

- **AP2 Protocol Compliance**: Full implementation of Google's Agent Payments Protocol
- **WhatsApp Integration**: Seamless payment processing through WhatsApp Business API
- **Cryptographic Security**: RSA-signed mandates with verifiable credentials
- **Multi-Mandate Support**: Intent, Cart, and Payment mandates with proper authorization
- **Real-time Processing**: Fast and secure payment flows with audit trails
- **Persistent Memory**: Supabase integration for conversation history and user preferences
- **BEMOBI Integration**: Payment gateway with mock/real modes for global deployment
- **Multi-Agent Architecture**: Orchestrator, sofIA, BEMOBI, and WhatsApp agents

## 🏗️ Architecture

```
sofIA Multi-Agent Payment System
├── orchestrator/ (Main Orchestrator)
│   ├── agent.py (Google ADK orchestrator agent)
│   ├── prompt.py (Orchestration instructions)
│   └── tools/ (A2A coordination tools)
├── sofIA/ (Payment Agent)
│   ├── agent.py (Google ADK payment agent)
│   ├── prompt.py (Payment instructions)
│   ├── memory/ (Persistent memory system)
│   │   ├── supabase_memory.py (Supabase integration)
│   │   └── memory_tool.py (Memory tool for agents)
│   └── tools/ (Agent Tools)
│       ├── ap2_protocol/ (AP2 Protocol implementation)
│       │   ├── ap2_core.py (Core AP2 types and functions)
│       │   ├── ap2_tool.py (AP2 tool for agent)
│       │   └── payment_processor.py (Payment processing logic)
│       ├── bemobi/ (BEMOBI payment gateway)
│       │   ├── bemobi_tool.py (BEMOBI integration)
│       │   ├── mock_bemobi.py (Mock implementation)
│       │   ├── bemobi_factory.py (Factory pattern)
│       │   └── mock_data_generators.py (Test data)
│       └── whatsapp/ (WhatsApp integration)
│           ├── whatsapp_tool.py (WhatsApp tool)
│           └── webhook_handler.py (Webhook processing)
├── whatsapp-bridge/ (Node.js WhatsApp bridge)
│   ├── server.js (WhatsApp Web.js server)
│   └── package.json (Node.js dependencies)
└── tests/ (Test suite)
    ├── test_ap2_protocol.py
    ├── test_supabase_connection.py
    └── test_memory_final.py
```

## 📋 Prerequisites

- Python 3.12+
- Node.js 16+ (for WhatsApp Web.js bridge)
- [uv](https://github.com/astral-sh/uv) package manager
- Personal WhatsApp account (no Business API needed!)
- Google AI API key (for Gemini integration)
- Supabase account (for persistent memory storage)
- BEMOBI API credentials (optional - mock mode available)

## 🛠️ Installation

1. **Clone and setup Python environment**:
   ```bash
   git clone <repository-url>
   cd HACKTUDO-2025
   uv sync
   ```

2. **Setup WhatsApp Web.js Bridge**:
   ```bash
   cd whatsapp-bridge
   npm install
   ```

3. **Setup Supabase (for persistent memory)**:
   ```bash
   # Create Supabase project at supabase.com
   # Run the SQL schema in Supabase SQL Editor
   cat supabase_schema.sql
   ```

4. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Required environment variables**:
   ```bash
   # WhatsApp Bridge
   WHATSAPP_BRIDGE_URL=http://localhost:3001

   # Google AI (Optional for enhanced AI features)
   GOOGLE_API_KEY=your_google_api_key

   # Supabase (for persistent memory)
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key

   # BEMOBI (optional - mock mode available)
   BEMOBI_MOCK_MODE=true

   # Server
   HOST=0.0.0.0
   PORT=8000
   SOFIA_API_URL=http://localhost:8000
   ```

## 🚀 Usage

### **Quick Start (Hackathon Demo)**

1. **Test the system**:
   ```bash
   # Test Supabase connection
   python test_supabase_connection.py
   
   # Test memory system
   python test_memory_final.py
   ```

2. **Start the API**:
   ```bash
   python app.py
   ```

3. **Test WhatsApp integration**:
   ```bash
   # Test message processing
   curl -X POST http://localhost:8000/process-whatsapp-message \
     -H "Content-Type: application/json" \
     -d '{"user_id": "demo_user", "message": "Hello sofIA!"}'
   ```

### **Full WhatsApp Integration**

1. **Start WhatsApp Bridge**:
   ```bash
   cd whatsapp-bridge
   ./start.sh
   # Or manually: npm start
   ```

2. **Scan QR Code**:
   - QR code appears in terminal
   - Scan with WhatsApp on your phone
   - Wait for "WhatsApp client is ready!"

3. **Start sofIA Agent**:
   ```bash
   # In a new terminal
   uv run app.py
   ```

4. **Test**: Send "Hello sofIA" to your WhatsApp number

### **Demo Mode (No WhatsApp needed)**
```bash
uv run app.py demo
```

### **Run Tests**
```bash
uv run pytest tests/ -v
```

## 💳 AP2 Protocol Implementation

### Mandate Types

1. **Intent Mandate**: Captures user purchase intent and authorization
2. **Cart Mandate**: Cryptographically signed merchant cart with guaranteed pricing
3. **Payment Mandate**: User-authorized payment with complete audit trail

### Security Features

- **RSA Digital Signatures**: All mandates are cryptographically signed
- **Verifiable Credentials**: User authorization with non-repudiation
- **Audit Trails**: Complete transaction history with timestamps
- **Expiry Management**: Time-limited mandates for security

## 📱 WhatsApp Integration

### **WhatsApp Web.js Architecture**

```
WhatsApp Phone ←→ WhatsApp Web.js ←→ Node.js Bridge ←→ Python sofIA Agent
                                                              ↓
                                                     AP2 Protocol Processing
```

### **API Endpoints**

- `GET /health` - Health check (both services)
- `POST /process-whatsapp-message` - Message processing
- `POST /send-message` - Send WhatsApp message
- `GET /client-info` - WhatsApp client status

### **Message Flow**

1. User sends message via WhatsApp → WhatsApp Web.js
2. Bridge forwards to sofIA → Creates AP2 Intent Mandate
3. sofIA processes payment intent → Creates Cart Mandate
4. User confirms → Payment Mandate created
5. Transaction processed with full AP2 compliance

### **Real-time Features**

- ✅ Instant message delivery
- ✅ QR code authentication
- ✅ Session persistence
- ✅ Error handling & reconnection

## 🔧 Development

### Adding Dependencies
```bash
uv add package-name
```

### Project Structure
```
sofIA/                   # Main agent package
├── __init__.py
├── agent.py             # Google ADK agent with tools
└── prompt.py            # Agent instructions and prompts

tools/                   # Agent tools
├── ap2_protocol/
│   ├── __init__.py
│   ├── ap2_core.py      # AP2 protocol implementation
│   └── ap2_tool.py      # AP2 tool for agent
└── whatsapp/
    ├── __init__.py
    ├── whatsapp_tool.py # WhatsApp tool for agent
    └── webhook_handler.py # Webhook processing

tests/                   # Test suite
├── __init__.py
└── test_ap2_protocol.py # Comprehensive tests

app.py                   # Main application entry point
env.example             # Environment configuration template
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=sofIA

# Run specific test file
uv run pytest tests/test_ap2_protocol.py -v
```

## 🔐 Security Considerations

- All mandates use RSA-2048 digital signatures
- JWT tokens with short expiration times (15 minutes for carts)
- Webhook signature verification
- Secure key management for production deployments
- Audit logging for compliance

## 🌐 Deployment

### Environment Setup
1. Set up WhatsApp Business API account
2. Configure webhook URL: `https://your-domain.com/webhook`
3. Set verify token in environment
4. Deploy with HTTPS (required for WhatsApp webhooks)

### Production Checklist
- [ ] Environment variables configured
- [ ] SSL certificate installed
- [ ] Webhook URL verified
- [ ] Database configured (if using persistent storage)
- [ ] Monitoring and logging enabled

## 📚 Documentation

- [AP2 Protocol Specification](https://github.com/google-agentic-commerce/AP2)
- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp/business-management-api)
- [Google ADK Documentation](https://developers.google.com/agent-development-kit)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [AP2 repository](https://github.com/google-agentic-commerce/AP2) for details.

## 🙏 Acknowledgments

- Google Cloud for the AP2 Protocol specification
- WhatsApp Business API team
- Google ADK for agent framework integration
- HACKTUDO 2025 organizers