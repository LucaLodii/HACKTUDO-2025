# sofIA Testing Documentation

## Overview

The sofIA application includes a comprehensive test suite that covers all aspects of the subscription management and payment orchestration system. This document provides detailed information about running tests, understanding test coverage, and contributing new tests.

## Test Architecture

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                    # Pytest configuration
├── test_subscription_management.py # Subscription tools and workflows
├── test_sofia_agent.py           # sofIA agent integration
├── test_orchestrator.py          # Multi-agent orchestration
├── test_api_integration.py       # API endpoints and services
├── test_end_to_end.py            # Complete user journeys
└── test_app.py                   # Main application tests
```

### Test Categories

Tests are organized using pytest markers:

- **`unit`** - Individual component tests
- **`integration`** - Component interaction tests  
- **`e2e`** - End-to-end user journey tests
- **`api`** - API endpoint tests
- **`database`** - Database integration tests
- **`whatsapp`** - WhatsApp bridge tests
- **`subscription`** - Subscription management tests
- **`payment`** - Payment processing tests
- **`agent`** - AI agent functionality tests
- **`slow`** - Tests that take longer than 5 seconds
- **`mock`** - Tests that use mock data only

## Running Tests

### Prerequisites

Install required testing dependencies:

```bash
pip install pytest pytest-asyncio
```

Optional dependencies for enhanced testing:

```bash
pip install pytest-cov pytest-html pytest-xdist
```

### Basic Test Execution

#### Run All Tests (Quick Mode)
```bash
python run_tests.py --mode quick
```

#### Run All Tests (Complete)
```bash
python run_tests.py --mode all
```

#### Run by Category
```bash
# Unit tests only
python run_tests.py --mode unit

# Integration tests
python run_tests.py --mode integration

# End-to-end tests
python run_tests.py --mode e2e
```

#### Run Specific Test File
```bash
python run_tests.py --file test_subscription_management.py
```

#### Run with Coverage Report
```bash
python run_tests.py --mode coverage
```

#### Run Tests in Parallel
```bash
python run_tests.py --mode parallel
```

### Advanced Test Options

#### Run Tests with Specific Markers
```bash
pytest -m "subscription and not slow"
pytest -m "unit or integration"
pytest -m "not database"
```

#### Run Tests with Verbose Output
```bash
pytest tests/ -v --tb=long
```

#### Run Tests with Custom Filters
```bash
pytest tests/ -k "renewal" -v
pytest tests/ -k "not payment" -v
```

## Test Coverage

### Components Tested

#### 1. Subscription Management (`test_subscription_management.py`)
- ✅ User subscription discovery
- ✅ Subscription details retrieval
- ✅ Expiring subscriptions monitoring
- ✅ Available plans fetching
- ✅ Plan cost calculations
- ✅ Operator data management
- ✅ Error handling and validation

#### 2. Renewal Orchestration (`test_subscription_management.py`)
- ✅ Renewal queue monitoring
- ✅ Reminder scheduling
- ✅ Renewal message generation
- ✅ User response processing
- ✅ Renewal cost calculation
- ✅ Payment processing integration
- ✅ Proactive notification system

#### 3. Plan Management (`test_subscription_management.py`)
- ✅ Plan upgrade/downgrade options
- ✅ Plan comparison and analysis
- ✅ Migration cost calculations
- ✅ Plan change validation
- ✅ Migration execution
- ✅ Payment integration for plan changes
- ✅ Plan recommendation system

#### 4. sofIA Agent Integration (`test_sofia_agent.py`)
- ✅ Agent initialization and configuration
- ✅ Tool integration and availability
- ✅ Prompt content and conversation patterns
- ✅ Multi-tool workflow coordination
- ✅ Mock data consistency
- ✅ Error handling across tools

#### 5. Multi-Agent Orchestration (`test_orchestrator.py`)
- ✅ Agent-to-Agent (A2A) communication
- ✅ Message format validation
- ✅ Session management
- ✅ Intent detection patterns
- ✅ Conversation flow management
- ✅ Error recovery and fallback
- ✅ Performance under load

#### 6. API Integration (`test_api_integration.py`)
- ✅ FastAPI endpoint functionality
- ✅ WhatsApp bridge integration
- ✅ Supabase database operations
- ✅ External service integration
- ✅ Security and compliance measures
- ✅ Load handling and stress testing

#### 7. End-to-End Journeys (`test_end_to_end.py`)
- ✅ Complete subscription discovery flow
- ✅ Proactive renewal reminder process
- ✅ Plan upgrade user journey
- ✅ Multi-subscription management
- ✅ Error recovery scenarios
- ✅ Business logic validation

#### 8. Application Core (`test_app.py`)
- ✅ Application initialization
- ✅ Configuration management
- ✅ Security measures
- ✅ Middleware functionality
- ✅ Performance characteristics
- ✅ Documentation structure

## Mock Data System

### Mock Data Strategy

All tests use a comprehensive mock data system that simulates:

- **Brazilian Telecom Operators**: VIVO, CLARO, OI, TIM
- **Realistic Subscription Plans**: 16+ plans with Brazilian pricing
- **Sample Users**: WhatsApp numbers and user profiles
- **Active Subscriptions**: Various expiry dates and statuses
- **Payment History**: Transaction records with AP2 references

### Benefits of Mock Data

1. **No External Dependencies**: Tests run without requiring Supabase or external APIs
2. **Consistent Results**: Predictable test outcomes
3. **Fast Execution**: No network calls or database queries
4. **Comprehensive Coverage**: Tests all edge cases and scenarios
5. **Development Friendly**: Easy to run tests locally

## Test Configuration

### Environment Variables

Tests automatically mock environment variables:

```python
# Automatically set by conftest.py
GOOGLE_API_KEY=test_google_api_key
WHATSAPP_BRIDGE_URL=http://localhost:3001
SUPABASE_URL=https://test-project.supabase.co
SUPABASE_KEY=test_supabase_key
ENVIRONMENT=test
DEBUG=true
```

### Pytest Configuration

Key configuration in `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short --strict-markers --disable-warnings
asyncio_mode = auto
timeout = 300
```

## Sample Test Scenarios

### Unit Test Example
```python
@pytest.mark.asyncio
async def test_get_user_subscriptions(subscription_tool):
    result = await subscription_tool.execute(
        operation="get_user_subscriptions",
        whatsapp_number="+5511999887766"
    )
    
    assert result["success"] is True
    assert "subscriptions" in result
```

### Integration Test Example
```python
@pytest.mark.asyncio
async def test_subscription_to_renewal_flow():
    # 1. Get user subscriptions
    subscriptions = await subscription_tool.execute(...)
    
    # 2. Check renewal queue
    renewals = await renewal_tool.execute(...)
    
    # 3. Calculate costs
    costs = await renewal_tool.execute(...)
    
    assert all(result["success"] for result in [subscriptions, renewals, costs])
```

### End-to-End Test Example
```python
@pytest.mark.asyncio
async def test_complete_renewal_journey():
    # Simulate complete user journey from reminder to payment
    user_message = {"from": "+5511999887766", "text": "Sim, quero renovar"}
    
    # Process through all system components
    # ... (complete workflow testing)
    
    assert final_result["success"] is True
```

## Performance Testing

### Performance Benchmarks

- **Response Time**: < 2 seconds for individual operations
- **Concurrent Users**: Support 20+ concurrent test users
- **Memory Usage**: Stable memory usage across multiple test runs
- **Throughput**: Process 10+ operations per second

### Load Testing Examples

```python
@pytest.mark.asyncio
async def test_concurrent_users():
    # Test 20 concurrent users
    tasks = [subscription_tool.execute(...) for _ in range(20)]
    results = await asyncio.gather(*tasks)
    
    assert all(r["success"] for r in results)
```

## Error Testing

### Error Scenarios Covered

1. **Invalid Operations**: Unknown operation types
2. **Missing Parameters**: Required parameters not provided
3. **Invalid Data**: Malformed input data
4. **Service Unavailability**: External service failures
5. **Network Issues**: Connection failures
6. **Data Corruption**: Invalid database states
7. **Rate Limiting**: Too many requests scenarios

### Error Handling Example

```python
@pytest.mark.asyncio
async def test_invalid_operation():
    result = await tool.execute(operation="invalid_operation")
    
    assert result["success"] is False
    assert "Unknown operation" in result["error"]
```

## Contributing Tests

### Adding New Tests

1. **Follow Naming Convention**: `test_*.py` files, `test_*` functions
2. **Use Appropriate Markers**: Mark tests with relevant categories
3. **Include Docstrings**: Document what each test validates
4. **Use Fixtures**: Leverage shared fixtures from `conftest.py`
5. **Test Both Success and Failure**: Include error scenarios
6. **Maintain Mock Data**: Update mock data as needed

### Test Writing Guidelines

```python
@pytest.mark.asyncio  # For async tests
@pytest.mark.unit     # Categorize appropriately
async def test_specific_functionality():
    """Test description explaining what is being validated"""
    
    # Arrange
    test_data = {"key": "value"}
    
    # Act
    result = await tool.execute(**test_data)
    
    # Assert
    assert result["success"] is True
    assert "expected_key" in result
```

### Mock Data Updates

When adding new functionality:

1. Update mock data in tool classes
2. Add new fixtures in `conftest.py`
3. Ensure consistency across all tools
4. Document new mock data structure

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-asyncio
      - name: Run tests
        run: python run_tests.py --mode all
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: python run_tests.py --mode quick
        language: system
        pass_filenames: false
        always_run: true
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ModuleNotFoundError: No module named 'google'
```
**Solution**: Tests use mocks for external dependencies. This is expected behavior.

#### 2. Async Test Issues
```
RuntimeWarning: coroutine was never awaited
```
**Solution**: Ensure `@pytest.mark.asyncio` decorator is used for async tests.

#### 3. Mock Data Inconsistency
```
AssertionError: Expected data not found
```
**Solution**: Check that tools are in mock mode and data is consistent.

### Debug Mode

Run tests with debug output:

```bash
python run_tests.py --mode all -s --log-cli-level=DEBUG
```

### Test Isolation

Each test runs in isolation with:
- Fresh mock data
- Clean environment variables
- Reset tool states
- Cleared session data

## Best Practices

### Test Organization

1. **One Concept Per Test**: Each test should validate one specific behavior
2. **Clear Test Names**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Independent Tests**: Tests should not depend on each other
5. **Comprehensive Coverage**: Test both happy path and edge cases

### Performance Considerations

1. **Use Mock Data**: Avoid external service calls in tests
2. **Parallel Execution**: Run tests in parallel when possible
3. **Efficient Fixtures**: Use session-scoped fixtures for expensive setup
4. **Timeout Management**: Set reasonable timeouts for async tests

### Maintenance

1. **Regular Updates**: Keep tests updated with code changes
2. **Refactor Common Code**: Extract common test logic to fixtures
3. **Review Coverage**: Regularly review test coverage reports
4. **Update Documentation**: Keep test documentation current

---

## Summary

The sofIA test suite provides comprehensive coverage of all system components with:

- **100+ Test Cases** across 6 test files
- **Complete User Journey Testing** from WhatsApp to payment completion
- **Mock Data System** for reliable, fast testing
- **Multiple Execution Modes** for different development needs
- **Performance and Load Testing** for production readiness
- **Error Scenario Coverage** for robust error handling

Run `python run_tests.py --mode info` for a complete overview of the test suite capabilities.
