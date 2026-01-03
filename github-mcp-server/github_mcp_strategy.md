# GitHub MCP Server Deployment Strategy

## Overview
This document outlines the strategy for deploying the official `github-mcp-server` using Docker.

## Architecture
- **Server Image**: Wraps `ghcr.io/github/github-mcp-server`.
- **Authentication**: Requires a **GitHub Personal Access Token (PAT)** passed via environment variable `GITHUB_PERSONAL_ACCESS_TOKEN`.

## Docker Usage

### 1. Build the Image
```bash
cd github-mcp-server
docker build -t local-github-mcp .
```

### 2. Run with PAT
You must provide a valid GitHub PAT.

```bash
export MY_GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$MY_GITHUB_TOKEN" \
  local-github-mcp
```

### 3. Usage with Toolsets
By default, the server enables: `context`, `repos`, `issues`, `pull_requests`, `users`.
To enable specific toolsets, use `GITHUB_TOOLSETS`:

```bash
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$MY_GITHUB_TOKEN" \
  -e GITHUB_TOOLSETS="repos,issues,actions" \
  local-github-mcp
```

## Integration
To connect an MCP client:
1.  Set the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable.
2.  Spawn the container using `docker run -i ...`.
3.  Communicate over Stdio.


