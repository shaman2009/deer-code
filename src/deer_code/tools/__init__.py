# Lazy imports to avoid loading langchain dependencies at import time
# This allows tests to import specific modules without triggering all dependencies

__all__ = [
    "bash_tool",
    "grep_tool",
    "load_mcp_tools",
    "ls_tool",
    "perplexity_search_tool",
    "tavily_search_tool",
    "text_editor_tool",
    "todo_write_tool",
    "tree_tool",
]


def __getattr__(name):
    """Lazy import tool attributes to avoid loading heavy dependencies at import time."""
    if name == "text_editor_tool":
        from .edit import text_editor_tool
        return text_editor_tool
    elif name == "grep_tool":
        from .fs import grep_tool
        return grep_tool
    elif name == "ls_tool":
        from .fs import ls_tool
        return ls_tool
    elif name == "tree_tool":
        from .fs import tree_tool
        return tree_tool
    elif name == "load_mcp_tools":
        from .mcp import load_mcp_tools
        return load_mcp_tools
    elif name == "perplexity_search_tool":
        from .search import perplexity_search_tool
        return perplexity_search_tool
    elif name == "tavily_search_tool":
        from .search import tavily_search_tool
        return tavily_search_tool
    elif name == "bash_tool":
        from .terminal.tool import bash_tool
        return bash_tool
    elif name == "todo_write_tool":
        from .todo import todo_write_tool
        return todo_write_tool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
