#!/usr/bin/env python3
"""
Example: Using research_agent with TODO functionality

This example demonstrates how the research_agent uses the todo_write tool
to track multi-step research tasks.
"""
import asyncio
from langchain.messages import HumanMessage


async def research_agent_todo_example():
    """
    Example showing how research_agent handles complex research with todos.

    Note: This requires valid API keys in config.yaml:
    - OPENAI_API_KEY (or compatible LLM provider)
    - TAVILY_API_KEY
    """
    from deer_code.agents import create_research_agent

    # Create research agent (with TODO support)
    agent = create_research_agent()

    # Example 1: Multi-step research task
    # The agent should automatically use todo_write to track progress
    query = """
    Research the following about Python 3.12:
    1. What are the main performance improvements?
    2. What new syntax features were added?
    3. How does it compare to Python 3.11 in benchmarks?
    """

    print("=" * 60)
    print("Example: Complex research with multiple questions")
    print("=" * 60)
    print(f"\nQuery: {query}\n")

    # Stream the agent's responses
    async for chunk in agent.astream(
        {"messages": [HumanMessage(content=query)]},
        stream_mode="updates",
        config={"thread_id": "example_thread"},
    ):
        # Each chunk contains updates to the state
        for node_name, state_update in chunk.items():
            if "todos" in state_update:
                todos = state_update["todos"]
                print(f"\n📝 TODO Update ({len(todos)} items):")
                for todo in todos:
                    status_icon = {
                        "pending": "⏳",
                        "in_progress": "🔄",
                        "completed": "✅",
                        "cancelled": "❌",
                    }.get(todo.status, "❓")
                    print(f"  {status_icon} [{todo.status}] {todo.title}")

            if "messages" in state_update:
                for msg in state_update["messages"]:
                    if hasattr(msg, "content") and msg.content:
                        print(f"\n💬 {msg.__class__.__name__}:")
                        print(f"   {msg.content[:200]}...")

    print("\n" + "=" * 60)


async def simple_research_example():
    """
    Example showing a simple research query that doesn't need todos.
    """
    from deer_code.agents import create_research_agent

    agent = create_research_agent()

    # Simple query - agent should NOT use todo_write
    query = "What is the latest version of Python?"

    print("\n" + "=" * 60)
    print("Example: Simple query (no todos needed)")
    print("=" * 60)
    print(f"\nQuery: {query}\n")

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=query)]},
        config={"thread_id": "simple_thread"},
    )

    print(f"Answer: {result['messages'][-1].content}\n")
    print(f"Todos used: {len(result.get('todos', []))}")
    print("=" * 60)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║   Research Agent with TODO Tracking - Usage Examples      ║
╚════════════════════════════════════════════════════════════╝

This script demonstrates the research_agent's TODO functionality:

1. Complex Research: Agent automatically creates todos for multi-step tasks
2. Simple Research: Agent skips todos for straightforward queries

Features:
- Automatic task decomposition
- Real-time progress tracking
- Status updates (pending → in_progress → completed)
- Streaming support

""")

    # Run examples
    asyncio.run(research_agent_todo_example())
    asyncio.run(simple_research_example())
