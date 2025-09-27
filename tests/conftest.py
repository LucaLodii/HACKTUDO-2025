"""
Pytest configuration and shared fixtures for sofIA test suite
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    env_vars = {
        "GOOGLE_API_KEY": "test_google_api_key",
        "WHATSAPP_BRIDGE_URL": "http://localhost:3001",
        "SUPABASE_URL": "https://test-project.supabase.co",
        "SUPABASE_KEY": "test_supabase_key",
        "ENVIRONMENT": "test",
        "DEBUG": "true"
    }
    
    with patch.dict(os.environ, env_vars):
        yield

@pytest.fixture
def mock_google_adk():
    """Mock Google ADK Agent class for all tests"""
    with patch('google.adk.agents.Agent') as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent.name = 'test_agent'
        mock_agent.model = 'gemini-2.5-flash'
        mock_agent.tools = []
        mock_agent_class.return_value = mock_agent
        yield mock_agent_class, mock_agent

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for database operations"""
    with patch('supabase.create_client') as mock_create_client:
        mock_client = MagicMock()
        
        # Mock table operations
        mock_table = MagicMock()
        mock_table.select.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.update.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        
        # Mock execute method with sample data
        mock_execute_result = MagicMock()
        mock_execute_result.data = [
            {
                "id": "test-id",
                "name": "Test Item",
                "created_at": "2025-01-28T10:00:00Z"
            }
        ]
        mock_table.execute.return_value = mock_execute_result
        
        mock_client.table.return_value = mock_table
        mock_create_client.return_value = mock_client
        
        yield mock_client

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "user_id": "+5511999887766",
        "full_name": "João Silva Santos",
        "email": "joao.silva@email.com",
        "preferred_language": "pt-BR",
        "timezone": "America/Sao_Paulo"
    }

@pytest.fixture
def sample_operator_data():
    """Sample operator data for testing"""
    return [
        {
            "id": "vivo-op",
            "name": "VIVO",
            "display_name": "Vivo",
            "logo_url": "https://example.com/vivo-logo.png",
            "brand_color": "#8B2797",
            "is_active": True
        },
        {
            "id": "claro-op",
            "name": "CLARO",
            "display_name": "Claro",
            "logo_url": "https://example.com/claro-logo.png",
            "brand_color": "#E61E24",
            "is_active": True
        }
    ]

@pytest.fixture
def sample_subscription_plans():
    """Sample subscription plans for testing"""
    return [
        {
            "id": "vivo-001",
            "operator_id": "vivo-op",
            "plan_code": "VIVO_BASIC_5GB",
            "name": "Vivo Basic 5GB",
            "description": "Plano básico com 5GB de internet",
            "price_cents": 2990,
            "billing_cycle": "monthly",
            "data_limit_gb": 5,
            "voice_minutes": -1,  # Unlimited
            "sms_count": 100,
            "features": {
                "unlimited_calls": True,
                "whatsapp_free": True,
                "social_media_free": False
            },
            "is_active": True
        },
        {
            "id": "vivo-002",
            "operator_id": "vivo-op",
            "plan_code": "VIVO_PREMIUM_10GB",
            "name": "Vivo Premium 10GB",
            "description": "Plano premium com 10GB de internet",
            "price_cents": 4990,
            "billing_cycle": "monthly",
            "data_limit_gb": 10,
            "voice_minutes": -1,
            "sms_count": -1,
            "features": {
                "unlimited_calls": True,
                "unlimited_sms": True,
                "whatsapp_free": True,
                "social_media_free": True
            },
            "is_active": True
        }
    ]

@pytest.fixture
def sample_active_subscriptions():
    """Sample active subscriptions for testing"""
    return [
        {
            "id": "sub-001",
            "user_id": "user-001",
            "operator_id": "vivo-op",
            "plan_id": "vivo-002",
            "subscription_external_id": "VIVO_SUB_001",
            "status": "active",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2025-01-31T23:59:59Z",
            "auto_renewal": True,
            "operators": {
                "id": "vivo-op",
                "name": "VIVO",
                "display_name": "Vivo",
                "brand_color": "#8B2797"
            },
            "subscription_plans": {
                "id": "vivo-002",
                "name": "Vivo Premium 10GB",
                "price_cents": 4990,
                "billing_cycle": "monthly",
                "data_limit_gb": 10,
                "features": {
                    "unlimited_calls": True,
                    "whatsapp_free": True
                }
            }
        }
    ]

@pytest.fixture
def sample_whatsapp_messages():
    """Sample WhatsApp messages for testing"""
    return [
        {
            "from": "+5511999887766",
            "text": "Quais são meus planos?",
            "timestamp": "2025-01-28T10:00:00Z",
            "message_id": "wamid.123",
            "type": "text"
        },
        {
            "from": "+5511999887766",
            "text": "Quero renovar meu plano Vivo",
            "timestamp": "2025-01-28T10:01:00Z",
            "message_id": "wamid.124",
            "type": "text"
        },
        {
            "from": "+5511999887766",
            "text": "Melhorar plano",
            "timestamp": "2025-01-28T10:02:00Z",
            "message_id": "wamid.125",
            "type": "text"
        }
    ]

@pytest.fixture
def sample_ap2_payment_data():
    """Sample AP2 payment data for testing"""
    return {
        "mandate_data": {
            "user_info": {
                "user_id": "+5511999887766",
                "name": "João Silva"
            },
            "subscription_info": {
                "subscription_id": "sub-001",
                "plan_name": "Vivo Premium 10GB",
                "amount_cents": 4990,
                "currency": "BRL"
            }
        },
        "mandate_response": {
            "success": True,
            "mandate_id": "ap2_mandate_123",
            "signature": "cryptographic_signature_here",
            "expires_at": "2025-01-28T10:15:00Z",
            "status": "created"
        },
        "payment_response": {
            "success": True,
            "transaction_id": "ap2_txn_456",
            "mandate_id": "ap2_mandate_123",
            "amount_cents": 4990,
            "currency": "BRL",
            "status": "completed",
            "processed_at": "2025-01-28T10:05:00Z"
        }
    }

@pytest.fixture
def mock_tools_force_mode():
    """Force all tools into mock mode for testing"""
    tools_to_mock = [
        'sofIA.tools.subscription_management.subscription_management_tool',
        'sofIA.tools.renewal_orchestration.renewal_orchestration_tool',
        'sofIA.tools.plan_management.plan_management_tool'
    ]
    
    patches = []
    for tool_path in tools_to_mock:
        try:
            # Import the tool and set mock_mode to True
            module_path, tool_name = tool_path.rsplit('.', 1)
            module = sys.modules.get(module_path)
            if module:
                tool = getattr(module, tool_name, None)
                if tool and hasattr(tool, 'mock_mode'):
                    tool.mock_mode = True
        except (ImportError, AttributeError):
            pass
    
    yield
    
    # Reset mock mode after test
    for tool_path in tools_to_mock:
        try:
            module_path, tool_name = tool_path.rsplit('.', 1)
            module = sys.modules.get(module_path)
            if module:
                tool = getattr(module, tool_name, None)
                if tool and hasattr(tool, 'mock_mode'):
                    tool.mock_mode = False
        except (ImportError, AttributeError):
            pass

@pytest.fixture
def conversation_session():
    """Sample conversation session data"""
    return {
        "user_id": "+5511999887766",
        "session_data": {
            "payment_state": "idle",
            "current_intent": None,
            "product_info": None,
            "agent_responses": [],
            "conversation_history": [],
            "subscription_context": {
                "active_subscriptions": [],
                "pending_renewals": [],
                "last_interaction": None
            }
        }
    }

# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "whatsapp: WhatsApp integration tests")

@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests"""
    import logging
    
    # Set log level to WARNING to reduce noise during tests
    logging.getLogger().setLevel(logging.WARNING)
    
    # Specific loggers that might be noisy
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    yield
    
    # Reset to INFO after tests
    logging.getLogger().setLevel(logging.INFO)
