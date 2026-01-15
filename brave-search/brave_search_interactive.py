#!/usr/bin/env python3
"""
Interactive Client for Brave Search MCP Server

This script provides a REPL interface to interact with the Brave Search MCP server.
It connects to the Docker container and allows executing search operations.
"""

import asyncio
import os
import shlex
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Configuration
DOCKER_IMAGE = "brave-search"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")

SYSTEM_INSTRUCTION = """
You are an expert assistant for the Brave Search MCP Server.
Your job is to translate the user's natural language search requests into MCP tool calls.

Tool: brave_search
Available tools:
- brave_web_search(query: str, count: int = 10, offset: int = 0): Performs a web search.
- brave_local_search(query: str, count: int = 5): Searches for local businesses and places.

Output Format:
Return ONLY the command string in the format: tool_name key=value key2=value2

Examples:
User: "Search for the latest news on AI"
Output: brave_web_search query="latest news on AI"

User: "Find pizza places near Central Park"
Output: brave_local_search query="pizza near Central Park" count=5

User: "What is the capital of France?"
Output: brave_web_search query="capital of France"
"""

class BraveSearchAgent:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
        self.chat = None
        if HAS_GENAI and api_key:
            self.client = genai.Client(api_key=api_key)
            self.chat = self.client.chats.create(
                model="gemini-2.0-flash-exp",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1
                )
            )

    def generate_tool_call(self, prompt: str) -> str:
        if not self.chat:
            return prompt
        
        try:
            response = self.chat.send_message(prompt)
            result = response.text.strip()
            # Clean up potential markdown
            if result.startswith("```"):
                result = result.split("\n", 1)[1]
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]
            return result.strip()
        except Exception as e:
            print(f"⚠️ NLP Translation failed: {e}")
            return prompt

def parse_command(cmd_str):
    """Parses a command string into tool name and arguments dict."""
    try:
        parts = shlex.split(cmd_str)
        if not parts:
            return None, {}
        
        tool_name = parts[0]
        tool_args = {}
        
        for arg in parts[1:]:
            if '=' in arg:
                k, v = arg.split('=', 1)
                try:
                    if v.lower() == 'true': v = True
                    elif v.lower() == 'false': v = False
                    elif v.isdigit(): v = int(v)
                    elif (v.startswith('[') and v.endswith(']')) or (v.startswith('{') and v.endswith('}')):
                        v = json.loads(v.replace("'", '"'))
                except:
                    pass
                tool_args[k] = v
        return tool_name, tool_args
    except Exception as e:
        print(f"⚠️ Error parsing command: {e}")
        return None, {}

async def run_interactive_session():
    print(f"Starting Interactive Brave Search MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    global BRAVE_API_KEY
    if not BRAVE_API_KEY:
        print("⚠️ BRAVE_API_KEY not found in env.")
        user_key = input("Enter Brave API Key (Required): ").strip()
        if user_key:
            BRAVE_API_KEY = user_key
        else:
            print("❌ Brave API Key is required. Exiting.")
            return

    agent = BraveSearchAgent(GOOGLE_API_KEY)
    
    if agent.client:
        print("✨ NLP Enabled: You can use natural language search queries.")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Brave Search MCP Server")
                
                print("\nDiscovering tools...")
                try:
                    response = await session.list_tools()
                    tools = response.tools
                    tool_names = [t.name for t in tools]
                    print(f"Available Tools: {', '.join(tool_names)}")
                except Exception as e:
                    print(f"⚠️ Could not list tools: {e}")

                print("\n" + "="*50)
                print("ENTER SEARCH QUERIES (type 'exit' or 'quit' to stop)")
                print("Examples:")
                print("  > Latest advancements in fusion energy")
                print("  > Thai restaurants in San Francisco")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\nbrave-search> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        cmd_str = agent.generate_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")

                        tool_name, tool_args = parse_command(cmd_str)
                        if not tool_name:
                            continue

                        print(f"Executing: {tool_name} with {tool_args} ...")
                        
                        try:
                            result = await session.call_tool(tool_name, arguments=tool_args)
                            
                            for content in result.content:
                                if content.type == "text":
                                    print(content.text)
                                else:
                                    print(f"[{content.type} content]")
                                    
                        except Exception as e:
                            print(f"❌ Tool execution failed: {e}")

                    except KeyboardInterrupt:
                        print("\nCancelled.")
                    except Exception as e:
                        print(f"Error: {e}")

    except Exception as e:
        print(f"\nFailed to connect/run: {e}")

def get_server_params():
    cmd = [
        "docker", "run", "-i", "--rm",
        "-e", f"BRAVE_API_KEY={BRAVE_API_KEY}",
        DOCKER_IMAGE
    ]
    return StdioServerParameters(
        command=cmd[0],
        args=cmd[1:],
        env=None
    )

if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print("\nExiting...")
