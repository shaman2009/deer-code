import os
from typing import Literal, Optional

from langchain.tools import ToolRuntime, tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

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
        # Build model_kwargs for Perplexity-specific parameters
        model_kwargs = {
            "return_citations": True,
        }

        if recency:
            model_kwargs["search_recency_filter"] = recency

        if domains:
            model_kwargs["search_domain_filter"] = domains

        # Initialize ChatOpenAI with Perplexity endpoint
        model = ChatOpenAI(
            base_url="https://api.perplexity.ai",
            api_key=api_key,
            model=model_name,
            model_kwargs=model_kwargs,
        )

        # Perform search
        response = model.invoke([HumanMessage(content=query)])

        # Format the response
        result_lines = []

        # Add answer
        result_lines.append("## Answer")
        result_lines.append(response.content)
        result_lines.append("")

        # Add citations if available
        if hasattr(response, "response_metadata"):
            citations = response.response_metadata.get("citations", [])
            if citations:
                result_lines.append("## Citations")
                for idx, citation in enumerate(citations, 1):
                    result_lines.append(f"{idx}. {citation}")
                result_lines.append("")

        return "\n".join(result_lines)

    except Exception as e:
        return f"Error performing Perplexity search: {str(e)}"
