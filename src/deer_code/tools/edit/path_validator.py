"""
Path validator for text editor to prevent path traversal attacks.

This module implements security controls for file path validation, protecting
against directory traversal attacks while maintaining legitimate file access.
"""

from pathlib import Path
from typing import Optional


class PathValidationError(Exception):
    """Raised when a path fails security validation."""

    pass


class PathValidator:
    """
    Validates file paths for security before file operations.

    Implements defense against:
    - Path traversal attacks (../, symlinks)
    - Access to files outside project root
    - Access to sensitive system directories

    All paths must be absolute and within the configured project root.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize PathValidator.

        Args:
            project_root: The root directory for file operations.
                         If None, uses current working directory.
                         Must be an absolute path.
        """
        if project_root is None:
            project_root = Path.cwd()

        if not project_root.is_absolute():
            raise ValueError(
                f"Project root must be an absolute path, got: {project_root}"
            )

        # Resolve to canonical path to handle symlinks
        self.project_root = project_root.resolve()

    def validate(self, path: Path, *, allow_nonexistent: bool = False) -> Path:
        """
        Validate a path for security and return its resolved form.

        Args:
            path: The file path to validate
            allow_nonexistent: If True, allows validation of paths that don't exist yet
                              (useful for file creation). Default: False

        Returns:
            The resolved absolute path

        Raises:
            PathValidationError: If the path fails security validation
        """
        if not isinstance(path, Path):
            raise PathValidationError(f"Path must be a Path object, got: {type(path)}")

        # Must be absolute
        if not path.is_absolute():
            raise PathValidationError(
                f"Path must be absolute (start with /), got: {path}"
            )

        # Resolve to canonical path (this handles ../ and symlinks)
        # If path doesn't exist and allow_nonexistent is True, find an existing ancestor
        if not path.exists() and allow_nonexistent:
            # Walk up the directory tree to find an existing ancestor
            current = path
            parts_to_append = []

            while not current.exists():
                parts_to_append.insert(0, current.name)
                current = current.parent

                # If we've reached the root without finding an existing directory
                if current == current.parent:
                    raise PathValidationError(
                        f"Cannot find existing ancestor directory for: {path}"
                    )

            # Resolve the existing ancestor
            try:
                resolved_ancestor = current.resolve(strict=True)
            except (FileNotFoundError, RuntimeError) as e:
                raise PathValidationError(
                    f"Error resolving ancestor directory: {current}"
                ) from e

            # Build the full resolved path
            resolved_path = resolved_ancestor
            for part in parts_to_append:
                resolved_path = resolved_path / part
        else:
            # Resolve the full path
            try:
                resolved_path = path.resolve(strict=not allow_nonexistent)
            except (FileNotFoundError, RuntimeError) as e:
                if not allow_nonexistent:
                    raise PathValidationError(f"Path does not exist: {path}") from e
                # This shouldn't happen, but handle it anyway
                raise PathValidationError(f"Error resolving path: {path}") from e

        # Check if path is within project root
        try:
            resolved_path.relative_to(self.project_root)
        except ValueError:
            raise PathValidationError(
                f"Path is outside project root. "
                f"Path: {resolved_path}, "
                f"Project root: {self.project_root}"
            )

        return resolved_path

    def is_safe(
        self, path: Path, *, allow_nonexistent: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a path is safe without raising an exception.

        Args:
            path: The file path to check
            allow_nonexistent: If True, allows validation of paths that don't exist yet

        Returns:
            Tuple of (is_safe: bool, error_message: Optional[str])
        """
        try:
            self.validate(path, allow_nonexistent=allow_nonexistent)
            return (True, None)
        except PathValidationError as e:
            return (False, str(e))
