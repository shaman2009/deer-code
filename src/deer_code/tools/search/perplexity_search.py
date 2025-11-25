import os
from functools import lru_cache
from typing import Literal, Optional

import httpx
from langchain.tools import ToolRuntime, tool

from deer_code.config import get_config_section

# Module-level HTTP client with connection pooling for better performance
_perplexity_client: Optional[httpx.Client] = None


def get_perplexity_client() -> httpx.Client:
    """Get or create a reusable HTTP client with connection pooling.

    This avoids the overhead of creating a new client and TCP connection
    for each API call, reducing latency by 100-300ms per request.
    """
    global _perplexity_client
    if _perplexity_client is None:
        _perplexity_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0,
            ),
        )
    return _perplexity_client


@lru_cache(maxsize=1)
def get_perplexity_config() -> tuple[Optional[str], str]:
    """Get Perplexity API configuration with caching.

    Caches the API key and model name to avoid repeated config reads
    and environment variable expansion on every tool call.

    Returns:
        Tuple of (api_key, model_name)
    """
    config = get_config_section(["tools", "perplexity"])
    api_key = config.get("api_key") if config else None

    if not api_key:
        # Fallback to environment variable
        api_key = os.getenv("PERPLEXITY_API_KEY")
    elif api_key.startswith("$"):
        # Expand environment variable from config
        api_key = os.getenv(api_key[1:])

    # Get model configuration
    model_name = config.get("model", "sonar") if config else "sonar"

    return api_key, model_name


@tool("perplexity_search", parse_docstring=True)
def perplexity_search_tool(
    runtime: ToolRuntime,
    query: str,
    recency: Optional[Literal["day", "week", "month", "year"]] = None,
    domains: Optional[list[str]] = None,
):
    """Search the web using Perplexity API and return a synthesized answer with citations.

    This tool returns a comprehensive, AI-synthesized answer from Perplexity, suitable for
    quick factual lookups. For in-depth analysis requiring multiple sources or complex
    research tasks, consider using tavily_search instead.

    Args:
        query: The search query string.
        recency: Time range filter - "day", "week", "month", or "year" (optional).
        domains: List of domains to restrict search, e.g. ["python.org"] (optional).
    """
    # Get cached configuration
    api_key, model_name = get_perplexity_config()

    if not api_key:
        return "Error: Perplexity API key not found. Please set it in config.yaml under tools.perplexity.api_key or set the PERPLEXITY_API_KEY environment variable."

    try:
        # Build request payload
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": query}],
        }

        # Add Perplexity-specific parameters
        if recency:
            payload["search_recency_filter"] = recency

        if domains:
            payload["search_domain_filter"] = domains

        # Make API request using connection-pooled client
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        client = get_perplexity_client()
        response = client.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        # Extract answer from response
        if not data.get("choices") or len(data["choices"]) == 0:
            return "Error performing Perplexity search: API returned no response choices"

        answer = data["choices"][0]["message"]["content"]

        # Format the response using optimized string building
        output_parts = [f"## Answer\n{answer}\n"]

        # Extract citations from search_results field
        if "search_results" in data and data["search_results"]:
            output_parts.append("\n## Citations\n")

            citation_idx = 1
            for result in data["search_results"]:
                title = result.get("title", "No Title")
                url = result.get("url", "")
                date = result.get("date", "")

                # Format as Markdown link (skip if no URL)
                if url:
                    citation = f"{citation_idx}. [{title}]({url})"
                    if date:
                        citation += f" ({date})"
                    output_parts.append(citation + "\n")
                    citation_idx += 1

        return "".join(output_parts)

    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if len(e.response.text) > 500 else e.response.text
        return f"Error performing Perplexity search: HTTP {e.response.status_code} - {error_text}"
    except httpx.RequestError as e:
        return f"Error performing Perplexity search: Network error - {str(e)}"
    except KeyError as e:
        return f"Error performing Perplexity search: Unexpected response format - missing {str(e)}"
    except Exception as e:
        return f"Error performing Perplexity search: {str(e)}"
