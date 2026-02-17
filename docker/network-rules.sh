#!/bin/bash
# Script to set up iptables rules for network monitoring

# Log all outbound connections
iptables -A OUTPUT -j LOG --log-prefix "MCP-OUTBOUND: " --log-level 4

# Log DNS queries
iptables -A OUTPUT -p udp --dport 53 -j LOG --log-prefix "MCP-DNS: " --log-level 4
iptables -A OUTPUT -p tcp --dport 53 -j LOG --log-prefix "MCP-DNS-TCP: " --log-level 4

# Allow only specific outbound ports (optional - uncomment to restrict)
# iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
# iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
# iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
# iptables -A OUTPUT -j DROP

echo "Network monitoring rules applied"
