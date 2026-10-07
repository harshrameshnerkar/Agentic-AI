"""
Day 13 - Session 2: Resilient Graph Agent with Durable Checkpointing & Resumption
================================================================================
Implements:
  1. Stateful Multi-Node Execution Graph (Intake -> Diagnose -> Execute Tools -> Synthesize -> Resolve)
  2. Durable Checkpointing after every node boundary via SqliteCheckpointer
  3. Crash / Kill Simulation (SimulatedCrashException at any target step)
  4. Flawless Run Resumption (Resuming from Step K+1 without re-executing steps 1..K)
  5. Audit Trail of Executed Steps (proving zero redundant side-effects)
"""

import os
import sys
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# Ensure local session directory is in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from checkpointer import SqliteCheckpointer, CheckpointRecord
from tenant_scoped_retrieval import TenantScopedRetriever


class SimulatedCrashException(Exception):
    """Raised when simulating a process termination, pod eviction, or unhandled SIGKILL."""
    pass


@dataclass
class AgentGraphState:
    session_id: str
    tenant_id: str
    user_id: str
    query: str
    step_index: int = 0
    current_node: str = "START"
    incident_type: Optional[str] = None
    tools_planned: List[str] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    root_cause_hypothesis: Optional[str] = None
    remediation_action: Optional[str] = None
    runbook_citation: Optional[str] = None
    approval_granted: bool = False
    is_resolved: bool = False
    steps_executed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "query": self.query,
            "step_index": self.step_index,
            "current_node": self.current_node,
            "incident_type": self.incident_type,
            "tools_planned": self.tools_planned,
            "tool_results": self.tool_results,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "remediation_action": self.remediation_action,
            "runbook_citation": self.runbook_citation,
            "approval_granted": self.approval_granted,
            "is_resolved": self.is_resolved,
            "steps_executed": self.steps_executed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentGraphState":
        return cls(
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            query=data["query"],
            step_index=data.get("step_index", 0),
            current_node=data.get("current_node", "START"),
            incident_type=data.get("incident_type"),
            tools_planned=data.get("tools_planned", []),
            tool_results=data.get("tool_results", []),
            root_cause_hypothesis=data.get("root_cause_hypothesis"),
            remediation_action=data.get("remediation_action"),
            runbook_citation=data.get("runbook_citation"),
            approval_granted=data.get("approval_granted", False),
            is_resolved=data.get("is_resolved", False),
            steps_executed=data.get("steps_executed", []),
        )


class ResilientGraphAgent:
    """
    LangGraph-Style Resilient Execution Engine with Durable SQLite Checkpointing.
    Executes a 5-step incident response graph.
    If the process dies at Step K, resume_run() loads the latest checkpoint
    and resumes seamlessly at Step K+1 without re-executing completed tools.
    """

    def __init__(
        self,
        checkpointer: Optional[SqliteCheckpointer] = None,
        retriever: Optional[TenantScopedRetriever] = None,
    ):
        self.checkpointer = checkpointer or SqliteCheckpointer()
        self.retriever = retriever or TenantScopedRetriever()

    # =========================================================================
    # GRAPH NODES (Step 1 to Step 5)
    # =========================================================================

    def _node_1_intake(self, state: AgentGraphState) -> None:
        """Step 1: Intake & Triage Classification."""
        state.step_index = 1
        state.current_node = "INTAKE"
        state.steps_executed.append("STEP_1_INTAKE")

        q_lower = state.query.lower()
        if "ledger" in q_lower or "payment" in q_lower or "failover" in q_lower:
            state.incident_type = "PAYMENT_LEDGER_INCIDENT"
        elif "buffer" in q_lower or "telematics" in q_lower or "fleet" in q_lower:
            state.incident_type = "FLEET_INGESTION_SATURATION"
        else:
            state.incident_type = "GENERAL_INFRASTRUCTURE_ANOMALY"

    def _node_2_diagnose(self, state: AgentGraphState) -> None:
        """Step 2: Diagnostic Planning."""
        state.step_index = 2
        state.current_node = "DIAGNOSE"
        state.steps_executed.append("STEP_2_DIAGNOSE")

        # Plan tenant-scoped diagnostic tool set
        state.tools_planned = [
            "tenant_query_telemetry",
            "tenant_retrieve_runbooks",
        ]

    def _node_3_execute_tools(self, state: AgentGraphState) -> None:
        """Step 3: Execute Diagnostic Tools."""
        state.step_index = 3
        state.current_node = "EXECUTE_TOOLS"
        state.steps_executed.append("STEP_3_EXECUTE_TOOLS")

        # Execute tenant-scoped tools
        telemetry = self.retriever.query_telemetry(state.tenant_id)
        runbooks = self.retriever.retrieve_runbooks(state.tenant_id, state.query)

        state.tool_results = [
            {"tool": "tenant_query_telemetry", "result": telemetry},
            {"tool": "tenant_retrieve_runbooks", "result": runbooks},
        ]

    def _node_4_synthesize(self, state: AgentGraphState) -> None:
        """Step 4: Synthesize Root Cause & Action Plan."""
        state.step_index = 4
        state.current_node = "SYNTHESIZE"
        state.steps_executed.append("STEP_4_SYNTHESIZE")

        # Evidence reasoning over Step 3 tool outputs
        rb_match = None
        for res in state.tool_results:
            if res.get("tool") == "tenant_retrieve_runbooks":
                matches = res["result"].get("matches", [])
                if matches:
                    rb_match = matches[0]

        if rb_match:
            state.runbook_citation = rb_match.get("runbook_id", "RB-GEN-01")
            state.root_cause_hypothesis = f"Telemetry confirms anomaly matching {rb_match.get('title')}."
            state.remediation_action = f"Apply procedure: {'; '.join(rb_match.get('steps', []))}"
        else:
            state.runbook_citation = "RB-FALLBACK-01"
            state.root_cause_hypothesis = "Standard service saturation."
            state.remediation_action = "Restart service pod and notify on-call."

    def _node_5_resolve(self, state: AgentGraphState) -> None:
        """Step 5: Apply Remediation & Incident Resolution."""
        state.step_index = 5
        state.current_node = "RESOLVE"
        state.steps_executed.append("STEP_5_RESOLVE")

        state.approval_granted = True
        state.is_resolved = True

    # =========================================================================
    # ORCHESTRATION & RESUMPTION PIPELINE
    # =========================================================================

    def run(
        self,
        session_id: str,
        tenant_id: str,
        user_id: str,
        query: str,
        kill_at_step: Optional[int] = None,
    ) -> AgentGraphState:
        """
        Executes agent graph starting from Step 1.
        If kill_at_step is provided, checkpoints at that step and simulates a process kill.
        """
        state = AgentGraphState(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            query=query,
        )

        node_pipeline = [
            (1, self._node_1_intake),
            (2, self._node_2_diagnose),
            (3, self._node_3_execute_tools),
            (4, self._node_4_synthesize),
            (5, self._node_5_resolve),
        ]

        parent_chk = None

        for step_num, node_fn in node_pipeline:
            # Execute Node
            node_fn(state)

            # Transactionally commit durable checkpoint to SQLite
            parent_chk = self.checkpointer.save_checkpoint(
                session_id=state.session_id,
                tenant_id=state.tenant_id,
                step_index=step_num,
                node_name=state.current_node,
                state=state.to_dict(),
                parent_checkpoint_id=parent_chk,
            )

            # Check if kill simulation is requested
            if kill_at_step is not None and step_num == kill_at_step:
                raise SimulatedCrashException(
                    f"[SIMULATED CRASH] Agent process crashed/killed at Step {step_num} ({state.current_node})! "
                    f"Checkpoint {parent_chk} saved to SQLite."
                )

        return state

    def resume_run(self, session_id: str, tenant_id: str) -> Tuple[AgentGraphState, int]:
        """
        Resumes an interrupted / killed execution run.
        1. Loads the latest checkpoint from SQLite.
        2. Recovers state exactly as it was when the crash occurred.
        3. Resumes execution from Step K+1 through completion.
        Returns: (completed_state, starting_step)
        """
        record = self.checkpointer.load_latest(session_id, tenant_id)
        if not record:
            raise ValueError(f"No checkpoint found for session '{session_id}' in tenant '{tenant_id}'.")

        state = AgentGraphState.from_dict(record.state)
        last_step = state.step_index
        next_step = last_step + 1

        node_pipeline = [
            (1, self._node_1_intake),
            (2, self._node_2_diagnose),
            (3, self._node_3_execute_tools),
            (4, self._node_4_synthesize),
            (5, self._node_5_resolve),
        ]

        # Only execute remaining steps
        parent_chk = record.checkpoint_id
        for step_num, node_fn in node_pipeline:
            if step_num < next_step:
                continue  # SKIP already completed steps!

            # Execute remaining node
            node_fn(state)

            # Commit subsequent checkpoint
            parent_chk = self.checkpointer.save_checkpoint(
                session_id=state.session_id,
                tenant_id=state.tenant_id,
                step_index=step_num,
                node_name=state.current_node,
                state=state.to_dict(),
                parent_checkpoint_id=parent_chk,
            )

        return state, next_step
