"""Day 17 - Session 1: Unit & Integration Tests for Standup & Riskiest Task."""

import asyncio
import os
import unittest

try:
    from .riskiest_task_derisker import (
        AsyncDiagnosticToolDispatcher,
        MockCloudInfrastructure,
        LogAnomalyCompactor,
        DiagnosticBundle,
    )
except ImportError:
    from riskiest_task_derisker import (
        AsyncDiagnosticToolDispatcher,
        MockCloudInfrastructure,
        LogAnomalyCompactor,
        DiagnosticBundle,
    )


class TestDay17Session1RiskiestTaskSuite(unittest.TestCase):
    """Test suite validating standup notes, backlog state, and concurrent tool de-risking."""

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.cloud_api = MockCloudInfrastructure(simulate_network_delay=0.1)
        self.dispatcher = AsyncDiagnosticToolDispatcher(
            cloud_api=self.cloud_api, tool_timeout_sec=1.5
        )

    def test_concurrent_dispatch_latency_and_schema(self):
        """Verifies that all 4 tools execute concurrently in under 2.5 seconds."""
        bundle = asyncio.run(
            self.dispatcher.dispatch_all_diagnostics(
                incident_id="INC-TEST-001",
                service="auth-service",
                namespace="prod-core",
            )
        )

        self.assertIsInstance(bundle, DiagnosticBundle)
        self.assertEqual(bundle.incident_id, "INC-TEST-001")
        self.assertEqual(bundle.service, "auth-service")
        self.assertEqual(bundle.namespace, "prod-core")

        # Must execute concurrently in under 2500ms
        self.assertLess(bundle.total_execution_ms, 2500.0)
        self.assertEqual(len(bundle.circuit_breaker_fallbacks), 0)

        # Check pod telemetry
        self.assertEqual(bundle.pod_telemetry.get("phase"), "CrashLoopBackOff")
        self.assertEqual(
            bundle.pod_telemetry.get("last_state", {})
            .get("terminated", {})
            .get("exit_code"),
            137,
        )

        # Check metrics telemetry
        self.assertGreater(bundle.metrics_telemetry.get("memory_ratio", 0), 0.95)

        # Check git telemetry
        self.assertTrue(bundle.git_telemetry.get("commit_sha"))

        # Check log compaction
        self.assertGreaterEqual(len(bundle.log_anomalies), 1)

    def test_log_anomaly_compactor_accuracy(self):
        """Verifies that 50,000 noisy logs are scanned and fatal traces extracted in < 1.5s."""
        raw_logs = [
            f"[INFO] 2026-10-08T09:00:{i%60:02d}Z request_id={i} status=200 path=/api/health"
            for i in range(50000)
        ]
        # Inject exact fatal error
        raw_logs.insert(
            25000,
            "[FATAL] java.lang.OutOfMemoryError: Java heap space at auth.TokenBuffer:99",
        )

        anomalies = LogAnomalyCompactor.compact_logs(raw_logs, max_anomalies=5)
        self.assertGreaterEqual(len(anomalies), 1)
        top_anomaly = anomalies[0]
        self.assertIn("OutOfMemoryError", top_anomaly["headline"])
        self.assertIn("context_snippet", top_anomaly)
        self.assertEqual(top_anomaly["occurrences"], 1)

    def test_circuit_breaker_timeout_resilience(self):
        """Verifies that a hanging tool triggers timeout without crashing sibling tools."""
        bundle = asyncio.run(
            self.dispatcher.dispatch_all_diagnostics(
                incident_id="INC-FAULT-002",
                service="auth-service",
                namespace="prod-core",
                simulate_faulty_tool="pod",
            )
        )

        # Check circuit breaker recorded the timeout
        self.assertEqual(len(bundle.circuit_breaker_fallbacks), 1)
        self.assertIn("CIRCUIT_BREAKER_TIMEOUT", bundle.circuit_breaker_fallbacks[0])
        self.assertEqual(bundle.pod_telemetry.get("phase"), "UNKNOWN")

        # Sibling tools must have succeeded
        self.assertTrue(bundle.metrics_telemetry.get("memory_ratio"))
        self.assertTrue(bundle.git_telemetry.get("commit_sha"))
        self.assertGreaterEqual(len(bundle.log_anomalies), 1)

    def test_standup_and_backlog_artifacts(self):
        """Verifies presence and depth of standup notes and sprint backlog documents."""
        standup_file = os.path.join(self.base_dir, "STANDUP_NOTES.md")
        backlog_file = os.path.join(self.base_dir, "SPRINT_BACKLOG.md")

        for f_path in [standup_file, backlog_file]:
            self.assertTrue(os.path.isfile(f_path), f"Missing document: {f_path}")
            with open(f_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 800)

        with open(standup_file, "r", encoding="utf-8") as f:
            s_text = f.read()
            self.assertIn("What Was Done", s_text)
            self.assertIn("What Is Next", s_text)
            self.assertIn("Blockers & Risks", s_text)
            self.assertIn("IN PROGRESS", s_text)

        with open(backlog_file, "r", encoding="utf-8") as f:
            b_text = f.read()
            self.assertIn("TASK-1.1", b_text)
            self.assertIn("IN PROGRESS", b_text)
            self.assertIn("Acceptance Criteria", b_text)


if __name__ == "__main__":
    unittest.main()
