# DeerCode 开源框架说明文档

## 目录
- [1. 框架总览](#1-框架总览)
- [2. LangChain 生态系统](#2-langchain-生态系统)
- [3. UI 框架](#3-ui-框架)
- [4. 系统工具](#4-系统工具)
- [5. 数据与模板](#5-数据与模板)
- [6. 外部服务](#6-外部服务)
- [7. 开发工具](#7-开发工具)
- [8. 框架对比与选型](#8-框架对比与选型)

---

## 1. 框架总览

### 1.1 技术栈全景

```
┌────────────────────────────────────────────────────────┐
│                   DeerCode 技术栈                      │
└────────────────────────────────────────────────────────┘

AI/Agent 层
├── LangChain (1.0.1+)           # LLM 应用框架
├── LangGraph (1.0.1+)           # 状态图 Agent 框架
├── langchain-deepseek (1.0.0+)  # DeepSeek 模型集成
└── langchain-mcp-adapters (0.1.11+)  # MCP 工具适配

UI 层
├── Textual (6.3.0+)             # TUI 框架
└── Rich (14.2.0+)               # 富文本渲染

系统工具
└── pexpect (4.9.0+)             # 终端控制

数据处理
├── Pydantic (2.12.2+)           # 数据验证
└── Jinja2 (3.1.6+)              # 模板引擎

外部服务
├── httpx (0.28.1+)              # HTTP 客户端
└── tavily-python (0.5.0+)       # 搜索 API

开发工具
├── pytest (8.0.0+)              # 测试框架
└── uv                           # 包管理器
```

### 1.2 依赖关系图

```
DeerCode
│
├─── LangChain Ecosystem
│    ├─── langchain
│    │    ├── Core: 基础抽象、链、运行时
│    │    ├── Agents: Agent 框架
│    │    ├── Tools: 工具抽象
│    │    └── Memory: 记忆管理
│    │
│    ├─── langgraph
│    │    ├── StateGraph: 状态图编程
│    │    ├── Checkpoint: 状态持久化
│    │    └── Streaming: 流式输出
│    │
│    ├─── langchain-openai
│    │    └── ChatOpenAI: OpenAI 模型
│    │
│    ├─── langchain-deepseek
│    │    └── ChatDeepSeek: DeepSeek 模型
│    │
│    └─── langchain-mcp-adapters
│         └── MCP 协议适配
│
├─── Textual Framework
│    ├─── textual
│    │    ├── App: 应用基类
│    │    ├── Widgets: UI 组件
│    │    ├── Layout: 布局系统
│    │    └── Events: 事件系统
│    │
│    └─── rich
│         ├── Syntax: 语法高亮
│         ├── Text: 富文本
│         └── Console: 终端输出
│
└─── Supporting Libraries
     ├─── pexpect: Bash 会话
     ├─── pydantic: 类型验证
     ├─── jinja2: 模板渲染
     ├─── httpx: HTTP 请求
     └─── tavily-python: 搜索服务
```

---

## 2. LangChain 生态系统

### 2.1 LangChain Core

#### 2.1.1 概述

**官网**: https://python.langchain.com/
**版本**: 1.0.1+
**许可证**: MIT

**核心概念**:
```python
# 1. 可运行对象 (Runnable)
class Runnable(ABC):
    def invoke(self, input): ...
    async def ainvoke(self, input): ...
    def stream(self, input): ...
    async def astream(self, input): ...

# 2. 消息抽象
HumanMessage("用户输入")
AIMessage("AI 回复")
SystemMessage("系统提示")
ToolMessage("工具输出", tool_call_id="...")

# 3. 工具抽象
@tool("tool_name", parse_docstring=True)
def my_tool(param: str) -> str:
    """Tool description."""
    return "result"
```

#### 2.1.2 在 DeerCode 中的使用

**消息管理** (`cli/app.py`):
```python
from langchain_core.messages import HumanMessage, AIMessage

# 创建用户消息
user_message = HumanMessage(content=user_input)

# 发送给 Agent
async for chunk in self._coding_agent.astream(
    {"messages": [user_message]},
    stream_mode="updates"
):
    # 处理响应
```

**工具定义** (`tools/*/tool.py`):
```python
from langchain.tools import tool, ToolRuntime

@tool("bash", parse_docstring=True)
def bash_tool(runtime: ToolRuntime, command: str) -> str:
    """Execute bash commands.

    Args:
        command: The bash command to execute
    """
    return keep_alive_terminal.run_command(command)
```

#### 2.1.3 关键特性

**1. LCEL (LangChain Expression Language)**
```python
# 链式组合
chain = prompt | model | output_parser

# 等价于
result = output_parser(model(prompt(input)))
```

**2. 流式输出**
```python
async for chunk in chain.astream(input):
    print(chunk, end="", flush=True)
```

**3. 批处理**
```python
results = chain.batch([input1, input2, input3])
```

**4. 回调系统**
```python
from langchain.callbacks import StdOutCallbackHandler

chain.invoke(input, config={"callbacks": [StdOutCallbackHandler()]})
```

### 2.2 LangGraph

#### 2.2.1 概述

**官网**: https://langchain-ai.github.io/langgraph/
**版本**: 1.0.1+
**许可证**: MIT

**核心价值**: 将 Agent 建模为状态图

#### 2.2.2 核心概念

**状态图编程**:
```python
from langgraph.graph import StateGraph

# 定义状态
class State(TypedDict):
    messages: list[BaseMessage]
    next_step: str

# 创建图
workflow = StateGraph(State)

# 添加节点 (函数)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)

# 添加边 (控制流)
workflow.add_edge("agent", "tools")
workflow.add_conditional_edges(
    "tools",
    should_continue,
    {
        "continue": "agent",
        "end": END
    }
)

# 编译
app = workflow.compile()
```

#### 2.2.3 在 DeerCode 中的使用

**创建 CodingAgent** (`agents/coding_agent.py`):
```python
from langchain.agents import create_agent

def create_coding_agent(plugin_tools: list[BaseTool] = []):
    return create_agent(
        model=init_chat_model(),
        tools=[bash_tool, grep_tool, ...],
        system_prompt=apply_prompt_template("coding_agent"),
        state_schema=CodingAgentState,
        name="coding_agent"
    )
```

**内部结构** (由 `create_agent` 生成):
```
┌─────────────────────────────────────┐
│         CodingAgent Graph           │
└─────────────────────────────────────┘
        ↓
    __start__
        ↓
      agent  ← (LLM 推理)
        ↓
      tools  ← (工具执行)
        ↓
    should_continue?
      ├── yes → agent (循环)
      └── no  → __end__
```

**流式调用** (`cli/app.py`):
```python
async for chunk in self._coding_agent.astream(
    {"messages": [user_message]},
    stream_mode="updates",  # 节点级更新
    config={
        "thread_id": "thread_1",  # 对话线程
        "recursion_limit": 100     # 最大循环次数
    }
):
    # chunk 格式:
    # {
    #   "agent": {"messages": [AIMessage(...)]},
    #   "tools": {"messages": [ToolMessage(...)]},
    # }
    await self._process_chunk(chunk)
```

#### 2.2.4 关键特性

**1. 检查点系统 (Checkpointing)**
```python
from langgraph.checkpoint import MemorySaver

# 添加检查点
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# 状态自动保存
# 可以恢复到任意时间点
```

**2. 时间旅行 (Time Travel)**
```python
# 获取历史状态
state = await app.aget_state(config)

# 回滚到之前的状态
await app.aupdate_state(config, state_from_past)
```

**3. 人机交互 (Human-in-the-Loop)**
```python
# 在执行前暂停等待确认
workflow.add_node("ask_human", ask_human_node)
workflow.add_conditional_edges(
    "agent",
    need_confirmation,
    {
        "yes": "ask_human",
        "no": "tools"
    }
)
```

**4. 并行执行**
```python
# 并行调用多个节点
workflow.add_node("tool1", tool1_node)
workflow.add_node("tool2", tool2_node)

# 从 agent 并行到两个工具
workflow.add_edge("agent", "tool1")
workflow.add_edge("agent", "tool2")
```

#### 2.2.5 调试工具

**LangGraph Studio**:
```bash
# 安装 CLI
pip install langgraph-cli

# 启动开发服务器
make dev  # 等价于 langgraph dev

# 访问可视化界面
# https://agentchat.vercel.app/?apiUrl=http://localhost:2024
```

**可视化功能**:
- 状态图展示
- 单步执行
- 状态检查
- 消息历史

### 2.3 LangChain 模型集成

#### 2.3.1 langchain-openai

**版本**: 作为 `langchain[openai]` 的一部分

**使用** (`models/chat_model.py`):
```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-5-2025-08-07",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.openai.com/v1",
    temperature=0,
    max_tokens=8192,
    # OpenAI 特定参数
    model_kwargs={
        "reasoning_effort": "medium"  # o1 模型
    }
)
```

**支持的模型**:
- GPT-4 系列: `gpt-4`, `gpt-4-turbo`
- GPT-5 系列: `gpt-5-2025-08-07`
- o1 系列: `o1-preview`, `o1-mini`

#### 2.3.2 langchain-deepseek

**官网**: https://github.com/langchain-ai/langchain-deepseek
**版本**: 1.0.0+

**使用**:
```python
from langchain_deepseek import ChatDeepSeek

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
    temperature=0,
    max_tokens=8192
)
```

**DeepSeek 模型**:
- `deepseek-chat`: 对话模型
- `deepseek-reasoner`: 推理模型 (类似 o1)

#### 2.3.3 Doubao (字节跳动)

**使用 OpenAI 兼容接口**:
```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="doubao-seed-1-6-250615",
    api_key=os.getenv("ARK_API_KEY"),
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # Doubao 特定参数
    model_kwargs={
        "thinking": {"type": "auto"}
    }
)
```

### 2.4 langchain-mcp-adapters

#### 2.4.1 概述

**版本**: 0.1.11+
**用途**: 将 MCP (Model Context Protocol) 服务器转换为 LangChain 工具

**MCP 协议**:
- 由 Anthropic 提出
- 标准化的工具协议
- 支持多种传输方式

#### 2.4.2 在 DeerCode 中的使用

**配置** (`config.yaml`):
```yaml
tools:
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
```

**加载工具** (`tools/mcp/load_mcp_tools.py`):
```python
from langchain_mcp_adapters import create_mcp_client

async def load_mcp_tools() -> list[BaseTool]:
    mcp_config = get_config_section(["tools", "mcp_servers"])
    tools = []

    for server_name, server_config in mcp_config.items():
        client = await create_mcp_client(
            transport=server_config["transport"],
            url=server_config["url"]
        )

        # 获取服务器提供的所有工具
        server_tools = await client.list_tools()
        tools.extend(server_tools)

    return tools
```

**集成到 Agent**:
```python
# 启动时加载
mcp_tools = await load_mcp_tools()

# 添加到工具列表
agent = create_coding_agent(plugin_tools=mcp_tools)
```

#### 2.4.3 MCP 工具示例

**Context7 MCP**:
```python
# Agent 可以调用
context7_search(query="authentication")
# 返回代码库中相关代码片段

context7_get_context(file_path="auth.py")
# 返回文件的上下文信息
```

---

## 3. UI 框架

### 3.1 Textual

#### 3.1.1 概述

**官网**: https://textual.textualize.io/
**版本**: 6.3.0+
**许可证**: MIT
**作者**: Textualize.io (Will McGugan)

**核心价值**: 在终端中构建现代化 UI

#### 3.1.2 核心概念

**1. App 类**
```python
from textual.app import App

class MyApp(App):
    def compose(self):
        """定义 UI 结构"""
        yield Header()
        yield Container(...)
        yield Footer()

    def on_mount(self):
        """应用启动时调用"""
        pass

if __name__ == "__main__":
    app = MyApp()
    app.run()
```

**2. Widget 组件**
```python
from textual.widgets import Static, Button, Input

class MyWidget(Static):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def on_button_pressed(self, event: Button.Pressed):
        self.counter += 1
        self.update(f"Count: {self.counter}")
```

**3. Reactive 响应式**
```python
from textual.reactive import reactive

class Counter(Static):
    count: reactive[int] = reactive(0)

    def watch_count(self, new_count: int):
        """count 变化时自动调用"""
        self.update(f"Count: {new_count}")

    def increment(self):
        self.count += 1  # 自动触发 watch_count
```

**4. CSS 样式**
```css
/* app.css */
#my-widget {
    background: #1e1e1e;
    color: #cccccc;
    border: solid blue;
    height: 10;
}

Button {
    width: 20;
    margin: 1 2;
}
```

```python
class MyApp(App):
    CSS_PATH = "app.css"
```

#### 3.1.3 在 DeerCode 中的使用

**主应用** (`cli/app.py`):
```python
from textual.app import App
from textual.widgets import Header, Footer
from textual.containers import Container, Horizontal, Vertical

class ConsoleApp(App):
    """DeerCode 主应用"""

    CSS = """
    .left-panel {
        width: 3fr;
    }
    .right-panel {
        width: 4fr;
    }
    """

    def compose(self):
        yield Header()
        with Horizontal():
            # 左侧：聊天
            yield ChatView().add_class("left-panel")

            # 右侧：编辑器 + 终端
            with Vertical().add_class("right-panel"):
                yield EditorTabs()
                with TabbedContent():
                    with TabPane("Terminal"):
                        yield TerminalView()
                    with TabPane("TODO"):
                        yield TodoListView()
        yield Footer()
```

**自定义组件** (`cli/components/chat/message_item_view.py`):
```python
from textual.widgets import Static
from rich.text import Text

class MessageItemView(Static):
    """单条消息组件"""

    def __init__(self, role: str, content: str):
        super().__init__()
        self.role = role
        self.content = content

    def render(self) -> Text:
        """渲染消息"""
        if self.role == "user":
            return Text(f"👤 {self.content}", style="cyan")
        else:
            return Text(f"🤖 {self.content}", style="green")
```

#### 3.1.4 关键特性

**1. 布局系统**
```python
# Horizontal: 水平布局
with Horizontal():
    yield Widget1()  # 左
    yield Widget2()  # 右

# Vertical: 垂直布局
with Vertical():
    yield Widget1()  # 上
    yield Widget2()  # 下

# Grid: 网格布局
with Grid():
    yield Widget1()  # (0, 0)
    yield Widget2()  # (0, 1)
    yield Widget3()  # (1, 0)
```

**2. 事件系统**
```python
class MyApp(App):
    def on_key(self, event: Key):
        """键盘事件"""
        if event.key == "q":
            self.exit()

    def on_button_pressed(self, event: Button.Pressed):
        """按钮点击"""
        self.notify(f"Button {event.button.id} pressed")

    def on_mount(self):
        """挂载事件"""
        self.title = "My App"
```

**3. Workers (异步任务)**
```python
from textual.worker import work

class MyApp(App):
    @work(exclusive=True, thread=False)
    async def fetch_data(self):
        """后台任务"""
        async for item in async_generator():
            self.update_ui(item)
```

**4. 通知系统**
```python
self.notify("操作成功", severity="information")
self.notify("警告信息", severity="warning")
self.notify("错误发生", severity="error")
```

#### 3.1.5 优势

- **纯 Python**: 无需学习 JS/HTML
- **响应式**: 自动更新 UI
- **高性能**: 60 FPS 渲染
- **跨平台**: Windows/macOS/Linux
- **现代化**: 支持鼠标、动画、主题

### 3.2 Rich

#### 3.2.1 概述

**官网**: https://rich.readthedocs.io/
**版本**: 14.2.0+
**许可证**: MIT
**作者**: Will McGugan (同 Textual)

**核心价值**: 终端富文本渲染

#### 3.2.2 核心功能

**1. 富文本 (Rich Text)**
```python
from rich.text import Text

text = Text("Hello", style="bold red")
text.append(" World", style="italic blue")
print(text)
```

**2. 语法高亮 (Syntax)**
```python
from rich.syntax import Syntax

code = '''
def hello():
    print("Hello, World!")
'''

syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
print(syntax)
```

**3. 表格 (Table)**
```python
from rich.table import Table

table = Table(title="Star Wars Movies")
table.add_column("Released", style="cyan")
table.add_column("Title", style="magenta")
table.add_row("1977", "A New Hope")
table.add_row("1980", "The Empire Strikes Back")
print(table)
```

**4. 进度条 (Progress)**
```python
from rich.progress import track

for i in track(range(100), description="Processing..."):
    # 处理任务
    time.sleep(0.1)
```

**5. Markdown 渲染**
```python
from rich.markdown import Markdown

md = Markdown("# Title\n\nThis is **bold** text.")
print(md)
```

#### 3.2.3 在 DeerCode 中的使用

**语法高亮** (`cli/components/editor/code_view.py`):
```python
from rich.syntax import Syntax

class CodeView(Static):
    def __init__(self, content: str, language: str):
        super().__init__()
        self.content = content
        self.language = language

    def render(self) -> Syntax:
        return Syntax(
            self.content,
            self.language,
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
```

**富文本消息** (`cli/components/chat/message_item_view.py`):
```python
from rich.text import Text

def render_message(role: str, content: str) -> Text:
    if role == "user":
        icon = Text("👤", style="cyan")
        message = Text(content, style="white")
    else:
        icon = Text("🤖", style="green")
        message = Text(content, style="white")

    return icon + Text(" ") + message
```

#### 3.2.4 主题系统

**预设主题**:
- monokai
- github-dark
- dracula
- nord
- one-dark

**自定义主题**:
```python
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "green",
})
```

---

## 4. 系统工具

### 4.1 pexpect

#### 4.1.1 概述

**官网**: https://pexpect.readthedocs.io/
**版本**: 4.9.0+
**许可证**: ISC
**用途**: 控制和自动化交互式程序

#### 4.1.2 核心功能

**1. 启动进程**
```python
import pexpect

child = pexpect.spawn("/bin/bash")
```

**2. 发送命令**
```python
child.sendline("ls -la")
```

**3. 等待输出**
```python
child.expect("prompt>")  # 等待提示符
child.expect(r"\d+")     # 等待正则匹配
```

**4. 读取输出**
```python
output = child.before  # 匹配前的内容
```

#### 4.1.3 在 DeerCode 中的使用

**BashTerminal** (`tools/terminal/bash_terminal.py`):
```python
import pexpect

class BashTerminal:
    def __init__(self):
        # 启动 bash 进程
        self.process = pexpect.spawn(
            "/bin/bash",
            encoding="utf-8",
            codec_errors="ignore",
            echo=False
        )

        # 设置自定义 prompt
        self.prompt = "DEERCODE_PROMPT_1234567890"
        self.process.sendline(f'export PS1="{self.prompt}"')
        self.process.expect(self.prompt)

    def run_command(self, command: str, timeout: int = 30) -> str:
        """执行命令并返回输出"""
        # 发送命令
        self.process.sendline(command)

        # 等待 prompt 返回
        try:
            self.process.expect(self.prompt, timeout=timeout)
        except pexpect.TIMEOUT:
            return "Error: Command timed out"

        # 读取输出
        output = self.process.before
        return output.strip()

    def get_cwd(self) -> str:
        """获取当前工作目录"""
        return self.run_command("pwd").strip()

# 全局单例，保持会话状态
keep_alive_terminal = BashTerminal()
```

#### 4.1.4 关键特性

**1. 持久化会话**
```python
# 工作目录保持
terminal.run_command("cd /tmp")
terminal.run_command("pwd")  # 输出: /tmp

# 环境变量保持
terminal.run_command("export MY_VAR=value")
terminal.run_command("echo $MY_VAR")  # 输出: value
```

**2. 精确输出解析**
```python
# 使用自定义 prompt 避免混淆
# 不会误判命令输出中的 "$ " 为 prompt
```

**3. 超时控制**
```python
try:
    terminal.run_command("sleep 100", timeout=5)
except pexpect.TIMEOUT:
    # 处理超时
```

**4. 交互式程序支持**
```python
# 可以自动化交互式程序
child.expect("Password:")
child.sendline("my_password")
```

---

## 5. 数据与模板

### 5.1 Pydantic

#### 5.1.1 概述

**官网**: https://docs.pydantic.dev/
**版本**: 2.12.2+
**许可证**: MIT
**用途**: 数据验证和设置管理

#### 5.1.2 核心功能

**1. 数据模型**
```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str
    age: int = Field(gt=0, lt=150)
    email: str

# 自动验证
user = User(name="Alice", age=30, email="alice@example.com")
# user = User(name="Bob", age=-1)  # ValidationError
```

**2. 类型强制**
```python
user = User(name="Alice", age="30", email="alice@example.com")
# age 自动转换为 int
```

**3. JSON 序列化**
```python
# 转 JSON
json_str = user.model_dump_json()

# 从 JSON
user = User.model_validate_json(json_str)
```

**4. 配置管理**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()  # 自动从环境变量加载
```

#### 5.1.3 在 DeerCode 中的使用

**TODO 模型** (`tools/todo/types.py`):
```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class Todo(BaseModel):
    """TODO 项数据模型"""
    id: str = Field(description="TODO ID")
    title: str = Field(description="TODO 标题")
    status: Literal["pending", "in_progress", "completed"] = Field(
        default="pending",
        description="TODO 状态"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def mark_completed(self):
        """标记为完成"""
        self.status = "completed"
        self.updated_at = datetime.now()
```

**Agent 状态** (`agents/state.py`):
```python
from pydantic import BaseModel
from langgraph.graph import MessagesState

class CodingAgentState(MessagesState):
    """编码 Agent 状态

    继承 MessagesState 获得 messages 字段
    添加自定义字段 todos
    """
    todos: list[Todo] = []

    class Config:
        arbitrary_types_allowed = True
```

#### 5.1.4 优势

- **类型安全**: 编译时和运行时检查
- **自动验证**: 无需手动编写验证逻辑
- **清晰的错误**: 详细的验证错误信息
- **IDE 支持**: 完整的自动补全

### 5.2 Jinja2

#### 5.2.1 概述

**官网**: https://jinja.palletsprojects.com/
**版本**: 3.1.6+
**许可证**: BSD
**用途**: 强大的模板引擎

#### 5.2.2 核心语法

**1. 变量替换**
```jinja2
Hello, {{ name }}!
```

**2. 条件语句**
```jinja2
{% if user.is_admin %}
  Admin Panel
{% else %}
  User Panel
{% endif %}
```

**3. 循环**
```jinja2
{% for item in items %}
  - {{ item }}
{% endfor %}
```

**4. 过滤器**
```jinja2
{{ name | upper }}
{{ price | round(2) }}
{{ date | format_date }}
```

**5. 宏 (函数)**
```jinja2
{% macro input(name, type='text') %}
  <input type="{{ type }}" name="{{ name }}">
{% endmacro %}

{{ input('username') }}
{{ input('password', type='password') }}
```

#### 5.2.3 在 DeerCode 中的使用

**Prompt 模板** (`prompts/templates/coding_agent.md`):
```jinja2
# System Prompt

You are an AI coding assistant for the project at {{ PROJECT_ROOT }}.

## Project Information
- Root Directory: {{ PROJECT_ROOT }}
- Python Version: {{ PYTHON_VERSION }}

## Available Tools

{% for tool in TOOLS %}
- **{{ tool.name }}**: {{ tool.description }}
{% endfor %}

## Guidelines

1. Always use `todo_write` when tasks have 3+ steps
2. Before editing files, use `text_editor` with command="view"
3. Use `bash` for running tests and commands

{% if DEBUG %}
## Debug Mode
You are in debug mode. Provide verbose explanations.
{% endif %}

Now, help the user with their coding tasks.
```

**模板应用** (`prompts/template.py`):
```python
from jinja2 import Environment, FileSystemLoader
import os

def apply_prompt_template(template_name: str, **kwargs) -> str:
    """应用 Jinja2 模板

    Args:
        template_name: 模板名称 (不含 .md 后缀)
        **kwargs: 模板变量

    Returns:
        渲染后的 Prompt
    """
    # 创建 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader("prompts/templates"),
        autoescape=False,  # 不转义 (因为是纯文本)
        trim_blocks=True,   # 删除块后的空行
        lstrip_blocks=True  # 删除块前的空格
    )

    # 加载模板
    template = env.get_template(f"{template_name}.md")

    # 渲染
    return template.render(**kwargs)

# 使用
prompt = apply_prompt_template(
    "coding_agent",
    PROJECT_ROOT="/path/to/project",
    PYTHON_VERSION="3.12",
    TOOLS=[bash_tool, grep_tool, ...],
    DEBUG=False
)
```

#### 5.2.4 优势

- **灵活强大**: 支持复杂逻辑
- **易于维护**: 分离模板和代码
- **可复用**: 宏和继承机制
- **调试友好**: 清晰的错误信息

---

## 6. 外部服务

### 6.1 httpx

#### 6.1.1 概述

**官网**: https://www.python-httpx.org/
**版本**: 0.28.1+
**许可证**: BSD
**用途**: 现代 HTTP 客户端

#### 6.1.2 核心功能

**1. 同步请求**
```python
import httpx

response = httpx.get("https://api.example.com/data")
print(response.json())
```

**2. 异步请求**
```python
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/data")
    print(response.json())
```

**3. SOCKS 代理**
```python
# DeerCode 安装了 httpx[socks]
proxies = {
    "http://": "socks5://localhost:1080",
    "https://": "socks5://localhost:1080"
}

response = httpx.get("https://api.example.com", proxies=proxies)
```

**4. HTTP/2 支持**
```python
client = httpx.Client(http2=True)
response = client.get("https://http2.example.com")
```

#### 6.1.3 在 DeerCode 中的使用

**MCP 客户端** (`tools/mcp/load_mcp_tools.py`):
```python
import httpx

async def fetch_mcp_tools(url: str) -> list[BaseTool]:
    async with httpx.AsyncClient() as client:
        # 获取 MCP 服务器信息
        response = await client.get(f"{url}/info")
        server_info = response.json()

        # 获取工具列表
        response = await client.get(f"{url}/tools")
        tools_data = response.json()

        # 转换为 LangChain 工具
        tools = [
            convert_mcp_tool_to_langchain(tool_data)
            for tool_data in tools_data
        ]

        return tools
```

**网络搜索** (未来可能的实现):
```python
async def web_search(query: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.search.com/search",
            params={"q": query}
        )
        return response.text
```

#### 6.1.4 相比 requests 的优势

- **异步支持**: 原生 async/await
- **HTTP/2**: 性能更好
- **更现代**: 更好的 API 设计
- **SOCKS 代理**: 内置支持

### 6.2 tavily-python

#### 6.2.1 概述

**官网**: https://tavily.com/
**版本**: 0.5.0+
**用途**: AI 搜索 API

#### 6.2.2 核心功能

**1. 基础搜索**
```python
from tavily import TavilyClient

client = TavilyClient(api_key="your_key")
results = client.search("Python programming")
```

**2. 高级搜索**
```python
results = client.search(
    query="LangGraph tutorial",
    search_depth="advanced",  # basic | advanced
    max_results=10,
    include_domains=["langchain-ai.github.io"],
    exclude_domains=["stackoverflow.com"]
)
```

**3. 结果格式**
```python
{
    "results": [
        {
            "title": "LangGraph Documentation",
            "url": "https://...",
            "content": "LangGraph is...",
            "score": 0.98
        },
        ...
    ]
}
```

#### 6.2.3 在 DeerCode 中的使用

**搜索工具** (`tools/search/tavily_search.py`):
```python
from langchain.tools import tool, ToolRuntime
from tavily import TavilyClient
import os

@tool("tavily_search", parse_docstring=True)
def tavily_search_tool(
    runtime: ToolRuntime,
    query: str,
    max_results: int = 5
) -> str:
    """Search the web using Tavily API.

    Args:
        query: The search query
        max_results: Maximum number of results (default: 5)

    Returns:
        Formatted search results
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY not set"

    client = TavilyClient(api_key=api_key)

    try:
        results = client.search(query, max_results=max_results)
    except Exception as e:
        return f"Error: {str(e)}"

    # 格式化结果
    formatted = f"Search results for '{query}':\n\n"
    for i, result in enumerate(results["results"], 1):
        formatted += f"{i}. {result['title']}\n"
        formatted += f"   URL: {result['url']}\n"
        formatted += f"   {result['content'][:200]}...\n\n"

    return formatted
```

**使用场景**:
```
User: "FastAPI 的最新最佳实践？"
Agent: tavily_search("FastAPI best practices 2025")
       → 返回最新文档和教程
       → 总结要点给用户
```

#### 6.2.4 优势

- **AI 优化**: 结果针对 AI 优化
- **高质量**: 过滤低质量内容
- **快速**: 响应速度快
- **可配置**: 灵活的搜索选项

---

## 7. 开发工具

### 7.1 pytest

#### 7.1.1 概述

**官网**: https://pytest.org/
**版本**: 8.0.0+
**许可证**: MIT
**用途**: Python 测试框架

#### 7.1.2 核心功能

**1. 简单测试**
```python
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"
```

**2. Fixtures (测试装置)**
```python
import pytest

@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("content")
    return file

def test_file_read(temp_file):
    assert temp_file.read_text() == "content"
```

**3. 参数化测试**
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

**4. 异步测试**
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result == "expected"
```

#### 7.1.3 在 DeerCode 中的使用

**测试结构**:
```
tests/
├── conftest.py              # 共享 fixtures
├── tools/
│   ├── test_edit.py
│   ├── test_fs.py
│   └── search/
│       └── test_tavily_search.py
```

**示例测试** (`tests/tools/search/test_tavily_search.py`):
```python
import pytest
from deer_code.tools.search import tavily_search_tool

@pytest.mark.asyncio
async def test_tavily_search_basic():
    """测试基本搜索功能"""
    class MockRuntime:
        def add_reminder(self, msg): pass

    runtime = MockRuntime()
    result = tavily_search_tool(runtime, "Python programming")

    assert len(result) > 0
    assert "Python" in result

@pytest.mark.skipif(
    "TAVILY_API_KEY" not in os.environ,
    reason="TAVILY_API_KEY not set"
)
async def test_tavily_search_real():
    """使用真实 API 测试 (需要 API key)"""
    runtime = MockRuntime()
    result = tavily_search_tool(runtime, "LangGraph")

    assert "LangGraph" in result
```

**运行测试**:
```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/tools/search/test_tavily_search.py

# 运行特定测试
pytest tests/tools/search/test_tavily_search.py::test_tavily_search_basic

# 生成覆盖率报告
pytest --cov=deer_code --cov-report=html
```

### 7.2 pytest 插件

#### 7.2.1 pytest-asyncio

**用途**: 异步测试支持

```python
@pytest.mark.asyncio
async def test_async():
    await asyncio.sleep(0.1)
    assert True
```

#### 7.2.2 pytest-cov

**用途**: 代码覆盖率

```bash
pytest --cov=deer_code --cov-report=term-missing
```

#### 7.2.3 pytest-mock

**用途**: Mock 和 Patch

```python
def test_with_mock(mocker):
    mock_function = mocker.patch('module.function')
    mock_function.return_value = "mocked"

    result = call_function()
    assert result == "mocked"
    mock_function.assert_called_once()
```

### 7.3 uv

#### 7.3.1 概述

**官网**: https://docs.astral.sh/uv/
**作者**: Astral (Ruff 团队)
**用途**: 极快的 Python 包管理器

#### 7.3.2 核心命令

```bash
# 创建虚拟环境
uv venv

# 安装依赖
uv sync

# 添加包
uv add package-name

# 运行脚本
uv run python script.py
uv run -m deer_code.main

# 构建包
uv build
```

#### 7.3.3 优势

- **极快**: 比 pip 快 10-100 倍
- **Rust 实现**: 高性能
- **兼容性**: 兼容 pip/poetry
- **锁文件**: uv.lock 精确锁定

---

## 8. 框架对比与选型

### 8.1 Agent 框架对比

| 框架 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| **LangGraph** | 状态管理强、可视化好 | 学习曲线稍陡 | 复杂 Agent、多步推理 |
| **LangChain Agent** | 简单易用 | 状态控制弱 | 简单任务、快速原型 |
| **AutoGen** | 多 Agent 协作 | 重量级、配置复杂 | 团队协作、复杂系统 |
| **CrewAI** | 角色明确、易理解 | 灵活性较低 | 特定领域、团队模拟 |

**DeerCode 选择 LangGraph 的原因**:
1. **教育友好**: 状态图易于理解
2. **调试工具**: LangGraph Studio 可视化
3. **生产就绪**: 检查点、时间旅行等特性
4. **社区活跃**: LangChain 生态系统

### 8.2 TUI 框架对比

| 框架 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| **Textual** | 现代化、响应式、易用 | 年轻、生态小 | 复杂 TUI、现代应用 |
| **Rich** | 简单、美观 | 不支持交互 | 日志、输出美化 |
| **Curses** | 成熟、标准库 | API 复杂、过时 | 传统 Unix 工具 |
| **PyQt** | 功能强大 | 重量级、非 TUI | GUI 应用 |

**DeerCode 选择 Textual 的原因**:
1. **纯 Python**: 无需编译、易分发
2. **现代化**: 响应式、CSS 样式
3. **开发体验**: 热重载、DevTools
4. **性能**: 60 FPS 渲染

### 8.3 模型集成对比

| 集成方式 | 优势 | 劣势 |
|---------|------|------|
| **langchain-openai** | 官方支持、功能完整 | 仅 OpenAI |
| **langchain-deepseek** | 专门优化、性能好 | 仅 DeepSeek |
| **OpenAI 兼容接口** | 通用、灵活 | 可能缺少特定功能 |

**DeerCode 策略**: 混合使用
- 主流模型用专门集成
- 新模型用兼容接口
- 统一 `init_chat_model()` 接口

---

## 附录

### A. 版本兼容性

| 框架 | 最低版本 | 推荐版本 | 已测试版本 |
|------|---------|---------|-----------|
| Python | 3.12 | 3.12 | 3.12, 3.13 |
| LangChain | 1.0.1 | 1.0.1+ | 1.0.1 |
| LangGraph | 1.0.1 | 1.0.1+ | 1.0.1 |
| Textual | 6.3.0 | 6.3.0+ | 6.3.0 |

### B. 性能基准

| 操作 | 时间 | 说明 |
|------|------|------|
| 应用启动 | ~2-5s | 包括模型初始化、MCP 加载 |
| 简单查询 | ~1-3s | 如 "查看文件" |
| 工具调用 | ~0.5-2s | 单个工具执行 |
| UI 渲染 | 16ms | 60 FPS |

### C. 许可证总结

所有依赖均为宽松开源许可证：
- MIT: LangChain, LangGraph, Textual, Rich, Pydantic
- BSD: Jinja2, httpx
- ISC: pexpect

DeerCode 本身: MIT 许可证

### D. 进一步学习资源

**LangChain/LangGraph**:
- [官方文档](https://python.langchain.com/)
- [LangGraph 教程](https://langchain-ai.github.io/langgraph/tutorials/)
- [示例项目](https://github.com/langchain-ai/langgraph/tree/main/examples)

**Textual**:
- [官方文档](https://textual.textualize.io/)
- [Widget 画廊](https://textual.textualize.io/widget_gallery/)
- [示例应用](https://github.com/Textualize/textual/tree/main/examples)

**Pydantic**:
- [官方文档](https://docs.pydantic.dev/)
- [验证器](https://docs.pydantic.dev/latest/concepts/validators/)
- [设置管理](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
