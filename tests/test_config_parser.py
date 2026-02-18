"""
Test MCP configuration parser.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.config_parser import (
    parse_config_file,
    find_mcp_configs,
    get_changed_mcp_configs,
)


class TestConfigParser:
    """Test configuration parser functionality."""

    def test_parse_basic_config(self, tmp_path):
        """Test parsing a basic configuration file."""
        config_file = tmp_path / "config.txt"
        config_file.write_text(
            """
# MCP Configuration
source: modelcontextprotocol/servers
ref: main
"""
        )

        config = parse_config_file(str(config_file))

        assert config["source"] == "modelcontextprotocol/servers"
        assert config["ref"] == "main"
        assert config["version"] is None
        assert config["source_type"] is None

    def test_parse_full_config(self, tmp_path):
        """Test parsing a configuration with all fields."""
        config_file = tmp_path / "config.txt"
        config_file.write_text(
            """
source: npm:my-package
ref: develop
version: 1.0.0
source_type: npm
server_url: http://localhost:8000
anthropic_key: sk-test-123
"""
        )

        config = parse_config_file(str(config_file))

        assert config["source"] == "npm:my-package"
        assert config["ref"] == "develop"
        assert config["version"] == "1.0.0"
        assert config["source_type"] == "npm"
        assert config["server_url"] == "http://localhost:8000"
        assert config["anthropic_key"] == "sk-test-123"

    def test_parse_config_with_comments(self, tmp_path):
        """Test parsing configuration with comments."""
        config_file = tmp_path / "config.txt"
        config_file.write_text(
            """
# This is a comment
source: owner/repo  # Inline comment should be parsed

# Another comment
ref: main
# version: 2.0.0  # This should be ignored
"""
        )

        config = parse_config_file(str(config_file))

        assert config["source"] == "owner/repo  # Inline comment should be parsed"
        assert config["ref"] == "main"
        assert config["version"] is None

    def test_parse_config_missing_source(self, tmp_path):
        """Test that missing source raises an error."""
        config_file = tmp_path / "config.txt"
        config_file.write_text(
            """
ref: main
version: 1.0.0
"""
        )

        with pytest.raises(ValueError, match="must specify 'source'"):
            parse_config_file(str(config_file))

    def test_parse_empty_config(self, tmp_path):
        """Test parsing empty configuration file."""
        config_file = tmp_path / "config.txt"
        config_file.write_text("")

        with pytest.raises(ValueError, match="must specify 'source'"):
            parse_config_file(str(config_file))

    def test_find_mcp_configs(self, tmp_path):
        """Test finding all MCP configurations in a directory."""
        # Create MCP-list directory structure
        mcp_list = tmp_path / "MCP-list"
        mcp_list.mkdir()

        # Create first MCP config
        mcp1 = mcp_list / "mcp1"
        mcp1.mkdir()
        (mcp1 / "config.txt").write_text("source: owner/repo1\nref: main")

        # Create second MCP config
        mcp2 = mcp_list / "mcp2"
        mcp2.mkdir()
        (mcp2 / "config.txt").write_text("source: npm:package2")

        # Create directory without config (should be ignored)
        mcp3 = mcp_list / "mcp3"
        mcp3.mkdir()

        # Change to temp directory and find configs
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            configs = find_mcp_configs()

            assert len(configs) == 2
            assert "mcp1" in configs
            assert "mcp2" in configs
            assert "mcp3" not in configs

            assert configs["mcp1"]["source"] == "owner/repo1"
            assert configs["mcp1"]["ref"] == "main"

            assert configs["mcp2"]["source"] == "npm:package2"
        finally:
            os.chdir(original_cwd)

    def test_find_mcp_configs_empty_directory(self, tmp_path):
        """Test finding configs in empty directory."""
        mcp_list = tmp_path / "MCP-list"
        mcp_list.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            configs = find_mcp_configs()
            assert len(configs) == 0
        finally:
            os.chdir(original_cwd)

    def test_find_mcp_configs_missing_directory(self, tmp_path):
        """Test finding configs when directory doesn't exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            configs = find_mcp_configs()
            assert len(configs) == 0
        finally:
            os.chdir(original_cwd)

    def test_get_changed_mcp_configs(self, tmp_path):
        """Test getting configs for changed files."""
        # Create MCP-list directory structure
        mcp_list = tmp_path / "MCP-list"
        mcp_list.mkdir()

        mcp1 = mcp_list / "changed-mcp"
        mcp1.mkdir()
        (mcp1 / "config.txt").write_text("source: owner/repo")

        mcp2 = mcp_list / "unchanged-mcp"
        mcp2.mkdir()
        (mcp2 / "config.txt").write_text("source: npm:package")

        changed_files = [
            "MCP-list/changed-mcp/config.txt",
            "MCP-list/changed-mcp/results.json",
            "README.md",
            "src/cli.py",
        ]

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            configs = get_changed_mcp_configs(changed_files)

            assert len(configs) == 1
            assert "changed-mcp" in configs
            assert "unchanged-mcp" not in configs
            assert configs["changed-mcp"]["source"] == "owner/repo"
        finally:
            os.chdir(original_cwd)

    def test_get_changed_mcp_configs_no_mcp_changes(self, tmp_path):
        """Test getting configs when no MCP files changed."""
        changed_files = [
            "README.md",
            "src/cli.py",
            "tests/test_installer.py",
        ]

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            configs = get_changed_mcp_configs(changed_files)
            assert len(configs) == 0
        finally:
            os.chdir(original_cwd)

    def test_parse_config_whitespace_handling(self, tmp_path):
        """Test that whitespace is properly handled."""
        config_file = tmp_path / "config.txt"
        config_file.write_text(
            """

source:   owner/repo  
ref:    main    

version: 1.0.0

"""
        )

        config = parse_config_file(str(config_file))

        assert config["source"] == "owner/repo"
        assert config["ref"] == "main"
        assert config["version"] == "1.0.0"
