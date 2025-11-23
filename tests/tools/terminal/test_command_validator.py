"""
Tests for CommandValidator security controls.

This test suite verifies that the CommandValidator correctly identifies
and blocks command injection patterns while allowing legitimate commands.
"""

import pytest

from deer_code.tools.terminal.command_validator import (
    CommandValidator,
    CommandValidationError,
)


class TestCommandValidatorForbiddenPatterns:
    """Test detection of strictly forbidden command patterns."""

    def test_blocks_semicolon_command_chaining(self):
        """Test that semicolon command chaining is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo 'first'; echo 'second'")

        assert "command chaining with semicolon" in str(exc_info.value)

    def test_blocks_and_command_chaining(self):
        """Test that && command chaining is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("mkdir test && cd test")

        assert "command chaining with &&" in str(exc_info.value)

    def test_blocks_or_command_chaining(self):
        """Test that || command chaining is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("test -f file || touch file")

        assert "command chaining with ||" in str(exc_info.value)

    def test_blocks_background_execution(self):
        """Test that background execution (&) is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("sleep 10 &")

        assert "background execution" in str(exc_info.value)

    def test_blocks_command_substitution_with_dollar_parens(self):
        """Test that command substitution with $() is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo $(whoami)")

        assert "command substitution with $()" in str(exc_info.value)

    def test_blocks_command_substitution_with_backticks(self):
        """Test that command substitution with backticks is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo `whoami`")

        assert "command substitution with backticks" in str(exc_info.value)

    def test_blocks_suspicious_etc_redirection(self):
        """Test that redirection to /etc is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo 'malicious' > /etc/passwd")

        assert "suspicious redirection to /etc" in str(exc_info.value)

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo 'malicious' >> /etc/hosts")

        assert "suspicious redirection to /etc" in str(exc_info.value)

    def test_blocks_suspicious_dev_redirection(self):
        """Test that redirection to /dev (except /dev/null) is blocked."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo 'data' > /dev/sda")

        assert "suspicious redirection to /dev" in str(exc_info.value)

    def test_allows_dev_null_redirection(self):
        """Test that redirection to /dev/null is allowed."""
        validator = CommandValidator()

        # Should not raise - /dev/null is safe
        validator.validate("echo 'data' > /dev/null")
        validator.validate("echo 'data' 2> /dev/null")


class TestCommandValidatorLegitimateCommands:
    """Test that legitimate commands are allowed."""

    def test_allows_simple_command(self):
        """Test that simple commands are allowed."""
        validator = CommandValidator()

        validator.validate("ls -la")
        validator.validate("echo 'hello world'")
        validator.validate("pwd")

    def test_allows_cd_command(self):
        """Test that cd commands are allowed."""
        validator = CommandValidator()

        validator.validate("cd /home/user")
        validator.validate('cd "directory with spaces"')

    def test_allows_pipe_commands_by_default(self):
        """Test that pipe commands are allowed by default."""
        validator = CommandValidator()

        validator.validate("cat file.txt | grep 'pattern'")
        validator.validate("ls -la | wc -l")

    def test_allows_file_redirection_by_default(self):
        """Test that file redirection is allowed by default."""
        validator = CommandValidator()

        validator.validate("echo 'content' > output.txt")
        validator.validate("cat < input.txt")
        validator.validate("echo 'append' >> log.txt")

    def test_allows_commands_with_arguments(self):
        """Test that commands with complex arguments are allowed."""
        validator = CommandValidator()

        validator.validate("grep -r 'pattern' /home/user/project")
        validator.validate("find . -name '*.py' -type f")

    def test_allows_environment_variable_setting(self):
        """Test that setting environment variables is allowed."""
        validator = CommandValidator()

        # Note: This is different from command substitution
        validator.validate("export PATH=/usr/bin:$PATH")
        validator.validate("VAR=value")


class TestCommandValidatorConfiguration:
    """Test CommandValidator configuration options."""

    def test_can_disable_pipes(self):
        """Test that pipes can be disabled via configuration."""
        validator = CommandValidator(allow_pipes=False)

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("cat file | grep pattern")

        assert "Pipe commands are not allowed" in str(exc_info.value)

    def test_can_disable_redirects(self):
        """Test that redirects can be disabled via configuration."""
        validator = CommandValidator(allow_redirects=False)

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("echo 'data' > file.txt")

        assert "File redirection is not allowed" in str(exc_info.value)

    def test_empty_command_raises_error(self):
        """Test that empty commands are rejected."""
        validator = CommandValidator()

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("")

        assert "Empty command" in str(exc_info.value)

        with pytest.raises(CommandValidationError) as exc_info:
            validator.validate("   ")

        assert "Empty command" in str(exc_info.value)


class TestCommandValidatorIsSafeMethod:
    """Test the is_safe() convenience method."""

    def test_is_safe_returns_true_for_safe_commands(self):
        """Test that is_safe() returns True for safe commands."""
        validator = CommandValidator()

        is_safe, error = validator.is_safe("ls -la")

        assert is_safe is True
        assert error is None

    def test_is_safe_returns_false_for_unsafe_commands(self):
        """Test that is_safe() returns False with error message for unsafe commands."""
        validator = CommandValidator()

        is_safe, error = validator.is_safe("echo 'first'; echo 'second'")

        assert is_safe is False
        assert error is not None
        assert "command chaining with semicolon" in error

    def test_is_safe_does_not_raise_exception(self):
        """Test that is_safe() never raises exceptions."""
        validator = CommandValidator()

        # Should not raise, just return False
        is_safe, error = validator.is_safe("rm -rf / &")

        assert is_safe is False
        assert "background execution" in error


class TestCommandValidatorEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_ampersand_in_middle_of_command_allowed(self):
        """Test that & in the middle of arguments is allowed."""
        validator = CommandValidator()

        # & should only be blocked at the end (background execution)
        validator.validate("echo 'rock & roll'")
        validator.validate("grep 'A & B' file.txt")

    def test_semicolon_in_quoted_string_still_blocked(self):
        """Test that semicolons even in quotes are blocked (conservative)."""
        validator = CommandValidator()

        # Conservative approach: block semicolons even in quotes
        with pytest.raises(CommandValidationError):
            validator.validate("echo 'first; second'")

    def test_handles_multiline_commands(self):
        """Test validation of multiline commands."""
        validator = CommandValidator()

        # Multiline should still be validated
        with pytest.raises(CommandValidationError):
            validator.validate("echo 'line1'\necho 'line2'; echo 'line3'")
