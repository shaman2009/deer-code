# DeerCode 技术架构文档

## 目录
- [1. 系统概述](#1-系统概述)
- [2. 架构设计](#2-架构设计)
- [3. 核心组件](#3-核心组件)
- [4. 数据流](#4-数据流)
- [5. 技术选型](#5-技术选型)
- [6. 扩展性设计](#6-扩展性设计)

---

## 1. 系统概述

DeerCode 是一个基于 ReAct 框架的 AI 编码助手，采用双层架构设计：
- **UI 层**：基于 Textual 的 VSCode 风格终端界面（TUI）
- **Agent 层**：基于 LangGraph 的状态图式 Agent 系统

### 1.1 设计理念

```
简约而不简单 (Minimalist yet Powerful)
├── 教育优先：代码结构清晰，易于学习
├── 实用导向：功能完整，可直接使用
└── 可扩展性：支持插件和工具扩展
```

### 1.2 系统特性

- **多轮对话**：维护完整的对话上下文
- **任务规划**：内置 TODO 系统进行任务跟踪
- **代码操作**：支持查看、编辑、搜索代码
- **命令执行**：持久化 Bash 会话
- **工具扩展**：通过 MCP 协议集成外部工具

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                           │
│                    (Terminal Interface)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     UI Layer (Textual)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat View   │  │ Editor Tabs  │  │Terminal View │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ TODO List    │  │ Input Widget │                        │
│  └──────────────┘  └──────────────┘                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Agent Layer (LangGraph)                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │            CodingAgent (StateGraph)                │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐      │    │
│  │  │ Reasoning│──▶│  Acting  │──▶│ Observing│      │    │
│  │  └──────────┘   └──────────┘   └──────────┘      │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Tools Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Bash   │  │  Editor  │  │    FS    │  │   TODO   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐                                │
│  │   MCP    │  │  Search  │                                │
│  └──────────┘  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 双层架构详解

#### UI 层 (Textual TUI)
- **职责**：用户交互、消息展示、工具输出可视化
- **技术**：Textual (Python TUI 框架)
- **布局**：
  ```
  ┌────────────────┬──────────────────────────────┐
  │                │  Editor (70%)                │
  │   Chat         ├──────────────────────────────┤
  │   (3fr)        │  Terminal/TODO Tabs (30%)    │
  │                │                              │
  └────────────────┴──────────────────────────────┘
  ```

#### Agent 层 (LangGraph)
- **职责**：推理、决策、工具调用、状态管理
- **模式**：ReAct (Reasoning + Acting)
- **状态管理**：基于 LangGraph 的 StateGraph

---

## 3. 核心组件

### 3.1 Agent 系统

#### 3.1.1 CodingAgent (`agents/coding_agent.py`)

```python
# 核心组件
create_agent(
    model=ChatModel,           # LLM 模型
    tools=[...],               # 工具列表
    system_prompt=Prompt,      # 系统提示词
    state_schema=State,        # 状态模式
    name="coding_agent"
)
```

**状态定义** (`agents/state.py`):
```python
class CodingAgentState(MessagesState):
    todos: list[Todo]  # 任务列表
```

**关键特性**：
- 递归限制：100 轮对话
- 线程管理：单线程 `thread_id="thread_1"`
- 流式输出：`stream_mode="updates"` (节点级，非 token 级)

#### 3.1.2 ResearchAgent (`agents/research_agent.py`)

用于辅助研究和信息检索的子 Agent。

### 3.2 工具系统

#### 3.2.1 工具架构

```python
@tool("tool_name", parse_docstring=True)
def tool_function(runtime: ToolRuntime, param: str):
    """Tool description for LLM.

    Args:
        param: Parameter description
    """
    return "result"
```

#### 3.2.2 内置工具

| 工具名 | 路径 | 功能 | 关键技术 |
|--------|------|------|---------|
| **bash** | `tools/terminal/` | Bash 命令执行 | pexpect.spawn |
| **text_editor** | `tools/edit/` | 文件编辑 | str_replace, insert |
| **grep** | `tools/fs/grep.py` | 代码搜索 | ripgrep 集成 |
| **ls** | `tools/fs/ls.py` | 文件列表 | .gitignore 支持 |
| **tree** | `tools/fs/tree.py` | 目录树 | 忽略规则 |
| **todo_write** | `tools/todo/` | 任务管理 | Pydantic 模型 |
| **tavily_search** | `tools/search/` | 网络搜索 | Tavily API |
| **MCP Tools** | `tools/mcp/` | 外部工具 | MCP 适配器 |

#### 3.2.3 BashTerminal 详解

**持久化会话**：
```python
# 全局单例
keep_alive_terminal = BashTerminal()

# pexpect 实现
self.process = pexpect.spawn("/bin/bash")
```

**关键特性**：
- 保持工作目录 (cwd)
- 保持环境变量
- 自定义 prompt：`DEERCODE_PROMPT_1234567890`
- 输出解析：基于 prompt 标记

#### 3.2.4 TextEditor 详解

**支持操作**：
- `view`: 查看文件内容
- `create`: 创建新文件
- `str_replace`: 字符串替换编辑
- `insert`: 在指定行插入内容

**错误处理**：
- 文件不存在检查
- 字符串匹配验证
- 行号范围验证

### 3.3 UI 组件

#### 3.3.1 组件树

```
ConsoleApp (app.py)
├── ChatView (components/chat/)
│   ├── MessageListView
│   │   └── MessageItemView (多个)
│   ├── ChatInput
│   └── LoadingIndicator
├── EditorTabs (components/editor/)
│   └── CodeView (多个)
├── TerminalView (components/terminal/)
└── TodoListView (components/todo/)
```

#### 3.3.2 关键组件

**ConsoleApp** (`cli/app.py`):
```python
# 异步消息处理
@work(exclusive=True, thread=False)
async def _send_message(self, user_input: str):
    async for chunk in self._coding_agent.astream(...):
        # 处理流式更新
```

**工具调用跟踪**：
```python
self._terminal_tool_calls: list[str]  # Terminal 输出工具
self._mutable_text_editor_tool_calls: dict[str, str]  # 编辑器工具
```

#### 3.3.3 主题系统

**DEER_DARK_THEME** (`cli/theme.py`):
- VSCode 风格配色
- 语法高亮支持
- 响应式布局

### 3.4 配置系统

#### 3.4.1 配置结构

```yaml
models:
  chat_model:
    type: deepseek | doubao | (omit for OpenAI)
    model: 'model-name'
    api_base: 'https://api.endpoint.com/v1'
    api_key: $ENV_VAR
    temperature: 0
    max_tokens: 8192
    extra_body: {}

tools:
  mcp_servers:
    server_name:
      transport: 'streamable_http'
      url: 'https://...'
```

#### 3.4.2 配置加载

**config.py**:
```python
# 启动时加载一次
config = load_config("config.yaml")

# 访问配置
get_config_section(["models", "chat_model"])
```

**环境变量展开**：
- 支持 `$VAR_NAME` 语法
- 自动从环境变量读取

### 3.5 模型系统

#### 3.5.1 支持的模型

**init_chat_model()** (`models/chat_model.py`):
```python
if model_type == "deepseek":
    from langchain_deepseek import ChatDeepSeek
elif model_type == "doubao":
    from langchain_openai import ChatOpenAI
else:
    from langchain_openai import ChatOpenAI
```

**特性**：
- OpenAI 兼容接口
- 自定义参数支持 (`extra_body`)
- 流式输出支持

### 3.6 Prompt 系统

#### 3.6.1 模板引擎

**Jinja2 模板** (`prompts/templates/coding_agent.md`):
```jinja2
You are an AI coding assistant.

Project root: {{ PROJECT_ROOT }}

Available tools:
- bash: Execute bash commands
- text_editor: Edit files
...
```

**应用**:
```python
apply_prompt_template("coding_agent", PROJECT_ROOT="/path/to/project")
```

---

## 4. 数据流

### 4.1 消息流详解

```
User Input
    ↓
[HumanMessage] → ConsoleApp._send_message()
    ↓
coding_agent.astream({"messages": [...]})
    ↓
[Chunk Stream] → stream_mode="updates"
    ↓
┌─────────────────────────────────────┐
│ Chunk = {role: {"messages": [...]}} │
└─────────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│ AIMessage with tool_calls?        │
│   YES → _process_tool_call_message│
│   NO  → _process_ai_text_message  │
└───────────────────────────────────┘
    ↓
┌───────────────────────────────────┐
│ Tool Routing:                     │
│ - bash/grep/ls/tree → Terminal    │
│ - text_editor → EditorTabs        │
│ - todo_write → TodoListView       │
└───────────────────────────────────┘
    ↓
[ToolMessage] ← Tool Execution
    ↓
_process_tool_message() → Display in UI
    ↓
Back to Agent for next iteration
```

### 4.2 工具调用流程

```python
# 1. Agent 生成工具调用
AIMessage(
    content="",
    tool_calls=[{
        "name": "bash",
        "args": {"command": "ls -la"},
        "id": "call_123"
    }]
)

# 2. UI 处理工具调用
_process_tool_call_message()
├── 识别工具类型
├── 更新 UI (显示加载状态)
└── 记录 tool_call_id

# 3. 工具执行
ToolMessage(
    content="file1.py\nfile2.py",
    tool_call_id="call_123"
)

# 4. UI 显示结果
_process_tool_message()
├── 根据 tool_call_id 找到对应 UI 组件
└── 显示工具输出
```

### 4.3 状态管理

#### 4.3.1 LangGraph 状态

```python
# 状态自动持久化
config = {
    "thread_id": "thread_1",
    "recursion_limit": 100
}

# 所有对话在同一线程
# 状态包括：messages + todos
```

#### 4.3.2 UI 状态

- **Bash 会话**：全局单例 `keep_alive_terminal`
- **编辑器标签**：动态创建和销毁
- **TODO 列表**：同步自 Agent 状态
- **对话历史**：MessageListView 维护

---

## 5. 技术选型

### 5.1 核心技术栈

| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|---------|
| **Python** | 3.12+ | 主语言 | 简洁、易学、丰富生态 |
| **LangGraph** | 1.0.1+ | Agent 框架 | 状态管理、可视化、易调试 |
| **LangChain** | 1.0.1+ | LLM 框架 | 工具抽象、模型集成 |
| **Textual** | 6.3.0+ | TUI 框架 | 现代化、响应式、易用 |
| **pexpect** | 4.9.0+ | Terminal | 持久化 Bash 会话 |
| **Jinja2** | 3.1.6+ | 模板引擎 | Prompt 模板化 |
| **Pydantic** | 2.12.2+ | 数据验证 | 类型安全、自动验证 |

### 5.2 开发工具

| 工具 | 用途 |
|------|------|
| **uv** | 依赖管理、虚拟环境 |
| **langgraph-cli** | Agent 调试、开发模式 |
| **pytest** | 单元测试 |
| **black/ruff** | 代码格式化 |

### 5.3 技术决策

#### 5.3.1 为什么选择 LangGraph？

**优势**：
- 声明式状态图编程
- 内置检查点和时间旅行
- 可视化调试工具
- 流式输出支持

**对比**：
- vs **LangChain Agent**：更强的状态控制
- vs **AutoGen**：更简单的架构
- vs **CrewAI**：更底层的控制

#### 5.3.2 为什么选择 Textual？

**优势**：
- 纯 Python，无需 JS
- 响应式布局系统
- 丰富的内置组件
- 优秀的性能

**对比**：
- vs **Rich**：支持交互式 UI
- vs **Curses**：更现代化的 API
- vs **Electron**：更轻量、更快

#### 5.3.3 为什么使用 pexpect？

**优势**：
- 持久化进程状态
- 保持工作目录和环境
- 精确的输出解析

**对比**：
- vs **subprocess**：无状态，每次新进程
- vs **pty**：更底层，需手动管理

---

## 6. 扩展性设计

### 6.1 工具扩展

#### 6.1.1 添加新工具

**步骤**：
```python
# 1. 创建工具文件
# tools/my_tool/tool.py
from langchain.tools import tool, ToolRuntime

@tool("my_tool", parse_docstring=True)
def my_tool(runtime: ToolRuntime, param: str):
    """Tool description."""
    return "result"

# 2. 注册工具
# agents/coding_agent.py
from deer_code.tools.my_tool import my_tool

tools = [bash_tool, ..., my_tool, *plugin_tools]

# 3. (可选) UI 集成
# cli/app.py
elif tool_name == "my_tool":
    # 自定义 UI 处理
```

#### 6.1.2 MCP 工具集成

**配置**:
```yaml
tools:
  mcp_servers:
    my_server:
      transport: 'streamable_http'
      url: 'https://my-mcp-server.com/mcp'
```

**加载**:
```python
# tools/mcp/load_mcp_tools.py
async def load_mcp_tools() -> list[BaseTool]:
    # 自动从配置加载所有 MCP 服务器
```

### 6.2 Agent 扩展

#### 6.2.1 添加新 Agent

```python
# agents/my_agent.py
def create_my_agent():
    return create_agent(
        model=init_chat_model(),
        tools=[...],
        system_prompt=apply_prompt_template("my_agent"),
        state_schema=MyAgentState,
        name="my_agent"
    )
```

#### 6.2.2 Multi-Agent 协作

```python
# 使用 LangGraph 的子图功能
from langgraph.graph import StateGraph

workflow = StateGraph(CodingAgentState)
workflow.add_node("coding", coding_agent)
workflow.add_node("research", research_agent)
workflow.add_edge("coding", "research")
```

### 6.3 UI 扩展

#### 6.3.1 添加新组件

```python
# cli/components/my_component/my_view.py
from textual.widgets import Static

class MyView(Static):
    def __init__(self):
        super().__init__()

    def on_mount(self):
        # 初始化逻辑
        pass
```

#### 6.3.2 自定义主题

```python
# cli/theme.py
MY_THEME = Theme({
    "primary": "#00ff00",
    "secondary": "#0000ff",
    ...
})
```

### 6.4 模型扩展

#### 6.4.1 添加新模型提供商

```python
# models/chat_model.py
def init_chat_model():
    model_type = config.get("type")

    if model_type == "my_provider":
        from langchain_my_provider import ChatMyProvider
        return ChatMyProvider(
            model=config["model"],
            api_key=config["api_key"],
            **config.get("extra_body", {})
        )
```

### 6.5 插件系统设计

#### 6.5.1 插件接口

```python
# plugins/base.py
class DeerCodePlugin:
    def get_tools(self) -> list[BaseTool]:
        """返回插件提供的工具"""
        pass

    def get_ui_components(self) -> dict[str, Widget]:
        """返回插件提供的 UI 组件"""
        pass
```

#### 6.5.2 插件加载

```python
# 动态加载插件
import importlib

def load_plugins():
    plugins_dir = Path("plugins")
    for plugin_path in plugins_dir.glob("*/plugin.py"):
        module = importlib.import_module(f"plugins.{plugin_path.parent.name}.plugin")
        plugin = module.Plugin()
        yield plugin
```

---

## 附录

### A. 性能优化

- **流式输出**：减少首字节延迟
- **异步 I/O**：非阻塞 UI 更新
- **工具并行**：未来可支持并行工具调用

### B. 安全考虑

- **命令注入防护**：工具参数验证
- **文件访问控制**：限制在项目目录内
- **API 密钥管理**：环境变量存储

### C. 调试技巧

- **LangGraph Studio**：可视化 Agent 执行
- **Textual DevTools**：UI 布局调试
- **日志系统**：待添加结构化日志

### D. 参考资源

- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Textual 文档](https://textual.textualize.io/)
- [MCP 协议](https://modelcontextprotocol.io/)
