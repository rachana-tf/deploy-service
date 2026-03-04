# One server running multiple stdio MCP servers (E2B user1, user2) via TBXark mcp-proxy.
# Build: docker build -t e2b-multi-stdio -f multi-stdio/Dockerfile .
# Run: docker run -p 8000:8000 -e E2B_API_KEY_USER1=... -e E2B_API_KEY_USER2=... e2b-multi-stdio
FROM ghcr.io/tbxark/mcp-proxy:latest AS proxy
FROM node:24-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=proxy /main /main
COPY multi-stdio/config.json.template /config/config.json.template
COPY multi-stdio/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
