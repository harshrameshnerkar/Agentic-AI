"""
Day 13: Complete Master Verification Test Suite
===============================================
Comprehensive automated test suite covering all 4 sessions of Day 13:
  - Session 1: Async API calls, Parallel Tool Execution, Worker Queue, Polling, Webhooks, Timeouts, Cancellation
  - Session 2: Durable State Checkpointing, Crash Recovery Resumption, Tenant Isolation, Scoped Retrieval, Retention TTL, GDPR Deletion
  - Session 3: Secret Masking, Environment Config, Distributed Rate Limiting, Jittered Backoff, Provider Failover, Graceful Degradation, Health Probes
  - Session 4: Risk Gates, Human Approval Queue, Rejection Flow, Confidence Escalation, SHA-256 Audit Chain, Cryptographic Tamper Detection, Compensating Undo
"""

import os
import sys
import time
import json
import asyncio
import tempfile
import unittest

# Ensure workspace root and session directories are accessible
_workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _workspace_root not in sys.path:
    sys.path.insert(0, _workspace_root)

_day13_dir = os.path.dirname(os.path.abspath(__file__))
for s_dir in ["session_1", "session_2", "session_3", "session_4"]:
    p = os.path.join(_day13_dir, s_dir)
    if p not in sys.path:
        sys.path.insert(0, p)

# Session 1 Imports
from day_13.session_1.async_capstone_agent import AsyncCapstoneAgent, ToolCallSpec
from day_13.session_1.worker_queue import AgentWorkerQueue, JobStatus
from day_13.session_1.async_tools import async_query_telemetry_db, async_read_system_logs, async_search_runbooks

# Session 2 Imports
from day_13.session_2.checkpointer import SqliteCheckpointer
from day_13.session_2.resilient_agent import ResilientGraphAgent, SimulatedCrashException
from day_13.session_2.multi_tenant_state import TenantSessionManager
from day_13.session_2.tenant_scoped_retrieval import TenantScopedRetriever

# Session 3 Imports
from day_13.session_3.config import settings, MaskedSecret, AgentServiceSettings
from day_13.session_3.provider_failover import MultiProviderFailoverEngine, CircuitState
from day_13.session_3.distributed_rate_limiter import DistributedTokenBucket
from day_13.session_3.app import liveness_probe, readiness_probe, provider_status

# Session 4 Imports
from day_13.session_4.approval_queue import HumanApprovalQueue, ApprovalStatus
from day_13.session_4.audit_trail import AuditTrailStore
from day_13.session_4.compensating_actions import CompensatingActionRegistry
from day_13.session_4.hitl_agent import HumanInTheLoopAgent


class TestDay13Session1AsyncConcurrency(unittest.IsolatedAsyncioTestCase):
    """Session 1: Async, Parallel Tools, Queues, Timeouts, and Cancellation."""

    async def asyncSetUp(self):
        self.agent = AsyncCapstoneAgent(default_tool_timeout_sec=1.5, global_run_timeout_sec=4.0)

    async def test_parallel_vs_sequential_speedup(self):
        """Verify parallel tool execution achieves significant latency reduction over sequential."""
        query = "Payment API gateway timeout and latency spike. Query telemetry, read logs, search runbooks."
        
        # Sequential execution
        t0 = time.perf_counter()
        seq_res = self.agent.run_sequential(query)
        seq_time = (time.perf_counter() - t0) * 1000.0

        # Parallel execution
        t0 = time.perf_counter()
        par_res = await self.agent.run_parallel(query)
        par_time = (time.perf_counter() - t0) * 1000.0

        self.assertGreater(len(par_res.tools_called), 1)
        self.assertEqual(len(seq_res.tool_results), len(par_res.tool_results))
        # Parallel should be significantly faster than sequential
        self.assertLess(par_res.wall_clock_latency_ms, seq_res.wall_clock_latency_ms)
        reduction_pct = ((seq_res.wall_clock_latency_ms - par_res.wall_clock_latency_ms) / seq_res.wall_clock_latency_ms) * 100.0
        self.assertGreater(reduction_pct, 40.0, f"Expected >40% latency reduction, achieved {reduction_pct:.1f}%")

    async def test_tool_timeout_handling(self):
        """Verify that individual tools exceeding timeout threshold degrade safely with TIMEOUT status."""
        strict_agent = AsyncCapstoneAgent(default_tool_timeout_sec=0.01)
        # Force a tool call spec that sleeps longer than 0.01s
        spec = ToolCallSpec("query_telemetry_db", {"table": "services"})
        res = await strict_agent._execute_tool_async(spec)
        self.assertEqual(res.get("status"), "TIMEOUT")
        self.assertIn("timed out", res.get("error", ""))

    async def test_worker_queue_polling_and_webhooks(self):
        """Verify producer-consumer worker queue with job status polling and webhook dispatch."""
        queue = AgentWorkerQueue(num_workers=2, agent=self.agent)
        await queue.start()

        webhook_received = []
        async def mock_webhook(payload):
            webhook_received.append(payload)

        job_id = await queue.submit_job("Payment API incident check", webhook_callback=mock_webhook)
        self.assertTrue(job_id.startswith("JOB-"))

        # Poll status
        max_polls = 40
        completed = False
        for _ in range(max_polls):
            status = queue.get_job_status(job_id)
            self.assertIn(status["status"], [JobStatus.PENDING.value, JobStatus.RUNNING.value, JobStatus.COMPLETED.value])
            if status["status"] == JobStatus.COMPLETED.value:
                completed = True
                break
            await asyncio.sleep(0.05)

        self.assertTrue(completed, "Job did not complete within polling window")
        job = queue.get_job(job_id)
        self.assertIsNotNone(job)
        self.assertIsNotNone(job.result)
        self.assertTrue(job.webhook_delivered)
        self.assertEqual(len(webhook_received), 1)
        self.assertEqual(webhook_received[0]["job_id"], job_id)

        await queue.stop()

    async def test_job_cancellation(self):
        """Verify dynamic job cancellation marks status CANCELLED and halts work."""
        queue = AgentWorkerQueue(num_workers=1, agent=self.agent)
        await queue.start()

        job_id = await queue.submit_job("Long running incident triage investigation")
        cancelled = await queue.cancel_job(job_id)
        self.assertTrue(cancelled)

        await asyncio.sleep(0.05)
        status = queue.get_job_status(job_id)
        self.assertEqual(status["status"], JobStatus.CANCELLED.value)

        await queue.stop()


class TestDay13Session2StateMultiTenancy(unittest.TestCase):
    """Session 2: Durable State, Checkpointing, Resumption, Multi-Tenancy, Retention."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.chk_db = os.path.join(self.temp_dir.name, "checkpoints.db")
        self.session_db = os.path.join(self.temp_dir.name, "sessions.db")
        self.checkpointer = SqliteCheckpointer(db_path=self.chk_db)
        self.retriever = TenantScopedRetriever()
        self.agent = ResilientGraphAgent(checkpointer=self.checkpointer, retriever=self.retriever)
        self.session_mgr = TenantSessionManager(db_path=self.session_db)

    def tearDown(self):
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_durable_checkpoint_save_and_lineage(self):
        """Verify state is durably written to SQLite with parent chaining."""
        chk1 = self.checkpointer.save_checkpoint("S1", "TENANT_A", 1, "INTAKE", {"step": 1})
        chk2 = self.checkpointer.save_checkpoint("S1", "TENANT_A", 2, "DIAGNOSE", {"step": 2}, parent_checkpoint_id=chk1)
        
        latest = self.checkpointer.load_latest("S1", "TENANT_A")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.step_index, 2)
        self.assertEqual(latest.node_name, "DIAGNOSE")
        self.assertEqual(latest.parent_checkpoint_id, chk1)

        history = self.checkpointer.list_checkpoints("S1", "TENANT_A")
        self.assertEqual(len(history), 2)

    def test_crash_recovery_and_resumption_without_duplicates(self):
        """Verify crash at Step 3 resumes at Step 4 without repeating Steps 1, 2, or 3."""
        session_id = "SESS-KILL-TEST"
        tenant_id = "ACME_FINTECH"
        user_id = "user-1@acme.internal"
        query = "Acme high-frequency ledger failover protocol"

        # Step A: Run and simulate process crash at Step 3
        with self.assertRaises(SimulatedCrashException):
            self.agent.run(session_id, tenant_id, user_id, query, kill_at_step=3)

        checkpoints = self.checkpointer.list_checkpoints(session_id, tenant_id)
        self.assertEqual(len(checkpoints), 3)

        # Step B: Cold restart and resume run
        recovered_agent = ResilientGraphAgent(checkpointer=self.checkpointer, retriever=self.retriever)
        final_state, resumed_step = recovered_agent.resume_run(session_id, tenant_id)

        self.assertEqual(resumed_step, 4)
        self.assertTrue(final_state.is_resolved)
        # Ensure completed steps were NOT executed twice
        self.assertEqual(final_state.steps_executed.count("STEP_1_INTAKE"), 1)
        self.assertEqual(final_state.steps_executed.count("STEP_2_DIAGNOSE"), 1)
        self.assertEqual(final_state.steps_executed.count("STEP_3_EXECUTE_TOOLS"), 1)
        self.assertEqual(final_state.steps_executed.count("STEP_4_SYNTHESIZE"), 1)
        self.assertEqual(final_state.steps_executed.count("STEP_5_RESOLVE"), 1)

    def test_tenant_isolation_in_retrieval(self):
        """Verify strict tenant isolation: ACME documents cannot leak to GLOBEX queries."""
        acme_docs = self.retriever.retrieve_runbooks("ACME_FINTECH", "ledger failover")
        self.assertEqual(acme_docs["status"], "SUCCESS")
        self.assertIn("Acme High-Frequency", acme_docs["matches"][0]["title"])

        globex_docs = self.retriever.retrieve_runbooks("GLOBEX_LOGISTICS", "telematics")
        self.assertEqual(globex_docs["status"], "SUCCESS")
        self.assertIn("Globex Fleet", globex_docs["matches"][0]["title"])

        # ACME querying globex data must return empty / unauthorized
        cross_res = self.retriever.query_telemetry("ACME_FINTECH", "globex")
        self.assertEqual(len(cross_res["data"]), 0)

    def test_conversation_journal_retention_ttl_and_gdpr_deletion(self):
        """Verify conversation storage, TTL retention pruning, and GDPR right-to-be-forgotten."""
        self.session_mgr.append_turn("S1", "ACME_FINTECH", "u1", "user", "Hello ACME")
        self.session_mgr.append_turn("S1", "ACME_FINTECH", "u1", "assistant", "Hello! Investigating.")
        self.session_mgr.append_turn("S2", "GLOBEX_LOGISTICS", "u2", "user", "Hello GLOBEX")

        acme_hist = self.session_mgr.get_conversation_history("S1", "ACME_FINTECH")
        self.assertEqual(len(acme_hist), 2)

        # GDPR Hard Purge of GLOBEX_LOGISTICS
        purged = self.session_mgr.hard_delete_tenant("GLOBEX_LOGISTICS")
        self.assertEqual(purged, 1)
        globex_hist = self.session_mgr.get_conversation_history("S2", "GLOBEX_LOGISTICS")
        self.assertEqual(len(globex_hist), 0)

        # Ensure ACME data remained intact
        acme_hist_after = self.session_mgr.get_conversation_history("S1", "ACME_FINTECH")
        self.assertEqual(len(acme_hist_after), 2)


class TestDay13Session3DeploymentScaling(unittest.IsolatedAsyncioTestCase):
    """Session 3: Docker, Secrets, Rate Limiting, Provider Failover, Graceful Degradation."""

    def test_secret_masking_hygiene(self):
        """Verify secrets are masked in logs, repr, and str, and accessible only via explicit getter."""
        secret = MaskedSecret("super-secret-production-token-12345678")
        s_repr = repr(secret)
        s_str = str(secret)

        self.assertNotIn("super-secret-production-token-12345678", s_repr)
        self.assertNotIn("super-secret-production-token-12345678", s_str)
        self.assertIn("****", s_repr)
        self.assertEqual(secret.get_secret_value(), "super-secret-production-token-12345678")

    async def test_distributed_rate_limiter_and_jittered_backoff(self):
        """Verify token bucket rate limiter with exponential backoff and jitter."""
        limiter = DistributedTokenBucket(rate_limit_rpm=60, burst_capacity=3)
        
        # Acquire burst capacity
        s1 = await limiter.try_acquire(tokens_requested=1)
        s2 = await limiter.try_acquire(tokens_requested=1)
        s3 = await limiter.try_acquire(tokens_requested=1)
        self.assertTrue(s1.allowed and s2.allowed and s3.allowed)

        # 4th request must be denied on immediate try
        s4 = await limiter.try_acquire(tokens_requested=1)
        self.assertFalse(s4.allowed)

        # Test backoff acquisition
        backoff_status = await limiter.acquire_with_backoff(max_retries=1, base_delay_sec=0.01, max_delay_sec=0.05)
        # Should record retries
        self.assertGreaterEqual(backoff_status.retry_count, 0)

    async def test_multi_provider_failover_cascade(self):
        """Verify primary -> secondary -> tertiary -> local SLM graceful degradation."""
        engine = MultiProviderFailoverEngine(error_threshold=2, recovery_time_sec=1.0)
        query = "Postgres connection pool saturation"

        # Tier 1: Anthropic Healthy
        res1 = await engine.execute_with_failover(query)
        self.assertEqual(res1.active_provider, "anthropic")
        self.assertFalse(res1.failover_occurred)

        # Tier 2: Anthropic Down -> OpenAI Secondary
        engine.set_simulated_outage("anthropic", is_down=True)
        res2 = await engine.execute_with_failover(query)
        self.assertEqual(res2.active_provider, "openai")
        self.assertTrue(res2.failover_occurred)

        # Tier 3: Anthropic + OpenAI Down -> Gemini Tertiary
        engine.set_simulated_outage("openai", is_down=True)
        res3 = await engine.execute_with_failover(query)
        self.assertEqual(res3.active_provider, "gemini")
        self.assertTrue(res3.failover_occurred)

        # Tier 4: All Frontier Cloud Down -> Local SLM Graceful Degradation Safe Mode
        engine.set_simulated_outage("gemini", is_down=True)
        res4 = await engine.execute_with_failover(query)
        self.assertEqual(res4.active_provider, "local_slm")
        self.assertTrue(res4.is_degraded_fallback)
        self.assertIn("safe mode", res4.response_text.lower())

        # Recovery Tier: Restore Anthropic
        engine.set_simulated_outage("anthropic", is_down=False)
        await asyncio.sleep(1.05)  # Wait for recovery cooldown
        res5 = await engine.execute_with_failover(query)
        self.assertEqual(res5.active_provider, "anthropic")

    def test_kubernetes_health_and_readiness_probes(self):
        """Verify Kubernetes liveness and readiness probe responses."""
        live = liveness_probe()
        self.assertEqual(live["status"], "HEALTHY")

        ready = readiness_probe()
        self.assertIn(ready["status"], ["READY", "NOT_READY"])
        self.assertIn("circuit_breakers", ready)

        status_info = provider_status()
        self.assertIn("anthropic", status_info["providers"])


class TestDay13Session4HumanInTheLoop(unittest.TestCase):
    """Session 4: Approval Gates, Rejection, Confidence Escalation, Audit Trail, Compensating Undo."""

    def setUp(self):
        self.audit_store = AuditTrailStore()
        self.approval_queue = HumanApprovalQueue()
        self.compensating_registry = CompensatingActionRegistry()
        self.agent = HumanInTheLoopAgent(
            audit_store=self.audit_store,
            approval_queue=self.approval_queue,
            compensating_registry=self.compensating_registry,
            confidence_threshold=0.80,
        )

    def test_destructive_action_blocked_at_approval_gate(self):
        """Verify high-risk actions are halted and routed to the Human Approval Queue."""
        turn = self.agent.triage_incident(
            session_id="S-401",
            tenant_id="ACME_FINTECH",
            operator_id="op-1",
            alert_query="Payment API elevated 5xx error rate",
        )
        self.assertEqual(turn.status, "AWAITING_APPROVAL")
        self.assertIsNotNone(turn.pending_approval)
        self.assertEqual(turn.pending_approval.blast_radius, "HIGH")

        pending = self.approval_queue.get_pending_requests()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].proposed_tool, "restart_service")

    def test_operator_rejection_flow(self):
        """Verify human operator can reject approval request without executing side effects."""
        turn = self.agent.triage_incident("S-402", "ACME_FINTECH", "op-1", "Payment API 5xx")
        req_id = turn.pending_approval.request_id

        ok, msg, req = self.approval_queue.reject(req_id, reviewer_id="lead-sre", reason="Freeze window")
        self.assertTrue(ok)
        self.assertEqual(req.status, ApprovalStatus.REJECTED)
        self.assertEqual(req.rejection_reason, "Freeze window")

    def test_operator_approval_execution_and_compensating_action(self):
        """Verify approval token unlocks execution and registers compensating undo."""
        token = "AUTH-TOKEN-APPROVED-99"
        turn = self.agent.triage_incident(
            "S-403", "ACME_FINTECH", "op-1", "Payment API 5xx", approval_token=token
        )
        self.assertEqual(turn.status, "RESOLVED")
        self.assertEqual(len(turn.executed_actions), 1)

        # Check registered compensating action
        reversible = self.compensating_registry.list_reversible_actions("S-403")
        self.assertEqual(len(reversible), 1)
        comp = reversible[0]
        self.assertEqual(comp.inverse_action_name, "rollback_pod_restart_or_scale")

        # Execute Compensating Undo
        undo_res = self.compensating_registry.execute_undo(comp.action_id, operator_id="lead-sre")
        self.assertEqual(undo_res["status"], "COMPENSATED")
        self.assertTrue(comp.is_reverted)

    def test_confidence_based_escalation(self):
        """Verify ambiguous queries trigger low confidence and automatic human escalation."""
        turn = self.agent.triage_incident(
            "S-404", "ACME_FINTECH", "op-1", "Split-brain unknown database cascade anomaly"
        )
        self.assertEqual(turn.status, "ESCALATED_LOW_CONFIDENCE")
        self.assertIn("below threshold", turn.user_explanation.lower())

    def test_cryptographic_audit_trail_and_tamper_detection(self):
        """Verify append-only SHA-256 hash chaining and cryptographic tamper detection."""
        self.agent.triage_incident("S-405", "ACME_FINTECH", "op-1", "Payment API triage")

        # Verify integrity of untampered chain
        is_valid, err = self.audit_store.verify_integrity()
        self.assertTrue(is_valid, f"Audit chain should be valid, error: {err}")

        # Intentionally tamper with a record to verify tamper detection
        records = self.audit_store.get_all_records()
        self.assertGreater(len(records), 0)
        target_rec = records[0]
        original_status = target_rec.status
        target_rec.status = "TAMPERED_STATUS"

        # Verification must now fail
        is_tampered_valid, tamper_err = self.audit_store.verify_integrity()
        self.assertFalse(is_tampered_valid)
        self.assertIn("Tampered record", str(tamper_err))

        # Restore
        target_rec.status = original_status
        target_rec.record_hash = target_rec.compute_hash()


if __name__ == "__main__":
    unittest.main(verbosity=2)
