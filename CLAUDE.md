# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment & Dependencies
```bash
# Install dependencies
uv sync

# Add new dependencies
uv add package-name

# Activate virtual environment (if needed)
source .venv/bin/activate
```

### Running the Application
```bash
# Start sofIA agent (requires GOOGLE_API_KEY in .env)
uv run app.py

# Run demo mode (no WhatsApp needed)
uv run app.py demo

# Start WhatsApp bridge (separate terminal)
cd whatsapp-bridge && npm start
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_ap2_protocol.py -v

# Run with coverage
uv run pytest --cov=sofIA
```

## Architecture Overview

This is a hackathon project implementing an AI payment agent using Google's AP2 (Agent Payments Protocol) for secure WhatsApp transactions.

### Core Architecture Pattern: Agent-to-Agent (A2A) Communication

The system uses two main agents that coordinate via A2A:

1. **sofIA Agent** (`sofIA/`): Specialized payment processing agent
   - Implements AP2 protocol (Intent, Cart, Payment Mandates)
   - Uses tools for AP2 protocol, WhatsApp integration, and Bemobi gateway
   - Model: Gemini 2.5 Flash

2. **Orchestrator Agent** (`orchestrator/`): Main conversation coordinator
   - Handles natural language conversations
   - Intelligently detects payment intent using AI (not hardcoded keywords)
   - Coordinates with sofIA agent for payment processing
   - Model: Gemini 2.5 Flash

### Agent Structure Pattern

Both agents follow the same clean structure:
```
agent_folder/
├── agent.py      # Agent definition (Google ADK)
├── prompt.py     # Agent instructions
└── tools/        # Agent tools folder
    ├── __init__.py
    └── tool_name.py
```

### WhatsApp Integration Architecture

```
WhatsApp Phone ←→ WhatsApp Web.js ←→ Node.js Bridge ←→ Orchestrator Agent
                                                              ↓
                                                         sofIA Agent
                                                              ↓
                                                      AP2 Protocol Processing
```

### Key Files

- **`app.py`**: Main FastAPI application, routes messages to orchestrator
- **`orchestrator/tools/orchestration_tool.py`**: Session management and A2A coordination functions
- **`sofIA/tools/ap2_protocol/ap2_core.py`**: Complete AP2 protocol implementation
- **`whatsapp-bridge/`**: Node.js service using WhatsApp Web.js (no Business API needed)

### Environment Configuration

Essential environment variables:
```bash
GOOGLE_API_KEY=your_google_api_key  # Required for both agents
HOST=0.0.0.0
PORT=8000
```

Optional (for enhanced features):
```bash
BEMOBI_API_KEY=your_bemobi_key  # Payment gateway (has mock fallback)
WHATSAPP_ACCESS_TOKEN=token     # Not used (using WhatsApp Web.js instead)
```

### Payment Flow

1. User sends WhatsApp message → Orchestrator detects intent intelligently
2. Orchestrator coordinates with sofIA agent → Creates AP2 Intent Mandate
3. User confirms → sofIA creates Cart Mandate → Payment processing
4. Transaction complete → AP2 Payment Mandate created

### Important Notes

- **No hardcoded keywords**: Orchestrator uses AI to detect payment intent
- **Mock integrations**: Bemobi gateway and some WhatsApp features have mock implementations for hackathon demo
- **AP2 Compliance**: Full implementation of Google's Agent Payments Protocol with cryptographic signatures
- **Session persistence**: Orchestrator maintains conversation state and payment flow
- **Error handling**: Graceful fallbacks when tools/agents are unavailable

### Development Patterns

- Tools are functions, not classes (see `sofIA/tools/` and `orchestrator/tools/`)
- Tools are dynamically loaded (see `sofIA/tools/__init__.py`)
- Agents coordinate via response markers (e.g., `[PAYMENT_INTENT]`)
- All payment operations create proper AP2 mandates with RSA signatures
- WhatsApp integration works with personal accounts (no Business API required)