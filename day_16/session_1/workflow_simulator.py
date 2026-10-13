"""Day 16 - Session 1: Workflow Simulator & ROI Modeling.

Compares manual incident triage vs autonomous agent triage.
"""

from dataclasses import dataclass
import json
import random
from typing import Any, Dict, List


@dataclass
class WorkflowStage:
    name: str
    description: str
    mean_human_minutes: float
    std_human_minutes: float
    mean_agent_seconds: float
    std_agent_seconds: float
    human_error_rate: float
    agent_error_rate: float


@dataclass
class IncidentSimulationResult:
    incident_id: str
    severity: str
    human_triage_minutes: float
    agent_triage_seconds: float
    human_error_occurred: bool
    agent_error_occurred: bool
    human_downtime_minutes: float
    agent_downtime_minutes: float
    human_sla_penalty_usd: float
    agent_sla_penalty_usd: float


class WorkflowModeler:
    """Models triage latency, error rates, and costs for manual vs agent workflows."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.stages = [
            WorkflowStage("1. Alert Ingestion & MFA Auth", "Alert receipt and login", 7.5, 2.0, 1.2, 0.3, 0.02, 0.0),
            WorkflowStage("2. Metrics Inspection", "Dashboard metrics analysis", 12.0, 3.5, 8.5, 1.5, 0.04, 0.0),
            WorkflowStage("3. Log Harvesting & Stack Trace Grep", "Log query and triage", 20.0, 5.0, 14.0, 2.5, 0.05, 0.0),
            WorkflowStage("4. Deployment & Git Correlation", "Recent deploy checks", 11.0, 2.5, 4.5, 0.8, 0.03, 0.0),
            WorkflowStage("5. Runbook Lookup & Root Cause Synthesis", "Runbook matching", 15.0, 4.0, 12.0, 2.0, 0.06, 0.002),
            WorkflowStage("6. Remediation Execution", "Action execution", 8.0, 2.5, 3.0, 0.5, 0.04, 0.0),
            WorkflowStage("7. Verification & Post-Mortem Logging", "Verify fix and ticket log", 12.5, 2.0, 15.0, 2.0, 0.02, 0.0),
        ]

    def simulate_single_incident(self, incident_idx: int, severity: str = "Sev-2") -> IncidentSimulationResult:
        h_mins = 0.0
        a_secs = 0.0
        h_err = False
        a_err = False

        for s in self.stages:
            h_mins += max(1.0, random.gauss(s.mean_human_minutes, s.std_human_minutes))
            if random.random() < s.human_error_rate:
                h_err = True
            a_secs += max(0.5, random.gauss(s.mean_agent_seconds, s.std_agent_seconds))
            if random.random() < s.agent_error_rate:
                a_err = True

        h_down = h_mins * 1.7 if h_err else h_mins
        a_down = (a_secs / 60.0) + (1.5 if severity == "Sev-1" else 0.5)

        h_penalty = 0.0
        a_penalty = 0.0
        if severity == "Sev-1":
            if h_down > 15:
                h_penalty = min(20000.0, (h_down - 15) * 250.0)
            if a_down > 15:
                a_penalty = min(20000.0, (a_down - 15) * 250.0)
        elif severity == "Sev-2":
            if h_down > 30:
                h_penalty = min(7500.0, (h_down - 30) * 100.0)
            if a_down > 30:
                a_penalty = min(7500.0, (a_down - 30) * 100.0)

        return IncidentSimulationResult(
            incident_id=f"INC-{incident_idx:04d}",
            severity=severity,
            human_triage_minutes=round(h_mins, 2),
            agent_triage_seconds=round(a_secs, 2),
            human_error_occurred=h_err,
            agent_error_occurred=a_err,
            human_downtime_minutes=round(h_down, 2),
            agent_downtime_minutes=round(a_down, 2),
            human_sla_penalty_usd=round(h_penalty, 2),
            agent_sla_penalty_usd=round(a_penalty, 2),
        )

    def run_monte_carlo(self, num_incidents: int = 210) -> Dict[str, Any]:
        severities = ["Sev-1"] * 25 + ["Sev-2"] * 85 + ["Sev-3"] * 100
        results = [
            self.simulate_single_incident(i, severities[i - 1] if i <= len(severities) else random.choice(severities))
            for i in range(1, num_incidents + 1)
        ]

        avg_h_time = sum(r.human_triage_minutes for r in results) / len(results)
        avg_a_secs = sum(r.agent_triage_seconds for r in results) / len(results)
        avg_h_down = sum(r.human_downtime_minutes for r in results) / len(results)
        avg_a_down = sum(r.agent_downtime_minutes for r in results) / len(results)
        h_err_cnt = sum(1 for r in results if r.human_error_occurred)
        a_err_cnt = sum(1 for r in results if r.agent_error_occurred)
        h_penalties = sum(r.human_sla_penalty_usd for r in results)
        a_penalties = sum(r.agent_sla_penalty_usd for r in results)

        h_hours = sum(r.human_triage_minutes for r in results) / 60.0
        a_hours = sum(r.agent_triage_seconds for r in results) / 3600.0
        saved_hours = h_hours - a_hours
        monthly_savings = (h_penalties - a_penalties) + (saved_hours * 95.0)

        return {
            "simulation_meta": {"total_incidents_simulated": num_incidents, "team_size_sres": 14},
            "latency_metrics": {
                "mean_human_triage_minutes": round(avg_h_time, 1),
                "mean_agent_triage_seconds": round(avg_a_secs, 1),
                "mean_human_downtime_minutes": round(avg_h_down, 1),
                "mean_agent_downtime_minutes": round(avg_a_down, 1),
                "speedup_factor": round((avg_h_time * 60) / avg_a_secs, 1),
            },
            "reliability_metrics": {
                "human_error_count": h_err_cnt,
                "human_error_rate_pct": round((h_err_cnt / num_incidents) * 100, 2),
                "agent_error_count": a_err_cnt,
                "agent_error_rate_pct": round((a_err_cnt / num_incidents) * 100, 2),
            },
            "financial_roi_monthly": {
                "human_toil_hours": round(h_hours, 1),
                "agent_toil_hours": round(a_hours, 1),
                "toil_hours_saved": round(saved_hours, 1),
                "net_monthly_savings_usd": round(monthly_savings, 2),
                "annualized_projected_savings_usd": round(monthly_savings * 12, 2),
            },
        }

    def simulate_workflow_comparison(self, num_incidents: int = 10) -> Dict[str, float]:
        mc = self.run_monte_carlo(num_incidents)
        h_mins = mc["latency_metrics"]["mean_human_triage_minutes"]
        a_mins = mc["latency_metrics"]["mean_agent_triage_seconds"] / 60.0
        return {
            "manual_mean_minutes": h_mins,
            "autonomous_mean_minutes": a_mins,
            "latency_reduction_pct": ((h_mins - a_mins) / h_mins) * 100,
            "manual_error_rate_pct": mc["reliability_metrics"]["human_error_rate_pct"],
            "autonomous_error_rate_pct": mc["reliability_metrics"]["agent_error_rate_pct"],
        }


if __name__ == "__main__":
    modeler = WorkflowModeler()
    print(json.dumps(modeler.run_monte_carlo(50), indent=2))
