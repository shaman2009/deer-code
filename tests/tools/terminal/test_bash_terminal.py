"""
Comprehensive tests for BashTerminal class.

This test suite covers:
1. Basic command execution
2. Command injection attack prevention (future security hardening)
3. Working directory management
4. Error handling and timeouts
5. Resource cleanup
6. Context manager support
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path and import BashTerminal directly from the module file
# This avoids importing the entire deer_code package which has dependency issues
src_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Direct import from module file
from deer_code.tools.terminal import bash_terminal
BashTerminal = bash_terminal.BashTerminal


class TestBashTerminalBasics:
    """Test basic functionality of BashTerminal."""

    def test_init_with_default_directory(self):
        """Test initialization with default directory."""
        terminal = BashTerminal()
        try:
            assert terminal.cwd == os.getcwd()
            assert terminal.shell.isalive()
            assert terminal.prompt == "BASH_TERMINAL_PROMPT> "
        finally:
            terminal.close()

    def test_init_with_custom_directory(self, tmp_path):
        """Test initialization with custom working directory."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            # Verify the working directory was set
            pwd_output = terminal.getcwd()
            assert str(tmp_path) in pwd_output or os.path.samefile(
                pwd_output, str(tmp_path)
            )
        finally:
            terminal.close()

    def test_simple_command_execution(self):
        """Test executing a simple command."""
        terminal = BashTerminal()
        try:
            result = terminal.execute("echo 'Hello, World!'")
            assert "Hello, World!" in result
        finally:
            terminal.close()

    def test_multiline_output(self):
        """Test command with multiline output."""
        terminal = BashTerminal()
        try:
            # Use printf to generate multiline output without command chaining
            result = terminal.execute("printf 'line1\\nline2\\nline3\\n'")
            assert "line1" in result
            assert "line2" in result
            assert "line3" in result
        finally:
            terminal.close()

    def test_command_with_special_characters(self):
        """Test command with special characters in output."""
        terminal = BashTerminal()
        try:
            result = terminal.execute("echo 'Special: !@#$%^&*()'")
            assert "Special: !@#$%^&*()" in result
        finally:
            terminal.close()


class TestBashTerminalWorkingDirectory:
    """Test working directory management."""

    def test_getcwd_returns_current_directory(self, tmp_path):
        """Test getcwd returns the current working directory."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            cwd = terminal.getcwd()
            assert str(tmp_path) in cwd or os.path.samefile(cwd, str(tmp_path))
        finally:
            terminal.close()

    def test_directory_change_persists(self, tmp_path):
        """Test that directory changes persist across commands."""
        # Create a subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            # Change to subdirectory
            terminal.execute(f'cd "{subdir}"')

            # Verify the change persisted
            cwd = terminal.getcwd()
            assert str(subdir) in cwd or os.path.samefile(cwd, str(subdir))
        finally:
            terminal.close()

    def test_relative_path_navigation(self, tmp_path):
        """Test navigation with relative paths."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            terminal.execute("cd subdir")
            cwd = terminal.getcwd()
            assert "subdir" in cwd
        finally:
            terminal.close()


class TestBashTerminalFileOperations:
    """Test file operations through bash commands."""

    def test_file_creation(self, tmp_path):
        """Test creating a file via bash command."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            terminal.execute("echo 'test content' > testfile.txt")
            result = terminal.execute("cat testfile.txt")
            assert "test content" in result
        finally:
            terminal.close()

    def test_directory_creation(self, tmp_path):
        """Test creating directories."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            terminal.execute("mkdir -p dir1/dir2/dir3")
            result = terminal.execute("ls -la dir1/dir2")
            assert "dir3" in result
        finally:
            terminal.close()

    def test_file_listing(self, tmp_path):
        """Test listing files."""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            result = terminal.execute("ls")
            assert "file1.txt" in result
            assert "file2.txt" in result
        finally:
            terminal.close()


class TestBashTerminalCommandInjection:
    """
    Test command injection protection (Week 2 security fixes).

    These tests verify that CommandValidator blocks dangerous command patterns
    while still allowing legitimate command usage.
    """

    def test_semicolon_command_chaining_blocked(self, tmp_path):
        """
        SECURITY FIX: Semicolon command chaining is now blocked.
        """
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("echo 'first'; echo 'second'")

            assert "command chaining with semicolon" in str(exc_info.value)
        finally:
            terminal.close()

    def test_pipe_command_still_works(self, tmp_path):
        """
        Pipe commands are allowed by default as they are legitimate Unix usage.

        CommandValidator allows pipes but validates both sides.
        """
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            result = terminal.execute("echo 'hello world' | grep 'hello'")
            assert "hello" in result
        finally:
            terminal.close()

    def test_background_command_blocked(self, tmp_path):
        """
        SECURITY FIX: Background commands are now blocked.
        """
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("sleep 0.1 &")

            assert "background execution" in str(exc_info.value)
        finally:
            terminal.close()

    def test_command_substitution_blocked(self, tmp_path):
        """
        SECURITY FIX: Command substitution is now blocked.
        """
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("echo $(echo 'substituted')")

            assert "command substitution" in str(exc_info.value)
        finally:
            terminal.close()

    def test_safe_redirection_works(self, tmp_path):
        """
        Safe file redirection within project directory is allowed.
        """
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            terminal.execute("echo 'content' > testfile.txt")
            result = terminal.execute("cat testfile.txt")
            assert "content" in result
        finally:
            terminal.close()

    def test_and_operator_blocked(self, tmp_path):
        """
        SECURITY FIX: && command chaining is now blocked.
        """
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("mkdir test && cd test")

            assert "command chaining with &&" in str(exc_info.value)
        finally:
            terminal.close()

    def test_or_operator_blocked(self, tmp_path):
        """
        SECURITY FIX: || command chaining is now blocked.
        """
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("test -f file || touch file")

            assert "command chaining with ||" in str(exc_info.value)
        finally:
            terminal.close()


class TestBashTerminalErrorHandling:
    """Test error handling and edge cases."""

    def test_command_not_found(self):
        """Test handling of non-existent commands."""
        terminal = BashTerminal()
        try:
            result = terminal.execute("nonexistentcommand12345")
            # Bash will output error message
            assert "command not found" in result.lower() or "nonexistentcommand" in result
        finally:
            terminal.close()

    def test_command_with_error_exit_code(self, tmp_path):
        """Test command that exits with error code."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            # Try to cat a non-existent file
            result = terminal.execute("cat nonexistent_file.txt")
            # Should contain error message
            assert "no such file" in result.lower() or "cannot" in result.lower()
        finally:
            terminal.close()

    def test_empty_command(self):
        """Test that empty commands are rejected by validator."""
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal()
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("")

            assert "Empty command" in str(exc_info.value)
        finally:
            terminal.close()

    def test_command_with_only_whitespace(self):
        """Test that whitespace-only commands are rejected by validator."""
        from deer_code.tools.terminal.command_validator import CommandValidationError

        terminal = BashTerminal()
        try:
            with pytest.raises(CommandValidationError) as exc_info:
                terminal.execute("   ")

            assert "Empty command" in str(exc_info.value)
        finally:
            terminal.close()


class TestBashTerminalResourceManagement:
    """Test resource cleanup and management."""

    def test_close_terminates_shell(self):
        """Test that close() terminates the shell process."""
        terminal = BashTerminal()
        assert terminal.shell.isalive()

        terminal.close()
        # Shell should be terminated
        assert not terminal.shell.isalive()

    def test_double_close_is_safe(self):
        """Test that calling close() twice doesn't raise errors."""
        terminal = BashTerminal()
        terminal.close()
        # Second close should not raise exception
        terminal.close()

    def test_context_manager_closes_shell(self):
        """Test that using context manager properly closes shell."""
        with BashTerminal() as terminal:
            assert terminal.shell.isalive()
            shell = terminal.shell

        # After exiting context, shell should be closed
        assert not shell.isalive()

    def test_context_manager_with_exception(self, tmp_path):
        """Test context manager closes shell even with exception."""
        try:
            with BashTerminal(cwd=str(tmp_path)) as terminal:
                shell = terminal.shell
                assert terminal.shell.isalive()
                # Raise exception
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Shell should still be closed
        assert not shell.isalive()


class TestBashTerminalEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_long_output_handling(self, tmp_path):
        """Test handling of commands with long output."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            # Generate long output
            result = terminal.execute("seq 1 100")
            lines = result.strip().split("\n")
            # Should have 100 lines
            assert len(lines) >= 90  # Allow some variance for output formatting
        finally:
            terminal.close()

    def test_command_with_quotes(self, tmp_path):
        """Test command containing quotes."""
        terminal = BashTerminal(cwd=str(tmp_path))
        try:
            result = terminal.execute('echo "hello \\"world\\""')
            assert "hello" in result
            assert "world" in result
        finally:
            terminal.close()

    def test_environment_variable_access(self):
        """Test accessing environment variables."""
        terminal = BashTerminal()
        try:
            result = terminal.execute("echo $HOME")
            # Should output the home directory
            assert len(result) > 0
            assert "/" in result  # Unix path
        finally:
            terminal.close()

    def test_command_with_unicode(self):
        """Test command with unicode characters."""
        terminal = BashTerminal()
        try:
            result = terminal.execute("echo '你好世界 🚀'")
            assert "你好世界" in result or "🚀" in result
        finally:
            terminal.close()


class TestBashTerminalTimeout:
    """Test timeout handling."""

    def test_fast_command_completes_within_timeout(self):
        """Test that fast commands complete successfully."""
        terminal = BashTerminal()
        try:
            # This should complete well within 30s timeout
            result = terminal.execute("echo 'quick'")
            assert "quick" in result
        finally:
            terminal.close()

    @pytest.mark.slow
    def test_slow_command_with_default_timeout(self):
        """Test command that takes longer time but within default timeout."""
        terminal = BashTerminal()
        try:
            # Sleep for 2 seconds (well within 30s timeout)
            terminal.execute("sleep 2")
            # Then verify terminal still works
            result = terminal.execute("echo 'done'")
            assert "done" in result
        finally:
            terminal.close()

    @pytest.mark.slow
    def test_very_slow_command_timeout(self):
        """
        Test that commands exceeding timeout raise an exception.

        NOTE: Default timeout is 30 seconds. This test is marked slow
        and will timeout, which is expected behavior.
        """
        terminal = BashTerminal()
        try:
            # This will timeout (trying to sleep for 35 seconds)
            with pytest.raises(Exception):  # pexpect.TIMEOUT
                terminal.execute("sleep 35")
        finally:
            terminal.close()
