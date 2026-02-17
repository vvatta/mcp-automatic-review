# Example: Using MCP Malware Sandbox

This directory contains example usage scenarios for the MCP Malware Sandbox.

## Quick Start Example

### 1. Basic Scan

Scan a directory containing an MCP server for vulnerabilities:

```bash
python -m src.cli scan /path/to/mcp-server
```

**Expected Output:**
```
Scanning: /path/to/mcp-server

Running Trivy scan...
Found 15 vulnerabilities:
  Critical: 2
  High: 5
  Medium: 8
  Low: 0

Dangerous permissions:
  - child_process: Can execute system commands
  - fs: Can access filesystem
```

### 2. Full Analysis

Run a complete security analysis with container isolation:

```bash
python -m src.cli analyze /path/to/mcp-server
```

**Expected Output:**
```
╭────────────────────────────────────╮
│   MCP Malware Sandbox              │
│   Comprehensive Security Analysis   │
╰────────────────────────────────────╯

Phase 1: Static & Dependency Analysis
Running Trivy scan...
Found 15 vulnerabilities

Phase 2: Isolation Engine (Docker + gVisor)
Building sandbox container...
✓ Container created: mcp-sandbox-1234567890

Phase 3: Behavioral Monitoring (Starting)
Starting behavioral monitoring...

Phase 4: Dynamic Interrogation (LLM Fuzzing)
Discovering MCP tools...
Found 3 tools
Generating payloads for read_file...
...

Phase 5: Behavioral Monitoring (Collecting)
Generating behavioral report...

Phase 6: Final Report Generation
╭─────────────────────────────────────╮
│ Security Analysis Summary           │
├─────────────┬───────────────────────┤
│ Category    │ Result                │
├─────────────┼───────────────────────┤
│ Risk Score  │ 45.0/100              │
│ Time        │ 142.5s                │
│ Status      │ COMPLETED             │
│ Vulns       │ C:2 H:5 M:8           │
│ Tests       │ 50                    │
╰─────────────┴───────────────────────╯

Recommendations:
  ⚠️  WARNING: Use with extreme caution
  🔍 Review and fix identified vulnerabilities
  🐛 Fix 2 critical vulnerabilities
  🔐 Fix 3 data leak vulnerabilities
```

### 3. With Live Server Testing

If you have an MCP server running:

```bash
# Start your MCP server
node server.js &

# Run analysis with server URL
python -m src.cli analyze . \
    --server-url http://localhost:8000 \
    --output results.json
```

### 4. Using Docker Compose

For a complete environment with network monitoring:

```bash
cd docker
docker-compose up -d

# Monitor logs
docker-compose logs -f

# Stop
docker-compose down
```

## Example Use Cases

### Use Case 1: CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Security Scan
  run: |
    pip install -r requirements.txt
    python -m src.cli scan .
    
- name: Upload Results
  uses: actions/upload-artifact@v4
  with:
    name: security-report
    path: reports/
```

### Use Case 2: Pre-Deployment Check

Before deploying an MCP server:

```bash
#!/bin/bash
# pre-deploy.sh

echo "Running security scan..."
python -m src.cli analyze . --output pre-deploy-report.json

# Check risk score
RISK_SCORE=$(jq '.overall_risk_score' reports/sandbox_result.json)

if (( $(echo "$RISK_SCORE > 60" | bc -l) )); then
    echo "❌ Risk score too high: $RISK_SCORE"
    exit 1
fi

echo "✓ Security check passed (risk: $RISK_SCORE)"
```

### Use Case 3: Third-Party MCP Server Evaluation

Evaluating an untrusted MCP server from GitHub:

```bash
# Clone the server
git clone https://github.com/unknown/mcp-server.git
cd mcp-server

# Run complete analysis
python -m src.cli analyze . \
    --anthropic-key $ANTHROPIC_API_KEY \
    --output evaluation.json

# Review results
cat reports/sandbox_result.json | jq '.recommendations'
```

### Use Case 4: Development Workflow

During development:

```bash
# Quick scan during development
python -m src.cli scan .

# Full analysis before commit
python -m src.cli analyze .

# If risk > 60, fix issues before commit
```

## Output Files

After running a scan, you'll find these files in the `reports/` directory:

- `trivy-report.json` - Detailed vulnerability report
- `sbom.json` - Software Bill of Materials
- `behavior_report_*.json` - Behavioral monitoring log
- `sandbox_result.json` - Overall results and recommendations

## Example Output Interpretation

### Low Risk (Score: 0-30)

```json
{
  "overall_risk_score": 25.0,
  "recommendations": [
    "✓ Moderate risk level",
    "🔧 Address minor issues before deployment"
  ]
}
```

**Action:** Safe to use with minor fixes.

### Medium Risk (Score: 31-60)

```json
{
  "overall_risk_score": 45.0,
  "recommendations": [
    "⚠️  WARNING: Use with extreme caution",
    "🔍 Review and fix identified vulnerabilities",
    "🐛 Fix 2 critical vulnerabilities"
  ]
}
```

**Action:** Review and fix critical issues before use.

### High Risk (Score: 61-100)

```json
{
  "overall_risk_score": 85.0,
  "recommendations": [
    "❌ CRITICAL: Do not use this MCP server in production",
    "🔒 High risk of security breach detected",
    "🐛 Fix 5 critical vulnerabilities",
    "🔐 Fix 10 data leak vulnerabilities"
  ]
}
```

**Action:** Do NOT use. Major security issues detected.

## Programmatic Usage

You can also use the sandbox programmatically:

```python
import asyncio
from src.orchestrator.main import MCPSandboxOrchestrator

async def analyze_server():
    orchestrator = MCPSandboxOrchestrator(
        workspace_path="/path/to/mcp-server",
        mcp_server_url="http://localhost:8000",
        anthropic_api_key="your-key"
    )
    
    result = await orchestrator.run_complete_analysis()
    orchestrator.save_results(result, "custom-report.json")
    
    print(f"Risk Score: {result.overall_risk_score}")
    print(f"Recommendations: {result.recommendations}")

asyncio.run(analyze_server())
```

## Tips

1. **First Time Setup**: Run `python -m src.cli setup` to check dependencies
2. **Faster Scans**: Use `scan` command for quick checks
3. **Detailed Analysis**: Use `analyze` for comprehensive testing
4. **CI/CD**: Use GitHub Actions workflow for automated scanning
5. **Custom Reports**: Specify `--output` to save results to custom location

## Troubleshooting

### "Trivy not found"
```bash
# Install Trivy
brew install trivy  # macOS
# or follow: https://aquasecurity.github.io/trivy/
```

### "Docker not running"
```bash
# Start Docker
sudo systemctl start docker  # Linux
# or start Docker Desktop
```

### "Permission denied"
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```
