"""
Day 6 - Session 4: Model Context Protocol (MCP)
Module: mcp_agent.py

Autonomous AI Agent dynamically powered by tools discovered from a live ready-made MCP Server.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import re
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_client_manager import MCPClientManager

# Load local .env with override
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class AutonomousMCPAgent:
    """
    An agent that dynamically negotiates tools with an external MCP server,
    converts MCP schemas to OpenAI format, and executes remote tools autonomously.
    """

    def __init__(self, mcp_manager: MCPClientManager, model: str = OPENAI_MODEL):
        self.mcp = mcp_manager
        self.model = model
        self.llm = OpenAI(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY
        )
        self.active_openai_tools: List[Dict[str, Any]] = []

    def _call_llm_with_retry(self, **kwargs) -> Any:
        """Invokes chat completion with backoff for rate limits."""
        from openai import RateLimitError, InternalServerError, APIConnectionError
        max_retries = 5
        base_delay = 5.0
        for attempt in range(1, max_retries + 1):
            try:
                return self.llm.chat.completions.create(**kwargs)
            except (RateLimitError, InternalServerError, APIConnectionError) as err:
                err_text = str(err)
                if "daily" in err_text.lower() or ("quota exceeded" in err_text.lower() and "h" in err_text):
                    print(f"\n[FATAL QUOTA ERROR] Model daily quota exhausted: {err_text}", flush=True)
                    raise err

                if attempt == max_retries:
                    raise err

                sleep_time = base_delay * attempt
                if "retry in " in err_text:
                    try:
                        match = re.search(r"retry in ([0-9.]+)s", err_text)
                        if match:
                            parsed_s = float(match.group(1))
                            if parsed_s < 60.0:
                                sleep_time = parsed_s + 1.0
                    except Exception:
                        pass

                print(f"  [RateLimit Notice] Cooling down for {sleep_time:.1f}s (Attempt {attempt}/{max_retries})...", flush=True)
                time.sleep(sleep_time)

    async def initialize_tools(self, target_tool_names: Optional[List[str]] = None):
        """
        Discovers tools from the MCP server and filters to a targeted set (under ~10).
        """
        all_mcp_tools = await self.mcp.list_tools()
        all_converted = self.mcp.mcp_to_openai_tools(all_mcp_tools)

        if target_tool_names:
            self.active_openai_tools = [
                t for t in all_converted if t["function"]["name"] in target_tool_names
            ]
        else:
            # Curate default standard filesystem tools to prevent tool count bloat
            core_tools = {"list_directory", "read_text_file", "write_file", "get_file_info", "search_files"}
            self.active_openai_tools = [
                t for t in all_converted if t["function"]["name"] in core_tools
            ]

        print(f"[MCP Agent] Initialized with {len(self.active_openai_tools)} active MCP tools:")
        for t in self.active_openai_tools:
            print(f"  • {t['function']['name']}: {t['function']['description'][:65]}...")

    async def run(self, user_prompt: str, max_turns: int = 5) -> Dict[str, Any]:
        """
        Runs the ReAct loop where the agent calls ready-made MCP server tools.
        """
        if not self.active_openai_tools:
            await self.initialize_tools()

        sandbox_path = str(self.mcp.sandbox_dir)
        system_prompt = (
            f"You are an enterprise operations AI assistant connected to an external MCP Filesystem Server. "
            f"Your managed sandbox directory path is: '{sandbox_path}'. "
            f"When calling filesystem tools, ALWAYS use absolute paths within the sandbox directory. "
            f"Fulfill the user's objective by reasoning and calling the appropriate MCP tools."
        )

        messages: List[Any] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        steps_log: List[Dict[str, Any]] = []
        print("\n" + "=" * 80, flush=True)
        print(" [MCP AGENT] AUTONOMOUS EXECUTION TRACE WITH READY-MADE MCP SERVER", flush=True)
        print("=" * 80, flush=True)
        print(f"Goal: \"{user_prompt}\"", flush=True)

        for turn in range(1, max_turns + 1):
            print(f"\n>>> TURN {turn} / {max_turns} <<<", flush=True)

            t0 = time.time()
            response = self._call_llm_with_retry(
                model=self.model,
                messages=messages,
                tools=self.active_openai_tools,
                tool_choice="auto"
            )
            llm_latency = time.time() - t0

            response_msg = response.choices[0].message
            messages.append(response_msg)

            thought = response_msg.content or ""
            tool_calls = response_msg.tool_calls or []

            print(f"  [LLM Latency: {llm_latency:.2f}s]", flush=True)
            if thought:
                print(f"  🧠 [THOUGHT]: {thought.strip()}", flush=True)
            else:
                print(f"  🧠 [THOUGHT]: Model reasoned to invoke {len(tool_calls)} tool(s).", flush=True)

            if not tool_calls:
                print(f"\n[Agent Finished] Objective achieved on Turn {turn}!", flush=True)
                return {
                    "status": "SUCCESS",
                    "turns": turn,
                    "steps": steps_log,
                    "final_answer": thought
                }

            for call in tool_calls:
                fn_name = call.function.name
                raw_args = call.function.arguments

                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except json.JSONDecodeError:
                    args = {}

                print(f"\n  ⚡ [ACTION]: Invoke Remote MCP Tool '{fn_name}'", flush=True)
                print(f"     Arguments: {json.dumps(args, indent=2)}", flush=True)

                # REMOTE EXECUTION VIA MCP JSON-RPC
                exec_t0 = time.perf_counter()
                result = await self.mcp.call_tool(fn_name, args)
                exec_ms = (time.perf_counter() - exec_t0) * 1000.0

                print(f"  👁️ [OBSERVATION from MCP Server] ({exec_ms:.2f}ms):", flush=True)
                obs_preview = result.output_text[:300] + ("..." if len(result.output_text) > 300 else "")
                print(f"     {obs_preview}", flush=True)

                steps_log.append({
                    "turn": turn,
                    "tool": fn_name,
                    "args": args,
                    "is_error": result.is_error,
                    "output": result.output_text,
                    "latency_ms": exec_ms
                })

                # Pass observation back to context
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": fn_name,
                    "content": result.output_text
                })

            time.sleep(2.0)

        return {
            "status": "MAX_TURNS_EXCEEDED",
            "turns": max_turns,
            "steps": steps_log,
            "final_answer": "Reached maximum turns."
        }
