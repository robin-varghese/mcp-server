FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Set entrypoint to run Sequential Thinking MCP server
# npx will install the package on first run
ENTRYPOINT ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"]
