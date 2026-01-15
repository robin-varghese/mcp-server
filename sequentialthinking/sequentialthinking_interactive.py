#!/usr/bin/env python3
"""
Interactive Client for Sequential Thinking MCP Server

This script provides a REPL interface to interact with the Sequential Thinking MCP server.
It connects to the Docker container and allows executing available tools.
It supports NLP-based tool calling and automatic Multi-Step Execution.
"""

import asyncio
import os
import shlex
import sys
import json
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# Configuration
DOCKER_IMAGE = "sequentialthinking"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

SYSTEM_INSTRUCTION = """
You are an expert assistant for Sequential Thinking.
Your job is to translate the user's natural language thought or problem into a 'sequentialthinking' tool call.
Crucially, you must maintain the state of the thinking process across multiple turns.

Tool: sequentialthinking
Arguments:
- thought (string): The current thinking step
- nextThoughtNeeded (boolean): Whether another thought step is needed
- thoughtNumber (integer): Current thought number
- totalThoughts (integer): Estimated total thoughts needed
- isRevision (boolean, optional)
- revisesThought (integer, optional)
- branchFromThought (integer, optional)
- branchId (string, optional)
- needsMoreThoughts (boolean, optional)

Output Format:
Return ONLY the command string in the format: sequentialthinking key=value key2=value2

Examples:
User: "First, I need to analyze the problem."
Output: sequentialthinking thought="First, I need to analyze the problem." thoughtNumber=1 totalThoughts=5 nextThoughtNeeded=true

User (History): "Step 1 complete."
User: "Proceed to step 2."
Output: sequentialthinking thought="Step 2: Break it down." thoughtNumber=2 totalThoughts=5 nextThoughtNeeded=true
"""

class SequentialThinker:
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
    print(f"Starting Interactive Sequential Thinking MCP Client...")
    print(f"Docker Image: {DOCKER_IMAGE}")
    
    global GOOGLE_API_KEY
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found in env.")
        user_key = input("Enter Google API Key for NLP (Enter to skip): ").strip()
        if user_key:
            GOOGLE_API_KEY = user_key

    thinker = SequentialThinker(GOOGLE_API_KEY)
    
    if thinker.client:
        print("✨ NLP Enabled: Auto-looping enabled for sequences.")
    else:
        print("⚠️ NLP Disabled: Use exact key=value syntax")

    try:
        async with stdio_client(get_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✅ Connected to Sequential Thinking MCP Server")
                
                print("\nDiscovering tools...")
                if thinker.client:
                    # Let the LLM know about available tools via system instruction context is implied, 
                    # but we can do a dummy turn if needed. For now, we rely on the system prompt.
                    pass

                print("\n" + "="*50)
                print("ENTER COMMANDS (type 'exit' or 'quit' to stop)")
                print("To run a full sequence, just describe your goal.")
                print("Examples:")
                print("  > Solve the problem of optimizing cloud costs.")
                print("="*50 + "\n")

                while True:
                    try:
                        user_input = input("\nsequential> ").strip()
                        if not user_input:
                            continue
                        if user_input.lower() in ['exit', 'quit']:
                            break
                        
                        # Initial Translation
                        cmd_str = thinker.generate_tool_call(user_input)
                        if cmd_str != user_input:
                            print(f"🤖 Initial Thought: {cmd_str}")

                        # Execution Loop
                        while True:
                            tool_name, tool_args = parse_command(cmd_str)
                            if tool_name == "tool_name":
                                tool_name = "sequentialthinking"
                            if not tool_name:
                                break

                            print(f"Executing: {tool_name} with {tool_args} ...")
                            
                            try:
                                result = await session.call_tool(tool_name, arguments=tool_args)
                                
                                # Print result
                                last_thought_result = {}
                                for content in result.content:
                                    if content.type == "text":
                                        print(content.text)
                                        try:
                                            # Try to extract the JSON output from the text if it's there
                                            # usually the tool returns a JSON string as text
                                            text_data = content.text
                                            if text_data.strip().startswith("{"):
                                                last_thought_result = json.loads(text_data)
                                        except:
                                            pass
                                    else:
                                        print(f"[{content.type} content]")
                                
                                # Check if we need to loop
                                if thinker.client and tool_name == "sequentialthinking":
                                    # We try to infer if we should continue from the tool arguments or the result
                                    # The result from sequentialthinking tool is usually just the updated thought data
                                    # The ARGUMENTS `nextThoughtNeeded` drive the logic, but the *result* confirms it.
                                    
                                    # Actually, sticking to the arguments passed is safer for the INTENT.
                                    # If the previous intent was "nextThoughtNeeded=True", we should generate the next one.
                                    
                                    needs_next = tool_args.get('nextThoughtNeeded', False)
                                    curr_thought = tool_args.get('thoughtNumber', 0)
                                    total_thoughts = tool_args.get('totalThoughts', 0)

                                    if needs_next and curr_thought < total_thoughts:
                                        print(f"\n🔄 Auto-continuing to step {curr_thought + 1}/{total_thoughts}...")
                                        
                                        # Feed context back to LLM to get next step
                                        prompt = f"The previous tool executed successfully. Result: {json.dumps(last_thought_result)}. Generate the next sequentialthinking tool call for thought number {curr_thought + 1}."
                                        cmd_str = thinker.generate_tool_call(prompt)
                                        print(f"🤖 Next Thought: {cmd_str}")
                                        
                                        # Small pause for readability
                                        time.sleep(1) 
                                        continue
                                    else:
                                        if needs_next:
                                             print("\n✅ Sequence complete (or limit reached).")
                                        break
                                else:
                                    # Not a sequential tool or no NLP, stop loop
                                    break
                                    
                            except Exception as e:
                                print(f"❌ Tool execution failed: {e}")
                                break

                    except KeyboardInterrupt:
                        print("\nCancelled.")
                    except Exception as e:
                        print(f"Error: {e}")

    except Exception as e:
        print(f"\nFailed to connect/run: {e}")
        # print(f"Make sure the Docker image is built: 'docker build -t {DOCKER_IMAGE} .'")

def get_server_params():
    cmd = ["docker", "run", "-i", "--rm", DOCKER_IMAGE]
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
