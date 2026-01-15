# Strategy: Brave Search MCP Server in Docker

This document outlines the strategy to containerize and deploy the Brave Search MCP server.

## 1. Overview
The goal is to host the Brave Search MCP server within a Docker container. This server integrates with the Brave Search API to provide privacy-focused web and local search capabilities to AI agents.

## 2. Prerequisites
Before you begin, you must obtain a Brave Search API Key:
1.  Visit the [Brave Search API Dashboard](https://api.search.brave.com/app/keys).
2.  Sign up or Log in.
3.  Generate a new API Key (Free tier available).
4.  **Note:** You (the user) currently need to perform this step.

## 3. Docker Image Strategy

### Dockerfile Specification
*   **Base Image**: `node:20-slim`
*   **Package**: `@modelcontextprotocol/server-brave-search`
*   **Entrypoint**: `npx -y @modelcontextprotocol/server-brave-search`
*   **Environment Variables**:
    *   `BRAVE_API_KEY`: Required. Your Brave Search API key.

## 3. Capabilities & Tools
The server exposes the following MCP tools:

| Tool Name | Description | Inputs |
|-----------|-------------|--------|
| `brave_web_search` | Performs a general web search | `query`, `count`, `offset` |
| `brave_local_search` | Searches for local businesses/POIs | `query`, `count` |

## 4. Connection Strategy

### Configuration
To use this with an MCP client, configure it as follows:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "BRAVE_API_KEY=your-api-key",
        "brave-search"
      ]
    }
  }
}
```

## 5. Verification

### Using the Interactive Client
A Python-based interactive client is provided to test the server capabilities using natural language.

```bash
# 1. Build the image
cd mcp-servers/brave-search
docker build -t brave-search .

# 2. Set API Keys
export GOOGLE_API_KEY="your-gemini-api-key"
export BRAVE_API_KEY="your-brave-api-key"

# 3. Run the client
python3 brave_search_interactive.py
```

### Sample Commands
*   "Search for the latest news on fusion energy"
*   "Find italian restaurants in London"
*   "Who won the 2024 Super Bowl?"
