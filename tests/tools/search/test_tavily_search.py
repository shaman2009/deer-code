"""Tests for tavily_search_tool."""

import os
from unittest.mock import MagicMock, patch

import pytest

from deer_code.tools.search.tavily_search import tavily_search_tool


@pytest.mark.unit
class TestTavilySearchTool:
    """Unit tests for tavily_search_tool."""

    def test_search_with_answer_and_results(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test successful search with answer and results."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response
            mock_client_class.return_value = mock_client

            # Call the tool function directly
            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="What is Python?",
                max_results=3,
            )

            # Verify TavilyClient was initialized with correct API key
            mock_client_class.assert_called_once_with(api_key=mock_tavily_api_key)

            # Verify search was called with correct parameters
            mock_client.search.assert_called_once_with(
                query="What is Python?",
                max_results=3,
                search_depth="basic",
                include_answer=True,
                include_raw_content=False,
            )

            # Verify output format
            assert "## Answer" in result
            assert "Python is a high-level programming language." in result
            assert "## Search Results" in result
            assert "### 1. Python Official Website" in result
            assert "**URL:** https://www.python.org" in result
            assert "**Relevance Score:** 0.95" in result

    def test_search_without_answer(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response_no_answer,
    ):
        """Test search without answer section."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response_no_answer
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test query",
                include_answer=False,
            )

            # Verify no answer section
            assert "## Answer" not in result
            assert "## Search Results" in result
            assert "### 1. Search Result" in result

    def test_search_empty_results(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response_empty,
    ):
        """Test search with no results."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response_empty
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="nonexistent query",
            )

            assert "No results found." in result

    def test_search_with_advanced_depth(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test search with advanced depth."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="advanced query",
                search_depth="advanced",
                max_results=10,
            )

            # Verify search was called with advanced depth
            mock_client.search.assert_called_once_with(
                query="advanced query",
                max_results=10,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
            )

            assert "## Search Results" in result

    def test_search_with_raw_content(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test search with raw content enabled."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test",
                include_raw_content=True,
            )

            # Verify search was called with include_raw_content=True
            mock_client.search.assert_called_once()
            call_kwargs = mock_client.search.call_args[1]
            assert call_kwargs["include_raw_content"] is True

    def test_missing_api_key_no_config_no_env(
        self,
        mock_tool_runtime,
        clear_tavily_api_key,
    ):
        """Test error when API key is missing from both config and environment."""
        with patch("deer_code.tools.search.tavily_search.get_config_section") as mock_config:
            mock_config.return_value = None

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test",
            )

            assert "Error: Tavily API key not found" in result
            assert "config.yaml" in result
            assert "TAVILY_API_KEY" in result

    def test_api_key_from_config(
        self,
        mock_tool_runtime,
        clear_tavily_api_key,
        sample_tavily_response,
    ):
        """Test that API key is read from config when not in environment."""
        config_api_key = "config_api_key_xyz"

        with patch("deer_code.tools.search.tavily_search.get_config_section") as mock_config:
            mock_config.return_value = config_api_key

            with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.search.return_value = sample_tavily_response
                mock_client_class.return_value = mock_client

                result = tavily_search_tool.func(
                    runtime=mock_tool_runtime,
                    query="test",
                )

                # Verify TavilyClient was initialized with config API key
                mock_client_class.assert_called_once_with(api_key=config_api_key)
                assert "## Search Results" in result

    def test_api_key_fallback_to_env(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test that API key falls back to environment variable when not in config."""
        with patch("deer_code.tools.search.tavily_search.get_config_section") as mock_config:
            mock_config.return_value = None

            with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.search.return_value = sample_tavily_response
                mock_client_class.return_value = mock_client

                result = tavily_search_tool.func(
                    runtime=mock_tool_runtime,
                    query="test",
                )

                # Verify TavilyClient was initialized with env API key
                mock_client_class.assert_called_once_with(api_key=mock_tavily_api_key)
                assert "## Search Results" in result

    def test_api_key_env_var_expansion(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test that API key with $ENV_VAR syntax is expanded correctly."""
        with patch("deer_code.tools.search.tavily_search.get_config_section") as mock_config:
            # Config returns "$TAVILY_API_KEY" which should be expanded
            mock_config.return_value = "$TAVILY_API_KEY"

            with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client.search.return_value = sample_tavily_response
                mock_client_class.return_value = mock_client

                result = tavily_search_tool.func(
                    runtime=mock_tool_runtime,
                    query="test",
                )

                # Verify TavilyClient was initialized with expanded env API key
                mock_client_class.assert_called_once_with(api_key=mock_tavily_api_key)
                assert "## Search Results" in result

    def test_tavily_client_exception(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
    ):
        """Test error handling when TavilyClient raises an exception."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.side_effect = Exception("API connection failed")
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test",
            )

            assert "Error performing Tavily search" in result
            assert "API connection failed" in result

    def test_result_without_title(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
    ):
        """Test handling of search result without title."""
        response_no_title = {
            "results": [
                {
                    "url": "https://example.com",
                    "content": "Content without title",
                }
            ]
        }

        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = response_no_title
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test",
            )

            assert "### 1. No Title" in result
            assert "**URL:** https://example.com" in result

    def test_result_without_score(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
    ):
        """Test handling of search result without score."""
        response_no_score = {
            "results": [
                {
                    "title": "Test Title",
                    "url": "https://example.com",
                    "content": "Test content",
                }
            ]
        }

        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = response_no_score
            mock_client_class.return_value = mock_client

            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test",
            )

            assert "**Relevance Score:**" not in result
            assert "### 1. Test Title" in result

    def test_default_parameters(
        self,
        mock_tool_runtime,
        mock_tavily_api_key,
        sample_tavily_response,
    ):
        """Test that default parameters are applied correctly."""
        with patch("deer_code.tools.search.tavily_search.TavilyClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.search.return_value = sample_tavily_response
            mock_client_class.return_value = mock_client

            # Call with only required parameter
            result = tavily_search_tool.func(
                runtime=mock_tool_runtime,
                query="test query",
            )

            # Verify defaults were used
            mock_client.search.assert_called_once_with(
                query="test query",
                max_results=5,  # default
                search_depth="basic",  # default
                include_answer=True,  # default
                include_raw_content=False,  # default
            )

            assert "## Search Results" in result


@pytest.mark.integration
class TestTavilySearchToolIntegration:
    """Integration tests for tavily_search_tool (requires real API key)."""

    @pytest.mark.skipif(
        not os.getenv("TAVILY_API_KEY"),
        reason="TAVILY_API_KEY environment variable not set",
    )
    def test_real_search(self, mock_tool_runtime):
        """Test real search with actual Tavily API (requires API key)."""
        result = tavily_search_tool.func(
            runtime=mock_tool_runtime,
            query="Python programming language",
            max_results=3,
        )

        # Basic sanity checks
        assert "Error" not in result
        assert "## Search Results" in result or "## Answer" in result

    @pytest.mark.skipif(
        not os.getenv("TAVILY_API_KEY"),
        reason="TAVILY_API_KEY environment variable not set",
    )
    def test_real_search_advanced(self, mock_tool_runtime):
        """Test real search with advanced depth (requires API key)."""
        result = tavily_search_tool.func(
            runtime=mock_tool_runtime,
            query="artificial intelligence",
            max_results=2,
            search_depth="advanced",
        )

        assert "Error" not in result
        assert "## Search Results" in result or "## Answer" in result
