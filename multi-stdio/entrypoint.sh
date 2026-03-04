#!/bin/sh
# Generate config from template by substituting env vars, then run TBXark mcp-proxy.
# Set E2B_API_KEY_USER1, E2B_API_KEY_USER2 (and add more in config + sed as needed).
set -e
CONFIG_TEMPLATE="${MCP_PROXY_CONFIG_TEMPLATE:-/config/config.json.template}"
CONFIG_OUT="${MCP_PROXY_CONFIG:-/config/config.json}"

sed "s|__E2B_API_KEY_USER1__|${E2B_API_KEY_USER1:-}|g" "$CONFIG_TEMPLATE" | \
sed "s|__E2B_API_KEY_USER2__|${E2B_API_KEY_USER2:-}|g" > "$CONFIG_OUT"

exec /main --config "$CONFIG_OUT"
