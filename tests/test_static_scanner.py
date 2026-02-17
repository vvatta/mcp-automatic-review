"""
Test the static scanner module.
"""
import pytest
from pathlib import Path
from src.inspector.static_scanner import StaticScanner


def test_static_scanner_init():
    """Test StaticScanner initialization."""
    scanner = StaticScanner("/tmp/test")
    assert scanner.workspace_path == Path("/tmp/test")
    assert scanner.results_dir.name == "reports"


def test_check_permissions_manifest(tmp_path):
    """Test permissions manifest checking."""
    # Create a temporary package.json
    package_json = tmp_path / "package.json"
    package_json.write_text("""
    {
        "dependencies": {
            "child_process": "^1.0.0"
        }
    }
    """)
    
    scanner = StaticScanner(str(tmp_path))
    permissions = scanner.check_permissions_manifest()
    
    assert "dangerous_permissions" in permissions
    # Should detect child_process as dangerous


def test_check_python_requirements(tmp_path):
    """Test Python requirements checking."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.28.0\nparamiko>=3.0.0\n")
    
    scanner = StaticScanner(str(tmp_path))
    permissions = scanner.check_permissions_manifest()
    
    assert "suspicious_dependencies" in permissions
