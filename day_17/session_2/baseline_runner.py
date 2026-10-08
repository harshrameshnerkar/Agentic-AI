"""
Day 17 - Session 2: Simplest Thing That Works
Baseline Evaluation Engine: Plain Prompt vs. Single Retrieval Call (Vanilla RAG)
Scored against the 20-case Golden Evaluation Dataset.
"""

import os
import sys
import json
import time
import math
import re
from typing import Dict, Any, List, Tuple

# Set UTF-8 encoding for Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class SimpleRunbookRetriever:
    """Single retrieval call baseline using BM25-style term frequency matching."""

    def __init__(self, runbooks_path: str):
        with open(runbooks_path, "r", encoding="utf-8") as f:
            self.runbooks = json.load(f)

    def retrieve_single(self, query: str) -> Tuple[Dict[str, Any], float]:
        """Performs a single retrieval call, returning top-1 matching runbook and score."""
        query_tokens = set(re.findall(r"\w+", query.lower()))
        best_doc = None
        best_score = 0.0

        for doc in self.runbooks:
            doc_text = f"{doc['title']} {doc['content']} {doc['service']}".lower()
            doc_tokens = re.findall(r"\w+", doc_text)
            
            # Simple term overlap scoring
            matches = sum(1 for t in query_tokens if t in doc_tokens)
            score = matches / (len(query_tokens) + 1e-5)
            
            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc is None or best_score < 0.15:
            return None, 0.0
        return best_doc, best_score


class BaselineArchitectures:
    """Implementations of Baseline 1 (Plain Prompt) and Baseline 2 (Single Retrieval RAG)."""

    def __init__(self, runbooks_path: str):
        self.retriever = SimpleRunbookRetriever(runbooks_path)

    def run_plain_prompt(self, query: str) -> Dict[str, Any]:
        """
        Baseline 1: Plain Prompt (Zero-Shot Completion).
        Has no access to documents, tools, or live cluster telemetry.
        """
        start_time = time.perf_counter()

        # Simulating plain LLM reasoning solely from pre-training weights
        # Notice: It produces plausible-sounding generic advice, but lacks real-time facts
        q_lower = query.lower()

        if "vault" in q_lower and "token" in q_lower:
            diagnosis = "Vault token rotation can usually be triggered via the Vault CLI or web UI."
            remediation = "Run vault token create or check corporate secret policies."
            is_generic = True
        elif "s3" in q_lower or "lifecycle" in q_lower:
            diagnosis = "Standard cloud storage lifecycles often transition data from S3 to Glacier."
            remediation = "Inspect the AWS S3 console under Management -> Lifecycle rules."
            is_generic = True
        elif "crashloopbackoff" in q_lower or "crashing" in q_lower:
            diagnosis = "The container is crashing repeatedly. Possible causes: memory limits, uncaught exceptions, or bad health checks."
            remediation = "Check kubectl logs and restart the pod deployment."
            is_generic = True
        elif "latency" in q_lower or "504" in q_lower:
            diagnosis = "High latency or 504 Gateway Timeout typically indicates upstream timeout or network bottleneck."
            remediation = "Check load balancer health checks and restart web servers."
            is_generic = True
        elif "kafka" in q_lower or "lag" in q_lower:
            diagnosis = "Kafka consumer lag happens when consumption rate is slower than production rate."
            remediation = "Increase number of consumer worker replicas."
            is_generic = True
        else:
            diagnosis = "Generic infrastructure alert detected. System requires operator inspection."
            remediation = "Examine service logs and restart affected workload."
            is_generic = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000 + 120.0  # +120ms baseline simulated LLM latency
        # Plain prompt token cost: ~200 input tokens, ~100 output tokens @ $0.00015/1k = ~$0.000045
        cost_usd = 0.000045

        return {
            "architecture": "Plain Prompt (Zero-Shot)",
            "diagnosis": diagnosis,
            "remediation": remediation,
            "is_generic": is_generic,
            "retrieved_doc": None,
            "latency_ms": round(elapsed_ms, 2),
            "cost_usd": round(cost_usd, 6)
        }

    def run_single_retrieval_rag(self, query: str) -> Dict[str, Any]:
        """
        Baseline 2: Single Retrieval Call (Vanilla RAG).
        Retrieves top-1 static runbook, appends to prompt, generates answer.
        """
        start_time = time.perf_counter()

        doc, score = self.retriever.retrieve_single(query)

        if doc is not None and score >= 0.15:
            # We retrieved a relevant runbook!
            diagnosis = f"According to documentation '{doc['title']}': {doc['content']}"
            remediation = doc['content']
            is_generic = False
        else:
            # Retrieval failed or no matching runbook found in static docs
            q_lower = query.lower()
            if "crashloopbackoff" in q_lower or "oom" in q_lower:
                diagnosis = "No matching runbook found. Suspected container failure. Recommending general pod restart."
                remediation = "kubectl rollout restart deployment"
            elif "504" in q_lower or "latency" in q_lower:
                diagnosis = "No matching runbook found. Suspected gateway timeout. Recommending generic upstream check."
                remediation = "Inspect network gateways and upstream databases."
            else:
                diagnosis = "No matching runbook found in knowledge base. Unrecognized incident."
                remediation = "Manual human SRE triage required."
            is_generic = True

        elapsed_ms = (time.perf_counter() - start_time) * 1000 + 280.0  # +280ms retrieval + LLM synthesis
        # Single RAG token cost: ~600 input tokens, ~150 output tokens = ~$0.000115
        cost_usd = 0.000115

        return {
            "architecture": "Single Retrieval Call (Vanilla RAG)",
            "diagnosis": diagnosis,
            "remediation": remediation,
            "is_generic": is_generic,
            "retrieved_doc": doc["doc_id"] if doc else None,
            "latency_ms": round(elapsed_ms, 2),
            "cost_usd": round(cost_usd, 6)
        }


class BaselineEvaluator:
    """Scores baseline predictions against the 20-case golden evaluation dataset."""

    def __init__(self, eval_dataset_path: str, runbooks_path: str):
        with open(eval_dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        self.architectures = BaselineArchitectures(runbooks_path)

    def score_prediction(self, test_case: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates whether prediction correctly identifies root cause and action."""
        pred_text = f"{pred['diagnosis']} {pred['remediation']}".lower()
        key_indicators = test_case["key_indicators"]

        # Check key indicator hits
        matched_indicators = [ind for ind in key_indicators if ind.lower() in pred_text]
        indicator_recall = len(matched_indicators) / len(key_indicators) if key_indicators else 1.0

        # Exact pass criterion: must achieve >= 60% key indicator recall and not be generic guess
        is_pass = (indicator_recall >= 0.60) and (not pred["is_generic"] or test_case["category"] == "static_runbook" and indicator_recall >= 0.75)

        return {
            "incident_id": test_case["incident_id"],
            "category": test_case["category"],
            "service": test_case["service"],
            "indicator_recall": round(indicator_recall, 3),
            "is_pass": is_pass,
            "is_generic": pred["is_generic"],
            "latency_ms": pred["latency_ms"],
            "cost_usd": pred["cost_usd"]
        }

    def evaluate_all(self) -> Dict[str, Any]:
        """Runs evaluation for both Baseline 1 and Baseline 2 across all 20 incidents."""
        plain_results = []
        rag_results = []

        for case in self.dataset:
            # 1. Plain prompt
            pred_plain = self.architectures.run_plain_prompt(case["query"])
            score_plain = self.score_prediction(case, pred_plain)
            plain_results.append(score_plain)

            # 2. Single retrieval RAG
            pred_rag = self.architectures.run_single_retrieval_rag(case["query"])
            score_rag = self.score_prediction(case, pred_rag)
            rag_results.append(score_rag)

        # Compute aggregate metrics
        def aggregate(results: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
            total = len(results)
            passed = sum(1 for r in results if r["is_pass"])
            pass_rate = (passed / total) * 100

            # Sub-category pass rates
            static_cases = [r for r in results if r["category"] == "static_runbook"]
            ephemeral_cases = [r for r in results if r["category"] == "ephemeral_cluster"]

            static_pass_rate = (sum(1 for r in static_cases if r["is_pass"]) / len(static_cases)) * 100 if static_cases else 0
            ephemeral_pass_rate = (sum(1 for r in ephemeral_cases if r["is_pass"]) / len(ephemeral_cases)) * 100 if ephemeral_cases else 0

            avg_recall = sum(r["indicator_recall"] for r in results) / total
            avg_latency = sum(r["latency_ms"] for r in results) / total
            avg_cost = sum(r["cost_usd"] for r in results) / total
            generic_guess_rate = (sum(1 for r in results if r["is_generic"]) / total) * 100

            return {
                "name": name,
                "total_cases": total,
                "passed_cases": passed,
                "overall_pass_rate_pct": round(pass_rate, 2),
                "static_runbook_pass_rate_pct": round(static_pass_rate, 2),
                "ephemeral_cluster_pass_rate_pct": round(ephemeral_pass_rate, 2),
                "avg_indicator_recall_pct": round(avg_recall * 100, 2),
                "generic_guess_rate_pct": round(generic_guess_rate, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "avg_cost_usd": round(avg_cost, 6)
            }

        plain_summary = aggregate(plain_results, "Baseline 1: Plain Prompt (Zero-Shot)")
        rag_summary = aggregate(rag_results, "Baseline 2: Single Retrieval Call (Vanilla RAG)")

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataset_size": len(self.dataset),
            "plain_summary": plain_summary,
            "rag_summary": rag_summary,
            "detailed_plain_results": plain_results,
            "detailed_rag_results": rag_results
        }


def run_and_save_baselines(output_dir: str = None) -> Dict[str, Any]:
    """Executes the baseline evaluations and saves BASELINE_SCORES.json."""
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    eval_path = os.path.join(output_dir, "eval_dataset.json")
    runbooks_path = os.path.join(output_dir, "static_runbooks.json")

    evaluator = BaselineEvaluator(eval_path, runbooks_path)
    scorecard = evaluator.evaluate_all()

    scores_file = os.path.join(output_dir, "BASELINE_SCORES.json")
    with open(scores_file, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)

    return scorecard


if __name__ == "__main__":
    scores = run_and_save_baselines()
    print("=" * 78)
    print(" DAY 17 - SESSION 2: SIMPLEST THING THAT WORKS (BASELINE EVALUATION)")
    print("=" * 78)
    print(f"Dataset: 20 Golden Cases (6 Static Runbook Queries, 14 Ephemeral Incidents)")
    print("-" * 78)
    
    p = scores["plain_summary"]
    r = scores["rag_summary"]
    
    print(f"{'METRIC':<36} | {'PLAIN PROMPT':<18} | {'SINGLE RETRIEVAL RAG':<20}")
    print("-" * 78)
    print(f"{'Overall Pass Rate':<36} | {p['overall_pass_rate_pct']:>16.1f}% | {r['overall_pass_rate_pct']:>18.1f}%")
    print(f"{'Static Runbook Pass Rate':<36} | {p['static_runbook_pass_rate_pct']:>16.1f}% | {r['static_runbook_pass_rate_pct']:>18.1f}%")
    print(f"{'Ephemeral Incident Pass Rate':<36} | {p['ephemeral_cluster_pass_rate_pct']:>16.1f}% | {r['ephemeral_cluster_pass_rate_pct']:>18.1f}%")
    print(f"{'Key Indicator Recall':<36} | {p['avg_indicator_recall_pct']:>16.1f}% | {r['avg_indicator_recall_pct']:>18.1f}%")
    print(f"{'Generic Guess / Hallucination Rate':<36} | {p['generic_guess_rate_pct']:>16.1f}% | {r['generic_guess_rate_pct']:>18.1f}%")
    print(f"{'Mean Latency (ms)':<36} | {p['avg_latency_ms']:>16.1f}ms | {r['avg_latency_ms']:>18.1f}ms")
    print(f"{'Cost per Query ($)':<36} | ${p['avg_cost_usd']:>15.6f} | ${r['avg_cost_usd']:>17.6f}")
    print("=" * 78)
    print("[*] Baseline scores successfully recorded to BASELINE_SCORES.json")
