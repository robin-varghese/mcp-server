# Looker Integration for MCP Toolbox

The Google MCP Database Toolbox supports connecting to Looker to allow AI agents to query analytics data and dashboards.

## ✅ Verified Support
The toolbox includes built-in support for Looker through **Prebuilt Configurations**.

- **Mode 1: `looker`** - Standard Looker tools (extensions, querying)
- **Mode 2: `looker-conversational-analytics`** - Advanced conversational capabilities

## 🚀 Setup Instructions

### 1. Prerequisites
You need Looker API credentials.
1. Log in to your Looker instance.
2. Go to **Admin** > **Users** > **Edit** (your user) > **API Keys**.
3. Generate a new key to get your `Client ID` and `Client Secret`.

### 2. Configuration (Docker Compose)

To use Looker, update your `docker-compose.yml` to use the `--prebuilt` flag instead of a tools file.

```yaml
services:
  toolbox-looker:
    image: us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:0.22.0
    command: ["toolbox", "--prebuilt", "looker", "--address", "0.0.0.0"]
    ports:
      - "5001:5000"
    environment:
      # Required Connection Details
      LOOKER_BASE_URL: "https://your-instance.looker.com"
      LOOKER_CLIENT_ID: "your_client_id"
      LOOKER_CLIENT_SECRET: "your_client_secret"
      
      # Optional
      LOOKER_VERIFY_SSL: "true"
```

### 3. Available Tools
When connected, the toolbox exposes tools to AI agents such as:

- **`run_look`**: Execute a predefined Look.
- **`run_query`**: Run a custom query against a Looker Explore.
- **`get_dashboard`**: Retrieve dashboard metadata and data.
- **`search_looks`**: Find Looks by title.

## 🤖 AI Agent Example

```python
# User: "How were sales last week?"

# AI Agent calls Looker tool:
await tool.run_look(look_id=123)
```

## ⚠️ Important Note
Unlike the PostgreSQL setup which uses a local database file, Looker integration connects to your **existing cloud Looker instance**. Ensure the toolbox container has internet access to reach your Looker URL.
