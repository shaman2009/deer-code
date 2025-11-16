# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeerCode is a minimalist AI coding agent with a VSCode-like TUI interface. It demonstrates the ReAct framework (Reasoning, Acting, Acting) using LangGraph for agent orchestration and Textual for the terminal UI.

**Key Technologies**: Python 3.12+, LangGraph, LangChain, Textual, pexpect

## Development Commands

### Setup and Installation
```bash
make install              # Install dependencies (uv sync)
cp config.example.yaml config.yaml  # Create config file (edit with your API keys)
```

### Running the Application
```bash
# CLI mode (analyze a specific project)
uv run -m deer_code.main "/path/to/your/project"

# Development mode (requires langgraph-cli)
# First, edit langgraph.json and set env.PROJECT_ROOT to your test project path
make dev
# Then visit: https://agentchat.vercel.app/?apiUrl=http://localhost:2024&assistantId=coding_agent
```

### Build
```bash
make build                # Build the package (uv build)
```

## Architecture Overview

### Core Design: Dual-Layer Architecture

```
User Interaction (TUI Layer)
    ↓
ConsoleApp (Textual TUI)
    ↓
CodingAgent (LangGraph State Graph)
    ↓
Tools (bash, text_editor, grep, ls, tree, todo_write, MCP tools)
```

### Message Flow (Critical to Understand)

1. **User Input** → `HumanMessage` → ConsoleApp receives input
2. **Agent Processing** → `coding_agent.astream()` with `stream_mode="updates"`
3. **Tool Invocation** → Agent returns `AIMessage` with `tool_calls`
4. **UI Updates** → `_process_tool_call_message()` routes to appropriate UI component:
   - `bash`/`grep`/`ls`/`tree` → TerminalView
   - `text_editor` → EditorTabs (opens/creates files)
   - `todo_write` → TodoListView
5. **Tool Execution** → Returns `ToolMessage` with results
6. **Display Results** → `_process_tool_message()` shows output in UI

### Key Components

**Agent System** (`agents/coding_agent.py`):
- Uses `create_agent()` from LangChain to build a ReAct agent
- State schema: `CodingAgentState` extends `MessagesState` with `todos` field
- System prompt from `prompts/templates/coding_agent.md` (Jinja2 template)
- Recursion limit: 100 (configurable in `app.py:152`)

**Tool System** (`tools/`):
- All tools use `@tool` decorator with `parse_docstring=True`
- Tools receive `ToolRuntime` for context (e.g., generating reminders)
- **BashTerminal** maintains session state using `pexpect.spawn("/bin/bash")`
  - Single global instance (`keep_alive_terminal`) preserves cwd and env vars
  - Custom prompt for output parsing: `DEERCODE_PROMPT_1234567890`
- **TextEditor** supports: `view`, `create`, `str_replace`, `insert`
- **MCP Tools** loaded asynchronously on startup (`_init_agent()`)

**UI System** (`cli/`):
- Layout: Left panel (3fr) = Chat | Right panel (4fr) = Editor (70%) + Terminal/Todo tabs (30%)
- `@work(exclusive=True, thread=False)` decorator for async message handling
- Theme: `DEER_DARK_THEME` with VSCode-inspired colors

### Configuration System

**config.yaml** structure:
```yaml
models:
  chat_model:
    type: deepseek | doubao | (omit for OpenAI-compatible)
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY  # Environment variable expansion supported
    temperature: 0
    max_tokens: 8192
    extra_body: {}  # Model-specific params (e.g., reasoning_effort for OpenAI)

tools:
  mcp_servers:
    server_name:
      transport: 'streamable_http'
      url: 'https://...'
```

- Config loaded once on startup (`config/config.py`)
- Access via `get_config_section(["models", "chat_model"])`
- Model initialization in `models/chat_model.py` supports OpenAI, DeepSeek, Doubao

## Critical Implementation Details

### Async Streaming Pattern
The app uses `astream()` with `stream_mode="updates"` to receive incremental updates from LangGraph. Each node execution produces a chunk. This is NOT token-level streaming - it's node-level.

```python
async for chunk in self._coding_agent.astream(
    {"messages": [user_message]},
    stream_mode="updates",
    config={"recursion_limit": 100, "thread_id": "thread_1"},
):
    # chunk = {role: {"messages": [...]}}
```

### Tool Call Tracking
The app maintains two tracking dicts:
- `_terminal_tool_calls: list[str]` - IDs of tools that output to terminal
- `_mutable_text_editor_tool_calls: dict[str, str]` - Maps tool call IDs to file paths for editor tools

This allows matching `ToolMessage` responses to the correct UI component.

### State Persistence
- **Bash session**: Persisted via single `BashTerminal` instance (cwd, env vars preserved)
- **LangGraph state**: Managed by LangGraph with `thread_id="thread_1"` (all conversations in one thread)
- **UI state**: Textual manages widget state; editor tabs persist until closed

## Adding New Tools

1. Create tool file in `tools/your_tool/tool.py`:
```python
from langchain.tools import tool, ToolRuntime

@tool("your_tool", parse_docstring=True)
def your_tool(runtime: ToolRuntime, param: str):
    """Tool description for LLM.

    Args:
        param: Parameter description
    """
    return "result"
```

2. Import and register in `agents/coding_agent.py`:
```python
from deer_code.tools.your_tool import your_tool

tools = [bash_tool, ..., your_tool, *plugin_tools]
```

3. Handle in UI if needed (`cli/app.py:_process_tool_call_message()`):
```python
elif tool_name == "your_tool":
    # Update UI component
```

## Modifying System Prompts

Edit `prompts/templates/coding_agent.md` (Jinja2 template). Variables are passed via `apply_prompt_template("coding_agent", PROJECT_ROOT=...)`. The template includes:
- TODO usage guidelines (when to use `todo_write` tool)
- Frontend technology defaults (React, Next.js, Tailwind, etc.)
- Agent behavior rules

Changes take effect on next agent creation (app restart or `_init_agent()`).

## Model Support

To add a new model provider, modify `models/chat_model.py`:
1. Add type detection in `init_chat_model()`
2. Import appropriate LangChain chat model class
3. Handle provider-specific parameters from `extra_body`

Current providers: OpenAI-compatible (default), DeepSeek (`type: deepseek`), Doubao (`type: doubao`)
