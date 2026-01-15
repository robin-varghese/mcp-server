FROM node:20-slim

# Install simple dependencies if needed, but npx handles the server
# The server requires a valid path argument
ENTRYPOINT ["npx", "-y", "@modelcontextprotocol/server-filesystem"]
CMD ["/projects"]
