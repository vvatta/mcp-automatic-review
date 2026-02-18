"""
GitHub repository source for MCP servers.
Handles cloning and installing MCP servers from GitHub repositories.
"""

import asyncio
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType


class GitHubSource(MCPSource):
    """
    Source for MCP servers hosted on GitHub.

    Supports:
    - Full GitHub URLs: https://github.com/owner/repo
    - GitHub short references: owner/repo
    - Branches, tags, and commit references
    """

    GITHUB_URL_PATTERN = re.compile(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")
    GITHUB_SHORT_PATTERN = re.compile(r"^([^/]+)/([^/]+)$")

    def __init__(self, reference: str, ref: Optional[str] = None, version: Optional[str] = None):
        """
        Initialize GitHub source.

        Args:
            reference: GitHub URL or owner/repo reference
            ref: Optional branch, tag, or commit reference
            version: Optional version string (for metadata)
        """
        owner, repo = self._parse_reference(reference)

        config = MCPConfig(
            name=repo,
            source_type=SourceType.GITHUB,
            source_reference=reference,
            version=version,
            ref=ref,
        )
        super().__init__(config)

        self.owner = owner
        self.repo = repo
        self.git_url = f"https://github.com/{owner}/{repo}.git"

    def _parse_reference(self, reference: str) -> tuple[str, str]:
        """
        Parse GitHub reference to extract owner and repo.

        Args:
            reference: GitHub URL or short reference

        Returns:
            Tuple of (owner, repo)

        Raises:
            ValueError if reference is invalid
        """
        # Try full URL pattern
        match = self.GITHUB_URL_PATTERN.match(reference)
        if match:
            return match.group(1), match.group(2)

        # Try short pattern
        match = self.GITHUB_SHORT_PATTERN.match(reference)
        if match:
            return match.group(1), match.group(2)

        raise ValueError(f"Invalid GitHub reference: {reference}")

    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        Clone the GitHub repository to target directory.

        Args:
            target_dir: Directory to clone the repository into

        Returns:
            Path to the cloned workspace

        Raises:
            subprocess.CalledProcessError if git clone fails
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        workspace = target_dir / self.config.name

        # Build git clone command
        clone_cmd = ["git", "clone", "--depth", "1"]

        if self.config.ref:
            clone_cmd.extend(["--branch", self.config.ref])

        clone_cmd.extend([self.git_url, str(workspace)])

        # Run git clone
        process = await asyncio.create_subprocess_exec(
            *clone_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, clone_cmd, output=stdout, stderr=stderr
            )

        # Update config with workspace path
        self.config.workspace_path = workspace

        # Install dependencies if needed
        await self._install_dependencies(workspace)

        return workspace

    async def _install_dependencies(self, workspace: Path) -> None:
        """
        Install dependencies for the MCP server.

        Args:
            workspace: Path to the workspace
        """
        # Check for package.json (Node.js)
        if (workspace / "package.json").exists():
            npm_install = await asyncio.create_subprocess_exec(
                "npm",
                "install",
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await npm_install.communicate()

        # Check for requirements.txt or pyproject.toml (Python)
        if (workspace / "requirements.txt").exists():
            pip_install = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "-r",
                "requirements.txt",
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await pip_install.communicate()
        elif (workspace / "pyproject.toml").exists():
            pip_install = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "-e",
                ".",
                cwd=str(workspace),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await pip_install.communicate()

    def cleanup(self) -> None:
        """Clean up cloned repository."""
        if self.config.workspace_path and self.config.workspace_path.exists():
            shutil.rmtree(self.config.workspace_path)

    def validate(self) -> bool:
        """
        Validate that the GitHub reference is properly formatted.

        Returns:
            True if reference is valid, False otherwise
        """
        try:
            self._parse_reference(self.config.source_reference)
            return True
        except ValueError:
            return False
