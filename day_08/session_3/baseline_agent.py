"""
Baseline Unengineered Agent.
Demonstrates common anti-patterns:
- Bloated system prompt with redundant few-shot examples and static tables.
- Raw, unpruned tool output ingestion (complete JSON dumps, verbose stack traces).
- Unbounded conversation history accumulation without compaction.
- Dumps all sub-task logs into the main reasoning context.
"""

import os
import json
import time
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from cost_tracker import SessionTokenTracker
from tools import BASELINE_TOOL_REGISTRY, BASELINE_TOOL_SCHEMAS

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


# Bloated 1,200+ token unengineered system prompt with redundant examples and static definitions
BLOATED_SYSTEM_PROMPT = """You are an Enterprise Site Reliability Engineering Diagnostic Agent.
Your duty is to investigate incidents in cloud infrastructure systems, analyze root causes, inspect telemetry,
evaluate container logs, assess networking configurations, review security groups, review cluster versions,
and synthesize comprehensive incident response reports.

=== EXTENSIVE GUIDELINES AND DETAILED METHODOLOGY ===
When analyzing an incident, you must always adhere strictly to the following 12-step SRE playbook:
1. Identify the incident identifier and confirm its presence in the cluster database.
2. Review the Kubernetes version, CNI plugin type, and proxy mode to ensure network driver compatibility.
3. Review all VPC endpoints and security groups to confirm ingress/egress authorization.
4. Retrieve every telemetry time series sample available in the database across all metrics.
5. Inspect CPU, memory, load average, disk I/O, network RX/TX, and GC statistics across each timestamp.
6. Pull full container logs from stdout/stderr, including all debug, trace, info, warn, and error statements.
7. Correlate timestamps between log events and telemetry degradation spikes.
8. Identify any OutOfMemoryError, NullPointerException, or JVM crash events.
9. Formulate an executive root cause summary detailing why the system failed.
10. Formulate an engineering remediation proposal.
11. Propose long-term preventative architectural guardrails.
12. Ensure all findings are formatted with comprehensive technical detail.

=== COMPREHENSIVE FEW-SHOT EXAMPLES ===
Example 1:
Incident ID: INC-1001
Symptoms: Pod crash loop in Billing Service.
Log excerpt: java.lang.NullPointerException at com.company.billing.TaxCalculator.calc(TaxCalculator.java:42)
Resolution: Deploy hotfix patching null tax rate checks.
Root cause: Missing null check in TaxCalculator.

Example 2:
Incident ID: INC-2002
Symptoms: Redis latency spike.
Log excerpt: Connection reset by peer from client 10.244.2.14
Resolution: Increase max clients setting and recycle idle pool connections.
Root cause: Connection pool exhaustion.

Example 3:
Incident ID: INC-3003
Symptoms: Disk full on node storage.
Log excerpt: Write failed: No space left on device.
Resolution: Rotate docker daemon container log files and purge orphan volumes.
Root cause: Unbounded container log generation.

Always use your tools systematically to gather the incident payload, telemetry series, and raw logs before finalizing your analysis.
"""


class BaselineAgent:
    """Agent running without context engineering or token budget controls."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.tracker = SessionTokenTracker("Baseline_Unoptimized_Agent")

    def run(self, user_prompt: str, max_turns: int = 5) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": BLOATED_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        t_start = time.monotonic()
        turn = 0
        final_answer = ""
        tool_call_history = []

        while turn < max_turns:
            turn += 1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=BASELINE_TOOL_SCHEMAS,
                tool_choice="auto",
                temperature=0.1,
            )

            usage = getattr(response, "usage", None)
            if usage:
                self.tracker.record_turn(
                    turn_number=turn,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    context_type="main"
                )

            msg = response.choices[0].message
            # Append message directly to preserve Gemini thought signatures
            messages.append(msg)

            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_answer = msg.content or ""
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                raw_args = tc.function.arguments
                try:
                    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                except Exception:
                    args = {}

                tool_fn = BASELINE_TOOL_REGISTRY.get(fn_name)
                obs = tool_fn(**args) if tool_fn else {"error": f"Tool '{fn_name}' not found"}

                tool_call_history.append({"tool": fn_name, "args": args})

                # Anti-pattern: Appending massive raw dictionary without any filtering or compaction
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs, default=str),
                })

        total_duration = time.monotonic() - t_start

        return {
            "approach": "Baseline (Unengineered Context)",
            "turns_executed": turn,
            "total_duration_sec": round(total_duration, 2),
            "token_summary": self.tracker.summary(),
            "final_answer": final_answer,
            "tool_calls_count": len(tool_call_history),
        }
