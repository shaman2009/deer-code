import subprocess
from pathlib import Path
from typing import Literal, Optional

from langchain.tools import ToolRuntime, tool

from deer_code.tools.reminders import generate_reminders
from deer_code.tools.edit.path_validator import PathValidator, PathValidationError

from .ignore import DEFAULT_IGNORE_PATTERNS


def _validate_grep_pattern(pattern: str) -> None:
    """
    Validate that grep pattern is safe.

    While ripgrep with list-style arguments is generally safe from command injection,
    we still validate patterns to prevent potential issues.

    Args:
        pattern: The regex pattern to validate

    Raises:
        ValueError: If pattern contains suspicious characters
    """
    if not pattern or not pattern.strip():
        raise ValueError("Pattern cannot be empty")

    # Check for null bytes (can cause issues in C code)
    if '\0' in pattern:
        raise ValueError("Pattern cannot contain null bytes")


@tool("grep", parse_docstring=True)
def grep_tool(
    runtime: ToolRuntime,
    pattern: str,
    path: Optional[str] = None,
    glob: Optional[str] = None,
    output_mode: Literal[
        "content", "files_with_matches", "count"
    ] = "files_with_matches",
    B: Optional[int] = None,
    A: Optional[int] = None,
    C: Optional[int] = None,
    n: Optional[bool] = None,
    i: Optional[bool] = None,
    type: Optional[str] = None,
    head_limit: Optional[int] = None,
    multiline: Optional[bool] = False,
) -> str:
    """A powerful search tool built on ripgrep for searching file contents with regex patterns.

    ALWAYS use this tool for search tasks. NEVER invoke `grep` or `rg` as a Bash command.
    Supports full regex syntax, file filtering, and various output modes.

    Args:
        pattern: The regular expression pattern to search for in file contents.
                Uses ripgrep syntax - literal braces need escaping (e.g., `interface\\{\\}` for `interface{}`).
        path: File or directory to search in. Defaults to current working directory if not specified.
              Must be an absolute path within the project root.
        glob: Glob pattern to filter files (e.g., "*.js", "*.{ts,tsx}").
        output_mode: Output mode - "content" shows matching lines with optional context,
                    "files_with_matches" shows only file paths (default),
                    "count" shows match counts per file.
        B: Number of lines to show before each match. Only works with output_mode="content".
        A: Number of lines to show after each match. Only works with output_mode="content".
        C: Number of lines to show before and after each match. Only works with output_mode="content".
        n: Show line numbers in output. Only works with output_mode="content".
        i: Enable case insensitive search.
        type: File type to search (e.g., "js", "py", "rust", "go", "java").
             More efficient than glob for standard file types.
        head_limit: Limit output to first N lines/entries. Works across all output modes.
        multiline: Enable multiline mode where patterns can span lines and . matches newlines.
                  Default is False (single-line matching only).

    Returns:
        Search results as a string, formatted according to the output_mode.

    Raises:
        ValueError: If pattern is invalid
        PathValidationError: If path is outside project root
    """
    # Validate pattern for security
    _validate_grep_pattern(pattern)

    # Validate path for security if provided
    if path:
        path_obj = Path(path)
        # Only validate if it's an absolute path (relative paths are relative to cwd which is safe)
        if path_obj.is_absolute():
            validator = PathValidator()
            try:
                # Validate that path is within project root
                # Allow nonexistent paths since we're searching
                validated_path = validator.validate(path_obj, allow_nonexistent=True)
                search_path = str(validated_path)
            except PathValidationError:
                # If validation fails, don't allow the search
                raise
        else:
            # Relative path - use as-is (relative to cwd)
            search_path = path
    else:
        search_path = "."

    # Build ripgrep command
    cmd = ["rg"]

    # Add pattern
    cmd.append(pattern)

    # Add path
    cmd.append(search_path)

    # Add output mode flags
    if output_mode == "files_with_matches":
        cmd.append("-l")
    elif output_mode == "count":
        cmd.append("-c")
    # content mode is default, no flag needed

    # Add context flags (only for content mode)
    if output_mode == "content":
        if C is not None:
            cmd.extend(["-C", str(C)])
        else:
            if B is not None:
                cmd.extend(["-B", str(B)])
            if A is not None:
                cmd.extend(["-A", str(A)])
        if n:
            cmd.append("-n")

    # Add case insensitive flag
    if i:
        cmd.append("-i")

    # Add file type filter
    if type:
        cmd.extend(["--type", type])

    # Add glob pattern
    if glob:
        cmd.extend(["--glob", glob])

    # Apply default ignore patterns
    for ignore_pattern in DEFAULT_IGNORE_PATTERNS:
        cmd.extend(["--glob", f"!{ignore_pattern}"])

    # Add multiline mode
    if multiline:
        cmd.extend(["-U", "--multiline-dotall"])

    # Execute ripgrep
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit (no matches found)
        )

        # Check for errors (exit code 2 indicates error, 1 means no matches)
        if result.returncode == 2 or result.stderr:
            return f"Error: {result.stderr.strip()}"

        output = result.stdout

        # Apply head limit if specified
        if head_limit and output:
            lines = output.splitlines()
            output = "\n".join(lines[:head_limit])

        # Format the result
        reminders = generate_reminders(runtime, tool_name="grep")
        if output:
            return (
                f"Here's the result in {search_path}:\n\n```\n{output}\n```{reminders}"
            )
        else:
            return f"No matches found.{reminders}"

    except Exception as e:
        return f"Error: {str(e)}"
