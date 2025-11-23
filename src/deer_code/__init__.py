"""🦌 DeerCode - A minimalist yet sufficient project for enabling everyone to learn how to develop an AI Coding Agent."""

__version__ = "0.1.0"

# Lazy imports to avoid loading the entire application when importing submodules
# This allows tests to import specific modules without triggering all dependencies
__all__ = ["main", "project"]


def __getattr__(name):
    """Lazy import attributes to avoid loading heavy dependencies at import time."""
    if name == "main":
        from .main import main
        return main
    elif name == "project":
        from .main import project
        return project
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
