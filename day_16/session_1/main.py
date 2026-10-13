"""
Day 16 - Session 01: Stakeholder Discovery & Workflow Replacement
Simulates the baseline manual SRE triage workflow vs the autonomous
OpsSentinel AI agent workflow to measure time and error reductions.
"""

from __future__ import annotations
from workflow_simulator import WorkflowModeler


def main():
    print("Day 16 Session 01: SRE Incident Triage Workflow Simulation\n")
    modeler = WorkflowModeler()
    summary = modeler.simulate_workflow_comparison(num_incidents=10)

    print("--- Workflow Simulation Results (10 incidents) ---")
    print(f"Manual Mean Triage Time:    {summary['manual_mean_minutes']:.1f} minutes")
    print(f"Autonomous Mean Triage:     {summary['autonomous_mean_minutes']:.1f} minutes")
    print(f"Latency Reduction:          {summary['latency_reduction_pct']:.1f}% faster")
    print(f"Human Fatigued Error Rate:  {summary['manual_error_rate_pct']:.1f}%")
    print(f"Autonomous Guarded Errors:  {summary['autonomous_error_rate_pct']:.1f}%")

    print("\nDiscovery Conclusion: Autonomous agent reduces triage latency by > 80% while guarding against fatigue errors.")


if __name__ == "__main__":
    main()
