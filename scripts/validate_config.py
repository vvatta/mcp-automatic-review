#!/usr/bin/env python3
"""
Validate MCP configuration files before committing.

Usage:
    python scripts/validate_config.py MCP-list/my-mcp/config.txt
    python scripts/validate_config.py  # validates all configs
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_parser import parse_config_file, find_mcp_configs


def validate_single_config(config_path: str) -> bool:
    """Validate a single configuration file."""
    try:
        config = parse_config_file(config_path)
        
        print(f"✅ Valid configuration: {config_path}")
        print(f"   Source: {config['source']}")
        
        if config['ref']:
            print(f"   Ref: {config['ref']}")
        if config['version']:
            print(f"   Version: {config['version']}")
        if config['source_type']:
            print(f"   Source Type: {config['source_type']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Invalid configuration: {config_path}")
        print(f"   Error: {e}")
        return False


def validate_all_configs() -> bool:
    """Validate all MCP configurations."""
    configs = find_mcp_configs()
    
    if not configs:
        print("No MCP configurations found in MCP-list/")
        return True
    
    print(f"Found {len(configs)} MCP configuration(s):\n")
    
    all_valid = True
    for mcp_name, config in configs.items():
        config_path = f"MCP-list/{mcp_name}/config.txt"
        
        try:
            print(f"✅ {mcp_name}")
            print(f"   Source: {config['source']}")
            if config['ref']:
                print(f"   Ref: {config['ref']}")
        except Exception as e:
            print(f"❌ {mcp_name}: {e}")
            all_valid = False
        
        print()
    
    return all_valid


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Validate specific config file
        config_path = sys.argv[1]
        
        if not Path(config_path).exists():
            print(f"Error: File not found: {config_path}")
            sys.exit(1)
        
        valid = validate_single_config(config_path)
        sys.exit(0 if valid else 1)
    
    else:
        # Validate all configs
        valid = validate_all_configs()
        
        if valid:
            print("All configurations are valid! ✨")
            sys.exit(0)
        else:
            print("Some configurations have errors. Please fix them before committing.")
            sys.exit(1)


if __name__ == "__main__":
    main()
