from langchain.messages import AIMessage
from langchain.tools import ToolRuntime

from deer_code.tools.todo.types import TodoStatus


def generate_reminders(
    runtime: ToolRuntime, force: bool = False, tool_name: str = ""
) -> str:
    """Generate intelligent reminders based on context.

    Args:
        runtime: The tool runtime to access state.
        force: Whether to force showing reminders regardless of context.
        tool_name: The name of the tool calling this function.

    Returns:
        A reminder string if applicable, empty string otherwise.
    """
    todos = runtime.state.get("todos")
    if todos is None or len(todos) == 0:
        return ""

    unfinished_todos = []
    for todo in todos:
        if (
            todo.status != TodoStatus.completed
            and todo.status != TodoStatus.cancelled
        ):
            unfinished_todos.append(todo)

    if len(unfinished_todos) == 0:
        return ""

    # Only show reminders in specific contexts to avoid repetition
    if not force:
        # Check if this is likely a final action before responding to user
        # Show reminders after edit operations or when explicitly forced
        show_after_tools = ["text_editor", "bash"]
        if tool_name not in show_after_tools:
            # Don't show reminders for read-only tools (grep, ls, tree)
            return ""

        # Check message history to avoid duplicate reminders
        messages = runtime.state.get("messages", [])
        if len(messages) > 0:
            # Look at recent messages to see if we already showed reminders
            recent_tool_messages = [
                m for m in messages[-5:] if hasattr(m, "tool_call_id")
            ]
            for msg in recent_tool_messages:
                if "todo" in str(msg.content).lower() and "not completed" in str(
                    msg.content
                ).lower():
                    # Already showed reminder recently, skip
                    return ""

    reminders = []
    reminders.append(
        f"- {len(unfinished_todos)} todo{' is' if len(unfinished_todos) == 1 else 's are'} not completed. Before you present the final result to the user, **make sure** all the todos are completed."
    )
    reminders.append(
        "- Update the TODO list using the `write_todos` tool to track progress."
    )
    return "\n\nIMPORTANT:\n" + "\n".join(reminders)
