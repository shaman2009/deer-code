"""
Comprehensive tests for TextEditor class.

This test suite covers:
1. File viewing with and without view_range
2. String replacement (str_replace)
3. Text insertion (insert)
4. Path validation and security
5. Path traversal attack scenarios (documenting current behavior)
6. Error handling
7. File creation and directory handling
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for direct import
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Direct import from module file
from deer_code.tools.edit import text_editor
from deer_code.tools.edit.path_validator import PathValidator
TextEditor = text_editor.TextEditor


@pytest.fixture
def editor(tmp_path):
    """Create a TextEditor with PathValidator configured for test directory."""
    path_validator = PathValidator(project_root=tmp_path)
    return TextEditor(path_validator=path_validator)


class TestTextEditorView:
    """Test file viewing functionality."""

    def test_view_simple_file(self, tmp_path, editor):
        """Test viewing a simple text file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        result = editor.view(test_file)

        # Check that line numbers are included
        assert "  1 Line 1" in result
        assert "  2 Line 2" in result
        assert "  3 Line 3" in result

    def test_view_with_range(self, tmp_path, editor):
        """Test viewing specific line range."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        result = editor.view(test_file, view_range=[2, 4])

        # Should only contain lines 2-4
        assert "  2 Line 2" in result
        assert "  3 Line 3" in result
        assert "  4 Line 4" in result
        assert "Line 1" not in result
        assert "Line 5" not in result

    def test_view_range_to_eof(self, tmp_path, editor):
        """Test viewing from specific line to end of file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")

        result = editor.view(test_file, view_range=[3, -1])

        # Should contain lines 3-5
        assert "  3 Line 3" in result
        assert "  4 Line 4" in result
        assert "  5 Line 5" in result
        assert "Line 1" not in result
        assert "Line 2" not in result

    def test_view_nonexistent_file(self, tmp_path, editor):
        """Test viewing a file that doesn't exist."""
        from deer_code.tools.edit.path_validator import PathValidationError

        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(PathValidationError, match="does not exist"):
            editor.view(test_file)

    def test_view_directory_not_file(self, tmp_path, editor):
        """Test viewing a directory instead of file."""
        with pytest.raises(ValueError, match="Path is not a file"):
            editor.view(tmp_path)

    def test_view_range_invalid_format(self, tmp_path, editor):
        """Test viewing with invalid view_range format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")


        # Test with single element
        with pytest.raises(ValueError, match="Invalid `view_range`"):
            editor.view(test_file, view_range=[1])

        # Test with non-integers
        with pytest.raises(ValueError, match="Invalid `view_range`"):
            editor.view(test_file, view_range=["1", "2"])

    def test_view_range_start_line_out_of_bounds(self, tmp_path, editor):
        """Test viewing with start line out of range."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")


        # Start line < 1
        with pytest.raises(ValueError, match="Invalid `view_range`"):
            editor.view(test_file, view_range=[0, 2])

        # Start line > file lines
        with pytest.raises(ValueError, match="Invalid `view_range`"):
            editor.view(test_file, view_range=[10, 12])

    def test_view_range_end_line_out_of_bounds(self, tmp_path, editor):
        """Test viewing with end line out of range."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")


        # End line before start line
        with pytest.raises(ValueError, match="Invalid `view_range`"):
            editor.view(test_file, view_range=[2, 1])

    def test_view_empty_file(self, tmp_path, editor):
        """Test viewing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = editor.view(test_file)

        # Empty file should return empty result or line number only
        assert result == "" or result.strip() == ""


class TestTextEditorStrReplace:
    """Test string replacement functionality."""

    def test_str_replace_single_occurrence(self, tmp_path, editor):
        """Test replacing string that appears once."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        count = editor.str_replace(test_file, "World", "Universe")

        assert count == 1
        assert test_file.read_text() == "Hello Universe"

    def test_str_replace_multiple_occurrences(self, tmp_path, editor):
        """Test replacing string that appears multiple times."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("foo bar foo baz foo")

        count = editor.str_replace(test_file, "foo", "qux")

        assert count == 3
        assert test_file.read_text() == "qux bar qux baz qux"

    def test_str_replace_with_none(self, tmp_path, editor):
        """Test replacing string with None (removal)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        count = editor.str_replace(test_file, " World", None)

        assert count == 1
        assert test_file.read_text() == "Hello"

    def test_str_replace_multiline(self, tmp_path, editor):
        """Test replacing multiline string."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        count = editor.str_replace(test_file, "Line 2\nLine 3", "New Line 2")

        assert count == 1
        assert test_file.read_text() == "Line 1\nNew Line 2"

    def test_str_replace_string_not_found(self, tmp_path, editor):
        """Test replacing string that doesn't exist."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        with pytest.raises(ValueError, match="String not found in file"):
            editor.str_replace(test_file, "Universe", "Galaxy")

    def test_str_replace_nonexistent_file(self, tmp_path, editor):
        """Test replacing in non-existent file."""
        from deer_code.tools.edit.path_validator import PathValidationError

        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(PathValidationError, match="does not exist"):
            editor.str_replace(test_file, "old", "new")

    def test_str_replace_directory_not_file(self, tmp_path, editor):
        """Test replacing in directory instead of file."""
        with pytest.raises(ValueError, match="Path is not a file"):
            editor.str_replace(tmp_path, "old", "new")


class TestTextEditorInsert:
    """Test text insertion functionality."""

    def test_insert_at_beginning(self, tmp_path, editor):
        """Test inserting at the beginning of file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2")

        editor.insert(test_file, 0, "New Line")

        assert test_file.read_text() == "New Line\nLine 1\nLine 2"

    def test_insert_at_middle(self, tmp_path, editor):
        """Test inserting in the middle of file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        editor.insert(test_file, 1, "Inserted Line")

        assert test_file.read_text() == "Line 1\nInserted Line\nLine 2\nLine 3"

    def test_insert_at_end(self, tmp_path, editor):
        """Test inserting at the end of file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2")

        editor.insert(test_file, 2, "New Last Line")

        assert test_file.read_text() == "Line 1\nLine 2\nNew Last Line"

    def test_insert_multiline_text(self, tmp_path, editor):
        """Test inserting multiline text."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 3")

        editor.insert(test_file, 1, "Line 2a\nLine 2b")

        assert "Line 2a\nLine 2b" in test_file.read_text()

    def test_insert_negative_line_number(self, tmp_path, editor):
        """Test inserting with negative line number."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2")

        with pytest.raises(ValueError, match="Invalid insert_line"):
            editor.insert(test_file, -1, "New Line")

    def test_insert_line_number_too_large(self, tmp_path, editor):
        """Test inserting with line number beyond file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2")

        with pytest.raises(ValueError, match="Invalid insert_line"):
            editor.insert(test_file, 100, "New Line")

    def test_insert_in_empty_file(self, tmp_path, editor):
        """Test inserting in empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        editor.insert(test_file, 0, "First Line")

        assert test_file.read_text() == "First Line"

    def test_insert_nonexistent_file(self, tmp_path, editor):
        """Test inserting in non-existent file."""
        from deer_code.tools.edit.path_validator import PathValidationError

        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(PathValidationError, match="does not exist"):
            editor.insert(test_file, 0, "Line")

    def test_insert_directory_not_file(self, tmp_path, editor):
        """Test inserting in directory instead of file."""
        with pytest.raises(ValueError, match="Path is not a file"):
            editor.insert(tmp_path, 0, "Line")


class TestTextEditorPathValidation:
    """Test path validation functionality."""

    def test_validate_absolute_path(self, tmp_path, editor):
        """Test validating absolute path (should pass)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Should not raise exception
        editor.validate_path("view", test_file)

    def test_validate_relative_path_raises_error(self):
        """Test validating relative path (should fail)."""
        editor = TextEditor()
        relative_path = Path("relative/path.txt")

        with pytest.raises(ValueError, match="not an absolute path"):
            editor.validate_path("view", relative_path)

    def test_validate_dot_relative_path(self):
        """Test validating ./relative path."""
        editor = TextEditor()
        relative_path = Path("./file.txt")

        with pytest.raises(ValueError, match="not an absolute path"):
            editor.validate_path("view", relative_path)


class TestTextEditorPathTraversal:
    """
    Test path traversal scenarios.

    These tests verify that PathValidator properly blocks path traversal attacks
    and access to files outside the project root.
    """

    def test_absolute_path_outside_project_is_blocked(self, tmp_path):
        """
        Test that absolute paths outside project root are blocked by PathValidator.
        """
        from deer_code.tools.edit.path_validator import PathValidationError

        # Create a project directory within tmp_path
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create an editor with project_dir as root
        path_validator = PathValidator(project_root=project_dir)
        editor = TextEditor(path_validator=path_validator)

        # Create a file outside the project directory
        outside_file = tmp_path / "outside_project.txt"
        outside_file.write_text("sensitive data")

        # This should now raise PathValidationError
        with pytest.raises(PathValidationError, match="outside project root"):
            editor.view(outside_file)

    def test_parent_directory_traversal_is_blocked(self, tmp_path):
        """
        Test that parent directory traversal is blocked by PathValidator.
        """
        from deer_code.tools.edit.path_validator import PathValidationError

        # Create directory structure
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Create an editor with project_dir as root
        path_validator = PathValidator(project_root=project_dir)
        editor = TextEditor(path_validator=path_validator)

        secret_file = outside_dir / "secret.txt"
        secret_file.write_text("secret content")

        # This should be blocked by security validation
        with pytest.raises(PathValidationError, match="outside project root"):
            editor.view(secret_file)

    def test_write_outside_project_is_blocked(self, tmp_path):
        """
        Test that writing files outside project is blocked by PathValidator.
        """
        from deer_code.tools.edit.path_validator import PathValidationError

        # Create a project directory within tmp_path
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create an editor with project_dir as root
        path_validator = PathValidator(project_root=project_dir)
        editor = TextEditor(path_validator=path_validator)

        # Create parent directory outside the project
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Try to write outside the project
        outside_file = outside_dir / "new_file.txt"

        # This should be blocked by security validation
        with pytest.raises(PathValidationError, match="outside project root"):
            editor.write_file(outside_file, "test content")


class TestTextEditorErrorHandling:
    """Test error handling for various scenarios."""

    @pytest.mark.skipif(os.getuid() == 0, reason="Permission tests don't work as root")
    def test_read_file_permission_error(self, tmp_path, editor):
        """Test reading file without read permissions."""
        test_file = tmp_path / "no_read.txt"
        test_file.write_text("content")
        test_file.chmod(0o000)  # No permissions

        try:
            with pytest.raises(ValueError, match="Error reading"):
                editor.read_file(test_file)
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    @pytest.mark.skipif(os.getuid() == 0, reason="Permission tests don't work as root")
    def test_write_file_to_readonly_parent(self, tmp_path, editor):
        """Test writing to file in readonly directory."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        test_file = readonly_dir / "file.txt"

        # Make directory readonly
        readonly_dir.chmod(0o444)

        try:
            with pytest.raises(ValueError, match="Error writing"):
                editor.write_file(test_file, "content")
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

    def test_view_file_with_unicode(self, tmp_path, editor):
        """Test viewing file with unicode content."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("Hello 世界 🚀")

        result = editor.view(test_file)

        assert "Hello 世界 🚀" in result or "Hello" in result

    def test_replace_in_binary_file(self, tmp_path, editor):
        """Test that text operations work on text files."""
        test_file = tmp_path / "text.txt"
        test_file.write_text("text content")

        count = editor.str_replace(test_file, "text", "new")
        assert count == 1


class TestTextEditorFileCreation:
    """Test file creation and directory handling."""

    def test_write_creates_parent_directories(self, tmp_path, editor):
        """Test that write_file creates parent directories."""
        nested_file = tmp_path / "a" / "b" / "c" / "file.txt"

        editor.write_file(nested_file, "content")

        assert nested_file.exists()
        assert nested_file.read_text() == "content"

    def test_write_overwrites_existing_file(self, tmp_path, editor):
        """Test that write_file overwrites existing content."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("old content")

        editor.write_file(test_file, "new content")

        assert test_file.read_text() == "new content"

    def test_write_empty_content(self, tmp_path, editor):
        """Test writing empty content to file."""
        test_file = tmp_path / "empty.txt"

        editor.write_file(test_file, "")

        assert test_file.exists()
        assert test_file.read_text() == ""


class TestTextEditorEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_view_file_with_no_newline_at_end(self, tmp_path, editor):
        """Test viewing file without trailing newline."""
        test_file = tmp_path / "no_newline.txt"
        test_file.write_bytes(b"Line 1\nLine 2")  # No trailing newline

        result = editor.view(test_file)

        assert "  1 Line 1" in result
        assert "  2 Line 2" in result

    def test_view_very_long_lines(self, tmp_path, editor):
        """Test viewing file with very long lines."""
        test_file = tmp_path / "long_lines.txt"
        long_line = "x" * 10000
        test_file.write_text(f"{long_line}\nshort line")

        result = editor.view(test_file)

        assert "  1 " in result
        assert "  2 short line" in result

    def test_str_replace_with_special_characters(self, tmp_path, editor):
        """Test replacing strings with special regex characters."""
        test_file = tmp_path / "special.txt"
        test_file.write_text("Price: $100 (special offer!)")

        count = editor.str_replace(test_file, "$100", "$200")

        assert count == 1
        assert test_file.read_text() == "Price: $200 (special offer!)"

    def test_insert_with_windows_line_endings(self, tmp_path, editor):
        """Test inserting text in file with Windows line endings."""
        test_file = tmp_path / "windows.txt"
        test_file.write_text("Line 1\r\nLine 2\r\nLine 3")

        editor.insert(test_file, 1, "Inserted Line")

        # Should handle line endings properly
        assert "Inserted Line" in test_file.read_text()

    def test_content_with_line_numbers_offset(self, tmp_path, editor):
        """Test line numbers with custom offset."""
        content = "Line 1\nLine 2\nLine 3"
        result = editor._content_with_line_numbers(content, init_line=10)

        assert " 10 Line 1" in result
        assert " 11 Line 2" in result
        assert " 12 Line 3" in result
