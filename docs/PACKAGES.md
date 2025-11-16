# DeerCode 包管理详细说明文档

## 目录
- [1. 包结构总览](#1-包结构总览)
- [2. 核心包详解](#2-核心包详解)
- [3. 依赖管理](#3-依赖管理)
- [4. 包开发指南](#4-包开发指南)
- [5. 测试策略](#5-测试策略)

---

## 1. 包结构总览

### 1.1 目录树

```
deer-code/
├── src/deer_code/              # 主包目录
│   ├── __init__.py             # 包初始化
│   ├── main.py                 # 入口文件
│   ├── project.py              # 项目管理
│   │
│   ├── agents/                 # Agent 层
│   │   ├── __init__.py
│   │   ├── coding_agent.py     # 编码 Agent
│   │   ├── research_agent.py   # 研究 Agent
│   │   └── state.py            # 状态定义
│   │
│   ├── cli/                    # UI 层
│   │   ├── __init__.py
│   │   ├── app.py              # 主应用
│   │   ├── theme.py            # 主题定义
│   │   └── components/         # UI 组件
│   │       ├── chat/           # 聊天组件
│   │       ├── editor/         # 编辑器组件
│   │       ├── terminal/       # 终端组件
│   │       └── todo/           # TODO 组件
│   │
│   ├── config/                 # 配置管理
│   │   ├── __init__.py
│   │   └── config.py           # 配置加载
│   │
│   ├── models/                 # 模型管理
│   │   ├── __init__.py
│   │   └── chat_model.py       # LLM 初始化
│   │
│   ├── prompts/                # Prompt 管理
│   │   ├── __init__.py
│   │   ├── template.py         # 模板引擎
│   │   └── templates/          # 模板文件
│   │       └── coding_agent.md
│   │
│   └── tools/                  # 工具层
│       ├── __init__.py
│       ├── reminders.py        # 提醒工具
│       ├── edit/               # 编辑工具
│       ├── fs/                 # 文件系统工具
│       ├── mcp/                # MCP 集成
│       ├── search/             # 搜索工具
│       ├── terminal/           # 终端工具
│       └── todo/               # TODO 工具
│
├── tests/                      # 测试目录
│   └── tools/
│       └── search/
│           └── test_tavily_search.py
│
├── docs/                       # 文档目录
│   ├── ARCHITECTURE.md         # 架构文档
│   ├── PACKAGES.md            # 本文档
│   ├── BUSINESS.md            # 业务文档
│   └── FRAMEWORKS.md          # 框架文档
│
├── config.example.yaml         # 配置示例
├── langgraph.json             # LangGraph 配置
├── pyproject.toml             # 项目配置
├── Makefile                   # 构建脚本
├── README.md                  # 项目说明
└── CLAUDE.md                  # Claude 指南
```

### 1.2 包分层架构

```
┌─────────────────────────────────────────────┐
│         Entry Point (main.py)              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          UI Layer (cli/)                    │
│  - 用户交互                                  │
│  - 消息展示                                  │
│  - 工具输出可视化                            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Agent Layer (agents/)               │
│  - 推理决策                                  │
│  - 工具调用                                  │
│  - 状态管理                                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Tools Layer (tools/)                │
│  - 文件操作                                  │
│  - 命令执行                                  │
│  - 外部集成                                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│    Infrastructure (config/, models/)        │
│  - 配置管理                                  │
│  - 模型初始化                                │
│  - Prompt 管理                              │
└─────────────────────────────────────────────┘
```

---

## 2. 核心包详解

### 2.1 agents/ - Agent 层

#### 2.1.1 包职责

负责 AI Agent 的创建、配置和状态管理。

#### 2.1.2 文件说明

##### `__init__.py`
```python
"""Agent 包导出"""
from .coding_agent import create_coding_agent
from .state import CodingAgentState

__all__ = ["create_coding_agent", "CodingAgentState"]
```

##### `coding_agent.py`
**功能**：创建主编码 Agent

**关键函数**：
```python
def create_coding_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """
    创建编码 Agent

    参数：
        plugin_tools: 额外的工具列表
        **kwargs: 传递给 create_agent 的其他参数

    返回：
        CompiledStateGraph: 编译后的状态图
    """
```

**依赖**：
- `langchain.agents.create_agent`
- 工具模块 (bash, grep, ls, text_editor, todo_write, tree)
- 模型初始化 (init_chat_model)
- Prompt 模板 (apply_prompt_template)

##### `research_agent.py`
**功能**：辅助研究和信息检索

**用途**：
- 网络搜索
- 文档查找
- 知识库检索

##### `state.py`
**功能**：定义 Agent 状态模式

```python
class CodingAgentState(MessagesState):
    """编码 Agent 状态

    属性：
        messages: 对话消息列表 (继承)
        todos: 任务列表
    """
    todos: list[Todo]
```

**状态生命周期**：
1. 初始化：空消息列表 + 空 TODO 列表
2. 更新：每轮对话后追加消息
3. 持久化：通过 LangGraph 检查点系统

#### 2.1.3 扩展指南

**添加新状态字段**：
```python
class CodingAgentState(MessagesState):
    todos: list[Todo]
    project_context: dict  # 新增：项目上下文
    file_history: list[str]  # 新增：文件访问历史
```

**创建新 Agent**：
```python
def create_review_agent():
    return create_agent(
        model=init_chat_model(),
        tools=[grep_tool, ls_tool],
        system_prompt=apply_prompt_template("review_agent"),
        state_schema=ReviewAgentState,
        name="review_agent"
    )
```

---

### 2.2 cli/ - UI 层

#### 2.2.1 包职责

提供基于 Textual 的终端用户界面。

#### 2.2.2 核心文件

##### `app.py` - 主应用

**类**: `ConsoleApp`

**关键方法**：
```python
class ConsoleApp(App):
    async def _init_agent(self):
        """异步初始化 Agent 和工具"""

    @work(exclusive=True, thread=False)
    async def _send_message(self, user_input: str):
        """处理用户消息"""

    async def _process_ai_text_message(self, message: AIMessage):
        """处理 AI 文本响应"""

    async def _process_tool_call_message(self, message: AIMessage):
        """处理工具调用请求"""

    async def _process_tool_message(self, message: ToolMessage):
        """处理工具执行结果"""
```

**状态跟踪**：
```python
self._terminal_tool_calls: list[str]  # Terminal 输出工具的 ID
self._mutable_text_editor_tool_calls: dict[str, str]  # 编辑器工具 ID → 文件路径
```

**工具路由表**：
```python
TOOL_ROUTING = {
    "bash": TerminalView,
    "grep": TerminalView,
    "ls": TerminalView,
    "tree": TerminalView,
    "text_editor": EditorTabs,
    "todo_write": TodoListView,
}
```

##### `theme.py` - 主题定义

**DEER_DARK_THEME**：
```python
DEER_DARK_THEME = Theme({
    "primary": "#007acc",        # VSCode 蓝色
    "secondary": "#6a9955",      # 绿色
    "warning": "#ce9178",        # 橙色
    "error": "#f48771",          # 红色
    "surface": "#1e1e1e",        # 深灰背景
    "surface-lighten-1": "#2d2d30",
    "text": "#cccccc",           # 浅灰文字
})
```

#### 2.2.3 组件包

##### `components/chat/` - 聊天组件

**文件**：
- `chat_view.py`: 聊天视图容器
- `message_list_view.py`: 消息列表
- `message_item_view.py`: 单条消息
- `chat_input.py`: 输入框
- `loading_indicator.py`: 加载指示器

**关键类**：
```python
class ChatView(Container):
    """聊天视图主容器"""
    def compose(self):
        yield MessageListView()
        yield ChatInput()

class MessageItemView(Static):
    """消息项视图"""
    def __init__(self, role: str, content: str):
        self.role = role  # "user" | "assistant"
        self.content = content
```

##### `components/editor/` - 编辑器组件

**文件**：
- `editor_tabs.py`: 编辑器标签页容器
- `code_view.py`: 代码视图

**关键功能**：
```python
class EditorTabs(TabbedContent):
    def open_file(self, file_path: str):
        """打开或创建文件标签"""

    def update_file_content(self, file_path: str, content: str):
        """更新文件内容"""

    def close_tab(self, tab_id: str):
        """关闭标签页"""

class CodeView(Static):
    """代码显示组件，支持语法高亮"""
    def __init__(self, content: str, language: str):
        # 使用 rich.syntax.Syntax 进行高亮
```

##### `components/terminal/` - 终端组件

**文件**：
- `terminal_view.py`: 终端输出视图

**功能**：
```python
class TerminalView(Static):
    def append_output(self, output: str):
        """追加命令输出"""

    def clear(self):
        """清空终端"""

    def set_working_directory(self, cwd: str):
        """显示当前工作目录"""
```

##### `components/todo/` - TODO 组件

**文件**：
- `todo_list_view.py`: TODO 列表视图

**功能**：
```python
class TodoListView(Static):
    def update_todos(self, todos: list[Todo]):
        """更新 TODO 列表"""

    def render_todo(self, todo: Todo) -> Text:
        """渲染单个 TODO 项"""
        # 返回格式化的 Rich Text
```

#### 2.2.4 布局配置

**网格布局** (app.py):
```python
def compose(self):
    with Container():
        with Horizontal():
            # 左侧：聊天视图 (3fr)
            yield ChatView().add_class("left-panel")

            # 右侧：编辑器 + 终端/TODO (4fr)
            with Vertical():
                # 编辑器 (70%)
                yield EditorTabs().add_class("editor-panel")

                # 底部标签页 (30%)
                with TabbedContent():
                    yield TabPane("Terminal", TerminalView())
                    yield TabPane("TODO", TodoListView())
```

---

### 2.3 config/ - 配置管理

#### 2.3.1 包职责

负责配置文件的加载、解析和访问。

#### 2.3.2 `config.py`

**关键函数**：
```python
def load_config(config_path: str = "config.yaml") -> dict:
    """
    加载 YAML 配置文件

    功能：
    - 读取 YAML 文件
    - 展开环境变量 ($VAR_NAME)
    - 验证必需字段

    返回：
        配置字典
    """

def get_config_section(path: list[str]) -> dict:
    """
    获取配置的指定部分

    示例：
        get_config_section(["models", "chat_model"])
        # 返回 config["models"]["chat_model"]
    """

def expand_env_vars(value: str) -> str:
    """
    展开环境变量

    示例：
        "$OPENAI_API_KEY" → os.getenv("OPENAI_API_KEY")
    """
```

**配置结构验证**：
```python
REQUIRED_SECTIONS = {
    "models": ["chat_model"],
    "models.chat_model": ["model", "api_base", "api_key"]
}
```

#### 2.3.3 配置示例

```yaml
models:
  chat_model:
    # 可选：指定提供商类型
    type: deepseek  # deepseek | doubao | (omit for OpenAI)

    # 必需：模型名称
    model: 'deepseek-chat'

    # 必需：API 端点
    api_base: 'https://api.deepseek.com/v1'

    # 必需：API 密钥 (支持环境变量)
    api_key: $DEEPSEEK_API_KEY

    # 可选：温度参数
    temperature: 0

    # 可选：最大 token
    max_tokens: 8192

    # 可选：额外参数
    extra_body:
      top_p: 0.9

tools:
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
```

---

### 2.4 models/ - 模型管理

#### 2.4.1 `chat_model.py`

**功能**：初始化 LLM 模型

**关键函数**：
```python
def init_chat_model() -> BaseChatModel:
    """
    根据配置初始化聊天模型

    支持的提供商：
    - OpenAI (默认)
    - DeepSeek (type: deepseek)
    - Doubao (type: doubao)

    返回：
        ChatModel 实例
    """
```

**实现逻辑**：
```python
config = get_config_section(["models", "chat_model"])
model_type = config.get("type")

if model_type == "deepseek":
    from langchain_deepseek import ChatDeepSeek
    return ChatDeepSeek(
        model=config["model"],
        api_key=config["api_key"],
        base_url=config["api_base"],
        temperature=config.get("temperature", 0),
        max_tokens=config.get("max_tokens", 8192),
        **config.get("extra_body", {})
    )
elif model_type == "doubao":
    # 类似实现
else:
    from langchain_openai import ChatOpenAI
    # 默认 OpenAI 实现
```

**扩展新提供商**：
```python
elif model_type == "anthropic":
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(
        model=config["model"],
        anthropic_api_key=config["api_key"],
        # ...
    )
```

---

### 2.5 prompts/ - Prompt 管理

#### 2.5.1 包职责

管理 Prompt 模板的加载和渲染。

#### 2.5.2 `template.py`

**关键函数**：
```python
def apply_prompt_template(template_name: str, **kwargs) -> str:
    """
    应用 Jinja2 模板

    参数：
        template_name: 模板名称 (不含 .md 后缀)
        **kwargs: 模板变量

    返回：
        渲染后的 Prompt

    示例：
        apply_prompt_template(
            "coding_agent",
            PROJECT_ROOT="/path/to/project"
        )
    """
```

**实现**：
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("prompts/templates"),
    autoescape=False
)

template = env.get_template(f"{template_name}.md")
return template.render(**kwargs)
```

#### 2.5.3 `templates/` - 模板目录

##### `coding_agent.md`

**模板结构**：
```markdown
# System Prompt

You are an AI coding assistant.

## Project Information
- Project Root: {{ PROJECT_ROOT }}
- Current Directory: {{ PROJECT_ROOT }}

## Available Tools
- bash: Execute bash commands
- text_editor: View, create, or edit files
- grep: Search for patterns in files
- ls: List directory contents
- tree: Display directory tree
- todo_write: Manage task list

## Guidelines
1. Use `todo_write` when tasks have 3+ steps
2. Always verify file paths before editing
3. Explain your reasoning before acting
...
```

**变量替换**：
```jinja2
{{ PROJECT_ROOT }}  → "/path/to/project"
{% if DEBUG %}...{% endif %}  → 条件渲染
{% for tool in TOOLS %}...{% endfor %}  → 循环渲染
```

---

### 2.6 tools/ - 工具层

#### 2.6.1 包结构

```
tools/
├── __init__.py              # 工具导出
├── reminders.py             # 提醒工具
├── edit/                    # 文本编辑
│   ├── tool.py
│   └── text_editor.py
├── fs/                      # 文件系统
│   ├── grep.py
│   ├── ls.py
│   ├── tree.py
│   └── ignore.py
├── mcp/                     # MCP 集成
│   ├── __init__.py
│   └── load_mcp_tools.py
├── search/                  # 搜索工具
│   ├── __init__.py
│   └── tavily_search.py
├── terminal/                # Bash 终端
│   ├── tool.py
│   └── bash_terminal.py
└── todo/                    # TODO 管理
    ├── tool.py
    └── types.py
```

#### 2.6.2 `edit/` - 文本编辑工具

##### `text_editor.py`

**类**: `TextEditor`

**方法**：
```python
class TextEditor:
    def view(self, file_path: str, line_range: Optional[tuple[int, int]] = None) -> str:
        """查看文件内容"""

    def create(self, file_path: str, file_text: str) -> str:
        """创建新文件"""

    def str_replace(self, file_path: str, old_str: str, new_str: str) -> str:
        """字符串替换"""

    def insert(self, file_path: str, insert_line: int, new_str: str) -> str:
        """在指定行插入"""
```

**错误处理**：
- 文件不存在 → 提示使用 `create`
- 字符串不匹配 → 显示上下文
- 行号越界 → 提示有效范围

##### `tool.py`

**工具定义**：
```python
@tool("text_editor", parse_docstring=True)
def text_editor_tool(
    runtime: ToolRuntime,
    command: Literal["view", "create", "str_replace", "insert"],
    file_path: str,
    **kwargs
) -> str:
    """Edit files with various operations."""
```

#### 2.6.3 `fs/` - 文件系统工具

##### `grep.py`

**功能**：正则表达式搜索

```python
@tool("grep", parse_docstring=True)
def grep_tool(
    runtime: ToolRuntime,
    pattern: str,
    file_glob: str = "*",
    case_sensitive: bool = True
) -> str:
    """Search for patterns in files."""
```

**特性**：
- 支持正则表达式
- 遵循 .gitignore 规则
- 显示行号和上下文

##### `ls.py`

**功能**：列出目录内容

```python
@tool("ls", parse_docstring=True)
def ls_tool(runtime: ToolRuntime, path: str = ".") -> str:
    """List directory contents."""
```

**特性**：
- 文件/目录图标
- 文件大小显示
- 修改时间

##### `tree.py`

**功能**：显示目录树

```python
@tool("tree", parse_docstring=True)
def tree_tool(
    runtime: ToolRuntime,
    path: str = ".",
    max_depth: int = 3
) -> str:
    """Display directory tree."""
```

**特性**：
- 可配置深度
- 遵循 .gitignore
- 树形可视化

##### `ignore.py`

**功能**：.gitignore 解析

```python
class IgnoreFilter:
    def __init__(self, root_dir: str):
        """加载 .gitignore 规则"""

    def should_ignore(self, path: str) -> bool:
        """判断路径是否应忽略"""
```

#### 2.6.4 `terminal/` - Bash 终端工具

##### `bash_terminal.py`

**类**: `BashTerminal`

**关键实现**：
```python
class BashTerminal:
    def __init__(self):
        # 启动持久化 bash 进程
        self.process = pexpect.spawn(
            "/bin/bash",
            encoding="utf-8",
            codec_errors="ignore"
        )

        # 设置自定义 prompt
        self.prompt = "DEERCODE_PROMPT_1234567890"
        self.process.sendline(f'export PS1="{self.prompt}"')

    def run_command(self, command: str, timeout: int = 30) -> str:
        """执行命令并返回输出"""
        self.process.sendline(command)
        self.process.expect(self.prompt, timeout=timeout)
        return self.process.before

    def get_cwd(self) -> str:
        """获取当前工作目录"""
        return self.run_command("pwd").strip()
```

**全局单例**：
```python
# 保持会话状态
keep_alive_terminal = BashTerminal()
```

##### `tool.py`

```python
@tool("bash", parse_docstring=True)
def bash_tool(
    runtime: ToolRuntime,
    command: str,
    timeout: int = 30
) -> str:
    """Execute bash commands."""
    return keep_alive_terminal.run_command(command, timeout)
```

#### 2.6.5 `todo/` - TODO 工具

##### `types.py`

**数据模型**：
```python
from pydantic import BaseModel

class Todo(BaseModel):
    """TODO 项"""
    id: str
    title: str
    status: Literal["pending", "in_progress", "completed"]
    created_at: datetime
    updated_at: datetime
```

##### `tool.py`

```python
@tool("todo_write", parse_docstring=True)
def todo_write_tool(
    runtime: ToolRuntime,
    action: Literal["add", "update", "remove"],
    todo_id: Optional[str] = None,
    **kwargs
) -> str:
    """Manage TODO list."""
```

#### 2.6.6 `mcp/` - MCP 集成

##### `load_mcp_tools.py`

**异步加载**：
```python
async def load_mcp_tools() -> list[BaseTool]:
    """从配置加载所有 MCP 服务器工具"""
    mcp_config = get_config_section(["tools", "mcp_servers"])
    tools = []

    for server_name, server_config in mcp_config.items():
        # 使用 langchain-mcp-adapters
        from langchain_mcp_adapters import create_mcp_client

        client = await create_mcp_client(
            transport=server_config["transport"],
            url=server_config["url"]
        )

        server_tools = await client.list_tools()
        tools.extend(server_tools)

    return tools
```

**集成流程**：
1. 读取 `config.yaml` 中的 `tools.mcp_servers`
2. 为每个服务器创建客户端
3. 获取工具列表
4. 返回给 Agent

#### 2.6.7 `search/` - 搜索工具

##### `tavily_search.py`

**功能**：网络搜索

```python
@tool("tavily_search", parse_docstring=True)
def tavily_search_tool(
    runtime: ToolRuntime,
    query: str,
    max_results: int = 5
) -> str:
    """Search the web using Tavily API."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    results = client.search(query, max_results=max_results)

    return format_search_results(results)
```

#### 2.6.8 `reminders.py`

**功能**：为 Agent 提供上下文提醒

```python
class ToolRuntime:
    """工具运行时上下文"""
    def add_reminder(self, message: str):
        """添加提醒消息"""

    def get_reminders(self) -> list[str]:
        """获取所有提醒"""
```

**使用示例**：
```python
@tool("my_tool")
def my_tool(runtime: ToolRuntime, param: str):
    if some_condition:
        runtime.add_reminder(
            "⚠️ Warning: This operation modifies system files"
        )
    return result
```

---

## 3. 依赖管理

### 3.1 核心依赖

#### pyproject.toml 分析

```toml
[project]
dependencies = [
    # HTTP 客户端 (支持 SOCKS 代理)
    "httpx[socks]>=0.28.1",

    # 模板引擎
    "jinja2>=3.1.6",

    # DeepSeek 模型集成
    "langchain-deepseek>=1.0.0",

    # MCP 适配器
    "langchain-mcp-adapters>=0.1.11",

    # LangChain 核心 + OpenAI
    "langchain[openai]>=1.0.1",

    # LangGraph 状态图框架
    "langgraph>=1.0.1",

    # 终端控制
    "pexpect>=4.9.0",

    # 数据验证
    "pydantic>=2.12.2",

    # 富文本终端输出
    "rich>=14.2.0",

    # 搜索 API
    "tavily-python>=0.5.0",

    # TUI 框架
    "textual>=6.3.0",
]
```

#### 依赖关系图

```
DeerCode
├── LangChain Ecosystem
│   ├── langchain>=1.0.1          # 核心框架
│   ├── langgraph>=1.0.1          # 状态图 Agent
│   ├── langchain-deepseek>=1.0.0 # DeepSeek 集成
│   └── langchain-mcp-adapters>=0.1.11  # MCP 工具
│
├── UI Framework
│   ├── textual>=6.3.0            # TUI 框架
│   └── rich>=14.2.0              # 富文本渲染
│
├── System Tools
│   └── pexpect>=4.9.0            # 终端控制
│
├── Data & Template
│   ├── pydantic>=2.12.2          # 数据验证
│   └── jinja2>=3.1.6             # 模板引擎
│
└── External APIs
    ├── httpx[socks]>=0.28.1      # HTTP 客户端
    └── tavily-python>=0.5.0      # 搜索 API
```

### 3.2 开发依赖

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0.0",              # 测试框架
    "pytest-asyncio>=0.24.0",     # 异步测试
    "pytest-cov>=6.0.0",          # 覆盖率
    "pytest-mock>=3.14.0",        # Mock 工具
]
```

### 3.3 依赖安装

#### 使用 uv (推荐)

```bash
# 安装生产依赖
uv sync

# 安装开发依赖
uv sync --all-extras

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev pytest-plugin
```

#### 使用 pip

```bash
# 安装生产依赖
pip install -e .

# 安装测试依赖
pip install -e ".[test]"
```

### 3.4 依赖锁定

**uv.lock**：
- 自动生成
- 精确版本锁定
- 跨平台一致性

**更新依赖**：
```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定依赖
uv sync --upgrade-package langchain
```

---

## 4. 包开发指南

### 4.1 创建新包

#### 步骤

```bash
# 1. 创建包目录
mkdir -p src/deer_code/my_package

# 2. 创建 __init__.py
touch src/deer_code/my_package/__init__.py

# 3. 添加模块文件
touch src/deer_code/my_package/module.py
```

#### 示例：创建 `analyzers` 包

```python
# src/deer_code/analyzers/__init__.py
"""代码分析器包"""
from .complexity import ComplexityAnalyzer
from .security import SecurityAnalyzer

__all__ = ["ComplexityAnalyzer", "SecurityAnalyzer"]
```

```python
# src/deer_code/analyzers/complexity.py
class ComplexityAnalyzer:
    def analyze(self, code: str) -> dict:
        """分析代码复杂度"""
        pass
```

### 4.2 添加新工具

#### 工具模板

```python
# src/deer_code/tools/my_tool/tool.py
from langchain.tools import tool, ToolRuntime
from typing import Literal

@tool("my_tool", parse_docstring=True)
def my_tool(
    runtime: ToolRuntime,
    action: Literal["action1", "action2"],
    param: str
) -> str:
    """Tool description for LLM.

    Args:
        action: The action to perform (action1 | action2)
        param: Parameter description

    Returns:
        Result description
    """
    # 实现逻辑
    if action == "action1":
        result = do_action1(param)
    else:
        result = do_action2(param)

    # 可选：添加提醒
    runtime.add_reminder("⚠️ Remember to check the result")

    return result
```

#### 注册工具

```python
# src/deer_code/tools/__init__.py
from .my_tool.tool import my_tool

__all__ = [..., "my_tool"]

# agents/coding_agent.py
from deer_code.tools import my_tool

tools = [bash_tool, ..., my_tool, *plugin_tools]
```

### 4.3 添加新 UI 组件

#### 组件模板

```python
# src/deer_code/cli/components/my_component/my_view.py
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text

class MyView(Static):
    """自定义视图组件"""

    # 响应式状态
    data: reactive[str] = reactive("")

    def __init__(self):
        super().__init__()

    def on_mount(self):
        """组件挂载时调用"""
        self.update_display()

    def watch_data(self, new_data: str):
        """data 变化时自动调用"""
        self.update_display()

    def update_display(self):
        """更新显示内容"""
        text = Text(self.data, style="cyan")
        self.update(text)

    async def on_click(self):
        """处理点击事件"""
        pass
```

#### 集成到主应用

```python
# cli/app.py
from .components.my_component.my_view import MyView

class ConsoleApp(App):
    def compose(self):
        # 添加到布局
        yield MyView()
```

### 4.4 添加新配置项

#### 配置定义

```yaml
# config.example.yaml
my_feature:
  enabled: true
  option1: value1
  option2: value2
```

#### 配置访问

```python
# 在代码中访问
from deer_code.config import get_config_section

my_config = get_config_section(["my_feature"])
if my_config.get("enabled"):
    # 使用功能
    pass
```

#### 配置验证

```python
# config/config.py
REQUIRED_SECTIONS = {
    "my_feature": ["enabled", "option1"],
}

def validate_config(config: dict):
    for section, required_keys in REQUIRED_SECTIONS.items():
        # 验证逻辑
```

---

## 5. 测试策略

### 5.1 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest 配置
├── agents/
│   └── test_coding_agent.py
├── cli/
│   └── test_app.py
├── config/
│   └── test_config.py
├── models/
│   └── test_chat_model.py
└── tools/
    ├── test_edit.py
    ├── test_fs.py
    ├── test_terminal.py
    └── search/
        └── test_tavily_search.py
```

### 5.2 测试示例

#### 单元测试

```python
# tests/tools/test_edit.py
import pytest
from deer_code.tools.edit import TextEditor

def test_text_editor_view(tmp_path):
    # 创建临时文件
    file_path = tmp_path / "test.py"
    file_path.write_text("def foo():\n    pass\n")

    # 测试 view 操作
    editor = TextEditor()
    content = editor.view(str(file_path))

    assert "def foo():" in content

def test_text_editor_str_replace(tmp_path):
    file_path = tmp_path / "test.py"
    file_path.write_text("old_value")

    editor = TextEditor()
    editor.str_replace(str(file_path), "old_value", "new_value")

    assert file_path.read_text() == "new_value"
```

#### 异步测试

```python
# tests/tools/search/test_tavily_search.py
import pytest
from deer_code.tools.search import tavily_search_tool

@pytest.mark.asyncio
async def test_tavily_search():
    # Mock ToolRuntime
    class MockRuntime:
        def add_reminder(self, msg): pass

    runtime = MockRuntime()
    result = tavily_search_tool(runtime, "Python programming")

    assert len(result) > 0
    assert "Python" in result
```

#### Mock 测试

```python
# tests/models/test_chat_model.py
import pytest
from unittest.mock import patch, MagicMock

@patch('deer_code.models.chat_model.ChatOpenAI')
def test_init_chat_model_openai(mock_openai):
    mock_model = MagicMock()
    mock_openai.return_value = mock_model

    from deer_code.models import init_chat_model
    model = init_chat_model()

    assert model == mock_model
    mock_openai.assert_called_once()
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/tools/test_edit.py

# 运行特定测试
pytest tests/tools/test_edit.py::test_text_editor_view

# 生成覆盖率报告
pytest --cov=deer_code --cov-report=html

# 查看覆盖率
open htmlcov/index.html
```

### 5.4 测试最佳实践

1. **使用 fixtures**：共享测试数据
2. **使用 tmp_path**：避免污染文件系统
3. **Mock 外部依赖**：API 调用、网络请求
4. **测试边界条件**：空输入、错误输入
5. **保持测试独立**：每个测试可独立运行

---

## 附录

### A. 包命名规范

- **包名**: 小写，下划线分隔 (如 `my_package`)
- **模块名**: 小写，下划线分隔 (如 `my_module.py`)
- **类名**: 大驼峰 (如 `MyClass`)
- **函数名**: 小写，下划线分隔 (如 `my_function`)
- **常量名**: 大写，下划线分隔 (如 `MAX_VALUE`)

### B. 导入规范

```python
# 标准库
import os
import sys

# 第三方库
from langchain.tools import tool
from textual.app import App

# 本地包 (绝对导入)
from deer_code.config import get_config_section
from deer_code.tools import bash_tool

# 相对导入 (仅在包内部)
from .utils import helper_function
```

### C. 文档字符串规范

```python
def my_function(param1: str, param2: int = 0) -> str:
    """简短描述 (一行).

    详细描述 (可选，多行).

    Args:
        param1: 参数1描述
        param2: 参数2描述 (默认: 0)

    Returns:
        返回值描述

    Raises:
        ValueError: 值错误的情况

    Example:
        >>> my_function("test", 42)
        "result"
    """
```

### D. 类型注解规范

```python
from typing import Optional, List, Dict, Literal, Union

def process_data(
    data: List[Dict[str, Any]],
    mode: Literal["fast", "slow"] = "fast",
    callback: Optional[Callable[[str], None]] = None
) -> Union[str, None]:
    """带完整类型注解的函数"""
    pass
```

### E. 包发布

```bash
# 构建包
uv build

# 检查包
twine check dist/*

# 上传到 PyPI (测试)
twine upload --repository testpypi dist/*

# 上传到 PyPI (生产)
twine upload dist/*
```
