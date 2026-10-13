"""
Day 07 - Session 02: LangGraph Agent
Demonstrates state machines, cyclical node routing, streaming execution,
and conversation persistence with checkpointers.
"""

from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

from langgraph_agent import (
    build_langgraph_agent,
    get_ascii_diagram,
    save_graph_diagram
)


def run_agent_stream(graph, question: str, thread_id: str):
    """Streams graph updates turn-by-turn for a given question and thread."""
    print(f"\nUser: {question}")
    config = {"configurable": {"thread_id": thread_id}}
    state_input = {
        "messages": [{"role": "user", "content": question}],
        "turns_count": 0,
        "current_node": "start"
    }

    step = 0
    for update in graph.stream(state_input, config=config, stream_mode="updates"):
        node_name = list(update.keys())[0]
        step += 1
        print(f"  Step {step}: Node '{node_name}' executed")
        for msg in update[node_name].get("messages", []):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "")
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)

            if role == "assistant" and tool_calls:
                for tc in tool_calls:
                    fn = tc.function.name if hasattr(tc, "function") else tc.get("function", {}).get("name")
                    print(f"    -> Agent called tool: {fn}")
            elif role == "assistant" and not tool_calls and content:
                print(f"  Agent: {content}")
            elif role == "tool":
                tool_name = getattr(msg, "name", None) or (msg.get("name") if isinstance(msg, dict) else "tool")
                print(f"    <- Observation from {tool_name}: {content}")


def main():
    print("Building LangGraph agent with checkpointing...")
    graph = build_langgraph_agent(use_checkpointer=True)

    # Save graph diagram
    save_graph_diagram(graph)
    print("\nGraph Diagram:")
    print(get_ascii_diagram(graph))

    thread_id = "session-space-01"

    # Turn 1
    run_agent_stream(
        graph,
        "How many years elapsed between Apollo 11 moon landing and JWST launch?",
        thread_id=thread_id
    )

    # Turn 2: Follow-up question verifying conversation persistence in same thread
    run_agent_stream(
        graph,
        "And how many years between Curiosity rover landing and JWST launch?",
        thread_id=thread_id
    )

    # Inspect checkpointed state
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    print(f"\nTotal messages saved in thread '{thread_id}': {len(state.values['messages'])}")


if __name__ == "__main__":
    main()
