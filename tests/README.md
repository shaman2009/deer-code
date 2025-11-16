# DeerCode Tests

This directory contains test files for the DeerCode project.

## Setup

Install test dependencies:

```bash
uv sync --extra test
```

## Running Tests

### Run all tests

```bash
uv run pytest
```

### Run with coverage report

```bash
uv run pytest --cov=deer_code --cov-report=html
```

### Run only unit tests (fast, no API keys required)

```bash
uv run pytest -m unit
```

### Run integration tests (requires API keys)

```bash
uv run pytest -m integration
```

### Run specific test file

```bash
uv run pytest tests/tools/search/test_tavily_search.py
```

### Run specific test

```bash
uv run pytest tests/tools/search/test_tavily_search.py::TestTavilySearchTool::test_search_with_answer_and_results
```

### Run with verbose output

```bash
uv run pytest -v
```

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── tools/
│   └── search/
│       └── test_tavily_search.py       # Tavily search tool tests
└── README.md                            # This file
```

## Test Markers

- `@pytest.mark.unit` - Unit tests with mocked dependencies (fast, no API keys)
- `@pytest.mark.integration` - Integration tests with real APIs (require API keys)
- `@pytest.mark.slow` - Tests that take longer to run

## Writing Tests

### Example unit test with mocking

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
def test_my_function(mock_tool_runtime):
    with patch("module.ExternalService") as mock_service:
        mock_service.return_value.method.return_value = "result"
        result = my_function()
        assert result == "expected"
```

### Example integration test

```python
import os
import pytest

@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("API_KEY"),
    reason="API_KEY not set"
)
def test_real_api():
    result = call_real_api()
    assert result is not None
```

## Coverage

Coverage reports are generated in `htmlcov/` directory. Open `htmlcov/index.html` in a browser to view detailed coverage information.

## CI/CD

Tests can be run in CI/CD pipelines. Unit tests should run on every commit, while integration tests can be run on a schedule or manually with API keys configured as secrets.
