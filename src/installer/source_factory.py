"""
Factory for creating MCP sources from various input formats.
"""

import re
from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource
from src.installer.local_source import LocalSource
from src.installer.github_source import GitHubSource
from src.installer.npm_source import NpmSource
from src.installer.pypi_source import PyPiSource


class MCPSourceFactory:
    """
    Factory for creating appropriate MCP source instances.

    Automatically detects source type from reference string:
    - Local paths: /path/to/mcp-server or ./relative/path
    - GitHub: https://github.com/owner/repo or owner/repo
    - npm: npm:package-name or package-name@version
    - PyPI: pypi:package-name or package-name==version
    """

    # Patterns for source detection
    GITHUB_URL_PATTERN = re.compile(r"^https?://github\.com/")
    GITHUB_SHORT_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$")
    NPM_PREFIX_PATTERN = re.compile(r"^npm:")
    PYPI_PREFIX_PATTERN = re.compile(r"^pypi:")
    NPM_VERSION_PATTERN = re.compile(r"@[\d\w\.\-]+$")
    PYPI_VERSION_PATTERN = re.compile(r"[=<>!]+[\d\w\.\-]+$")

    @classmethod
    def create_source(
        cls,
        reference: str,
        source_type: Optional[str] = None,
        version: Optional[str] = None,
        ref: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
    ) -> MCPSource:
        """
        Create appropriate MCP source from reference string.

        Args:
            reference: Source reference (path, URL, package name)
            source_type: Optional explicit source type (local, github, npm, pypi)
            version: Optional version specification
            ref: Optional git reference (branch/tag/commit) for GitHub
            command: Optional command to execute the MCP server
            args: Optional arguments for the command

        Returns:
            MCPSource instance

        Raises:
            ValueError if source type cannot be determined
        """
        # If source_type is explicitly provided, use it
        if source_type:
            return cls._create_by_type(source_type, reference, version, ref, command, args)

        # Auto-detect source type
        return cls._auto_detect_source(reference, version, ref, command, args)

    @classmethod
    def _create_by_type(
        cls, source_type: str, reference: str, version: Optional[str], ref: Optional[str], command: Optional[str], args: Optional[list[str]]
    ) -> MCPSource:
        """Create source by explicit type."""
        source_type = source_type.lower()

        if source_type == "local":
            return LocalSource(reference, command=command, args=args)
        elif source_type == "github":
            return GitHubSource(reference, ref=ref, version=version, command=command, args=args)
        elif source_type == "npm":
            return NpmSource(reference, version=version, command=command, args=args)
        elif source_type == "pypi":
            return PyPiSource(reference, version=version, command=command, args=args)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    @classmethod
    def _auto_detect_source(
        cls, reference: str, version: Optional[str], ref: Optional[str], command: Optional[str], args: Optional[list[str]]
    ) -> MCPSource:
        """Auto-detect source type from reference string."""

        # Check for explicit prefixes
        if cls.NPM_PREFIX_PATTERN.match(reference):
            package_name = reference[4:]  # Remove 'npm:' prefix
            return NpmSource(package_name, version=version, command=command, args=args)

        if cls.PYPI_PREFIX_PATTERN.match(reference):
            package_name = reference[5:]  # Remove 'pypi:' prefix
            return PyPiSource(package_name, version=version, command=command, args=args)

        # Check for GitHub patterns
        if cls.GITHUB_URL_PATTERN.match(reference):
            return GitHubSource(reference, ref=ref, version=version, command=command, args=args)

        if cls.GITHUB_SHORT_PATTERN.match(reference) and "/" in reference:
            # Could be GitHub short reference, but verify it's not a local path
            if not Path(reference).exists():
                return GitHubSource(reference, ref=ref, version=version, command=command, args=args)

        # Check if it's a local path
        if cls._is_local_path(reference):
            return LocalSource(reference, command=command, args=args)

        # Default fallback - check for version patterns
        if "@" in reference and not reference.startswith("@"):
            # Likely npm package with version
            return NpmSource(reference, version=version, command=command, args=args)

        if any(op in reference for op in ["==", ">=", "<=", ">", "<", "!="]):
            # Likely PyPI package with version
            return PyPiSource(reference, version=version, command=command, args=args)

        # Final fallback: treat as local path
        return LocalSource(reference, command=command, args=args)

    @classmethod
    def _is_local_path(cls, reference: str) -> bool:
        """Check if reference is a local path."""
        # Check for absolute or relative path indicators
        if reference.startswith("/") or reference.startswith("./") or reference.startswith("../"):
            return True

        # Check if path exists
        if Path(reference).exists():
            return True

        # Check for Windows paths
        if len(reference) > 2 and reference[1] == ":":
            return True

        return False
