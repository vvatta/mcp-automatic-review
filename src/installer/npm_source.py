"""
npm registry source for MCP servers.
Handles installing MCP servers from the npm registry.
"""
import asyncio
import shutil
from pathlib import Path
from typing import Optional

from src.installer.mcp_source import MCPSource, MCPConfig, SourceType


class NpmSource(MCPSource):
    """
    Source for MCP servers published to npm registry.
    
    Supports:
    - Package names: package-name
    - Package with version: package-name@1.0.0
    - Package with tag: package-name@latest
    """
    
    def __init__(self, package_name: str, version: Optional[str] = None):
        """
        Initialize npm source.
        
        Args:
            package_name: npm package name (can include @version)
            version: Optional version specification
        """
        # Parse package name and version if included in package_name
        if '@' in package_name and not package_name.startswith('@'):
            name_parts = package_name.rsplit('@', 1)
            pkg_name = name_parts[0]
            pkg_version = version or name_parts[1]
        else:
            pkg_name = package_name
            pkg_version = version or "latest"
        
        config = MCPConfig(
            name=pkg_name,
            source_type=SourceType.NPM,
            source_reference=package_name,
            version=pkg_version
        )
        super().__init__(config)
        
        self.package_name = pkg_name
        self.package_version = pkg_version
    
    async def fetch_and_install(self, target_dir: Path) -> Path:
        """
        Install the npm package to target directory.
        
        Args:
            target_dir: Directory to install the package
            
        Returns:
            Path to the installed workspace
            
        Raises:
            subprocess.CalledProcessError if npm install fails
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        workspace = target_dir / self.config.name
        workspace.mkdir(parents=True, exist_ok=True)
        
        # Create minimal package.json
        package_json = workspace / "package.json"
        package_json.write_text('{"name": "mcp-sandbox-temp", "version": "1.0.0"}\n')
        
        # Build npm install command
        package_spec = f"{self.package_name}@{self.package_version}"
        install_cmd = ["npm", "install", package_spec, "--no-save"]
        
        # Run npm install
        process = await asyncio.create_subprocess_exec(
            *install_cmd,
            cwd=str(workspace),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"npm install failed: {error_msg}")
        
        # The actual package is in node_modules
        installed_package = workspace / "node_modules" / self.package_name
        
        if not installed_package.exists():
            raise FileNotFoundError(f"Package not found after install: {self.package_name}")
        
        # Update config with workspace path (pointing to the installed package)
        self.config.workspace_path = installed_package
        
        return installed_package
    
    def cleanup(self) -> None:
        """Clean up installed npm package."""
        if self.config.workspace_path:
            # Remove the parent workspace (includes node_modules)
            workspace_root = self.config.workspace_path.parent.parent
            if workspace_root.exists() and workspace_root.name == self.config.name:
                shutil.rmtree(workspace_root)
    
    def validate(self) -> bool:
        """
        Validate that the package name is properly formatted.
        
        Returns:
            True if package name is valid, False otherwise
        """
        # Basic validation - npm package names should not be empty
        return bool(self.package_name and len(self.package_name) > 0)
