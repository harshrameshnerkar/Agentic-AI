"""
Unit and Integration Tests for Day 17 Session 3: First Real Iteration.
Verifies incremental improvements, intent router accuracy, latency reduction, and scorecard persistence.
"""

import os
import sys
import json
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from first_iteration_engine import (
    IntentRouter,
    HybridRunbookRetriever,
    EphemeralClusterInspector,
    IterativeScorer,
    run_and_save_iterations
)


class TestFirstIteration(unittest.TestCase):

    def setUp(self):
        self.eval_path = os.path.join(CURRENT_DIR, "eval_dataset.json")
        self.runbooks_path = os.path.join(CURRENT_DIR, "static_runbooks.json")
        with open(self.eval_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)

    def test_intent_router_classification(self):
        """Tests that the intent router correctly distinguishes static vs dynamic queries."""
        router = IntentRouter()
        
        static_query = "What is the standard procedure to rotate the production Vault root token?"
        self.assertEqual(router.classify_intent(static_query), "STATIC_POLICY")

        dynamic_query = "CRITICAL: auth-service pod is crashing with CrashLoopBackOff."
        self.assertEqual(router.classify_intent(dynamic_query), "EPHEMERAL_INCIDENT")

    def test_incremental_iteration_progression(self):
        """Verifies that each step matches the scientific hypotheses and deltas."""
        scorer = IterativeScorer(self.eval_path, self.runbooks_path)
        scorecard = scorer.run_all_iterations()

        s0 = scorecard["Step 0: Baseline (Vanilla RAG)"]
        s1 = scorecard["Step 1: +Hybrid Retrieval (RRF)"]
        s2 = scorecard["Step 2: +Cluster Telemetry Tool"]
        s3 = scorecard["Step 3: +Conditional Routing"]

        # Step 0 baseline: 30% pass rate
        self.assertEqual(s0["overall_pass_rate_pct"], 30.0)
        self.assertEqual(s0["ephemeral_pass_rate_pct"], 0.0)

        # Step 1: Same pass rate as Step 0 because retrieval can't invent cluster telemetry
        self.assertEqual(s1["overall_pass_rate_pct"], 30.0)
        self.assertEqual(s1["ephemeral_pass_rate_pct"], 0.0)

        # Step 2: Telemetry tool creates massive jump to 100%
        self.assertEqual(s2["overall_pass_rate_pct"], 100.0)
        self.assertEqual(s2["ephemeral_pass_rate_pct"], 100.0)

        # Step 3: Maintains 100% pass rate while reducing latency vs Step 2
        self.assertEqual(s3["overall_pass_rate_pct"], 100.0)
        self.assertLess(s3["avg_latency_ms"], s2["avg_latency_ms"])
        self.assertLess(s3["avg_cost_usd"], s2["avg_cost_usd"])

    def test_scorecard_file_generation(self):
        """Verifies that run_and_save_iterations generates ITERATION_SCORECARD.json correctly."""
        scores = run_and_save_iterations(CURRENT_DIR)
        score_file = os.path.join(CURRENT_DIR, "ITERATION_SCORECARD.json")
        self.assertTrue(os.path.exists(score_file))

        with open(score_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("Step 3: +Conditional Routing", data)
        self.assertEqual(data["Step 3: +Conditional Routing"]["overall_pass_rate_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
