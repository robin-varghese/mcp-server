#!/usr/bin/env python3
"""
Interactive Client for Google Storage MCP Server

This script provides a REPL interface to interact with the Storage MCP server.
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
DOCKER_IMAGE = "google-storage-mcp"
# Default to mounting local gcloud config if no token is provided
MOUNT_PATH = f"{os.path.expanduser('~')}/.config/gcloud:/root/.config/gcloud"
GOOGLE_ACCESS_TOKEN = os.environ.get("GOOGLE_ACCESS_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def get_server_params():
    cmd = ["docker", "run", "-i", "--rm"]
    
    # If a token is present, pass it as env var
    if GOOGLE_ACCESS_TOKEN:
        cmd.extend(["-e", f"GOOGLE_ACCESS_TOKEN={GOOGLE_ACCESS_TOKEN}"])
    else:
        # Otherwise mount credentials
        cmd.extend(["-v", MOUNT_PATH])
        
    cmd.append(DOCKER_IMAGE)
    
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
        You are an expert Google Cloud Storage assistant.
        Translate the user's natural language request into a valid Tool Call for the 'storage-mcp' server.
        
        Available Tools:
        - list_buckets(project_id=str)
        - list_objects(bucket=str, prefix=str optional)
        - read_object_content(bucket=str, object=str)
        - get_bucket_metadata(bucket=str)
        - get_bucket_location(bucket=str)
        
        Output Format:
        Return ONLY the command string in the format: tool_name key=value key2=value2
        
        Rules:
        1. If the user asks to list buckets, use project_id.
        2. If the user asks for files/objects, use list_objects.
        3. If the user asks to read/cat/show content of a file, use read_object_content.
        4. Do NOT output markdown or explanations. Just the raw command string.
        5. If you cannot understand or map the request, return the prompt as is or "Need more info: ..."
        
        Examples:
        User: "list buckets in project my-p-123"
        Output: list_buckets project_id=my-p-123
        
        User: "show files in bucket my-data"
        Output: list_objects bucket=my-data
        
        User: "read config.json from bucket app-conf"
        Output: read_object_content bucket=app-conf object=config.json
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
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
    print(f"Starting Interactive Storage MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    if HAS_GENAI and GOOGLE_API_KEY:
        print("✨ NLP Enabled: You can use natural language (e.g., 'list buckets in my-project')")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax (e.g., 'list_buckets project_id=foo')")

    if GOOGLE_ACCESS_TOKEN:
        print("🔑 Using provided GOOGLE_ACCESS_TOKEN")
    else:
        print(f"📂 Mounting local credentials from: {MOUNT_PATH}")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Storage MCP Server")
                
                # List tools
                tools = await session.list_tools()
                print("\nGiven the dynamic nature, here are the exact schemas for available tools:")
                for t in tools.tools:
                     args = t.inputSchema.get("properties", {}).keys()
                     print(f"  - {t.name}: {list(args)}")

                print("\n" + "="*50)
                print("ENTER COMMANDS (type 'exit' or 'quit' to stop)")
                print("Examples:")
                print("  > list buckets in project my-project")
                print("  > read file README.md from bucket my-bucket")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\nstorage> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        # Attempt translation first
                        cmd_str = translate_to_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")
                        
                        # Parse input: tool_name key=value key=value
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
                                tool_args[k] = v
                            else:
                                valid_syntax = False
                                print(f"⚠️ Warning: Arg '{arg}' is not in key=value format. NLP might have failed or input is malformed.")
                        
                        if not valid_syntax and cmd_str == user_input:
                             # If we didn't translate and syntax is wrong, it's likely a raw NLP query that failed translation
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
        print("Make sure the Docker image is built: 'docker build -t google-storage-mcp .'")

if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print("\nExiting...")
