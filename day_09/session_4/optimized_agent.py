"""
Cost & Latency Optimized Agent.
Integrates:
1. Exact & Semantic Hybrid Cache (<2ms, $0 cost on hits).
2. Prompt Compression (75-token lean system prompt).
3. Observation Compactor (compact tabular format instead of bloated JSON arrays).
4. Tiered Model Routing (small model first, escalate on failure).
"""

import os
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

from tools import (
    OPTIMIZED_TOOL_SCHEMAS,
    tool_query_database,
    tool_search_docs,
    tool_calculate,
    tool_read_log,
)
from prompt_optimizer import (
    OPTIMIZED_COMPRESSED_SYSTEM_PROMPT,
    ObservationCompactor,
)
from cache_manager import HybridCacheManager
from model_router import ModelRouter

load_dotenv()


class OptimizedAgent:
    """Production-optimized agent maximizing cost reduction and latency efficiency."""

    def __init__(self, semantic_threshold: float = 0.55):
        self.router = ModelRouter()
        self.cache = HybridCacheManager(semantic_threshold=semantic_threshold)
        self.compactor = ObservationCompactor()

    def execute_tool_compact(self, name: str, args: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Executes tool and returns both raw observation and token-compacted string."""
        if name == "query_database":
            raw = tool_query_database(**args)
            compact_str = self.compactor.compact_db_output(raw.get("rows", []))
            return raw, f"table:{raw.get('table')}\n{compact_str}"
        elif name == "search_docs":
            raw = tool_search_docs(**args)
            compact_str = self.compactor.compact_doc_output(raw.get("matches", []))
            return raw, compact_str
        elif name == "calculate":
            raw = tool_calculate(**args)
            return raw, f"res:{raw.get('result')}"
        elif name == "read_log":
            raw = tool_read_log(**args)
            compact_str = self.compactor.compact_log_output(raw.get("content", ""))
            return raw, compact_str
        return {"error": f"Unknown tool: {name}"}, "err"

    def run(self, prompt: str, max_turns: int = 3) -> Dict[str, Any]:
        t0 = time.time()

        # ===================================================================
        # LAYER 1: EXACT & SEMANTIC CACHE LOOKUP
        # ===================================================================
        cached_val, cache_type = self.cache.lookup(prompt)
        if cached_val is not None:
            latency_ms = (time.time() - t0) * 1000.0
            return {
                "prompt": prompt,
                "final_answer": cached_val["final_answer"],
                "tools_called": cached_val.get("tools_called", []),
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_ms": latency_ms,
                "is_cache_hit": True,
                "cache_type": cache_type,
                "model_used": "cached",
            }

        # ===================================================================
        # LAYER 2: COMPRESSED PROMPT & ROUTED EXECUTION
        # ===================================================================
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": OPTIMIZED_COMPRESSED_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        total_prompt_tokens = 0
        total_completion_tokens = 0
        final_answer = ""
        tools_called = []
        last_model = self.router.tier1_model

        turn = 0
        while turn < max_turns:
            turn += 1

            res, model_used, was_escalated = self.router.call_with_routing(
                messages=messages,
                tools=OPTIMIZED_TOOL_SCHEMAS,
            )
            last_model = model_used
            msg = res.choices[0].message
            messages.append(msg)

            usage = getattr(res, "usage", None)
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

                # Execute with observation compaction
                raw_obs, compact_content = self.execute_tool_compact(fn_name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": compact_content,
                })

        if not final_answer:
            res_final, model_used, _ = self.router.call_with_routing(messages=messages, tools=None)
            last_model = model_used
            final_answer = res_final.choices[0].message.content or ""
            usage = getattr(res_final, "usage", None)
            if usage:
                total_prompt_tokens += getattr(usage, "prompt_tokens", 0)
                total_completion_tokens += getattr(usage, "completion_tokens", 0)

        latency_ms = (time.time() - t0) * 1000.0

        result = {
            "prompt": prompt,
            "final_answer": final_answer,
            "tools_called": tools_called,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "latency_ms": latency_ms,
            "is_cache_hit": False,
            "cache_type": None,
            "model_used": last_model,
        }

        # Store in cache for future exact/semantic hits
        self.cache.store(prompt, result)

        return result
