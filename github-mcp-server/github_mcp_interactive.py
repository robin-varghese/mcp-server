#!/usr/bin/env python3
"""
Interactive Client for GitHub MCP Server

This script provides a REPL interface to interact with the GitHub MCP server.
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
DOCKER_IMAGE = "local-github-mcp"
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

def get_server_params():
    cmd = ["docker", "run", "-i", "--rm"]
    
    if GITHUB_TOKEN:
        cmd.extend(["-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={GITHUB_TOKEN}"])
    
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
        You are an expert GitHub assistant.
        Translate the user's natural language request into a valid Tool Call for the 'github-mcp-server'.
        
        Common Tools:
        - search_repositories(query=str, page=int)
        - get_file_contents(owner=str, repo=str, path=str, ref=str optional)
        - issue_write(owner, repo, title, body)  <-- maps to creating issue
        - list_issues(owner=str, repo=str)
        - create_pull_request(owner=str, repo=str, title=str, head=str, base=str, body=str)
        - list_pull_requests(owner=str, repo=str)
        
        Output Format:
        Return ONLY the command string in the format: tool_name key=value key2=value2
        
        Rules:
        1. If user provides a GitHub URL (e.g., https://github.com/owner/repo), EXTRACT author and repo name from it.
        2. Use extracted 'owner' and 'repo' for tools like list_issues, get_file_contents, etc.
        3. For "list my repos" or similar, if a URL was previously mentioned or context is available, use it. Otherwise use 'search_repositories query=user:<owner>' if owner is known, or ask for clarification.
        4. Do NOT output markdown.
        5. Use 'search_repositories' to list repos.
        
        Examples:
        User: "list issues in https://github.com/microsoft/vscode"
        Output: list_issues owner=microsoft repo=vscode
        
        User: "show me code for README.md in https://github.com/facebook/react"
        Output: get_file_contents owner=facebook repo=react path=README.md
        
        User: "list repos for user https://github.com/robinkv"
        Output: search_repositories query=user:robinkv
        
        User: "list my repos" (assuming user is robinkv)
        Output: search_repositories query=user:robinkv
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
        if result.startswith("```"):
            result = result.split("\n", 1)[1]
            if result.endswith("```"):
                result = result.rsplit("\n", 1)[0]
        return result.strip()
        
    except Exception as e:
        print(f"⚠️ NLP Translation failed: {e}")
        return prompt

async def run_interactive_session():
    print(f"Starting Interactive GitHub MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GITHUB_TOKEN
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_PERSONAL_ACCESS_TOKEN not found in env.")
        token = input("Enter GitHub PAT: ").strip()
        if token:
            GITHUB_TOKEN = token
            
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    if HAS_GENAI and GOOGLE_API_KEY:
        print("✨ NLP Enabled")
    else:
        print("⚠️ NLP Disabled")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to GitHub MCP Server")
                
                tools = await session.list_tools()
                print("\nAvailable Tools:")
                for t in tools.tools:
                    print(f"  - {t.name}")

                print("\n" + "="*50)
                print("ENTER COMMANDS (type 'exit' or 'quit' to stop)")
                print("Examples:")
                print("  > list my repos")
                print("  > show issues in owner/repo")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\ngithub> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        cmd_str = translate_to_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Translated to: {cmd_str}")
                        
                        parts = shlex.split(cmd_str)
                        if not parts:
                            continue
                            
                        tool_name = parts[0]
                        tool_args = {}
                        
                        for arg in parts[1:]:
                            if '=' in arg:
                                k, v = arg.split('=', 1)
                                tool_args[k] = v
                            else:
                                print(f"⚠️ Warning: Arg '{arg}' malformed.")

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
        print("Make sure the Docker image is built.")

if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_session())
    except KeyboardInterrupt:
        print("\nExiting...")
