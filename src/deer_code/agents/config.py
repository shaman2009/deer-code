"""Configuration models for agents."""

from pydantic import BaseModel, Field

from deer_code.tools.tool_groups import ToolGroup


class AgentConfig(BaseModel):
    """Base configuration for all agents."""

    recursion_limit: int = Field(default=100, ge=1, le=500, description="Maximum recursion depth for agent")
    enable_debug: bool = Field(default=False, description="Enable debug mode")


class CodingAgentConfig(AgentConfig):
    """Configuration for the coding agent."""

    enabled_tool_groups: list[ToolGroup | str] = Field(
        default_factory=lambda: [
            ToolGroup.FILESYSTEM,
            ToolGroup.EDITOR,
            ToolGroup.TERMINAL,
        ],
        description="Tool groups to enable for the coding agent",
    )

    class Config:
        use_enum_values = True


class ResearchAgentConfig(AgentConfig):
    """Configuration for the research agent."""

    enabled_tool_groups: list[ToolGroup | str] = Field(
        default_factory=lambda: [ToolGroup.SEARCH],
        description="Tool groups to enable for the research agent",
    )

    class Config:
        use_enum_values = True
