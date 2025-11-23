"""
Command validator for bash terminal to prevent command injection attacks.

This module implements security controls for bash command execution, protecting
against common command injection patterns while maintaining legitimate functionality.
"""

import re
from typing import Optional


class CommandValidationError(Exception):
    """Raised when a command fails security validation."""

    pass


class CommandValidator:
    """
    Validates bash commands for security before execution.

    Implements defense against:
    - Command chaining (;, &&, ||)
    - Background execution (&)
    - Command substitution ($(), ``)
    - Potentially dangerous redirections

    Note: Pipes (|) are allowed as they are legitimate command composition,
    but both sides are validated to ensure safety.
    """

    # Patterns that are strictly forbidden
    FORBIDDEN_PATTERNS = [
        (r";", "command chaining with semicolon"),
        (r"&&", "command chaining with &&"),
        (r"\|\|", "command chaining with ||"),
        (r"&\s*$", "background execution"),
        (r"\$\(", "command substitution with $()"),
        (r"`", "command substitution with backticks"),
        (r">>\s*/etc/", "suspicious redirection to /etc"),
        (r">\s*/etc/", "suspicious redirection to /etc"),
        (r">>\s*/dev/", "suspicious redirection to /dev (except /dev/null)"),
        (r">\s*/dev/(?!null)", "suspicious redirection to /dev (except /dev/null)"),
    ]

    # Patterns that require additional validation
    WARNING_PATTERNS = [
        (r"\|", "pipe command"),
        (r">>", "append redirection"),
        (r">", "output redirection"),
        (r"<", "input redirection"),
    ]

    def __init__(self, allow_pipes: bool = True, allow_redirects: bool = True):
        """
        Initialize CommandValidator.

        Args:
            allow_pipes: Whether to allow pipe commands (|)
            allow_redirects: Whether to allow file redirections (>, <, >>)
        """
        self.allow_pipes = allow_pipes
        self.allow_redirects = allow_redirects

    def validate(self, command: str) -> None:
        """
        Validate a command for security issues.

        Args:
            command: The bash command to validate

        Raises:
            CommandValidationError: If the command contains forbidden patterns
        """
        if not command or not command.strip():
            raise CommandValidationError("Empty command")

        command = command.strip()

        # Check for strictly forbidden patterns
        for pattern, description in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command):
                raise CommandValidationError(
                    f"Forbidden pattern detected: {description}. "
                    f"Command: {command[:50]}..."
                )

        # Check warning patterns based on configuration
        if not self.allow_pipes and "|" in command:
            raise CommandValidationError(
                f"Pipe commands are not allowed. Command: {command[:50]}..."
            )

        if not self.allow_redirects:
            for pattern, description in self.WARNING_PATTERNS:
                if pattern in [">", ">>", "<"] and re.search(pattern, command):
                    raise CommandValidationError(
                        f"File redirection is not allowed: {description}. "
                        f"Command: {command[:50]}..."
                    )

    def is_safe(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if a command is safe without raising an exception.

        Args:
            command: The bash command to check

        Returns:
            Tuple of (is_safe: bool, error_message: Optional[str])
        """
        try:
            self.validate(command)
            return (True, None)
        except CommandValidationError as e:
            return (False, str(e))
