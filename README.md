# MCP Servers

This repository hosts a collection of Model Context Protocol (MCP) servers designed to provide AI agents with context and tools for interacting with various external services.

## Server Index
*   **[gcloud-mcpserver](./gcloud-mcpserver)**: Comprehensive Google Cloud Platform suite.
    *   [Core GCloud](./gcloud-mcpserver/remote-mcp-server/gcloud-mcp-server) (Compute, Resources)
    *   [Google Analytics](./gcloud-mcpserver/remote-mcp-server/google-analytics-mcp) (GA4 Reports)
    *   [Google Storage](./gcloud-mcpserver/remote-mcp-server/google-storage-mcp) (GCS Buckets)
    *   [Cloud Monitoring](./gcloud-mcpserver/remote-mcp-server/gcloud-monitoring-mcp) (Metrics & Logs)
    *   [Database Toolbox](./gcloud-mcpserver/google-db-mcp-toolbox) (Postgres/SQL)
*   **[github-mcp-server](./github-mcp-server)**: GitHub repository management (Issues, PRs, Code).
*   **[sequentialthinking](./sequentialthinking)**: Advanced reasoning and thought tracking for agents.
*   **[filesystem](./filesystem)**: Local file manipulation with Linux-like capabilities.
*   **[brave-search](./brave-search)**: Privacy-focused web and local search using Brave API.
*   **[puppeteer](./puppeteer)**: Headless browser automation (Screenshots, Navigation, Interaction).

## Release History

### v0.4.0 (2025-01-15)
- **Puppeteer Support**: Added `puppeteer` MCP server for browser automation (Dockerized with headless Chromium).

### v0.3.0 (2025-01-15)
- **Brave Search**: Added `brave-search` MCP server (requires API Key).
- **Filesystem Support**: Added `filesystem` MCP server for local file management with Linux-like emulation (`cd`, `ls -l`).
- **Sequential Thinking**: Added `sequentialthinking` server to improve agent reasoning capabilities with persistent thought tracking.
- **Google Analytics**: Added `google-analytics-mcp` for querying GA4 reports.

## Available Servers

### [gcloud-mcpserver](./gcloud-mcpserver)
An MCP server that enables interaction with Google Cloud Platform (GCP) services. It allows agents to perform tasks such as:
- Managing Compute Engine instances
- interacting with Cloud Storage
- querying resources via `gcloud` CLI wrappers

It includes the following specialized components:

#### [gcloud-mcp-server](./gcloud-mcpserver/remote-mcp-server/gcloud-mcp-server)
A general-purpose server for GCloud operations, including:
- **Core Operations**: Executing arbitrary `gcloud` commands.
- **Cost Optimization**: Interacting with `gcloud recommender` to find idle resources (VMs, IPs, Disks) and rightsizing opportunities.
- **Includes**: An interactive NLP client for natural language command execution.

#### [google-db-mcp-toolbox](./gcloud-mcpserver/google-db-mcp-toolbox)
A focused toolbox for database interactions, specifically PostgreSQL.
- **Features**: Translates MCP tool calls into SQL queries.
- **Usage**: Enables AI agents to query databases using a standardized interface.
- **Components**: Includes a server, an interactive client, and pgAdmin for monitoring.

#### [gcloud-monitoring-mcp](./gcloud-mcpserver/remote-mcp-server/gcloud-monitoring-mcp)
Dedicated to Google Cloud observability (Monitoring and Logging).
- **Tools**:
    - `query_time_series`: Fetch metrics (CPU, memory, etc.) from Cloud Monitoring.
    - `query_logs`: Search Cloud Logging entries with filters.
    - `list_metrics`: Discover available metrics in a project.

#### [google-storage-mcp](./gcloud-mcpserver/remote-mcp-server/google-storage-mcp)
Focused specifically on Google Cloud Storage operations.
- **Capabilities**: Listing buckets, listing objects, reading/writing content, and deleting objects.
- **Auth Strategy**: Supports dynamic authentication via OAuth access tokens or mounted credentials.

### [github-mcp-server](./github-mcp-server)
An MCP server for GitHub, facilitating interactions such as:
- Searching repositories
- Reading file contents
- Listing branches and commits
- Managing issues and pull requests (capabilities dependent on implementation)

### [google-analytics-mcp](./gcloud-mcpserver/remote-mcp-server/google-analytics-mcp)
Allows agents to query GA4 reports providing insights into web traffic and user behavior.
- **Core Tool**: `run_report` (supports dimensions, metrics, date ranges).
- **Authentication**: Uses `GOOGLE_ACCESS_TOKEN` for secure API access.

### [sequentialthinking](./sequentialthinking)
Enhances agent reasoning by allowing it to break down complex problems into a structured sequence of thoughts.
- **Features**: Dynamic thought generation, branching/forking thoughts, and revision history.
- **Persistence**: Supports saving thought processes to JSON files (if volume mounted).
- **Best For**: Complex logic puzzles, code architecture planning, and debugging.

### [filesystem](./filesystem)
A robust server for local file system interactions with advanced client-side emulation.
- **Tools**: `read`, `write`, `list`, `search`, `move`, `get_info`.
- **Linux Emulation**: The interactive client supports `cd` (stateful CWD), `ls -all` (detailed listings), and resolving relative paths.
- **Security**: Requires explicit volume mounting (Client defaults to current directory).

### [brave-search](./brave-search)
Integration with Brave Search API for web and local discovery.
- **Tools**: `brave_web_search`, `brave_local_search`.
- **Privacy**: No tracking or profiling of search queries.
- **Emulation**: Includes an interactive client for testing search queries naturally.
- **Requirement**: Needs a `BRAVE_API_KEY` (Free tier available).

### [puppeteer](./puppeteer)
Browser automation using headless Chrome.
- **Tools**: `navigate`, `screenshot`, `click`, `fill`, `evaluate`.
- **Environment**: Containerized with all necessary fonts and dependencies for headless execution.
- **Compatibility**: Supports ARM64 (e.g., Apple Silicon) and AMD64 via system Chromium.


## Local Deployment Instructions

Most servers in this repository are containerized using Docker. Below are the general steps to deploy them locally.

### Prerequisites
1.  **Docker**: Ensure Docker Desktop is installed and running.
2.  **Authentication**:
    *   **GCloud**: Run `gcloud auth login` on your host machine to create credentials that can be shared with the container.
    *   **GitHub**: Generate a Personal Access Token (PAT).
    *   **Google API Key**: Required if you want to use the NLP-powered interactive clients.

### Deploying Specific Servers

#### 1. GCloud MCP Server
```bash
cd gcloud-mcpserver/remote-mcp-server/gcloud-mcp-server
# Build the image
docker build -t gcloud-mcp-image .

# Run manually (or use the interactive client)
docker run -i --rm \
  -v ~/.config/gcloud:/root/.config/gcloud \
  gcloud-mcp-image
```

#### 2. GitHub MCP Server
```bash
cd github-mcp-server
# Build the image
docker build -t local-github-mcp .

# Run with your token
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
docker run -i --rm \
  -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN" \
  local-github-mcp
```

#### 3. Google Storage MCP
```bash
cd gcloud-mcpserver/remote-mcp-server/google-storage-mcp
# Build
docker build -t google-storage-mcp .
```

#### 4. Database Toolbox
This uses Docker Compose:
```bash
cd gcloud-mcpserver/google-db-mcp-toolbox
docker-compose up -d
```

#### 5. Google Analytics MCP
```bash
cd gcloud-mcpserver/remote-mcp-server/google-analytics-mcp
# Build
docker build -t analytics-mcp .
```

#### 6. Sequential Thinking MCP
```bash
cd sequentialthinking
# Build
docker build -t sequentialthinking .
```

#### 7. Filesystem MCP
```bash
cd filesystem
# Build
docker build -t filesystem .
```

#### 8. Brave Search MCP
```bash
cd brave-search
# Build
docker build -t brave-search .
```

#### 9. Puppeteer MCP
```bash
cd puppeteer
# Build
docker build -t puppeteer-mcp .
```

---

## Agentic AI Implementation (Interactive Client)

These servers come with **Interactive Clients** (`*_interactive.py`) that demonstrate how an Agentic AI can interact with the tools. These clients use **Google Gemini** (via `google-genai` SDK) to translate natural language into specific MCP tool calls.

### How it Works
1.  **User Input**: You type a natural language command (e.g., "List all VMs in us-central1").
2.  **Translation**: The script sends this prompt to Gemini (Flash model).
3.  **Tool Call Generation**: Gemini returns a structured tool call (e.g., `run_gcloud_command command="gcloud compute instances list ..."`).
4.  **Execution**: The script executes the tool against the Dockerized MCP server.
5.  **Response**: The result is displayed to the user.

### Running the Interactive Clients

Ensure you have your `GOOGLE_API_KEY` exported:
```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

#### GCloud Client
```bash
cd gcloud-mcpserver/remote-mcp-server/gcloud-mcp-server
python gcloud_mcp_interactive.py
```
*Example: "Find idle IP addresses in my project"*

#### GitHub Client
```bash
cd github-mcp-server
python github_mcp_interactive.py
# You will be prompted for your GitHub PAT if not set in env
```
*Example: "Show me the issues in microsoft/vscode"*

#### Storage Client
```bash
cd gcloud-mcpserver/remote-mcp-server/google-storage-mcp
python storage_mcp_interactive.py
```
*Example: "List files in bucket my-data-bucket"*

#### Database Client
```bash
cd gcloud-mcpserver/google-db-mcp-toolbox
python db_mcp_interactive.py
```
*Example: "Show me the top 10 users by order count"*

#### Google Analytics Client
```bash
cd gcloud-mcpserver/remote-mcp-server/google-analytics-mcp
# Requires valid Access Token
export GOOGLE_ACCESS_TOKEN=$(gcloud auth print-access-token)
python analytics_interactive.py
```
*Example: "Get total users and active users for the last 28 days"*

#### Sequential Thinking Client
```bash
cd sequentialthinking
python sequentialthinking_interactive.py
```
*Example: "Plan a complex microservices architecture"* (The agent will loop through thoughts)

#### Filesystem Client
```bash
cd filesystem
# Run from the directory you want to manage!
python filesystem_interactive.py
```
*Example: "ls -all", "create file src/main.py", "cd src"*

#### Brave Search Client
```bash
cd brave-search
export BRAVE_API_KEY="your-brave-key"
python brave_search_interactive.py
```
*Example: "Search for best hiking trails in Colorado"*

#### Puppeteer Client
```bash
cd puppeteer
# NLP is optional but recommended
export GOOGLE_API_KEY="your-gemini-key"
python puppeteer_interactive.py
```
*Example: "Go to github.com and take a screenshot"*
