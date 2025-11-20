"""Tests for prompts/template.py module."""

import os
from pathlib import Path

import pytest
from jinja2 import TemplateNotFound

from deer_code.prompts.template import apply_prompt_template


@pytest.fixture
def test_templates_dir(tmp_path):
    """Create a temporary templates directory with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a simple test template
    simple_template = templates_dir / "test_simple.md"
    simple_template.write_text("Hello, World!")

    # Create a template with variables
    variable_template = templates_dir / "test_variables.md"
    variable_template.write_text("Hello, {{ name }}! You are {{ age }} years old.")

    # Create a template with conditionals
    conditional_template = templates_dir / "test_conditional.md"
    conditional_template.write_text(
        "{% if show_greeting %}Hello!{% else %}Goodbye!{% endif %}"
    )

    # Create a template with loops
    loop_template = templates_dir / "test_loop.md"
    loop_template.write_text(
        "{% for item in items %}- {{ item }}\n{% endfor %}"
    )

    return templates_dir


@pytest.mark.unit
class TestApplyPromptTemplate:
    """Tests for apply_prompt_template function."""

    def test_render_simple_template(self, monkeypatch, test_templates_dir):
        """Test rendering a simple template without variables."""
        # Monkeypatch the template directory location
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            result = apply_prompt_template("test_simple")
            assert result == "Hello, World!"
        finally:
            template_module.__file__ = original_file

    def test_render_template_with_variables(self, monkeypatch, test_templates_dir):
        """Test rendering template with variable substitution."""
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            result = apply_prompt_template("test_variables", name="Alice", age=30)
            assert result == "Hello, Alice! You are 30 years old."
        finally:
            template_module.__file__ = original_file

    def test_render_template_with_conditional(self, monkeypatch, test_templates_dir):
        """Test rendering template with conditional logic."""
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            # Test with True condition
            result = apply_prompt_template("test_conditional", show_greeting=True)
            assert result == "Hello!"

            # Test with False condition
            result = apply_prompt_template("test_conditional", show_greeting=False)
            assert result == "Goodbye!"
        finally:
            template_module.__file__ = original_file

    def test_render_template_with_loop(self, monkeypatch, test_templates_dir):
        """Test rendering template with loops."""
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            items = ["apple", "banana", "cherry"]
            result = apply_prompt_template("test_loop", items=items)
            assert result == "- apple\n- banana\n- cherry\n"
        finally:
            template_module.__file__ = original_file

    def test_render_template_with_empty_loop(self, monkeypatch, test_templates_dir):
        """Test rendering template with empty loop."""
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            result = apply_prompt_template("test_loop", items=[])
            assert result == ""
        finally:
            template_module.__file__ = original_file

    def test_render_nonexistent_template(self, monkeypatch, test_templates_dir):
        """Test that TemplateNotFound is raised for missing templates."""
        import deer_code.prompts.template as template_module
        original_file = template_module.__file__
        template_module.__file__ = str(test_templates_dir.parent / "template.py")

        try:
            with pytest.raises(TemplateNotFound):
                apply_prompt_template("nonexistent_template")
        finally:
            template_module.__file__ = original_file

    def test_render_real_coding_agent_template(self):
        """Test rendering the actual coding_agent.md template."""
        # This test uses the real template from the project
        result = apply_prompt_template("coding_agent", PROJECT_ROOT="/test/path")

        # Verify the template was rendered and contains expected content
        assert isinstance(result, str)
        assert len(result) > 0
        assert "/test/path" in result  # Check that variable substitution worked

    def test_render_real_research_agent_template(self):
        """Test rendering the actual research_agent.md template."""
        # This test uses the real template from the project
        result = apply_prompt_template("research_agent")

        # Verify the template was rendered
        assert isinstance(result, str)
        assert len(result) > 0
