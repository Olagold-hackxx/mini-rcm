# Testing Guide

This directory contains tests for the Medical Claims Validator application.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_api_auth.py         # Authentication API tests
├── test_api_rules.py        # Rules management API tests
├── test_api_tenants.py      # Tenant management API tests
├── test_pipeline_stages.py  # Pipeline stage tests
├── test_technical_rules.py  # Technical rules validator tests
└── test_services.py         # Service layer tests
```

## Running Tests

### Install Test Dependencies

```bash
cd app
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_technical_rules.py
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test

```bash
pytest tests/test_technical_rules.py::TestTechnicalRulesEngine::test_service_approval_required_missing
```

## Test Fixtures

- `db_session`: Database session for testing
- `client`: FastAPI test client
- `test_user`: Sample user for authentication
- `auth_token`: JWT token for authenticated requests
- `authenticated_client`: Pre-authenticated test client
- `mock_openai`: Mocked OpenAI API
- `sample_claim_data`: Sample claim dictionary
- `sample_claims_file`: Sample CSV file

## Writing New Tests

1. Create test file: `test_<module_name>.py`
2. Import pytest and necessary modules
3. Use fixtures from `conftest.py`
4. Follow naming convention: `test_<functionality>`
5. Use descriptive test names

Example:
```python
def test_service_approval_required_with_approval(self, engine):
    """Test that service requiring approval with approval number passes."""
    # Test implementation
```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Via GitHub Actions (`.github/workflows/ci.yml`)

## Coverage Goals

- Target: 80%+ code coverage
- Critical paths: 100% coverage
- API endpoints: 90%+ coverage

