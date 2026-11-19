#!/bin/sh
set -eu

if [ -z "${DATABASE_URL:-}" ]; then
  DATABASE_URL="$(python -c 'from pathlib import Path; from urllib.parse import quote; password = quote(Path("/run/secrets/db_password").read_text().strip(), safe=""); print(f"postgresql+psycopg://agentboard:{password}@db:5432/agentboard")')"
  export DATABASE_URL
fi

# Compose file secrets retain host permissions. Copy only the credentials
# this service receives into a directory owned by its unprivileged worker.
install -d -m 0700 -o 10001 -g 10001 /tmp/agentboard-secrets
if [ -f /run/secrets/browser_token ]; then
  install -m 0600 -o 10001 -g 10001 /run/secrets/browser_token /tmp/agentboard-secrets/browser_token
  export AGENTBOARD_BROWSER_TOKEN_FILE=/tmp/agentboard-secrets/browser_token
else
  unset AGENTBOARD_BROWSER_TOKEN_FILE
fi
if [ -f /run/secrets/mcp_token ]; then
  install -m 0600 -o 10001 -g 10001 /run/secrets/mcp_token /tmp/agentboard-secrets/mcp_token
  export AGENTBOARD_MCP_TOKEN_FILE=/tmp/agentboard-secrets/mcp_token
else
  unset AGENTBOARD_MCP_TOKEN_FILE
fi
exec setpriv --reuid 10001 --regid 10001 --clear-groups --no-new-privs "$@"
