#!/usr/bin/env python3
"""
Interactive Client for Filesystem MCP Server

This script provides a REPL interface to interact with the Filesystem MCP server.
It connects to the Docker container and allows executing file operations.

CRITICAL:
The Filesystem MCP server requires specific directories to be allowed/mounted.
This client automatically creates a local './test_data' directory and mounts it 
to '/projects' inside the container.
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
DOCKER_IMAGE = "filesystem"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Local testing directory - Defaults to current working directory
LOCAL_TEST_DIR = os.getcwd()
CONTAINER_MOUNT_POINT = "/projects"

SYSTEM_INSTRUCTION = f"""
You are an expert assistant for the Filesystem MCP Server behaving like a Linux shell.
Your job is to translate the user's natural language file requests into MCP tool calls.

Tool: filesystem
Available tools:
- read_text_file(path)
- write_file(path, content)
- list_directory(path): Basic listing of names.
- list_directory_with_sizes(path): Detailed listing with sizes and stats (Use for 'ls -l', 'ls -all', 'details').
- create_directory(path)
- move_file(source, destination)
- get_file_info(path)
- search_files(path, pattern)

# Client-Side Tools (Simulated)
- change_directory(path): Changes the current working directory.

IMPORTANT PATH RULES:
1. You will be provided with the [Current Working Directory].
2. ALWAYS resolve relative paths against this Current Working Directory.
3. The container mount point is '{CONTAINER_MOUNT_POINT}'. All absolute paths must start with this.
4. If the user asks to change directory ('cd'), output a `change_directory` tool call.

Output Format:
Return ONLY the command string in the format: tool_name key=value key2=value2

Examples:
[Current Directory: {CONTAINER_MOUNT_POINT}]
User: "ls"
Output: list_directory path="{CONTAINER_MOUNT_POINT}"

[Current Directory: {CONTAINER_MOUNT_POINT}]
User: "ls -l" (or "ll", "list details")
Output: list_directory_with_sizes path="{CONTAINER_MOUNT_POINT}"

[Current Directory: {CONTAINER_MOUNT_POINT}]
User: "cd test_data"
Output: change_directory path="{CONTAINER_MOUNT_POINT}/test_data"

[Current Directory: {CONTAINER_MOUNT_POINT}/test_data]
User: "read notes.txt"
Output: read_text_file path="{CONTAINER_MOUNT_POINT}/test_data/notes.txt"
"""

class FilesystemAgent:
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

    def generate_tool_call(self, prompt: str, cwd: str) -> str:
        if not self.chat:
            return prompt
        
        try:
            # Inject CWD context into the prompt
            context_prompt = f"[Current Directory: {cwd}]\nUser: {prompt}"
            response = self.chat.send_message(context_prompt)
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
    # ensure_test_dir() -> Removed, we use CWD

    print(f"Starting Interactive Filesystem MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    print(f"Mounting: {LOCAL_TEST_DIR} -> {CONTAINER_MOUNT_POINT}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    agent = FilesystemAgent(GOOGLE_API_KEY)
    
    if agent.client:
        print("✨ NLP Enabled: You can use natural language file commands.")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax")

    current_path = CONTAINER_MOUNT_POINT

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Filesystem MCP Server")
                
                print("\nDiscovering tools...")
                try:
                    response = await session.list_tools()
                    tools = response.tools
                    tool_names = [t.name for t in tools]
                    print(f"Available Tools: {', '.join(tool_names)}")
                except Exception as e:
                    print(f"⚠️ Could not list tools (server might require explicit roots): {e}")

                print("\n" + "="*50)
                print("ENTER COMMANDS (type 'exit' or 'quit' to stop)")
                print(f"Reminder: Files will be created in {LOCAL_TEST_DIR}")
                print(f"      (mapped to /projects)")
                print(f"Linux emulation enabled ('cd', 'ls' work relatively)")
                print("="*50 + "\n")

                while True:
                    try:
                        # Show CWD in prompt
                        display_path = current_path.replace(CONTAINER_MOUNT_POINT, '/projects')
                        user_input = input(f"\nfilesystem [{display_path}]> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        # Pass CWD to agent
                        cmd_str = agent.generate_tool_call(user_input, current_path)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")

                        tool_name, tool_args = parse_command(cmd_str)
                        if not tool_name:
                            continue

                        # Handle Client-Side "cd" simulation
                        if tool_name == "change_directory":
                            new_path = tool_args.get('path')
                            if new_path:
                                # Normalize path slightly (simple string manip)
                                if new_path.startswith(".."):
                                     new_path = os.path.normpath(os.path.join(current_path, new_path))
                                
                                # Basic validation (container side validation would happen on next call usually, but we check prefix)
                                if not new_path.startswith(CONTAINER_MOUNT_POINT):
                                    print(f"❌ Cannot go above mount point {CONTAINER_MOUNT_POINT}")
                                else:
                                    current_path = new_path
                                    print(f"📂 Changed directory to: {current_path}")
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
    # Mount local test dir to /projects
    # The server expects valid Allowed Paths as arguments
    mount_arg = f"type=bind,src={LOCAL_TEST_DIR},dst={CONTAINER_MOUNT_POINT}"
    
    cmd = [
        "docker", "run", "-i", "--rm",
        "--mount", mount_arg,
        DOCKER_IMAGE,
        CONTAINER_MOUNT_POINT 
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
