"""
Day 17 - Session 2: Simplest Thing That Works
Evaluates Plain Prompt vs Single Retrieval RAG baselines against 20 golden cases.
"""

import json
import os
import re
import time
from typing import Any, Dict, List, Tuple


class SimpleRunbookRetriever:
    """Keyword retriever for static runbooks."""

    def __init__(self, runbooks_path: str):
        with open(runbooks_path, "r", encoding="utf-8") as f:
            self.runbooks = json.load(f)

    def retrieve_single(self, query: str) -> Tuple[Any, float]:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        best_doc, best_score = None, 0.0

        for doc in self.runbooks:
            doc_text = f"{doc['title']} {doc['content']} {doc['service']}".lower()
            doc_tokens = re.findall(r"\w+", doc_text)
            matches = sum(1 for t in query_tokens if t in doc_tokens)
            score = matches / (len(query_tokens) + 1e-5)
            if score > best_score:
                best_score = score
                best_doc = doc

        if best_doc is None or best_score < 0.15:
            return None, 0.0
        return best_doc, best_score


class BaselineArchitectures:
    """Implementations for Plain Prompt and Single Retrieval RAG."""

    def __init__(self, runbooks_path: str):
        self.retriever = SimpleRunbookRetriever(runbooks_path)

    def run_plain_prompt(self, query: str) -> Dict[str, Any]:
        return {
            "architecture": "Plain Prompt (Zero-Shot)",
            "diagnosis": "Generic infrastructure alert detected without live cluster access.",
            "remediation": "Examine service logs and restart affected workload.",
            "is_generic": True,
            "retrieved_doc": None,
            "latency_ms": 120.0,
            "cost_usd": 0.000045,
        }

    def run_single_retrieval_rag(self, query: str) -> Dict[str, Any]:
        doc, score = self.retriever.retrieve_single(query)
        if doc and score >= 0.15:
            return {
                "architecture": "Single Retrieval Call (Vanilla RAG)",
                "diagnosis": f"Runbook {doc['title']}: {doc['content']}",
                "remediation": doc["content"],
                "is_generic": False,
                "retrieved_doc": doc["doc_id"],
                "latency_ms": 280.0,
                "cost_usd": 0.000115,
            }
        return {
            "architecture": "Single Retrieval Call (Vanilla RAG)",
            "diagnosis": "No matching runbook found in knowledge base.",
            "remediation": "Manual triage required.",
            "is_generic": True,
            "retrieved_doc": None,
            "latency_ms": 280.0,
            "cost_usd": 0.000115,
        }


class BaselineEvaluator:
    """Scores baselines against the 20-case golden evaluation dataset."""

    def __init__(self, eval_dataset_path: str, runbooks_path: str):
        with open(eval_dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        self.architectures = BaselineArchitectures(runbooks_path)

    def score_prediction(self, test_case: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, Any]:
        pred_text = f"{pred['diagnosis']} {pred['remediation']}".lower()
        key_indicators = test_case["key_indicators"]
        matched = [ind for ind in key_indicators if ind.lower() in pred_text]
        recall = len(matched) / len(key_indicators) if key_indicators else 1.0

        is_pass = (recall >= 0.60) and (
            not pred["is_generic"] or (test_case["category"] == "static_runbook" and recall >= 0.75)
        )

        return {
            "incident_id": test_case["incident_id"],
            "category": test_case["category"],
            "service": test_case["service"],
            "indicator_recall": round(recall, 3),
            "is_pass": is_pass,
            "is_generic": pred["is_generic"],
            "latency_ms": pred["latency_ms"],
            "cost_usd": pred["cost_usd"],
        }

    def evaluate_all(self) -> Dict[str, Any]:
        plain_results = [self.score_prediction(c, self.architectures.run_plain_prompt(c["query"])) for c in self.dataset]
        rag_results = [self.score_prediction(c, self.architectures.run_single_retrieval_rag(c["query"])) for c in self.dataset]

        def aggregate(results: List[Dict[str, Any]], name: str) -> Dict[str, Any]:
            total = len(results)
            passed = sum(1 for r in results if r["is_pass"])
            static_cases = [r for r in results if r["category"] == "static_runbook"]
            ephemeral_cases = [r for r in results if r["category"] == "ephemeral_cluster"]

            return {
                "name": name,
                "total_cases": total,
                "passed_cases": passed,
                "overall_pass_rate_pct": round((passed / total) * 100, 2),
                "static_runbook_pass_rate_pct": round((sum(1 for r in static_cases if r["is_pass"]) / len(static_cases)) * 100, 2),
                "ephemeral_cluster_pass_rate_pct": round((sum(1 for r in ephemeral_cases if r["is_pass"]) / len(ephemeral_cases)) * 100, 2),
                "avg_indicator_recall_pct": round((sum(r["indicator_recall"] for r in results) / total) * 100, 2),
                "generic_guess_rate_pct": round((sum(1 for r in results if r["is_generic"]) / total) * 100, 2),
                "avg_latency_ms": round(sum(r["latency_ms"] for r in results) / total, 2),
                "avg_cost_usd": round(sum(r["cost_usd"] for r in results) / total, 6),
            }

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataset_size": len(self.dataset),
            "plain_summary": aggregate(plain_results, "Baseline 1: Plain Prompt (Zero-Shot)"),
            "rag_summary": aggregate(rag_results, "Baseline 2: Single Retrieval Call (Vanilla RAG)"),
            "detailed_plain_results": plain_results,
            "detailed_rag_results": rag_results,
        }


def run_and_save_baselines(output_dir: str = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    evaluator = BaselineEvaluator(
        os.path.join(output_dir, "eval_dataset.json"),
        os.path.join(output_dir, "static_runbooks.json"),
    )
    scorecard = evaluator.evaluate_all()
    with open(os.path.join(output_dir, "BASELINE_SCORES.json"), "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2)
    return scorecard


if __name__ == "__main__":
    scores = run_and_save_baselines()
    print("Baseline scores saved to BASELINE_SCORES.json")
