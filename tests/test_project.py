"""Tests for project.py module."""

import os
from pathlib import Path

import pytest

from deer_code.project import Project


@pytest.mark.unit
class TestProject:
    """Tests for Project class."""

    def test_init_with_valid_directory(self, tmp_path):
        """Test Project initialization with a valid directory."""
        project = Project(str(tmp_path))
        assert project.root_dir == str(tmp_path)

    def test_init_with_current_directory(self):
        """Test Project initialization with current directory."""
        cwd = os.getcwd()
        project = Project(cwd)
        assert project.root_dir == cwd

    def test_root_dir_property_getter(self, tmp_path):
        """Test root_dir property getter."""
        project = Project(str(tmp_path))
        assert project.root_dir == str(tmp_path)
        assert project._root_dir == str(tmp_path)

    def test_root_dir_property_setter_with_valid_directory(self, tmp_path):
        """Test setting root_dir to a valid directory."""
        project = Project(os.getcwd())

        # Create a new directory
        new_dir = tmp_path / "new_project"
        new_dir.mkdir()

        # Set root_dir to the new directory
        project.root_dir = str(new_dir)
        assert project.root_dir == str(new_dir)

    def test_root_dir_setter_with_nonexistent_directory(self, tmp_path):
        """Test that FileNotFoundError is raised for nonexistent directory."""
        project = Project(os.getcwd())

        nonexistent_path = str(tmp_path / "nonexistent")

        with pytest.raises(FileNotFoundError, match="does not exist"):
            project.root_dir = nonexistent_path

    def test_root_dir_setter_with_file_not_directory(self, tmp_path):
        """Test that NotADirectoryError is raised when path is a file."""
        project = Project(os.getcwd())

        # Create a file instead of a directory
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(NotADirectoryError, match="is not a directory"):
            project.root_dir = str(file_path)

    def test_root_dir_immutability_on_error(self, tmp_path):
        """Test that root_dir doesn't change if setter raises an error."""
        project = Project(os.getcwd())
        original_root = project.root_dir

        nonexistent_path = str(tmp_path / "nonexistent")

        with pytest.raises(FileNotFoundError):
            project.root_dir = nonexistent_path

        # root_dir should remain unchanged
        assert project.root_dir == original_root

    def test_multiple_project_instances(self, tmp_path):
        """Test creating multiple independent Project instances."""
        dir1 = tmp_path / "project1"
        dir2 = tmp_path / "project2"
        dir1.mkdir()
        dir2.mkdir()

        project1 = Project(str(dir1))
        project2 = Project(str(dir2))

        assert project1.root_dir == str(dir1)
        assert project2.root_dir == str(dir2)
        assert project1.root_dir != project2.root_dir

    def test_project_with_nested_directories(self, tmp_path):
        """Test Project with deeply nested directory structure."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        project = Project(str(nested_dir))
        assert project.root_dir == str(nested_dir)

    def test_project_global_instance(self):
        """Test that module-level project instance exists."""
        from deer_code.project import project

        assert isinstance(project, Project)
        assert os.path.exists(project.root_dir)
        assert os.path.isdir(project.root_dir)
