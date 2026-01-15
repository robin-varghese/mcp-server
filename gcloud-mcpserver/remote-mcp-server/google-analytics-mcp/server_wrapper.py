import os
import sys
import google.auth
from google.oauth2.credentials import Credentials
import analytics_mcp.server

# Patch google.auth.default to return credentials from GOOGLE_ACCESS_TOKEN
original_default = google.auth.default

def patched_default(scopes=None, request=None, quota_project_id=None, default_scopes=None):
    access_token = os.environ.get("GOOGLE_ACCESS_TOKEN")
    if access_token:
        print("Using GOOGLE_ACCESS_TOKEN for authentication")
        # Create credentials from the access token
        creds = Credentials(token=access_token)
        # Return project_id as None (or from env if needed) and the creds
        return creds, os.environ.get("GOOGLE_PROJECT_ID")
    else:
        print("GOOGLE_ACCESS_TOKEN not found, falling back to default auth")
        return original_default(scopes, request, quota_project_id, default_scopes)

# Apply the patch
google.auth.default = patched_default

if __name__ == "__main__":
    print("Starting Google Analytics MCP Server with Auth Wrapper...")
    sys.exit(analytics_mcp.server.run_server())
