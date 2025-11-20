"""Tests for tools/todo/types.py module."""

import pytest
from pydantic import ValidationError

from deer_code.tools.todo.types import TodoStatus, TodoPriority, TodoItem


@pytest.mark.unit
class TestTodoStatus:
    """Tests for TodoStatus enum."""

    def test_todo_status_values(self):
        """Test that TodoStatus has all expected values."""
        assert TodoStatus.pending == "pending"
        assert TodoStatus.in_progress == "in_progress"
        assert TodoStatus.completed == "completed"
        assert TodoStatus.cancelled == "cancelled"

    def test_todo_status_is_string_enum(self):
        """Test that TodoStatus is a string enum."""
        assert isinstance(TodoStatus.pending, str)
        assert isinstance(TodoStatus.in_progress, str)

    def test_todo_status_all_members(self):
        """Test that all expected status values exist."""
        expected_statuses = {"pending", "in_progress", "completed", "cancelled"}
        actual_statuses = {status.value for status in TodoStatus}
        assert actual_statuses == expected_statuses


@pytest.mark.unit
class TestTodoPriority:
    """Tests for TodoPriority enum."""

    def test_todo_priority_values(self):
        """Test that TodoPriority has all expected values."""
        assert TodoPriority.low == "low"
        assert TodoPriority.medium == "medium"
        assert TodoPriority.high == "high"

    def test_todo_priority_is_string_enum(self):
        """Test that TodoPriority is a string enum."""
        assert isinstance(TodoPriority.low, str)
        assert isinstance(TodoPriority.high, str)

    def test_todo_priority_all_members(self):
        """Test that all expected priority values exist."""
        expected_priorities = {"low", "medium", "high"}
        actual_priorities = {priority.value for priority in TodoPriority}
        assert actual_priorities == expected_priorities


@pytest.mark.unit
class TestTodoItem:
    """Tests for TodoItem model."""

    def test_todo_item_creation_minimal(self):
        """Test creating TodoItem with minimal required fields."""
        todo = TodoItem(id=0, title="Test task")

        assert todo.id == 0
        assert todo.title == "Test task"
        assert todo.priority == TodoPriority.medium  # Default
        assert todo.status == TodoStatus.pending  # Default

    def test_todo_item_creation_with_all_fields(self):
        """Test creating TodoItem with all fields specified."""
        todo = TodoItem(
            id=1,
            title="Important task",
            priority=TodoPriority.high,
            status=TodoStatus.in_progress,
        )

        assert todo.id == 1
        assert todo.title == "Important task"
        assert todo.priority == TodoPriority.high
        assert todo.status == TodoStatus.in_progress

    def test_todo_item_default_priority(self):
        """Test that default priority is medium."""
        todo = TodoItem(id=0, title="Task")
        assert todo.priority == TodoPriority.medium

    def test_todo_item_default_status(self):
        """Test that default status is pending."""
        todo = TodoItem(id=0, title="Task")
        assert todo.status == TodoStatus.pending

    def test_todo_item_id_validation_non_negative(self):
        """Test that id must be non-negative."""
        # Valid: zero and positive
        TodoItem(id=0, title="Task")
        TodoItem(id=1, title="Task")
        TodoItem(id=100, title="Task")

        # Invalid: negative
        with pytest.raises(ValidationError):
            TodoItem(id=-1, title="Task")

    def test_todo_item_title_validation_non_empty(self):
        """Test that title must not be empty."""
        # Valid: non-empty string
        TodoItem(id=0, title="Valid title")
        TodoItem(id=0, title="a")  # Single character is valid

        # Invalid: empty string
        with pytest.raises(ValidationError):
            TodoItem(id=0, title="")

    def test_todo_item_title_validation_required(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            TodoItem(id=0)

    def test_todo_item_id_validation_required(self):
        """Test that id is required."""
        with pytest.raises(ValidationError):
            TodoItem(title="Task")

    def test_todo_item_with_different_statuses(self):
        """Test creating TodoItem with different status values."""
        for status in TodoStatus:
            todo = TodoItem(id=0, title="Task", status=status)
            assert todo.status == status

    def test_todo_item_with_different_priorities(self):
        """Test creating TodoItem with different priority values."""
        for priority in TodoPriority:
            todo = TodoItem(id=0, title="Task", priority=priority)
            assert todo.priority == priority

    def test_todo_item_equality(self):
        """Test equality comparison between TodoItem instances."""
        todo1 = TodoItem(id=1, title="Task", priority=TodoPriority.high)
        todo2 = TodoItem(id=1, title="Task", priority=TodoPriority.high)
        todo3 = TodoItem(id=2, title="Task", priority=TodoPriority.high)

        assert todo1 == todo2
        assert todo1 != todo3

    def test_todo_item_dict_conversion(self):
        """Test converting TodoItem to dictionary."""
        todo = TodoItem(
            id=5,
            title="Test task",
            priority=TodoPriority.low,
            status=TodoStatus.completed,
        )

        todo_dict = todo.model_dump()

        assert todo_dict["id"] == 5
        assert todo_dict["title"] == "Test task"
        assert todo_dict["priority"] == "low"
        assert todo_dict["status"] == "completed"

    def test_todo_item_from_dict(self):
        """Test creating TodoItem from dictionary."""
        todo_dict = {
            "id": 10,
            "title": "From dict",
            "priority": "high",
            "status": "in_progress",
        }

        todo = TodoItem(**todo_dict)

        assert todo.id == 10
        assert todo.title == "From dict"
        assert todo.priority == TodoPriority.high
        assert todo.status == TodoStatus.in_progress

    def test_todo_item_json_serialization(self):
        """Test JSON serialization of TodoItem."""
        todo = TodoItem(id=1, title="JSON task")
        json_str = todo.model_dump_json()

        assert isinstance(json_str, str)
        assert '"id":1' in json_str or '"id": 1' in json_str
        assert "JSON task" in json_str

    def test_todo_item_json_deserialization(self):
        """Test JSON deserialization to TodoItem."""
        json_str = '{"id": 2, "title": "From JSON", "priority": "high", "status": "pending"}'
        todo = TodoItem.model_validate_json(json_str)

        assert todo.id == 2
        assert todo.title == "From JSON"
        assert todo.priority == TodoPriority.high
        assert todo.status == TodoStatus.pending

    def test_todo_item_immutability_after_creation(self):
        """Test that TodoItem fields can be updated (Pydantic models are mutable by default)."""
        todo = TodoItem(id=0, title="Original")

        # Pydantic models are mutable by default, so this should work
        todo.title = "Updated"
        assert todo.title == "Updated"

        todo.status = TodoStatus.completed
        assert todo.status == TodoStatus.completed

    def test_todo_item_with_special_characters_in_title(self):
        """Test TodoItem with special characters in title."""
        special_titles = [
            "Task with emoji 🎯",
            "Task with 'quotes'",
            'Task with "double quotes"',
            "Task with\nnewline",
            "Task with\ttab",
            "中文任务",  # Chinese characters
        ]

        for title in special_titles:
            todo = TodoItem(id=0, title=title)
            assert todo.title == title
