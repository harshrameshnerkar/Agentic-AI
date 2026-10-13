"""
Day 16 - Session 01: Stakeholder Discovery & Workflow Replacement
Simulates manual SRE triage workflow vs autonomous AI agent workflow.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .workflow_simulator import WorkflowModeler
except ImportError:
    from workflow_simulator import WorkflowModeler


def run_simulation(export_path: Optional[str] = None, num_incidents: int = 210) -> Dict[str, Any]:
    modeler = WorkflowModeler()
    summary = modeler.run_monte_carlo(num_incidents=num_incidents)
    if export_path:
        Path(export_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    print("Day 16 Session 01: SRE Incident Triage Workflow Simulation\n")
    modeler = WorkflowModeler()
    cmp_summary = modeler.simulate_workflow_comparison(num_incidents=10)

    print("--- Workflow Simulation Results (10 incidents) ---")
    print(f"Manual Mean Triage Time:    {cmp_summary['manual_mean_minutes']:.1f} minutes")
    print(f"Autonomous Mean Triage:     {cmp_summary['autonomous_mean_minutes']:.1f} minutes")
    print(f"Latency Reduction:          {cmp_summary['latency_reduction_pct']:.1f}% faster")
    print(f"Human Fatigued Error Rate:  {cmp_summary['manual_error_rate_pct']:.1f}%")
    print(f"Autonomous Guarded Errors:  {cmp_summary['autonomous_error_rate_pct']:.1f}%")
    print("\nDiscovery Conclusion: Autonomous agent reduces triage latency by > 80% while guarding against fatigue errors.")


if __name__ == "__main__":
    main()
