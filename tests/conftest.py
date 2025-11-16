"""Pytest configuration and shared fixtures."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from langchain.tools import ToolRuntime


@pytest.fixture(scope="session", autouse=True)
def mock_config_loading():
    """Mock config loading for all tests to avoid requiring config.yaml."""
    # Mock the config module's __config variable and load_config function
    with patch("deer_code.config.config.__config", {}):
        with patch("deer_code.config.config.load_config") as mock_load:
            mock_load.return_value = {}
            yield


@pytest.fixture
def mock_tool_runtime():
    """Create a mock ToolRuntime for testing tools."""
    runtime = MagicMock(spec=ToolRuntime)
    return runtime


@pytest.fixture
def mock_tavily_api_key(monkeypatch):
    """Set a mock Tavily API key in environment."""
    test_api_key = "test_tavily_api_key_123"
    monkeypatch.setenv("TAVILY_API_KEY", test_api_key)
    return test_api_key


@pytest.fixture
def clear_tavily_api_key(monkeypatch):
    """Clear Tavily API key from environment."""
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


@pytest.fixture
def sample_tavily_response():
    """Sample Tavily API response for testing."""
    return {
        "answer": "Python is a high-level programming language.",
        "results": [
            {
                "title": "Python Official Website",
                "url": "https://www.python.org",
                "content": "Python is a programming language that lets you work quickly and integrate systems more effectively.",
                "score": 0.95,
            },
            {
                "title": "Python Wikipedia",
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "content": "Python is an interpreted, high-level programming language with dynamic semantics.",
                "score": 0.89,
            },
            {
                "title": "Learn Python",
                "url": "https://www.learnpython.org",
                "content": "Free interactive Python tutorial for beginners.",
                "score": 0.78,
            },
        ],
    }


@pytest.fixture
def sample_tavily_response_no_answer():
    """Sample Tavily API response without answer."""
    return {
        "results": [
            {
                "title": "Search Result",
                "url": "https://example.com",
                "content": "Some content here.",
                "score": 0.75,
            }
        ]
    }


@pytest.fixture
def sample_tavily_response_empty():
    """Sample empty Tavily API response."""
    return {"results": []}
