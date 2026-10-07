"""
Day 7 - Session 2: LangGraph
Module: langgraph_agent.py

Rebuilds the ReAct agent from Session 1 as a formal LangGraph StateGraph:
- Centralized TypedDict state with reducer
- Autonomous LLM node and deterministic ToolNode
- Clean dictionary message serialization for 100% native checkpointing
- Conditional routing for tool-use cycles
- Checkpointing & state persistence via MemorySaver
- Real-time step streaming
- Visual graph rendering (Mermaid & ASCII)
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
from tools import search, calculate

# Load local environment
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)

# Tool Schemas for the OpenAI-compatible endpoint
LANGGRAPH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search factual database for historical space mission milestones and dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword, e.g., 'Apollo 11' or 'James Webb'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Safely evaluate a mathematical expression (e.g. '2021 - 1969').",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Arithmetic expression to compute"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

TOOL_EXECUTORS = {
    "search": lambda args: search.invoke(args.get("query", "")),
    "calculate": lambda args: calculate.invoke(args.get("expression", ""))
}


# ============================================================================
# 1. MESSAGE SERIALIZATION HELPER (For native msgpack checkpointing)
# ============================================================================

def serialize_message(msg: Any) -> Dict[str, Any]:
    """
    Standardizes messages into native dictionaries with thought signature preservation,
    guaranteeing seamless msgpack serialization in LangGraph MemorySaver.
    """
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


# ============================================================================
# 2. STATE DEFINITION & REDUCERS
# ============================================================================

def append_messages(existing: List[Any], new_items: List[Any]) -> List[Any]:
    """State reducer that appends new messages while preserving conversation history."""
    clean_existing = [serialize_message(m) for m in existing]
    clean_new = [serialize_message(m) for m in new_items]
    return clean_existing + clean_new


class AgentState(TypedDict):
    """
    Centralized shared state that flows across nodes in the LangGraph graph.
    """
    messages: Annotated[List[Dict[str, Any]], append_messages]
    turns_count: int
    current_node: str


# ============================================================================
# 3. GRAPH NODES (Assistant & Tools)
# ============================================================================

def call_llm_with_backoff(messages: List[Dict[str, Any]]) -> Any:
    """Invokes chat completion with backoff for rate limits."""
    from openai import RateLimitError, InternalServerError, APIConnectionError
    max_retries = 5
    base_delay = 5.0
    for attempt in range(1, max_retries + 1):
        try:
            return client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=LANGGRAPH_TOOLS,
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


def assistant_node(state: AgentState) -> Dict[str, Any]:
    """
    The reasoning node: Invokes the LLM with the current conversation history.
    Outputs an assistant message with either final content or tool_calls.
    """
    clean_history = [serialize_message(m) for m in state["messages"]]
    resp = call_llm_with_backoff(clean_history)
    msg = resp.choices[0].message
    return {
        "messages": [serialize_message(msg)],
        "turns_count": state.get("turns_count", 0) + 1,
        "current_node": "assistant"
    }


def tools_node(state: AgentState) -> Dict[str, Any]:
    """
    The execution node: Dispatches all tool calls requested by the assistant
    and appends role='tool' observation messages.
    """
    last_msg = state["messages"][-1]
    tool_calls = last_msg.get("tool_calls") if isinstance(last_msg, dict) else getattr(last_msg, "tool_calls", None) or []
    tool_observations = []

    for call in tool_calls:
        fn_name = call.get("function", {}).get("name") if isinstance(call, dict) else call.function.name
        raw_args = call.get("function", {}).get("arguments") if isinstance(call, dict) else call.function.arguments
        call_id = call.get("id") if isinstance(call, dict) else getattr(call, "id", None)

        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            args = {}

        executor = TOOL_EXECUTORS.get(fn_name)
        if executor:
            obs = executor(args)
        else:
            obs = f"Error: Tool '{fn_name}' not found."

        tool_observations.append({
            "role": "tool",
            "tool_call_id": call_id,
            "name": fn_name,
            "content": str(obs)
        })

    # Rate-limit pacing between tool execution and next assistant turn
    time.sleep(1.5)

    return {
        "messages": tool_observations,
        "current_node": "tools"
    }


# ============================================================================
# 4. CONDITIONAL ROUTING & CYCLES
# ============================================================================

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Conditional Edge: Checks if the assistant requested tool calls.
    - If tool_calls present -> Route to 'tools' node (creating a cycle).
    - If no tool_calls -> Route to '__end__' (terminating the workflow).
    """
    last_msg = state["messages"][-1]
    tool_calls = last_msg.get("tool_calls") if isinstance(last_msg, dict) else getattr(last_msg, "tool_calls", None)
    if tool_calls and len(tool_calls) > 0:
        return "tools"
    return "__end__"


# ============================================================================
# 5. GRAPH COMPILATION & CHECKPOINTING
# ============================================================================

def build_langgraph_agent(use_checkpointer: bool = True):
    """
    Assembles the LangGraph StateGraph, defines nodes, edges, conditional cycles,
    and attaches an in-memory checkpointer for session persistence.
    """
    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("assistant", assistant_node)
    builder.add_node("tools", tools_node)

    # Add Edges
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges(
        "assistant",
        should_continue,
        {
            "tools": "tools",
            "__end__": END
        }
    )
    # The Cycle: Tools edge returns back to assistant!
    builder.add_edge("tools", "assistant")

    # Compile with persistence
    checkpointer = MemorySaver() if use_checkpointer else None
    return builder.compile(checkpointer=checkpointer)


# ============================================================================
# 6. GRAPH VISUALIZATION HELPERS
# ============================================================================

def get_mermaid_diagram(graph) -> str:
    """Extracts Mermaid diagram definition for visualization in markdown/web."""
    return graph.get_graph().draw_mermaid()


def get_ascii_diagram(graph) -> str:
    """Renders ASCII terminal diagram."""
    try:
        return graph.get_graph().draw_ascii()
    except Exception as e:
        return f"ASCII rendering unavailable: {e}"


def save_graph_diagram(graph, output_path: Path):
    """Saves a standalone markdown file with Mermaid diagram and node descriptions."""
    mermaid_code = get_mermaid_diagram(graph)
    ascii_code = get_ascii_diagram(graph)

    content = f"""# LangGraph StateGraph Architecture

## 1. Mermaid Flowchart
```mermaid
{mermaid_code}
```

## 2. ASCII Graph Representation
```text
{ascii_code}
```

## 3. Graph Structure Breakdown
- **START**: Entrypoint routing into `assistant` node.
- **Node `assistant`**: LLM invocation evaluating messages & emitting tool calls or final answer.
- **Conditional Edge `should_continue`**:
  - `tools`: If `last_message.tool_calls` is non-empty.
  - `END`: If model has produced final text output.
- **Node `tools`**: Executes requested tools (`search`, `calculate`) and emits `role='tool'` observations.
- **Cyclic Edge**: `tools` routes directly back to `assistant`.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path
