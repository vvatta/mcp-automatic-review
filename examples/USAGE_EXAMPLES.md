# MCP Source Examples

This directory contains examples of how to use the MCP Malware Sandbox with different source types.

## Quick Examples

### 1. Analyze Local MCP Server

```bash
# Analyze the malicious server example in this directory
python -m src.cli analyze ./examples
```

### 2. Analyze from GitHub

```bash
# Analyze a public GitHub repository
python -m src.cli analyze https://github.com/modelcontextprotocol/servers

# Analyze with specific branch
python -m src.cli analyze modelcontextprotocol/servers --ref main

# Analyze with specific tag
python -m src.cli analyze owner/repo --ref v1.0.0
```

### 3. Analyze from npm Registry

```bash
# Analyze an npm package (latest version)
python -m src.cli analyze npm:@modelcontextprotocol/server-filesystem

# Analyze with specific version
python -m src.cli analyze express@4.18.0

# Explicitly specify source type
python -m src.cli analyze my-package --source-type npm --version "^2.0.0"
```

### 4. Analyze from PyPI Registry

```bash
# Analyze a PyPI package
python -m src.cli analyze pypi:requests

# Analyze with version constraint
python -m src.cli analyze requests==2.31.0

# Explicitly specify source type
python -m src.cli analyze django --source-type pypi --version ">=4.0.0"
```

## Advanced Usage

### MCP Server Configuration with Command and Args

When creating MCP server configurations programmatically, you can now specify how to execute the server:

```python
from src.installer.source_factory import MCPSourceFactory

# Create an npm source with custom command and args
source = MCPSourceFactory.create_source(
    "npm:@openbnb/mcp-server-airbnb",
    command="npx",
    args=["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]
)

# The configuration is available in source.config
print(f"Command: {source.config.command}")
print(f"Args: {source.config.args}")
```

This is particularly useful when you need to:
- Pass additional flags to the MCP server
- Use a specific runtime command (npx, node, python, etc.)
- Configure server behavior for testing

Example configuration for different server types:

```python
# npm/npx-based MCP server
source = MCPSourceFactory.create_source(
    "npm:@modelcontextprotocol/server-filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "--allowed-directory", "/safe/path"]
)

# Python-based MCP server
source = MCPSourceFactory.create_source(
    "pypi:my-mcp-server",
    command="python",
    args=["-m", "my_mcp_server", "--debug"]
)

# Local MCP server with custom command
source = MCPSourceFactory.create_source(
    "./my-local-server",
    command="node",
    args=["index.js", "--port", "8080"]
)
```

### With API Key for LLM Fuzzing

```bash
# GitHub source with fuzzing
python -m src.cli analyze owner/repo \
    --anthropic-key YOUR_API_KEY \
    --output github-analysis.json

# npm package with fuzzing
python -m src.cli analyze npm:package-name \
    --anthropic-key YOUR_API_KEY \
    --output npm-analysis.json
```

### With Live Server Testing

```bash
# Analyze local server with live testing
python -m src.cli analyze ./my-mcp-server \
    --server-url http://localhost:8000 \
    --anthropic-key YOUR_API_KEY
```

### Explicit Source Type

When the auto-detection might be ambiguous, specify the source type explicitly:

```bash
# Force GitHub interpretation
python -m src.cli analyze ambiguous-ref --source-type github

# Force npm interpretation
python -m src.cli analyze ambiguous-ref --source-type npm

# Force PyPI interpretation
python -m src.cli analyze ambiguous-ref --source-type pypi
```

## Expected Output

The scanner will:

1. **Fetch the MCP source**
   - For local: Validate path exists
   - For GitHub: Clone repository
   - For npm: Install package
   - For PyPI: Install package

2. **Run static analysis**
   - Scan dependencies for vulnerabilities (Trivy)
   - Check for dangerous permissions
   - Generate SBOM

3. **Launch in Docker container**
   - Isolated environment with gVisor
   - Honeypot decoy files
   - Network monitoring

4. **Perform dynamic testing**
   - LLM-generated fuzzing payloads
   - Command injection tests
   - Path traversal tests
   - SQL injection tests

5. **Generate report**
   - JSON output with risk score
   - Vulnerability details
   - Behavioral analysis
   - Recommendations

## Example Output

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

## Testing Different Sources

You can test the source detection without running full analysis:

```python
from src.installer.source_factory import MCPSourceFactory

# Test source detection
source = MCPSourceFactory.create_source("https://github.com/owner/repo")
print(f"Detected type: {source.config.source_type}")
print(f"Will fetch from: {source.config.source_reference}")
```

## Troubleshooting

### GitHub Authentication

For private repositories, configure Git with SSH keys or use HTTPS with tokens:

```bash
git config --global credential.helper store
```

### npm Authentication

For private npm packages, ensure you're logged in:

```bash
npm login
```

### PyPI Authentication

For private PyPI packages, configure pip with credentials:

```bash
pip config set global.index-url https://username:password@private-pypi.org/simple
```

### Docker Not Found

Ensure Docker is installed and running:

```bash
docker --version
docker ps
```

### Trivy Not Found

Install Trivy scanner:

```bash
# macOS
brew install trivy

# Linux
sudo apt-get install trivy
```
