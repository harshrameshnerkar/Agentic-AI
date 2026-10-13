"""
Day 06 - Session 04: Model Context Protocol (MCP)
Demonstrates connecting to an MCP filesystem server via stdio,
discovering capabilities, calling tools directly, and using an autonomous agent.
"""

from __future__ import annotations
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from mcp_client_manager import MCPClientManager
from mcp_agent import AutonomousMCPAgent


async def call_sample_tools(mcp: MCPClientManager):
    """Calls three MCP tools directly: write_file, list_directory, and get_file_info."""
    print("\n--- Testing 3 MCP Tools Directly ---")
    sandbox = mcp.sandbox_dir
    test_path = str(sandbox / "cluster_audit.json")
    content = json.dumps({
        "audit_id": "AUDIT-2026-Q4-001",
        "cluster_health": "OPTIMAL",
        "compliance_status": "SOC2_COMPLIANT"
    }, indent=2)

    # 1. write_file
    res1 = await mcp.call_tool("write_file", {"path": test_path, "content": content})
    print(f"1. write_file: {'Success' if not res1.is_error else 'Failed'}")
    assert not res1.is_error, f"write_file failed: {res1.output_text}"

    # 2. list_directory
    res2 = await mcp.call_tool("list_directory", {"path": str(sandbox)})
    print(f"2. list_directory: {'Success' if not res2.is_error else 'Failed'}")
    assert not res2.is_error, f"list_directory failed: {res2.output_text}"
    assert "cluster_audit.json" in res2.output_text

    # 3. get_file_info
    res3 = await mcp.call_tool("get_file_info", {"path": test_path})
    print(f"3. get_file_info: {'Success' if not res3.is_error else 'Failed'}")
    assert not res3.is_error, f"get_file_info failed: {res3.output_text}"


async def run_agent_workflow(mcp: MCPClientManager):
    """Runs an autonomous agent using MCP tools."""
    print("\n--- Running Autonomous MCP Agent ---")
    agent = AutonomousMCPAgent(mcp_manager=mcp)
    await agent.initialize_tools(target_tool_names=[
        "list_directory", "read_text_file", "write_file", "get_file_info"
    ])

    prompt = (
        "Inspect the sandbox directory. Read 'system_manifest.json' to identify which service is degraded, "
        "write an incident mitigation plan to 'incident_mitigation.md', and verify it."
    )
    result = await agent.run(user_prompt=prompt, max_turns=5)
    print(f"Agent finished in {result['turns']} turns with status: {result['status']}")
    print(f"Tools called: {' -> '.join([s['tool'] for s in result['steps']])}")
    print(f"Summary:\n{result['final_answer']}")


async def main():
    print("Connecting to MCP filesystem server...")
    mcp = MCPClientManager()
    await mcp.connect()

    tools = await mcp.list_tools()
    print(f"Discovered {len(tools)} tools from server.")

    await call_sample_tools(mcp)
    await run_agent_workflow(mcp)

    await mcp.disconnect()
    print("\nMCP Session closed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
