FROM --platform=linux/amd64 ubuntu:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Download Toolbox binary
ARG VERSION=0.22.0
RUN curl -L -o /usr/local/bin/toolbox "https://storage.googleapis.com/genai-toolbox/v${VERSION}/linux/amd64/toolbox" \
    && chmod +x /usr/local/bin/toolbox

WORKDIR /app

# Expose HTTP port
EXPOSE 5000

# Run as HTTP server (not stdio)
CMD ["toolbox", "--tools-file", "/app/tools.yaml", "--address", "0.0.0.0", "--port", "5000", "--verbose"]
