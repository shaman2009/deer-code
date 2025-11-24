"""Unified error handling for tools."""

import logging
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def safe_tool_execution(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator for safe tool execution with unified error handling.

    This decorator catches common exceptions and returns user-friendly error messages.
    It also logs errors for debugging purposes.

    Args:
        func: The tool function to wrap.

    Returns:
        The wrapped function with error handling.

    Example:
        @tool("my_tool", parse_docstring=True)
        @safe_tool_execution
        def my_tool(runtime: ToolRuntime, ...):
            ...
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        tool_name = func.__name__.replace("_tool", "")
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            error_msg = f"Error: File or directory not found - {e}"
            logger.warning(f"{tool_name} failed: {error_msg}")
            return error_msg  # type: ignore
        except PermissionError as e:
            error_msg = f"Error: Permission denied - {e}"
            logger.warning(f"{tool_name} failed: {error_msg}")
            return error_msg  # type: ignore
        except ValueError as e:
            error_msg = f"Error: Invalid input - {e}"
            logger.warning(f"{tool_name} failed: {error_msg}")
            return error_msg  # type: ignore
        except OSError as e:
            error_msg = f"Error: System error - {e}"
            logger.error(f"{tool_name} failed: {error_msg}")
            return error_msg  # type: ignore
        except Exception as e:
            error_msg = f"Error: Unexpected error - {str(e)}"
            logger.exception(f"{tool_name} failed with unexpected error")
            return error_msg  # type: ignore

    return wrapper
