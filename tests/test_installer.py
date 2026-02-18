"""
Test the MCP source installer modules.
"""

import pytest
from pathlib import Path
from src.installer.local_source import LocalSource
from src.installer.github_source import GitHubSource
from src.installer.npm_source import NpmSource
from src.installer.pypi_source import PyPiSource
from src.installer.source_factory import MCPSourceFactory
from src.installer.mcp_source import SourceType


class TestLocalSource:
    """Test LocalSource."""

    def test_init(self, tmp_path):
        """Test LocalSource initialization."""
        source = LocalSource(str(tmp_path))
        assert source.config.source_type == SourceType.LOCAL
        assert source.config.workspace_path == tmp_path.resolve()

    def test_validate_exists(self, tmp_path):
        """Test validation with existing path."""
        source = LocalSource(str(tmp_path))
        assert source.validate() is True

    def test_validate_not_exists(self):
        """Test validation with non-existing path."""
        source = LocalSource("/nonexistent/path")
        assert source.validate() is False

    @pytest.mark.asyncio
    async def test_fetch_and_install(self, tmp_path):
        """Test fetch and install returns the local path."""
        source = LocalSource(str(tmp_path))
        workspace = await source.fetch_and_install(Path("/tmp"))
        assert workspace == tmp_path.resolve()


class TestGitHubSource:
    """Test GitHubSource."""

    def test_parse_full_url(self):
        """Test parsing full GitHub URL."""
        source = GitHubSource("https://github.com/owner/repo")
        assert source.owner == "owner"
        assert source.repo == "repo"

    def test_parse_short_reference(self):
        """Test parsing short GitHub reference."""
        source = GitHubSource("owner/repo")
        assert source.owner == "owner"
        assert source.repo == "repo"

    def test_parse_url_with_git_extension(self):
        """Test parsing URL with .git extension."""
        source = GitHubSource("https://github.com/owner/repo.git")
        assert source.owner == "owner"
        assert source.repo == "repo"

    def test_invalid_reference(self):
        """Test invalid GitHub reference."""
        with pytest.raises(ValueError):
            GitHubSource("invalid-reference")

    def test_validate(self):
        """Test validation."""
        source = GitHubSource("owner/repo")
        assert source.validate() is True

    def test_git_url_construction(self):
        """Test git URL construction."""
        source = GitHubSource("owner/repo")
        assert source.git_url == "https://github.com/owner/repo.git"


class TestNpmSource:
    """Test NpmSource."""

    def test_init_simple(self):
        """Test simple package name."""
        source = NpmSource("my-package")
        assert source.package_name == "my-package"
        assert source.package_version == "latest"

    def test_init_with_version(self):
        """Test package name with version."""
        source = NpmSource("my-package@1.0.0")
        assert source.package_name == "my-package"
        assert source.package_version == "1.0.0"

    def test_init_explicit_version(self):
        """Test explicit version parameter."""
        source = NpmSource("my-package", version="2.0.0")
        assert source.package_name == "my-package"
        assert source.package_version == "2.0.0"

    def test_validate(self):
        """Test validation."""
        source = NpmSource("my-package")
        assert source.validate() is True

        source = NpmSource("")
        assert source.validate() is False


class TestPyPiSource:
    """Test PyPiSource."""

    def test_init_simple(self):
        """Test simple package name."""
        source = PyPiSource("my-package")
        assert source.package_name == "my-package"
        assert source.package_version is None

    def test_init_with_version(self):
        """Test explicit version."""
        source = PyPiSource("my-package", version="==1.0.0")
        assert source.package_name == "my-package"
        assert source.package_version == "==1.0.0"

    def test_validate(self):
        """Test validation."""
        source = PyPiSource("my-package")
        assert source.validate() is True

        source = PyPiSource("")
        assert source.validate() is False


class TestMCPSourceFactory:
    """Test MCPSourceFactory."""

    def test_local_path_absolute(self, tmp_path):
        """Test local absolute path detection."""
        source = MCPSourceFactory.create_source(str(tmp_path))
        assert isinstance(source, LocalSource)
        assert source.config.source_type == SourceType.LOCAL

    def test_local_path_relative(self):
        """Test local relative path detection."""
        source = MCPSourceFactory.create_source("./my-path")
        assert isinstance(source, LocalSource)

    def test_github_url(self):
        """Test GitHub URL detection."""
        source = MCPSourceFactory.create_source("https://github.com/owner/repo")
        assert isinstance(source, GitHubSource)
        assert source.config.source_type == SourceType.GITHUB

    def test_github_short(self):
        """Test GitHub short reference detection."""
        source = MCPSourceFactory.create_source("owner/repo")
        assert isinstance(source, GitHubSource)

    def test_npm_prefix(self):
        """Test npm prefix detection."""
        source = MCPSourceFactory.create_source("npm:my-package")
        assert isinstance(source, NpmSource)
        assert source.config.source_type == SourceType.NPM

    def test_npm_version(self):
        """Test npm version detection."""
        source = MCPSourceFactory.create_source("my-package@1.0.0")
        assert isinstance(source, NpmSource)

    def test_pypi_prefix(self):
        """Test PyPI prefix detection."""
        source = MCPSourceFactory.create_source("pypi:my-package")
        assert isinstance(source, PyPiSource)
        assert source.config.source_type == SourceType.PYPI

    def test_pypi_version(self):
        """Test PyPI version detection."""
        source = MCPSourceFactory.create_source("my-package==1.0.0")
        assert isinstance(source, PyPiSource)

    def test_explicit_source_type(self):
        """Test explicit source type."""
        source = MCPSourceFactory.create_source("owner/repo", source_type="github")
        assert isinstance(source, GitHubSource)

        source = MCPSourceFactory.create_source("my-package", source_type="npm")
        assert isinstance(source, NpmSource)

        source = MCPSourceFactory.create_source("my-package", source_type="pypi")
        assert isinstance(source, PyPiSource)

    def test_invalid_source_type(self):
        """Test invalid explicit source type."""
        with pytest.raises(ValueError):
            MCPSourceFactory.create_source("my-ref", source_type="invalid")
