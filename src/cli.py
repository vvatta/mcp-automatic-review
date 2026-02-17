"""
Command-line interface for MCP Malware Sandbox.
"""
import asyncio
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.orchestrator.main import MCPSandboxOrchestrator

app = typer.Typer(
    name="mcp-sandbox",
    help="Comprehensive MCP malware sandbox with layered security architecture"
)
console = Console()


@app.command()
def analyze(
    workspace: str = typer.Argument(
        ...,
        help="Path to MCP server workspace to analyze"
    ),
    server_url: Optional[str] = typer.Option(
        None,
        "--server-url",
        help="URL of running MCP server (for live testing)"
    ),
    anthropic_key: Optional[str] = typer.Option(
        None,
        "--anthropic-key",
        help="Anthropic API key for LLM fuzzing"
    ),
    output: str = typer.Option(
        "sandbox_result.json",
        "--output",
        "-o",
        help="Output file for results"
    )
) -> None:
    """
    Run complete malware sandbox analysis on an MCP server.
    
    This will:
    1. Scan for vulnerabilities (Trivy)
    2. Launch in isolated container (Docker + gVisor)
    3. Monitor behavior (eBPF, syscalls)
    4. Fuzz with adversarial payloads (LLM)
    5. Generate comprehensive security report
    """
    console.print("[bold cyan]MCP Malware Sandbox[/bold cyan]")
    console.print(f"Analyzing workspace: {workspace}\n")
    
    # Get API key from environment if not provided
    if not anthropic_key:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    # Create orchestrator
    orchestrator = MCPSandboxOrchestrator(
        workspace_path=workspace,
        mcp_server_url=server_url,
        anthropic_api_key=anthropic_key
    )
    
    # Run analysis
    result = asyncio.run(orchestrator.run_complete_analysis())
    
    # Save results
    orchestrator.save_results(result, output)
    
    # Exit with appropriate code
    if result.overall_risk_score > 70:
        console.print("\n[red]⚠️  CRITICAL RISK DETECTED - Analysis failed[/red]")
        raise typer.Exit(code=1)
    elif result.overall_risk_score > 40:
        console.print("\n[yellow]⚠️  WARNING - High risk detected[/yellow]")
        raise typer.Exit(code=0)
    else:
        console.print("\n[green]✓ Analysis complete[/green]")
        raise typer.Exit(code=0)


@app.command()
def scan(
    workspace: str = typer.Argument(
        ...,
        help="Path to scan"
    )
) -> None:
    """
    Run static analysis only (no container isolation).
    
    Quick scan for vulnerabilities and suspicious dependencies.
    """
    from src.inspector.static_scanner import StaticScanner
    
    console.print(f"[bold]Scanning: {workspace}[/bold]\n")
    
    scanner = StaticScanner(workspace)
    
    # Run Trivy scan
    result = scanner.scan_with_trivy()
    
    if result:
        console.print(f"\n[bold]Found {result.total_count} vulnerabilities:[/bold]")
        console.print(f"  Critical: {result.critical_count}")
        console.print(f"  High: {result.high_count}")
        console.print(f"  Medium: {result.medium_count}")
        console.print(f"  Low: {result.low_count}")
    
    # Check permissions
    permissions = scanner.check_permissions_manifest()
    
    if permissions.get("dangerous_permissions"):
        console.print("\n[yellow]Dangerous permissions:[/yellow]")
        for perm in permissions["dangerous_permissions"]:
            console.print(f"  - {perm}")


@app.command()
def build() -> None:
    """
    Build the sandbox Docker image.
    """
    import subprocess
    
    console.print("[bold]Building Docker sandbox image...[/bold]\n")
    
    try:
        subprocess.run(
            ["docker", "build", "-f", "docker/Dockerfile.sandbox", "-t", "mcp-sandbox:latest", "."],
            check=True
        )
        console.print("\n[green]✓ Image built successfully[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]Build failed: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def setup() -> None:
    """
    Setup the sandbox environment (install dependencies, check tools).
    """
    console.print("[bold]Setting up MCP Malware Sandbox...[/bold]\n")
    
    # Check for required tools
    required_tools = {
        "docker": "Docker",
        "trivy": "Trivy vulnerability scanner",
    }
    
    missing = []
    
    for cmd, name in required_tools.items():
        try:
            import subprocess
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            console.print(f"[green]✓ {name} found[/green]")
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print(f"[red]✗ {name} not found[/red]")
            missing.append(name)
    
    if missing:
        console.print(f"\n[yellow]Missing tools: {', '.join(missing)}[/yellow]")
        console.print("\nInstallation instructions:")
        console.print("  Docker: https://docs.docker.com/get-docker/")
        console.print("  Trivy: brew install trivy (or see https://aquasecurity.github.io/trivy/)")
    else:
        console.print("\n[green]✓ All required tools installed[/green]")
    
    # Create directories
    dirs = ["reports", "docker/network-monitor"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓ Created directory: {d}[/green]")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold cyan]MCP Malware Sandbox[/bold cyan]")
    console.print("Version: 0.1.0")
    console.print("A comprehensive security sandbox for MCP servers")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
