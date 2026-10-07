"""
Day 6 - Session 3: Multi-Step Tool Use
Module: history_manager.py

Tracks conversation history growth and provides intelligent summarization / truncation:
1. Turn-by-turn token & character growth telemetry.
2. Truncation of large intermediate payloads (e.g., massive database records or verbose API responses).
3. Context compaction: Summarizing multi-turn tool observations into a milestone summary to prevent token blowout.
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Tuple


class HistoryGrowthTracker:
    """
    Monitors message list size, estimates tokens, and executes compaction strategies.
    """

    def __init__(self, token_compaction_threshold: int = 1500):
        self.compaction_threshold = token_compaction_threshold
        self.growth_log: List[Dict[str, Any]] = []

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimate based on standard ~4 characters per token."""
        return max(1, len(text) // 4)

    def measure_history(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates total characters, estimated tokens, and message role breakdown.
        """
        total_chars = 0
        role_counts = {"system": 0, "user": 0, "assistant": 0, "tool": 0}

        for msg in messages:
            # Handle dictionary or ChatCompletionMessage object
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "unknown")
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            if content is None:
                content = ""
            
            tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
            tool_call_str = json.dumps([str(tc) for tc in tool_calls]) if tool_calls else ""

            msg_chars = len(str(content)) + len(tool_call_str)
            total_chars += msg_chars
            if role in role_counts:
                role_counts[role] += 1

        est_tokens = self.estimate_tokens(" " * total_chars)
        metric = {
            "message_count": len(messages),
            "role_breakdown": role_counts,
            "total_chars": total_chars,
            "estimated_tokens": est_tokens,
            "compaction_recommended": est_tokens >= self.compaction_threshold
        }
        self.growth_log.append(metric)
        return metric

    @staticmethod
    def truncate_payload(data: Any, max_chars: int = 400) -> str:
        """
        Truncates verbose observation data, returning a clean preview with omission indicators.
        """
        text = json.dumps(data) if not isinstance(data, str) else data
        if len(text) <= max_chars:
            return text
        head = text[: max_chars - 50]
        tail = text[-30:]
        omitted = len(text) - (len(head) + len(tail))
        return f"{head} ... [TRUNCATED {omitted} CHARS] ... {tail}"

    def compact_completed_tools(
        self,
        messages: List[Dict[str, Any]],
        keep_recent_turns: int = 2
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Summarizes older intermediate tool results into a compact milestone summary,
        drastically reducing token footprint while retaining crucial facts.
        """
        current_metrics = self.measure_history(messages)
        if not current_metrics["compaction_recommended"]:
            return messages, False

        # If compaction threshold crossed, compress older tool observation messages
        system_msgs = [m for m in messages if (getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else "")) == "system"]
        user_msgs = [m for m in messages if (getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else "")) == "user"]
        other_msgs = [m for m in messages if m not in system_msgs and m not in user_msgs]

        if len(other_msgs) <= keep_recent_turns * 2:
            return messages, False

        # Preserve the initial instructions and recent interactions, summarize intermediate steps
        older = other_msgs[:-keep_recent_turns * 2]
        recent = other_msgs[-keep_recent_turns * 2:]

        extracted_facts = []
        for msg in older:
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "")
            if role == "tool":
                name = getattr(msg, "name", None) or (msg.get("name") if isinstance(msg, dict) else "tool")
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
                try:
                    parsed = json.loads(content)
                    status = parsed.get("status", "unknown")
                    # Extract high-signal key facts
                    keys = [f"{k}={v}" for k, v in list(parsed.items())[:3] if k != "status"]
                    extracted_facts.append(f"{name} ({status}): {', '.join(keys)}")
                except Exception:
                    extracted_facts.append(f"{name}: observation preserved")

        milestone_content = "[CONTEXT COMPACTION MILESTONE]: Earlier multi-step execution verified: " + "; ".join(extracted_facts)
        compacted_summary_msg = {
            "role": "system",
            "content": milestone_content
        }

        compacted_messages = system_msgs + user_msgs + [compacted_summary_msg] + recent
        return compacted_messages, True
