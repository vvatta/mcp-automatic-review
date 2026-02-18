"""
Static analysis and dependency scanner for MCP servers.
Integrates Trivy and OSV-Scanner to detect vulnerabilities.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from rich.console import Console

console = Console()


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""

    package_name: str
    installed_version: str
    vulnerability_id: str
    severity: SeverityLevel
    title: str
    description: str
    fixed_version: Optional[str] = None


@dataclass
class ScanResult:
    """Results from static analysis scan."""

    path: str
    vulnerabilities: List[Vulnerability]
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int


class StaticScanner:
    """Performs static analysis and dependency scanning."""

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.results_dir = self.workspace_path / "reports"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def scan_with_trivy(self) -> Optional[ScanResult]:
        """
        Run Trivy filesystem scan.

        Returns:
            ScanResult with vulnerabilities found
        """
        console.print("[bold blue]Running Trivy scan...[/bold blue]")

        output_file = self.results_dir / "trivy-report.json"

        try:
            # Run Trivy scan
            cmd = [
                "trivy",
                "fs",
                "--format",
                "json",
                "--output",
                str(output_file),
                "--severity",
                "CRITICAL,HIGH,MEDIUM,LOW",
                str(self.workspace_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0 and not output_file.exists():
                console.print(f"[red]Trivy scan failed: {result.stderr}[/red]")
                return None

            # Parse results
            with open(output_file, "r") as f:
                trivy_data = json.load(f)

            return self._parse_trivy_results(trivy_data)

        except subprocess.TimeoutExpired:
            console.print("[red]Trivy scan timed out[/red]")
            return None
        except FileNotFoundError:
            console.print("[yellow]Trivy not installed. Install with: brew install trivy[/yellow]")
            return None
        except Exception as e:
            console.print(f"[red]Error running Trivy: {e}[/red]")
            return None

    def _parse_trivy_results(self, trivy_data: Dict[str, Any]) -> ScanResult:
        """Parse Trivy JSON output into ScanResult."""
        vulnerabilities = []

        results = trivy_data.get("Results", [])
        for result in results:
            vulns = result.get("Vulnerabilities", [])

            for vuln in vulns:
                vulnerabilities.append(
                    Vulnerability(
                        package_name=vuln.get("PkgName", "unknown"),
                        installed_version=vuln.get("InstalledVersion", "unknown"),
                        vulnerability_id=vuln.get("VulnerabilityID", "unknown"),
                        severity=SeverityLevel(vuln.get("Severity", "UNKNOWN")),
                        title=vuln.get("Title", ""),
                        description=vuln.get("Description", ""),
                        fixed_version=vuln.get("FixedVersion"),
                    )
                )

        # Count by severity
        severity_counts = {
            SeverityLevel.CRITICAL: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0,
        }

        for vuln in vulnerabilities:
            if vuln.severity in severity_counts:
                severity_counts[vuln.severity] += 1

        return ScanResult(
            path=str(self.workspace_path),
            vulnerabilities=vulnerabilities,
            total_count=len(vulnerabilities),
            critical_count=severity_counts[SeverityLevel.CRITICAL],
            high_count=severity_counts[SeverityLevel.HIGH],
            medium_count=severity_counts[SeverityLevel.MEDIUM],
            low_count=severity_counts[SeverityLevel.LOW],
        )

    def check_permissions_manifest(self) -> Dict[str, Any]:
        """
        Check package.json or pyproject.toml for suspicious permissions.

        Returns:
            Dict with permission analysis
        """
        console.print("[bold blue]Checking permissions manifest...[/bold blue]")

        findings = {
            "suspicious_dependencies": [],
            "dangerous_permissions": [],
            "recommendations": [],
        }

        # Check package.json (Node.js)
        package_json = self.workspace_path / "package.json"
        if package_json.exists():
            findings.update(self._check_node_permissions(package_json))

        # Check pyproject.toml (Python)
        pyproject = self.workspace_path / "pyproject.toml"
        if pyproject.exists():
            findings.update(self._check_python_permissions(pyproject))

        # Check requirements.txt (Python)
        requirements = self.workspace_path / "requirements.txt"
        if requirements.exists():
            findings.update(self._check_requirements_permissions(requirements))

        return findings

    def _check_node_permissions(self, package_json: Path) -> Dict[str, List[str]]:
        """Check Node.js package.json for suspicious dependencies."""
        findings = {"suspicious_dependencies": [], "dangerous_permissions": []}

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            # Dangerous Node.js modules
            dangerous_modules = {
                "child_process": "Can execute system commands",
                "fs": "Can access filesystem",
                "net": "Can create network connections",
                "dgram": "Can send UDP packets",
                "crypto": "Cryptographic operations (check if needed)",
            }

            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))

            for dep in all_deps:
                if dep in dangerous_modules:
                    findings["dangerous_permissions"].append(f"{dep}: {dangerous_modules[dep]}")

        except Exception as e:
            console.print(f"[yellow]Error checking package.json: {e}[/yellow]")

        return findings

    def _check_python_permissions(self, pyproject: Path) -> Dict[str, List[str]]:
        """Check Python pyproject.toml for suspicious dependencies."""
        findings = {"suspicious_dependencies": [], "dangerous_permissions": []}

        try:
            import tomli

            with open(pyproject, "rb") as f:
                data = tomli.load(f)

            # Dangerous Python modules
            dangerous_modules = {
                "subprocess": "Can execute system commands",
                "os": "Can access operating system",
                "requests": "Can make HTTP requests",
                "socket": "Can create network connections",
                "paramiko": "SSH client - can connect remotely",
            }

            deps = data.get("project", {}).get("dependencies", [])

            for dep in deps:
                dep_name = dep.split("[")[0].split(">=")[0].split("==")[0].strip()
                if dep_name in dangerous_modules:
                    findings["dangerous_permissions"].append(
                        f"{dep_name}: {dangerous_modules[dep_name]}"
                    )

        except Exception as e:
            console.print(f"[yellow]Error checking pyproject.toml: {e}[/yellow]")

        return findings

    def _check_requirements_permissions(self, requirements: Path) -> Dict[str, List[str]]:
        """Check Python requirements.txt for suspicious dependencies."""
        findings = {"suspicious_dependencies": [], "dangerous_permissions": []}

        try:
            with open(requirements, "r") as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            # Common suspicious packages
            suspicious = [
                "requests",
                "httpx",
                "aiohttp",  # Network access
                "paramiko",
                "fabric",  # SSH
                "boto3",
                "google-cloud",  # Cloud APIs
            ]

            for dep in deps:
                dep_name = dep.split(">=")[0].split("==")[0].strip()
                if any(susp in dep_name.lower() for susp in suspicious):
                    findings["suspicious_dependencies"].append(dep_name)

        except Exception as e:
            console.print(f"[yellow]Error checking requirements.txt: {e}[/yellow]")

        return findings

    def generate_sbom(self) -> Optional[str]:
        """
        Generate Software Bill of Materials (SBOM).

        Returns:
            Path to SBOM file
        """
        console.print("[bold blue]Generating SBOM...[/bold blue]")

        sbom_file = self.results_dir / "sbom.json"

        try:
            cmd = [
                "trivy",
                "fs",
                "--format",
                "cyclonedx",
                "--output",
                str(sbom_file),
                str(self.workspace_path),
            ]

            subprocess.run(cmd, capture_output=True, timeout=120)

            if sbom_file.exists():
                console.print(f"[green]SBOM generated: {sbom_file}[/green]")
                return str(sbom_file)

        except Exception as e:
            console.print(f"[yellow]Could not generate SBOM: {e}[/yellow]")

        return None
