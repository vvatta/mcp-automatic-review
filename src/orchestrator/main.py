"""
Main orchestrator for the MCP malware sandbox.
Coordinates all phases: isolation, inspection, interrogation, and monitoring.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import docker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.inspector.static_scanner import StaticScanner, ScanResult
from src.interrogator.llm_fuzzer import MCPInterrogator, FuzzResult
from src.monitor.behavior_monitor import BehaviorMonitor, BehaviorReport

console = Console()


class SandboxStatus(str, Enum):
    """Status of sandbox execution."""
    INITIALIZING = "INITIALIZING"
    SCANNING = "SCANNING"
    ISOLATING = "ISOLATING"
    INTERROGATING = "INTERROGATING"
    MONITORING = "MONITORING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class SandboxResult:
    """Complete sandbox execution result."""
    status: SandboxStatus
    scan_result: Optional[ScanResult]
    fuzz_results: list[FuzzResult]
    behavior_report: Optional[BehaviorReport]
    overall_risk_score: float
    recommendations: list[str]
    execution_time: float


class MCPSandboxOrchestrator:
    """
    Main orchestrator for MCP malware sandbox.
    
    Workflow:
    1. Ingest - Load MCP server code
    2. Inspect - Static analysis with Trivy
    3. Isolate - Launch in Docker + gVisor
    4. Monitor - eBPF and telemetry
    5. Attack - LLM fuzzing
    6. Report - Generate results
    """

    def __init__(
        self,
        workspace_path: str,
        mcp_server_url: Optional[str] = None,
        anthropic_api_key: Optional[str] = None
    ):
        self.workspace_path = Path(workspace_path)
        self.mcp_server_url = mcp_server_url or "http://localhost:8000"
        self.anthropic_api_key = anthropic_api_key
        
        # Initialize components
        self.scanner = StaticScanner(str(self.workspace_path))
        self.docker_client = docker.from_env()
        
        # Results
        self.scan_result: Optional[ScanResult] = None
        self.fuzz_results: list[FuzzResult] = []
        self.behavior_report: Optional[BehaviorReport] = None

    async def run_complete_analysis(self) -> SandboxResult:
        """
        Run complete malware sandbox analysis.
        
        Returns:
            SandboxResult with all findings
        """
        start_time = time.time()
        
        console.print(Panel.fit(
            "[bold cyan]MCP Malware Sandbox[/bold cyan]\n"
            "Comprehensive Security Analysis",
            border_style="cyan"
        ))
        
        try:
            # Phase 1: Static Analysis
            console.print("\n[bold]Phase 1: Static & Dependency Analysis[/bold]")
            self.scan_result = await self._run_static_analysis()
            
            # Phase 2: Container Isolation
            console.print("\n[bold]Phase 2: Isolation Engine (Docker + gVisor)[/bold]")
            container = await self._setup_isolation()
            
            if not container:
                return self._create_failed_result("Failed to create sandbox", time.time() - start_time)
            
            # Phase 3: Behavioral Monitoring (start)
            console.print("\n[bold]Phase 3: Behavioral Monitoring (Starting)[/bold]")
            monitor = BehaviorMonitor(container.name)
            monitor.start_monitoring()
            
            # Wait for container to be ready
            await asyncio.sleep(5)
            
            # Phase 4: Dynamic Interrogation
            console.print("\n[bold]Phase 4: Dynamic Interrogation (LLM Fuzzing)[/bold]")
            self.fuzz_results = await self._run_interrogation()
            
            # Phase 5: Behavioral Monitoring (collect)
            console.print("\n[bold]Phase 5: Behavioral Monitoring (Collecting)[/bold]")
            self.behavior_report = monitor.generate_report()
            
            # Cleanup container
            await self._cleanup_container(container)
            
            # Phase 6: Generate Final Report
            console.print("\n[bold]Phase 6: Final Report Generation[/bold]")
            result = self._generate_final_result(time.time() - start_time)
            
            self._display_summary(result)
            
            return result
            
        except Exception as e:
            console.print(f"[red]Fatal error: {e}[/red]")
            return self._create_failed_result(str(e), time.time() - start_time)

    async def _run_static_analysis(self) -> Optional[ScanResult]:
        """Run Phase 2: Static & Dependency Analysis."""
        
        # Run Trivy scan
        scan_result = self.scanner.scan_with_trivy()
        
        # Check permissions
        permissions = self.scanner.check_permissions_manifest()
        
        if permissions.get("dangerous_permissions"):
            console.print("[yellow]⚠ Dangerous permissions detected:[/yellow]")
            for perm in permissions["dangerous_permissions"]:
                console.print(f"  - {perm}")
        
        # Generate SBOM
        sbom = self.scanner.generate_sbom()
        
        if scan_result:
            console.print(f"\n[bold]Vulnerability Summary:[/bold]")
            console.print(f"  Critical: {scan_result.critical_count}")
            console.print(f"  High: {scan_result.high_count}")
            console.print(f"  Medium: {scan_result.medium_count}")
            console.print(f"  Low: {scan_result.low_count}")
        
        return scan_result

    async def _setup_isolation(self) -> Optional[docker.models.containers.Container]:
        """Setup Phase 1: Isolation Engine."""
        
        console.print("[blue]Building sandbox container...[/blue]")
        
        try:
            # Check if image exists, build if not
            try:
                self.docker_client.images.get("mcp-sandbox:latest")
            except docker.errors.ImageNotFound:
                console.print("[yellow]Building Docker image...[/yellow]")
                # In real implementation, build from Dockerfile
                console.print("[yellow]Note: Use 'docker-compose build' to build the image[/yellow]")
                return None
            
            # Run container with security restrictions
            container = self.docker_client.containers.run(
                "mcp-sandbox:latest",
                name=f"mcp-sandbox-{int(time.time())}",
                detach=True,
                remove=False,
                network_mode="bridge",
                cap_drop=["ALL"],
                cap_add=["NET_BIND_SERVICE"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "", "/var/tmp": ""},
                environment={
                    "PYTHONUNBUFFERED": "1",
                    "SANDBOX_MODE": "true",
                    "HOME": "/tmp/fake_home"
                }
            )
            
            console.print(f"[green]✓ Container created: {container.name}[/green]")
            return container
            
        except Exception as e:
            console.print(f"[red]Failed to create container: {e}[/red]")
            return None

    async def _run_interrogation(self) -> list[FuzzResult]:
        """Run Phase 3: Dynamic Interrogation."""
        
        interrogator = MCPInterrogator(
            self.mcp_server_url,
            self.anthropic_api_key
        )
        
        try:
            results = await interrogator.run_fuzzing_campaign()
            
            # Summary
            total = len(results)
            with_leaks = sum(1 for r in results if r.leaked_data)
            with_suspicious = sum(1 for r in results if r.suspicious_behavior)
            
            console.print(f"\n[bold]Fuzzing Summary:[/bold]")
            console.print(f"  Total payloads: {total}")
            console.print(f"  Data leaks detected: {with_leaks}")
            console.print(f"  Suspicious behaviors: {with_suspicious}")
            
            return results
            
        finally:
            await interrogator.close()

    async def _cleanup_container(self, container: docker.models.containers.Container) -> None:
        """Cleanup container after analysis."""
        try:
            console.print("[blue]Cleaning up container...[/blue]")
            container.stop(timeout=10)
            container.remove()
            console.print("[green]✓ Container cleaned up[/green]")
        except Exception as e:
            console.print(f"[yellow]Cleanup error: {e}[/yellow]")

    def _calculate_risk_score(self) -> float:
        """
        Calculate overall risk score (0-100).
        
        Returns:
            Risk score as float
        """
        score = 0.0
        
        # Vulnerability score (max 40 points)
        if self.scan_result:
            score += min(self.scan_result.critical_count * 10, 40)
            score += min(self.scan_result.high_count * 5, 20)
        
        # Fuzzing score (max 30 points)
        if self.fuzz_results:
            leaks = sum(1 for r in self.fuzz_results if r.leaked_data)
            suspicious = sum(1 for r in self.fuzz_results if r.suspicious_behavior)
            score += min(leaks * 10, 20)
            score += min(suspicious * 5, 10)
        
        # Behavioral score (max 30 points)
        if self.behavior_report:
            score += min(len(self.behavior_report.alerts) * 10, 30)
        
        return min(score, 100.0)

    def _generate_recommendations(self, risk_score: float) -> list[str]:
        """Generate security recommendations."""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("❌ CRITICAL: Do not use this MCP server in production")
            recommendations.append("🔒 High risk of security breach detected")
        elif risk_score > 40:
            recommendations.append("⚠️  WARNING: Use with extreme caution")
            recommendations.append("🔍 Review and fix identified vulnerabilities")
        else:
            recommendations.append("✓ Moderate risk level")
            recommendations.append("🔧 Address minor issues before deployment")
        
        if self.scan_result and self.scan_result.critical_count > 0:
            recommendations.append(f"🐛 Fix {self.scan_result.critical_count} critical vulnerabilities")
        
        if self.fuzz_results:
            leaks = sum(1 for r in self.fuzz_results if r.leaked_data)
            if leaks > 0:
                recommendations.append(f"🔐 Fix {leaks} data leak vulnerabilities")
        
        if self.behavior_report and self.behavior_report.alerts:
            recommendations.append("👁️  Review behavioral alerts")
        
        return recommendations

    def _generate_final_result(self, execution_time: float) -> SandboxResult:
        """Generate final sandbox result."""
        
        risk_score = self._calculate_risk_score()
        recommendations = self._generate_recommendations(risk_score)
        
        return SandboxResult(
            status=SandboxStatus.COMPLETED,
            scan_result=self.scan_result,
            fuzz_results=self.fuzz_results,
            behavior_report=self.behavior_report,
            overall_risk_score=risk_score,
            recommendations=recommendations,
            execution_time=execution_time
        )

    def _create_failed_result(self, error: str, execution_time: float) -> SandboxResult:
        """Create failed result."""
        return SandboxResult(
            status=SandboxStatus.FAILED,
            scan_result=self.scan_result,
            fuzz_results=self.fuzz_results,
            behavior_report=self.behavior_report,
            overall_risk_score=100.0,
            recommendations=[f"Analysis failed: {error}"],
            execution_time=execution_time
        )

    def _display_summary(self, result: SandboxResult) -> None:
        """Display summary table."""
        
        # Create summary table
        table = Table(title="Security Analysis Summary", show_header=True)
        table.add_column("Category", style="cyan")
        table.add_column("Result", style="white")
        
        table.add_row("Overall Risk Score", f"{result.overall_risk_score:.1f}/100")
        table.add_row("Execution Time", f"{result.execution_time:.2f}s")
        table.add_row("Status", result.status.value)
        
        if result.scan_result:
            table.add_row(
                "Vulnerabilities",
                f"C:{result.scan_result.critical_count} "
                f"H:{result.scan_result.high_count} "
                f"M:{result.scan_result.medium_count}"
            )
        
        table.add_row("Fuzzing Tests", str(len(result.fuzz_results)))
        
        console.print("\n")
        console.print(table)
        
        # Display recommendations
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in result.recommendations:
            console.print(f"  {rec}")

    def save_results(self, result: SandboxResult, output_file: str = "sandbox_result.json") -> None:
        """Save results to file."""
        
        output_path = Path("reports") / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict (simplified)
        result_dict = {
            "status": result.status.value,
            "overall_risk_score": result.overall_risk_score,
            "recommendations": result.recommendations,
            "execution_time": result.execution_time,
            "scan_summary": {
                "total": result.scan_result.total_count if result.scan_result else 0,
                "critical": result.scan_result.critical_count if result.scan_result else 0,
                "high": result.scan_result.high_count if result.scan_result else 0,
            } if result.scan_result else None,
            "fuzzing_summary": {
                "total_tests": len(result.fuzz_results),
                "leaked_data": sum(1 for r in result.fuzz_results if r.leaked_data),
                "suspicious": sum(1 for r in result.fuzz_results if r.suspicious_behavior),
            },
            "behavior_summary": result.behavior_report.summary if result.behavior_report else None
        }
        
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        console.print(f"\n[green]Results saved to: {output_path}[/green]")
