"""Configuration for MCP Malware Sandbox."""
from pydantic import BaseModel
from typing import Optional


class SandboxConfig(BaseModel):
    """Configuration for sandbox execution."""
    
    # Container settings
    container_runtime: str = "runsc"  # gVisor runtime
    container_memory_limit: str = "512m"
    container_cpu_limit: str = "1.0"
    container_timeout: int = 300  # 5 minutes
    
    # Network settings
    enable_network_monitoring: bool = True
    allow_outbound_network: bool = True
    blocked_domains: list[str] = []
    
    # Monitoring settings
    enable_filesystem_monitoring: bool = True
    enable_process_monitoring: bool = True
    enable_syscall_tracing: bool = True
    
    # Fuzzing settings
    num_valid_payloads: int = 5
    num_malicious_payloads: int = 10
    enable_llm_fuzzing: bool = False
    
    # Reporting settings
    output_format: str = "json"  # json, html, pdf
    verbose: bool = True
    
    # Decoy files
    decoy_files: dict[str, str] = {
        ".ssh/id_rsa": "-----BEGIN OPENSSH PRIVATE KEY-----\nDECOY_KEY\n-----END OPENSSH PRIVATE KEY-----",
        ".env": "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ".aws/credentials": "[default]\naws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    }


class TriviConfig(BaseModel):
    """Configuration for Trivy scanner."""
    
    severity_levels: list[str] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    timeout: int = 300
    enable_sbom: bool = True
    format: str = "json"


class LLMConfig(BaseModel):
    """Configuration for LLM fuzzing."""
    
    model: str = "claude-3-5-sonnet-20241022"
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
