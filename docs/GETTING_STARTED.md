# Getting Started with MCP Malware Sandbox

This guide will help you get started with the MCP Malware Sandbox.

## Prerequisites

Before you begin, ensure you have:

- Python 3.10 or higher
- Docker installed and running
- At least 2GB of free disk space
- (Optional) Trivy for vulnerability scanning
- (Optional) gVisor for enhanced container isolation

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vvatta/mcp-automatic-review.git
cd mcp-automatic-review
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install External Tools

#### Install Trivy (Vulnerability Scanner)

**macOS:**
```bash
brew install trivy
```

**Linux:**
```bash
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy
```

**Windows:**
```bash
# Using Chocolatey
choco install trivy
```

#### Install gVisor (Optional, for Enhanced Isolation)

Follow the [official gVisor installation guide](https://gvisor.dev/docs/user_guide/install/).

### 4. Setup Environment

```bash
# Run the setup command
python -m src.cli setup

# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional)
```

### 5. Build the Sandbox Container

```bash
python -m src.cli build
```

## Basic Usage

### Analyze an MCP Server

The simplest way to analyze an MCP server:

```bash
python -m src.cli analyze /path/to/mcp-server
```

This will:
1. Scan for vulnerabilities
2. Check for suspicious dependencies
3. Create an isolated container
4. Monitor behavior
5. Run security tests
6. Generate a report

### Static Analysis Only

For a quick scan without running the server:

```bash
python -m src.cli scan /path/to/mcp-server
```

### Advanced Analysis

For a comprehensive analysis with live server testing:

```bash
python -m src.cli analyze /path/to/mcp-server \
    --server-url http://localhost:8000 \
    --anthropic-key your-api-key \
    --output detailed-report.json
```

## Understanding the Results

The sandbox generates several types of output:

### 1. Vulnerability Report (`reports/trivy-report.json`)
Lists all CVEs found in dependencies with severity levels.

### 2. SBOM (`reports/sbom.json`)
Complete Software Bill of Materials for the analyzed server.

### 3. Fuzzing Results
Details of all security tests performed, including:
- Command injection attempts
- Path traversal tests
- SQL injection tests
- Detected data leaks

### 4. Behavioral Report (`reports/behavior_report_*.json`)
Logs of all system activities:
- File access attempts
- Network connections
- Process executions
- Decoy file access (honeypot triggers)

### 5. Overall Results (`reports/sandbox_result.json`)
Summary with:
- Risk score (0-100)
- Recommendations
- Summary statistics

## Example: Testing a Sample Server

We provide an example malicious server for testing:

```bash
# Analyze the example server
python -m src.cli analyze examples/
```

This will detect various security issues in the example server.

## Interpreting Risk Scores

- **0-30**: Low risk - Minor issues, safe to use with caution
- **31-60**: Moderate risk - Several issues, review before use
- **61-80**: High risk - Significant security concerns
- **81-100**: Critical risk - Do not use in production

## Next Steps

- Read the [Architecture Guide](ARCHITECTURE.md) to understand how it works
- Check the API Documentation for programmatic usage
- See Advanced Usage for customization options

## Troubleshooting

### Docker Issues

If you encounter Docker errors:

```bash
# Check Docker is running
docker ps

# Check Docker version
docker --version
```

### Trivy Not Found

If Trivy is not found:

```bash
# Verify installation
trivy --version

# Or run without Trivy (limited functionality)
python -m src.cli analyze /path/to/mcp-server
```

### Permission Errors

If you encounter permission errors:

```bash
# Add your user to the docker group (Linux)
sudo usermod -aG docker $USER
# Then log out and back in
```

## Getting Help

- Open an issue on [GitHub](https://github.com/vvatta/mcp-automatic-review/issues)
- Read the full [Documentation](../README.md)
