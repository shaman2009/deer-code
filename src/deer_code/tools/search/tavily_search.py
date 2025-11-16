import os
from typing import Literal, Optional

from langchain.tools import ToolRuntime, tool
from tavily import TavilyClient

from deer_code.config import get_config_section


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
    # Get Tavily API key from config
    api_key = get_config_section(["tools", "tavily", "api_key"])
    if not api_key:
        # Fallback to environment variable
        api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return "Error: Tavily API key not found. Please set it in config.yaml under tools.tavily.api_key or set the TAVILY_API_KEY environment variable."

    try:
        # Initialize Tavily client
        client = TavilyClient(api_key=api_key)

        # Perform search
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
        )

        # Format the response
        result_lines = []

        # Add answer if available
        if include_answer and response.get("answer"):
            result_lines.append("## Answer")
            result_lines.append(response["answer"])
            result_lines.append("")

        # Add search results
        if response.get("results"):
            result_lines.append("## Search Results")
            result_lines.append("")

            for idx, result in enumerate(response["results"], 1):
                result_lines.append(f"### {idx}. {result.get('title', 'No Title')}")
                result_lines.append(f"**URL:** {result.get('url', 'N/A')}")
                result_lines.append(f"**Content:** {result.get('content', 'No content available')}")
                if result.get("score"):
                    result_lines.append(f"**Relevance Score:** {result['score']:.2f}")
                result_lines.append("")
        else:
            result_lines.append("No results found.")

        return "\n".join(result_lines)

    except Exception as e:
        return f"Error performing Tavily search: {str(e)}"
