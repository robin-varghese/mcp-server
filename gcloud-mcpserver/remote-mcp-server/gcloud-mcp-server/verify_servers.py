import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def check_server(name, image_name):
    print(f"Checking {name} ({image_name})...")
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "--network", "host",
            "-v", f"{os.path.expanduser('~')}/.config/gcloud:/root/.config/gcloud",
            image_name
        ],
        env=None
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                print(f"✅ {name} is running. Found {len(tools.tools)} tools.")
                # Print first 3 tools to keep output clean
                for t in tools.tools[:3]:
                    print(f"  - {t.name}")
                if len(tools.tools) > 3:
                    print(f"  ... and {len(tools.tools) - 3} more")
                return True
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

async def main():
    print("Verifying MCP Servers...")
    
    gcloud_ok = await check_server("GCloud MCP Server", "gcloud-mcp-image")
    print("-" * 20)
    monitoring_ok = await check_server("Monitoring MCP Server", "gcloud-monitoring-mcp-image")
    
    if gcloud_ok and monitoring_ok:
        print("\n✅ Both servers are running as expected.")
    else:
        print("\n❌ Some servers failed to respond.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ImportError:
        print("Error: 'mcp' package is not installed. Please install it with 'pip install mcp'.")
    except Exception as e:
        print(f"Unexpected error: {e}")
