# MCP Malware Sandbox

A comprehensive security sandbox for analyzing MCP (Model Context Protocol) servers with layered architecture for static inspection, isolated dynamic execution, and behavioral auditing.

## 🎯 Overview

The MCP Malware Sandbox treats untrusted MCP servers exactly like suspicious software: it doesn't trust their claims, isolates their environment, and records every move they make.

## 🏗️ Architecture

### Phase 1: Isolation Engine (The "Detonation" Chamber)
- **Runtime**: Docker with gVisor runtime (runsc) for kernel-level isolation
- **Virtual Filesystem**: Dummy directory with realistic decoy files (honeypot detection)
- **Network Guard**: Restricted network bridge with iptables logging

### Phase 2: Static & Dependency Analysis (Pre-Flight)
- **Dependency Audit**: Trivy/OSV-Scanner integration for CVE detection
- **Permissions Manifest**: Analyzes package.json/pyproject.toml for suspicious capabilities
- **SBOM Generation**: Complete Software Bill of Materials

### Phase 3: Dynamic Interrogation (The LLM Fuzzer)
- **Tool Discovery**: Automatic MCP tool enumeration
- **Adversarial Fuzzing**: LLM-generated payloads for security testing
- **Attack Vectors**: Command Injection, Path Traversal, SQL Injection, XSS, SSRF

### Phase 4: Behavioral Monitoring (Kernel-Level Telemetry)
- **Network Monitoring**: Logs all DNS queries and outbound connections
- **Filesystem Monitoring**: Tracks access to decoy files and system paths
- **Process Monitoring**: Detects suspicious process execution

## 📦 Installation

### Prerequisites

- Python 3.10+
- Docker
- Trivy (vulnerability scanner)
- gVisor (optional, for enhanced isolation)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/vvatta/mcp-automatic-review.git
cd mcp-automatic-review

# Install Python dependencies
pip install -r requirements.txt

# Or use pip with pyproject.toml
pip install -e .
```

### Setup Environment

```bash
# Run setup to check dependencies
python -m src.cli setup

# Build the sandbox Docker image
python -m src.cli build
```

## 🚀 Usage

### Quick Start

Analyze an MCP server workspace:

```bash
python -m src.cli analyze /path/to/mcp-server
```

### Advanced Usage

```bash
# Analyze with live server testing
python -m src.cli analyze /path/to/mcp-server \
    --server-url http://localhost:8000 \
    --anthropic-key YOUR_API_KEY \
    --output results.json

# Run static analysis only
python -m src.cli scan /path/to/mcp-server

# Check version
python -m src.cli version
```

### Using Docker Compose

```bash
# Start the complete sandbox environment
cd docker
docker-compose up -d

# Run with Trivy scanner
docker-compose --profile scanner up

# View logs
docker-compose logs -f

# Stop and cleanup
docker-compose down
```

## 📊 Output

The sandbox generates comprehensive reports including:

- **Vulnerability Report**: CVEs found in dependencies
- **SBOM**: Complete software bill of materials
- **Fuzzing Results**: Test results from adversarial payloads
- **Behavioral Report**: System calls, network activity, file access
- **Risk Score**: Overall security assessment (0-100)
- **Recommendations**: Actionable security advice

### Example Output

```json
{
  "status": "COMPLETED",
  "overall_risk_score": 35.0,
  "recommendations": [
    "✓ Moderate risk level",
    "🔧 Address minor issues before deployment",
    "🐛 Fix 2 critical vulnerabilities"
  ],
  "scan_summary": {
    "total": 15,
    "critical": 2,
    "high": 5
  },
  "fuzzing_summary": {
    "total_tests": 50,
    "leaked_data": 0,
    "suspicious": 3
  }
}
```

## 🛠️ Configuration

Create a `.env` file for configuration:

```env
# Anthropic API key (optional, for LLM fuzzing)
ANTHROPIC_API_KEY=your-key-here

# Container settings
CONTAINER_RUNTIME=runsc
CONTAINER_MEMORY_LIMIT=512m
CONTAINER_CPU_LIMIT=1.0

# Network monitoring
ENABLE_NETWORK_MONITORING=true
ALLOW_OUTBOUND_NETWORK=true

# Fuzzing settings
NUM_VALID_PAYLOADS=5
NUM_MALICIOUS_PAYLOADS=10
ENABLE_LLM_FUZZING=false
```

## 🔒 Security Features

### Container Isolation
- Non-root user execution
- Read-only filesystem (except /tmp)
- Dropped capabilities (CAP_DROP ALL)
- No new privileges
- gVisor runtime for kernel isolation

### Honeypot Detection
Decoy files are planted to detect exfiltration attempts:
- `.ssh/id_rsa` - Fake SSH private key
- `.env` - Fake environment variables
- `.aws/credentials` - Fake AWS credentials

### Network Monitoring
- All DNS queries logged
- Outbound connections tracked
- PCAP files for forensic analysis
- iptables rules for traffic inspection

### Attack Simulation
Tests include:
- Command injection: `; ls -la`, `| cat /etc/passwd`
- Path traversal: `../../../../etc/passwd`
- SQL injection: `' OR '1'='1`
- SSRF attempts
- XSS payloads

## 📁 Project Structure

```
mcp-automatic-review/
├── src/
│   ├── orchestrator/      # Main workflow coordinator
│   ├── inspector/         # Static analysis & Trivy
│   ├── interrogator/      # LLM fuzzing & payload generation
│   ├── monitor/           # Behavioral monitoring
│   ├── utils/            # Configuration & utilities
│   └── cli.py            # Command-line interface
├── docker/
│   ├── Dockerfile.sandbox # Sandbox container
│   ├── docker-compose.yml # Full environment
│   └── network-rules.sh   # iptables configuration
├── tests/                # Test suite
├── examples/             # Example MCP servers
├── config/               # Configuration files
└── reports/              # Generated reports
```

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## 📚 Implementation Workflow

| Stage | Component | Tool/Technology |
|-------|-----------|----------------|
| 1. Ingest | Orchestrator | Python (FastAPI/Typer) |
| 2. Inspect | Static Scanner | Trivy + Semgrep |
| 3. Isolate | Sandbox Container | Docker + gVisor (runsc) |
| 4. Monitor | Telemetry | eBPF + tcpdump |
| 5. Attack | LLM Interrogator | LangChain + MCP Python SDK |
| 6. Report | Result Collector | JSONL + PCAP Export |

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is for security research and testing purposes only. Always obtain proper authorization before testing any systems you don't own.

## 🔗 References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [gVisor Documentation](https://gvisor.dev/)
- [Trivy Scanner](https://aquasecurity.github.io/trivy/)
- [eBPF Guide](https://ebpf.io/)

## 📞 Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/vvatta/mcp-automatic-review).