"""
Parse MCP configuration from text file.

This module provides functionality to parse MCP test configuration files
from the MCP-list directory.
"""

import re
from pathlib import Path
from typing import Dict, Optional


def parse_config_file(config_path: str) -> Dict[str, Optional[str]]:
    """
    Parse MCP configuration from a text file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary containing parsed configuration options

    Example config.txt format:
        source: modelcontextprotocol/servers
        ref: main
        version: 1.0.0
        source_type: github
        server_url: http://localhost:8000
    """
    config = {
        "source": None,
        "ref": None,
        "version": None,
        "source_type": None,
        "server_url": None,
        "anthropic_key": None,
    }

    with open(config_path, "r") as f:
        for line in f:
            # Strip whitespace and skip comments/empty lines
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse key: value format
            match = re.match(r"^(\w+):\s*(.+)$", line)
            if match:
                key, value = match.groups()
                key = key.lower()
                value = value.strip()

                if key in config:
                    config[key] = value

    # Validate required fields
    if not config["source"]:
        raise ValueError("Configuration file must specify 'source'")

    return config


def find_mcp_configs(base_path: str = "MCP-list") -> Dict[str, Dict[str, Optional[str]]]:
    """
    Find all MCP configurations in the MCP-list directory.

    Args:
        base_path: Base directory containing MCP configurations

    Returns:
        Dictionary mapping MCP names to their configurations
    """
    base_dir = Path(base_path)
    if not base_dir.exists():
        return {}

    configs = {}
    for mcp_dir in base_dir.iterdir():
        if not mcp_dir.is_dir():
            continue

        config_file = mcp_dir / "config.txt"
        if config_file.exists():
            try:
                config = parse_config_file(str(config_file))
                configs[mcp_dir.name] = config
            except Exception as e:
                print(f"Warning: Failed to parse config for {mcp_dir.name}: {e}")

    return configs


def get_changed_mcp_configs(changed_files: list) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Get MCP configurations for changed files in a PR.

    Args:
        changed_files: List of changed file paths

    Returns:
        Dictionary mapping MCP names to their configurations
    """
    mcp_names = set()

    for file_path in changed_files:
        # Check if file is in MCP-list directory
        if file_path.startswith("MCP-list/"):
            parts = file_path.split("/")
            if len(parts) >= 2:
                mcp_name = parts[1]
                mcp_names.add(mcp_name)

    configs = {}
    for mcp_name in mcp_names:
        config_file = Path("MCP-list") / mcp_name / "config.txt"
        if config_file.exists():
            try:
                config = parse_config_file(str(config_file))
                configs[mcp_name] = config
            except Exception as e:
                print(f"Warning: Failed to parse config for {mcp_name}: {e}")

    return configs


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        try:
            config = parse_config_file(config_path)
            print("Parsed configuration:")
            for key, value in config.items():
                if value:
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Find all configs
        configs = find_mcp_configs()
        print(f"Found {len(configs)} MCP configurations:")
        for mcp_name, config in configs.items():
            print(f"\n{mcp_name}:")
            print(f"  source: {config['source']}")
