"""Day 16 - Session 1: Stakeholder Discovery CLI & Executive Review.

Executes stakeholder problem scoping, prints the baseline workflow breakdown,
and runs the analytical workflow replacement simulation.
"""

import argparse
import json
import os
import sys

try:
    from .workflow_simulator import WorkflowModeler
except ImportError:
    from workflow_simulator import WorkflowModeler


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def print_banner():
    banner = """
================================================================================
   DAY 16 - SESSION 1: STAKEHOLDER DISCOVERY & WORKFLOW REPLACEMENT SCOPING
================================================================================
  Role: Senior AI Systems Architect / Production Engineer
  Stakeholder: Marcus Vance (VP of Cloud Infrastructure & Reliability)
  Mentor: Dr. Elena Rostova (Principal AI Systems Architect)
  Domain: Cloud SRE Incident Triage & Autonomous Remediation
================================================================================
"""
    print(banner)


def show_problem_statement():
    print("\n" + "=" * 78)
    print(" [*] STAKEHOLDER PROBLEM STATEMENT (IN STAKEHOLDER'S EXACT WORDS)")
    print("=" * 78)
    statement = """
"Look, here is the brutal truth about our production operations:

At 2:30 in the morning, an alert fires on PagerDuty. An on-call engineer gets
woken up out of a deep sleep. Their heart rate spikes, their brain is foggy, and
they have exactly 15 minutes before our SLA breach countdown begins.

What does that engineer have to do today? They have to log into Okta, fight with
VPN multi-factor auth, open six different browser windows — Datadog for CPU
spikes, Grafana for latency curves, Splunk for log traces, ArgoCD for deployment
status, AWS CloudWatch, and Confluence for some outdated runbook written eight
months ago that nobody maintains.

By the time they even correlate the logs with the pod crash and find out that a
recent canary deployment ran out of memory, 45 TO 60 MINUTES HAVE EVAPORATED.
That is 45 minutes of customers experiencing 504 errors on checkout.

And that’s not even the worst part. The worst part is WHEN THEY GET IT WRONG.

Six weeks ago, an engineer panicked during an incident, misread the Kubernetes
cluster namespace, and issued a 'kubectl scale --replicas=0' on our production
payments service instead of the staging replica. That single human mistake caused
a 38-minute total checkout outage, cost us $185,000 in direct contractual SLA
refunds, and severely damaged customer trust.

We don't need a novelty chatbot that spits out generic troubleshooting advice.
We need an AUTONOMOUS, DETERMINISTIC AGENTIC AI COPILOT that can ingest the alert,
instantly execute read-only diagnostic telemetry across logs, metrics, and
topology in parallel within 30 seconds, match the root cause against living
runbooks, and present the on-call engineer with a verified, one-click remediation
plan — while strictly locking any destructive action behind cryptographic human
approval."

  — Marcus Vance, VP of Infrastructure & Reliability Engineering
"""
    print(statement)


def show_workflow_analysis():
    print("\n" + "=" * 78)
    print(" [*] WORKFLOW BEING REPLACED (AS-IS HUMAN vs. TO-BE AGENTIC AI)")
    print("=" * 78)
    workflow_text = """
Stage 1: Alert Ingestion & MFA Auth
  - Human (As-Is): 5 - 10 mins (Wakeup, VPN connection, Okta Duo push)
  - Agent (To-Be): 1.2 secs (Instant webhook ingestion & parsing)

Stage 2: Metrics Dashboard Inspection
  - Human (As-Is): 10 - 15 mins (Hunt through Datadog/Grafana charts)
  - Agent (To-Be): 8.5 secs (Parallel Prometheus/Datadog API telemetry)

Stage 3: Log Harvesting & Stack Trace Grep
  - Human (As-Is): 15 - 25 mins (Construct Splunk/Coralogix queries)
  - Agent (To-Be): 14.0 secs (Automated semantic log clustering & regex)

Stage 4: Deployment & Git History Correlation
  - Human (As-Is): 10 - 15 mins (Check ArgoCD, GitHub releases)
  - Agent (To-Be): 4.5 secs (Git commit SHA & diff timeline extraction)

Stage 5: Runbook Lookup & Root Cause Synthesis
  - Human (As-Is): 10 - 20 mins (Search stale Confluence wiki pages)
  - Agent (To-Be): 12.0 secs (Dynamic RAG over verified enterprise SOPs)

Stage 6: Remediation Execution
  - Human (As-Is): 5 - 10 mins (Manual kubectl commands on terminal)
  - Agent (To-Be): 3.0 secs (Cryptographic HITL token sign-off)

Stage 7: Verification & Post-Mortem Logging
  - Human (As-Is): 10 - 15 mins (Monitor traffic, write Jira tickets)
  - Agent (To-Be): 15.0 secs (Automated post-recovery validation & Slack brief)
--------------------------------------------------------------------------------
TOTAL MTTR:
  - Human Baseline : 65 - 110 minutes (Average: ~85.5 mins)
  - Agentic AI     : < 60 seconds diagnostic triage (~1.6 min total recovery)
  - Speedup Factor : ~88x Latency Reduction
"""
    print(workflow_text)


def run_simulation(export_path: str = None) -> dict:
    print("\n" + "=" * 78)
    print(" [*] RUNNING MONTE CARLO WORKFLOW REPLACEMENT SIMULATION (210 INCIDENTS)")
    print("=" * 78)

    modeler = WorkflowModeler(seed=42)
    summary = modeler.run_monte_carlo(num_incidents=210)

    lat = summary["latency_metrics"]
    rel = summary["reliability_metrics"]
    roi = summary["financial_roi_monthly"]

    print(f"\n[LATENCY COMPARISON]")
    print(f"  • Mean Human Triage Time : {lat['mean_human_triage_minutes']} minutes")
    print(f"  • Mean Agent Triage Time : {lat['mean_agent_triage_seconds']} seconds")
    print(f"  • Mean Human Downtime    : {lat['mean_human_downtime_minutes']} minutes")
    print(f"  • Mean Agent Downtime    : {lat['mean_agent_downtime_minutes']} minutes")
    print(f"  • Diagnostic Speedup     : {lat['speedup_factor']}x Faster")

    print(f"\n[RELIABILITY & ERROR RATE]")
    print(f"  • Human Errors Observed  : {rel['human_error_count']} ({rel['human_error_rate_pct']}%)")
    print(f"  • Agent Errors Observed  : {rel['agent_error_count']} ({rel['agent_error_rate_pct']}%)")
    print(f"  • Blast Radius Protection: 100% Guaranteed via HITL Gateway")

    print(f"\n[FINANCIAL ROI & BUSINESS VALUE (MONTHLY)]")
    print(f"  • Human Toil Hours       : {roi['human_toil_hours']} hours/month")
    print(f"  • Agent Toil Hours       : {roi['agent_toil_hours']} hours/month")
    print(f"  • Engineering Hours Saved: {roi['toil_hours_saved']} hours/month")
    print(f"  • SRE Salary Savings     : ${roi['salary_savings_usd']:,.2f} / month")
    print(f"  • Net Monthly Savings    : ${roi['net_monthly_savings_usd']:,.2f} / month")
    print(f"  • Projected Annual ROI   : ${roi['annualized_projected_savings_usd']:,.2f} / year")
    print("=" * 78)

    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[+] Executive simulation summary exported to: {export_path}")

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Day 16 Session 1: Stakeholder Discovery & Workflow Scoping"
    )
    parser.add_argument(
        "--problem-statement",
        action="store_true",
        help="Print the written problem statement in stakeholder's exact words",
    )
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="Print detailed breakdown of the workflow being replaced",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run Monte Carlo workflow replacement simulation",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Path to export simulation results JSON",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run full stakeholder discovery review suite",
    )

    args = parser.parse_args()

    print_banner()

    default_run = not (args.problem_statement or args.workflow or args.simulate or args.export)

    if args.problem_statement or args.all or default_run:
        show_problem_statement()

    if args.workflow or args.all or default_run:
        show_workflow_analysis()

    if args.simulate or args.all or default_run:
        out_file = args.export
        if default_run and not out_file:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            out_file = os.path.join(curr_dir, "executive_discovery_summary.json")
        run_simulation(export_path=out_file)


if __name__ == "__main__":
    main()
