"""
Capstone Agent: OpsSentinel AI (Autonomous Enterprise SRE & Incident Response Agent).
Wired End-to-End combining:
1. RAG (SOPs, Runbooks, Citations)
2. Tool Execution (Telemetry DB, System Logs, Arithmetic, Service Restarts, Alerts)
3. Memory (Short-Term Dialogue Buffer + Long-Term Entity State)
4. Guardrails (Prompt Injection Defense, PII Masking, Blast-Radius Gates, Output Sanitization)
5. Robust Error Handling (429 rate-limit backoff, graceful degradations)
"""

import os
import re
import time
import json
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI

from rag_engine import RAGEngine
from tools import (
    CAPSTONE_TOOL_SCHEMAS,
    tool_query_telemetry_db,
    tool_read_system_logs,
    tool_calculate_metrics,
    tool_search_runbooks,
    tool_restart_service,
    tool_rollback_deployment,
    tool_dispatch_emergency_alert,
)
from memory_manager import MemoryManager
from guardrails import SecurityGuardrails

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")

CAPSTONE_SYSTEM_PROMPT = """You are OpsSentinel AI, an Autonomous Enterprise SRE & Incident Response Assistant.
Your core mission is reliable, secure incident triage, operational diagnostics, and system remediation.

CORE OPERATIONAL PROTOCOLS:
1. Grounding & RAG: When answering questions regarding corporate policies, incident SLAs, or disaster recovery runbooks, always search runbooks and cite the source document ID.
2. Diagnostic Tools: Use query_telemetry_db to inspect services and incidents, read_system_logs to diagnose errors, and calculate_metrics for exact arithmetic.
3. Blast-Radius Protection: Destructive actions (service restarts, deployment rollbacks) require explicit authorization tokens. If a token is provided in context or by the user, pass it to the tool; otherwise warn the user that authorization is required.
4. Concision & Accuracy: Deliver direct, factual answers without fluff. State root causes and concrete remediation steps clearly.
"""


class CapstoneAgent:
    """Production Capstone Agent unifying RAG, Tools, Memory, and Security Guardrails."""

    def __init__(self, memory: Optional[MemoryManager] = None):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be provided in .env.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.memory = memory or MemoryManager()
        self.guardrails = SecurityGuardrails()
        self.rag = RAGEngine()

    def _call_llm_with_retry(self, messages: List[Dict[str, Any]], tools: Any, max_retries: int = 4) -> Any:
        """Executes LLM call with exponential backoff on 429 quota exhaustion."""
        delay = 10.0
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    match = re.search(r"retryDelay':\s*'(\d+)s", err_str)
                    sleep_time = int(match.group(1)) + 2 if match else delay
                    print(f"      [Rate-Limit Notice] 429 quota on {self.model}. Sleeping {sleep_time}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(sleep_time)
                    delay = max(delay * 1.5, 30.0)
                else:
                    raise e
        # Final fallback attempt
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.1}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution to the appropriate implementation."""
        if name == "query_telemetry_db":
            return tool_query_telemetry_db(**args)
        elif name == "read_system_logs":
            return tool_read_system_logs(**args)
        elif name == "calculate_metrics":
            return tool_calculate_metrics(**args)
        elif name == "search_runbooks":
            return tool_search_runbooks(**args)
        elif name == "restart_service":
            return tool_restart_service(**args)
        elif name == "rollback_deployment":
            return tool_rollback_deployment(**args)
        elif name == "dispatch_emergency_alert":
            return tool_dispatch_emergency_alert(**args)
        return {"status": "ERROR", "error": f"Unknown tool: '{name}'"}

    def run(self, user_query: str, max_turns: int = 4) -> Dict[str, Any]:
        """
        Executes unified Capstone pipeline:
        Input Guardrail -> Context & Memory Prep -> Tool Loop with Blast-Radius Gate -> Output Guardrail -> Memory Store.
        """
        t0 = time.time()
        trajectory = []
        tools_called = []
        total_prompt_tokens = 0
        total_completion_tokens = 0

        # ===================================================================
        # LAYER 1: INPUT GUARDRAIL & PII REDACTION
        # ===================================================================
        guard_res = self.guardrails.validate_input(user_query)
        if not guard_res.is_allowed:
            latency_ms = (time.time() - t0) * 1000.0
            return {
                "user_query": user_query,
                "sanitized_query": guard_res.sanitized_input,
                "final_answer": f"SECURITY_BLOCK: {guard_res.rejection_reason}",
                "tools_called": [],
                "trajectory": [{"step": "input_guardrail", "status": "BLOCKED", "reason": guard_res.rejection_reason}],
                "is_blocked_by_guardrail": True,
                "redactions": [],
                "tokens_used": 0,
                "latency_ms": latency_ms,
            }

        effective_query = guard_res.sanitized_input

        # ===================================================================
        # LAYER 2: CONTEXT & MEMORY ASSEMBLY
        # ===================================================================
        entity_context = self.memory.get_context_injection()
        full_system_prompt = f"{CAPSTONE_SYSTEM_PROMPT}\n\n{entity_context}"

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": full_system_prompt},
        ]
        # Append short-term conversation history
        messages.extend(self.memory.buffer.get_recent_messages())
        # Append current user prompt
        messages.append({"role": "user", "content": effective_query})

        # ===================================================================
        # LAYER 3: REASONING & FUNCTION CALLING LOOP
        # ===================================================================
        final_answer = ""
        user_role = self.memory.entity_store.get_entity("user_role", "Admin")
        default_token = self.memory.entity_store.get_entity("approval_token", "")

        turn = 0
        while turn < max_turns:
            turn += 1

            response = self._call_llm_with_retry(messages, CAPSTONE_TOOL_SCHEMAS)
            msg = response.choices[0].message
            messages.append(msg)

            usage = getattr(response, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

            tool_calls = getattr(msg, "tool_calls", None) or []
            if not tool_calls:
                final_answer = msg.content or ""
                break

            for tc in tool_calls:
                fn_name = tc.function.name
                tools_called.append(fn_name)
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}

                # ===========================================================
                # BLAST-RADIUS & TOOL AUTHORIZATION GATE
                # ===========================================================
                is_auth, deny_reason = self.guardrails.validate_tool_execution(
                    tool_name=fn_name,
                    tool_args=args,
                    user_role=user_role,
                    approval_token=default_token,
                )

                if not is_auth:
                    obs = {
                        "status": "PERMISSION_DENIED",
                        "error": deny_reason,
                        "tool": fn_name,
                    }
                    trajectory.append({
                        "step": f"turn_{turn}",
                        "tool": fn_name,
                        "args": args,
                        "status": "BLOCKED_BY_BLAST_RADIUS_GATE",
                        "reason": deny_reason,
                    })
                else:
                    obs = self.execute_tool(fn_name, args)
                    trajectory.append({
                        "step": f"turn_{turn}",
                        "tool": fn_name,
                        "args": args,
                        "status": "EXECUTED",
                        "result_summary": str(obs)[:120],
                    })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(obs),
                })

        # Synthesize final answer if not completed
        if not final_answer:
            resp_final = self._call_llm_with_retry(messages, None)
            final_answer = resp_final.choices[0].message.content or ""
            usage = getattr(resp_final, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

        # ===================================================================
        # LAYER 4: OUTPUT GUARDRAIL SANITIZATION
        # ===================================================================
        sanitized_final_answer = self.guardrails.validate_output(final_answer)

        # ===================================================================
        # LAYER 5: SHORT-TERM MEMORY RECORDING
        # ===================================================================
        latency_ms = (time.time() - t0) * 1000.0
        self.memory.record_interaction(
            query=effective_query,
            response=sanitized_final_answer,
            tools=tools_called,
            timestamp=t0,
        )

        return {
            "user_query": user_query,
            "sanitized_query": effective_query,
            "final_answer": sanitized_final_answer,
            "tools_called": tools_called,
            "trajectory": trajectory,
            "is_blocked_by_guardrail": False,
            "redactions": guard_res.redactions_made,
            "tokens_used": total_prompt_tokens + total_completion_tokens,
            "latency_ms": latency_ms,
        }
