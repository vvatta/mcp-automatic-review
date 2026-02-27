# MCP Testing Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Developer Actions                            │
│                                                                      │
│  1. Create MCP folder: MCP-list/my-mcp/                             │
│  2. Add config.txt with MCP source details                          │
│  3. Open Pull Request                                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                          │
│                    (mcp-testing.yml triggered)                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Job 1: Detect MCP Changes                           │
│                                                                      │
│  • Fetch PR diff (git diff base...head)                             │
│  • Filter files in MCP-list/**                                      │
│  • Extract MCP names from paths                                     │
│  • Output: JSON array ["mcp1", "mcp2", ...]                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Job 2: Test MCP (Matrix Strategy)                       │
│                                                                      │
│  Runs in parallel for each MCP detected                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ For each MCP:                                           │         │
│  │                                                          │         │
│  │ Step 1: Parse config.txt                                │         │
│  │   • Read source, ref, version, etc.                     │         │
│  │   • Set GitHub Actions outputs                          │         │
│  │                                                          │         │
│  │ Step 2: Build Docker Image                              │         │
│  │   • docker build -t mcp-sandbox                         │         │
│  │                                                          │         │
│  │ Step 3: Run MCP Analysis                                │         │
│  │   • python -m src.cli analyze <source>                  │         │
│  │   • Static scan (Trivy)                                 │         │
│  │   • Container execution                                 │         │
│  │   • Behavioral monitoring                               │         │
│  │   • LLM fuzzing (optional)                              │         │
│  │   • Output: MCP-list/<mcp>/results.json                 │         │
│  │                                                          │         │
│  │ Step 4: Generate Reports                                │         │
│  │   • Create report.md from results.json                  │         │
│  │   • Copy vulnerabilities.json                           │         │
│  │                                                          │         │
│  │ Step 5: Commit Results                                  │         │
│  │   • git add MCP-list/<mcp>/                             │         │
│  │   • git commit & push to PR branch                      │         │
│  └────────────────────────────────────────────────────────┘         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Job 3: Update PR Description                            │
│                                                                      │
│  • Checkout updated PR branch                                       │
│  • Read all results.json files                                      │
│  • Generate summary with risk scores                                │
│  • Format as markdown table:                                        │
│    ┌──────────────┬──────────┬──────────────┐                      │
│    │ MCP          │ Risk     │ Vulns        │                      │
│    ├──────────────┼──────────┼──────────────┤                      │
│    │ ✅ mcp-1     │ 25/100   │ 2 (0 crit)   │                      │
│    │ ⚠️  mcp-2    │ 65/100   │ 15 (3 crit)  │                      │
│    └──────────────┴──────────┴──────────────┘                      │
│  • Update PR body via GitHub API                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Results Available                              │
│                                                                      │
│  ✓ PR description shows test summary                                │
│  ✓ MCP folders contain detailed reports:                            │
│    - MCP-list/my-mcp/results.json                                   │
│    - MCP-list/my-mcp/report.md                                      │
│    - MCP-list/my-mcp/vulnerabilities.json                           │
│  ✓ Artifacts uploaded for download                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Timeline Example

For a PR with 3 MCPs:

```
Time    Action
────────────────────────────────────────────────────────────
0:00    PR opened with changes to MCP-list/mcp1/, mcp2/, mcp3/
0:01    detect-mcp-changes job starts
0:02    detect-mcp-changes job completes
        Output: ["mcp1", "mcp2", "mcp3"]
        
0:02    test-mcp jobs start (3 parallel jobs)
        
        ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
        │  Test mcp1  │  │  Test mcp2  │  │  Test mcp3  │
        │             │  │             │  │             │
0:05    │  Scanning   │  │  Scanning   │  │  Scanning   │
0:10    │  Analysis   │  │  Analysis   │  │  Analysis   │
0:15    │  Complete   │  │  Running... │  │  Complete   │
0:18    └─────────────┘  │  Complete   │  └─────────────┘
                         └─────────────┘
                         
0:18    update-pr-description starts
0:19    update-pr-description completes
        PR description updated with all results
        
0:19    Workflow complete ✅
```

## Key Features

1. **Parallel Execution**: Multiple MCPs tested simultaneously
2. **Automatic Detection**: Only tests changed MCPs
3. **Isolated Testing**: Each MCP runs in separate container
4. **Comprehensive Results**: JSON + Markdown + Vulnerabilities
5. **PR Integration**: Results committed and summary posted
6. **Artifact Upload**: Full logs available for download
