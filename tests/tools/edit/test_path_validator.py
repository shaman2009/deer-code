"""
Tests for PathValidator security controls.

This test suite verifies that the PathValidator correctly identifies
and blocks path traversal attacks while allowing legitimate file access.
"""

import pytest
from pathlib import Path

from deer_code.tools.edit.path_validator import PathValidator, PathValidationError


class TestPathValidatorBasics:
    """Test basic PathValidator functionality."""

    def test_init_with_default_root(self):
        """Test PathValidator initialization with default project root."""
        validator = PathValidator()

        assert validator.project_root.is_absolute()
        assert validator.project_root == Path.cwd().resolve()

    def test_init_with_custom_root(self, tmp_path):
        """Test PathValidator initialization with custom project root."""
        validator = PathValidator(project_root=tmp_path)

        assert validator.project_root == tmp_path.resolve()

    def test_init_rejects_relative_project_root(self):
        """Test that relative project roots are rejected."""
        with pytest.raises(ValueError) as exc_info:
            PathValidator(project_root=Path("relative/path"))

        assert "must be an absolute path" in str(exc_info.value)

    def test_resolves_symlinks_in_project_root(self, tmp_path):
        """Test that project root symlinks are resolved."""
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link_dir = tmp_path / "link"
        link_dir.symlink_to(real_dir)

        validator = PathValidator(project_root=link_dir)

        # Should resolve to real directory
        assert validator.project_root == real_dir.resolve()


class TestPathValidatorValidation:
    """Test path validation logic."""

    def test_allows_absolute_path_within_project(self, tmp_path):
        """Test that absolute paths within project are allowed."""
        validator = PathValidator(project_root=tmp_path)
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = validator.validate(test_file)

        assert result == test_file.resolve()

    def test_allows_nested_path_within_project(self, tmp_path):
        """Test that nested paths within project are allowed."""
        validator = PathValidator(project_root=tmp_path)
        nested_dir = tmp_path / "subdir" / "nested"
        nested_dir.mkdir(parents=True)
        test_file = nested_dir / "test.txt"
        test_file.write_text("content")

        result = validator.validate(test_file)

        assert result == test_file.resolve()

    def test_rejects_relative_path(self, tmp_path):
        """Test that relative paths are rejected."""
        validator = PathValidator(project_root=tmp_path)

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(Path("relative/path.txt"))

        assert "must be absolute" in str(exc_info.value)

    def test_rejects_path_outside_project(self, tmp_path):
        """Test that paths outside project root are rejected."""
        project = tmp_path / "project"
        project.mkdir()
        outside = tmp_path / "outside" / "file.txt"
        outside.parent.mkdir()
        outside.write_text("sensitive")

        validator = PathValidator(project_root=project)

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(outside)

        assert "outside project root" in str(exc_info.value)

    def test_rejects_nonexistent_path_by_default(self, tmp_path):
        """Test that nonexistent paths are rejected by default."""
        validator = PathValidator(project_root=tmp_path)
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(nonexistent)

        assert "does not exist" in str(exc_info.value)

    def test_allows_nonexistent_path_with_flag(self, tmp_path):
        """Test that nonexistent paths can be allowed with flag."""
        validator = PathValidator(project_root=tmp_path)
        nonexistent = tmp_path / "newfile.txt"

        result = validator.validate(nonexistent, allow_nonexistent=True)

        assert result == nonexistent.resolve()

    def test_rejects_non_path_object(self, tmp_path):
        """Test that non-Path objects are rejected."""
        validator = PathValidator(project_root=tmp_path)

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate("/some/path")  # String instead of Path

        assert "must be a Path object" in str(exc_info.value)


class TestPathValidatorTraversalAttacks:
    """Test protection against path traversal attacks."""

    def test_blocks_parent_directory_traversal(self, tmp_path):
        """Test that ../ traversal outside project is blocked."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "file.txt").write_text("inside")

        # Create a sensitive file outside project
        sensitive = tmp_path / "sensitive.txt"
        sensitive.write_text("secret")

        validator = PathValidator(project_root=project)

        # Try to access via ../
        traversal_path = project / ".." / "sensitive.txt"

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(traversal_path)

        assert "outside project root" in str(exc_info.value)

    def test_blocks_deep_parent_traversal(self, tmp_path):
        """Test that deep ../ traversal is blocked."""
        project = tmp_path / "project" / "subdir" / "deep"
        project.mkdir(parents=True)

        sensitive = tmp_path / "root_secret.txt"
        sensitive.write_text("secret")

        validator = PathValidator(project_root=project)

        # Try ../../.. to escape
        traversal_path = project / ".." / ".." / ".." / "root_secret.txt"

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(traversal_path)

        assert "outside project root" in str(exc_info.value)

    def test_blocks_symlink_escape(self, tmp_path):
        """Test that symlinks pointing outside project are blocked."""
        project = tmp_path / "project"
        project.mkdir()

        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("sensitive")

        # Create symlink inside project pointing outside
        link = project / "escape_link"
        link.symlink_to(outside_file)

        validator = PathValidator(project_root=project)

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(link)

        assert "outside project root" in str(exc_info.value)

    def test_allows_symlink_within_project(self, tmp_path):
        """Test that symlinks within project are allowed."""
        project = tmp_path / "project"
        project.mkdir()

        real_file = project / "real.txt"
        real_file.write_text("content")

        link = project / "link.txt"
        link.symlink_to(real_file)

        validator = PathValidator(project_root=project)

        result = validator.validate(link)

        # Should resolve to real file within project
        assert result == real_file.resolve()

    def test_blocks_absolute_path_to_system_files(self, tmp_path):
        """Test that absolute paths to system files are blocked."""
        project = tmp_path / "project"
        project.mkdir()

        validator = PathValidator(project_root=project)

        # Try to access /etc/passwd
        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(Path("/etc/passwd"), allow_nonexistent=True)

        assert "outside project root" in str(exc_info.value)


class TestPathValidatorEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_handles_nonexistent_parent_directory(self, tmp_path):
        """Test handling of paths with nonexistent parent directories."""
        validator = PathValidator(project_root=tmp_path)

        # Parent doesn't exist
        path = tmp_path / "nonexistent_dir" / "file.txt"

        with pytest.raises(PathValidationError) as exc_info:
            validator.validate(path, allow_nonexistent=True)

        assert "Parent directory does not exist" in str(exc_info.value)

    def test_allows_file_creation_in_existing_directory(self, tmp_path):
        """Test that new files in existing directories are allowed."""
        validator = PathValidator(project_root=tmp_path)
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        new_file = subdir / "new.txt"

        result = validator.validate(new_file, allow_nonexistent=True)

        assert result == new_file.resolve()

    def test_project_root_at_filesystem_root(self):
        """Test PathValidator with project root at /."""
        # This is an edge case - using / as project root
        validator = PathValidator(project_root=Path("/"))

        # Any absolute path should be valid
        result = validator.validate(Path("/tmp"), allow_nonexistent=True)

        assert result.is_absolute()

    def test_handles_paths_with_dots_in_filename(self, tmp_path):
        """Test that files with dots in name are handled correctly."""
        validator = PathValidator(project_root=tmp_path)

        # Dots in filename, not directory traversal
        file_with_dots = tmp_path / "my.file.with.dots.txt"
        file_with_dots.write_text("content")

        result = validator.validate(file_with_dots)

        assert result == file_with_dots.resolve()


class TestPathValidatorIsSafeMethod:
    """Test the is_safe() convenience method."""

    def test_is_safe_returns_true_for_safe_paths(self, tmp_path):
        """Test that is_safe() returns True for safe paths."""
        validator = PathValidator(project_root=tmp_path)
        safe_file = tmp_path / "safe.txt"
        safe_file.write_text("content")

        is_safe, error = validator.is_safe(safe_file)

        assert is_safe is True
        assert error is None

    def test_is_safe_returns_false_for_unsafe_paths(self, tmp_path):
        """Test that is_safe() returns False with error for unsafe paths."""
        project = tmp_path / "project"
        project.mkdir()
        outside = tmp_path / "outside.txt"
        outside.write_text("sensitive")

        validator = PathValidator(project_root=project)

        is_safe, error = validator.is_safe(outside)

        assert is_safe is False
        assert error is not None
        assert "outside project root" in error

    def test_is_safe_does_not_raise_exception(self, tmp_path):
        """Test that is_safe() never raises exceptions."""
        validator = PathValidator(project_root=tmp_path)

        # Should not raise, just return False
        is_safe, error = validator.is_safe(Path("relative/path"))

        assert is_safe is False
        assert "must be absolute" in error

    def test_is_safe_with_allow_nonexistent(self, tmp_path):
        """Test is_safe() with allow_nonexistent flag."""
        validator = PathValidator(project_root=tmp_path)
        new_file = tmp_path / "new.txt"

        is_safe, error = validator.is_safe(new_file, allow_nonexistent=True)

        assert is_safe is True
        assert error is None
