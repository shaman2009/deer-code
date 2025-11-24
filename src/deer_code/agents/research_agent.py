import os

from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware
from langchain.tools import BaseTool
from langgraph.checkpoint.base import RunnableConfig

from deer_code.models import init_chat_model
from deer_code.project import project
from deer_code.prompts import apply_prompt_template
from deer_code.tools import perplexity_search_tool, tavily_search_tool


def create_research_agent(plugin_tools: list[BaseTool] | None = None, **kwargs):
    """Create a research agent with todo list capabilities.

    Args:
        plugin_tools: Additional tools to add to the agent.
        **kwargs: Additional keyword arguments to pass to the agent.

    Returns:
        The research agent with TodoListMiddleware enabled.
    """
    if plugin_tools is None:
        plugin_tools = []
    return create_agent(
        model=init_chat_model(),
        tools=[
            perplexity_search_tool,
            tavily_search_tool,
            *plugin_tools,
        ],
        system_prompt=apply_prompt_template("research_agent"),
        middleware=[TodoListMiddleware()],
        name="research_agent",
        **kwargs,
    )


def create_research_agent_for_debug(config: RunnableConfig):
    project.root_dir = os.getenv("PROJECT_ROOT", os.getcwd())
    return create_research_agent(debug=True)
