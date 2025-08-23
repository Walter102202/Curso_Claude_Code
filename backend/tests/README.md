# RAG System Test Suite

This directory contains the test suite for the RAG (Retrieval-Augmented Generation) system.

## Test Structure

- `conftest.py` - Shared pytest fixtures and test configuration
- `test_api.py` - FastAPI endpoint tests
- `__init__.py` - Package initialization

## Running Tests

### Run all tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run specific test categories
```bash
# API endpoint tests only
python -m pytest tests/ -m api -v

# Unit tests only (when available)
python -m pytest tests/ -m unit -v

# Integration tests only (when available)  
python -m pytest tests/ -m integration -v
```

### Run specific test files
```bash
python -m pytest tests/test_api.py -v
```

### Run specific test classes or methods
```bash
python -m pytest tests/test_api.py::TestQueryEndpoint -v
python -m pytest tests/test_api.py::TestQueryEndpoint::test_query_with_session_id -v
```

## Test Features

### Fixtures Available (conftest.py)

- `test_client` - FastAPI TestClient with mocked dependencies
- `mock_rag_system` - Complete mocked RAG system
- `mock_config` - Test configuration
- `sample_course` - Sample course data
- `sample_chunks` - Sample course chunks
- `temp_docs_dir` - Temporary directory with test documents
- Various component mocks (vector_store, ai_generator, session_manager)

### Test Categories (Markers)

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Tests that take longer to run

## API Test Coverage

The API tests cover:

### `/api/query` endpoint:
- Query with provided session ID
- Query without session ID (auto-creation)
- Different source formats (dict vs string)
- Request validation
- Error handling

### `/api/courses` endpoint:
- Successful course statistics retrieval
- Empty results handling
- Error handling

### Root `/` endpoint:
- Basic API information

### Middleware and CORS:
- CORS header presence
- Options request handling
- Request validation
- Content type handling

## Static File Issue Solution

The test suite creates a separate test FastAPI app that doesn't mount static files, avoiding import issues with non-existent frontend files during testing. The test app replicates all API endpoints with the same behavior but uses mocked dependencies.

## Adding New Tests

1. Create test files following the `test_*.py` pattern
2. Use appropriate markers (`@pytest.mark.api`, `@pytest.mark.unit`, etc.)
3. Import fixtures from `conftest.py`
4. Follow existing patterns for mocking dependencies

Example:
```python
import pytest

@pytest.mark.unit
def test_new_feature(mock_rag_system):
    # Test implementation
    pass
```