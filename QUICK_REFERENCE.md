# DeerCode - Quick Reference Guide

## Critical Path (User Input → Result Display)

```
┌─────────────────────────────────────────────────────────────────────┐
│ CRITICAL PATH FLOWCHART                                             │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: APPLICATION START
  main.py:13-22
  └─ project.root_dir = Path(sys.argv[1])
  └─ ConsoleApp() created
  └─ app.run() starts Textual event loop

STEP 2: UI INITIALIZATION
  cli/app.py:104-143
  └─ on_mount() called
  └─ Theme registered, Welcome tab opened
  └─ asyncio.create_task(_init_agent()) → loads MCP tools
  └─ Agent recreated with loaded tools at line 143

STEP 3: USER INPUT (ENTER)
  cli/app.py:114-123
  └─ ChatInput.on_submit() fires
  └─ is_generating checked (prevent concurrent requests)
  └─ HumanMessage created
  └─ _handle_user_input() called

STEP 4: AGENT STREAMING LOOP
  cli/app.py:145-160
  └─ @work(exclusive=True, thread=False)
  └─ is_generating = True
  └─ agent.astream() begins
     ├─ Input: {"messages": [HumanMessage]}
     ├─ Config: recursion_limit=100, thread_id="thread_1"
     └─ stream_mode="updates" (node-level chunks)

STEP 5: AGENT PROCESSES
  agents/coding_agent.py (LangChain/LangGraph ReAct)
  └─ Model from config.yaml
  └─ Available tools
  └─ System prompt (Jinja2 template)
  └─ Maintains state with thread_id

STEP 6A: AGENT RESPONDS (NO TOOLS)
  └─ Returns AIMessage with content
  └─ _process_incoming_message(AIMessage)
  └─ chat_view.add_message()
  └─ MessageListView renders with "🦌 DeerCode" header

STEP 6B: AGENT CALLS TOOL
  └─ Returns AIMessage with tool_calls
  └─ _process_incoming_message(AIMessage)
  ├─ chat_view.add_message() → shows descriptions
  └─ _process_tool_call_message() [app.py:177-215]
     │
     ├─ BASH/GREP/LS/TREE?
     │  └─ Add to _terminal_tool_calls[]
     │  └─ TerminalView.write("$ command")
     │
     ├─ TEXT_EDITOR?
     │  └─ EditorTabs.open_file(path)
     │  └─ Map id → path in dict
     │
     └─ TODO_WRITE?
        └─ TodoListView.update_items(todos)

STEP 7: TOOL EXECUTION
  └─ bash_tool, grep_tool, text_editor_tool, etc.
  └─ Terminal tools use persistent pexpect session
  └─ Return ToolMessage with results

STEP 8: RESULT DISPLAY
  cli/app.py:217-230
  └─ _process_tool_message(ToolMessage)
  ├─ IF tool_id in _terminal_tool_calls:
  │  └─ TerminalView.write(output, muted=True)
  └─ ELIF tool_id in _mutable_text_editor_tool_calls:
     └─ EditorTabs.open_file(path)

STEP 9: LOOP CONTINUES
  └─ While astream() not complete:
     ├─ More tools? → step 6B
     ├─ Final response? → step 6A
     └─ Done? → exit loop

STEP 10: DONE
  └─ is_generating = False
  └─ focus_input()
  └─ Ready for next message
```

## Key File Locations

| Component | File | Key Lines |
|-----------|------|-----------|
| Entry Point | `main.py` | 13-22 |
| App Class | `cli/app.py` | 20-74 |
| Initialization | `cli/app.py` | 104-143 |
| Input Handling | `cli/app.py` | 114-123 |
| Agent Stream | `cli/app.py` | 145-160 |
| Message Routing | `cli/app.py` | 166-172 |
| Tool Routing | `cli/app.py` | 177-215 |
| Result Display | `cli/app.py` | 217-230 |
| Agent Creation | `agents/coding_agent.py` | 22-49 |
| Agent State | `agents/state.py` | 1-8 |
| Bash Tool | `tools/terminal/tool.py` | 13-40 |
| Session Mgmt | `tools/terminal/bash_terminal.py` | 7-86 |
| Grep Tool | `tools/fs/grep.py` | 11-135 |
| Editor Tool | `tools/edit/tool.py` | 11-62 |
| Todo Tool | `tools/todo/tool.py` | 10-42 |
| Chat View | `cli/components/chat/chat_view.py` | 47-56 |
| Terminal View | `cli/components/terminal/terminal_view.py` | 25-30 |
| Editor Tabs | `cli/components/editor/editor_tabs.py` | 18-56 |
| Messages | `cli/components/chat/message_item_view.py` | 57-142 |
| Config | `config/config.py` | 1-33 |
| MCP Loader | `tools/mcp/load_mcp_tools.py` | 6-12 |

## State Structures

### Agent State (Persisted)
```
CodingAgentState:
  messages: [] → All conversation messages
  todos: [] → Current todo list
  thread_id: "thread_1" → Single thread context
```

### UI State
```
ConsoleApp:
  _is_generating: bool → Prevents concurrent requests
  _terminal_tool_calls: [] → bash/grep/ls/tree IDs
  _mutable_text_editor_tool_calls: {} → id → file_path
```

### Session State
```
BashTerminal:
  Single global instance
  Persistent pexpect shell
  Custom prompt: "BASH_TERMINAL_PROMPT> "
  cwd & env preserved
```

## Design Patterns

### 1. Exclusive Async Work
```python
@work(exclusive=True, thread=False)
# Only one request at a time
# Runs in main event loop
```

### 2. Node-Level Streaming
```python
async for chunk in agent.astream(..., stream_mode="updates"):
    # Each chunk = complete node output
    # Not token-level streaming
```

### 3. Tool Call Tracking
```
Terminal tools: _terminal_tool_calls = [id1, id2, ...]
Editor tools: _mutable_text_editor_tool_calls = {id1: path1, id2: path2}
```

### 4. Message-Driven
```
HumanMessage
    ↓
AIMessage (with/without tool_calls)
    ↓
ToolMessage (if tools called)
    ↓
Display in UI
```

## Common Patterns

### Adding a Tool
1. Create `tools/your_tool/tool.py`
2. Decorate with `@tool("name", parse_docstring=True)`
3. Import in `agents/coding_agent.py`
4. Add to tools list (line 34-41)
5. If terminal output: add handler (app.py line 185+)
6. If special UI: add in `_process_tool_call_message()` or `_process_tool_message()`

### Handling Tool Results
```python
# In _process_tool_message():
if message.tool_call_id in self._terminal_tool_calls:
    # Terminal tool result
    output = self._extract_code(message.content)
    terminal_view.write(output, muted=True)
    self._terminal_tool_calls.remove(message.tool_call_id)
```

### Persistent Bash Operations
```python
# First call: creates BashTerminal
bash_tool("command1")

# Second call: uses same instance
bash_tool("command2")  # cwd is preserved!

# Reset if needed
bash_tool("command3", reset_cwd=True)  # Creates new instance
```

## Async/Threading Model

- **on_input_submitted()**: Synchronous event handler
- **_handle_user_input()**: Async work task
  - `@work(exclusive=True)` ensures single execution
  - `thread=False` runs in main event loop
  - Other TUI events can fire during streaming
- **_init_agent()**: Async task for MCP loading
  - `asyncio.create_task()` non-blocking startup

## Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Input disabled | is_generating=True | Wait for stream complete |
| Tool results not showing | tool_call_id not tracked | Check routing logic |
| Bash commands failing | project.root_dir wrong | Verify path passed to app |
| Editor not updating | File path missing | Check _mutable_text_editor_tool_calls |
| Agent stuck | Infinite tool loop | Increase recursion_limit |
| MCP tools not loading | config.yaml issue | Check tools.mcp_servers section |

## Testing Workflow Manually

```bash
# 1. Setup
cd /home/user/deer-code
cp config.example.yaml config.yaml
# Edit config.yaml with API keys

# 2. Run
uv run -m deer_code.main "/path/to/project"

# 3. Test message
# Type: "List the first 5 files in this directory"

# 4. Observe
# - Message appears in chat
# - Tool call description shown
# - Terminal output displays results
# - Ready for next input

# 5. Verify state
# - All messages persisted (scroll up)
# - Editor tabs remain open
# - Terminal output accumulates
```

## Architecture Summary

```
┌────────────────────────────────────┐
│ Textual TUI (main event loop)      │
├────────────────────────────────────┤
│ ChatInput → ChatView                │
│ EditorTabs → CodeView               │
│ TerminalView (output)               │
│ TodoListView                        │
└────────────────────────────────────┘
           ↓
┌────────────────────────────────────┐
│ ConsoleApp (app.py)                │
│ - _handle_user_input()             │
│ - _process_tool_call_message()     │
│ - _process_tool_message()          │
└────────────────────────────────────┘
           ↓
┌────────────────────────────────────┐
│ CodingAgent (LangGraph)            │
│ - create_agent() with tools        │
│ - ReAct loop                       │
│ - State: thread_1                  │
└────────────────────────────────────┘
           ↓
┌────────────────────────────────────┐
│ Tools                              │
│ - bash_tool (persistent session)   │
│ - grep_tool (ripgrep)              │
│ - text_editor_tool                 │
│ - todo_write_tool                  │
│ - MCP tools (loaded dynamically)   │
└────────────────────────────────────┘
```

---

See `/home/user/deer-code/WORKFLOW_ANALYSIS.md` for comprehensive documentation.

