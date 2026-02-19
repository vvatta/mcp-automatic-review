# MCP Automated Testing Workflow

This document describes the automated testing workflow for MCP servers using GitHub Actions.

## Overview

The MCP Automated Testing workflow allows you to test MCP servers by simply opening a Pull Request with a configuration file. The workflow automatically:

1. Detects MCP configurations in the PR
2. Runs comprehensive security analysis in isolated containers
3. Generates detailed reports
4. Updates the PR description with results
5. Commits results back to the repository

## How It Works

### Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Pull Request Opened                       │
│              (changes in MCP-list folder)                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│          Job 1: Detect MCP Configuration Changes             │
│  • Analyze changed files                                     │
│  • Extract MCP names from paths                              │
│  • Create matrix of MCPs to test                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│         Job 2: Test MCP (runs in parallel per MCP)          │
│  • Parse configuration file                                  │
│  • Build Docker sandbox image                                │
│  • Run MCP sandbox analysis                                  │
│    - Static vulnerability scanning (Trivy)                   │
│    - Dynamic analysis in isolated container                  │
│    - Behavioral monitoring                                   │
│    - LLM fuzzing (if API key provided)                       │
│  • Generate reports (JSON + Markdown)                        │
│  • Commit results back to PR                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│          Job 3: Update PR Description                        │
│  • Collect all test results                                  │
│  • Generate summary with risk scores                         │
│  • Update PR description with formatted results              │
└─────────────────────────────────────────────────────────────┘
```

### Trigger Conditions

The workflow triggers on Pull Requests when:
- Files in `MCP-list/**` are added, modified, or deleted
- PR is opened, synchronized, or reopened

### Jobs

#### 1. detect-mcp-changes
- **Purpose**: Identify which MCP configurations have changed
- **Runs on**: ubuntu-latest
- **Outputs**: 
  - `mcp-configs`: JSON array of MCP names to test
  - `has-changes`: Boolean indicating if any MCP configs changed

#### 2. test-mcp
- **Purpose**: Run comprehensive security analysis for each MCP
- **Runs on**: ubuntu-latest
- **Strategy**: Matrix build (parallel execution per MCP)
- **Steps**:
  1. Checkout code
  2. Install Python & system dependencies (Trivy)
  3. Parse MCP configuration from `config.txt`
  4. Build Docker sandbox image
  5. Run MCP sandbox analysis
  6. Generate human-readable report
  7. Copy vulnerability details
  8. Commit results to PR branch

#### 3. update-pr-description
- **Purpose**: Aggregate results and update PR description
- **Runs on**: ubuntu-latest
- **Depends on**: detect-mcp-changes, test-mcp
- **Runs**: Always (even if tests fail)

## Configuration File Format

Each MCP must have a `config.txt` file in its folder: `MCP-list/<mcp-name>/config.txt`

### Required Fields

- `source`: MCP source (GitHub URL, npm package, PyPI package, or local path)

### Optional Fields

- `ref`: Git reference (branch, tag, or commit) for GitHub sources
- `version`: Version specification for npm/PyPI packages
- `source_type`: Explicit source type (local, github, npm, pypi)
- `server_url`: URL of running MCP server for live testing
- `anthropic_key`: Anthropic API key for LLM fuzzing (prefer using GitHub secrets)

### Example Configurations

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

**Local Path:**
```
source: /path/to/mcp-server
```

## Output Files

After the workflow runs, the following files are added to each MCP folder:

### results.json
Complete analysis results in JSON format. Contains:
- Overall risk score (0-100)
- Status (COMPLETED, FAILED, etc.)
- Vulnerability scan summary
- Fuzzing results
- Recommendations
- Timestamp

### report.md
Human-readable markdown report. Includes:
- Executive summary
- Risk assessment
- Vulnerability breakdown
- Fuzzing results (if LLM fuzzing was enabled)
- Recommendations

### vulnerabilities.json
Detailed vulnerability report from Trivy scanner. Contains:
- CVE details
- Severity levels
- Affected packages
- Remediation advice

## Secrets Configuration

To enable LLM fuzzing, add the following secret to your repository:

1. Go to repository Settings → Secrets and variables → Actions
2. Add new repository secret:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key

The workflow will automatically use this secret if available.

## Permissions

The workflow requires the following permissions:
- `contents: write` - To commit results back to the PR branch
- `pull-requests: write` - To update PR description

These are configured in the workflow file.

## Example Usage

### Adding a New MCP Test

1. **Create MCP folder:**
   ```bash
   mkdir -p MCP-list/my-awesome-mcp
   ```

2. **Create configuration:**
   ```bash
   cat > MCP-list/my-awesome-mcp/config.txt << 'EOF'
   source: owner/repository
   ref: main
   EOF
   ```

3. **Open Pull Request:**
   ```bash
   git checkout -b test-my-awesome-mcp
   git add MCP-list/my-awesome-mcp/
   git commit -m "Add MCP test configuration for my-awesome-mcp"
   git push origin test-my-awesome-mcp
   # Open PR on GitHub
   ```

4. **Wait for workflow:**
   - Workflow automatically runs
   - Results are committed to your PR branch
   - PR description is updated with summary

5. **Review results:**
   - Check PR description for summary
   - View `MCP-list/my-awesome-mcp/report.md` for details
   - Review `MCP-list/my-awesome-mcp/results.json` for raw data

## Testing Multiple MCPs

You can test multiple MCPs in a single PR:

```bash
# Create configurations for multiple MCPs
mkdir -p MCP-list/mcp-1 MCP-list/mcp-2 MCP-list/mcp-3

echo "source: owner/repo1" > MCP-list/mcp-1/config.txt
echo "source: npm:package2" > MCP-list/mcp-2/config.txt
echo "source: pypi:package3" > MCP-list/mcp-3/config.txt

# Commit all at once
git add MCP-list/
git commit -m "Add multiple MCP test configurations"
git push
```

The workflow will test all MCPs in parallel using a matrix strategy.

## Troubleshooting

### Workflow doesn't trigger
- Ensure changes are in `MCP-list/**` paths
- Check that PR is not from a fork (workflows may have restricted permissions)

### Analysis fails
- Check if `config.txt` has valid `source` field
- For GitHub sources, ensure repository is accessible
- For npm/PyPI, verify package name and version exist

### Missing results files
- Check workflow logs for errors
- Ensure MCP analysis completed successfully
- Verify write permissions are enabled

### PR description not updated
- Check that workflow has `pull-requests: write` permission
- Verify the update-pr-description job completed successfully
- Look for errors in GitHub Actions logs

## Best Practices

1. **Use descriptive MCP names**: Choose folder names that clearly identify the MCP
2. **Test one MCP at a time initially**: Verify workflow works before adding multiple
3. **Review results carefully**: Check both automated reports and manual review
4. **Keep configurations up to date**: Update `ref` or `version` when upstream changes
5. **Use GitHub secrets for API keys**: Never commit API keys to config files

## Security Considerations

- All MCP analysis runs in isolated Docker containers
- gVisor runtime provides kernel-level isolation
- Network activity is monitored and logged
- File system access is restricted
- Tests run with minimal privileges

## Workflow Customization

To customize the workflow for your needs:

1. Edit `.github/workflows/mcp-testing.yml`
2. Modify job steps or add new jobs
3. Adjust container resource limits
4. Change output formats
5. Add custom notification steps

## Support

For issues or questions:
- Check workflow logs in GitHub Actions tab
- Review existing issues in the repository
- Open a new issue with workflow run details
