"""Structured logging configuration for DeerCode."""

import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as structured data.

        Args:
            record: The log record to format.

        Returns:
            Formatted log message.
        """
        # Base log data
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "tool_name"):
            log_data["tool"] = record.tool_name
        if hasattr(record, "duration"):
            log_data["duration_ms"] = f"{record.duration * 1000:.2f}"
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Format as key=value pairs
        parts = [f"{k}={v}" for k, v in log_data.items()]
        return " ".join(parts)


def setup_logging(
    level: str = "INFO",
    structured: bool = True,
    log_file: str | None = None,
) -> None:
    """Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        structured: Whether to use structured logging format.
        log_file: Optional file path to write logs to.
    """
    # Create formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


# Convenience functions for structured logging
def log_tool_execution(
    logger: logging.Logger,
    tool_name: str,
    duration: float,
    success: bool = True,
    **extra: Any,
) -> None:
    """Log tool execution with structured data.

    Args:
        logger: Logger instance.
        tool_name: Name of the tool.
        duration: Execution duration in seconds.
        success: Whether the execution was successful.
        **extra: Additional fields to log.
    """
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Tool execution {'succeeded' if success else 'failed'}",
        extra={"tool_name": tool_name, "duration": duration, **extra},
    )


def log_agent_action(
    logger: logging.Logger,
    agent: str,
    action: str,
    **extra: Any,
) -> None:
    """Log agent action with structured data.

    Args:
        logger: Logger instance.
        agent: Name of the agent.
        action: Description of the action.
        **extra: Additional fields to log.
    """
    logger.info(action, extra={"agent": agent, **extra})
