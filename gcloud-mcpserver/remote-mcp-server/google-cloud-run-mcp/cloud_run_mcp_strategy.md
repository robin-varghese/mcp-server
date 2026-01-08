# Google Cloud Run MCP Server Deployment Strategy

## Overview
This document outlines the strategy for deploying the `google-cloud-run-mcp` server using Docker, consistent with the existing `google-storage-mcp` implementation. This server enables agentic applications to deploy and manage Cloud Run services.

## Architecture
- **Server Image**: Built from `node:20`, installs `gcloud` CLI (optional helper), and runs `@google-cloud/cloud-run-mcp`.
- **Authentication**: Credentials are **not** baked into the image. They are passed at runtime via environment variables or volume mounts.

## Authentication Strategy
The agentic application (client) performs the OAuth flow (or uses existing credentials) to authenticate. These credentials must be provided to the Docker container.

### Option 1: Passing Access Token (Recommended for dynamic agentic sessions)
If the agentic application has a valid OAuth 2.0 Access Token, pass it via the `GOOGLE_ACCESS_TOKEN` environment variable.

### Option 2: Mounting Credentials File (Recommended for Local Dev / Service Accounts)
If you have `application_default_credentials.json` (ADC) configured locally (e.g., via `gcloud auth application-default login`), mount the gcloud configuration directory.

## Deployment Commands (Docker)

### 1. Build the Image
```bash
cd google-cloud-run-mcp
docker build -t google-cloud-run-mcp .
```

### 2. Run with Access Token (Agentic Flow)
Assuming the agent application has retrieved an access token:

```bash
export USER_ACCESS_TOKEN="<captured-oauth-token>"

docker run -i --rm \
  -e GOOGLE_ACCESS_TOKEN="$USER_ACCESS_TOKEN" \
  google-cloud-run-mcp
```
*Note: Stdio (`-i`) is used for MCP JSON-RPC communication.*

### 3. Run with Mounted Credentials (Local Dev)
To use your local `gcloud` authentication:

```bash
docker run -i --rm \
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  google-cloud-run-mcp
```

## Available Tools (Likely, based on @google-cloud/cloud-run-mcp)
- `list-services`: List Cloud Run services in a project.
- `get-service`: Get details of a specific service.
- `get-service-log`: Retrieve logs for a service.
- `deploy-file-contents`: Deploy a service from file contents directly.

## Integration with Agentic App
1.  **Auth**: App triggers Google OAuth flow.
2.  **Token**: App receives Access Token.
3.  **Spawn**: App uses a Docker client to spawn the container, setting `GOOGLE_ACCESS_TOKEN`.
4.  **Communicate**: App interacts with the MCP server via Stdio.
