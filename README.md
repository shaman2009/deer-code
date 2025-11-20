# 🦌 deer-code

A minimalist yet powerful AI coding agent that helps developers learn and build intelligent coding assistants. Built with Python and featuring a VSCode-like TUI interface, deer-code demonstrates how to create AI agents that can reason, plan, and act on code.

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
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: minimal # `minimal`, `low`, `medium` or `high`
  # Alternatively, uncomment the following section to use Doubao's model:
  #
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
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
    # your_mcp_server:
    #   ...
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

- [x] **Beginner-friendly**: Simple project structure designed for learning
- [x] **VSCode-like TUI**: Intuitive terminal user interface
- [x] **OpenAI Compatible**: Works with any OpenAI-compatible API
- [x] **ReAct Framework**: Reasoning, planning, and acting capabilities
- [x] **Multi-turn Conversations**: Maintains context across interactions
- [x] **Task Planning**: Built-in todo system for project management
- [x] **Code Generation**: AI-powered code creation and editing
- [x] **Code Search**: Intelligent code location and search
- [x] **Bash Execution**: Bash command execution
- [x] **MCP Integration**: Bring your own MCP tools to enhance the agent's capabilities

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

DeerCode 使用 Python 编写，设计简单易用。按照以下步骤开始使用：

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
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: minimal # `minimal`, `low`, `medium` 或 `high`
  # 或者，取消以下部分注释以使用豆包模型：
  #
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
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
    # your_mcp_server:
    #   ...
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

- [x] **新手友好**：专为学习设计的简单项目结构
- [x] **类 VSCode 终端界面**：直观的终端用户界面（TUI）
- [x] **OpenAI 兼容**：支持任何 OpenAI 兼容的 API
- [x] **ReAct 框架**：具备推理、规划和行动能力
- [x] **多轮对话**：在交互过程中保持上下文
- [x] **任务规划**：内置待办事项系统用于项目管理
- [x] **代码生成**：AI 驱动的代码创建和编辑
- [x] **代码搜索**：智能代码定位和搜索
- [x] **Bash 执行**：Bash 命令执行
- [x] **MCP 集成**：引入你自己的 MCP 工具来增强智能体能力

## 🤝 贡献

欢迎贡献！欢迎在 GitHub 上提交 Issue 和 Pull Request。

## 📄 许可证

本项目开源，采用 [MIT 许可证](./LICENSE)。

## 🙏 致谢

- 灵感来源于 [Anthropic 的 Claude Code](https://github.com/anthropics/claude-code)
- 使用 [Textual](https://github.com/Textualize/textual) 构建终端界面
- 由 [LangGraph](https://github.com/langchain-ai/langgraph) 提供智能体编排能力

**[🔝 返回顶部](#-deer-code)** | **[📖 View English Version](#english)**
