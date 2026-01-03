#!/usr/bin/env python3
"""
Interactive MCP Database Client for Google MCP Toolbox
Uses the official toolbox-core SDK to interact with the server
"""

import asyncio
import requests

TOOLBOX_URL = "http://localhost:5001"

# Tools we know exist from our tools.yaml configuration
KNOWN_TOOLS = {
    "list_tables": "List all tables in the database",
    "query_database": "Run a read-only SQL query on the database"
}

def test_connection():
    """Test if the toolbox server is reachable."""
    try:
        response = requests.get(TOOLBOX_URL, timeout=2)
        if response.status_code == 200:
            print(f"✅ Connected to MCP Toolbox at {TOOLBOX_URL}")
            print(f"   Response: {response.text.strip()}\n")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {TOOLBOX_URL}")
        print("   Make sure docker-compose is running:")
        print("   cd google-db-mcp-toolbox && docker-compose up -d\n")
        return False

async def run_tool(tool_name, params=None):
    """Load and call a tool using the SDK."""
    try:
        from toolbox_core import ToolboxClient
        
        async with ToolboxClient(url=TOOLBOX_URL) as client:
            print(f"\n🔧 Loading tool '{tool_name}'...")
            tool = await client.load_tool(name=tool_name)
            
            print(f"📝 Calling tool...")
            # Use the correct method - tools are callable
            if params:
                result = await tool(**params)
            else:
                result = await tool()
            
            print(f"\n✅ Result:")
            print(f"{result}")
            return result
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

async def interactive_session():
    """Run an interactive session."""
    print("=" * 70)
    print("🧰 MCP Database Toolbox - Interactive Test Client")
    print("=" * 70)
    
    if not test_connection():
        return
        
    print("📋 Available Tools (from config/tools.yaml):")
    for name, desc in KNOWN_TOOLS.items():
        print(f"   - {name}: {desc}")
    
    print("\n" + "=" * 70)
    print("Commands:")
    print("  list tables        - List all database tables")
    print("  query <SQL>        - Run a SQL query")
    print("  help               - Show this help")
    print("  exit               - Exit")
    print("=" * 70)
    
    while True:
        try:
            user_input = await asyncio.to_thread(input, "\n🔧 > ")
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            # Normalize for comparison
            normalized = user_input.lower()
                
            if normalized in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
                
            elif normalized in ['help', '?', 'show this help']:
                print("\nCommands:")
                print("  list tables        - List all database tables")
                print("  query <SQL>        - Run a SQL query")
                print("  exit               - Exit")
                
            elif normalized in ["list tables", "show tables", "list all tables", 
                               "list all database tables", "tables"]:
                await run_tool("list_tables")
                
            elif normalized.startswith("query "):
                sql = user_input[6:].strip()
                if sql:
                    await run_tool("query_database", {"query": sql})
                else:
                    print("⚠️  Please provide a SQL query")
                    print("   Example: query SELECT 1")
            
            # Allow direct SQL queries without "query" prefix
            elif any(normalized.startswith(kw) for kw in ["select ", "show ", "describe ", "explain "]):
                await run_tool("query_database", {"query": user_input})
                    
            else:
                print(f"⚠️  Unknown command: {user_input}")
                print("   Type 'help' for available commands")
                print("\n   Quick examples:")
                print("   - list tables")
                print("   - query SELECT * FROM your_table LIMIT 5")
                print("   - SELECT 1  (direct SQL)")
                
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    try:
        from toolbox_core import ToolboxClient
    except ImportError:
        print("❌ toolbox-core SDK not installed")
        print("   Install with: pip install toolbox-core\n")
        return
    
    try:
        asyncio.run(interactive_session())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")

if __name__ == "__main__":
    main()
