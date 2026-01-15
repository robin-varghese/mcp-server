#!/usr/bin/env python3
"""
Interactive Client for Puppeteer MCP Server

This script provides a REPL interface to interact with the Puppeteer MCP server.
It connects to the Docker container and allows performing browser automation tasks.
"""

import asyncio
import os
import shlex
import sys
import json
import base64
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ImageContent, TextContent

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Configuration
DOCKER_IMAGE = "puppeteer-mcp"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

SYSTEM_INSTRUCTION = """
You are an expert assistant for the Puppeteer MCP Server.
Your job is to translate the user's natural language browser automation requests into MCP tool calls.

Tool: puppeteer
Available tools:
- puppeteer_navigate(url: str): Go to a URL.
- puppeteer_screenshot(name: str = "screenshot", width: int = 800, height: int = 600): Take a screenshot.
- puppeteer_click(selector: str): Click an element.
- puppeteer_fill(selector: str, value: str): Fill an input field.
- puppeteer_evaluate(script: str): Execute JavaScript in the console.
- puppeteer_hover(selector: str): Hover over an element.

Output Format:
Return ONLY the command string in the format: tool_name key=value key2=value2

Examples:
User: "Go to google.com"
Output: puppeteer_navigate url="https://google.com"

User: "Take a screenshot named homepage"
Output: puppeteer_screenshot name="homepage"

User: "Click the search button #submit"
Output: puppeteer_click selector="#submit"

User: "Type 'MCP Servers' into the search box .search-input"
Output: puppeteer_fill selector=".search-input" value="MCP Servers"
"""

class PuppeteerAgent:
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

def save_image(data_base64, name_prefix="screenshot"):
    """Saves a base64 encoded image to disk."""
    try:
        if "," in data_base64:
            data_base64 = data_base64.split(",")[1]
        
        img_data = base64.b64decode(data_base64)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name_prefix}_{timestamp}.png"
        with open(filename, "wb") as f:
            f.write(img_data)
        print(f"📸 Screenshot saved to: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"❌ Failed to save screenshot: {e}")

async def run_interactive_session():
    print(f"Starting Interactive Puppeteer MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    agent = PuppeteerAgent(GOOGLE_API_KEY)
    
    if agent.client:
        print("✨ NLP Enabled: You can use natural language browser commands.")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Puppeteer MCP Server")
                
                print("\nDiscovering tools...")
                try:
                    response = await session.list_tools()
                    tools = response.tools
                    tool_names = [t.name for t in tools]
                    print(f"Available Tools: {', '.join(tool_names)}")
                except Exception as e:
                    print(f"⚠️ Could not list tools: {e}")

                print("\n" + "="*50)
                print("ENTER BROWSER COMMANDS (type 'exit' or 'quit' to stop)")
                print("Examples:")
                print("  > Navigate to github.com")
                print("  > Take a screenshot")
                print("  > Click the login button")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\npuppeteer> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        cmd_str = agent.generate_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")

                        # Handle multiple commands (one per line)
                        commands = [cmd.strip() for cmd in cmd_str.splitlines() if cmd.strip()]
                        
                        for single_cmd in commands:
                            tool_name, tool_args = parse_command(single_cmd)
                            if not tool_name:
                                continue

                            print(f"Executing: {tool_name} with {tool_args} ...")
                            
                            try:
                                result = await session.call_tool(tool_name, arguments=tool_args)
                                
                                for content in result.content:
                                    if content.type == "text":
                                        print(content.text)
                                    elif content.type == "image":
                                        print(f"[Image content received, MIME: {content.mimeType}]")
                                        save_image(content.data)
                                    else:
                                        print(f"[{content.type} content]")
                                        
                            except Exception as e:
                                print(f"❌ Tool execution failed for {tool_name}: {e}")

                    except KeyboardInterrupt:
                        print("\nCancelled.")
                    except Exception as e:
                        print(f"Error: {e}")

    except Exception as e:
        print(f"\nFailed to connect/run: {e}")

def get_server_params():
    # --init is important for puppeteer in docker to avoid zombie processes
    cmd = [
        "docker", "run", "-i", "--rm", "--init",
        "-e", "DOCKER_CONTAINER=true",
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
