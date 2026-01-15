# Strategy: Google Analytics MCP Server in Docker

This document outlines the strategy to containerize and deploy the Google Analytics MCP server (`google-analytics-mcp`) for use by AI agents.

## 1. Overview
The goal is to host the `google-analytics-mcp` server within a Docker container. This allows an agentic application to perform Google Analytics operations (e.g., running reports, listing credentials) via the Model Context Protocol (MCP), with a consistent environment and isolated dependencies.

## 2. Prerequisites
Before building the server, ensure the following are prepared:

*   **Google Cloud Project**: A valid GCP project with the following APIs enabled:
    *   Google Analytics Admin API
    *   Google Analytics Data API
*   **Google Analytics Access**: The authenticated user must have access to the GA4 properties.
*   **Authentication**:
    *   **OAuth Token**: This implementation uses `GOOGLE_ACCESS_TOKEN` for robust authentication.
    *   **Host Credentials**: Can also use host credential sharing via `~/.config/gcloud`.
*   **Docker**: Installed on the host machine.

## 3. Docker Image Strategy
The Docker image bundles the official `analytics-mcp` package and a custom wrapper for enhanced authentication.

### Dockerfile Specification
*   **Base Image**: `python:3.12-slim`
*   **Package**: `analytics-mcp` (Official PyPI package)
*   **Wrapper**: `server_wrapper.py` intercepts `GOOGLE_ACCESS_TOKEN` to force OAuth authentication, overriding default ADC behavior when a token is provided.
*   **Entrypoint**: `python3 /app/server_wrapper.py`

## 4. Capabilities & Tools
The server exposes the following MCP tools for AI agents:

| Tool Name | Description | Arguments |
|-----------|-------------|-----------|
| `get_account_summaries` | List accessible GA4 accounts and property summaries. | None |
| `list_google_ads_links` | List Google Ads links for a property. | `property_id` |
| `get_property_details` | Retrieve metadata for a specific property. | `property_id` |
| `get_custom_dimensions_and_metrics` | List custom definitions for a property. | `property_id` |
| `run_realtime_report` | Execute a realtime report query. | `property_id`, `dimensions`, `metrics`, `limit`, etc. |
| `run_report` | Execute a core report query (historical data). | `property_id`, `date_ranges`, `dimensions`, `metrics`, etc. |

## 5. Connection Strategy

### Configuration
In your agent's MCP configuration:

```json
{
  "mcpServers": {
    "analytics": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network", "host",
        "-e", "GOOGLE_ACCESS_TOKEN",
        "-v", "$HOME/.config/gcloud:/root/.config/gcloud",
        "google-analytics-mcp"
      ],
      "env": {
        "GOOGLE_ACCESS_TOKEN": "${env:GOOGLE_ACCESS_TOKEN}"
      }
    }
  }
}
```

### Authentication Flow
1.  **Agent/Host** obtains an OAuth access token (e.g., via `gcloud auth print-access-token`).
2.  **Agent** passes this token as the `GOOGLE_ACCESS_TOKEN` environment variable to the Docker container.
3.  **Wrapper Script** (`server_wrapper.py`) inside the container detects the token.
4.  **Patching**: The wrapper patches `google.auth.default()` to return credentials created from this token.
5.  **MCP Server** initializes using these credentials, ensuring all operations perform as the authenticated user.

## 6. Testing & Verification

### Using the Interactive Client
A Python-based interactive client is provided for testing and manual operations.

```bash
# 1. Get an access token
export GOOGLE_ACCESS_TOKEN=$(gcloud auth print-access-token)

# 2. (Optional) Set API Key for NLP features
export GOOGLE_API_KEY="your-gemini-api-key"

# 3. Run the client
python3 gcloud-mcpserver/remote-mcp-server/google-analytics-mcp/analytics_interactive.py
```

### Sample Commands (NLP)
*   "list my accounts"
*   "show active users for property 123456"
*   "what are the top events for last week in property 987654"

## 7. Implementation Details
*   **Directory**: `gcloud-mcpserver/remote-mcp-server/google-analytics-mcp`
*   **Files**:
    *   `Dockerfile`: Builds the image.
    *   `server_wrapper.py`: Auth interception logic.
    *   `analytics_interactive.py`: Client for testing.
