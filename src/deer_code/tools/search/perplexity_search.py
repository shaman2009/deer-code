import os
from typing import Literal, Optional

import httpx
from langchain.tools import ToolRuntime, tool

from deer_code.config import get_config_section


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

    Typical use cases:
    - Query software versions, release dates, and other factual information
    - Get quick explanations of technical concepts
    - Search official documentation (using domains parameter)
    - Find latest information (using recency parameter)

    Args:
        query: The search query - should be clear, specific, and focused.
        recency: Limit search results by time range (optional).
            - "day": Only search content from the last day
            - "week": Only search content from the last week
            - "month": Only search content from the last month
            - "year": Only search content from the last year
            Use this for rapidly evolving technical topics.
        domains: List of domains to restrict search to (optional).
            Example: ["python.org", "github.com"] to search only official docs
            Improves answer authority and accuracy.

    Returns:
        Formatted text containing synthesized answer and citation sources.
    """
    # Get API key from config
    config = get_config_section(["tools", "perplexity"])
    api_key = config.get("api_key") if config else None

    if not api_key:
        # Fallback to environment variable
        api_key = os.getenv("PERPLEXITY_API_KEY")
    elif api_key.startswith("$"):
        # Expand environment variable from config
        api_key = os.getenv(api_key[1:])

    if not api_key:
        return "Error: Perplexity API key not found. Please set it in config.yaml under tools.perplexity.api_key or set the PERPLEXITY_API_KEY environment variable."

    # Get model configuration
    model_name = config.get("model", "sonar") if config else "sonar"

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

        # Make API request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client() as client:
            response = client.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        # Extract answer from response
        answer = data["choices"][0]["message"]["content"]

        # Format the response
        result_lines = []
        result_lines.append("## Answer")
        result_lines.append(answer)
        result_lines.append("")

        # Extract citations from search_results field
        if "search_results" in data and data["search_results"]:
            result_lines.append("## Citations")
            for idx, result in enumerate(data["search_results"], 1):
                title = result.get("title", "No Title")
                url = result.get("url", "")
                date = result.get("date", "")

                # Format as Markdown link
                citation = f"{idx}. [{title}]({url})"
                if date:
                    citation += f" ({date})"
                result_lines.append(citation)
            result_lines.append("")

        return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"Error performing Perplexity search: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error performing Perplexity search: Network error - {str(e)}"
    except KeyError as e:
        return f"Error performing Perplexity search: Unexpected response format - missing {str(e)}"
    except Exception as e:
        return f"Error performing Perplexity search: {str(e)}"
