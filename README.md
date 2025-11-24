# 🦌 deer-code

A minimalist yet powerful AI coding agent that helps developers learn and build intelligent coding assistants. Built with Python and featuring a VSCode-like TUI interface, deer-code demonstrates the ReAct framework (Reasoning, Acting, Acting) using LangGraph for agent orchestration and Textual for the terminal UI.

<img width="2764" height="1988" alt="Screenshot" src="https://github.com/user-attachments/assets/3a86b15f-d616-4b56-80c9-63fccb4d8f28" />

**Brought to you by** [🦌 The DeerFlow Team](https://github.com/bytedance/deer-flow). *Inspired by Anthropic's Claude Code.*

---

[English](#english) | [中文](#中文)

---

## English

## 🚀 Quick Start

DeerCode is written in Python and designed to be easy to set up and use. Follow these steps to get started:

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.12 or higher
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management)
- [langgraph-cli](https://docs.langchain.com/langsmith/cli) (for development and debugging)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shaman2009/deer-code.git
   cd deer-code
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

### Configuration

1. **Copy the configuration template:**
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **Edit `config.yaml` with your settings:**

```yaml
models:
  chat_model:
    # OpenAI-compatible API (default)
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: minimal # `minimal`, `low`, `medium`, or `high`

  # Alternatively, use DeepSeek:
  # chat_model:
  #   type: deepseek
  #   model: 'deepseek-chat'
  #   api_base: 'https://api.deepseek.com/v1'
  #   api_key: $DEEPSEEK_API_KEY
  #   temperature: 0
  #   max_tokens: 8192

  # Or use Doubao:
  # chat_model:
  #   type: doubao
  #   model: 'doubao-seed-1-6-250615'
  #   api_base: 'https://ark.cn-beijing.volces.com/api/v3'
  #   api_key: $ARK_API_KEY
  #   temperature: 0
  #   max_tokens: 8192
  #   extra_body:
  #     thinking:
  #       type: auto

tools:
  # Optional: Tavily API for web research (ResearchAgent)
  tavily:
    api_key: $TAVILY_API_KEY

  # Optional: Perplexity API for AI-powered search (ResearchAgent)
  perplexity:
    api_key: $PERPLEXITY_API_KEY
    model: 'sonar'  # Options: 'sonar' (faster, cheaper) or 'sonar-pro' (more detailed)

  # Optional: MCP servers for additional capabilities
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
    # your_mcp_server:
    #   transport: 'streamable_http'
    #   url: 'https://your-server.com/mcp'
```

### Running the Application

**Start deer-code:**
```bash
uv run -m deer_code.main "/path/to/your/developing/project"
```

**Development mode (with LangGraph CLI):**

First, change `env.PROJECT_ROOT` in `langgraph.json` file.

Then, run the following command:
```bash
make dev
```

Now, open the browser and navigate to `https://agentchat.vercel.app/?apiUrl=http://localhost:2024&assistantId=coding_agent` to chat with the agent.

## 🌟 Features

### Core Capabilities
- [x] **Beginner-friendly**: Simple project structure designed for learning AI agent development
- [x] **VSCode-like TUI**: Intuitive terminal user interface with split-panel layout
- [x] **Multi-Model Support**: Compatible with OpenAI, DeepSeek, Doubao, and any OpenAI-compatible API
- [x] **ReAct Framework**: Advanced reasoning, planning, and acting capabilities powered by LangGraph
- [x] **Multi-turn Conversations**: Maintains context across interactions with persistent state management

### Agent System
- [x] **Dual-Agent Architecture**:
  - **CodingAgent**: Primary agent for code analysis, editing, and execution
  - **ResearchAgent**: Specialized agent for web research using Perplexity and Tavily search
- [x] **Task Planning**: Built-in todo system with TodoListMiddleware for project management
- [x] **Agent Middleware**: Extensible middleware system for adding capabilities

### Developer Tools
- [x] **Code Editor**: Full-featured text editor with view, create, replace, and insert operations
- [x] **File System Tools**:
  - `grep`: Ripgrep-powered code search with context lines
  - `ls`: Directory listing with glob pattern matching
  - `tree`: Recursive directory tree visualization (max depth 3)
- [x] **Bash Execution**: Persistent bash terminal sessions with state preservation
- [x] **Web Search**: Dual search capabilities for comprehensive research
  - **Perplexity Search**: AI-powered search with synthesized answers and citations
  - **Tavily Search**: Raw web search results with relevance scores for deep analysis
- [x] **MCP Integration**: Bring your own MCP tools to enhance the agent's capabilities

### Configuration & Extensibility
- [x] **Flexible Configuration**: YAML-based config with environment variable expansion
- [x] **Custom System Prompts**: Jinja2 template system for prompt customization
- [x] **Ignore Patterns**: Smart filtering with 77+ default ignore patterns
- [x] **Testing Support**: pytest-based test suite with coverage reporting

## 🏗️ Architecture

deer-code follows a clean, dual-layer architecture:

```
User Interaction (TUI Layer)
    ↓
ConsoleApp (Textual TUI)
    ↓
Agents (LangGraph State Graphs)
    ├── CodingAgent → bash, text_editor, grep, ls, tree, todo_write, MCP tools
    └── ResearchAgent → perplexity_search, tavily_search, write_todos (via TodoListMiddleware), MCP tools
```

### Key Technologies

- **LangGraph** - Agent orchestration and state management
- **LangChain** - Tool management and model integration
- **Textual** - Terminal UI framework
- **pexpect** - Persistent bash terminal sessions
- **Tavily** - Web search capabilities
- **Rich** - Terminal formatting

### Directory Structure

```
deer-code/
├── src/deer_code/
│   ├── agents/          # CodingAgent and ResearchAgent implementations
│   ├── cli/             # Textual TUI components (app, theme, widgets)
│   ├── config/          # YAML configuration with env var expansion
│   ├── models/          # Multi-provider LLM initialization
│   ├── prompts/         # Jinja2 system prompt templates
│   ├── tools/           # Tool implementations (edit, fs, mcp, search, terminal, todo)
│   └── main.py          # Application entry point
├── tests/               # pytest test suite
├── docs/                # Documentation (Chinese)
└── pyproject.toml       # Project metadata and dependencies
```

For detailed architecture information, see [CLAUDE.md](./CLAUDE.md).

## 🤝 Contributing

We welcome contributions! Feel free to submit issues and pull requests on GitHub.

## 📄 License

This project is open source and available under the [MIT License](./LICENSE).

## 🙏 Acknowledgments

- Inspired by [Anthropic's Claude Code](https://github.com/anthropics/claude-code)
- Built with [Textual](https://github.com/Textualize/textual) for the TUI interface
- Powered by [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration

**[🔝 Back to Top](#-deer-code)** | **[📖 查看中文版](#中文)**

---

## 中文

## 🚀 快速开始

DeerCode 使用 Python 编写，设计简单易用。它展示了如何使用 LangGraph 进行智能体编排，以及使用 Textual 构建终端 UI 来实现 ReAct 框架（推理、行动、行动）。按照以下步骤开始使用：

### 前置要求

- [Python](https://www.python.org/downloads/) 3.12 或更高版本
- [uv](https://docs.astral.sh/uv/) （推荐用于依赖管理）
- [langgraph-cli](https://docs.langchain.com/langsmith/cli) （用于开发和调试）

### 安装

1. **克隆仓库：**
   ```bash
   git clone https://github.com/shaman2009/deer-code.git
   cd deer-code
   ```

2. **安装依赖：**
   ```bash
   make install
   ```

### 配置

1. **复制配置模板：**
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **编辑 `config.yaml` 文件，填入你的配置：**

```yaml
models:
  chat_model:
    # OpenAI 兼容 API（默认）
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: minimal # `minimal`, `low`, `medium` 或 `high`

  # 或者，使用 DeepSeek：
  # chat_model:
  #   type: deepseek
  #   model: 'deepseek-chat'
  #   api_base: 'https://api.deepseek.com/v1'
  #   api_key: $DEEPSEEK_API_KEY
  #   temperature: 0
  #   max_tokens: 8192

  # 或者，使用豆包：
  # chat_model:
  #   type: doubao
  #   model: 'doubao-seed-1-6-250615'
  #   api_base: 'https://ark.cn-beijing.volces.com/api/v3'
  #   api_key: $ARK_API_KEY
  #   temperature: 0
  #   max_tokens: 8192
  #   extra_body:
  #     thinking:
  #       type: auto

tools:
  # 可选：Tavily API 用于网络研究（ResearchAgent）
  tavily:
    api_key: $TAVILY_API_KEY

  # 可选：Perplexity API 用于 AI 驱动的搜索（ResearchAgent）
  perplexity:
    api_key: $PERPLEXITY_API_KEY
    model: 'sonar'  # 选项：'sonar'（更快、更便宜）或 'sonar-pro'（更详细）

  # 可选：MCP 服务器用于扩展功能
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
    # your_mcp_server:
    #   transport: 'streamable_http'
    #   url: 'https://your-server.com/mcp'
```

### 运行应用

**启动 deer-code：**
```bash
uv run -m deer_code.main "/path/to/your/developing/project"
```

**开发模式（使用 LangGraph CLI）：**

首先，修改 `langgraph.json` 文件中的 `env.PROJECT_ROOT`。

然后运行以下命令：
```bash
make dev
```

现在，打开浏览器访问 `https://agentchat.vercel.app/?apiUrl=http://localhost:2024&assistantId=coding_agent` 与智能体对话。

## 🌟 特性

### 核心能力
- [x] **新手友好**：专为学习 AI 智能体开发设计的简单项目结构
- [x] **类 VSCode 终端界面**：直观的分屏布局终端用户界面（TUI）
- [x] **多模型支持**：兼容 OpenAI、DeepSeek、豆包以及任何 OpenAI 兼容的 API
- [x] **ReAct 框架**：由 LangGraph 驱动的高级推理、规划和行动能力
- [x] **多轮对话**：通过持久化状态管理在交互过程中保持上下文

### 智能体系统
- [x] **双智能体架构**：
  - **CodingAgent**：用于代码分析、编辑和执行的主要智能体
  - **ResearchAgent**：使用 Perplexity 和 Tavily 搜索进行网络研究的专用智能体
- [x] **任务规划**：使用 TodoListMiddleware 的内置待办事项系统用于项目管理
- [x] **智能体中间件**：用于添加功能的可扩展中间件系统

### 开发者工具
- [x] **代码编辑器**：功能完整的文本编辑器，支持查看、创建、替换和插入操作
- [x] **文件系统工具**：
  - `grep`：基于 Ripgrep 的代码搜索，支持上下文行
  - `ls`：支持 glob 模式匹配的目录列表
  - `tree`：递归目录树可视化（最大深度 3）
- [x] **Bash 执行**：持久化 bash 终端会话，保留状态
- [x] **网络搜索**：双重搜索能力，实现全面研究
  - **Perplexity 搜索**：AI 驱动的搜索，提供综合答案和引用
  - **Tavily 搜索**：原始网络搜索结果，带相关性评分，用于深度分析
- [x] **MCP 集成**：引入你自己的 MCP 工具来增强智能体能力

### 配置与扩展性
- [x] **灵活配置**：基于 YAML 的配置，支持环境变量展开
- [x] **自定义系统提示**：Jinja2 模板系统用于提示词定制
- [x] **忽略模式**：智能过滤，包含 77+ 默认忽略模式
- [x] **测试支持**：基于 pytest 的测试套件，支持覆盖率报告

## 🏗️ 架构

deer-code 遵循简洁的双层架构：

```
用户交互层（TUI 层）
    ↓
ConsoleApp（Textual TUI）
    ↓
智能体层（LangGraph 状态图）
    ├── CodingAgent → bash, text_editor, grep, ls, tree, todo_write, MCP 工具
    └── ResearchAgent → perplexity_search, tavily_search, write_todos（通过 TodoListMiddleware）, MCP 工具
```

### 关键技术

- **LangGraph** - 智能体编排和状态管理
- **LangChain** - 工具管理和模型集成
- **Textual** - 终端 UI 框架
- **pexpect** - 持久化 bash 终端会话
- **Tavily** - 网络搜索能力
- **Rich** - 终端格式化

### 目录结构

```
deer-code/
├── src/deer_code/
│   ├── agents/          # CodingAgent 和 ResearchAgent 实现
│   ├── cli/             # Textual TUI 组件（app, theme, widgets）
│   ├── config/          # 支持环境变量展开的 YAML 配置
│   ├── models/          # 多提供商 LLM 初始化
│   ├── prompts/         # Jinja2 系统提示模板
│   ├── tools/           # 工具实现（edit, fs, mcp, search, terminal, todo）
│   └── main.py          # 应用入口点
├── tests/               # pytest 测试套件
├── docs/                # 文档（中文）
└── pyproject.toml       # 项目元数据和依赖
```

详细的架构信息请参阅 [CLAUDE.md](./CLAUDE.md)。

## 🤝 贡献

欢迎贡献！欢迎在 GitHub 上提交 Issue 和 Pull Request。

## 📄 许可证

本项目开源，采用 [MIT 许可证](./LICENSE)。

## 🙏 致谢

- 灵感来源于 [Anthropic 的 Claude Code](https://github.com/anthropics/claude-code)
- 使用 [Textual](https://github.com/Textualize/textual) 构建终端界面
- 由 [LangGraph](https://github.com/langchain-ai/langgraph) 提供智能体编排能力

**[🔝 返回顶部](#-deer-code)** | **[📖 View English Version](#english)**
