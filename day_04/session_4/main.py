"""
Day 04 - Session 04: Model Context Protocol (MCP)
Demonstrates:
  1. Connecting to an MCP Server over stdio
  2. Dynamic tool, resource, and prompt discovery
  3. Calling MCP tools (list_directory, read_file)
  4. Autonomous LLM Agent operating over dynamic MCP tools
"""

from __future__ import annotations
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from mcp_client import MCPClientManager
from mcp_agent import MCPAgent


async def main():
    print("=== Day 4 Session 4: Model Context Protocol (MCP) ===")
    server_script = str(Path(__file__).parent / "filesystem_mcp_server.py")

    # 1. Direct MCP client connection & capability discovery
    print("\n1. Connecting to MCP Server...")
    async with MCPClientManager(server_script) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(f"   Discovered {len(tools)} tools: {[t.name for t in tools]}")
        print(f"   Discovered {len(resources)} resources: {[r.name for r in resources]}")
        print(f"   Discovered {len(prompts)} prompts: {[p.name for p in prompts]}")

        # Call MCP tools directly
        res1 = await client.call_tool("list_directory", {"sub_dir": "."})
        print(f"   Called 'list_directory' -> Status: {'Error' if res1.is_error else 'Success'}")

        res2 = await client.call_tool("read_file", {"file_name": "company_policy.md"})
        print(f"   Called 'read_file' -> Length: {len(res2.text_content)} characters")

    # 2. Autonomous Agent powered by dynamic MCP tools
    print("\n2. Running autonomous agent with MCP tools...")
    goal = "Check company operations policy and find the flight duration required for business class."

    async with MCPClientManager(server_script) as client:
        agent = MCPAgent(mcp_client=client)
        result = await agent.run(user_goal=goal, max_turns=4)

        print(f"   Agent Status: {result['status']}")
        print(f"   Turns:        {result['turns']}")
        print(f"   Final Answer:\n   {result['final_answer'].strip()}")


if __name__ == "__main__":
    asyncio.run(main())
