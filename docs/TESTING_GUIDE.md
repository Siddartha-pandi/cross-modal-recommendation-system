# Testing Guide

## Table of Contents
1. [Overview](#overview)
2. [Test Setup](#test-setup)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Writing Tests](#writing-tests)
6. [Coverage Reports](#coverage-reports)
7. [Performance Testing](#performance-testing)
8. [CI/CD Integration](#cicd-integration)

---

## Overview

The Cross-Modal Recommendation System includes comprehensive test coverage for:

- **Unit Tests:** Individual component testing (CLIP, Fusion, FAISS, Cache)
- **Integration Tests:** API endpoint and service integration
- **Performance Tests:** Speed and scalability benchmarks
- **End-to-End Tests:** Complete workflow validation

**Target Coverage:** 80%+

---

## Test Setup

### 1. Install Test Dependencies

```bash
cd backend

# Install pytest and plugins
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Verify installation
pytest --version
```

### 2. Configure pytest

The `pytest.ini` file is already configured with:

```ini
[pytest]
testpaths = tests
addopts = -v --tb=short --cov=app --cov-report=html
asyncio_mode = auto
```

### 3. Setup Test Database

```bash
# Create test database
createdb cmrs_test

# Set test environment variable
export DATABASE_URL=postgresql://user:pass@localhost:5432/cmrs_test
```

### 4. Setup Test Redis

```bash
# Use separate Redis database for testing
export REDIS_TEST_DB=15
```

---

## Running Tests

### Run All Tests

```bash
# From backend directory
pytest

# With verbose output
pytest -v

# Show print statements
pytest -s
```

### Run Specific Test Files

```bash
# Single file
pytest tests/test_comprehensive.py

# Multiple files
pytest tests/test_comprehensive.py tests/conftest.py
```

### Run Specific Tests

```bash
# Single test function
pytest tests/test_comprehensive.py::test_clip_encode_text

# Test class
pytest tests/test_comprehensive.py::TestFusion

# Pattern matching
pytest -k "test_clip"          # All tests with "clip" in name
pytest -k "not slow"           # Skip slow tests
```

### Run by Markers

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Performance tests
pytest -m performance
```

---

## Test Categories

### Unit Tests

Test individual components in isolation:

```python
@pytest.mark.unit
async def test_clip_encode_text(clip_model):
    """Test CLIP text encoding"""
    text = "red summer dress"
    embedding = await clip_model.encode_text(text)
    
    assert embedding is not None
    assert embedding.shape == (512,)
    assert np.isclose(np.linalg.norm(embedding), 1.0)
```

### Integration Tests

Test component interactions:

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_pipeline(search_service, sample_products):
    """Test complete search pipeline"""
    # Add products
    for product in sample_products:
        embedding = await get_embedding(product)
        search_service.faiss_index.add_product(embedding, product)
    
    # Execute search
    results, metadata = await search_service.search(
        text_query="blue shirt",
        top_k=5
    )
    
    assert len(results) <= 5
    assert metadata['search_time_ms'] > 0
```

### Performance Tests

Test speed and scalability:

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_search_speed(search_service):
    """Test search meets performance targets"""
    import time
    
    start = time.time()
    results, metadata = await search_service.search(
        text_query="test query",
        top_k=10
    )
    duration = (time.time() - start) * 1000
    
    assert duration < 500  # Must be under 500ms
    print(f"Search took: {duration:.2f}ms")
```

### End-to-End Tests

Test complete user workflows:

```python
@pytest.mark.e2e
async def test_user_registration_and_search(async_client):
    """Test registration → login → search workflow"""
    # Register
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    token = response.json()['access_token']
    
    # Login
    response = await async_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
    
    # Search (authenticated)
    response = await async_client.post(
        "/api/v1/recommend",
        json={"text": "blue shirt", "top_k": 5},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert len(response.json()['results']) <= 5
```

---

## Writing Tests

### Test Structure

```python
# tests/test_feature.py

import pytest
from app.module import Component

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def component():
    """Create component instance"""
    return Component()

# ============================================================================
# UNIT TESTS
# ============================================================================

def test_component_initialization(component):
    """Test component initializes correctly"""
    assert component is not None
    assert component.status == "initialized"

@pytest.mark.asyncio
async def test_async_operation(component):
    """Test async operation"""
    result = await component.process()
    assert result == expected_value

# ============================================================================
# EDGE CASES
# ============================================================================

def test_component_handles_empty_input(component):
    """Test component handles empty input gracefully"""
    with pytest.raises(ValueError):
        component.process(None)

def test_component_handles_invalid_input(component):
    """Test component validates input"""
    with pytest.raises(ValidationError):
        component.process("invalid")
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result is not None
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """Test with mocked dependency"""
    mock_service = Mock()
    mock_service.fetch_data.return_value = "mocked_data"
    
    component = Component(service=mock_service)
    result = component.process()
    
    assert result == "mocked_data"
    mock_service.fetch_data.assert_called_once()

@patch('app.models.clip_model.CLIPModel')
def test_with_patched_dependency(mock_clip):
    """Test with patched CLIP model"""
    mock_clip.encode_text.return_value = np.zeros(512)
    
    result = process_with_clip("test")
    assert result.shape == (512,)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("text,expected_length", [
    ("short", 5),
    ("medium length text", 18),
    ("very long text that should be truncated", 30)
])
def test_text_processing(text, expected_length):
    """Test text processing with multiple inputs"""
    result = process_text(text, max_length=30)
    assert len(result) == expected_length
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report (most detailed)
pytest --cov=app --cov-report=html
open htmlcov/index.html  # Opens in browser

# Terminal report
pytest --cov=app --cov-report=term

# Missing lines report
pytest --cov=app --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Requirements

```bash
# Fail if coverage below 80%
pytest --cov=app --cov-fail-under=80
```

### View Coverage by Module

```bash
pytest --cov=app --cov-report=term

# Output:
# Name                      Stmts   Miss  Cover
# ---------------------------------------------
# app/__init__.py               2      0   100%
# app/models/clip_model.py     45      3    93%
# app/models/fusion.py         67      5    93%
# app/utils/faiss_index.py     52      8    85%
# app/services/search.py       89     12    87%
# ---------------------------------------------
# TOTAL                       255     28    89%
```

### Improve Coverage

1. **Identify untested code:**
```bash
pytest --cov=app --cov-report=term-missing
```

2. **Focus on critical paths:**
   - API endpoints
   - Authentication logic
   - Search algorithms
   - Error handling

3. **Add edge case tests:**
   - Empty inputs
   - Invalid data
   - Boundary conditions
   - Error scenarios

---

## Performance Testing

### Speed Benchmarks

```python
import pytest
import time

@pytest.mark.performance
def test_embedding_generation_speed(clip_model):
    """Benchmark embedding generation"""
    text = "test query"
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        _ = clip_model.encode_text(text)
    duration = time.time() - start
    
    avg_time = (duration / iterations) * 1000
    print(f"\nAvg embedding time: {avg_time:.2f}ms")
    
    assert avg_time < 200  # Target: <200ms per embedding
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class RecommendationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search_text(self):
        self.client.post("/api/v1/text-search", 
            params={"query": "blue shirt", "top_k": 10})
    
    @task(3)
    def recommend_hybrid(self):
        self.client.post("/api/v1/recommend",
            json={"text": "red dress", "top_k": 5, "alpha": 0.7})
EOF

# Run load test
locust -f locustfile.py --host http://localhost:8000

# Open http://localhost:8089 to view results
```

### Stress Testing

```python
import asyncio
import aiohttp

async def stress_test_api():
    """Stress test with concurrent requests"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # 100 concurrent requests
        for i in range(100):
            task = session.post(
                "http://localhost:8000/api/v1/text-search",
                params={"query": f"query {i}", "top_k": 10}
            )
            tasks.append(task)
        
        start = time.time()
        responses = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        success = sum(1 for r in responses if r.status == 200)
        print(f"Completed 100 requests in {duration:.2f}s")
        print(f"Success rate: {success}%")
        
        assert success >= 95  # At least 95% success rate

asyncio.run(stress_test_api())
```

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/test_db
        REDIS_HOST: localhost
      run: |
        cd backend
        pytest --cov=app --cov-report=xml --cov-fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: true
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
image: python:3.10

services:
  - postgres:15
  - redis:7

variables:
  POSTGRES_DB: test_db
  POSTGRES_USER: test_user
  POSTGRES_PASSWORD: test_password
  DATABASE_URL: postgresql://test_user:test_password@postgres:5432/test_db

stages:
  - test

test:
  stage: test
  script:
    - cd backend
    - pip install -r requirements.txt
    - pip install pytest pytest-asyncio pytest-cov
    - pytest --cov=app --cov-report=term --cov-fail-under=80
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

Install pre-commit:

```bash
pip install pre-commit
pre-commit install
```

---

## Best Practices

1. **Write tests first (TDD):** Define expected behavior before implementing
2. **Test one thing per test:** Keep tests focused and simple
3. **Use descriptive names:** `test_user_registration_with_invalid_email`
4. **Mock external dependencies:** Don't rely on external APIs in tests
5. **Clean up after tests:** Use fixtures with teardown
6. **Test edge cases:** Empty inputs, boundary values, error conditions
7. **Maintain test independence:** Tests should not depend on each other
8. **Keep tests fast:** Use mocks to avoid slow operations
9. **Update tests with code:** Tests are documentation
10. **Achieve meaningful coverage:** Focus on critical paths, not just numbers

---

## Common Test Patterns

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    """Test that invalid input raises ValueError"""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(None)
```

### Testing Async Exceptions

```python
@pytest.mark.asyncio
async def test_async_error_handling():
    """Test async error handling"""
    with pytest.raises(APIError):
        await fetch_data("invalid_url")
```

### Testing with Fixtures

```python
@pytest.fixture
def populated_index(faiss_index):
    """Fixture with pre-populated FAISS index"""
    for i in range(10):
        emb = np.random.randn(512)
        faiss_index.add_product(emb, {'id': f'P{i}'})
    return faiss_index

def test_search_populated_index(populated_index):
    """Test search with populated index"""
    query = np.random.randn(512)
    results = populated_index.search(query, k=5)
    assert len(results) == 5
```

---

## Debugging Tests

### Run with debugger

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start of test
pytest --trace
```

### Show print statements

```bash
pytest -s  # Show all print statements
pytest -s tests/test_file.py::test_specific  # For specific test
```

### Increase verbosity

```bash
pytest -vv  # Very verbose
pytest -vv -s  # Very verbose + print statements
```

### Re-run failed tests

```bash
# Run only failed tests from last run
pytest --lf

# Run failed tests first, then others
pytest --ff
```

---

**For issues or questions, see:** [Troubleshooting Guide](DEPLOYMENT_GUIDE.md#troubleshooting)
