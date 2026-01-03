# Google Storage MCP Server Deployment Strategy

## Overview
This document outlines the strategy for deploying the `google-storage-mcp` server using Docker, with authentication handled dynamically via the agentic application using Google OAuth.

## Architecture
- **Server Image**: Built from `node:20`, installs `gcloud` CLI (optional helper), and runs `@google-cloud/storage-mcp`.
- **Authentication**: Credentials are **not** baked into the image. They are passed at runtime.

## Authentication Strategy
The agentic application (client) performs the OAuth flow to obtain credentials. These credentials must be provided to the Docker container so the MCP server can authenticate with Google APIs.

### Option 1: Passing Access Token (Recommended for dynamic short-lived sessions)
If the agentic application has a valid OAuth 2.0 Access Token, pass it via the `GOOGLE_ACCESS_TOKEN` environment variable.

### Option 2: Mounting Credentials File (Recommended for Service Accounts or Persistent Auth)
If the agentic application has a standard `application_default_credentials.json` (ADC), mount the directory.

## Deployment Commands (Docker)

### 1. Build the Image
```bash
cd google-storage-mcp
docker build -t google-storage-mcp .
```

### 2. Run with Access Token (Agentic Flow)
Assuming the agent application has retrieved an access token for the user:

```bash
export USER_ACCESS_TOKEN="<captured-oauth-token>"

docker run -i --rm \
  -e GOOGLE_ACCESS_TOKEN="$USER_ACCESS_TOKEN" \
  google-storage-mcp
```
*Note: Stdio (`-i`) is used for MCP JSON-RPC communication.*

### 3. Run with Mounted Credentials (Local Dev / ADC)
If you want to use your local `gcloud` login:

```bash
docker run -i --rm \
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  google-storage-mcp
```

## Integration with Agentic App
1.  **Auth**: App triggers Google OAuth flow.
2.  **Token**: App receives Access Token.
3.  **Spawn**: App uses a Docker client (e.g., Docker SDK for Python/Node) to spawn the container, setting the `GOOGLE_ACCESS_TOKEN` env var.
4.  **Communicate**: App attaches to the container's Stdio to send/receive MCP messages.
