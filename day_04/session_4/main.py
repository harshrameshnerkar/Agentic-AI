"""
Day 4 - Session 4: Model Context Protocol (MCP)
Entrypoint: main.py

Learning Objectives:
1. Understand the Model Context Protocol (MCP) and why it solves the N x M integration problem.
2. Distinguish MCP Clients (Hosts) from MCP Servers.
3. Master the 3 core MCP Primitives: Tools, Resources, and Prompts.
4. Connect to a ready-made MCP server over stdio and execute tools dynamically.
5. Integrate MCP into an autonomous Agent powered by Gemini with zero hardcoded tool logic.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Load local environment
env_file = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_file)

# Add local folder and workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from mcp_client import MCPClientManager
from mcp_agent import MCPAgent


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n--- {title} ---")


async def main():
    print_header("DAY 4 - SESSION 4: MODEL CONTEXT PROTOCOL (MCP)")

    print("""
[ARCHITECTURE CONCEPT: THE N x M PROBLEM & THE MCP REVOLUTION]

  Traditional Architecture (Without MCP):
    N LLM Apps / Frameworks x M Tools / Data Sources = N x M Custom Integrations!
    Every agent framework writes its own custom adapters for Postgres, GitHub, Slack, Filesystem.

  Standardized Architecture (With MCP):
    N Clients + M Servers = N + M Modular Ecosystem!
    A universal open protocol (JSON-RPC 2.0) defining how models discover and interact with:
      1. Tools     -> Model-controlled callable functions (e.g. read_file, list_dir)
      2. Resources -> Application-controlled contextual data by URI (e.g. resource://data/status)
      3. Prompts   -> User-controlled reusable prompts & slash commands
""")

    # -------------------------------------------------------------------------
    # PART 1: Direct MCP Client Connection & Two-Tool Execution
    # -------------------------------------------------------------------------
    print_header("PART 1: CONNECTING TO MCP SERVER OVER STDIO & CALLING TOOLS")
    
    server_script = str(Path(__file__).resolve().parent / "filesystem_mcp_server.py")
    print(f"Connecting to MCP Server subprocess via stdio transport:\n  Target Server Script: {server_script}")

    start_time = time.time()

    async with MCPClientManager(server_script) as client:
        print("[+] Stdio JSON-RPC connection successfully established with MCP Server.")

        # Capability Discovery
        print_section("1. Dynamic Capability Discovery")
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(f"Discovered {len(tools)} Tools:")
        for t in tools:
            print(f"  • Tool: {t.name:<18} | Description: {t.description}")

        print(f"\nDiscovered {len(resources)} Resources:")
        for r in resources:
            print(f"  • URI: {r.uri:<36} | Name: {r.name}")

        print(f"\nDiscovered {len(prompts)} Prompts:")
        for p in prompts:
            print(f"  • Prompt: {p.name:<25} | Description: {p.description}")

        # MANDATORY TASK REQUIREMENT: Call Two of its Tools
        print_header("MANDATORY TASK: CALL TWO MCP SERVER TOOLS")

        # Tool Call 1: list_directory
        print_section("Invocation 1: 'list_directory' (Tool 1)")
        call1_args = {"sub_dir": "."}
        print(f"Client -> Server JSON-RPC Request: call_tool('list_directory', {call1_args})")
        res1 = await client.call_tool("list_directory", call1_args)
        print(f"Server -> Client Response Status: {'ERROR' if res1.is_error else 'SUCCESS'}")
        print("Received Directory Listing:")
        if res1.structured_content:
            for item in res1.structured_content.get("result", []):
                size_str = f"{item.get('size_bytes')} bytes" if item.get('size_bytes') is not None else "DIR"
                print(f"  [{item.get('type').upper():<5}] {item.get('name'):<24} ({size_str})")
        else:
            print(res1.text_content)

        # Tool Call 2: read_file
        print_section("Invocation 2: 'read_file' (Tool 2)")
        call2_args = {"file_name": "company_policy.md"}
        print(f"Client -> Server JSON-RPC Request: call_tool('read_file', {call2_args})")
        res2 = await client.call_tool("read_file", call2_args)
        print(f"Server -> Client Response Status: {'ERROR' if res2.is_error else 'SUCCESS'}")
        print("Received File Content Snippet:")
        lines = res2.text_content.strip().splitlines()
        for line in lines[:8]:
            print(f"  | {line}")
        if len(lines) > 8:
            print(f"  | ... [{len(lines) - 8} more lines]")

        # Tool Call 3 (Bonus): get_file_info
        print_section("Invocation 3: 'get_file_info' (Tool 3)")
        call3_args = {"file_name": "server_status.json"}
        res3 = await client.call_tool("get_file_info", call3_args)
        print(f"File Metadata: {json.dumps(res3.structured_content, indent=2)}")

        # MCP Primitive 2 Demo: Read Resource
        print_section("Primitive 2 Demo: Read MCP Resource by URI")
        resource_uri = "resource://system/server_status"
        print(f"Fetching: {resource_uri}")
        res_data = await client.read_resource(resource_uri)
        print("Resource Payload Preview:")
        print(res_data[:220] + "...\n")

        # MCP Primitive 3 Demo: Get Prompt Template
        print_section("Primitive 3 Demo: Render MCP Prompt Template")
        rendered_prompt = await client.get_prompt("review_operations_policy", {"policy_focus": "travel and database credentials"})
        print(f"Rendered Prompt Instruction:\n{rendered_prompt}")

    # -------------------------------------------------------------------------
    # PART 2: Autonomous LLM Agent Operating Over MCP Tools
    # -------------------------------------------------------------------------
    print_header("PART 2: AUTONOMOUS AGENT INTEGRATING DYNAMIC MCP TOOLS")

    print("""
The agent does NOT have any hardcoded tool definitions.
It dynamically inspects the MCP Server, translates input_schema into OpenAI/Gemini
function specifications, and executes multi-turn tool loops over stdio.
""")

    user_goal = (
        "Inspect our filesystem repository. Identify any degraded services in the server status file "
        "and state the alert details. Then check the company operations policy for international travel "
        "and state the flight duration required for business class qualification."
    )

    async with MCPClientManager(server_script) as client:
        agent = MCPAgent(mcp_client=client)
        result = await agent.run(user_goal=user_goal, max_turns=6)

        print_header("AGENT EXECUTION SUMMARY & FINAL ANSWER")
        print(f"Goal: {user_goal}")
        print(f"Execution Status: {result['status']}")
        print(f"Turns Completed:  {result['turns']}")
        print(f"Total Tools Run:  {len(result['tool_call_history'])}")

        print("\n--- Final Agent Response ---")
        print(result["final_answer"])

        print("\n--- Tool Execution Audit Trail ---")
        print(f"{'Turn':<6} | {'Tool Executed':<18} | {'Arguments':<35} | {'Observation Length'}")
        print("-" * 75)
        for step in result["tool_call_history"]:
            args_str = json.dumps(step['args'])
            if len(args_str) > 33:
                args_str = args_str[:30] + "..."
            print(f"{step['turn']:<6} | {step['tool']:<18} | {args_str:<35} | {step['observation_length']} bytes")

    elapsed = time.time() - start_time
    print(f"\n[+] Day 4 - Session 4 completed successfully in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
