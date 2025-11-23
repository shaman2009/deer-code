# Lazy imports to avoid loading langchain dependencies at import time

__all__ = ["TextEditor", "text_editor_tool"]


def __getattr__(name):
    """Lazy import attributes to avoid loading heavy dependencies at import time."""
    if name == "TextEditor":
        from .text_editor import TextEditor
        return TextEditor
    elif name == "text_editor_tool":
        from .tool import text_editor_tool
        return text_editor_tool
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
