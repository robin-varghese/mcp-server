#!/usr/bin/env python3
"""
Interactive Client for Google Analytics MCP Server

This script provides a REPL interface to interact with the Google Analytics MCP server.
It connects to the Docker container and allows executing available tools.
It supports both direct tool execution and Natural Language Processing (NLP) via Gemini.
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
DOCKER_IMAGE = "google-analytics-mcp"
# Default to mounting local gcloud config if no token is provided
MOUNT_PATH = f"{os.path.expanduser('~')}/.config/gcloud:/root/.config/gcloud"
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN")

def get_server_params():
    cmd = ["docker", "run", "-i", "--rm"]
    
    # Pass necessary environment variables
    if GOOGLE_PROJECT_ID:
        cmd.extend(["-e", f"GOOGLE_PROJECT_ID={GOOGLE_PROJECT_ID}"])

    if GOOGLE_ACCESS_TOKEN:
        cmd.extend(["-e", f"GOOGLE_ACCESS_TOKEN={GOOGLE_ACCESS_TOKEN}"])
    
    if GOOGLE_APPLICATION_CREDENTIALS:
         # If credentials file path is provided, we need to make sure the file is mounted
         # But usually for local docker desktop simplicity we mount the whole .config/gcloud or expect user to handle it
         # For simplicity in this script, we assume the standard mount or passed credentials content via env var if supported by lib
         # The google-analytics-mcp docs say to set GOOGLE_APPLICATION_CREDENTIALS to a path.
         # So we must mount the file if it's a file path.
         
         # If it's a path on host, we should mount it. 
         # Simplification: We assume the user might have set up ADC via gcloud and we default to mounting ~/.config/gcloud
         pass

    # Mount gcloud config for ADC
    # The container runs as root by default in this simple Dockerfile, so we map to /root/.config/gcloud
    cmd.extend(["-v", MOUNT_PATH])
        
    cmd.append(DOCKER_IMAGE)
    
    # Debug print
    # print(f"DEBUG: Running command: {' '.join(cmd)}")

    return StdioServerParameters(
        command=cmd[0],
        args=cmd[1:],
        env=None
    )

def translate_to_tool_call(prompt: str) -> str:
    """Translate natural language prompt to a tool call using Gemini."""
    if not HAS_GENAI or not GOOGLE_API_KEY:
        return prompt

    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        system_instruction = """
        You are an expert Google Analytics assistant.
        Translate the user's natural language request into a valid Tool Call for the 'analytics-mcp' server.
        
        Expected tools (examples, may vary based on dynamic discovery):
        - get_account_summaries()
        - run_report(property_id=str, dimensions=list, metrics=list, date_ranges=list, ...)
        - run_realtime_report(property_id=str, dimensions=list, metrics=list, ...)
        - get_metadata(property_id=str)
        
        Output Format:
        Return ONLY the command string in the format: tool_name key=value key2=value2
        For list arguments, use JSON strings or valid python representation if simple.
        
        Rules:
        1. Parse the property_id from the request if possible.
        2. Do NOT output markdown or explanations. Just the raw command string.
        3. If you cannot understand or map the request, return the prompt as is.
        
        Examples:
        User: "list account summaries"
        Output: get_account_summaries
        
        User: "show popular events for property 123456"
        Output: run_report property_id=123456 dimensions=['eventName'] metrics=['eventCount'] date_ranges=[{'startDate': '30daysAgo', 'endDate': 'today'}]
        """
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        
        result = response.text.strip()
        # Clean up any potential markdown code blocks
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result.rsplit("\n", 1)[0]
        return result.strip()
        
    except Exception as e:
        print(f"⚠️ NLP Translation failed: {e}")
        return prompt

async def run_interactive_session():
    print(f"Starting Interactive Google Analytics MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    if HAS_GENAI and GOOGLE_API_KEY:
        print("✨ NLP Enabled: You can use natural language (e.g., 'list my accounts')")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax")

    print(f"📂 Mounting local credentials from: {MOUNT_PATH}")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Google Analytics MCP Server")
                
                # List tools
                print("\nDiscovering tools...")
                tools = await session.list_tools()
                print("\nAvailable Tools:")
                for t in tools.tools:
                     args = t.inputSchema.get("properties", {}).keys()
                     print(f"  - {t.name}: {list(args)}")

                print("\n" + "="*50)
                print("ENTER COMMANDS (type 'exit' or 'quit' to stop)")
                print("Examples:")
                print("  > list accounts")
                print("  > run report property_id=... metrics=['activeUsers']")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\nanalytics-mcp> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        # Attempt translation first
                        cmd_str = translate_to_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")
                        
                        # Parse input: tool_name key=value key=value
                        # Basic parsing that handles quoted values roughly would be better but shlex suffices for simple cases
                        parts = shlex.split(cmd_str)
                        if not parts:
                            continue
                            
                        tool_name = parts[0]
                        tool_args = {}
                        
                        # Simple parsing of key=value
                        valid_syntax = True
                        for arg in parts[1:]:
                            if '=' in arg:
                                k, v = arg.split('=', 1)
                                # Try to parse JSON values for lists/dicts
                                try:
                                    if (v.startswith('[') and v.endswith(']')) or (v.startswith('{') and v.endswith('}')):
                                        v = json.loads(v.replace("'", '"')) # Simple quote fix try
                                except:
                                    pass
                                tool_args[k] = v
                            else:
                                valid_syntax = False
                                print(f"⚠️ Warning: Arg '{arg}' is not in key=value format. NLP might have failed or input is malformed.")
                        
                        if not valid_syntax and cmd_str == user_input:
                             print("💡 Tip: Set GOOGLE_API_KEY to enable smart translation.")

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
        print(f"Make sure the Docker image is built: 'docker build -t {DOCKER_IMAGE} .'")

if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print("\nExiting...")
