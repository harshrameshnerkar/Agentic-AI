"""
Test Suite for Production Incident Response & Operational Safety (Day 14 - Session 4).
Validates multi-tier kill switches, circuit breaker state machine,
automated configuration rollbacks, and defensive schema parsing.
"""

import unittest
import os
import time
from typing import Dict, Any

from day_14.session_4.kill_switch_controller import (
    EmergencyKillSwitchController,
    KillSwitchLevel,
    CircuitBreakerState,
    PromptModelConfig,
)
from day_14.session_4.main import defensive_json_parser


class IncidentResponseTestSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.initial_config = PromptModelConfig(
            version="v1.0.0-stable",
            model_id="claude-3-5-sonnet-20241022",
            prompt_template="Base stable prompt template",
        )
        self.controller = EmergencyKillSwitchController(
            initial_config=self.initial_config,
            error_threshold=3,
            recovery_time_seconds=0.1,  # Short timeout for fast testing
        )

    def test_01_kill_switch_level_enforcement(self) -> None:
        """Verifies policy enforcement across all 4 kill switch levels."""
        # 1. NORMAL: Both read-only and destructive actions allowed
        self.controller.set_kill_switch(KillSwitchLevel.NORMAL, "Healthy state")
        ok_read, _ = self.controller.validate_action_execution("read_logs", is_destructive=False)
        ok_destr, _ = self.controller.validate_action_execution("restart_pod", is_destructive=True)
        self.assertTrue(ok_read)
        self.assertTrue(ok_destr)

        # 2. READ_ONLY: Read-only allowed, destructive blocked
        self.controller.set_kill_switch(KillSwitchLevel.READ_ONLY, "Suspicious mutations")
        ok_read, _ = self.controller.validate_action_execution("read_logs", is_destructive=False)
        ok_destr, msg = self.controller.validate_action_execution("restart_pod", is_destructive=True)
        self.assertTrue(ok_read)
        self.assertFalse(ok_destr)
        self.assertIn("BLOCKED", msg)

        # 3. MANDATORY_HITL: All actions require human sign-off
        self.controller.set_kill_switch(KillSwitchLevel.MANDATORY_HITL, "High hallucination drift")
        ok_read, msg_read = self.controller.validate_action_execution("read_logs", is_destructive=False)
        self.assertFalse(ok_read)
        self.assertIn("ESCALATED", msg_read)

        # 4. EMERGENCY_SHUTDOWN: All actions frozen
        self.controller.set_kill_switch(KillSwitchLevel.EMERGENCY_SHUTDOWN, "Catastrophic failure")
        ok_read, msg_sd = self.controller.validate_action_execution("read_logs", is_destructive=False)
        self.assertFalse(ok_read)
        self.assertIn("BLOCKED: Emergency kill switch", msg_sd)

    def test_02_circuit_breaker_tripping_and_recovery(self) -> None:
        """Verifies circuit breaker trips upon error threshold and transitions through HALF_OPEN."""
        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.CLOSED)

        # Record 2 failures (threshold is 3)
        self.controller.record_provider_result(False, "504 Gateway Timeout")
        self.controller.record_provider_result(False, "504 Gateway Timeout")
        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.CLOSED)

        # 3rd failure trips circuit breaker
        self.controller.record_provider_result(False, "504 Gateway Timeout")
        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.OPEN)
        self.assertEqual(self.controller.current_level, KillSwitchLevel.READ_ONLY)

        # Wait for cooloff timeout (0.1s in test)
        time.sleep(0.12)
        state_probing = self.controller.check_circuit_breaker()
        self.assertEqual(state_probing, CircuitBreakerState.HALF_OPEN)

        # Probing success resets circuit breaker
        self.controller.record_provider_result(True)
        self.assertEqual(self.controller.circuit_state, CircuitBreakerState.CLOSED)
        self.assertEqual(self.controller.consecutive_failures, 0)

    def test_03_prompt_and_model_rollback(self) -> None:
        """Verifies configuration rollback restores last known good baseline."""
        # Baseline is v1.0.0-stable
        self.assertEqual(self.controller.active_config.version, "v1.0.0-stable")

        # Deploy candidate version v1.2.0
        candidate_config = PromptModelConfig(
            version="v1.2.0-candidate",
            model_id="gpt-4o-latest",
            prompt_template="Candidate prompt with higher temperature",
        )
        self.controller.deploy_config(candidate_config)
        self.assertEqual(self.controller.active_config.version, "v1.2.0-candidate")

        # Emergency rollback to LKG
        restored = self.controller.rollback_to_last_known_good(reason="Regression detected in prod")
        self.assertEqual(restored.version, "v1.0.0-stable")
        self.assertEqual(self.controller.active_config.version, "v1.0.0-stable")

        # Check audit log entries
        events = [e["event"] for e in self.controller.safety_audit_log]
        self.assertIn("CONFIG_DEPLOYED", events)
        self.assertIn("CONFIG_ROLLBACK", events)

    def test_04_defensive_json_parser_mitigation(self) -> None:
        """Verifies defensive JSON parser handles markdown fences, extra whitespace, and raw JSON."""
        # 1. Raw JSON
        raw = '{"service": "payment-api", "status": "active"}'
        self.assertEqual(defensive_json_parser(raw)["service"], "payment-api")

        # 2. Markdown fenced JSON
        fenced = '```json\n{"service": "auth-api", "error_code": 403}\n```'
        parsed_fenced = defensive_json_parser(fenced)
        self.assertEqual(parsed_fenced["service"], "auth-api")
        self.assertEqual(parsed_fenced["error_code"], 403)

        # 3. Generic codeblock fenced JSON
        generic_fence = '```\n{"database": "primary-postgres", "replica_lag": 12}\n```'
        parsed_generic = defensive_json_parser(generic_fence)
        self.assertEqual(parsed_generic["database"], "primary-postgres")

    def test_05_incident_runbook_and_postmortem_documentation(self) -> None:
        """Verifies incident response runbook and blameless postmortem artifacts exist and contain key sections."""
        base_dir = os.path.dirname(__file__)
        runbook_path = os.path.join(base_dir, "incident_runbook.md")
        postmortem_path = os.path.join(base_dir, "postmortem_incident_inc042.md")

        self.assertTrue(os.path.exists(runbook_path), "incident_runbook.md missing")
        self.assertTrue(os.path.exists(postmortem_path), "postmortem_incident_inc042.md missing")

        with open(runbook_path, "r", encoding="utf-8") as f:
            rb_content = f.read()
            self.assertIn("Severity Classification", rb_content)
            self.assertIn("Kill Switch Playbook", rb_content)
            self.assertIn("Silent Model Update", rb_content)

        with open(postmortem_path, "r", encoding="utf-8") as f:
            pm_content = f.read()
            self.assertIn("Executive Summary", pm_content)
            self.assertIn("Incident Timeline", pm_content)
            self.assertIn("Root Cause Analysis", pm_content)
            self.assertIn("Action Items", pm_content)


if __name__ == "__main__":
    unittest.main()
