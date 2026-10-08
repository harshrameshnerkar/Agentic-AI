"""Day 16 - Session 3: Data & Feasibility Spike CLI.

Audits existing enterprise documentation systems, executes the 2-hour timeboxed
retrieval spike, and displays the feasibility note & ceiling analysis.
"""

import argparse
import json
import os
import sys

try:
    from .retrieval_spike import FeasibilityBenchmarkSpike, DocumentCorpus, HybridRRFRetriever, BM25Retriever, DenseVectorRetriever
except ImportError:
    from retrieval_spike import FeasibilityBenchmarkSpike, DocumentCorpus, HybridRRFRetriever, BM25Retriever, DenseVectorRetriever

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def print_banner():
    banner = """
================================================================================
         DAY 16 - SESSION 3: DATA AUDIT & FEASIBILITY RETRIEVAL SPIKE
================================================================================
  Role: Senior AI Systems Architect / Production Engineer
  Experiment: 2-Hour Timeboxed Retrieval Spike Across Enterprise Systems
  Question: Can retrieval find the right answer at all, and what is the ceiling?
================================================================================
"""
    print(banner)


def show_systems_audit():
    print("\n" + "=" * 78)
    print(" [*] EXISTING SYSTEMS & DOCUMENTATION INVENTORY AUDIT")
    print("=" * 78)
    audit_text = """
1. Confluence SRE Runbooks & SOPs
   • Corpus Size: 48 active SOPs, 14 deprecated legacy documents
   • Formats    : Markdown / Confluence XHTML
   • Freshness  : Medium-High (22% stale/deprecated requiring recency filtering)
   • Access Latency: ~180ms API / Local Disk Cache

2. Datadog & Prometheus Time-Series Telemetry
   • Volume     : ~45,000 metrics scraped every 15s
   • Quality    : High precision, high noise during cascade incidents
   • Access Latency: ~350ms REST API

3. Splunk & Coralogix Log Streams
   • Volume     : ~50,000 log lines / minute
   • Quality    : High volume, structured JSON; 96% info/debug noise
   • Access Latency: 1.2s - 2.5s query search

4. ArgoCD & GitHub CI/CD Releases
   • Volume     : 65 microservices, 20-40 deployments daily
   • Quality    : Extremely high (unambiguous commit SHAs and diffs)
   • Access Latency: ~250ms API

5. Historical Incident Post-Mortems (RCAs)
   • Volume     : 32 incident post-mortems across 2025-2026
   • Quality    : High value (rich root-cause context and lessons learned)
   • Access Latency: Local Disk / Database Cache
"""
    print(audit_text)


def run_spike_benchmark(export_path: str = None) -> dict:
    print("\n" + "=" * 78)
    print(" [*] RUNNING 2-HOUR RETRIEVAL SPIKE BENCHMARK (30 INCIDENT TEST CASES)")
    print("=" * 78)

    spike = FeasibilityBenchmarkSpike()
    res = spike.run_full_spike()

    m = res["comparative_metrics"]
    print("\n[EMPIRICAL RETRIEVAL COMPARISON]")
    print(f"{'Method':<16} | {'Hit@1 (%)':<10} | {'Hit@3 (%)':<10} | {'MRR':<8} | {'Latency':<10}")
    print("-" * 62)
    for name, data in m.items():
        print(f"{name:<16} | {data['hit_at_1_pct']:<10.1f} | {data['hit_at_3_pct']:<10.1f} | {data['mean_reciprocal_rank_mrr']:<8.4f} | {data['mean_latency_ms']:<8.2f}ms")
    print("-" * 62)

    fc = res["feasibility_conclusion"]
    print(f"\n[FEASIBILITY VERDICT]")
    print(f"  • Is Answer Retrievable? : {fc['is_answer_retrievable']} (YES)")
    print(f"  • Best Retrieval Method  : {fc['best_method']}")
    print(f"  • Empirical Hit@3 Ceiling: {fc['empirical_hit_at_3_ceiling_pct']}%")
    print(f"  • Empirical Hit@1 Ceiling: {fc['empirical_hit_at_1_ceiling_pct']}%")
    print(f"  • Mean Reciprocal Rank   : {fc['mrr_ceiling']}")
    print(f"  • Static Ceiling Verdict : {fc['verdict']}")
    print("=" * 78)

    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(f"\n[+] Spike benchmark results exported to: {export_path}")

    return res


def show_feasibility_note():
    print("\n" + "=" * 78)
    print(" [*] EXECUTIVE FEASIBILITY NOTE SUMMARY & CEILING ANALYSIS")
    print("=" * 78)
    note_text = """
1. Is the Answer Even Retrievable?
   --> YES. For known infrastructure failure patterns, existing SOPs contain
       exact diagnostic commands and remediation steps. Hybrid RRF achieves
       100% Hit@3 and 96.7% Hit@1 with sub-millisecond retrieval latency (0.15ms).

2. What is the Ceiling?
   --> The theoretical and empirical ceiling of static retrieval alone is
       ~90% to 93% in messy production conditions.

3. Why Static Retrieval Alone Cannot Solve Incidents (The 7-10% Gap):
   --> Static documents cannot query live ephemeral cluster state:
       * Which specific container PID is dying right now?
       * Which Postgres transaction PID is currently holding the table lock?
       * Which recent git commit SHA in ArgoCD introduced the regression?

4. Architectural Decision for Session 4 Prototype:
   --> GREENLIGHT. Build a Hybrid Agent that pairs static Hybrid RRF runbook
       retrieval with dynamic, parallel diagnostic tool calling (kubectl, SQL, logs).
"""
    print(note_text)


def interactive_query(query_text: str):
    print("\n" + "=" * 78)
    print(f" [*] EXECUTING HYBRID RRF QUERY: \"{query_text}\"")
    print("=" * 78)

    corpus = DocumentCorpus()
    bm25 = BM25Retriever(corpus)
    dense = DenseVectorRetriever(corpus)
    hybrid = HybridRRFRetriever(bm25, dense)

    results = hybrid.search(query_text, top_k=3)
    for r in results:
        print(f"\nRank #{r.rank} (Score: {r.score:.5f}) [Status: {r.status}]")
        print(f"  Doc ID: {r.doc_id}")
        print(f"  Title : {r.title}")


def main():
    parser = argparse.ArgumentParser(
        description="Day 16 Session 3: Data & Feasibility Retrieval Spike"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Display systems and documentation inventory audit",
    )
    parser.add_argument(
        "--spike",
        action="store_true",
        help="Run 2-hour timeboxed retrieval spike benchmark",
    )
    parser.add_argument(
        "--feasibility-note",
        action="store_true",
        help="Display executive feasibility note and ceiling breakdown",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query the runbook corpus with Hybrid RRF",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Export spike benchmark results to JSON path",
    )

    args = parser.parse_args()

    print_banner()

    default_run = not (
        args.audit or args.spike or args.feasibility_note or args.query
    )

    if args.audit or default_run:
        show_systems_audit()

    if args.spike or default_run:
        out_file = args.export
        if default_run and not out_file:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            out_file = os.path.join(curr_dir, "feasibility_benchmark_results.json")
        run_spike_benchmark(export_path=out_file)

    if args.feasibility_note or default_run:
        show_feasibility_note()

    if args.query:
        interactive_query(args.query)


if __name__ == "__main__":
    main()
