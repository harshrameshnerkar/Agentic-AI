"""
Day 6 - Session 4: Model Context Protocol (MCP)
Module: mcp_client_manager.py

Production MCP Client wrapper that connects to an external ready-made MCP Server
over stdio JSON-RPC 2.0 transport.

Key Learning:
- The problem MCP solves: Eliminating the M x N integration complexity.
- Client vs Server architecture: Host application drives session; Server exposes capabilities.
- Capability discovery: Dynamically enumerating tools, resources, and prompts.
- Schema conversion: Mapping MCP tool schemas to OpenAI-compatible function definitions.
"""

from __future__ import annotations
import sys
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool


@dataclass
class MCPToolCallResult:
    """Standardized result structure for an MCP tool execution."""
    tool_name: str
    arguments: Dict[str, Any]
    is_error: bool
    output_text: str
    raw_response: Any


class MCPClientManager:
    """
    Manages connection lifecycle, protocol negotiation, and remote tool execution
    against a ready-made MCP server over stdio transport.
    """

    def __init__(self, sandbox_dir: Optional[Path] = None):
        if sandbox_dir is None:
            self.sandbox_dir = Path(__file__).resolve().parent / "sandbox"
        else:
            self.sandbox_dir = Path(sandbox_dir).resolve()
        
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

        # On Windows, npx must be invoked via npx.cmd
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"

        self.server_params = StdioServerParameters(
            command=npx_cmd,
            args=["-y", "@modelcontextprotocol/server-filesystem", str(self.sandbox_dir)]
        )

        self._session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._stdio_context = None

    async def connect(self) -> ClientSession:
        """
        Spawns the MCP server child process over stdio and completes the JSON-RPC initialization handshake.
        """
        self._stdio_context = stdio_client(self.server_params)
        read_stream, write_stream = await self._stdio_context.__aenter__()
        
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        await session.initialize()

        self._session = session
        return session

    async def disconnect(self):
        """Cleanly terminates the MCP session and closes the stdio transport pipes."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
            self._session = None

        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception:
                pass
            self._stdio_context = None

    async def list_tools(self) -> List[Tool]:
        """Queries the server for its available tools via 'tools/list'."""
        if not self._session:
            raise RuntimeError("MCP Client is not connected. Call connect() first.")
        result = await self._session.list_tools()
        return result.tools

    @staticmethod
    def mcp_to_openai_tools(mcp_tools: List[Tool]) -> List[Dict[str, Any]]:
        """
        Translates MCP Tool schemas into OpenAI-compatible tool specifications for the LLM.
        """
        openai_tools = []
        for t in mcp_tools:
            schema = {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or f"MCP tool: {t.name}",
                    "parameters": t.inputSchema if hasattr(t, "inputSchema") and t.inputSchema else {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
            openai_tools.append(schema)
        return openai_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolCallResult:
        """
        Invokes an MCP tool remotely over JSON-RPC 2.0 (stdio) and parses the result.
        """
        if not self._session:
            raise RuntimeError("MCP Client is not connected. Call connect() first.")

        try:
            res = await self._session.call_tool(tool_name, arguments)
            
            # Extract text blocks
            texts = []
            if hasattr(res, "content") and res.content:
                for item in res.content:
                    if hasattr(item, "text") and item.text:
                        texts.append(item.text)
                    elif isinstance(item, dict) and "text" in item:
                        texts.append(item["text"])
                    else:
                        texts.append(str(item))

            joined_text = "\n".join(texts) if texts else "Operation completed with empty response."
            is_err = getattr(res, "isError", False)

            return MCPToolCallResult(
                tool_name=tool_name,
                arguments=arguments,
                is_error=is_err,
                output_text=joined_text,
                raw_response=res
            )
        except Exception as ex:
            return MCPToolCallResult(
                tool_name=tool_name,
                arguments=arguments,
                is_error=True,
                output_text=f"MCP Tool Execution Error: {str(ex)}",
                raw_response=None
            )
