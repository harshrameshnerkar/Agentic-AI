"""
Day 14 - Session 1: CI Evaluation Harness & Metric Aggregator
==============================================================
Orchestrates batch evaluation runs across the golden dataset and computes:
  - Aggregate Pass Rate (%)
  - Schema Validity Rate (%)
  - Tool Accuracy Rate (%)
  - Safety Compliance Score (%) (Zero tolerance on un-gated destructive mutations)
  - Latency Metrics (p50, p95, mean)
  - Exports JSON metrics and rich GitHub Actions Markdown report
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    from day_14.session_1.prompt_registry import PromptVersion, PromptRegistry
    from day_14.session_1.golden_dataset import GOLDEN_EVAL_SUITE, GoldenTestCase
    from day_14.session_1.agent_evaluator import AgentEvaluator, TestEvaluationResult
except ImportError:
    from prompt_registry import PromptVersion, PromptRegistry
    from golden_dataset import GOLDEN_EVAL_SUITE, GoldenTestCase
    from agent_evaluator import AgentEvaluator, TestEvaluationResult


@dataclass
class EvalSuiteSummary:
    prompt_version: str
    prompt_name: str
    commit_sha: str
    author: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_pct: float
    schema_validity_pct: float
    tool_accuracy_pct: float
    safety_compliance_pct: float
    mean_latency_ms: float
    p95_latency_ms: float
    failed_test_ids: List[str]
    failure_breakdown: Dict[str, int]
    timestamp_utc: str


class EvaluationHarness:
    """Executes evaluation runs and compiles CI-ready metrics and reports."""

    def __init__(self, test_suite: Optional[List[GoldenTestCase]] = None):
        self.test_suite = test_suite or GOLDEN_EVAL_SUITE

    def run_eval(self, prompt_version: PromptVersion) -> Tuple[EvalSuiteSummary, List[TestEvaluationResult]]:
        """Executes full evaluation suite for a specific prompt version."""
        evaluator = AgentEvaluator(prompt_version)
        results: List[TestEvaluationResult] = []

        for tc in self.test_suite:
            res = evaluator.evaluate_case(tc)
            results.append(res)

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        pass_rate = round((passed / total) * 100.0, 2) if total > 0 else 0.0

        schema_valid_cnt = sum(1 for r in results if r.schema_valid)
        schema_pct = round((schema_valid_cnt / total) * 100.0, 2)

        tool_correct_cnt = sum(1 for r in results if r.tool_correct)
        tool_pct = round((tool_correct_cnt / total) * 100.0, 2)

        # Safety: check destructive cases specifically
        destructive_results = [r for r, tc in zip(results, self.test_suite) if tc.is_destructive]
        destructive_total = len(destructive_results)
        safe_cnt = sum(1 for r in destructive_results if r.safety_compliant)
        safety_pct = round((safe_cnt / destructive_total) * 100.0, 2) if destructive_total > 0 else 100.0

        latencies = sorted(r.latency_ms for r in results)
        mean_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        p95_idx = int(0.95 * len(latencies))
        p95_lat = latencies[min(p95_idx, len(latencies) - 1)] if latencies else 0.0

        failed_ids = [r.test_id for r in results if not r.passed]

        # Breakdown failure categories
        breakdown: Dict[str, int] = {}
        for r in results:
            for reason in r.failure_reasons:
                cat = reason.split(":")[0]
                breakdown[cat] = breakdown.get(cat, 0) + 1

        summary = EvalSuiteSummary(
            prompt_version=prompt_version.version,
            prompt_name=prompt_version.prompt_name,
            commit_sha=prompt_version.commit_sha,
            author=prompt_version.author,
            total_cases=total,
            passed_cases=passed,
            failed_cases=failed,
            pass_rate_pct=pass_rate,
            schema_validity_pct=schema_pct,
            tool_accuracy_pct=tool_pct,
            safety_compliance_pct=safety_pct,
            mean_latency_ms=mean_lat,
            p95_latency_ms=p95_lat,
            failed_test_ids=failed_ids,
            failure_breakdown=breakdown,
            timestamp_utc=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        )

        return summary, results

    def export_json(self, summary: EvalSuiteSummary, filepath: str) -> None:
        """Exports summary to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(summary), f, indent=2)

    def generate_markdown_report(
        self,
        summary: EvalSuiteSummary,
        results: List[TestEvaluationResult],
        baseline_summary: Optional[EvalSuiteSummary] = None,
    ) -> str:
        """Generates a GitHub-flavored Markdown report suitable for CI job summaries and PR comments."""
        badge = "PASSED" if summary.failed_cases == 0 else "FAILED"
        status_color = "🟢" if badge == "PASSED" else "🔴"

        md = []
        md.append(f"# {status_color} LLMOps CI Eval Report: `{summary.prompt_name}` ({summary.prompt_version})\n")
        md.append(f"**Commit:** `{summary.commit_sha}` | **Author:** `{summary.author}` | **Timestamp:** `{summary.timestamp_utc}`\n")
        md.append("## Executive Scorecard\n")
        md.append("| Metric | Candidate Value | Baseline Value | Delta | Status |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")

        def fmt_row(name: str, cand: float, base: Optional[float], unit: str = "%", invert: bool = False):
            if base is not None:
                delta = cand - base
                delta_str = f"{delta:+.1f}{unit}"
                if invert:
                    is_ok = delta <= 0
                else:
                    is_ok = delta >= 0
                st = "✅" if is_ok else "❌ REGRESSED"
                base_str = f"{base:.1f}{unit}"
            else:
                delta_str = "N/A"
                base_str = "N/A"
                st = "✅"
            return f"| **{name}** | {cand:.1f}{unit} | {base_str} | {delta_str} | {st} |"

        b_pass = baseline_summary.pass_rate_pct if baseline_summary else None
        b_schema = baseline_summary.schema_validity_pct if baseline_summary else None
        b_tool = baseline_summary.tool_accuracy_pct if baseline_summary else None
        b_safety = baseline_summary.safety_compliance_pct if baseline_summary else None

        md.append(fmt_row("Overall Pass Rate", summary.pass_rate_pct, b_pass))
        md.append(fmt_row("Safety Compliance (Zero Tolerance)", summary.safety_compliance_pct, b_safety))
        md.append(fmt_row("Schema Validity", summary.schema_validity_pct, b_schema))
        md.append(fmt_row("Tool Selection Accuracy", summary.tool_accuracy_pct, b_tool))
        md.append(fmt_row("Mean Latency", summary.mean_latency_ms, baseline_summary.mean_latency_ms if baseline_summary else None, "ms", invert=True))
        md.append(fmt_row("p95 Latency", summary.p95_latency_ms, baseline_summary.p95_latency_ms if baseline_summary else None, "ms", invert=True))

        md.append("\n## Test Case Results\n")
        md.append(f"- **Total Tests:** {summary.total_cases}")
        md.append(f"- **Passed:** {summary.passed_cases} ✅")
        md.append(f"- **Failed:** {summary.failed_cases} ❌")

        if summary.failed_cases > 0:
            md.append("\n### ⚠️ Failed Test Case Dissection\n")
            md.append("| Test ID | Category | Failure Reasons |")
            md.append("| :--- | :--- | :--- |")
            for r in results:
                if not r.passed:
                    reasons = "<br>".join(r.failure_reasons)
                    md.append(f"| `{r.test_id}` | `{r.category}` | {reasons} |")

        return "\n".join(md)
