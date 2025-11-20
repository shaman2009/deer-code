"""Tests for agents/state.py module."""

import pytest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from deer_code.agents.state import CodingAgentState
from deer_code.tools.todo.types import TodoItem, TodoStatus, TodoPriority


@pytest.mark.unit
class TestCodingAgentState:
    """Tests for CodingAgentState class."""

    def test_state_with_messages_only(self):
        """Test CodingAgentState with messages."""
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]

        # CodingAgentState is a TypedDict, so we use it as a type annotation
        # and work with dicts
        state: CodingAgentState = {"messages": messages}

        assert "messages" in state
        assert len(state["messages"]) == 2
        assert state["messages"][0].content == "Hello"
        assert state["messages"][1].content == "Hi there!"

    def test_state_with_todos_only(self):
        """Test CodingAgentState with todos."""
        todos = [
            TodoItem(id=1, title="Task 1"),
            TodoItem(id=2, title="Task 2", priority=TodoPriority.high),
        ]

        state: CodingAgentState = {"todos": todos}

        assert "todos" in state
        assert len(state["todos"]) == 2
        assert state["todos"][0].title == "Task 1"
        assert state["todos"][1].priority == TodoPriority.high

    def test_state_with_messages_and_todos(self):
        """Test CodingAgentState with both messages and todos."""
        messages = [HumanMessage(content="Test message")]
        todos = [TodoItem(id=1, title="Test task")]

        state: CodingAgentState = {
            "messages": messages,
            "todos": todos,
        }

        assert "messages" in state
        assert "todos" in state
        assert len(state["messages"]) == 1
        assert len(state["todos"]) == 1

    def test_state_todos_field_structure(self):
        """Test that todos field accepts TodoItem objects with various properties."""
        todo1 = TodoItem(id=0, title="First task")
        todo2 = TodoItem(
            id=1,
            title="Second task",
            priority=TodoPriority.high,
            status=TodoStatus.in_progress,
        )

        state: CodingAgentState = {"todos": [todo1, todo2]}

        assert len(state["todos"]) == 2
        assert state["todos"][0].id == 0
        assert state["todos"][0].title == "First task"
        assert state["todos"][1].priority == TodoPriority.high
        assert state["todos"][1].status == TodoStatus.in_progress

    def test_state_messages_field_accepts_various_types(self):
        """Test that messages field accepts different message types."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="User input"),
            AIMessage(content="AI response"),
        ]

        state: CodingAgentState = {"messages": messages}

        assert len(state["messages"]) == 3
        assert isinstance(state["messages"][0], SystemMessage)
        assert isinstance(state["messages"][1], HumanMessage)
        assert isinstance(state["messages"][2], AIMessage)

    def test_state_is_dict_like(self):
        """Test that state behaves like a dictionary."""
        state: CodingAgentState = {
            "messages": [HumanMessage(content="Test")],
            "todos": [TodoItem(id=0, title="Task")],
        }

        # Test dict-like access
        assert "messages" in state
        assert "todos" in state

        # Test getting values
        assert isinstance(state["messages"], list)
        assert isinstance(state["todos"], list)

    def test_state_extends_messages_state(self):
        """Test that CodingAgentState has both MessagesState and todos fields."""
        # CodingAgentState should be compatible with MessagesState structure
        state: CodingAgentState = {
            "messages": [HumanMessage(content="Test")],
            "todos": [TodoItem(id=0, title="Task")],
        }

        # Should have messages field from MessagesState
        assert "messages" in state
        # Should have additional todos field
        assert "todos" in state

    def test_state_update_messages(self):
        """Test updating messages in state."""
        state: CodingAgentState = {"messages": [HumanMessage(content="First")]}

        # Add a new message
        state["messages"] = state["messages"] + [AIMessage(content="Second")]

        assert len(state["messages"]) == 2
        assert state["messages"][1].content == "Second"

    def test_state_update_todos(self):
        """Test updating todos in state."""
        state: CodingAgentState = {
            "messages": [],
            "todos": [TodoItem(id=0, title="Original")],
        }

        # Add a new todo
        state["todos"] = state["todos"] + [TodoItem(id=1, title="New")]

        assert len(state["todos"]) == 2
        assert state["todos"][1].title == "New"

    def test_empty_state_structure(self):
        """Test creating an empty state."""
        state: CodingAgentState = {}

        # Empty state should be a valid dict
        assert isinstance(state, dict)
        assert len(state) == 0

    def test_state_with_empty_lists(self):
        """Test state with empty messages and todos lists."""
        state: CodingAgentState = {
            "messages": [],
            "todos": [],
        }

        assert state["messages"] == []
        assert state["todos"] == []
