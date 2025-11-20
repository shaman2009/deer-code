"""Pytest configuration and shared fixtures."""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch, mock_open

import pytest
from langchain.tools import ToolRuntime
import yaml


def pytest_sessionstart(session):
    """Create a temporary config.yaml before tests start."""
    # Create a minimal config.yaml for testing
    # Use the same API key as mock_tavily_api_key fixture for consistency
    minimal_config = {
        "models": {
            "chat_model": {
                "model": "gpt-4",
                "api_base": "https://api.openai.com/v1",
                "api_key": "test_key",
                "temperature": 0,
                "max_tokens": 8192,
            }
        },
        "tools": {
            "tavily": {
                "api_key": "test_tavily_api_key_123"  # Match the fixture value
            }
        },
    }

    # Write to config.yaml in the current directory
    config_path = os.path.join(os.getcwd(), "config.yaml")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            yaml.dump(minimal_config, f)
        # Mark that we created it so we can clean up later
        session.config._created_config = True
    else:
        session.config._created_config = False


def pytest_sessionfinish(session, exitstatus):
    """Clean up the temporary config.yaml after tests finish."""
    if getattr(session.config, "_created_config", False):
        config_path = os.path.join(os.getcwd(), "config.yaml")
        if os.path.exists(config_path):
            os.remove(config_path)


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
