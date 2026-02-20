"""
Local filesystem source for MCP servers.
Handles MCP servers that are already on the local filesystem.
"""

from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType


class LocalSource(MCPSource):
    """
    Source for MCP servers on the local filesystem.

    This is used for backward compatibility with the existing CLI
    that accepts local paths.
    """

    def __init__(self, path: str, command: Optional[str] = None, args: Optional[list[str]] = None):
        """
        Initialize local source.

        Args:
            path: Local filesystem path to MCP server
            command: Optional command to execute the MCP server
            args: Optional arguments for the command
        """
        config = MCPConfig(
            name=Path(path).name,
            source_type=SourceType.LOCAL,
            source_reference=path,
            workspace_path=Path(path).resolve(),
            command=command,
            args=args,
        )
        super().__init__(config)

    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        For local sources, just validate and return the path.

        Args:
            target_dir: Ignored for local sources

        Returns:
            Path to the local workspace

        Raises:
            FileNotFoundError if path doesn't exist
        """
        if not self.validate():
            raise FileNotFoundError(f"Local path does not exist: {self.config.source_reference}")

        return self.config.workspace_path

    def cleanup(self) -> None:
        """No cleanup needed for local sources."""
        pass

    def validate(self) -> bool:
        """
        Validate that the local path exists.

        Returns:
            True if path exists, False otherwise
        """
        return self.config.workspace_path.exists()
