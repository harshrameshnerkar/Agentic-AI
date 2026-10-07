"""
State Definitions and Telemetry Schema for Multi-Agent Systems.
Highlights the distinction between Shared State and Isolated State.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class MultiAgentState(TypedDict):
    """
    Shared State contract visible across the supervisor and worker nodes.

    Design Principle (Shared vs Isolated State):
    - Shared State: Contains global task objectives, finalized worker artifacts (research_notes, draft_report),
      and routing directives. Every agent has visibility into these outputs.
    - Isolated State: Each worker maintains its own private reasoning and internal scratchpad during execution,
      returning only condensed, high-value synthesized artifacts back into the shared state.
      This prevents worker context pollution (e.g. Writer is not overwhelmed with raw HTTP headers or search logs).
    """
    task: str
    next_agent: str
    supervisor_instructions: str
    research_notes: Optional[str]
    draft_report: Optional[str]
    review_feedback: Optional[str]
    iteration: int
    max_iterations: int
    execution_history: List[Dict[str, Any]]
    telemetry: Dict[str, Any]


def initialize_state(task: str, max_iterations: int = 6) -> MultiAgentState:
    """Initializes a pristine multi-agent state."""
    return {
        "task": task,
        "next_agent": "supervisor",
        "supervisor_instructions": "Initial task dispatch: evaluate task requirements.",
        "research_notes": None,
        "draft_report": None,
        "review_feedback": None,
        "iteration": 0,
        "max_iterations": max_iterations,
        "execution_history": [],
        "telemetry": {
            "node_latencies": {},
            "total_latency_sec": 0.0,
            "estimated_tokens": 0,
            "routing_decisions": [],
        }
    }
