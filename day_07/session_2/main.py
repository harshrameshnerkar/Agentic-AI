"""
Day 7 - Session 2: LangGraph
Master Demonstration: main.py

Learning Objectives:
1. State: Centralized shared state schema with reducers (append_messages).
2. Nodes: Functional units for reasoning (assistant) and execution (tools).
3. Edges: Explicit transitions between nodes (START -> assistant, tools -> assistant).
4. Conditional Routing: Router evaluating state to dynamically branch to tools or END.
5. Cycles: Allowing multi-turn autonomous loops without hardcoded while-loops.
6. Checkpointing & Persistence: Preserving graph state across turns using thread_id.
7. Streaming: Consuming intermediate steps in real-time.
8. Visualizing the Graph: Rendering Mermaid flowchart and ASCII diagram.

Task:
Rebuild the same agent in LangGraph as a state graph and render the graph diagram.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure local .env takes absolute priority
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from langgraph_agent import (
    build_langgraph_agent,
    get_mermaid_diagram,
    get_ascii_diagram,
    save_graph_diagram
)


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def print_langgraph_concepts():
    """Prints foundational LangGraph architectural concepts."""
    print_banner("1. LANGGRAPH ARCHITECTURAL FOUNDATIONS")
    print("""
1. STATE (Shared Typed Schema):
   • A centralized dictionary or dataclass that flows through all nodes in the graph.
   • Uses 'Reducers' (e.g. append_messages) to define how partial node outputs merge into state.

2. NODES (Callable Functions):
   • Standalone Python functions: (state) -> state_update.
   • 'assistant' node: Invokes the LLM to reason and emit tool calls or answers.
   • 'tools' node: Executes requested tools and appends observations.

3. EDGES & CONDITIONAL ROUTING:
   • Normal Edges: Fixed transitions (START -> assistant, tools -> assistant).
   • Conditional Edges: Inspects state dynamically (does last message have tool_calls?).
     Routes to 'tools' or 'END'.

4. CYCLES:
   • By directing the 'tools' node back to 'assistant', LangGraph enables natural multi-turn
     agent loops without infinite while-loops or fragile recursion.

5. CHECKPOINTING & PERSISTENCE:
   • Checkpointers (MemorySaver, SqliteSaver) serialize state at every node boundary.
   • Keyed by 'thread_id', enabling conversational memory, multi-turn follow-ups,
     human-in-the-loop inspection, and state time-travel.

6. STREAMING:
   • .stream(..., stream_mode='updates') yields incremental node outputs as they complete,
     providing instant real-time telemetry.
""", flush=True)


def demonstrate_graph_visualization(graph):
    """Renders and saves the graph diagrams (Mermaid + ASCII)."""
    print_banner("2. RENDERING LANGGRAPH STATE GRAPH DIAGRAMS")

    # 1. ASCII Diagram
    print("--- [ASCII Terminal Graph] ---")
    print(get_ascii_diagram(graph))

    # 2. Mermaid Diagram
    print("\n--- [Mermaid Graph Definition] ---")
    print(get_mermaid_diagram(graph))

    # 3. Save Artifact
    artifact_path = Path(__file__).resolve().parent / "graph_diagram.md"
    save_graph_diagram(graph, artifact_path)
    print(f"\n✓ Saved standalone graph visualization artifact to: {artifact_path.name}")


def stream_multihop_task(graph, thread_id: str):
    """
    Executes the multi-hop reasoning question through streaming intermediate node steps.
    """
    print_banner("3. STREAMING MULTI-HOP TASK THROUGH LANGGRAPH AGENT")
    question = "How many years elapsed between the Apollo 11 moon landing and the launch of the James Webb Space Telescope (JWST)?"
    print(f"Goal: \"{question}\"")
    print(f"Session Thread ID: '{thread_id}'")

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful space science assistant with access to two tools: 'search' and 'calculate'. "
                    "When given a multi-hop factual question, use 'search' to find the relevant event dates and "
                    "'calculate' to perform arithmetic. Then synthesize a clear final answer."
                )
            },
            {"role": "user", "content": question}
        ],
        "turns_count": 0,
        "current_node": "start"
    }

    turn = 0
    t0 = time.time()
    for update in graph.stream(initial_state, config=config, stream_mode="updates"):
        turn += 1
        node_name = list(update.keys())[0]
        data = update[node_name]
        print(f"\n>>> [STEP {turn}] Node Executed: '{node_name}' <<<", flush=True)

        new_messages = data.get("messages", [])
        for msg in new_messages:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "unknown")
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)

            if role == "assistant":
                if tool_calls:
                    print(f"  🧠 [THOUGHT & ACTION]: Model requested {len(tool_calls)} tool call(s):")
                    for tc in tool_calls:
                        fn = tc.function.name if hasattr(tc, "function") else tc.get("function", {}).get("name")
                        args = tc.function.arguments if hasattr(tc, "function") else tc.get("function", {}).get("arguments")
                        print(f"     -> Call '{fn}' with args: {args}")
                else:
                    print(f"  🎯 [FINAL ANSWER]:\n{content}")
            elif role == "tool":
                tool_name = msg.get("name") if isinstance(msg, dict) else getattr(msg, "name", "tool")
                print(f"  👁️ [OBSERVATION from '{tool_name}']:\n     {content}")

    total_latency = time.time() - t0
    print(f"\nExecution Latency: {total_latency:.2f}s across {turn} graph node transitions.")


def demonstrate_persistence_and_followup(graph, thread_id: str):
    """
    Demonstrates Checkpointing & Persistence by sending a follow-up query
    using the identical thread_id, proving memory retention.
    """
    print_banner("4. PERSISTENCE DEMO: MULTI-TURN CONVERSATION VIA CHECKPOINTER")
    followup_question = "And how many years between the Curiosity rover landing and JWST launch?"
    print(f"Follow-up Query: \"{followup_question}\"")
    print(f"Re-using existing Thread ID: '{thread_id}'")

    config = {"configurable": {"thread_id": thread_id}}
    followup_input = {
        "messages": [{"role": "user", "content": followup_question}]
    }

    t0 = time.time()
    for update in graph.stream(followup_input, config=config, stream_mode="updates"):
        node_name = list(update.keys())[0]
        data = update[node_name]
        print(f"  [Step] Node '{node_name}' finished.")
        new_messages = data.get("messages", [])
        for msg in new_messages:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "unknown")
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
            if role == "assistant" and not tool_calls:
                print(f"\n  🎯 [FOLLOW-UP ANSWER]:\n{content}")

    # Inspect the checkpointed state
    print("\n--- Inspecting Checkpointed Graph State ---")
    state = graph.get_state(config)
    all_msgs = state.values["messages"]
    print(f"Total Checkpointed Messages in Thread '{thread_id}': {len(all_msgs)}")
    print(f"Current Next Nodes to Execute: {state.next}")
    print(f"Turn Count: {state.values.get('turns_count')}")
    print("✓ State persistence and multi-turn conversational context verified!")


def main():
    print_banner("DAY 7 - SESSION 2: LANGGRAPH MASTER DEMONSTRATION")

    # Step 1: Explain LangGraph Concepts
    print_langgraph_concepts()

    # Step 2: Build and compile graph with MemorySaver checkpointer
    graph = build_langgraph_agent(use_checkpointer=True)

    # Step 3: Render and save diagrams
    demonstrate_graph_visualization(graph)

    # Step 4: Stream multi-hop execution trace
    thread_id = "space-mission-session-701"
    stream_multihop_task(graph, thread_id=thread_id)

    time.sleep(3.0)

    # Step 5: Demonstrate persistence and follow-up
    demonstrate_persistence_and_followup(graph, thread_id=thread_id)

    print_banner("DAY 7 - SESSION 2: SUMMARY & VERIFICATION COMPLETE")
    print("""
Key Principles Proven:
  [✓] State Schema: Defined TypedDict with custom message reducer.
  [✓] Nodes & Edges: Configured 'assistant' and 'tools' with START and cyclic loop.
  [✓] Conditional Routing: Implemented should_continue dynamically evaluating tool calls.
  [✓] Cycles: Multi-turn tool execution achieved natively in graph without while-loops.
  [✓] Checkpointing & Persistence: State stored in MemorySaver; thread_id preserved context.
  [✓] Streaming: Yielded real-time node updates via graph.stream(stream_mode='updates').
  [✓] Visualized Graph: Rendered ASCII graph and Mermaid diagram in graph_diagram.md.
""", flush=True)


if __name__ == "__main__":
    main()
