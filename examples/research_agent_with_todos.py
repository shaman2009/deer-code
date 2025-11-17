"""
Example demonstrating research_agent with TodoListMiddleware.

This example shows how the research agent now has built-in todo list
capabilities for tracking complex multi-step research tasks.
"""

import asyncio
import os

from langchain.messages import HumanMessage

from deer_code.agents.research_agent import create_research_agent


async def main():
    """Run a research task that demonstrates todo list functionality."""

    # Ensure API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("⚠️  TAVILY_API_KEY not set. Using placeholder.")
        os.environ["TAVILY_API_KEY"] = "test_key"

    # Create research agent with TodoListMiddleware
    agent = create_research_agent()
    print("✓ Research agent created with TodoListMiddleware\n")

    # Example research task
    task = """
    Research the latest developments in LangChain 1.0 middleware architecture.
    Please break this down into steps and use the write_todos tool to track your progress.
    """

    print(f"Task: {task.strip()}\n")
    print("=" * 60)

    # Run the agent
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=task)]
    })

    # Display results
    print("\n" + "=" * 60)
    print("\nAgent Response:")
    print("-" * 60)
    if result.get("messages"):
        last_message = result["messages"][-1]
        print(last_message.content)

    # Display todos if available
    if "todos" in result:
        print("\n" + "=" * 60)
        print("\nTodo List:")
        print("-" * 60)
        for i, todo in enumerate(result["todos"], 1):
            print(f"{i}. {todo}")

    print("\n✓ Task completed!")


if __name__ == "__main__":
    asyncio.run(main())
