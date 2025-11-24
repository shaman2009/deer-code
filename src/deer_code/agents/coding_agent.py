import os

from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware
from langchain.tools import BaseTool
from langgraph.checkpoint.base import RunnableConfig

from deer_code.models import init_chat_model
from deer_code.project import project
from deer_code.prompts import apply_prompt_template
from deer_code.tools.tool_groups import ToolGroup, get_tools_by_groups


def create_coding_agent(
    plugin_tools: list[BaseTool] | None = None,
    enabled_tool_groups: list[ToolGroup | str] | None = None,
    **kwargs,
):
    """Create a coding agent.

    Args:
        plugin_tools: Additional tools to add to the agent.
        enabled_tool_groups: List of tool groups to enable. If None, enables all coding tools.
                           Can be ToolGroup enums or strings like "filesystem", "editor", "terminal".
        **kwargs: Additional keyword arguments to pass to the agent.

    Returns:
        The coding agent.

    Example:
        # Use default coding tools
        agent = create_coding_agent()

        # Use only filesystem and editor tools
        agent = create_coding_agent(
            enabled_tool_groups=[ToolGroup.FILESYSTEM, ToolGroup.EDITOR]
        )

        # Use all tools with additional plugins
        agent = create_coding_agent(plugin_tools=[my_custom_tool])
    """
    if plugin_tools is None:
        plugin_tools = []

    # Get tools by groups
    if enabled_tool_groups is None:
        # Default: filesystem, editor, terminal
        enabled_tool_groups = [
            ToolGroup.FILESYSTEM,
            ToolGroup.EDITOR,
            ToolGroup.TERMINAL,
        ]

    core_tools = get_tools_by_groups(enabled_tool_groups)

    # Get project context
    try:
        project_ctx = project.get_context()
        project_info = {
            "PROJECT_ROOT": project.root_dir,
            "PROJECT_TYPE": project_ctx.project_type.value,
            "PACKAGE_MANAGER": project_ctx.package_manager or "unknown",
            "PROJECT_CONTEXT": project_ctx.get_context_summary(),
        }
    except Exception:
        # Fallback if context detection fails
        project_info = {
            "PROJECT_ROOT": project.root_dir,
            "PROJECT_TYPE": "unknown",
            "PACKAGE_MANAGER": "unknown",
            "PROJECT_CONTEXT": "Could not detect project context",
        }

    return create_agent(
        model=init_chat_model(),
        tools=[*core_tools, *plugin_tools],
        system_prompt=apply_prompt_template("coding_agent", **project_info),
        middleware=[TodoListMiddleware()],
        name="coding_agent",
        **kwargs,
    )


def create_coding_agent_for_debug(config: RunnableConfig):
    project.root_dir = os.getenv("PROJECT_ROOT", os.getcwd())
    return create_coding_agent(debug=True)
