"""
PyPI registry source for MCP servers.
Handles installing MCP servers from the Python Package Index (PyPI).
"""
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType


class PyPiSource(MCPSource):
    """
    Source for MCP servers published to PyPI.
    
    Supports:
    - Package names: package-name
    - Package with version: package-name==1.0.0
    - Package with version specifier: package-name>=1.0.0
    """
    
    def __init__(self, package_name: str, version: Optional[str] = None):
        """
        Initialize PyPI source.
        
        Args:
            package_name: PyPI package name
            version: Optional version specification (e.g., "==1.0.0", ">=1.0.0")
        """
        config = MCPConfig(
            name=package_name,
            source_type=SourceType.PYPI,
            source_reference=package_name,
            version=version
        )
        super().__init__(config)
        
        self.package_name = package_name
        self.package_version = version
    
    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        Install the PyPI package to target directory using pip.
        
        Args:
            target_dir: Directory to install the package
            
        Returns:
            Path to the installed workspace
            
        Raises:
            Exception if pip install fails
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        workspace = target_dir / self.config.name
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Create a virtual environment
        venv_path = workspace / ".venv"
        venv_cmd = ["python", "-m", "venv", str(venv_path)]
        
        process = await asyncio.create_subprocess_exec(
            *venv_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        # Build package spec
        if self.package_version:
            package_spec = f"{self.package_name}{self.package_version}"
        else:
            package_spec = self.package_name
        
        # Install package using pip with --target
        pip_target = workspace / "package"
        pip_target.mkdir(exist_ok=True)
        
        install_cmd = [
            "pip", "install",
            package_spec,
            "--target", str(pip_target),
            "--no-cache-dir"
        ]
        
        # Run pip install
        process = await asyncio.create_subprocess_exec(
            *install_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"pip install failed: {error_msg}")
        
        # Update config with workspace path
        self.config.workspace_path = pip_target
        
        return pip_target
    
    def cleanup(self) -> None:
        """Clean up installed PyPI package."""
        if self.config.workspace_path:
            # Remove the parent workspace
            workspace_root = self.config.workspace_path.parent
            if workspace_root.exists() and workspace_root.name == self.config.name:
                shutil.rmtree(workspace_root)
    
    def validate(self) -> bool:
        """
        Validate that the package name is properly formatted.
        
        Returns:
            True if package name is valid, False otherwise
        """
        # Basic validation - PyPI package names should not be empty
        return bool(self.package_name and len(self.package_name) > 0)
