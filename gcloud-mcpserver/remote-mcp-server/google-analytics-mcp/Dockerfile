FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Google Analytics MCP server
RUN pip install analytics-mcp

# Copy wrapper script
COPY server_wrapper.py /app/server_wrapper.py

# Create app directory
WORKDIR /app

# Set entrypoint to run Google Analytics MCP server via wrapper
ENTRYPOINT ["python3", "/app/server_wrapper.py"]
