# Research Agent 演进路线图

## 📊 当前能力分析

### 现有实现 (deer_code/agents/research_agent.py)

**核心组件：**
- 单一工具：`tavily_search_tool`（Tavily API）
- 状态管理：`MessagesState`（无自定义状态）
- 架构：简单的 ReAct agent（通过 `create_agent`）
- 提示词：基础的搜索-总结模式

**当前能力：**
1. ✅ 基础 Web 搜索（Tavily）
2. ✅ 搜索结果格式化
3. ✅ 简单的查询-响应模式
4. ✅ 可配置搜索深度（basic/advanced）
5. ✅ MCP 工具扩展支持

**主要限制：**
1. ❌ 无查询分解能力
2. ❌ 无多步推理机制
3. ❌ 单一搜索源（仅 Tavily）
4. ❌ 无引用管理和源验证
5. ❌ 无 PDF/文档分析
6. ❌ 无研究状态跟踪
7. ❌ 无反思和质量评估
8. ❌ 无结构化报告生成
9. ❌ 无人机协作机制

---

## 🌍 业界标准能力对比

### Deep Research Agent 核心能力矩阵

基于对 2025 年业界标准的研究（OpenAI Deep Research、Microsoft Researcher、Google ADK、各类开源实现），标准 Deep Research Agent 应具备：

| 能力分类 | 具体能力 | DeerCode 现状 | 业界标准 |
|---------|---------|--------------|---------|
| **查询处理** | 查询分解（Query Decomposition） | ❌ | ✅ 分解为 3-7 个子查询 |
| | 查询优化（Query Refinement） | ❌ | ✅ 基于结果迭代优化 |
| | 上下文保持（Context Retention） | ⚠️ 仅消息历史 | ✅ 专门状态管理 |
| **信息检索** | 多源搜索 | ❌ 仅 Tavily | ✅ Web+arXiv+Scholar+GitHub |
| | 多跳检索（Multi-hop Retrieval） | ❌ | ✅ 迭代式深度搜索 |
| | PDF/文档分析 | ❌ | ✅ 下载并分析 PDF |
| | 结果排序和过滤 | ⚠️ 依赖 Tavily | ✅ 自主相关性评分 |
| **推理与规划** | 多步推理（Multi-step Reasoning） | ❌ | ✅ 动态推理链 |
| | 自适应规划（Adaptive Planning） | ❌ | ✅ 长期规划+回溯 |
| | 反思机制（Reflection） | ❌ | ✅ 质量评估+继续决策 |
| **质量保证** | 引用管理（Citation Management） | ❌ | ✅ 自动引用+可验证链接 |
| | 事实核查（Fact-Checking） | ❌ | ✅ 多源交叉验证 |
| | 源可信度评分 | ❌ | ✅ 可信度打分 |
| | 幻觉检测 | ❌ | ✅ RAG + 源约束 |
| **输出生成** | 结构化报告 | ❌ | ✅ Markdown 报告+章节 |
| | 引用追踪 | ❌ | ✅ 可点击源链接 |
| | 多语言支持 | ⚠️ 依赖模型 | ✅ 明确多语言 |
| **协作与监督** | 人机协作（Human-in-the-loop） | ❌ | ✅ Checkpoint 机制 |
| | 中间结果展示 | ⚠️ 工具调用可见 | ✅ 结构化进度报告 |
| | 可解释性 | ⚠️ 基础 | ✅ 推理路径可视化 |
| **扩展性** | 多智能体架构 | ❌ 单一 Agent | ✅ Master+专门 Agents |
| | 工具生态系统 | ✅ MCP 支持 | ✅ MCP + 专门工具 |
| | 自定义检索器 | ❌ | ✅ 可插拔检索器 |

**综合评分：** DeerCode Research Agent 约实现业界标准的 **15-20%** 能力

---

## 🎯 演进路线图

### 阶段一：核心能力增强（1-2 周）🔥 优先级：高

**目标：** 实现基础的多步研究能力

#### 1.1 状态管理升级
```python
# 新建：src/deer_code/agents/research_state.py
class ResearchAgentState(MessagesState):
    """Research agent state with tracking."""

    # 研究状态
    main_query: str  # 主查询
    sub_queries: list[dict]  # 子查询列表 [{"query": str, "status": str, "results": list}]

    # 检索历史
    search_history: list[dict]  # 所有搜索记录
    retrieved_sources: list[dict]  # 源列表 [{"url": str, "title": str, "relevance": float}]

    # 研究进度
    research_depth: int = 0  # 当前深度（0-3）
    max_depth: int = 3  # 最大深度

    # 质量控制
    confidence_score: float = 0.0  # 结果置信度
    needs_more_info: bool = True  # 是否需要更多信息
```

**影响文件：**
- `src/deer_code/agents/research_agent.py` - 更新为使用 `ResearchAgentState`
- `src/deer_code/agents/state.py` - 导出新状态类

#### 1.2 查询分解工具
```python
# 新建：src/deer_code/tools/research/query_decomposition.py
@tool("decompose_query", parse_docstring=True)
def decompose_query_tool(runtime: ToolRuntime, main_query: str, num_sub_queries: int = 5):
    """
    将复杂查询分解为多个子查询以进行深度研究。

    Args:
        runtime: Agent runtime context
        main_query: 主研究问题
        num_sub_queries: 生成的子查询数量（3-7）

    Returns:
        JSON 格式的子查询列表，包括每个子查询的搜索策略
    """
    # 使用 LLM 分解查询
    # 返回结构化的子查询计划
```

**影响文件：**
- 新建 `src/deer_code/tools/research/` 目录
- 新建 `src/deer_code/tools/research/query_decomposition.py`
- 新建 `src/deer_code/tools/research/__init__.py`

#### 1.3 反思与评估工具
```python
# 新建：src/deer_code/tools/research/reflection.py
@tool("evaluate_research_quality", parse_docstring=True)
def evaluate_research_quality_tool(
    runtime: ToolRuntime,
    gathered_info: str,
    original_query: str
) -> str:
    """
    评估当前收集信息的质量和完整性。

    Args:
        runtime: Agent runtime
        gathered_info: 已收集的信息摘要
        original_query: 原始查询

    Returns:
        评估报告，包括置信度分数、缺失信息、是否需要继续搜索
    """
```

**影响文件：**
- 新建 `src/deer_code/tools/research/reflection.py`

#### 1.4 提示词升级
更新 `src/deer_code/prompts/templates/research_agent.md`：

**新增章节：**
- 多步研究策略（Query Decomposition → Search → Evaluate → Continue/Stop）
- 反思机制指导（何时停止、何时深入）
- 状态管理说明（如何使用 sub_queries、search_history）

**影响文件：**
- `src/deer_code/prompts/templates/research_agent.md`

#### 1.5 LangGraph 工作流升级
```python
# 修改：src/deer_code/agents/research_agent.py
def create_research_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """创建支持多步推理的研究 agent。"""

    # 定义节点
    def should_continue(state: ResearchAgentState):
        """决定是否继续研究。"""
        if state.research_depth >= state.max_depth:
            return "generate_report"
        if not state.needs_more_info:
            return "generate_report"
        return "continue_research"

    # 构建图
    workflow = StateGraph(ResearchAgentState)
    workflow.add_node("decompose", decompose_query_node)
    workflow.add_node("search", search_node)
    workflow.add_node("reflect", reflection_node)
    workflow.add_node("generate_report", report_node)

    # 添加条件边
    workflow.add_conditional_edges("reflect", should_continue)

    return workflow.compile()
```

**影响文件：**
- `src/deer_code/agents/research_agent.py` - 重构为 StateGraph

**交付物：**
- ✅ 新的状态管理（ResearchAgentState）
- ✅ 查询分解工具
- ✅ 反思评估工具
- ✅ 多步工作流（LangGraph StateGraph）
- ✅ 更新的系统提示词

**测试要求：**
- 单元测试：查询分解、反思工具
- 集成测试：完整的多步研究流程
- 测试用例：复杂查询（如"比较 2025 年 top 3 个 LLM 的推理能力"）

---

### 阶段二：多源检索能力（2-3 周）🔥 优先级：高

**目标：** 支持多种数据源，实现真正的深度研究

#### 2.1 多源搜索工具集
```python
# 新建：src/deer_code/tools/research/sources/

# arxiv_search.py
@tool("arxiv_search", parse_docstring=True)
def arxiv_search_tool(runtime: ToolRuntime, query: str, max_results: int = 10):
    """搜索 arXiv 学术论文。"""
    # 使用 arxiv Python 包

# scholar_search.py
@tool("scholar_search", parse_docstring=True)
def scholar_search_tool(runtime: ToolRuntime, query: str, max_results: int = 10):
    """搜索 Google Scholar（通过 SerpAPI 或 scholarly）。"""

# github_search.py
@tool("github_search", parse_docstring=True)
def github_search_tool(runtime: ToolRuntime, query: str, search_type: str = "repositories"):
    """搜索 GitHub 仓库、代码、issues。"""
    # 使用 GitHub API

# pdf_analyzer.py
@tool("analyze_pdf", parse_docstring=True)
def analyze_pdf_tool(runtime: ToolRuntime, url: str, questions: list[str]):
    """下载并分析 PDF 文档。"""
    # 使用 PyPDF2 + LLM 分析
```

**新增依赖（pyproject.toml）：**
```toml
arxiv = "^2.1.0"
scholarly = "^1.7.11"  # 或 serpapi
PyGithub = "^2.1.1"
PyPDF2 = "^3.0.1"
pypdf = "^3.17.0"  # 更好的 PDF 解析
```

**影响文件：**
- 新建 `src/deer_code/tools/research/sources/` 目录
- 新建 4 个搜索工具文件
- 更新 `pyproject.toml`

#### 2.2 源聚合器
```python
# 新建：src/deer_code/tools/research/aggregator.py
@tool("aggregate_sources", parse_docstring=True)
def aggregate_sources_tool(
    runtime: ToolRuntime,
    query: str,
    source_types: list[str] = ["web", "arxiv", "scholar"]
):
    """
    并行从多个源搜索并聚合结果。

    Args:
        query: 搜索查询
        source_types: 要使用的源类型列表

    Returns:
        聚合并排序的结果，带有源标识和相关性分数
    """
    # 并行调用多个搜索工具
    # 聚合、去重、排序结果
```

**影响文件：**
- 新建 `src/deer_code/tools/research/aggregator.py`

#### 2.3 配置更新
```yaml
# config.example.yaml 新增
tools:
  research:
    sources:
      tavily:
        enabled: true
        api_key: $TAVILY_API_KEY
      arxiv:
        enabled: true
        max_results: 10
      scholar:
        enabled: true
        api_key: $SERPAPI_KEY  # 可选，使用 scholarly 可免费
      github:
        enabled: true
        token: $GITHUB_TOKEN  # 可选，提高 API 限制
    pdf_analysis:
      enabled: true
      max_file_size_mb: 50
      cache_dir: ".cache/pdfs"
```

**影响文件：**
- `config.example.yaml` - 新增 research 配置部分
- `src/deer_code/config/config.py` - 可能需要添加配置验证

#### 2.4 更新 Research Agent
```python
# 修改：src/deer_code/agents/research_agent.py
def create_research_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """创建支持多源检索的研究 agent。"""

    # 根据配置启用工具
    config = get_config_section(["tools", "research", "sources"])
    tools = []

    if config.get("tavily", {}).get("enabled"):
        tools.append(tavily_search_tool)
    if config.get("arxiv", {}).get("enabled"):
        tools.append(arxiv_search_tool)
    if config.get("scholar", {}).get("enabled"):
        tools.append(scholar_search_tool)
    if config.get("github", {}).get("enabled"):
        tools.append(github_search_tool)

    tools.extend([
        aggregate_sources_tool,
        analyze_pdf_tool,
        decompose_query_tool,
        evaluate_research_quality_tool,
        *plugin_tools,
    ])

    # ... 构建 StateGraph
```

**影响文件：**
- `src/deer_code/agents/research_agent.py`

**交付物：**
- ✅ 4 个新搜索源（arXiv, Scholar, GitHub, PDF）
- ✅ 源聚合器
- ✅ 配置化的源启用/禁用
- ✅ 更新的 research agent

**测试要求：**
- 单元测试：每个搜索工具
- 集成测试：多源聚合
- 测试用例：需要学术论文的查询、需要代码示例的查询

---

### 阶段三：引用与质量保证（1-2 周）🔥 优先级：中

**目标：** 确保研究结果可验证、可追溯

#### 3.1 引用管理系统
```python
# 新建：src/deer_code/tools/research/citation.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class Citation:
    """引用数据结构。"""
    id: str  # 引用 ID（如 [1], [2]）
    title: str
    url: str
    source_type: Literal["web", "arxiv", "scholar", "github", "pdf"]
    authors: list[str] = None
    publication_date: str = None
    relevance_score: float = 0.0
    excerpt: str = ""  # 引用的具体片段

@tool("add_citation", parse_docstring=True)
def add_citation_tool(runtime: ToolRuntime, citation_data: dict):
    """添加引用到当前研究状态。"""

@tool("generate_bibliography", parse_docstring=True)
def generate_bibliography_tool(runtime: ToolRuntime, format: str = "markdown"):
    """
    生成参考文献列表。

    Args:
        format: 输出格式（markdown, bibtex, apa）
    """
```

**影响文件：**
- 新建 `src/deer_code/tools/research/citation.py`

#### 3.2 事实核查工具
```python
# 新建：src/deer_code/tools/research/fact_check.py
@tool("verify_claim", parse_docstring=True)
def verify_claim_tool(
    runtime: ToolRuntime,
    claim: str,
    sources: list[str]
):
    """
    对比多个源验证声明的真实性。

    Args:
        claim: 需要验证的声明
        sources: 用于验证的源 URL 列表

    Returns:
        验证结果，包括：
        - 一致性分数
        - 支持/反对的源
        - 可信度评级
    """
    # 从多个源提取相关信息
    # 使用 LLM 对比和评估一致性
```

**影响文件：**
- 新建 `src/deer_code/tools/research/fact_check.py`

#### 3.3 源可信度评分
```python
# 新建：src/deer_code/tools/research/credibility.py
CREDIBILITY_SCORES = {
    # 学术源
    "arxiv.org": 0.95,
    "scholar.google.com": 0.90,
    "ieee.org": 0.95,
    "acm.org": 0.95,

    # 官方文档
    "github.com": 0.85,
    "docs.python.org": 0.95,

    # 新闻/媒体（需要更细粒度）
    "reuters.com": 0.85,
    "nature.com": 0.95,

    # 默认
    "default": 0.50,
}

@tool("evaluate_source_credibility", parse_docstring=True)
def evaluate_source_credibility_tool(runtime: ToolRuntime, url: str):
    """评估信息源的可信度。"""
    # 基于域名、HTTPS、内容类型等评分
```

**影响文件：**
- 新建 `src/deer_code/tools/research/credibility.py`

#### 3.4 更新状态管理
```python
# 修改：src/deer_code/agents/research_state.py
class ResearchAgentState(MessagesState):
    # ... 现有字段

    # 引用管理（新增）
    citations: list[Citation] = []  # 所有引用
    citation_map: dict[str, str] = {}  # {content_hash: citation_id}

    # 质量控制（新增）
    verified_claims: list[dict] = []  # 已验证的声明
    credibility_scores: dict[str, float] = {}  # {url: score}
```

**影响文件：**
- `src/deer_code/agents/research_state.py`

**交付物：**
- ✅ 引用管理系统（Citation 类 + 工具）
- ✅ 事实核查工具
- ✅ 源可信度评分
- ✅ 更新的状态管理

**测试要求：**
- 单元测试：引用格式化、可信度评分
- 集成测试：端到端引用追踪
- 测试用例：生成带完整引用的研究报告

---

### 阶段四：报告生成与人机协作（1-2 周）🔥 优先级：中

**目标：** 生成高质量的结构化报告，支持人类监督

#### 4.1 报告生成器
```python
# 新建：src/deer_code/tools/research/report.py
@tool("generate_research_report", parse_docstring=True)
def generate_research_report_tool(
    runtime: ToolRuntime,
    title: str,
    sections: list[str] = ["summary", "key_findings", "detailed_analysis", "conclusion"],
    include_citations: bool = True,
    output_format: str = "markdown"
):
    """
    生成结构化的研究报告。

    Args:
        title: 报告标题
        sections: 包含的章节
        include_citations: 是否包含参考文献
        output_format: 输出格式（markdown, html, pdf）

    Returns:
        格式化的研究报告，包含：
        - 执行摘要
        - 分章节的发现
        - 引用链接（可点击）
        - 参考文献列表
    """
    state: ResearchAgentState = runtime.state

    # 使用 Jinja2 模板
    template = """
# {{ title }}

*生成时间：{{ timestamp }}*
*主查询：{{ main_query }}*

## 执行摘要
{{ summary }}

{% for section in sections %}
## {{ section.title }}
{{ section.content }}

{% if section.citations %}
**参考资料：**
{% for cite in section.citations %}
- [{{ cite.id }}] {{ cite.title }} - [链接]({{ cite.url }})
{% endfor %}
{% endif %}
{% endfor %}

## 参考文献
{% for citation in all_citations %}
[{{ citation.id }}] {{ citation.title }}
作者：{{ citation.authors | join(", ") }}
来源：{{ citation.url }}
相关性：{{ citation.relevance_score | round(2) }}
{% endfor %}

---
*本报告由 DeerCode Research Agent 自动生成*
"""
```

**影响文件：**
- 新建 `src/deer_code/tools/research/report.py`
- 新建 `src/deer_code/tools/research/templates/report_template.md`

#### 4.2 人机协作机制（Checkpoint）
```python
# 修改：src/deer_code/agents/research_agent.py
from langgraph.checkpoint.memory import MemorySaver

def create_research_agent(
    plugin_tools: list[BaseTool] = [],
    enable_human_in_loop: bool = False,
    **kwargs
):
    """创建研究 agent，支持人机协作。"""

    # ... 构建工作流

    # 添加人类审批节点
    if enable_human_in_loop:
        def human_approval_node(state: ResearchAgentState):
            """等待人类批准继续研究。"""
            # 显示当前进度和发现
            # 等待用户输入：continue / stop / modify_query
            pass

        workflow.add_node("human_approval", human_approval_node)
        workflow.add_edge("reflect", "human_approval")
        workflow.add_conditional_edges(
            "human_approval",
            lambda s: s.user_decision,
            {
                "continue": "search",
                "stop": "generate_report",
                "modify": "decompose",
            }
        )

    # 使用 checkpoint 保存状态
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
```

**影响文件：**
- `src/deer_code/agents/research_agent.py`

#### 4.3 TUI 集成（可选）
如果要在 Textual TUI 中展示研究进度：

```python
# 新建：src/deer_code/cli/components/research/progress.py
class ResearchProgressView(Widget):
    """显示研究进度的 widget。"""

    def __init__(self):
        super().__init__()
        self.main_query = ""
        self.sub_queries = []
        self.current_depth = 0
        self.confidence = 0.0

    def render(self) -> RenderableType:
        # 显示：
        # - 主查询
        # - 子查询列表（状态：pending/searching/completed）
        # - 当前深度
        # - 置信度分数
        # - 已检索源数量
```

**影响文件：**
- 新建 `src/deer_code/cli/components/research/` 目录
- 新建 `src/deer_code/cli/components/research/progress.py`
- 修改 `src/deer_code/cli/app.py`（如果要集成）

**交付物：**
- ✅ 报告生成器（Jinja2 模板）
- ✅ 人机协作机制（Checkpoint）
- ✅ （可选）TUI 进度展示

**测试要求：**
- 单元测试：报告格式化
- 集成测试：完整的人机协作流程
- 测试用例：带人类干预的复杂研究任务

---

### 阶段五：高级特性（2-3 周）🔥 优先级：低

**目标：** 实现多智能体、可视化等高级能力

#### 5.1 多智能体架构
```python
# 新建：src/deer_code/agents/research/multi_agent.py
from langgraph.graph import StateGraph

class MasterPlannerAgent:
    """主规划 agent，分解任务并协调子 agents。"""

class SpecializedSearchAgent:
    """专门搜索 agent（Web/Academic/Code）。"""

class SynthesisAgent:
    """综合分析 agent，聚合多个 agent 的结果。"""

def create_multi_agent_research_system():
    """创建多智能体研究系统。"""
    workflow = StateGraph(ResearchAgentState)

    # 添加 agents 作为节点
    workflow.add_node("master_planner", MasterPlannerAgent())
    workflow.add_node("web_searcher", SpecializedSearchAgent("web"))
    workflow.add_node("academic_searcher", SpecializedSearchAgent("academic"))
    workflow.add_node("code_searcher", SpecializedSearchAgent("code"))
    workflow.add_node("synthesizer", SynthesisAgent())

    # 定义路由逻辑
    # ...
```

**影响文件：**
- 新建 `src/deer_code/agents/research/` 目录
- 新建 `src/deer_code/agents/research/multi_agent.py`

#### 5.2 可视化工具
```python
# 新建：src/deer_code/tools/research/visualization.py
@tool("generate_visualization", parse_docstring=True)
def generate_visualization_tool(
    runtime: ToolRuntime,
    data_type: str,  # "timeline", "comparison_table", "mind_map"
    data: dict
):
    """
    生成可视化图表。

    支持：
    - 时间线（事件发展）
    - 对比表格（多个选项对比）
    - 思维导图（概念关系）
    """
    # 使用 matplotlib/plotly 生成图表
    # 保存为图片或 HTML
```

**影响文件：**
- 新建 `src/deer_code/tools/research/visualization.py`

#### 5.3 NL2SQL（可选）
如果需要查询结构化数据：

```python
# 新建：src/deer_code/tools/research/nl2sql.py
@tool("query_database", parse_docstring=True)
def nl2sql_tool(
    runtime: ToolRuntime,
    natural_language_query: str,
    database_schema: dict
):
    """将自然语言转换为 SQL 并查询数据库。"""
    # 使用 LLM 生成 SQL
    # 安全执行（只读模式）
```

**影响文件：**
- 新建 `src/deer_code/tools/research/nl2sql.py`

#### 5.4 缓存与性能优化
```python
# 新建：src/deer_code/tools/research/cache.py
from functools import lru_cache
import hashlib
import pickle

class ResearchCache:
    """搜索结果缓存。"""

    def __init__(self, cache_dir: str = ".cache/research"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, query: str, source: str):
        """获取缓存的搜索结果。"""
        cache_key = hashlib.md5(f"{query}:{source}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            # 检查是否过期（例如 24 小时）
            if (time.time() - cache_file.stat().st_mtime) < 86400:
                return pickle.load(cache_file.open("rb"))
        return None

    def set(self, query: str, source: str, results: dict):
        """缓存搜索结果。"""
        # ...
```

**影响文件：**
- 新建 `src/deer_code/tools/research/cache.py`

**交付物：**
- ✅ 多智能体架构（可选）
- ✅ 可视化工具
- ✅ NL2SQL（可选）
- ✅ 结果缓存

**测试要求：**
- 性能测试：缓存命中率、响应时间
- 集成测试：多智能体协作

---

## 📅 完整时间线

| 阶段 | 功能 | 时间 | 优先级 | 团队规模 |
|-----|------|------|--------|---------|
| **阶段一** | 核心能力增强 | 1-2 周 | 🔥 高 | 1 人 |
| **阶段二** | 多源检索 | 2-3 周 | 🔥 高 | 1-2 人 |
| **阶段三** | 引用与质量 | 1-2 周 | ⚠️ 中 | 1 人 |
| **阶段四** | 报告与协作 | 1-2 周 | ⚠️ 中 | 1 人 |
| **阶段五** | 高级特性 | 2-3 周 | 💡 低 | 1-2 人 |
| **总计** | | **7-12 周** | | |

**最小可行产品（MVP）：** 阶段一 + 阶段二（3-5 周）
**生产就绪版本：** 阶段一 ~ 阶段四（5-9 周）
**完整版本：** 所有阶段（7-12 周）

---

## 🎯 成功指标

### 能力指标
- [ ] 能够分解复杂查询为 3-7 个子查询
- [ ] 支持至少 4 个不同的信息源（Web, arXiv, Scholar, GitHub）
- [ ] 生成带完整引用的结构化报告
- [ ] 置信度评分准确率 > 80%
- [ ] PDF 分析成功率 > 90%

### 质量指标
- [ ] 引用准确性：100%（无幻觉引用）
- [ ] 源可信度标注覆盖率 > 95%
- [ ] 多源一致性验证覆盖重要声明
- [ ] 报告结构清晰度：用户满意度 > 4/5

### 性能指标
- [ ] 简单查询响应时间 < 30 秒
- [ ] 复杂查询（深度=3）响应时间 < 5 分钟
- [ ] 缓存命中率 > 40%
- [ ] 并发搜索能力：至少 3 个源并行

### 用户体验指标
- [ ] 研究进度可视化
- [ ] 支持人机协作（checkpoint）
- [ ] 中间结果可查看
- [ ] 错误恢复能力（重试、回退）

---

## 🚧 技术债务与风险

### 已知风险
1. **API 成本：** 多源搜索会增加 API 调用（SerpAPI、Tavily 等）
   - **缓解措施：** 实现缓存、配置化源启用、使用免费 API（scholarly）

2. **PDF 处理复杂性：** 不同 PDF 格式、扫描文档
   - **缓解措施：** OCR 支持、错误处理、文件大小限制

3. **事实核查准确性：** LLM 本身可能产生误判
   - **缓解措施：** 多源交叉验证、人类监督、明确置信度

4. **性能问题：** 多步研究可能很慢
   - **缓解措施：** 并行搜索、流式输出、深度限制

### 技术债务
- 当前 `research_agent.py` 过于简单，需要完全重构
- 缺少统一的错误处理策略
- 配置管理需要增强（验证、默认值）
- 测试覆盖率需要提升（当前缺少 research agent 测试）

---

## 📚 参考资源

### 学术论文
1. **Deep Research Agents: A Systematic Examination And Roadmap** (arXiv:2506.18096)
2. **Deep Research: A Survey of Autonomous Research Agents** (arXiv:2508.12752)
3. **Enterprise Deep Research** (arXiv:2510.17797)
4. **Towards Robust Fact-Checking: A Multi-Agent System** (arXiv:2506.17878)

### 开源项目
- [OpenAI Deep Research](https://openai.com/index/introducing-deep-research/)
- [LangGraph Deep Research Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [Google ADK](https://cloud.google.com/blog/products/ai-machine-learning/build-a-deep-research-agent-with-google-adk)

### 工具与库
- **arxiv** - Python 客户端：https://github.com/lukasschwab/arxiv.py
- **scholarly** - Google Scholar 爬虫：https://scholarly.readthedocs.io/
- **PyPDF2** / **pypdf** - PDF 解析
- **SerpAPI** - 商业搜索 API（Google Scholar, Google Search）

---

## 🤝 贡献指南

### 阶段实施顺序建议
1. **先做阶段一：** 这是基础，所有后续功能都依赖它
2. **再做阶段二：** 多源能力是 "Deep Research" 的核心差异化
3. **然后阶段三/四：** 引用和报告是用户直接体验的部分
4. **最后阶段五：** 可选的高级特性，可根据用户反馈决定优先级

### 开发注意事项
- 每个阶段结束后进行用户测试
- 保持向后兼容（旧的简单 research agent 仍可用）
- 文档先行（每个新工具都要有清晰的 docstring）
- 测试驱动（先写测试，再实现功能）

---

**文档版本：** v1.0
**创建时间：** 2025-11-17
**最后更新：** 2025-11-17
**作者：** DeerCode Development Team
