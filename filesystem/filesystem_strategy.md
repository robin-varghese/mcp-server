# Strategy: Filesystem MCP Server in Docker

This document outlines the strategy to containerize and deploy the Filesystem MCP server (`@modelcontextprotocol/server-filesystem`).

## 1. Overview
The goal is to host the Filesystem MCP server within a Docker container. This server provides tools for reading, writing, and managing files and directories.

## 2. Docker Image Strategy

### Dockerfile Specification
*   **Base Image**: `node:20-slim`
*   **Package**: `@modelcontextprotocol/server-filesystem` (Official NPM package)
*   **Entrypoint**: `npx -y @modelcontextprotocol/server-filesystem`
*   **Arguments**: Requires allowed paths as arguments (e.g., `/projects`).

## 3. Capabilities & Tools
The server exposes the following MCP tools for controlled file access:

| Tool Name | Description | Inputs |
|-----------|-------------|--------|
| `read_text_file` | Read complete file text | `path` |
| `write_file` | Create/overwrite file | `path`, `content` |
| `list_directory` | List contents | `path` |
| `list_directory_with_sizes` | Detailed listing with sizes/stats | `path` |
| `create_directory` | Create directory | `path` |
| `move_file` | Move/rename | `source`, `destination` |
| `get_file_info` | Get metadata | `path` |
| `search_files` | Recursive search | `path`, `pattern` |

### Client-Side Features (Interactive Client)
The interactive client adds simulated shell behavior:
*   **Linux Emulation**: Supports `cd`, `ls`, `mkdir`, and relative paths.
*   **Stateful CWD**: Tracks your current working directory across commands.
*   **Detailed Listings**: `ls -l`, `ls -all`, and `ll` map to `list_directory_with_sizes`.
*   **Auto-Mounting**: Automatically mounts your **current local directory** to `/projects`.

## 4. Connection Strategy

### Configuration
In your agent's MCP configuration, you must mount the directories you want to expose.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--mount", "type=bind,src=/Users/username/data,dst=/projects/data",
        "filesystem",
        "/projects/data"
      ]
    }
  }
}
```

## 5. Verification

### Using the Interactive Client
A Python-based interactive client is provided. It *automatically* mounts your **current working directory** (where you run the script from) to `/projects` in the container.

```bash
# 1. Build the image
docker build -t filesystem mcp-servers/filesystem

# 2. (Optional) Set API Key for NLP features
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Run the client
# IMPORTANT: Run this from the directory you want to work on!
python3 mcp-servers/filesystem/filesystem_interactive.py
```

### Sample Commands (NLP & Shell-Like)
*   "List files" or just `ls`
*   "Show details" or `ls -all`
*   "Create a hello.txt file with some content"
*   `mkdir src`
*   `cd src`
*   `read_text_file app.py` (reads relative to current directory)

## 6. Limitations (Cloud Deployment)
This server is designed for **local** use via Docker. It is **NOT** suitable for direct deployment to serverless platforms like Google Cloud Run in its current form.

*   **Communication Protocol**: Cloud Run requires an HTTP server. This server uses Standard IO (stdio), so it would need an SSE/HTTP adapter to function.
*   **Data Persistence**: Cloud Run filesystems are ephemeral. Any files written would be lost upon container restart. A persistent volume (like Cloud Storage FUSE) would be required for meaningful usage.
