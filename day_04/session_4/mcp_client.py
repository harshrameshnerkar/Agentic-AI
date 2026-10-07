"""
Day 4 - Session 4: Model Context Protocol (MCP) Client
Module: mcp_client.py

Description:
    Standardized MCP Client wrapper that connects to an external MCP Server
    (via stdio JSON-RPC transport or in-memory transport), performs dynamic capability
    discovery (Tools, Resources, Prompts), and invokes tools remotely.

Key Learning:
    - MCP Client vs MCP Server architecture
    - Dynamic capability negotiation & schema discovery
    - Remote procedure calls over JSON-RPC 2.0 (stdio)
    - Handling structured results and resource URIs
"""

from __future__ import annotations
import asyncio
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from mcp import Client, StdioServerParameters
from mcp.types import Tool, Resource, Prompt


@dataclass
class ToolExecutionResult:
    """Represents the standardized output of an MCP tool execution."""
    tool_name: str
    arguments: Dict[str, Any]
    is_error: bool
    text_content: str
    structured_content: Optional[Dict[str, Any]]
    raw_response: Any


class MCPClientManager:
    """
    Manages client connection, protocol negotiation, and remote tool execution
    against an MCP server over stdio or in-process.
    """

    def __init__(self, server_script_path: Optional[str] = None):
        """
        Args:
            server_script_path: Path to the Python MCP server script to run via stdio.
                               If None, defaults to filesystem_mcp_server.py in this directory.
        """
        if server_script_path is None:
            default_path = Path(__file__).resolve().parent / "filesystem_mcp_server.py"
            self.server_script_path = str(default_path)
        else:
            self.server_script_path = str(Path(server_script_path).resolve())

        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[self.server_script_path]
        )
        self._client: Optional[Client] = None
        self._context_manager = None

    async def __aenter__(self) -> "MCPClientManager":
        """Establishes connection to the MCP server via stdio transport."""
        self._context_manager = Client(self.server_params)
        self._client = await self._context_manager.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Closes the connection and terminates the server subprocess."""
        if self._context_manager:
            await self._context_manager.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None
            self._context_manager = None

    def _ensure_connected(self) -> Client:
        if self._client is None:
            raise RuntimeError("MCPClientManager is not connected. Use 'async with MCPClientManager() as client:'.")
        return self._client

    # =========================================================================
    # Capability Discovery
    # =========================================================================

    async def list_tools(self) -> List[Tool]:
        """Discovers all tools advertised by the connected MCP Server."""
        client = self._ensure_connected()
        result = await client.list_tools()
        return result.tools

    async def list_resources(self) -> List[Resource]:
        """Discovers all resources advertised by the connected MCP Server."""
        client = self._ensure_connected()
        result = await client.list_resources()
        return result.resources

    async def list_prompts(self) -> List[Prompt]:
        """Discovers all prompt templates advertised by the connected MCP Server."""
        client = self._ensure_connected()
        result = await client.list_prompts()
        return result.prompts

    # =========================================================================
    # Tool Invocations
    # =========================================================================

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        """
        Invokes a remote tool on the MCP server via JSON-RPC 2.0.

        Args:
            tool_name: The name of the tool to execute.
            arguments: Dictionary of arguments conforming to tool's inputSchema.

        Returns:
            ToolExecutionResult containing text, structured data, and error status.
        """
        client = self._ensure_connected()
        try:
            res = await client.call_tool(tool_name, arguments)
            
            # Extract textual content from TextContent objects
            text_parts = []
            if hasattr(res, "content") and res.content:
                for c in res.content:
                    if hasattr(c, "text"):
                        text_parts.append(c.text)
                    elif isinstance(c, str):
                        text_parts.append(c)
            combined_text = "\n".join(text_parts) if text_parts else ""

            # Extract structured content if available
            structured = getattr(res, "structured_content", None)
            is_error = getattr(res, "is_error", False)

            return ToolExecutionResult(
                tool_name=tool_name,
                arguments=arguments,
                is_error=is_error,
                text_content=combined_text,
                structured_content=structured,
                raw_response=res
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=tool_name,
                arguments=arguments,
                is_error=True,
                text_content=f"MCP Client Error executing '{tool_name}': {str(e)}",
                structured_content=None,
                raw_response=None
            )

    # =========================================================================
    # Resource & Prompt Operations
    # =========================================================================

    async def read_resource(self, uri: str) -> str:
        """Reads a resource by URI from the MCP server."""
        client = self._ensure_connected()
        res = await client.read_resource(uri)
        texts = []
        for c in res.contents:
            if hasattr(c, "text"):
                texts.append(c.text)
        return "\n".join(texts)

    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        """Retrieves and formats a prompt template from the MCP server."""
        client = self._ensure_connected()
        res = await client.get_prompt(name, arguments)
        parts = []
        for msg in res.messages:
            if hasattr(msg, "content") and hasattr(msg.content, "text"):
                parts.append(f"[{msg.role.upper()}]: {msg.content.text}")
        return "\n".join(parts)


async def run_mcp_client_direct_demo():
    """
    Demonstrates connecting to the ready-made Filesystem MCP Server,
    discovering its capabilities, and executing TWO distinct tools:
      1. Tool 1: list_directory
      2. Tool 2: read_file
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n" + "=" * 75)
    print(" 🔌 MCP CLIENT DEMO: Connecting to Filesystem MCP Server via stdio")
    print("=" * 75)

    async with MCPClientManager() as client_mgr:
        print("[+] Subprocess connection established via stdio JSON-RPC transport.")

        # Step 1: Discover Tools
        print("\n--- 1. Dynamic Tool Discovery ---")
        tools = await client_mgr.list_tools()
        print(f"Discovered {len(tools)} tools on server:")
        for t in tools:
            print(f"  • Tool: {t.name:<18} | Description: {t.description}")

        # Step 2: Call Tool 1 -> list_directory
        print("\n--- 2. Invoking Tool 1: 'list_directory' ---")
        tool1_result = await client_mgr.call_tool("list_directory", {"sub_dir": "."})
        print(f"Execution Status: {'FAILED' if tool1_result.is_error else 'SUCCESS'}")
        if tool1_result.structured_content:
            print(f"Structured Content (JSON):\n{json.dumps(tool1_result.structured_content, indent=2)}")
        else:
            print(f"Text Content:\n{tool1_result.text_content}")

        # Step 3: Call Tool 2 -> read_file
        target_file = "company_policy.md"
        print(f"\n--- 3. Invoking Tool 2: 'read_file' (Target: '{target_file}') ---")
        tool2_result = await client_mgr.call_tool("read_file", {"file_name": target_file})
        print(f"Execution Status: {'FAILED' if tool2_result.is_error else 'SUCCESS'}")
        print(f"File Contents Received:\n{tool2_result.text_content.strip()}")

        # Step 4: Optional Tool 3 -> get_file_info
        print(f"\n--- 4. Invoking Tool 3: 'get_file_info' (Target: '{target_file}') ---")
        tool3_result = await client_mgr.call_tool("get_file_info", {"file_name": target_file})
        print(f"Metadata:\n{json.dumps(tool3_result.structured_content, indent=2)}")

        # Step 5: Discover & Read Resource
        print("\n--- 5. Dynamic Resource Discovery & Retrieval ---")
        resources = await client_mgr.list_resources()
        print(f"Discovered {len(resources)} resources:")
        for r in resources:
            print(f"  • URI: {r.uri} | Name: {r.name}")
        
        resource_uri = "resource://system/server_status"
        print(f"\nReading Resource: {resource_uri}")
        res_content = await client_mgr.read_resource(resource_uri)
        print(f"Resource Body:\n{res_content.strip()}")

        # Step 6: Discover & Evaluate Prompt Template
        print("\n--- 6. Dynamic Prompt Discovery & Template Evaluation ---")
        prompts = await client_mgr.list_prompts()
        print(f"Discovered {len(prompts)} prompts:")
        for p in prompts:
            print(f"  • Prompt Name: {p.name} | Description: {p.description}")

        rendered_prompt = await client_mgr.get_prompt("review_operations_policy", {"policy_focus": "hotel & flight reimbursements"})
        print(f"Rendered Prompt Instruction:\n{rendered_prompt}")

    print("\n[+] MCP Client Session completed successfully.")


if __name__ == "__main__":
    asyncio.run(run_mcp_client_direct_demo())
