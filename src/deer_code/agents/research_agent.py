import os

from langchain.agents import create_agent
from langchain.tools import BaseTool
from langgraph.checkpoint.base import RunnableConfig

from deer_code.models import init_chat_model
from deer_code.project import project
from deer_code.prompts import apply_prompt_template
from deer_code.tools import tavily_search_tool, todo_write_tool

from .state import ResearchAgentState


def create_research_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """Create a research agent.

    Args:
        plugin_tools: Additional tools to add to the agent.
        **kwargs: Additional keyword arguments to pass to the agent.

    Returns:
        The research agent.
    """
    return create_agent(
        model=init_chat_model(),
        tools=[
            tavily_search_tool,
            todo_write_tool,
            *plugin_tools,
        ],
        system_prompt=apply_prompt_template("research_agent"),
        state_schema=ResearchAgentState,
        name="research_agent",
        **kwargs,
    )


def create_research_agent_for_debug(config: RunnableConfig):
    project.root_dir = os.getenv("PROJECT_ROOT", os.getcwd())
    return create_research_agent(debug=True)
