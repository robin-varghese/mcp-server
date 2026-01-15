# Strategy: Puppeteer MCP Server in Docker

This document outlines the strategy to containerize and deploy the Puppeteer MCP server.

## 1. Overview
The goal is to host the Puppeteer MCP server within a Docker container. This server allows AI agents to control a headless Chrome browser to navigate pages, take screenshots, and interact with web elements.

## 2. Docker Image Strategy

### Dockerfile Specification
*   **Base Image**: `node:20-slim`
*   **System Dependencies**: Installs `google-chrome-stable` and necessary fonts/libraries via `apt-get` to ensure Chrome runs correctly in headless mode.
*   **Package**: `@modelcontextprotocol/server-puppeteer`
*   **Environment**: Sets `DOCKER_CONTAINER=true`.
*   **Entrypoint**: `npx -y @modelcontextprotocol/server-puppeteer`

## 3. Capabilities & Tools
The server exposes tools for browser settings:

| Tool Name | Description | Inputs |
|-----------|-------------|--------|
| `navigate` | Navigate to a URL | `url` |
| `screenshot` | Take a screenshot of the current page | `name`, `width`, `height` |
| `click` | Click an element by selector | `selector` |
| `fill` | Fill an input field | `selector`, `value` |
| `evaluate` | Execute JavaScript in console | `script` |
| `hover` | Hover over an element | `selector` |

## 4. Connection Strategy

### Configuration
To use this with an MCP client, configure it as follows:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--init",
        "-e", "DOCKER_CONTAINER=true",
        "puppeteer-mcp"
      ]
    }
  }
}
```

## 5. Verification

### Using the Interactive Client
A Python-based interactive client is provided.

```bash
# 1. Build the image
cd mcp-servers/puppeteer
docker build -t puppeteer-mcp .

# 2. Set NLP API Key (Optional)
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Run the client
python3 puppeteer_interactive.py
```

### Sample Commands
*   "Navigate to https://example.com"
*   "Take a screenshot"
*   "Click the button .more-info"
