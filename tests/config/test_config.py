"""Tests for config/config.py module."""

import os
from unittest.mock import patch, mock_open

import pytest
import yaml

from deer_code.config.config import load_config, get_config_section


@pytest.mark.unit
class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_returns_dict(self):
        """Test that load_config returns a dictionary."""
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_expected_structure(self):
        """Test that loaded config has expected top-level keys."""
        config = load_config()
        # Config created by conftest should have these keys
        assert "models" in config or "tools" in config

    def test_load_config_caching(self):
        """Test that config is cached (returns same object)."""
        config1 = load_config()
        config2 = load_config()
        # Should return the same cached object
        assert config1 is config2


@pytest.mark.unit
class TestGetConfigSection:
    """Tests for get_config_section function."""

    def test_get_config_section_with_existing_key(self):
        """Test getting an existing config section."""
        # Get a section that exists in the loaded config
        models_section = get_config_section("models")
        # Should return a dict (not None) if models section exists
        assert models_section is not None or models_section == {}

    def test_get_config_section_with_nested_list_key(self):
        """Test getting config with list of keys."""
        # Try to get models.chat_model
        result = get_config_section(["models", "chat_model"])
        # Should either return the section or None
        assert result is None or isinstance(result, dict)

    def test_get_config_section_nonexistent_key(self):
        """Test that None is returned for nonexistent keys."""
        result = get_config_section("this_key_definitely_does_not_exist_12345")
        assert result is None

    def test_get_config_section_partial_path_missing(self):
        """Test that None is returned when part of the path doesn't exist."""
        result = get_config_section(["nonexistent_parent", "nonexistent_child"])
        assert result is None

    def test_get_config_section_with_string_key_type(self):
        """Test that get_config_section accepts string keys."""
        # Should not raise an error
        result = get_config_section("any_string_key")
        # Result can be None or a dict
        assert result is None or isinstance(result, dict)

    def test_get_config_section_with_list_key_type(self):
        """Test that get_config_section accepts list keys."""
        # Should not raise an error
        result = get_config_section(["key1", "key2"])
        # Result can be None or a dict
        assert result is None or isinstance(result, dict)
