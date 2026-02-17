"""
Test the LLM fuzzer module.
"""
import pytest
from src.interrogator.llm_fuzzer import MCPInterrogator, AttackType, FuzzPayload


@pytest.mark.asyncio
async def test_interrogator_init():
    """Test MCPInterrogator initialization."""
    interrogator = MCPInterrogator("http://localhost:8000")
    assert interrogator.server_url == "http://localhost:8000"
    await interrogator.close()


def test_generate_manual_payloads():
    """Test manual payload generation."""
    interrogator = MCPInterrogator("http://localhost:8000")
    
    tool_schema = {
        "name": "test_tool",
        "inputSchema": {
            "properties": {
                "path": {"type": "string"},
                "command": {"type": "string"}
            }
        }
    }
    
    payloads = interrogator._generate_manual_payloads(tool_schema)
    
    assert len(payloads) > 0
    assert any(p.attack_type == AttackType.COMMAND_INJECTION for p in payloads)
    assert any(p.attack_type == AttackType.PATH_TRAVERSAL for p in payloads)
    assert any(p.attack_type == AttackType.SQL_INJECTION for p in payloads)
