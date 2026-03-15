"""
Remote URL source for MCP servers.
Handles cloud-hosted MCP servers accessible via HTTP/HTTPS endpoints
(e.g., https://mcp.atlassian.com/v1/mcp).
"""

import re
import tempfile
from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType


class UrlSource(MCPSource):
    """
    Source for remote/cloud-hosted MCP servers reachable via HTTP/HTTPS.

    Unlike local, GitHub, npm, or PyPI sources, URL sources represent servers
    that are already running remotely.  There is no code to clone or install —
    the URL is used directly as the MCP server endpoint for live testing.

    Supports:
    - Full HTTPS URLs: https://mcp.atlassian.com/v1/mcp
    - Full HTTP URLs:  http://localhost:8080/mcp
    - url: prefix:    url:https://mcp.atlassian.com/v1/mcp
    """

    URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

    def __init__(
        self,
        url: str,
        auth_token: Optional[str] = None,
    ):
        """
        Initialize URL source.

        Args:
            url: Full HTTP/HTTPS URL of the remote MCP server
            auth_token: Optional API token for authenticated endpoints
        """
        # Normalise — strip any leading 'url:' prefix
        if url.lower().startswith("url:"):
            url = url[4:]

        # Derive a friendly name from the host + path
        name = self._derive_name(url)

        config = MCPConfig(
            name=name,
            source_type=SourceType.URL,
            source_reference=url,
            auth_token=auth_token,
        )
        super().__init__(config)

        self.url = url

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_name(url: str) -> str:
        """Create a short, filesystem-safe name from a URL."""
        # Strip scheme
        name = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        # Replace non-alphanumeric characters with '-'
        name = re.sub(r"[^a-zA-Z0-9]", "-", name)
        # Collapse repeated dashes and strip leading/trailing dashes
        name = re.sub(r"-{2,}", "-", name).strip("-")
        return name[:64] or "remote-mcp"

    # ------------------------------------------------------------------
    # MCPSource interface
    # ------------------------------------------------------------------

    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        No installation needed for remote servers.

        Creates a minimal placeholder directory so that the orchestrator
        can still write reports alongside this "workspace".

        Args:
            target_dir: Directory where a workspace folder is created

        Returns:
            Path to the (empty) workspace directory
        """
        if not self.validate():
            raise ValueError(f"Invalid MCP server URL: {self.url}")

        workspace = target_dir / self.config.name
        workspace.mkdir(parents=True, exist_ok=True)

        # Persist the URL so downstream stages can discover the endpoint
        (workspace / "mcp_url.txt").write_text(self.url)
        if self.config.auth_token:
            # Write a placeholder so reports show auth is configured;
            # never write the actual token to disk.
            (workspace / "auth_configured.txt").write_text("auth_token: <configured>\n")

        self.config.workspace_path = workspace
        return workspace

    def cleanup(self) -> None:
        """Remove the placeholder workspace directory if it was created."""
        if self.config.workspace_path and self.config.workspace_path.exists():
            import shutil
            shutil.rmtree(self.config.workspace_path, ignore_errors=True)

    def validate(self) -> bool:
        """
        Validate that the URL is a well-formed HTTP/HTTPS URL.

        Returns:
            True if the URL is valid, False otherwise
        """
        return bool(self.url and self.URL_PATTERN.match(self.url))
