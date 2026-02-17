"""
Abstract base class for MCP sources.
Defines interface for fetching and installing MCP servers from various sources.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class SourceType(str, Enum):
    """Type of MCP source."""
    LOCAL = "local"
    GITHUB = "github"
    NPM = "npm"
    PYPI = "pypi"


@dataclass
class MCPConfig:
    """Configuration for an MCP server."""
    name: str
    source_type: SourceType
    source_reference: str  # Path, URL, or package name
    version: Optional[str] = None
    ref: Optional[str] = None  # Branch, tag, or commit for GitHub
    workspace_path: Optional[Path] = None  # Local path after installation


class MCPSource(ABC):
    """
    Abstract base class for MCP sources.
    
    Implementations should handle fetching and installing MCP servers
    from their respective sources (local, GitHub, npm, PyPI, etc.).
    """
    
    def __init__(self, config: MCPConfig):
        self.config = config
    
    @abstractmethod
    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        Fetch and install the MCP server to target directory.
        
        Args:
            target_dir: Directory to install the MCP server
            
        Returns:
            Path to the installed workspace
            
        Raises:
            Exception if fetch/install fails
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up any temporary resources created during installation.
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that the source reference is valid.
        
        Returns:
            True if valid, False otherwise
        """
        pass
