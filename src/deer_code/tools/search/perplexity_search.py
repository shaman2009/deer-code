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

    Args:
        query: The search query string.
        recency: Time range filter - "day", "week", "month", or "year" (optional).
        domains: List of domains to restrict search, e.g. ["python.org"] (optional).
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
        if not data.get("choices") or len(data["choices"]) == 0:
            return "Error performing Perplexity search: API returned no response choices"

        answer = data["choices"][0]["message"]["content"]

        # Format the response
        result_lines = []
        result_lines.append("## Answer")
        result_lines.append(answer)
        result_lines.append("")

        # Extract citations from search_results field
        if "search_results" in data and data["search_results"]:
            result_lines.append("## Citations")
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
                    result_lines.append(citation)
                    citation_idx += 1
            result_lines.append("")

        return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        error_text = e.response.text[:500] if len(e.response.text) > 500 else e.response.text
        return f"Error performing Perplexity search: HTTP {e.response.status_code} - {error_text}"
    except httpx.RequestError as e:
        return f"Error performing Perplexity search: Network error - {str(e)}"
    except KeyError as e:
        return f"Error performing Perplexity search: Unexpected response format - missing {str(e)}"
    except Exception as e:
        return f"Error performing Perplexity search: {str(e)}"
