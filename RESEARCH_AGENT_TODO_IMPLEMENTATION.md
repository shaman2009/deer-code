# Research Agent TODO 功能实现总结

## 概述

为 `research_agent` 添加了 TODO 跟踪功能，使其能够管理复杂的多步骤研究任务。实现基于 LangGraph 框架，与 `coding_agent` 的 TODO 功能保持一致。

## 实现的文件修改

### 1. `src/deer_code/agents/state.py`

**新增内容**：
```python
class ResearchAgentState(MessagesState):
    todos: list[TodoItem] = Field(default_factory=list)
```

**说明**：
- 创建了新的状态类 `ResearchAgentState`
- 继承自 LangGraph 的 `MessagesState`
- 添加 `todos` 字段用于存储任务列表
- 使用 `Field(default_factory=list)` 确保每个实例都有独立的空列表

---

### 2. `src/deer_code/agents/research_agent.py`

**修改内容**：

#### 导入部分：
```python
# 移除了 MessagesState 导入
from deer_code.tools import tavily_search_tool, todo_write_tool  # 添加 todo_write_tool
from .state import ResearchAgentState  # 添加新的状态类
```

#### create_research_agent 函数：
```python
tools=[
    tavily_search_tool,
    todo_write_tool,      # 新增
    *plugin_tools,
],
state_schema=ResearchAgentState,  # 从 MessagesState 改为 ResearchAgentState
```

**说明**：
- 添加 `todo_write_tool` 到工具列表
- 使用 `ResearchAgentState` 替代 `MessagesState`
- 保持与 coding_agent 一致的架构模式

---

### 3. `src/deer_code/prompts/templates/research_agent.md`

**新增章节**：

#### TODO Usage Guidelines

**何时使用 `todo_write`**：
1. **Multi-step research tasks** - 需要多次搜索或调查不同方面
2. **Comparative analysis** - 对比多个主题、产品或技术
3. **Deep research** - 从不同角度深入研究某个主题
4. **User provides multiple questions** - 用户一次提出多个研究问题
5. **User explicitly requests progress tracking** - 用户明确要求跟踪进度
6. **Complex synthesis** - 需要整合多个搜索结果

**何时不使用**：
1. **Single simple search** - 一次搜索就能回答的简单查询
2. **Quick fact-checking** - 简单的事实核查
3. **Clarification questions** - 需要向用户澄清细节时
4. **Trivial queries** - 少于 3 步就能完成的简单任务

#### TODO Best Practices

- **分解研究任务为搜索查询** - 每个 todo 代表一个具体的搜索或调查角度
- **实时更新进度** - 搜索前标记为 `in_progress`，完成后标记为 `completed`
- **清晰的标题** - 使用描述性标题如 "Search for Python 3.12 performance improvements"
- **策略性优先级** - 先进行基础搜索，再深入具体细节
- **完成所有任务** - 在给出最终总结前确保所有研究任务完成

---

### 4. `src/deer_code/agents/__init__.py`

**修改内容**：
```python
from .state import CodingAgentState, ResearchAgentState  # 添加 ResearchAgentState

__all__ = [
    "CodingAgentState",
    "ResearchAgentState",  # 导出新状态类
    "create_coding_agent",
    "create_research_agent",
]
```

---

## 技术实现细节

### 状态管理

**LangGraph 状态流**：
```
User Query → HumanMessage
    ↓
ResearchAgentState {
    messages: [HumanMessage, AIMessage, ToolMessage, ...]
    todos: [TodoItem, TodoItem, ...]
}
    ↓
Agent 决策 → 调用 todo_write_tool
    ↓
Command.update({
    "todos": updated_todos,
    "messages": [ToolMessage(...)]
})
    ↓
状态自动更新并流式返回
```

### TODO 工具工作原理

`todo_write_tool` 返回 `Command` 对象：
```python
Command(
    update={
        "todos": todos,              # 更新完整的 todo 列表
        "messages": [ToolMessage]    # 添加工具执行结果消息
    }
)
```

LangGraph 自动处理状态更新，并支持流式输出。

### 流式支持

使用 `astream()` 方法时：
```python
async for chunk in agent.astream(
    {"messages": [HumanMessage(content=query)]},
    stream_mode="updates",
):
    # chunk = {node_name: {"todos": [...], "messages": [...]}}
```

每次状态更新都会作为一个 chunk 返回，包括：
- **todos 更新** - 当 agent 调用 `todo_write` 时
- **messages 更新** - 每次消息添加时

---

## 使用示例

### 场景 1: 复杂研究（会使用 TODO）

```python
query = """
Research the following about Python 3.12:
1. What are the main performance improvements?
2. What new syntax features were added?
3. How does it compare to Python 3.11 in benchmarks?
"""

# Agent 会自动：
# 1. 创建 3 个 todo items
# 2. 逐个标记为 in_progress → completed
# 3. 整合所有搜索结果
# 4. 返回综合总结
```

预期的 TODO 列表：
```
⏳ [pending] Search for Python 3.12 performance improvements
⏳ [pending] Search for Python 3.12 new syntax features
⏳ [pending] Compare Python 3.12 vs 3.11 benchmarks
```

### 场景 2: 简单查询（不使用 TODO）

```python
query = "What is the latest version of Python?"

# Agent 会：
# 1. 直接搜索
# 2. 返回答案
# 3. 不创建 todos（因为只需一次搜索）
```

---

## 与 Coding Agent 的对比

| 特性 | Coding Agent | Research Agent |
|------|-------------|----------------|
| **状态类** | `CodingAgentState` | `ResearchAgentState` |
| **核心工具** | bash, text_editor, grep, etc. | tavily_search |
| **TODO 用途** | 代码任务分解与跟踪 | 研究任务分解与跟踪 |
| **TODO 粒度** | 代码编辑、测试、构建等 | 搜索查询、对比分析等 |
| **触发条件** | 复杂编码任务 | 多步骤研究任务 |

---

## 验证与测试

### 语法验证
所有修改的文件都已通过 Python 语法检查：
```bash
python3 -m py_compile src/deer_code/agents/state.py
python3 -m py_compile src/deer_code/agents/research_agent.py
python3 -m py_compile src/deer_code/agents/__init__.py
```

### 使用示例
参考 `research_agent_todo_example.py` 了解完整的使用示例。

---

## LangGraph 特性使用

### 已实现
- ✅ **状态管理** - 通过 `ResearchAgentState` 扩展状态模式
- ✅ **Command API** - 使用 `Command` 对象更新状态
- ✅ **流式输出** - 支持 `stream_mode="updates"` 实时获取状态变化

### 可扩展（未来）
- ⏸️ **Checkpointing** - 保存和恢复研究进度
- ⏸️ **Time Travel** - 回溯到之前的研究状态
- ⏸️ **Custom Reducers** - 自定义 todos 合并逻辑（当前使用默认覆盖）

---

## 设计原则

1. **简洁性** - 保持与 coding_agent 一致的简单架构
2. **可扩展性** - 易于添加新的状态字段或工具
3. **用户友好** - Agent 自动决定何时使用 TODO，无需用户明确指示
4. **流式优先** - 支持实时进度更新，提升用户体验

---

## 未来改进方向

1. **优先级管理** - 根据问题重要性自动设置 todo 优先级
2. **并行搜索** - 支持同时进行多个独立的搜索任务
3. **依赖关系** - 某些 todo 需要等待其他 todo 完成
4. **进度估算** - 估算每个研究任务的时间或复杂度
5. **结果缓存** - 避免重复搜索相同的内容

---

## 总结

本次实现为 `research_agent` 添加了完整的 TODO 跟踪功能：
- ✅ 创建了 `ResearchAgentState` 状态类
- ✅ 集成了 `todo_write_tool` 工具
- ✅ 添加了详细的使用指引和最佳实践
- ✅ 支持流式状态更新
- ✅ 保持了与 coding_agent 的架构一致性

实现简洁、可扩展，符合 LangGraph 的设计模式。
