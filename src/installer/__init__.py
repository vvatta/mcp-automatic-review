"""
MCP source installer module.
Handles fetching and installing MCP servers from various sources.
"""

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType
from src.installer.local_source import LocalSource
from src.installer.github_source import GitHubSource
from src.installer.npm_source import NpmSource
from src.installer.pypi_source import PyPiSource

__all__ = [
    "MCPSource",
    "MCPConfig",
    "SourceType",
    "LocalSource",
    "GitHubSource",
    "NpmSource",
    "PyPiSource",
]
