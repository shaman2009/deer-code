import os
from functools import lru_cache
from typing import Literal, Optional

from langchain.tools import ToolRuntime, tool
from tavily import TavilyClient

from deer_code.config import get_config_section


@lru_cache(maxsize=1)
def get_tavily_client(api_key: str) -> TavilyClient:
    """Get or create a cached Tavily client instance.

    Caching the client avoids repeated initialization overhead
    and allows connection reuse across multiple searches.

    Args:
        api_key: The Tavily API key

    Returns:
        Cached TavilyClient instance
    """
    return TavilyClient(api_key=api_key)


@lru_cache(maxsize=1)
def get_tavily_config() -> Optional[str]:
    """Get Tavily API key with caching.

    Caches the API key to avoid repeated config reads and
    environment variable expansion on every tool call.

    Returns:
        The API key or None if not found
    """
    # Get Tavily API key from config
    api_key = get_config_section(["tools", "tavily", "api_key"])
    if not api_key:
        # Fallback to environment variable
        api_key = os.getenv("TAVILY_API_KEY")
    elif api_key.startswith("$"):
        # Expand environment variable from config
        api_key = os.getenv(api_key[1:])

    return api_key


@tool("tavily_search", parse_docstring=True)
def tavily_search_tool(
    runtime: ToolRuntime,
    query: str,
    max_results: int = 5,
    search_depth: Literal["basic", "advanced"] = "basic",
    include_answer: bool = True,
    include_raw_content: bool = False,
):
    """Search the web using Tavily API and return relevant results.

    Args:
        query: The search query string.
        max_results: Maximum number of search results to return (default: 5).
        search_depth: Search depth, either "basic" or "advanced" (default: "basic").
        include_answer: Whether to include a short answer to the query (default: True).
        include_raw_content: Whether to include raw HTML content (default: False).
    """
    # Get cached API key
    api_key = get_tavily_config()

    if not api_key:
        return "Error: Tavily API key not found. Please set it in config.yaml under tools.tavily.api_key or set the TAVILY_API_KEY environment variable."

    try:
        # Get cached Tavily client
        client = get_tavily_client(api_key)

        # Perform search
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
        )

        # Format the response using optimized string building
        # Use f-string concatenation for better performance with moderate-sized outputs
        output_parts = []

        # Add answer if available
        if include_answer and response.get("answer"):
            output_parts.append(f"## Answer\n{response['answer']}\n")

        # Add search results
        if response.get("results"):
            output_parts.append("## Search Results\n")

            for idx, result in enumerate(response["results"], 1):
                title = result.get("title", "No Title")
                url = result.get("url", "N/A")
                content = result.get("content", "No content available")

                result_text = f"### {idx}. {title}\n**URL:** {url}\n**Content:** {content}\n"

                # Add relevance score if available
                if result.get("score"):
                    result_text += f"**Relevance Score:** {result['score']:.2f}\n"

                result_text += "\n"
                output_parts.append(result_text)
        else:
            output_parts.append("No results found.")

        return "".join(output_parts)

    except Exception as e:
        return f"Error performing Tavily search: {str(e)}"
