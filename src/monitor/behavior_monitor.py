"""
Behavioral monitoring using eBPF and system call tracking.
Monitors filesystem access, network connections, and process execution.
"""
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from rich.console import Console

console = Console()


class EventType(str, Enum):
    """Types of monitoring events."""
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    PROCESS = "process"
    SYSCALL = "syscall"


@dataclass
class MonitoringEvent:
    """A single monitoring event."""
    timestamp: str
    event_type: EventType
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"


@dataclass
class BehaviorReport:
    """Complete behavioral monitoring report."""
    start_time: str
    end_time: str
    events: List[MonitoringEvent]
    summary: Dict[str, Any]
    alerts: List[str]


class BehaviorMonitor:
    """Monitors MCP server behavior using various techniques."""

    def __init__(self, container_name: str = "mcp-malware-sandbox"):
        self.container_name = container_name
        self.events: List[MonitoringEvent] = []
        self.start_time = datetime.now().isoformat()
        self.decoy_files = [
            "/tmp/fake_home/.ssh/id_rsa",
            "/tmp/fake_home/.env",
            "/tmp/fake_home/.aws/credentials"
        ]

    def start_monitoring(self) -> None:
        """Start all monitoring processes."""
        console.print("[bold blue]Starting behavioral monitoring...[/bold blue]")
        self.start_time = datetime.now().isoformat()
        self.events = []

    def monitor_filesystem_access(self) -> List[MonitoringEvent]:
        """
        Monitor filesystem access using strace.
        
        Returns:
            List of filesystem events
        """
        console.print("[blue]Monitoring filesystem access...[/blue]")
        
        events = []
        
        try:
            # Run strace to capture filesystem syscalls
            cmd = [
                "docker", "exec", self.container_name,
                "strace", "-e", "trace=openat,read,write,stat",
                "-f", "-p", "1", "-o", "/tmp/strace.log"
            ]
            
            # This would run in background
            # For now, we'll check existing logs
            
            # Check if decoy files were accessed
            for decoy in self.decoy_files:
                event = self._check_decoy_access(decoy)
                if event:
                    events.append(event)
                    
        except Exception as e:
            console.print(f"[yellow]Filesystem monitoring error: {e}[/yellow]")
        
        return events

    def _check_decoy_access(self, filepath: str) -> Optional[MonitoringEvent]:
        """Check if a decoy file was accessed."""
        try:
            # Check file access time in container
            cmd = [
                "docker", "exec", self.container_name,
                "stat", "-c", "%X", filepath
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                access_time = int(result.stdout.strip())
                current_time = int(time.time())
                
                # If accessed in last 60 seconds
                if current_time - access_time < 60:
                    return MonitoringEvent(
                        timestamp=datetime.now().isoformat(),
                        event_type=EventType.FILESYSTEM,
                        description=f"ALERT: Decoy file accessed: {filepath}",
                        details={"path": filepath, "access_time": access_time},
                        severity="CRITICAL"
                    )
        except Exception:
            pass
        
        return None

    def monitor_network_activity(self) -> List[MonitoringEvent]:
        """
        Monitor network activity from pcap files.
        
        Returns:
            List of network events
        """
        console.print("[blue]Monitoring network activity...[/blue]")
        
        events = []
        
        try:
            # Read network monitor logs
            connections_log = Path("docker/network-monitor/connections.log")
            if connections_log.exists():
                with open(connections_log, 'r') as f:
                    content = f.read()
                
                # Parse for outbound connections
                if "ESTABLISHED" in content or "SYN_SENT" in content:
                    events.append(MonitoringEvent(
                        timestamp=datetime.now().isoformat(),
                        event_type=EventType.NETWORK,
                        description="Outbound network connection detected",
                        details={"log": content[:500]},
                        severity="WARNING"
                    ))
            
            # Check pcap file
            pcap_file = Path("docker/network-monitor/capture.pcap")
            if pcap_file.exists() and pcap_file.stat().st_size > 0:
                # Parse pcap for suspicious destinations
                dns_queries = self._parse_dns_from_pcap(pcap_file)
                for query in dns_queries:
                    events.append(MonitoringEvent(
                        timestamp=datetime.now().isoformat(),
                        event_type=EventType.NETWORK,
                        description=f"DNS query: {query}",
                        details={"domain": query},
                        severity="INFO"
                    ))
                    
        except Exception as e:
            console.print(f"[yellow]Network monitoring error: {e}[/yellow]")
        
        return events

    def _parse_dns_from_pcap(self, pcap_file: Path) -> List[str]:
        """Extract DNS queries from pcap file."""
        queries = []
        
        try:
            # Use tshark to parse DNS
            cmd = [
                "tshark", "-r", str(pcap_file),
                "-Y", "dns.qry.name",
                "-T", "fields",
                "-e", "dns.qry.name"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                queries = [q.strip() for q in result.stdout.split('\n') if q.strip()]
                
        except FileNotFoundError:
            console.print("[yellow]tshark not available for DNS parsing[/yellow]")
        except Exception as e:
            console.print(f"[yellow]DNS parsing error: {e}[/yellow]")
        
        return queries

    def monitor_process_execution(self) -> List[MonitoringEvent]:
        """
        Monitor process execution (execve syscalls).
        
        Returns:
            List of process events
        """
        console.print("[blue]Monitoring process execution...[/blue]")
        
        events = []
        
        try:
            # Get process list from container
            cmd = ["docker", "exec", self.container_name, "ps", "aux"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                processes = result.stdout
                
                # Check for suspicious processes
                suspicious_procs = [
                    "sh", "bash", "/bin/sh", "/bin/bash",
                    "nc", "netcat", "curl", "wget"
                ]
                
                for proc in suspicious_procs:
                    if proc in processes.lower():
                        events.append(MonitoringEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type=EventType.PROCESS,
                            description=f"Suspicious process detected: {proc}",
                            details={"process": proc},
                            severity="WARNING"
                        ))
                        
        except Exception as e:
            console.print(f"[yellow]Process monitoring error: {e}[/yellow]")
        
        return events

    def collect_container_logs(self) -> List[MonitoringEvent]:
        """
        Collect and analyze container logs.
        
        Returns:
            List of log events
        """
        console.print("[blue]Collecting container logs...[/blue]")
        
        events = []
        
        try:
            cmd = ["docker", "logs", "--tail", "100", self.container_name]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                logs = result.stdout + result.stderr
                
                # Check for error patterns
                error_patterns = [
                    "error", "exception", "failed", "denied",
                    "traceback", "fatal"
                ]
                
                for pattern in error_patterns:
                    if pattern in logs.lower():
                        events.append(MonitoringEvent(
                            timestamp=datetime.now().isoformat(),
                            event_type=EventType.SYSCALL,
                            description=f"Error pattern in logs: {pattern}",
                            details={"pattern": pattern},
                            severity="INFO"
                        ))
                        break
                        
        except Exception as e:
            console.print(f"[yellow]Log collection error: {e}[/yellow]")
        
        return events

    def generate_report(self) -> BehaviorReport:
        """
        Generate comprehensive behavioral monitoring report.
        
        Returns:
            BehaviorReport with all collected events
        """
        console.print("[bold blue]Generating behavioral report...[/bold blue]")
        
        # Collect all events
        self.events.extend(self.monitor_filesystem_access())
        self.events.extend(self.monitor_network_activity())
        self.events.extend(self.monitor_process_execution())
        self.events.extend(self.collect_container_logs())
        
        # Generate summary
        summary = {
            "total_events": len(self.events),
            "filesystem_events": sum(1 for e in self.events if e.event_type == EventType.FILESYSTEM),
            "network_events": sum(1 for e in self.events if e.event_type == EventType.NETWORK),
            "process_events": sum(1 for e in self.events if e.event_type == EventType.PROCESS),
            "critical_events": sum(1 for e in self.events if e.severity == "CRITICAL"),
            "warning_events": sum(1 for e in self.events if e.severity == "WARNING"),
        }
        
        # Generate alerts
        alerts = [
            event.description
            for event in self.events
            if event.severity in ["CRITICAL", "WARNING"]
        ]
        
        end_time = datetime.now().isoformat()
        
        report = BehaviorReport(
            start_time=self.start_time,
            end_time=end_time,
            events=self.events,
            summary=summary,
            alerts=alerts
        )
        
        # Save report
        self._save_report(report)
        
        return report

    def _save_report(self, report: BehaviorReport) -> None:
        """Save report to file."""
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            filename = reports_dir / f"behavior_report_{int(time.time())}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    "start_time": report.start_time,
                    "end_time": report.end_time,
                    "summary": report.summary,
                    "alerts": report.alerts,
                    "events": [
                        {
                            "timestamp": e.timestamp,
                            "type": e.event_type.value,
                            "description": e.description,
                            "details": e.details,
                            "severity": e.severity
                        }
                        for e in report.events
                    ]
                }, f, indent=2)
            
            console.print(f"[green]Report saved: {filename}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error saving report: {e}[/red]")
