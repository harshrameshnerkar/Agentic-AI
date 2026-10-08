"""Day 16 - Session 1: Workflow Simulator & Business ROI Modeling.

Compares the human baseline incident triage workflow (As-Is) against the
autonomous Agentic AI copilot workflow (To-Be) using empirical statistical
modeling and Monte Carlo simulation.
"""

from dataclasses import dataclass, field
import json
import random
from typing import Any, Dict, List


@dataclass
class WorkflowStage:
    """Represents a discrete stage in an incident triage workflow."""

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
    """Result of a single incident triage simulation run."""

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
    """Analytical model comparing manual human incident response against Agentic AI."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.stages: List[WorkflowStage] = [
            WorkflowStage(
                name="1. Alert Ingestion & MFA Auth",
                description="Wakeup, VPN connection, Okta multi-factor authentication",
                mean_human_minutes=7.5,
                std_human_minutes=2.0,
                mean_agent_seconds=1.2,
                std_agent_seconds=0.3,
                human_error_rate=0.02,
                agent_error_rate=0.00,
            ),
            WorkflowStage(
                name="2. Metrics Inspection",
                description="Datadog/Grafana CPU, memory, and p99 latency curve analysis",
                mean_human_minutes=12.0,
                std_human_minutes=3.5,
                mean_agent_seconds=8.5,
                std_agent_seconds=1.5,
                human_error_rate=0.04,
                agent_error_rate=0.00,
            ),
            WorkflowStage(
                name="3. Log Harvesting & Stack Trace Grep",
                description="Splunk/Coralogix query construction across 50k logs/min",
                mean_human_minutes=20.0,
                std_human_minutes=5.0,
                mean_agent_seconds=14.0,
                std_agent_seconds=2.5,
                human_error_rate=0.05,
                agent_error_rate=0.00,
            ),
            WorkflowStage(
                name="4. Deployment & Git Correlation",
                description="ArgoCD/GitHub commit log inspection for recent canary releases",
                mean_human_minutes=11.0,
                std_human_minutes=2.5,
                mean_agent_seconds=4.5,
                std_agent_seconds=0.8,
                human_error_rate=0.03,
                agent_error_rate=0.00,
            ),
            WorkflowStage(
                name="5. Runbook Lookup & Root Cause Synthesis",
                description="Confluence search, SOP validation, hypothesis formulation",
                mean_human_minutes=15.0,
                std_human_minutes=4.0,
                mean_agent_seconds=12.0,
                std_agent_seconds=2.0,
                human_error_rate=0.06,
                agent_error_rate=0.002,
            ),
            WorkflowStage(
                name="6. Remediation Execution",
                description="Terminal kubectl command or HITL cryptographic token sign-off",
                mean_human_minutes=8.0,
                std_human_minutes=2.5,
                mean_agent_seconds=3.0,
                std_agent_seconds=0.5,
                human_error_rate=0.04,
                agent_error_rate=0.00,
            ),
            WorkflowStage(
                name="7. Verification & Post-Mortem Logging",
                description="10-minute traffic recovery monitoring and Jira ticket creation",
                mean_human_minutes=12.5,
                std_human_minutes=2.0,
                mean_agent_seconds=15.0,
                std_agent_seconds=2.0,
                human_error_rate=0.02,
                agent_error_rate=0.00,
            ),
        ]

    def get_baseline_summary(self) -> Dict[str, Any]:
        """Calculates nominal theoretical baseline timings across stages."""
        total_human_mins = sum(s.mean_human_minutes for s in self.stages)
        total_agent_secs = sum(s.mean_agent_seconds for s in self.stages)
        cumulative_human_error = 1.0 - (
            (1.0 - s.human_error_rate) for s in self.stages
        )  # approx compound
        # More exact compound probability:
        no_error_prob = 1.0
        for s in self.stages:
            no_error_prob *= 1.0 - s.human_error_rate
        compound_human_error = 1.0 - no_error_prob

        return {
            "total_human_minutes": round(total_human_mins, 1),
            "total_agent_seconds": round(total_agent_secs, 1),
            "speedup_factor": round((total_human_mins * 60) / total_agent_secs, 1),
            "compound_human_error_probability": round(
                compound_human_error * 100, 2
            ),
        }

    def simulate_single_incident(
        self, incident_idx: int, severity: str = "Sev-2"
    ) -> IncidentSimulationResult:
        """Simulates one incident through the 7-stage workflow."""
        human_time_mins = 0.0
        agent_time_secs = 0.0
        human_error = False
        agent_error = False

        for stage in self.stages:
            # Sample human time (clamped at positive values)
            h_time = max(
                1.0, random.gauss(stage.mean_human_minutes, stage.std_human_minutes)
            )
            human_time_mins += h_time

            # Check human error probability
            if random.random() < stage.human_error_rate:
                human_error = True

            # Sample agent time
            a_time = max(
                0.5, random.gauss(stage.mean_agent_seconds, stage.std_agent_seconds)
            )
            agent_time_secs += a_time

            # Check agent error probability
            if random.random() < stage.agent_error_rate:
                agent_error = True

        # Compute downtime and SLA impact
        # If human error occurs, penalty multiplier of 1.7x downtime due to misdiagnosis/fat-finger
        human_downtime = (
            human_time_mins * 1.7 if human_error else human_time_mins
        )
        agent_downtime = (agent_time_secs / 60.0) + (
            1.5 if severity == "Sev-1" else 0.5
        )  # include 30-90s human review for HITL

        # Financial penalty model:
        # Realistic enterprise SLA: Sev-1 breaches incur $250/min after 15 min grace (cap $20k).
        # Sev-2 breaches incur $100/min after 30 min grace (cap $7.5k).
        human_sla_penalty = 0.0
        agent_sla_penalty = 0.0

        if severity == "Sev-1":
            if human_downtime > 15.0:
                human_sla_penalty = min(20000.0, (human_downtime - 15.0) * 250.0)
            if agent_downtime > 15.0:
                agent_sla_penalty = min(20000.0, (agent_downtime - 15.0) * 250.0)
        elif severity == "Sev-2":
            if human_downtime > 30.0:
                human_sla_penalty = min(7500.0, (human_downtime - 30.0) * 100.0)
            if agent_downtime > 30.0:
                agent_sla_penalty = min(7500.0, (agent_downtime - 30.0) * 100.0)

        return IncidentSimulationResult(
            incident_id=f"INC-{incident_idx:04d}",
            severity=severity,
            human_triage_minutes=round(human_time_mins, 2),
            agent_triage_seconds=round(agent_time_secs, 2),
            human_error_occurred=human_error,
            agent_error_occurred=agent_error,
            human_downtime_minutes=round(human_downtime, 2),
            agent_downtime_minutes=round(agent_downtime, 2),
            human_sla_penalty_usd=round(human_sla_penalty, 2),
            agent_sla_penalty_usd=round(agent_sla_penalty, 2),
        )

    def run_monte_carlo(
        self, num_incidents: int = 210
    ) -> Dict[str, Any]:
        """Runs a Monte Carlo simulation across typical monthly incident volume."""
        results: List[IncidentSimulationResult] = []
        severities = ["Sev-1"] * 25 + ["Sev-2"] * 85 + ["Sev-3"] * 100

        for i in range(1, num_incidents + 1):
            sev = (
                random.choice(severities)
                if i > len(severities)
                else severities[i - 1]
            )
            results.append(self.simulate_single_incident(i, severity=sev))

        # Metrics aggregation
        avg_human_triage = sum(r.human_triage_minutes for r in results) / len(
            results
        )
        avg_agent_triage = sum(r.agent_triage_seconds for r in results) / len(
            results
        )
        avg_human_downtime = sum(r.human_downtime_minutes for r in results) / len(
            results
        )
        avg_agent_downtime = sum(r.agent_downtime_minutes for r in results) / len(
            results
        )

        total_human_errors = sum(1 for r in results if r.human_error_occurred)
        total_agent_errors = sum(1 for r in results if r.agent_error_occurred)

        total_human_penalties = sum(r.human_sla_penalty_usd for r in results)
        total_agent_penalties = sum(r.agent_sla_penalty_usd for r in results)

        # Engineering toil hours saved
        # 14 SREs, $95/hour blended compensation
        human_toil_hours = sum(r.human_triage_minutes for r in results) / 60.0
        agent_toil_hours = sum(r.agent_triage_seconds for r in results) / 3600.0
        hours_saved_monthly = human_toil_hours - agent_toil_hours
        monthly_salary_saved = hours_saved_monthly * 95.0

        monthly_total_savings = (
            total_human_penalties - total_agent_penalties
        ) + monthly_salary_saved
        annualized_savings = monthly_total_savings * 12.0

        return {
            "simulation_meta": {
                "total_incidents_simulated": num_incidents,
                "team_size_sres": 14,
                "blended_hourly_rate_usd": 95.0,
            },
            "latency_metrics": {
                "mean_human_triage_minutes": round(avg_human_triage, 1),
                "mean_agent_triage_seconds": round(avg_agent_triage, 1),
                "mean_human_downtime_minutes": round(avg_human_downtime, 1),
                "mean_agent_downtime_minutes": round(avg_agent_downtime, 1),
                "speedup_factor": round(
                    (avg_human_triage * 60) / avg_agent_triage, 1
                ),
            },
            "reliability_metrics": {
                "human_error_count": total_human_errors,
                "human_error_rate_pct": round(
                    (total_human_errors / num_incidents) * 100, 2
                ),
                "agent_error_count": total_agent_errors,
                "agent_error_rate_pct": round(
                    (total_agent_errors / num_incidents) * 100, 2
                ),
            },
            "financial_roi_monthly": {
                "human_toil_hours": round(human_toil_hours, 1),
                "agent_toil_hours": round(agent_toil_hours, 1),
                "toil_hours_saved": round(hours_saved_monthly, 1),
                "salary_savings_usd": round(monthly_salary_saved, 2),
                "human_sla_penalties_usd": round(total_human_penalties, 2),
                "agent_sla_penalties_usd": round(total_agent_penalties, 2),
                "net_monthly_savings_usd": round(monthly_total_savings, 2),
                "annualized_projected_savings_usd": round(
                    annualized_savings, 2
                ),
            },
        }


if __name__ == "__main__":
    modeler = WorkflowModeler()
    summary = modeler.run_monte_carlo(num_incidents=210)
    print(json.dumps(summary, indent=2))
