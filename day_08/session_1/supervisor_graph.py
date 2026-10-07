"""
LangGraph Multi-Agent Supervisor Orchestration Graph.
Implements:
- Central Supervisor node routing dynamically between specialized workers
- Conditional routing edges based on structured router output
- Loop and iteration caps to avoid infinite delegation
- Per-node telemetry tracking (latency, token consumption, routing trace)
"""

import time
from typing import Any, Dict
from langgraph.graph import StateGraph, START, END

from state import MultiAgentState, initialize_state
from agents import SupervisorAgent, ResearcherAgent, WriterAgent


class MultiAgentOrchestrator:
    """
    Manages and executes the LangGraph multi-agent supervisor graph.
    """

    def __init__(self, max_iterations: int = 6):
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.max_iterations = max_iterations
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(MultiAgentState)

        # 1. Define Nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("writer", self._writer_node)

        # 2. Define Edges
        workflow.add_edge(START, "supervisor")

        # Dynamic conditional routing from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "researcher": "researcher",
                "writer": "writer",
                "FINISH": END,
            }
        )

        # Workers always report back to supervisor for evaluation
        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("writer", "supervisor")

        return workflow.compile()

    def _supervisor_node(self, state: MultiAgentState) -> Dict[str, Any]:
        """Supervisor inspects state, updates telemetry, and determines next step."""
        t0 = time.monotonic()
        current_iter = state.get("iteration", 0) + 1

        # Check iteration cap
        if current_iter > self.max_iterations:
            elapsed = time.monotonic() - t0
            decision = {
                "next_agent": "FINISH",
                "instructions": f"Halted: Maximum iterations ({self.max_iterations}) exceeded.",
                "rationale": "Safety guard: Prevent infinite supervisor-worker ping-pong.",
                "quality_assessment": "Force completed due to iteration limit."
            }
        else:
            decision = self.supervisor.evaluate_and_route(state)
            elapsed = time.monotonic() - t0

        # Update telemetry
        telemetry = dict(state.get("telemetry", {}))
        node_latencies = dict(telemetry.get("node_latencies", {}))
        node_latencies[f"supervisor_turn_{current_iter}"] = round(elapsed, 3)
        telemetry["node_latencies"] = node_latencies
        telemetry["total_latency_sec"] = round(telemetry.get("total_latency_sec", 0.0) + elapsed, 3)

        routing_history = list(telemetry.get("routing_decisions", []))
        routing_history.append({
            "iteration": current_iter,
            "decision": decision["next_agent"],
            "rationale": decision.get("rationale", ""),
            "duration_sec": round(elapsed, 3)
        })
        telemetry["routing_decisions"] = routing_history

        history = list(state.get("execution_history", []))
        history.append({
            "node": "supervisor",
            "iteration": current_iter,
            "target": decision["next_agent"],
            "instructions": decision.get("instructions", ""),
            "rationale": decision.get("rationale", ""),
            "elapsed_sec": round(elapsed, 3)
        })

        return {
            "iteration": current_iter,
            "next_agent": decision["next_agent"],
            "supervisor_instructions": decision.get("instructions", ""),
            "review_feedback": decision.get("quality_assessment", ""),
            "execution_history": history,
            "telemetry": telemetry
        }

    def _researcher_node(self, state: MultiAgentState) -> Dict[str, Any]:
        """Researcher node executes domain investigation."""
        t0 = time.monotonic()
        task = state["task"]
        instructions = state.get("supervisor_instructions", "Perform comprehensive technical research.")

        notes = self.researcher.research(task=task, supervisor_instructions=instructions)
        elapsed = time.monotonic() - t0

        telemetry = dict(state.get("telemetry", {}))
        node_latencies = dict(telemetry.get("node_latencies", {}))
        node_latencies[f"researcher_turn_{state.get('iteration', 1)}"] = round(elapsed, 3)
        telemetry["node_latencies"] = node_latencies
        telemetry["total_latency_sec"] = round(telemetry.get("total_latency_sec", 0.0) + elapsed, 3)

        history = list(state.get("execution_history", []))
        history.append({
            "node": "researcher",
            "iteration": state.get("iteration", 1),
            "output_preview": notes[:150] + "...",
            "elapsed_sec": round(elapsed, 3)
        })

        return {
            "research_notes": notes,
            "execution_history": history,
            "telemetry": telemetry
        }

    def _writer_node(self, state: MultiAgentState) -> Dict[str, Any]:
        """Writer node synthesizes research into an executive briefing."""
        t0 = time.monotonic()
        task = state["task"]
        notes = state.get("research_notes", "")
        instructions = state.get("supervisor_instructions", "Draft executive briefing from research.")

        report = self.writer.write(task=task, research_notes=notes, supervisor_instructions=instructions)
        elapsed = time.monotonic() - t0

        telemetry = dict(state.get("telemetry", {}))
        node_latencies = dict(telemetry.get("node_latencies", {}))
        node_latencies[f"writer_turn_{state.get('iteration', 1)}"] = round(elapsed, 3)
        telemetry["node_latencies"] = node_latencies
        telemetry["total_latency_sec"] = round(telemetry.get("total_latency_sec", 0.0) + elapsed, 3)

        history = list(state.get("execution_history", []))
        history.append({
            "node": "writer",
            "iteration": state.get("iteration", 1),
            "output_preview": report[:150] + "...",
            "elapsed_sec": round(elapsed, 3)
        })

        return {
            "draft_report": report,
            "execution_history": history,
            "telemetry": telemetry
        }

    def _route_decision(self, state: MultiAgentState) -> str:
        """Route from supervisor to chosen worker or END."""
        next_step = state.get("next_agent", "FINISH")
        if state.get("iteration", 0) > self.max_iterations:
            return "FINISH"
        if next_step in ("researcher", "writer"):
            return next_step
        return "FINISH"

    def run(self, task: str) -> MultiAgentState:
        """Runs the complete multi-agent graph from START to FINISH."""
        initial_state = initialize_state(task=task, max_iterations=self.max_iterations)
        final_state = self.graph.invoke(initial_state)
        return final_state
