"""
Day 4 - Session 4: Model Context Protocol (MCP) Autonomous Agent
Module: mcp_agent.py

Description:
    An autonomous LLM Agent powered by Gemini that dynamically queries an MCP Server,
    discovers its available tools at runtime, translates their MCP input_schema into
    OpenAI-compatible function definitions, and executes the tools over JSON-RPC stdio.

Highlights:
    - Zero hardcoded tool definitions in the Agent code.
    - True decoupled architecture: Tools reside exclusively on the MCP Server.
    - Handles tool calling loop with full thought-signature preservation.
"""

from __future__ import annotations
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_client import MCPClientManager

# Load environment configuration
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3-flash-preview")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(f"API key missing. Ensure OPENAI_API_KEY is configured in {env_path}")


class MCPAgent:
    """
    Autonomous agent that dynamically discovers tools from an MCP server
    and executes multi-turn tool calling workflows.
    """

    def __init__(self, mcp_client: MCPClientManager, model: str = OPENAI_MODEL):
        self.mcp_client = mcp_client
        self.model = model
        self.llm = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        self.discovered_tools: List[Dict[str, Any]] = []

    async def initialize_tools(self) -> List[Dict[str, Any]]:
        """
        Dynamically discovers tools from the connected MCP Server and
        translates MCP Tool schemas to OpenAI function calling specifications.
        """
        server_tools = await self.mcp_client.list_tools()
        openai_tools = []
        for t in server_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "No description provided.",
                    "parameters": t.input_schema or {"type": "object", "properties": {}}
                }
            })
        self.discovered_tools = openai_tools
        return self.discovered_tools

    async def run(self, user_goal: str, max_turns: int = 6) -> Dict[str, Any]:
        """
        Executes an autonomous goal-driven loop using dynamically discovered MCP tools.

        Args:
            user_goal: User's prompt/instruction.
            max_turns: Maximum allowed iterations to prevent infinite loops.

        Returns:
            Dictionary containing the final answer, trace of tool calls, and turn count.
        """
        if not self.discovered_tools:
            await self.initialize_tools()

        system_instruction = (
            "You are an autonomous enterprise AI agent equipped with tools via the Model Context Protocol (MCP). "
            "You have direct access to a managed server environment. "
            "Explore the filesystem to discover relevant files, read their contents, "
            "and answer the user request with precise facts and citations."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_goal}
        ]

        tool_call_history: List[Dict[str, Any]] = []

        print(f"\n[Agent Started] Goal: \"{user_goal}\"", flush=True)
        print(f"[Dynamic MCP Tools Available]: {[t['function']['name'] for t in self.discovered_tools]}", flush=True)

        for turn in range(1, max_turns + 1):
            print(f"\n--- Turn {turn} / {max_turns} ---", flush=True)

            response = self.llm.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.discovered_tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            # Append message directly to preserve Gemini thought signature
            messages.append(response_message)

            tool_calls = response_message.tool_calls

            # If no tools called, the LLM has synthesized the final answer
            if not tool_calls:
                final_answer = response_message.content or ""
                print(f"[Agent Completed] Final answer generated on turn {turn}.", flush=True)
                return {
                    "status": "COMPLETED",
                    "turns": turn,
                    "final_answer": final_answer,
                    "tool_call_history": tool_call_history
                }

            # Execute all requested MCP tool calls
            for tool_call in tool_calls:
                fn_name = tool_call.function.name
                fn_args_raw = tool_call.function.arguments

                try:
                    fn_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                except json.JSONDecodeError:
                    fn_args = {}

                print(f" -> Invoking MCP Server Tool: {fn_name}({json.dumps(fn_args)})", flush=True)

                # Remote execution through MCP Client over stdio
                exec_result = await self.mcp_client.call_tool(fn_name, fn_args)

                # Format observation
                if exec_result.structured_content:
                    observation_payload = json.dumps(exec_result.structured_content)
                else:
                    observation_payload = exec_result.text_content

                # Truncate preview for log display
                preview = (observation_payload[:180] + "...") if len(observation_payload) > 180 else observation_payload
                print(f" <- Observation from MCP Server: {preview}", flush=True)

                tool_call_history.append({
                    "turn": turn,
                    "tool": fn_name,
                    "args": fn_args,
                    "is_error": exec_result.is_error,
                    "observation_length": len(observation_payload)
                })

                # Pass observation back to model context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": observation_payload
                })

        return {
            "status": "MAX_TURNS_EXCEEDED",
            "turns": max_turns,
            "final_answer": "Loop limit reached before completion.",
            "tool_call_history": tool_call_history
        }
