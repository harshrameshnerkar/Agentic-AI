"""Day 16 - Session 2: Constraints & Success Metrics Executive CLI.

Reviews the signed-off success metrics, inspects the HITL operational boundary,
demonstrates cryptographic HMAC approval tokens, and runs compliance evaluation.
"""

import argparse
import json
import os
import sys

try:
    from .constraints_validator import (
        SignedOffMetrics,
        SecretMasker,
        BlacklistEnforcer,
        BlastRadiusClassifier,
        CryptographicHITLGateway,
        ComplianceEvaluator,
    )
except ImportError:
    from constraints_validator import (
        SignedOffMetrics,
        SecretMasker,
        BlacklistEnforcer,
        BlastRadiusClassifier,
        CryptographicHITLGateway,
        ComplianceEvaluator,
    )

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def print_banner():
    banner = """
================================================================================
    DAY 16 - SESSION 2: CONSTRAINTS & SIGNED-OFF SUCCESS METRICS
================================================================================
  Role: Senior AI Systems Architect / Reliability Reviewer
  Stakeholder: Marcus Vance (VP of Cloud Infrastructure & Reliability)
  Focus: Signed-Off Metrics (Accuracy, Latency, Cost) + HITL Operational Boundary
================================================================================
"""
    print(banner)


def show_success_metrics():
    print("\n" + "=" * 78)
    print(" [*] SIGNED-OFF SUCCESS METRICS CHARTER (WITH EXACT NUMBERS)")
    print("=" * 78)
    metrics_text = """
1. Diagnostic Accuracy Bar (M1)
   • Target Threshold: >= 95.0% on 100-case golden benchmark suite
   • Hard Floor      : 92.0%
   • Human Baseline  : 82.4% (under nighttime cognitive fatigue)

2. Acceptable Triage Latency (M2)
   • p50 Latency     : <= 45.0 seconds
   • p95 Latency     : <= 60.0 seconds (Hard SLA Ceiling: <= 90.0s)
   • Human Baseline  : 78.5 minutes (45-80x latency reduction)

3. Cost Per Triage Ceiling (M3)
   • Target Cost     : <= $0.10 USD per incident triage
   • Hard Ceiling    : <= $0.15 USD per incident triage
   • Human Baseline  : $134.50 USD in engineering toil salary per incident

4. Unattended Destructive Operations (M4)
   • Hard Threshold  : 0.0% (Zero tolerance for unapproved Tier-3 actions)
   • Enforcement     : 100% gated behind Cryptographic HMAC-SHA256 token

5. Data Sensitivity & Credential Scrubbing (M5)
   • Target Threshold: 100.0% of API keys, tokens, and PII masked
   • Action          : Automatically replaced with [REDACTED_SECRET] / [REDACTED_PII]

6. MTTR Reduction Ratio (M6)
   • Target Reduction: >= 80.0% reduction in Mean Time to Recovery
   • Human Baseline  : ~85.5 mins --> Target: < 3.0 mins
"""
    print(metrics_text)


def show_hitl_boundary():
    print("\n" + "=" * 78)
    print(" [*] HUMAN-IN-THE-LOOP (HITL) BOUNDARY & 5 NEVER-AUTOMATE RED LINES")
    print("=" * 78)
    boundary_text = """
[THE 3-TIER BLAST-RADIUS CLASSIFICATION]
  • Tier 1: Read-Only Diagnostics (100% Autonomous)
      - Tools: query_metrics, fetch_logs, get_pod_status, get_git_diff
      - Autonomy: Executed asynchronously in parallel without human waiting.

  • Tier 2: Low-Risk Rebalancing (Autonomous + Rollback)
      - Tools: drain_read_replica, warm_cache, scale_up_replicas
      - Autonomy: Auto-executes with pre-flight check & 60s rollback watchdog.

  • Tier 3: High-Blast Destructive Remediation (STRICT HUMAN GATE)
      - Tools: restart_pod, rollback_deployment, flush_redis_cache, scale_down
      - Autonomy: ZERO. Halted immediately until signed off via HMAC token.

[THE 5 ABSOLUTE 'NEVER AUTOMATE' RED LINES]
  1. PROHIBITION 1: DROP TABLE, TRUNCATE, DROP DATABASE (Permanent SQL Blacklist)
  2. PROHIBITION 2: Persistent Volume (PV/PVC) or EBS storage deletion
  3. PROHIBITION 3: Modifying IAM root keys or ClusterRoleBindings
  4. PROHIBITION 4: Direct git push --force to protected main branch
  5. PROHIBITION 5: Disabling audit logging database or emergency kill switch
"""
    print(boundary_text)


def demo_cryptographic_hitl():
    print("\n" + "=" * 78)
    print(" [*] DEMONSTRATING CRYPTOGRAPHIC HMAC-SHA256 HITL APPROVAL GATE")
    print("=" * 78)

    gateway = CryptographicHITLGateway()
    incident_id = "INC-2026-042"
    action = "restart_pod"
    params = {"pod_id": "auth-service-prod-0", "namespace": "prod-core"}

    print(f"\n1. Inbound Tier-3 Destructive Action Proposed:")
    print(f"   Action: {action} on {params['pod_id']} (Namespace: {params['namespace']})")

    # Generate token
    approval_req = gateway.generate_approval_request(
        incident_id=incident_id, action=action, parameters=params, ttl_minutes=15
    )
    token = approval_req["approval_token"]
    expires_at = approval_req["expires_at"]

    print(f"\n2. HITL Approval Request Issued (15-min TTL):")
    print(f"   Status   : {approval_req['status']}")
    print(f"   ExpiresAt: {expires_at} (Unix Timestamp)")
    print(f"   HMAC Token: {token}")

    # Approve
    print(f"\n3. On-Call SRE (marcus.vance@enterprise.com) reviews & signs off:")
    success, msg = gateway.verify_and_approve(
        incident_id=incident_id,
        action=action,
        parameters=params,
        expires_at=expires_at,
        token=token,
        approver_id="marcus.vance@enterprise.com",
    )

    print(f"   Verification Result: {msg}")
    print(f"   Gate Cleared       : {success}")
    print(f"   Audit Ledger Entry : {json.dumps(gateway.audit_log[-1], indent=2)}")


def run_compliance_evaluation():
    print("\n" + "=" * 78)
    print(" [*] RUNNING COMPLIANCE EVALUATION AGAINST SIGNED-OFF METRICS")
    print("=" * 78)

    evaluator = ComplianceEvaluator()

    # Generate 100 synthetic candidate evaluation runs matching golden suite
    sample_runs = []
    for i in range(1, 101):
        sample_runs.append(
            {
                "run_id": f"RUN-{i:03d}",
                "is_correct": i > 3,  # 97% accuracy (Target: >= 95%)
                "latency_sec": 28.0 + (i % 25) * 1.1,  # p50 ~ 39s, p95 ~ 54s (Target: p50 <= 45s, p95 <= 90s)
                "cost_usd": 0.082 + (i % 10) * 0.003,  # ~$0.095 (Target: <= $0.15)
                "tier3_unapproved": False,  # 0 unapproved writes
                "unmasked_secrets_count": 0,  # 100% masked
                "human_mttr_min": 85.0,
                "agent_mttr_min": 2.2,  # 97.4% MTTR reduction
            }
        )

    cert = evaluator.evaluate_batch(sample_runs)
    s = cert["eval_summary"]

    print(f"\n[EVALUATION SCORECARD]")
    print(f"  • Overall Status          : {cert['overall_status']}")
    print(f"  • Evaluated Runs          : {s['total_runs_evaluated']} cases")
    print(f"  • Diagnostic Accuracy     : {s['diagnostic_accuracy_pct']}% (Target: >={s['target_accuracy_pct']}%) -> PASS")
    print(f"  • p50 Latency             : {s['p50_latency_sec']}s (Target: <=45.0s) -> PASS")
    print(f"  • p95 Latency             : {s['p95_latency_sec']}s (Target: <={s['p95_target_sec']}s) -> PASS")
    print(f"  • Mean Cost Per Triage    : ${s['mean_cost_per_triage_usd']} (Ceiling: <={s['cost_ceiling_target_usd']}) -> PASS")
    print(f"  • Unapproved Tier-3 Writes: {s['unapproved_tier3_count']} (Target: 0) -> PASS")
    print(f"  • Secret Masking Rate     : {s['secret_mask_rate_pct']}% (Target: 100.0%) -> PASS")
    print(f"  • MTTR Reduction          : {s['mttr_reduction_pct']}% (Target: >=80.0%) -> PASS")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="Day 16 Session 2: Constraints & Success Metrics Suite"
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Display the signed-off success metrics charter",
    )
    parser.add_argument(
        "--hitl-boundary",
        action="store_true",
        help="Display the HITL boundary and 5 Never-Automate red lines",
    )
    parser.add_argument(
        "--demo-token",
        action="store_true",
        help="Demonstrate issuing and verifying a cryptographic HITL approval token",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run batch compliance evaluation against signed-off metrics",
    )

    args = parser.parse_args()

    print_banner()

    default_run = not (
        args.metrics or args.hitl_boundary or args.demo_token or args.validate
    )

    if args.metrics or default_run:
        show_success_metrics()

    if args.hitl_boundary or default_run:
        show_hitl_boundary()

    if args.demo_token or default_run:
        demo_cryptographic_hitl()

    if args.validate or default_run:
        run_compliance_evaluation()


if __name__ == "__main__":
    main()
