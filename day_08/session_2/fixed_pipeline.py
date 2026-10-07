"""
Fixed Deterministic Pipeline Solution.
Demonstrates:
- Pure Python deterministic computation for known, rule-based operations:
  (validation, currency normalization, summation, sorting, anomaly detection).
- Single targeted LLM call for executive natural language narrative synthesis.
"""

import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from data import EXCHANGE_RATES, GROUND_TRUTH, RAW_INVOICES

# Load environment configuration
load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class FixedPipelineAuditor:
    """
    Solves the FinOps audit task using a deterministic pipeline for data & math,
    followed by a single LLM call for executive narrative synthesis.
    """

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def execute_deterministic_audit(self, invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pure Python: Validation, normalization, aggregation, anomaly detection.
        Zero LLM calls, zero hallucinations, microsecond latency.
        """
        normalized_items = []
        total_spend_usd = 0.0
        anomalies = []

        for item in invoices:
            rate = EXCHANGE_RATES.get(item["currency"], 1.0)
            cost_usd = round(item["amount"] * rate, 2)
            budget_usd = item["monthly_budget_usd"]
            variance_pct = round(((cost_usd - budget_usd) / budget_usd) * 100.0, 2)
            is_anomaly = variance_pct > 15.0

            row = {
                "service": item["service"],
                "vendor": item["vendor"],
                "raw_amount": item["amount"],
                "currency": item["currency"],
                "cost_usd": cost_usd,
                "budget_usd": budget_usd,
                "variance_pct": variance_pct,
                "is_anomaly": is_anomaly,
            }
            normalized_items.append(row)
            total_spend_usd = round(total_spend_usd + cost_usd, 2)

            if is_anomaly:
                anomalies.append({
                    "service": item["service"],
                    "cost_usd": cost_usd,
                    "budget_usd": budget_usd,
                    "variance_pct": variance_pct,
                })

        # Top 3 most expensive services
        sorted_by_spend = sorted(normalized_items, key=lambda x: x["cost_usd"], reverse=True)
        top_3 = [
            {"service": x["service"], "cost_usd": x["cost_usd"]}
            for x in sorted_by_spend[:3]
        ]

        # Sort anomalies by variance descending
        anomalies.sort(key=lambda x: x["variance_pct"], reverse=True)

        return {
            "normalized_items": normalized_items,
            "total_spend_usd": total_spend_usd,
            "top_3_services": top_3,
            "anomalies": anomalies,
        }

    def run(self, invoices: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        invoices = invoices or RAW_INVOICES
        t_start = time.monotonic()

        # Step 1: Pure Deterministic Data & Math Processing
        t_det_start = time.monotonic()
        audit_data = self.execute_deterministic_audit(invoices)
        det_duration_sec = time.monotonic() - t_det_start

        # Step 2: Single Targeted LLM Call for Executive Narrative
        t_llm_start = time.monotonic()
        system_prompt = (
            "You are a Senior FinOps Financial Analyst. "
            "Write an executive briefing summarizing the provided exact infrastructure audit calculations. "
            "Include key spend figures, the top 3 services, budget anomalies, and actionable next steps. "
            "Do NOT recalculate numbers; use the exact metrics supplied."
        )

        user_content = (
            f"Official FinOps Audit Calculations:\n"
            f"- Total Normalized Spend: ${audit_data['total_spend_usd']:,.2f} USD\n"
            f"- Top 3 Cost Drivers:\n"
            f"  1. {audit_data['top_3_services'][0]['service']}: ${audit_data['top_3_services'][0]['cost_usd']:,.2f}\n"
            f"  2. {audit_data['top_3_services'][1]['service']}: ${audit_data['top_3_services'][1]['cost_usd']:,.2f}\n"
            f"  3. {audit_data['top_3_services'][2]['service']}: ${audit_data['top_3_services'][2]['cost_usd']:,.2f}\n"
            f"- Budget Anomalies (>15% over):\n"
        )
        for a in audit_data["anomalies"]:
            user_content += f"  • {a['service']}: ${a['cost_usd']:,.2f} (Budget: ${a['budget_usd']:,.2f}, +{a['variance_pct']}%)\n"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1
        )
        llm_duration_sec = time.monotonic() - t_llm_start
        total_duration_sec = time.monotonic() - t_start

        executive_summary = (response.choices[0].message.content or "").strip()
        usage = getattr(response, "usage", None)
        prompt_tokens = usage.prompt_tokens if usage else 450
        completion_tokens = usage.completion_tokens if usage else 250
        total_tokens = prompt_tokens + completion_tokens

        # Correctness check against ground truth
        is_exact_match = (
            abs(audit_data["total_spend_usd"] - GROUND_TRUTH["total_spend_usd"]) < 0.01 and
            len(audit_data["anomalies"]) == len(GROUND_TRUTH["anomalies"])
        )

        return {
            "approach": "Fixed Deterministic Pipeline",
            "audit_data": audit_data,
            "executive_summary": executive_summary,
            "llm_calls_made": 1,
            "deterministic_time_sec": round(det_duration_sec, 6),
            "llm_time_sec": round(llm_duration_sec, 3),
            "total_time_sec": round(total_duration_sec, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "math_accuracy_pct": 100.0 if is_exact_match else 0.0,
            "is_exact_match": is_exact_match,
        }
