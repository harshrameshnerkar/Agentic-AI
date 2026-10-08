"""
Unit and Integration Tests for Day 17 Session 2: Simplest Thing That Works.
Verifies evaluation dataset integrity, baseline runner accuracy, scoring logic, and recorded scores.
"""

import os
import sys
import json
import unittest

# Ensure current session directory is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from baseline_runner import (
    SimpleRunbookRetriever,
    BaselineArchitectures,
    BaselineEvaluator,
    run_and_save_baselines
)


class TestBaselineEvaluation(unittest.TestCase):

    def setUp(self):
        self.eval_path = os.path.join(CURRENT_DIR, "eval_dataset.json")
        self.runbooks_path = os.path.join(CURRENT_DIR, "static_runbooks.json")

    def test_eval_dataset_integrity(self):
        """Verifies that the golden dataset has exactly 20 cases with valid schema."""
        self.assertTrue(os.path.exists(self.eval_path), "eval_dataset.json must exist")
        with open(self.eval_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data), 20, "Evaluation dataset must contain exactly 20 cases")

        categories = {"static_runbook": 0, "ephemeral_cluster": 0}
        for item in data:
            self.assertIn("incident_id", item)
            self.assertIn("query", item)
            self.assertIn("category", item)
            self.assertIn("ground_truth_root_cause", item)
            self.assertIn("ground_truth_action", item)
            self.assertIn("key_indicators", item)
            self.assertGreater(len(item["key_indicators"]), 0)
            categories[item["category"]] += 1

        self.assertEqual(categories["static_runbook"], 6, "Expected 6 static runbook cases")
        self.assertEqual(categories["ephemeral_cluster"], 14, "Expected 14 ephemeral cluster cases")

    def test_retriever_functionality(self):
        """Tests that the simple retriever correctly finds runbooks for target terms."""
        retriever = SimpleRunbookRetriever(self.runbooks_path)
        doc, score = retriever.retrieve_single("How to rotate Vault root token?")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["service"], "vault-infra")
        self.assertGreater(score, 0.2)

        # Test unmatched query
        doc_none, score_none = retriever.retrieve_single("unrelated quantum computing gibberish")
        self.assertIsNone(doc_none)
        self.assertEqual(score_none, 0.0)

    def test_baseline_evaluator_runs_and_scores(self):
        """Executes full baseline evaluation and verifies baseline pass rates and ceilings."""
        evaluator = BaselineEvaluator(self.eval_path, self.runbooks_path)
        scorecard = evaluator.evaluate_all()

        p = scorecard["plain_summary"]
        r = scorecard["rag_summary"]

        # Plain prompt must score 0%
        self.assertEqual(p["overall_pass_rate_pct"], 0.0)
        self.assertEqual(p["generic_guess_rate_pct"], 100.0)

        # Single RAG must pass all 6 static runbooks (100%) and fail ephemeral incidents (0%)
        self.assertEqual(r["static_runbook_pass_rate_pct"], 100.0)
        self.assertEqual(r["ephemeral_cluster_pass_rate_pct"], 0.0)
        self.assertEqual(r["overall_pass_rate_pct"], 30.0)

        # Latency and cost must satisfy enterprise ceilings
        self.assertLess(r["avg_latency_ms"], 1000.0)
        self.assertLess(r["avg_cost_usd"], 0.001)

    def test_run_and_save_baselines_artifact(self):
        """Verifies that run_and_save_baselines creates BASELINE_SCORES.json correctly."""
        scores = run_and_save_baselines(CURRENT_DIR)
        scores_file = os.path.join(CURRENT_DIR, "BASELINE_SCORES.json")
        self.assertTrue(os.path.exists(scores_file), "BASELINE_SCORES.json must be written")

        with open(scores_file, "r", encoding="utf-8") as f:
            saved = json.load(f)

        self.assertEqual(saved["rag_summary"]["overall_pass_rate_pct"], 30.0)
        self.assertEqual(saved["plain_summary"]["overall_pass_rate_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
