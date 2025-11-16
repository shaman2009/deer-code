# DeerCode Core Workflow Documentation Index

This index provides navigation to comprehensive documentation of the DeerCode core workflow.

## Documents Created

### 1. WORKFLOW_ANALYSIS.md
**Comprehensive technical analysis** of the complete DeerCode workflow
- Entry point and application startup
- ConsoleApp initialization and layout
- User input handling
- Agent creation and LLM integration
- Message processing loop
- Tool routing and execution
- Result display and UI updates
- Complete message flow diagrams

**Read this for:** Deep understanding of how every component connects

### 2. QUICK_REFERENCE.md
**Condensed guide** with critical path flowchart and quick lookups
- Step-by-step critical path (user input → result display)
- File locations and key line numbers
- State structures and data persistence
- Design patterns and common patterns
- Async/threading model
- Common issues and solutions
- Architecture summary diagram

**Read this for:** Quick lookup, troubleshooting, pattern reference

## Critical Components Overview

### Entry Point
**File:** `/home/user/deer-code/src/deer_code/main.py:13-22`
- Sets project root from CLI argument
- Creates ConsoleApp instance
- Starts Textual event loop

### ConsoleApp (Main Application)
**File:** `/home/user/deer-code/src/deer_code/cli/app.py:20-230`
- **Initialization:** Lines 72-143
  - UI composition (Lines 87-98)
  - Mount setup (Lines 104-112)
  - Async MCP tool loading (Lines 125-143)
- **Input Handling:** Lines 114-123
  - Receives user input from ChatInput
  - Creates HumanMessage
  - Routes to _handle_user_input()
- **Agent Streaming:** Lines 145-160
  - Async work with exclusive lock
  - Streams from agent.astream()
  - Node-level updates (not token-level)
- **Message Processing:** Lines 162-230
  - Routes messages to UI components
  - Handles tool calls and results
  - Updates chat, editor, terminal, todo views

### CodingAgent (LLM Agent)
**File:** `/home/user/deer-code/src/deer_code/agents/coding_agent.py:22-49`
- Created with LangChain's create_agent()
- Tools: bash, grep, ls, text_editor, todo_write, tree, + MCP tools
- State: CodingAgentState (messages + todos)
- System prompt: Jinja2 template from prompts/
- Runs ReAct loop for decision making

### Tool System
**Files:** `/home/user/deer-code/src/deer_code/tools/`
- **bash_tool** (terminal/tool.py:13-40)
  - Uses persistent BashTerminal via pexpect
  - Preserves cwd and env across calls
- **grep_tool** (fs/grep.py:11-135)
  - Uses ripgrep subprocess
  - Supports multiline patterns and filtering
- **text_editor_tool** (edit/tool.py:11-62)
  - Commands: view, create, str_replace, insert
  - Auto-creates parent directories
- **todo_write_tool** (todo/tool.py:10-42)
  - Updates agent state with todos
  - Returns Command for state mutation
- **MCP Tools** (mcp/load_mcp_tools.py:6-12)
  - Loaded asynchronously on startup
  - Added to agent in _init_agent()

### UI Components
**Files:** `/home/user/deer-code/src/deer_code/cli/components/`
- **ChatView** (chat/chat_view.py)
  - Displays messages from agent and user
  - Shows tool call descriptions
- **TerminalView** (terminal/terminal_view.py)
  - Shows bash commands and output
  - Muted styling for tool results
- **EditorTabs** (editor/editor_tabs.py)
  - Opens and displays files
  - Refreshed when editor tools complete
- **TodoListView** (todo/todo_list_view.py)
  - Shows current todos
  - Updated by todo_write tool

## Key Data Flows

### User Input → Agent → Tools → Display

```
User types message
    ↓
ChatInput.on_submit() [Textual event]
    ↓
ConsoleApp.on_input_submitted() [app.py:114-123]
    ├─ Create HumanMessage
    └─ Call _handle_user_input()
    ↓
@work decorator schedules async task
    ↓
agent.astream() begins streaming
    ├─ Input: {"messages": [HumanMessage]}
    ├─ recursion_limit: 100
    └─ thread_id: "thread_1"
    ↓
Agent processes with ReAct loop
    ├─ Option 1: Respond with AIMessage
    │  └─ Display in ChatView
    │
    └─ Option 2: Call tool with AIMessage
       ├─ Route to handler (terminal/editor/todo)
       ├─ Tool executes and returns ToolMessage
       └─ Display results in UI
    ↓
Agent loop continues or completes
    ↓
is_generating = False
    ↓
User can type next message
```

### Tool Call Tracking System

```
AIMessage with tool_calls arrives
    ↓
_process_tool_call_message() routes to handler
    │
    ├─ Terminal tool (bash/grep/ls/tree)?
    │  └─ Add tool_call_id to _terminal_tool_calls[]
    │
    ├─ Editor tool (text_editor)?
    │  └─ Add mapping: id → path
    │
    └─ Todo tool (todo_write)?
       └─ Direct update to TodoListView
    ↓
Agent executes tool and returns ToolMessage
    ↓
_process_tool_message() uses tracking ID
    │
    ├─ Is ID in _terminal_tool_calls?
    │  └─ Display in TerminalView
    │
    └─ Is ID in _mutable_text_editor_tool_calls?
       └─ Open/refresh in EditorTabs
    ↓
Remove ID from tracking
```

## State Persistence

### LangGraph Agent State
- **File:** `/home/user/deer-code/src/deer_code/agents/state.py`
- Persists across entire conversation
- Thread ID: "thread_1" (single thread context)
- Fields:
  - `messages`: All conversation messages
  - `todos`: Current todo list

### Bash Session State
- **File:** `/home/user/deer-code/src/deer_code/tools/terminal/bash_terminal.py`
- Single global instance (`keep_alive_terminal`)
- Uses pexpect to spawn persistent bash process
- Preserves:
  - Current working directory
  - Environment variables
  - Shell history

### UI State
- ConsoleApp instance variables:
  - `_is_generating`: Prevents concurrent requests
  - `_terminal_tool_calls`: IDs awaiting results
  - `_mutable_text_editor_tool_calls`: ID → file path mapping

## Configuration System

**File:** `/home/user/deer-code/src/deer_code/config/config.py`

```yaml
models:
  chat_model:
    type: openai | deepseek | doubao  # optional
    model: 'gpt-4'
    api_key: $OPENAI_API_KEY  # env var expansion
    api_base: 'https://api.openai.com/v1'
    temperature: 0
    max_tokens: 8192
    extra_body: {}  # Provider-specific params

tools:
  mcp_servers:
    name:
      transport: 'streamable_http'
      url: 'https://...'
```

Configuration loaded on module import and accessed via:
```python
get_config_section(["models", "chat_model"])
get_config_section(["tools", "mcp_servers"])
```

## Async/Threading Model

- **Input Handler:** Synchronous (on_input_submitted)
- **Agent Processing:** Async work task
  - `@work(exclusive=True, thread=False)`
  - Serializes requests
  - Runs in main event loop (not threaded)
  - Other TUI events can fire during streaming
- **MCP Loading:** Async task
  - `asyncio.create_task(_init_agent())`
  - Non-blocking initialization
  - Final agent created after MCP tools loaded

## Critical Implementation Details

### 1. Stream Mode
```python
agent.astream(..., stream_mode="updates")
# Returns node-level updates, NOT token-level
# Each chunk contains complete messages from one node
```

### 2. Tool Call Tracking
```python
# Terminal tools (simple list)
_terminal_tool_calls: list[str] = []

# Editor tools (needs file path for refresh)
_mutable_text_editor_tool_calls: dict[str, str] = {}
```

### 3. Persistent Bash Session
```python
# Single global instance
global keep_alive_terminal

# Uses pexpect with custom prompt
self.shell = pexpect.spawn("/bin/bash")
self.prompt = "BASH_TERMINAL_PROMPT> "
```

### 4. Message Flow
```
HumanMessage → AIMessage → ToolMessage → Back to processing
All stored in LangGraph state
Displayed incrementally in UI
```

## Quick Navigation

### To Understand...
- **Application startup:** main.py:13-22 and cli/app.py:72-112
- **User input handling:** cli/app.py:114-123
- **Agent creation:** agents/coding_agent.py:22-49
- **Message streaming:** cli/app.py:145-160
- **Tool routing:** cli/app.py:177-215
- **Result display:** cli/app.py:217-230
- **Bash session:** tools/terminal/bash_terminal.py:7-86
- **Configuration:** config/config.py

### To Modify...
- **Add a new tool:** Create in tools/, import in coding_agent.py, handle in app.py
- **Change system prompt:** Edit prompts/templates/coding_agent.md
- **Add UI component:** Create in cli/components/
- **Change LLM provider:** Modify models/chat_model.py

### To Debug...
- **Agent not responding:** Check recursion_limit and system prompt
- **Tool results missing:** Verify tool_call_id tracking
- **Editor not updating:** Check _mutable_text_editor_tool_calls
- **Bash commands failing:** Verify project.root_dir and prompt detection
- **Input stuck disabled:** Check if agent is in infinite loop

## Architecture Principles

1. **Async-First:** Streaming, non-blocking UI updates
2. **Message-Driven:** All communication via LangChain messages
3. **State Persistence:** Single thread maintains context
4. **Modular Tools:** Each tool is self-contained and testable
5. **Exclusive Work:** Only one agent request at a time
6. **Incremental Display:** Messages appear as they arrive
7. **Session Persistence:** Bash maintains state across calls

---

## Next Steps

1. **Read QUICK_REFERENCE.md** for the critical path
2. **Read WORKFLOW_ANALYSIS.md** for detailed implementation
3. **Explore the codebase** following the file locations listed above
4. **Run the application** and trace through the workflow manually
5. **Add a custom tool** to test your understanding

---

**Last Updated:** 2025-11-16
**Documentation Version:** 1.0
**DeerCode Project:** Minimalist AI coding agent with VSCode-like TUI

