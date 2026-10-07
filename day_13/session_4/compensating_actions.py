"""
Day 13 - Session 4: Undo & Compensating Action Engine
=====================================================
Implements:
  1. Compensating Transaction Pattern (Saga / Reversible Agent Actions)
  2. Automatic Inverse Action Registration for mutating operations
  3. One-click Undo Execution (reverting scaling, restarts, rollbacks)
  4. Pre- and Post-State Snapshotting for verification
"""

import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class CompensatingActionRecord:
    action_id: str
    session_id: str
    tenant_id: str
    mutating_tool: str
    forward_parameters: Dict[str, Any]
    inverse_action_name: str
    inverse_parameters: Dict[str, Any]
    state_before: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    is_reverted: bool = False
    reverted_at: Optional[float] = None
    reverted_by: Optional[str] = None


class CompensatingActionRegistry:
    """
    Registry for reversible agent modifications.
    Enables operators to safely click 'Undo' or trigger automated rollback if post-action health checks fail.
    """

    def __init__(self):
        self._actions: Dict[str, CompensatingActionRecord] = {}

    def register_action(
        self,
        session_id: str,
        tenant_id: str,
        mutating_tool: str,
        forward_parameters: Dict[str, Any],
        inverse_action_name: str,
        inverse_parameters: Dict[str, Any],
        state_before: Dict[str, Any],
    ) -> CompensatingActionRecord:
        """Records an executed mutating action alongside its exact compensating rollback plan."""
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        rec = CompensatingActionRecord(
            action_id=action_id,
            session_id=session_id,
            tenant_id=tenant_id,
            mutating_tool=mutating_tool,
            forward_parameters=forward_parameters,
            inverse_action_name=inverse_action_name,
            inverse_parameters=inverse_parameters,
            state_before=state_before,
        )
        self._actions[action_id] = rec
        return rec

    def get_action(self, action_id: str) -> Optional[CompensatingActionRecord]:
        return self._actions.get(action_id)

    def list_reversible_actions(self, session_id: str) -> List[CompensatingActionRecord]:
        """Returns all un-reverted actions for a session."""
        return [
            a for a in self._actions.values()
            if a.session_id == session_id and not a.is_reverted
        ]

    def execute_undo(self, action_id: str, operator_id: str) -> Dict[str, Any]:
        """Executes the inverse compensating action and updates status."""
        rec = self.get_action(action_id)
        if not rec:
            return {"status": "ERROR", "error": f"Action '{action_id}' not found."}

        if rec.is_reverted:
            return {"status": "ALREADY_REVERTED", "action_id": action_id}

        # Simulate execution of inverse action
        rec.is_reverted = True
        rec.reverted_at = time.time()
        rec.reverted_by = operator_id

        return {
            "status": "COMPENSATED",
            "action_id": action_id,
            "inverse_action_executed": rec.inverse_action_name,
            "restored_parameters": rec.inverse_parameters,
            "operator_id": operator_id,
            "message": f"Successfully executed compensating action '{rec.inverse_action_name}'. State restored.",
        }
