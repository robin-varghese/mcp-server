FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK (optional but good for debugging/auth helpers)
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Set entrypoint to run Cloud Run MCP server directly
ENTRYPOINT ["npx", "-y", "@google-cloud/cloud-run-mcp"]
