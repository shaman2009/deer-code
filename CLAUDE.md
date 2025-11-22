# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeerCode is a minimalist AI coding agent with a VSCode-like TUI interface. It demonstrates the ReAct framework (Reasoning, Acting, Acting) using LangGraph for agent orchestration and Textual for the terminal UI.

**Key Technologies**: Python 3.12+, LangGraph, LangChain, Textual, pexpect, Tavily

**Key Dependencies**:
- `langchain` & `langgraph` - Agent orchestration and tool management
- `langchain-mcp-adapters` - MCP tool integration
- `langchain-deepseek` - DeepSeek model support
- `textual` - Terminal UI framework
- `pexpect` - Persistent bash terminal sessions
- `tavily-python` - Web search capabilities
- `rich` - Terminal formatting
- `jinja2` - System prompt templating
- `httpx[socks]` - HTTP client with SOCKS proxy support

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

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=deer_code --cov-report=html

# Run specific test types
uv run pytest -m unit        # Unit tests only
uv run pytest -m integration # Integration tests only
```

## Directory Structure

```
deer-code/
├── src/deer_code/              # Main source code
│   ├── agents/                 # Agent implementations
│   │   ├── coding_agent.py     # Main coding agent (bash, edit, grep, ls, tree, todo)
│   │   ├── research_agent.py   # Research agent (Tavily search + TodoListMiddleware)
│   │   └── state.py            # CodingAgentState (MessagesState + todos)
│   ├── cli/                    # Textual TUI components
│   │   ├── app.py              # ConsoleApp - main TUI application
│   │   ├── theme.py            # DEER_DARK_THEME color scheme
│   │   └── components/         # UI widgets
│   │       ├── chat/           # Chat interface (view, messages, input, loading)
│   │       ├── editor/         # Code editor tabs and display
│   │       ├── terminal/       # Terminal output view
│   │       └── todo/           # Todo list view
│   ├── config/                 # Configuration management
│   │   └── config.py           # YAML config loader with $ENV_VAR expansion
│   ├── models/                 # LLM model initialization
│   │   └── chat_model.py       # Multi-provider support (OpenAI, DeepSeek, Doubao)
│   ├── prompts/                # System prompt templates
│   │   ├── template.py         # Jinja2 template renderer
│   │   └── templates/          # Prompt files
│   │       ├── coding_agent.md # Coding agent system prompt
│   │       └── research_agent.md # Research agent system prompt
│   ├── tools/                  # Tool implementations
│   │   ├── edit/               # Text editor (view, create, str_replace, insert)
│   │   ├── fs/                 # File system tools
│   │   │   ├── grep.py         # Ripgrep search with context
│   │   │   ├── ls.py           # Directory listing with filtering
│   │   │   ├── tree.py         # Recursive directory tree (max depth 3)
│   │   │   └── ignore.py       # DEFAULT_IGNORE_PATTERNS (77 patterns)
│   │   ├── mcp/                # MCP tool loader (async)
│   │   ├── search/             # Web search tools (Tavily, Perplexity)
│   │   ├── terminal/           # Bash terminal with pexpect
│   │   ├── todo/               # Todo management (state updates)
│   │   └── reminders.py        # Generates reminders for unfinished todos
│   ├── main.py                 # Entry point (loads dotenv, launches TUI)
│   └── project.py              # Project root directory management
├── docs/                       # Documentation (Chinese)
│   ├── ARCHITECTURE.md         # Technical architecture
│   ├── BUSINESS.md             # Business documentation
│   ├── FRAMEWORKS.md           # Framework documentation
│   └── PACKAGES.md             # Package documentation
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures
│   ├── tools/search/           # Tavily search tests
│   └── README.md               # Test documentation
├── pyproject.toml              # Project metadata and dependencies
├── Makefile                    # Build commands (install, build, dev)
├── langgraph.json              # LangGraph CLI configuration
├── config.example.yaml         # Configuration template
└── CLAUDE.md                   # This file - AI assistant guide
```

## Architecture Overview

### Core Design: Dual-Layer Architecture

```
User Interaction (TUI Layer)
    ↓
ConsoleApp (Textual TUI)
    ↓
Agents (LangGraph State Graphs)
    ├── CodingAgent → bash, text_editor, grep, ls, tree, todo_write, MCP tools
    └── ResearchAgent → perplexity_search, tavily_search, write_todos (via TodoListMiddleware), MCP tools
```

**Two Agent Types**:
1. **CodingAgent** (`agents/coding_agent.py`) - Primary agent for code analysis, editing, and execution
2. **ResearchAgent** (`agents/research_agent.py`) - Specialized agent for web research using Tavily with built-in todo list tracking via TodoListMiddleware

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

**Agent System** (`agents/`):

*CodingAgent* (`coding_agent.py`):
- Uses `create_agent()` from LangChain to build a ReAct agent
- State schema: `CodingAgentState` extends `MessagesState` with `todos` field
- System prompt from `prompts/templates/coding_agent.md` (Jinja2 template)
- Recursion limit: 100 (configurable in `app.py:152`)
- Tools: bash, text_editor, grep, ls, tree, todo_write, + MCP tools

*ResearchAgent* (`research_agent.py`):
- Specialized for web research and information gathering
- State schema: Managed by `TodoListMiddleware` (PlanningState with todos field)
- System prompt from `prompts/templates/research_agent.md`
- Middleware: `TodoListMiddleware` for task planning and tracking
- Tools: perplexity_search, tavily_search, write_todos (from middleware), + MCP tools

**Tool System** (`tools/`):

All tools use `@tool` decorator with `parse_docstring=True`. Tools receive `ToolRuntime` for context.

*Core Tools (6)*:
1. **bash** (`terminal/tool.py`) - Execute bash commands
   - `BashTerminal` maintains session state using `pexpect.spawn("/bin/bash")`
   - Single global instance (`keep_alive_terminal`) preserves cwd and env vars
   - Custom prompt for output parsing: `DEERCODE_PROMPT_1234567890`
2. **text_editor** (`edit/tool.py`) - File editing operations
   - Commands: `view`, `create`, `str_replace`, `insert`
   - Requires absolute paths for all file operations
3. **grep** (`fs/grep.py`) - Search file contents using ripgrep
   - Supports regex patterns, file filtering, context lines (-A, -B, -C)
   - Respects DEFAULT_IGNORE_PATTERNS
4. **ls** (`fs/ls.py`) - List directory contents
   - Supports glob pattern matching and filtering
   - Respects DEFAULT_IGNORE_PATTERNS
5. **tree** (`fs/tree.py`) - Display directory tree
   - Max depth: 3 levels
   - Respects DEFAULT_IGNORE_PATTERNS
6. **todo_write** (`todo/tool.py`) - Manage todo list
   - Updates `CodingAgentState.todos` field
   - Used for task planning and tracking

*Research Tools (2)*:
7. **perplexity_search** (`search/perplexity_search.py`) - AI-powered search via Perplexity API
   - Requires `tools.perplexity.api_key` in config.yaml
   - Returns synthesized answer with citations
   - Parameters: `query`, `recency` (day/week/month/year), `domains` (filter by domain)
   - Best for: Quick factual lookups, latest information, official documentation queries
   - Used by ResearchAgent
8. **tavily_search** (`search/tavily_search.py`) - Web search via Tavily API
   - Requires `tools.tavily.api_key` in config.yaml
   - Returns raw search results with relevance scores + optional AI answer
   - Best for: Deep research, multi-source analysis, complex comparisons
   - Used by ResearchAgent

*Extensibility*:
- **MCP Tools** (`mcp/load_mcp_tools.py`) - Loaded asynchronously on startup
  - Configured in `tools.mcp_servers` section of config.yaml
  - Supports `streamable_http` transport
- **Reminders** (`reminders.py`) - Generates context-aware reminders for unfinished todos

*File Filtering*:
- **DEFAULT_IGNORE_PATTERNS** (`fs/ignore.py`) - 77 patterns covering:
  - Version control (.git, .svn, .hg)
  - Dependencies (node_modules, vendor, __pycache__)
  - Build outputs (dist, build, target)
  - IDE files (.vscode, .idea)
  - Temporary files and logs

**UI System** (`cli/`):
- Layout: Left panel (3fr) = Chat | Right panel (4fr) = Editor (70%) + Terminal/Todo tabs (30%)
- `@work(exclusive=True, thread=False)` decorator for async message handling
- Theme: `DEER_DARK_THEME` with VSCode-inspired colors

### Configuration System

**config.yaml** structure:
```yaml
models:
  chat_model:
    # type: Optional - omit for OpenAI-compatible, or use 'deepseek' | 'doubao'
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'  # Converted to base_url for OpenAI SDK
    api_key: $OPENAI_API_KEY  # $VAR_NAME expands environment variables
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: 'minimal'  # OpenAI: minimal | low | medium | high
      # For Doubao model:
      # thinking:
      #   type: auto

tools:
  tavily:
    api_key: $TAVILY_API_KEY  # Required for tavily_search tool
  perplexity:
    api_key: $PERPLEXITY_API_KEY  # Required for perplexity_search tool
    model: 'sonar'  # Options: 'sonar' (faster, cheaper) or 'sonar-pro' (more detailed)
  mcp_servers:
    server_name:
      transport: 'streamable_http'
      url: 'https://...'
```

**Configuration Features**:
- **Loaded once on startup** (`config/config.py`)
- **Environment variable expansion**: `$VAR_NAME` syntax expands to env vars
- **Access method**: `get_config_section(["models", "chat_model"])`
- **Model initialization** (`models/chat_model.py`):
  - OpenAI-compatible (default): No `type` field needed, `api_base` → `base_url`
  - DeepSeek: `type: deepseek` + `langchain-deepseek` package
  - Doubao: `type: doubao` + `extra_body.thinking` for reasoning control
- **Search tools configuration**:
  - **Tavily**: Required in `tools.tavily.api_key` for tavily_search tool
  - **Perplexity**: Required in `tools.perplexity.api_key` for perplexity_search tool
    - Optional `tools.perplexity.model`: 'sonar' (default, faster) or 'sonar-pro' (more detailed)
- **MCP servers**: Configured under `tools.mcp_servers` with transport and URL

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

## Testing

**Test Structure** (`tests/`):
- **pytest** configuration in `pytest.ini`
- **Fixtures** in `conftest.py` for common test setup
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
- **Coverage** via `pytest-cov`

**Running Tests**:
```bash
# All tests
uv run pytest

# With coverage report
uv run pytest --cov=deer_code --cov-report=html

# Unit tests only
uv run pytest -m unit

# Integration tests only
uv run pytest -m integration

# Specific test file
uv run pytest tests/tools/search/test_tavily_search.py
```

**Test Dependencies** (optional):
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities

Install test dependencies: `uv sync --extra test`

## Adding New Tools

**Step 1: Create Tool Implementation**

Create tool file in `tools/your_category/tool.py`:
```python
from langchain.tools import tool, ToolRuntime

@tool("your_tool", parse_docstring=True)
def your_tool(runtime: ToolRuntime, param: str):
    """Tool description for LLM (this becomes the tool's documentation).

    Args:
        runtime: Access to agent runtime (todos, state, etc.)
        param: Parameter description (clearly explain what it does)

    Returns:
        String result that will be shown to the LLM
    """
    # Tool implementation
    return "result"
```

**Step 2: Register Tool**

For CodingAgent - Edit `agents/coding_agent.py`:
```python
from deer_code.tools.your_category import your_tool

def create_coding_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    return create_agent(
        tools=[
            bash_tool,
            grep_tool,
            # ... other tools
            your_tool,  # Add here
            *plugin_tools,
        ],
        # ...
    )
```

For ResearchAgent - Edit `agents/research_agent.py` similarly.

**Step 3: Handle in UI (if needed)**

If your tool requires UI updates, edit `cli/app.py:_process_tool_call_message()`:
```python
elif tool_name == "your_tool":
    # Route to appropriate UI component
    # Example: self.terminal.add_output(...)
```

**Best Practices**:
- Use descriptive tool names (lowercase, underscores)
- Write clear docstrings (LLM sees these)
- Return string results (LLM-readable format)
- Use `ToolRuntime` to access agent state if needed
- Add type hints for all parameters
- Consider file filtering with DEFAULT_IGNORE_PATTERNS for file operations

## Using Agent Middleware

**LangChain Agent Middleware** provides a powerful way to extend agent capabilities without modifying core agent logic. Middleware can add tools, manage state, and modify agent behavior.

### TodoListMiddleware (Used in ResearchAgent)

The `TodoListMiddleware` from LangChain provides built-in task planning and tracking capabilities.

**Features**:
- Automatically adds `write_todos` tool to the agent
- Manages `PlanningState` (extends MessagesState with todos field)
- Enables agents to break down complex tasks into trackable steps
- Todos persist across agent turns for continuous task tracking

**Usage Example**:

```python
from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware

def create_my_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    return create_agent(
        model=init_chat_model(),
        tools=[
            # your tools here
            *plugin_tools,
        ],
        system_prompt="...",
        middleware=[TodoListMiddleware()],  # Add todo capabilities
        name="my_agent",
        **kwargs,
    )
```

**Customization**:
```python
TodoListMiddleware(
    system_prompt="Custom instructions for todo usage...",
    tool_description="Custom description for write_todos tool..."
)
```

**State Access**:
```python
# After invoking the agent
result = await agent.ainvoke({"messages": [HumanMessage("Task...")]})

# Access todos from state
if "todos" in result:
    for todo in result["todos"]:
        print(todo)  # Todo items tracked by the agent
```

**Other Available Middleware** (from LangChain):
- `SummarizationMiddleware` - Automatic conversation summarization
- `HumanInTheLoopMiddleware` - Human approval for tool calls
- `ModelCallLimitMiddleware` - Limit model calls
- `ToolCallLimitMiddleware` - Limit tool executions
- `ShellToolMiddleware` - Persistent shell sessions
- `FilesystemFileSearchMiddleware` - File search capabilities
- And more (see LangChain middleware documentation)

**Best Practices**:
- Use middleware for cross-cutting concerns (state management, limits, monitoring)
- Prefer middleware over `state_schema` parameter when possible (better organization)
- Multiple middleware can be combined: `middleware=[Middleware1(), Middleware2()]`
- Middleware-managed state is automatically integrated with agent state

## Modifying System Prompts

Edit `prompts/templates/coding_agent.md` (Jinja2 template). Variables are passed via `apply_prompt_template("coding_agent", PROJECT_ROOT=...)`. The template includes:
- TODO usage guidelines (when to use `todo_write` tool)
- Frontend technology defaults (React, Next.js, Tailwind, etc.)
- Agent behavior rules

Changes take effect on next agent creation (app restart or `_init_agent()`).

## Model Support

**Supported Providers** (via `models/chat_model.py`):
1. **OpenAI-compatible** (default) - No `type` field needed
   - Uses `ChatOpenAI` from `langchain-openai`
   - `api_base` automatically converted to `base_url`
   - Supports `extra_body.reasoning_effort`: minimal | low | medium | high
2. **DeepSeek** - Set `type: deepseek`
   - Uses `ChatDeepSeek` from `langchain-deepseek`
   - Optimized for DeepSeek API endpoints
3. **Doubao** - Set `type: doubao`
   - Uses `ChatVolcEngine` from `langchain-deepseek`
   - Supports `extra_body.thinking.type: auto` for reasoning control

**Adding New Providers**:
To add a new model provider, modify `models/chat_model.py`:
1. Add type detection in `init_chat_model()`
2. Import appropriate LangChain chat model class
3. Handle provider-specific parameters from `extra_body`
4. Map configuration fields to model constructor parameters

## Agent Usage Patterns

**When to use CodingAgent** (primary agent in TUI):
- Code analysis, editing, and refactoring
- File system operations (search, list, tree)
- Bash command execution
- Task planning with todos
- General development workflows

**When to use ResearchAgent** (available via `agents/research_agent.py`):
- Web search and information gathering
- Finding documentation or examples online
- Researching libraries, frameworks, or APIs
- General knowledge queries requiring current information

Note: The TUI currently uses CodingAgent by default. ResearchAgent can be integrated by modifying `cli/app.py` to switch agents or by using it in custom LangGraph workflows.

## Important Coding Conventions

**File Paths**:
- Always use absolute paths for file operations
- Never use relative paths in tool calls
- The `project.root_dir` provides the project root directory

**Environment Variables**:
- Use `$VAR_NAME` syntax in config.yaml for automatic expansion
- Variables are expanded once at config load time
- Supports API keys, URLs, and other configuration values

**Async Patterns**:
- All agent streaming uses `async for` with `astream()`
- UI updates use `@work(exclusive=True, thread=False)` decorator
- MCP tools are loaded asynchronously on startup

**State Management**:
- CodingAgent state includes `messages` + `todos` (via CodingAgentState)
- ResearchAgent state includes `messages` + `todos` (via TodoListMiddleware's PlanningState)
- All state managed by LangGraph with `thread_id`
- Bash terminal state persisted in `keep_alive_terminal` instance

**Error Handling**:
- Tools should return error messages as strings (LLM-readable)
- UI components handle tool errors gracefully
- File operations respect ignore patterns to avoid irrelevant files

**Performance Considerations**:
- Tree depth limited to 3 levels to avoid deep recursion
- Grep and ls respect DEFAULT_IGNORE_PATTERNS (77 patterns)
- Agent recursion limited to 100 steps
- MCP tools loaded once at startup (async)

## Common Development Tasks

**Adding a new model provider**:
1. Edit `models/chat_model.py`
2. Add type detection logic
3. Import LangChain model class
4. Map config to model parameters

**Adding a new agent**:
1. Create `agents/your_agent.py`
2. Define state schema (extend MessagesState if needed)
3. Create system prompt in `prompts/templates/your_agent.md`
4. Register tools in `create_your_agent()` function
5. Export in `agents/__init__.py`

**Modifying UI layout**:
1. Edit `cli/app.py` compose() method
2. Update panel sizes (currently 3fr:4fr for left:right)
3. Modify component routing in `_process_tool_call_message()`

**Updating system prompts**:
1. Edit Jinja2 templates in `prompts/templates/`
2. Add variables in `apply_prompt_template()` calls
3. Restart app to see changes

**Debugging agents**:
1. Use development mode: `make dev`
2. Access LangGraph Studio at http://localhost:2024
3. Check agent state and tool calls in browser UI
4. Enable debug mode: `create_coding_agent(debug=True)`
