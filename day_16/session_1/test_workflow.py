"""Day 16 - Session 1: Unit & Integration Tests for Workflow Scoping Suite."""

import os
import sys
import unittest

try:
    from .workflow_simulator import WorkflowModeler, IncidentSimulationResult
    from .main import run_simulation
except ImportError:
    from workflow_simulator import WorkflowModeler, IncidentSimulationResult
    from main import run_simulation


class TestDay16Session1WorkflowScoping(unittest.TestCase):
    """Test suite validating Day 16 Session 1 stakeholder scoping and workflow simulation."""

    def setUp(self):
        self.modeler = WorkflowModeler(seed=42)
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def test_workflow_stages_integrity(self):
        """Verifies that all 7 stages of the triage workflow are correctly modeled."""
        self.assertEqual(len(self.modeler.stages), 7)
        stage_names = [s.name for s in self.modeler.stages]
        self.assertIn("1. Alert Ingestion & MFA Auth", stage_names[0])
        self.assertIn("2. Metrics Inspection", stage_names[1])
        self.assertIn("3. Log Harvesting & Stack Trace Grep", stage_names[2])
        self.assertIn("4. Deployment & Git Correlation", stage_names[3])
        self.assertIn("5. Runbook Lookup & Root Cause Synthesis", stage_names[4])
        self.assertIn("6. Remediation Execution", stage_names[5])
        self.assertIn("7. Verification & Post-Mortem Logging", stage_names[6])

        for stage in self.modeler.stages:
            self.assertGreater(stage.mean_human_minutes, 0)
            self.assertGreater(stage.mean_agent_seconds, 0)
            self.assertGreaterEqual(stage.human_error_rate, 0.0)
            self.assertLessEqual(stage.human_error_rate, 1.0)
            self.assertGreaterEqual(stage.agent_error_rate, 0.0)
            self.assertLessEqual(stage.agent_error_rate, 1.0)

    def test_single_incident_simulation(self):
        """Verifies that single incident execution generates valid latency and SLA data."""
        res = self.modeler.simulate_single_incident(1, severity="Sev-1")
        self.assertIsInstance(res, IncidentSimulationResult)
        self.assertEqual(res.incident_id, "INC-0001")
        self.assertEqual(res.severity, "Sev-1")
        self.assertGreater(res.human_triage_minutes, 0)
        self.assertGreater(res.agent_triage_seconds, 0)
        self.assertGreater(res.human_downtime_minutes, res.agent_downtime_minutes)
        self.assertGreaterEqual(res.human_sla_penalty_usd, 0.0)
        self.assertGreaterEqual(res.agent_sla_penalty_usd, 0.0)

    def test_monte_carlo_aggregation(self):
        """Verifies Monte Carlo statistical aggregation across 210 incidents."""
        summary = self.modeler.run_monte_carlo(num_incidents=210)
        self.assertIn("latency_metrics", summary)
        self.assertIn("reliability_metrics", summary)
        self.assertIn("financial_roi_monthly", summary)

        lat = summary["latency_metrics"]
        self.assertGreater(lat["speedup_factor"], 50.0)
        self.assertLess(lat["mean_agent_triage_seconds"], 120.0)  # Sub-2 min SLA

        rel = summary["reliability_metrics"]
        self.assertGreater(rel["human_error_rate_pct"], 10.0)
        self.assertLess(rel["agent_error_rate_pct"], 1.0)

        roi = summary["financial_roi_monthly"]
        self.assertGreater(roi["toil_hours_saved"], 200.0)
        self.assertGreater(roi["net_monthly_savings_usd"], 100000.0)

    def test_stakeholder_problem_statement_artifacts(self):
        """Verifies that all stakeholder discovery markdown artifacts exist and are well-formed."""
        problem_stmt = os.path.join(self.base_dir, "STAKEHOLDER_PROBLEM_STATEMENT.md")
        workflow_doc = os.path.join(self.base_dir, "WORKFLOW_REPLACEMENT_ANALYSIS.md")
        transcript_doc = os.path.join(self.base_dir, "INTERVIEW_TRANSCRIPT.md")

        for path in [problem_stmt, workflow_doc, transcript_doc]:
            self.assertTrue(os.path.isfile(path), f"Missing required document: {path}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 500, f"Document too short: {path}")

        # Check key sections in problem statement
        with open(problem_stmt, "r", encoding="utf-8") as f:
            ps_text = f.read()
            self.assertIn("Marcus Vance", ps_text)
            self.assertIn("The Problem Statement", ps_text)

        # Check key sections in workflow replacement document
        with open(workflow_doc, "r", encoding="utf-8") as f:
            wf_text = f.read()
            self.assertIn("What a Human Does Today", wf_text)
            self.assertIn("What Happens When They Get It Wrong", wf_text)

    def test_cli_summary_export(self):
        """Verifies that simulation export produces a valid JSON artifact."""
        export_file = os.path.join(self.base_dir, "test_summary.json")
        try:
            summary = run_simulation(export_path=export_file)
            self.assertTrue(os.path.isfile(export_file))
            self.assertIn("latency_metrics", summary)
        finally:
            if os.path.exists(export_file):
                os.remove(export_file)


if __name__ == "__main__":
    unittest.main()
