"""
Tiered Model Router (Small Model First, Escalate on Failure).
Implements:
- Primary Tier: Fast & Economical lightweight model (gemini-3.1-flash-lite).
- Secondary Tier: High-capacity flagship model (gemini-2.5-pro) invoked only on escalation.
- Quality Validation Gate triggering automated fallback.
"""

import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
MODEL_CHEAP = os.getenv("MODEL_CHEAP", "gemini-3.1-flash-lite")
MODEL_EXPENSIVE = os.getenv("MODEL_EXPENSIVE", "gemini-2.5-pro")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")


class ModelRouter:
    """Routes requests to the cheapest capable model tier, escalating only on failure."""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY or GEMINI_API_KEY must be configured in .env.")
        self.client = OpenAI(base_url=OPENAI_BASE_URL, api_key=OPENAI_API_KEY)
        self.tier1_model = MODEL_CHEAP
        self.tier2_model = MODEL_EXPENSIVE

        self.tier1_invocations = 0
        self.tier2_escalations = 0

    def call_with_routing(
        self,
        messages: List[Dict[str, Any]],
        tools: Any = None,
        force_tier2: bool = False,
        max_retries: int = 4,
    ) -> Tuple[Any, str, bool]:
        """
        Attempts execution on Tier 1.
        If an error or invalid generation occurs, escalates to Tier 2.
        Returns: (completion_response, model_used, was_escalated)
        """
        if force_tier2:
            self.tier2_escalations += 1
            res = self._execute_api(self.tier2_model, messages, tools, max_retries)
            return res, self.tier2_model, True

        # Attempt Tier 1 (Small & Fast)
        self.tier1_invocations += 1
        try:
            res = self._execute_api(self.tier1_model, messages, tools, max_retries)
            msg = res.choices[0].message
            # Quality Gate: Ensure non-empty response or valid tool call
            has_tools = bool(getattr(msg, "tool_calls", None))
            has_content = bool(msg.content and len(msg.content.strip()) > 0)

            if has_tools or has_content:
                return res, self.tier1_model, False

            # If empty/degenerate, trigger escalation
            raise ValueError("Tier 1 produced empty content and no tool calls.")
        except Exception as e:
            # Escalate to Tier 2
            self.tier2_escalations += 1
            print(f"      [Router Escalation] Tier 1 ({self.tier1_model}) failed ({e}). Escalating to Tier 2 ({self.tier2_model})...")
            res_tier2 = self._execute_api(self.tier2_model, messages, tools, max_retries)
            return res_tier2, self.tier2_model, True

    def _execute_api(self, model: str, messages: List[Dict[str, Any]], tools: Any, max_retries: int) -> Any:
        delay = 10.0
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": model,
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
                    print(f"      [Rate-Limit Notice] 429 quota on {model}. Sleeping {sleep_time}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(sleep_time)
                    delay = max(delay * 1.5, 30.0)
                else:
                    raise e
        # Final fallback
        kwargs = {"model": model, "messages": messages, "temperature": 0.1}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)
