"""
Day 7 - Session 3: Memory
Module: langgraph_memory_agent.py

LangGraph agent integrating:
1. Long-term persistent memory (per-user_id) via SQLite PersistentMemoryStore
2. Short-term thread memory (per-thread_id)
3. Just-in-time memory retrieval node dynamically injecting recalled preferences
4. Tool-based preference updating and operational telemetry
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
from typing import Annotated, Literal, List, Dict, Any, Optional
from typing_extensions import TypedDict
from dotenv import load_dotenv
from openai import OpenAI

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

sys.path.insert(0, str(Path(__file__).resolve().parent))
from memory_store import PersistentMemoryStore
from tools import MEMORY_AGENT_TOOLS, execute_get_cluster_metrics

# Load local environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)


def serialize_message(msg: Any) -> Dict[str, Any]:
    """Standardizes messages into native dictionaries with thought signature preservation."""
    if isinstance(msg, dict):
        return msg

    role = getattr(msg, "role", "assistant")
    content = getattr(msg, "content", "") or ""
    d: Dict[str, Any] = {"role": role, "content": content}

    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        serial_calls = []
        for call in tool_calls:
            fn_name = call.function.name if hasattr(call, "function") else call.get("function", {}).get("name")
            fn_args = call.function.arguments if hasattr(call, "function") else call.get("function", {}).get("arguments")
            call_id = getattr(call, "id", None) or call.get("id")

            call_dict: Dict[str, Any] = {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": fn_name,
                    "arguments": fn_args
                }
            }
            extra = getattr(call, "extra_content", None) or (call.get("extra_content") if isinstance(call, dict) else None)
            if extra:
                call_dict["extra_content"] = extra
            serial_calls.append(call_dict)
        d["tool_calls"] = serial_calls

    return d


def append_messages(existing: List[Any], new_items: List[Any]) -> List[Any]:
    clean_existing = [serialize_message(m) for m in existing]
    clean_new = [serialize_message(m) for m in new_items]
    return clean_existing + clean_new


class MemoryAgentState(TypedDict):
    """Shared state for the memory-aware LangGraph agent."""
    messages: Annotated[List[Dict[str, Any]], append_messages]
    user_id: str
    thread_id: str
    recalled_memory: str
    turns_count: int


class MemoryAwareAgent:
    """
    Manages LangGraph StateGraph lifecycle with persistent SQLite memory store.
    """

    def __init__(self, memory_store: Optional[PersistentMemoryStore] = None):
        self.memory_store = memory_store or PersistentMemoryStore()
        self.graph = self._build_graph()

    def _call_llm_with_backoff(self, messages: List[Dict[str, Any]]) -> Any:
        from openai import RateLimitError, InternalServerError, APIConnectionError
        max_retries = 5
        base_delay = 5.0
        for attempt in range(1, max_retries + 1):
            try:
                return client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    tools=MEMORY_AGENT_TOOLS,
                    tool_choice="auto"
                )
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

    def memory_retrieval_node(self, state: MemoryAgentState) -> Dict[str, Any]:
        """
        Just-in-Time Memory Retrieval:
        Inspects user_id, queries SQLite for persistent preferences,
        and ensures system instructions contain recalled preferences.
        """
        user_id = state.get("user_id", "default_user")
        recalled_block = self.memory_store.build_memory_prompt_injection(user_id)

        base_system = (
            "You are an enterprise infrastructure AI assistant. "
            "You have access to tools: 'save_user_preference' (to persist user preferences, rules, or identity) "
            "and 'get_cluster_metrics' (to fetch system telemetry). "
            "Always follow user preferences faithfully."
        )

        full_system = f"{base_system}\n\n{recalled_block}" if recalled_block else base_system

        # Check if first message is system prompt
        current_messages = list(state.get("messages", []))
        if current_messages and current_messages[0].get("role") == "system":
            # Update system prompt with fresh memory injection
            updated_first = dict(current_messages[0])
            updated_first["content"] = full_system
            # Replace first message
            return {
                "messages": [updated_first] + current_messages[1:],
                "recalled_memory": recalled_block
            }
        else:
            # Prepend system prompt
            system_msg = {"role": "system", "content": full_system}
            return {
                "messages": [system_msg],
                "recalled_memory": recalled_block
            }

    def assistant_node(self, state: MemoryAgentState) -> Dict[str, Any]:
        """Invokes LLM with current messages and returns assistant message."""
        clean_history = [serialize_message(m) for m in state["messages"]]
        resp = self._call_llm_with_backoff(clean_history)
        raw_msg = resp.choices[0].message
        return {
            "messages": [serialize_message(raw_msg)],
            "turns_count": state.get("turns_count", 0) + 1
        }

    def tools_node(self, state: MemoryAgentState) -> Dict[str, Any]:
        """Executes tool calls (saving preference or fetching metrics)."""
        last_msg = state["messages"][-1]
        tool_calls = last_msg.get("tool_calls") if isinstance(last_msg, dict) else getattr(last_msg, "tool_calls", None) or []
        user_id = state.get("user_id", "default_user")
        tool_observations = []

        for call in tool_calls:
            fn_name = call.get("function", {}).get("name") if isinstance(call, dict) else call.function.name
            raw_args = call.get("function", {}).get("arguments") if isinstance(call, dict) else call.function.arguments
            call_id = call.get("id") if isinstance(call, dict) else getattr(call, "id", None)

            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}

            if fn_name == "save_user_preference":
                key = args.get("key", "")
                val = args.get("value", "")
                cat = args.get("category", "general")
                # Persist directly into SQLite memory store under user_id!
                obs = self.memory_store.save_user_preference(
                    user_id=user_id,
                    key=key,
                    value=val,
                    category=cat
                )
            elif fn_name == "get_cluster_metrics":
                svc = args.get("service_name", "Storage Gateway")
                obs = execute_get_cluster_metrics(svc)
            else:
                obs = {"status": "error", "message": f"Unknown tool: {fn_name}"}

            tool_observations.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": fn_name,
                "content": json.dumps(obs)
            })

        time.sleep(1.5)
        return {"messages": tool_observations}

    def _should_continue(self, state: MemoryAgentState) -> Literal["tools", "__end__"]:
        last_msg = state["messages"][-1]
        tool_calls = last_msg.get("tool_calls") if isinstance(last_msg, dict) else getattr(last_msg, "tool_calls", None)
        if tool_calls and len(tool_calls) > 0:
            return "tools"
        return "__end__"

    def _build_graph(self):
        builder = StateGraph(MemoryAgentState)

        # Add Nodes
        builder.add_node("memory_retrieval", self.memory_retrieval_node)
        builder.add_node("assistant", self.assistant_node)
        builder.add_node("tools", self.tools_node)

        # Add Edges
        builder.add_edge(START, "memory_retrieval")
        builder.add_edge("memory_retrieval", "assistant")
        builder.add_conditional_edges(
            "assistant",
            self._should_continue,
            {
                "tools": "tools",
                "__end__": END
            }
        )
        builder.add_edge("tools", "assistant")

        return builder.compile(checkpointer=MemorySaver())

    def run_turn(self, user_id: str, thread_id: str, user_message: str) -> str:
        """
        Executes a turn, streaming updates and returning the final assistant answer.
        """
        config = {"configurable": {"thread_id": thread_id}}
        input_data = {
            "messages": [{"role": "user", "content": user_message}],
            "user_id": user_id,
            "thread_id": thread_id,
            "turns_count": 0
        }

        final_content = ""
        for update in self.graph.stream(input_data, config=config, stream_mode="updates"):
            node = list(update.keys())[0]
            data = update[node]
            msgs = data.get("messages", [])
            for m in msgs:
                role = m.get("role") if isinstance(m, dict) else getattr(m, "role", "")
                content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
                tool_calls = m.get("tool_calls") if isinstance(m, dict) else getattr(m, "tool_calls", None)

                if node == "memory_retrieval" and data.get("recalled_memory"):
                    print(f"\n  🔍 [JUST-IN-TIME MEMORY RETRIEVAL]:\n{data['recalled_memory']}")
                elif node == "assistant":
                    if tool_calls:
                        print(f"  ⚡ [ACTION] Assistant requested {len(tool_calls)} tool(s):")
                        for tc in tool_calls:
                            fn = tc.get("function", {}).get("name") if isinstance(tc, dict) else tc.function.name
                            args = tc.get("function", {}).get("arguments") if isinstance(tc, dict) else tc.function.arguments
                            print(f"     • {fn}({args})")
                    elif content:
                        final_content = content
                elif node == "tools":
                    print(f"  👁️ [OBSERVATION]: {content[:200]}")

        return final_content
