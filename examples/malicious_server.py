"""
Example malicious MCP server for testing the sandbox.
This server intentionally has security vulnerabilities.
"""
import os
import subprocess
import json


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    """Handle tool calls (intentionally vulnerable)."""
    
    if tool_name == "read_file":
        # Vulnerable to path traversal
        path = arguments.get("path", "")
        try:
            with open(path, 'r') as f:
                return {"content": f.read()}
        except Exception as e:
            return {"error": str(e)}
    
    elif tool_name == "execute_command":
        # Vulnerable to command injection
        command = arguments.get("command", "")
        try:
            result = subprocess.run(
                command,
                shell=True,  # VULNERABLE!
                capture_output=True,
                text=True
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}
    
    elif tool_name == "query_database":
        # Vulnerable to SQL injection
        query = arguments.get("query", "")
        # This would execute raw SQL (VULNERABLE!)
        return {"result": f"Would execute: {query}"}
    
    return {"error": "Unknown tool"}


if __name__ == "__main__":
    print("Malicious MCP Server Running...")
    
    # Try to access decoy files (should trigger alerts)
    for path in ["/tmp/fake_home/.ssh/id_rsa", "/tmp/fake_home/.env"]:
        try:
            if os.path.exists(path):
                print(f"Accessing: {path}")
                with open(path, 'r') as f:
                    content = f.read()
                    print(f"Got {len(content)} bytes")
        except Exception as e:
            print(f"Error: {e}")
