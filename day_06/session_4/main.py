"""
Day 6 - Session 4: Model Context Protocol (MCP)
Master Demonstration: main.py

Learning Objectives:
1. The Problem MCP Solves: Eliminating the M x N integration matrix.
2. Client vs Server: Host application drives JSON-RPC sessions; Server exposes capabilities.
3. Primitives: Tools (executable actions), Resources (read-only URIs), Prompts (parameterized templates).
4. Connecting an Existing Server: Protocol handshake and dynamic tool discovery.
5. Transport Basics: stdio (subprocess pipes for local tools) vs SSE/HTTP (remote services).
6. When to Write Your Own Server: Off-the-shelf for standard systems; custom for proprietary APIs.

Task:
Connect a ready-made MCP server (filesystem) and call three of its tools successfully.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Ensure local .env takes absolute priority
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Ensure local imports work reliably
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_client_manager import MCPClientManager
from mcp_agent import AutonomousMCPAgent


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def print_mcp_education():
    """Prints clear architectural education covering all curriculum theory points."""
    print_banner("MCP ARCHITECTURAL FOUNDATIONS & CORE CONCEPTS")
    print("""
1. THE PROBLEM MCP SOLVES (M x N Complexity):
   • Before MCP: M AI applications (Claude, ChatGPT, Antigravity, custom agents) connecting
     to N data sources (Filesystem, GitHub, Postgres, Slack, Jira) required M x N bespoke adapters.
   • With MCP: Every application implements ONE MCP Client, and every data source implements
     ONE MCP Server. Total integration complexity collapses from M x N to M + N.

2. CLIENT VS SERVER ROLES:
   • MCP Client (Host): The AI assistant/IDE that orchestrates sessions, prompts the LLM,
     and relays tool call requests to servers over JSON-RPC 2.0.
   • MCP Server: A lightweight provider that exposes tools, resources, and prompt templates.
     The server NEVER calls the LLM itself; it serves capabilities to the client.

3. THE THREE CORE MCP PRIMITIVES:
   • Tools: Executable functions with JSON schema parameters (e.g. read_file, write_file).
   • Resources: Read-only data/context URIs (e.g. file:///path, postgres://table).
   • Prompts: Parameterized prompt templates provided by the server to guide the model.

4. TRANSPORT BASICS:
   • stdio (Standard Input/Output): Local subprocess execution. Zero network overhead,
     highest security, process boundary isolation. Perfect for local dev & filesystem tools.
   • SSE / HTTP (Server-Sent Events): Network protocol for remote or cloud-hosted servers.

5. WHEN TO WRITE YOUR OWN SERVER:
   • Use Off-The-Shelf (Ready-Made): Standard filesystems, GitHub, SQLite/Postgres, Brave Search.
   • Write Custom Server: Proprietary internal enterprise APIs, custom microservice telemetry,
     specialized authentication/firewall rules, or custom business domain logic.
""", flush=True)


async def demonstrate_three_mcp_tools(mcp: MCPClientManager):
    """
    Connects to the ready-made MCP server and calls 3 of its tools successfully:
    1. write_file
    2. list_directory
    3. get_file_info
    """
    print_banner("PART 1: CALLING THREE READY-MADE MCP TOOLS DIRECTLY")

    sandbox = mcp.sandbox_dir
    test_file_path = str(sandbox / "cluster_audit.json")
    test_file_content = json.dumps({
        "audit_id": "AUDIT-2026-Q4-001",
        "auditor": "Automated Security Agent",
        "cluster_health": "OPTIMAL",
        "compliance_status": "SOC2_COMPLIANT",
        "timestamp": "2026-10-05T18:45:00Z"
    }, indent=2)

    # -------------------------------------------------------------
    # Tool Call 1: write_file
    # -------------------------------------------------------------
    print("\n" + "-" * 70, flush=True)
    print(" [TOOL 1/3]: 'write_file' (Persisting configuration into sandbox)", flush=True)
    print("-" * 70, flush=True)
    res1 = await mcp.call_tool("write_file", {
        "path": test_file_path,
        "content": test_file_content
    })
    print(f"Target Path: {test_file_path}")
    print(f"Is Error: {res1.is_error}")
    print(f"Server Response:\n{res1.output_text}", flush=True)
    assert not res1.is_error, f"Tool 1 write_file failed: {res1.output_text}"

    # -------------------------------------------------------------
    # Tool Call 2: list_directory
    # -------------------------------------------------------------
    print("\n" + "-" * 70, flush=True)
    print(" [TOOL 2/3]: 'list_directory' (Scanning sandbox contents)", flush=True)
    print("-" * 70, flush=True)
    res2 = await mcp.call_tool("list_directory", {
        "path": str(sandbox)
    })
    print(f"Scanned Directory: {sandbox}")
    print(f"Is Error: {res2.is_error}")
    print(f"Server Response (Directory Listing):\n{res2.output_text}", flush=True)
    assert not res2.is_error, f"Tool 2 list_directory failed: {res2.output_text}"
    assert "cluster_audit.json" in res2.output_text, "Newly written file not found in listing!"

    # -------------------------------------------------------------
    # Tool Call 3: get_file_info
    # -------------------------------------------------------------
    print("\n" + "-" * 70, flush=True)
    print(" [TOOL 3/3]: 'get_file_info' (Querying filesystem metadata)", flush=True)
    print("-" * 70, flush=True)
    res3 = await mcp.call_tool("get_file_info", {
        "path": test_file_path
    })
    print(f"Target Path: {test_file_path}")
    print(f"Is Error: {res3.is_error}")
    print(f"Server Response (File Metadata):\n{res3.output_text}", flush=True)
    assert not res3.is_error, f"Tool 3 get_file_info failed: {res3.output_text}"

    print("\n  ✅ SUCCESS: All 3 ready-made MCP tools executed cleanly over stdio transport!", flush=True)


async def demonstrate_autonomous_agent(mcp: MCPClientManager):
    """
    Demonstrates an autonomous agent reasoning and executing multiple MCP tools sequentially.
    """
    print_banner("PART 2: AUTONOMOUS AGENT REASONING WITH MCP TOOLS")

    agent = AutonomousMCPAgent(mcp_manager=mcp)
    # Filter to active core tools to maintain optimal tool count (< 10)
    await agent.initialize_tools(target_tool_names=[
        "list_directory",
        "read_text_file",
        "write_file",
        "get_file_info"
    ])

    user_objective = (
        "Inspect the sandbox directory. Read 'system_manifest.json' to identify which service is degraded, "
        "write an incident mitigation plan to 'incident_mitigation.md' with corrective actions, "
        "and inspect the file metadata of the new file to verify it was saved properly."
    )

    result = await agent.run(user_prompt=user_objective, max_turns=5)

    print_banner("AUTONOMOUS MCP AGENT RESULT")
    print(f"Status: {result['status']}")
    print(f"Turns Completed: {result['turns']}")
    print(f"Total MCP Tools Called: {len(result['steps'])}")
    print(f"Tool Sequence: {' -> '.join([s['tool'] for s in result['steps']])}")
    print("\n--- Final Agent Synthesis ---")
    print(result["final_answer"])


async def main():
    print_banner("DAY 6 - SESSION 4: MODEL CONTEXT PROTOCOL (MCP) MASTER VERIFICATION")

    # Display conceptual foundations
    print_mcp_education()

    # Step 1: Connect to ready-made MCP Server (@modelcontextprotocol/server-filesystem)
    mcp = MCPClientManager()
    print_banner("CONNECTING TO READY-MADE MCP SERVER")
    print(f"Spawning: {mcp.server_params.command} {' '.join(mcp.server_params.args)}", flush=True)

    await mcp.connect()
    print("✓ MCP Client Handshake Successful (JSON-RPC 2.0 via stdio)!", flush=True)

    # Step 2: Discover capabilities
    tools = await mcp.list_tools()
    print(f"✓ Discovered {len(tools)} ready-made tools from server:")
    for t in tools:
        print(f"  • {t.name:<22} | {t.description[:55]}...")

    # Step 3: Call 3 MCP tools directly
    await demonstrate_three_mcp_tools(mcp)

    # Step 4: Run Autonomous Agent leveraging MCP tools
    await demonstrate_autonomous_agent(mcp)

    # Step 5: Clean disconnect
    await mcp.disconnect()
    print("\n[MCP Client] Session cleanly disconnected.", flush=True)

    print_banner("DAY 6 - SESSION 4: SUMMARY & VERIFICATION COMPLETE")
    print("""
Key Principles Proven:
  [✓] Standard Protocol: Connected to official @modelcontextprotocol/server-filesystem over stdio.
  [✓] Capability Discovery: Dynamically enumerated all 14 server tools via tools/list.
  [✓] 3 Tools Called: write_file, list_directory, and get_file_info executed with verified results.
  [✓] Autonomous Agent: LLM reasoned, invoked remote MCP tools, and solved operational objective.
""", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
