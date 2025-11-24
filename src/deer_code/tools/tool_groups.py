"""Tool group management for organizing agent tools."""

from enum import Enum
from typing import Literal

from langchain.tools import BaseTool


class ToolGroup(str, Enum):
    """Tool groups for organizing tools by functionality."""

    FILESYSTEM = "filesystem"
    EDITOR = "editor"
    TERMINAL = "terminal"
    SEARCH = "search"
    ALL = "all"


# Tool group definitions
TOOL_GROUPS: dict[ToolGroup, list[str]] = {
    ToolGroup.FILESYSTEM: ["grep", "ls", "tree"],
    ToolGroup.EDITOR: ["text_editor"],
    ToolGroup.TERMINAL: ["bash"],
    ToolGroup.SEARCH: ["perplexity_search", "tavily_search"],
}


def get_tools_by_groups(
    groups: list[ToolGroup | Literal["all"]] | None = None,
) -> list[BaseTool]:
    """Get tools by group names.

    Args:
        groups: List of tool groups to include. If None or contains "all",
               returns all available tools.

    Returns:
        List of tool instances for the specified groups.

    Example:
        # Get filesystem tools only
        tools = get_tools_by_groups([ToolGroup.FILESYSTEM])

        # Get filesystem and editor tools
        tools = get_tools_by_groups([ToolGroup.FILESYSTEM, ToolGroup.EDITOR])

        # Get all tools
        tools = get_tools_by_groups([ToolGroup.ALL])
        tools = get_tools_by_groups()  # Same as above
    """
    from deer_code.tools import (
        bash_tool,
        grep_tool,
        ls_tool,
        perplexity_search_tool,
        tavily_search_tool,
        text_editor_tool,
        tree_tool,
    )

    # Mapping of tool names to tool instances
    all_tools: dict[str, BaseTool] = {
        "bash": bash_tool,
        "grep": grep_tool,
        "ls": ls_tool,
        "text_editor": text_editor_tool,
        "tree": tree_tool,
        "perplexity_search": perplexity_search_tool,
        "tavily_search": tavily_search_tool,
    }

    # If no groups specified or "all" is in groups, return all tools
    if groups is None or ToolGroup.ALL in groups or "all" in groups:
        return list(all_tools.values())

    # Collect tools from specified groups
    selected_tools: list[BaseTool] = []
    seen_tool_names: set[str] = set()

    for group in groups:
        if isinstance(group, str):
            group = ToolGroup(group)

        tool_names = TOOL_GROUPS.get(group, [])
        for tool_name in tool_names:
            if tool_name not in seen_tool_names:
                tool = all_tools.get(tool_name)
                if tool:
                    selected_tools.append(tool)
                    seen_tool_names.add(tool_name)

    return selected_tools


def get_tool_groups_for_agent(agent_name: str) -> list[ToolGroup]:
    """Get recommended tool groups for a specific agent type.

    Args:
        agent_name: The name of the agent (e.g., "coding_agent", "research_agent").

    Returns:
        List of recommended tool groups for the agent.

    Example:
        groups = get_tool_groups_for_agent("coding_agent")
        tools = get_tools_by_groups(groups)
    """
    # Default tool groups for different agent types
    agent_tool_groups = {
        "coding_agent": [
            ToolGroup.FILESYSTEM,
            ToolGroup.EDITOR,
            ToolGroup.TERMINAL,
        ],
        "research_agent": [
            ToolGroup.SEARCH,
        ],
    }

    return agent_tool_groups.get(agent_name, [ToolGroup.ALL])
