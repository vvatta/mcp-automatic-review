# MCP-list Directory

This directory contains MCP test configurations for automated testing on GitHub runners.

## How to Add a New MCP Test

1. Create a new folder with your MCP name: `MCP-list/your-mcp-name/`
2. Add a `config.txt` file with your MCP configuration
3. Open a Pull Request with the new configuration
4. The GitHub workflow will automatically run tests and add results to your PR

## Configuration File Format

Create a `config.txt` file in your MCP folder with the following format:

```
# Required: Source of the MCP
source: <mcp-source>

# Optional: Git reference (for GitHub sources)
ref: main

# Optional: Version (for npm/PyPI packages)
# version: 1.0.0

# Optional: Source type (local, github, npm, pypi, url)
# source_type: github

# Optional: Server URL for live testing
# server_url: http://localhost:8000

# Optional: API token for remote/cloud-hosted MCP servers
# auth_token: your-api-token-here
```

### Source Examples

**GitHub Repository:**
```
source: modelcontextprotocol/servers
ref: main
```

**npm Package:**
```
source: npm:@modelcontextprotocol/server-filesystem
version: 1.0.0
```

**PyPI Package:**
```
source: pypi:mcp-server-example
version: 1.0.0
```

**Remote / Cloud-hosted MCP Server (e.g. Atlassian Rovo):**
```
source: url:https://mcp.atlassian.com/v1/mcp
source_type: url
server_url: https://mcp.atlassian.com/v1/mcp
# auth_token: your-api-token-here
```

For remote URL sources, static analysis and container isolation are skipped
because there is no local code to inspect.  Only live LLM fuzzing is
performed against the running endpoint.

## Test Results

After the workflow runs, test results will be:
1. Added to the PR description
2. Saved as files in your MCP folder:
   - `results.json` - Complete test results
   - `report.md` - Human-readable report
   - `vulnerabilities.json` - Security scan results

## Validating Configuration

Before opening a PR, you can validate your configuration file:

```bash
# Validate a specific config
python scripts/validate_config.py MCP-list/your-mcp-name/config.txt

# Validate all configs
python scripts/validate_config.py
```

This will check that your `config.txt` has the required fields and proper format.

## Example

See `MCP-list/example-mcp/` for a sample configuration.
