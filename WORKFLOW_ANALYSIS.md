# DeerCode Core Workflow Analysis

This document provides a detailed explanation of the complete DeerCode workflow, tracing the critical path from user input through agent processing to tool execution and results display.

## Quick Links
- Main Entry Point: `/home/user/deer-code/src/deer_code/main.py:13-22`
- ConsoleApp: `/home/user/deer-code/src/deer_code/cli/app.py:20-230`
- Agent Creation: `/home/user/deer-code/src/deer_code/agents/coding_agent.py:22-49`
- Message Processing Loop: `/home/user/deer-code/src/deer_code/cli/app.py:145-160`
- Tool Call Routing: `/home/user/deer-code/src/deer_code/cli/app.py:177-215`
- Result Display: `/home/user/deer-code/src/deer_code/cli/app.py:217-230`

## Complete Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CRITICAL PATH: User Input → UI → Agent → Tools → UI  │
└─────────────────────────────────────────────────────────────────────────────┘

User Input (Terminal)
    ↓
ChatInput Widget (chat_input.py:4-27)
    ↓
ConsoleApp.on_input_submitted() (app.py:114-123)
    ↓
ConsoleApp._handle_user_input() (app.py:146-160) [Async Task]
    ↓
┌─────────────────────────────────────────────────┐
│ Agent Stream Processing (LangGraph)             │
│ ↓ Message through ReAct loop                    │
│ ↓ Tool invocation with tool_calls               │
│ ↓ Tool execution returns results                │
│ ↓ Loop repeats until agent.stop                 │
└─────────────────────────────────────────────────┘
    ↓
UI Updates via Message Processing
    ├─ AIMessage → ChatView (app.py:168)
    ├─ Tool Calls → Terminal/Editor/Todo (app.py:177-215)
    └─ ToolMessage → Display Results (app.py:217-230)
```

## The 5 Critical Components Explained

### 1. MAIN ENTRY POINT: Application Startup

**File: `/home/user/deer-code/src/deer_code/main.py`**

**Lines 13-22:**
```python
def main():
    """Main entry point for deer-code."""
    if len(sys.argv) > 1:
        project.root_dir = Path(sys.argv[1])  # Set project root from CLI arg
    app = ConsoleApp()
    app.run()
```

**Flow:**
1. `load_dotenv()` loads environment variables
2. Set project root from command-line argument (or use current directory)
3. Create `ConsoleApp` instance (Textual TUI application)
4. Call `app.run()` to start the event loop

**Global Context:**
- `/home/user/deer-code/src/deer_code/project.py:27` - `project` singleton stores root directory
- `/home/user/deer-code/src/deer_code/config/config.py:33` - Config loaded on module import

---

### 2. CONSOLE APP: Initialization and User Input Handling

**File: `/home/user/deer-code/src/deer_code/cli/app.py`**

#### 2.1 Class Initialization (Lines 20-74)
```python
class ConsoleApp(App):
    _coding_agent: CompiledStateGraph
    _is_generating = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._coding_agent = create_coding_agent()  # Line 74 - Initial agent
```

- **Line 68**: `_coding_agent` stores the compiled LangGraph state machine
- **Line 74**: Creates agent synchronously (before MCP tools loaded)
- **Line 70**: `_is_generating` prevents concurrent requests

#### 2.2 UI Layout (Lines 87-98)
```python
def compose(self) -> ComposeResult:
    yield Header(id="header")
    with Vertical(id="left-panel"):  # 3fr width
        yield ChatView(id="chat-view")
    with Vertical(id="right-panel"):  # 4fr width
        yield EditorTabs(id="editor-tabs")  # 70% height
        with TabbedContent(id="bottom-right-tabs"):  # 30% height
            with TabPane(id="terminal-tab", title="Terminal"):
                yield TerminalView(id="terminal-view")
            with TabPane(id="todo-tab", title="To-do"):
                yield TodoListView(id="todo-list-view")
    yield Footer(id="footer")
```

#### 2.3 Mount & Async Initialization (Lines 104-143)
```python
def on_mount(self) -> None:
    self.register_theme(DEER_DARK_THEME)  # Line 105
    self.theme = "deer-dark"
    self.sub_title = project.root_dir  # Display project root
    self.focus_input()  # Focus chat input
    editor_tabs = self.query_one("#editor-tabs", EditorTabs)
    editor_tabs.open_welcome()  # Open welcome docs
    
    asyncio.create_task(self._init_agent())  # Line 112 - Non-blocking

async def _init_agent(self) -> None:
    terminal_view = self.query_one("#terminal-view", TerminalView)
    terminal_view.write("$ Loading MCP tools...")
    try:
        mcp_tools = await load_mcp_tools()  # Line 129 - Load from config
        # Recreate agent with MCP tools
        self._coding_agent = create_coding_agent(plugin_tools=mcp_tools)  # Line 143
    except Exception as e:
        print(f"Error loading MCP tools: {e}")
        self.exit(1)
```

**Key Detail:**
- **Line 112**: Async task for MCP loading (non-blocking UI)
- **Line 143**: Agent recreated with loaded tools - **THIS IS THE FINAL AGENT**

#### 2.4 User Input Handling (Lines 114-123)
```python
def on_input_submitted(self, event: Input.Submitted) -> None:
    if not self.is_generating and event.input.id == "chat-input":  # Line 115 - Gate
        user_input = event.value.strip()
        if user_input:
            if user_input == "exit" or user_input == "quit":
                self.exit()
                return
            event.input.value = ""  # Clear input
            user_message = HumanMessage(content=user_input)  # LangChain message
            self._handle_user_input(user_message)  # Line 123
```

**Flow:**
1. Check `is_generating` flag (prevent concurrent requests)
2. Create `HumanMessage` (LangChain message object)
3. Call `_handle_user_input()` to process async

---

### 3. CODING AGENT: Creation and Message Processing

**File: `/home/user/deer-code/src/deer_code/agents/coding_agent.py` Lines 22-49**

```python
def create_coding_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """Create a coding agent with tools and system prompt."""
    return create_agent(
        model=init_chat_model(),  # Load LLM from config
        tools=[  # Built-in tools
            bash_tool,
            grep_tool,
            ls_tool,
            text_editor_tool,
            todo_write_tool,
            tree_tool,
            *plugin_tools,  # MCP tools appended
        ],
        system_prompt=apply_prompt_template(
            "coding_agent", PROJECT_ROOT=project.root_dir
        ),
        state_schema=CodingAgentState,  # Custom state with todos
        name="coding_agent",
    )
```

**Components:**

1. **LLM Model** (`init_chat_model()`)
   - File: `/home/user/deer-code/src/deer_code/models/chat_model.py`
   - Loads from `config.yaml`: model, api_key, api_base, temperature, etc.
   - Supports: OpenAI (default), DeepSeek, Doubao
   - Environment variable expansion (line 21-22)

2. **Tools** (in order)
   - `bash_tool` - Execute commands in persistent session
   - `grep_tool` - Search files with ripgrep
   - `ls_tool` - List directory contents
   - `text_editor_tool` - Create/edit files
   - `todo_write_tool` - Manage TODO list
   - `tree_tool` - Explore directory structure
   - `*plugin_tools` - MCP tools loaded dynamically

3. **System Prompt**
   - File: `/home/user/deer-code/src/deer_code/prompts/templates/coding_agent.md`
   - Jinja2 template with agent instructions
   - Variables: `PROJECT_ROOT` passed from agent creation

4. **State Schema**
   - File: `/home/user/deer-code/src/deer_code/agents/state.py`
   - Extends `MessagesState` with `todos: list[TodoItem]`
   - Persists messages and todos across conversation

---

### 4. MESSAGE FLOW: The Critical Processing Loop

**File: `/home/user/deer-code/src/deer_code/cli/app.py` Lines 145-230**

#### 4.1 Agent Streaming (Lines 145-160)

```python
@work(exclusive=True, thread=False)  # Textual async work decorator
async def _handle_user_input(self, user_message: HumanMessage) -> None:
    self._process_outgoing_message(user_message)  # Display user message
    self.is_generating = True  # Disable input
    
    # Stream updates from agent
    async for chunk in self._coding_agent.astream(
        {"messages": [user_message]},  # Add message to state
        stream_mode="updates",  # Node-level updates
        config={"recursion_limit": 100, "thread_id": "thread_1"},
    ):
        roles = chunk.keys()  # Get node names
        for role in roles:
            messages: list[AnyMessage] = chunk[role].get("messages", [])
            for message in messages:
                self._process_incoming_message(message)
    
    self.is_generating = False  # Enable input
    self.focus_input()
```

**Streaming Details:**
- **`stream_mode="updates"`**: Node-level chunks (not token-level)
- Each chunk: `{"coding_agent": {"messages": [AIMessage, ToolMessage, ...]}}`
- **`recursion_limit: 100`**: Prevents infinite loops
- **`thread_id: "thread_1"`**: All messages in one thread (conversation context)
- **`@work(exclusive=True)`**: Serializes requests

#### 4.2 Message Processing (Lines 166-172)

```python
def _process_incoming_message(self, message: AnyMessage) -> None:
    chat_view = self.query_one("#chat-view", ChatView)
    chat_view.add_message(message)  # Display message
    
    if isinstance(message, AIMessage) and message.tool_calls:  # Line 169
        self._process_tool_call_message(message)  # Route tool calls
    
    if isinstance(message, ToolMessage):  # Line 171
        self._process_tool_message(message)  # Display results
```

**Message Types:**
1. **HumanMessage**: Displayed in chat with "👤 You" header
2. **AIMessage** (no tool_calls): Agent reasoning text with "🦌 DeerCode" header
3. **AIMessage** (with tool_calls): Show descriptions + route to handlers
4. **ToolMessage**: Not displayed in chat, only used internally for result display

---

### 5. TOOL EXECUTION: The Complete System

#### 5.1 Tool Call Routing (Lines 174-215)

```python
_terminal_tool_calls: list[str] = []  # Track bash/grep/ls/tree
_mutable_text_editor_tool_calls: dict[str, str] = {}  # tool_id → path

def _process_tool_call_message(self, message: AIMessage) -> None:
    """Route tool calls to appropriate UI components."""
    terminal_view = self.query_one("#terminal-view", TerminalView)
    todo_list_view = self.query_one("#todo-list-view", TodoListView)
    editor_tabs = self.query_one("#editor-tabs", EditorTabs)
    bottom_right_tabs = self.query_one("#bottom-right-tabs", TabbedContent)
    
    for tool_call in message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # BASH TOOL (Lines 185-188)
        if tool_name == "bash":
            self._terminal_tool_calls.append(tool_call["id"])  # Track
            terminal_view.write(f"$ {tool_args["command"]}")
            bottom_right_tabs.active = "terminal-tab"  # Switch tab
        
        # GREP TOOL (Lines 194-196)
        elif tool_name == "grep":
            self._terminal_tool_calls.append(tool_call["id"])
            terminal_view.write(f"$ grep {" ".join(tool_args.values())}")
        
        # LS TOOL (Lines 197-199)
        elif tool_name == "ls":
            self._terminal_tool_calls.append(tool_call["id"])
            terminal_view.write(f"$ ls {" ".join(tool_args.values())}")
        
        # TEXT EDITOR TOOL (Lines 203-215)
        elif tool_name == "text_editor":
            command = tool_args["command"]
            if command == "create":
                editor_tabs.open_file(tool_args["path"], tool_args["file_text"])
            else:
                editor_tabs.open_file(tool_args["path"])
            
            if command != "view":  # Track mutable operations
                self._mutable_text_editor_tool_calls[tool_call["id"]] = tool_args["path"]
        
        # TODO WRITE TOOL (Lines 200-202)
        elif tool_name == "todo_write":
            bottom_right_tabs.active = "todo-tab"  # Switch tab
            todo_list_view.update_items(tool_args["todos"])  # Display todos
```

**Routing Logic:**
- **Terminal tools**: Add `tool_call_id` to `_terminal_tool_calls` list
- **Editor tools**: Map `tool_call_id` → `path` in dict (need path for refresh)
- **Todo tools**: Direct update to TodoListView

#### 5.2 Bash Tool & Session Persistence

**File: `/home/user/deer-code/src/deer_code/tools/terminal/tool.py` Lines 13-40**

```python
keep_alive_terminal: BashTerminal | None = None  # Global instance

@tool("bash", parse_docstring=True)
def bash_tool(runtime: ToolRuntime, command: str, reset_cwd: Optional[bool] = False):
    """Execute bash command in keep-alive shell."""
    global keep_alive_terminal
    
    if keep_alive_terminal is None:
        keep_alive_terminal = BashTerminal(project.root_dir)  # Create on first call
    elif reset_cwd:
        keep_alive_terminal.close()
        keep_alive_terminal = BashTerminal(project.root_dir)
    
    reminders = generate_reminders(runtime)
    return f"```\n{keep_alive_terminal.execute(command)}\n```{reminders}"
```

**Session Management (BashTerminal Class):**

File: `/home/user/deer-code/src/deer_code/tools/terminal/bash_terminal.py` Lines 7-86

```python
class BashTerminal:
    def __init__(self, cwd=None):
        self.cwd = cwd or os.getcwd()
        
        # Persistent bash process
        self.shell = pexpect.spawn("/bin/bash", encoding="utf-8", echo=False)
        
        # Custom prompt for completion detection
        self.prompt = "BASH_TERMINAL_PROMPT> "
        self.shell.sendline(f'PS1="{self.prompt}"')
        self.shell.expect(self.prompt, timeout=5)
        
        # Change to project directory
        if cwd:
            self.execute(f'cd "{self.cwd}"')
    
    def execute(self, command):
        """Execute command and return output."""
        self.shell.sendline(command)
        self.shell.expect(self.prompt, timeout=30)  # Wait for prompt
        
        # Parse and clean output
        output = self.shell.before
        lines = output.split("\n")
        if lines and lines[0].strip() == command.strip():
            lines = lines[1:]  # Remove echoed command
        
        result = "\n".join([line.strip() for line in lines]).strip()
        result = re.sub(r"\x1b\[[0-9;]*m", "", result)  # Remove ANSI codes
        return result
```

**Critical Details:**
- Single global instance maintains shell state
- `pexpect.spawn()` creates persistent process
- Custom prompt detects command completion
- **Working directory preserved** across commands
- **Environment variables preserved** across commands
- ANSI color codes stripped from output

#### 5.3 Other Tools

**Grep Tool** (`/home/user/deer-code/src/deer_code/tools/fs/grep.py`):
- Uses `ripgrep` (rg) subprocess
- Supports: multiline patterns, file filtering, output modes
- Returns results in code blocks

**Text Editor Tool** (`/home/user/deer-code/src/deer_code/tools/edit/tool.py`):
- Commands: `view`, `create`, `str_replace`, `insert`
- Auto-creates parent directories
- Returns operation status

**Todo Write Tool** (`/home/user/deer-code/src/deer_code/tools/todo/tool.py`):
- Updates `todos` field in CodingAgentState
- Returns `Command` object for state update
- Tracks completed/cancelled todos

#### 5.4 Result Display (Lines 217-230)

```python
def _process_tool_message(self, message: ToolMessage) -> None:
    """Display tool execution results."""
    terminal_view = self.query_one("#terminal-view", TerminalView)
    
    # TERMINAL TOOL RESULTS
    if message.tool_call_id in self._terminal_tool_calls:
        output = self._extract_code(message.content)  # Extract code blocks
        terminal_view.write(
            output if output.strip() != "" else "\n(empty)\n",
            muted=True,  # Muted styling
        )
        self._terminal_tool_calls.remove(message.tool_call_id)  # Untrack
    
    # EDITOR TOOL RESULTS
    elif self._mutable_text_editor_tool_calls.get(message.tool_call_id):
        path = self._mutable_text_editor_tool_calls[message.tool_call_id]
        del self._mutable_text_editor_tool_calls[message.tool_call_id]
        editor_tabs = self.query_one("#editor-tabs", EditorTabs)
        editor_tabs.open_file(path)  # Refresh file display

def _extract_code(self, text: str) -> str:
    """Extract code from markdown code blocks."""
    match = re.search(r"```(.*)```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text
```

**Result Processing:**
1. Check `tool_call_id` against tracking dicts
2. Extract code blocks from ToolMessage
3. Display in appropriate component:
   - **Terminal tools** → TerminalView with muted styling
   - **Editor tools** → EditorTabs (reload file from disk)

---

## Complete Message Flow Diagram

```
1. USER INPUT
   ↓
   ChatInput.on_submit()
   ↓
   ConsoleApp.on_input_submitted() [app.py:114-123]

2. USER MESSAGE DISPLAY
   ↓
   _process_outgoing_message(HumanMessage)
   ├─ ChatView.add_message()
   ├─ MessageListView.add_message()
   └─ Render with "👤 You" header

3. AGENT PROCESSING (ASYNC)
   ↓
   _handle_user_input() [app.py:145-160] @work decorator
   ├─ is_generating = True
   ├─ agent.astream() begins
   │  ├─ Input: {"messages": [HumanMessage]}
   │  ├─ Config: recursion_limit=100, thread_id="thread_1"
   │  └─ stream_mode="updates"
   │
   └─ For each chunk from agent:
      └─ For each message in chunk:
         └─ _process_incoming_message()

4a. AGENT RESPONSE (NO TOOLS)
   ↓
   _process_incoming_message(AIMessage)
   ├─ ChatView.add_message(AIMessage)
   ├─ MessageListView.add_message()
   └─ Render with "🦌 DeerCode" header + markdown

4b. TOOL INVOCATION
   ↓
   _process_incoming_message(AIMessage with tool_calls)
   ├─ ChatView.add_message() → shows tool descriptions
   ├─ _process_tool_call_message() [app.py:177-215]
   │
   ├─ FOR BASH/GREP/LS/TREE:
   │  ├─ Add tool_call["id"] to _terminal_tool_calls
   │  ├─ TerminalView.write("$ command")
   │  └─ Switch to terminal-tab
   │
   ├─ FOR TEXT_EDITOR:
   │  ├─ EditorTabs.open_file(path, [file_text])
   │  └─ Map tool_call_id → path in dict
   │
   └─ FOR TODO_WRITE:
      ├─ TodoListView.update_items(todos)
      └─ Switch to todo-tab

5. TOOL EXECUTION (BY AGENT)
   ↓
   Agent executes tool in ReAct loop
   └─ Tool runs (bash, grep, etc.)
      └─ Returns ToolMessage with results

6. RESULT DISPLAY
   ↓
   _process_incoming_message(ToolMessage) [app.py:166-172]
   └─ _process_tool_message(ToolMessage) [app.py:217-230]
      │
      ├─ IF tool_call_id in _terminal_tool_calls:
      │  ├─ Extract code block
      │  ├─ TerminalView.write(output, muted=True)
      │  └─ Remove from tracking
      │
      └─ ELIF tool_call_id in _mutable_text_editor_tool_calls:
         ├─ EditorTabs.open_file(path)
         └─ Remove from tracking

7. AGENT LOOP CONTINUES
   ↓
   While astream() not complete:
   ├─ If more tools → step 4b
   ├─ If responding → step 4a
   └─ If done → astream() completes

8. INPUT READY
   ↓
   is_generating = False
   focus_input()
   → Back to step 1
```

---

## Key Data Structures

### Agent State
```python
class CodingAgentState(MessagesState):
    todos: list[TodoItem] = Field(default_factory=list)
```

### Tool Call Tracking
```python
_terminal_tool_calls: list[str] = []
_mutable_text_editor_tool_calls: dict[str, str] = {}
```

### Configuration
```python
# Global singleton, loaded on module import
__config: dict  # From config.yaml
```

---

## State Persistence

### Agent State (LangGraph)
- **messages**: All conversation messages
- **todos**: Current todo list
- **thread_id**: "thread_1" (all in one thread)

### UI State
- **_is_generating**: Prevents concurrent requests
- **_terminal_tool_calls**: Tool IDs awaiting results
- **_mutable_text_editor_tool_calls**: Tool ID → file path mapping

### Session State
- **BashTerminal**: Single global instance
  - Persistent pexpect shell
  - Current working directory preserved
  - Environment variables preserved

---

## Critical Design Patterns

### 1. Exclusive Async Work
```python
@work(exclusive=True, thread=False)
async def _handle_user_input(...):
    # Serializes requests, runs in main event loop
```

### 2. Node-Level Streaming
```python
async for chunk in agent.astream(..., stream_mode="updates"):
    # Each chunk = one node execution
    # Not token-level streaming
```

### 3. Tool Call Tracking
```python
# Terminal tools: Linear list
_terminal_tool_calls.append(tool_call["id"])

# Editor tools: Dict for file path
_mutable_text_editor_tool_calls[tool_call["id"]] = file_path
```

### 4. Session Persistence
```python
# Single global instance across calls
global keep_alive_terminal
if keep_alive_terminal is None:
    keep_alive_terminal = BashTerminal(...)
```

### 5. Message-Driven Architecture
```
HumanMessage → AIMessage → ToolMessage → Display
     ↓              ↓              ↓
  Display       Route/Display   Update UI
```

---

## Summary

DeerCode implements a **ReAct Agent Architecture** with:

1. **Synchronous Startup**: Quick application initialization
2. **Asynchronous MCP Loading**: Non-blocking tool loading on mount
3. **Exclusive Request Handling**: Only one request at a time
4. **Streaming Agent Updates**: Node-level updates, not token-level
5. **Smart Tool Routing**: Different handlers for different tool types
6. **Session Persistence**: Bash commands maintain state
7. **Incremental Display**: Messages appear as they arrive

The critical insight is that messages flow through **LangChain's message system** with explicit **tool call ID tracking** for matching results to UI components, enabling a smooth asynchronous experience.

