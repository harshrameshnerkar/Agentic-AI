"""
history_manager.py
==================
Conversation History Management, Token Growth Tracking & Context Summarization.

Core Learning Concepts Addressed:
1. Proper message serialization (preserving provider metadata like thought_signatures).
2. Tracking Token Growth across multi-step agentic loops.
3. Defining clear policies for WHEN and HOW to summarize conversation history (Context Compaction).
"""

import json
from typing import List, Dict, Any, Optional

try:
    import tiktoken
    _ENCODER = tiktoken.get_encoding("cl100k_base")
    def count_tokens(text: str) -> int:
        return len(_ENCODER.encode(str(text)))
except Exception:
    def count_tokens(text: str) -> int:
        return max(1, len(str(text)) // 4)


class ConversationHistoryManager:
    """
    Manages the multi-turn message buffer for an autonomous tool-calling agent.
    Maintains role ordering, tracks token growth, and provides history summarization.
    """

    def __init__(self, system_prompt: str, token_compaction_threshold: int = 1500):
        self.system_prompt = system_prompt
        self.token_compaction_threshold = token_compaction_threshold
        self.messages: List[Any] = [
            {"role": "system", "content": system_prompt}
        ]
        self.token_history: List[Dict[str, Any]] = []
        self._record_token_snapshot("Initial System Prompt")

    def _estimate_message_tokens(self, msg: Any) -> int:
        """Estimates token footprint of a message (dict or ChatCompletionMessage)."""
        tokens = 4  # Per message framing overhead

        if hasattr(msg, "content"):
            tokens += count_tokens(msg.content or "")
        elif isinstance(msg, dict):
            tokens += count_tokens(msg.get("content") or "")

        # Add tool_calls tokens if present
        tool_calls = None
        if hasattr(msg, "tool_calls"):
            tool_calls = msg.tool_calls
        elif isinstance(msg, dict) and "tool_calls" in msg:
            tool_calls = msg["tool_calls"]

        if tool_calls:
            for tc in tool_calls:
                if hasattr(tc, "function"):
                    tokens += count_tokens(getattr(tc.function, "name", ""))
                    tokens += count_tokens(getattr(tc.function, "arguments", ""))
                elif isinstance(tc, dict):
                    fn = tc.get("function", {})
                    tokens += count_tokens(fn.get("name", ""))
                    tokens += count_tokens(fn.get("arguments", ""))

        return tokens

    def get_total_tokens(self) -> int:
        """Calculates total estimated tokens across all messages currently in context."""
        return sum(self._estimate_message_tokens(m) for m in self.messages)

    def _record_token_snapshot(self, event_description: str):
        total = self.get_total_tokens()
        self.token_history.append({
            "step": len(self.token_history),
            "event": event_description,
            "message_count": len(self.messages),
            "total_tokens": total,
        })

    def add_user_message(self, user_content: str):
        """Appends the user question/task to context."""
        self.messages.append({"role": "user", "content": user_content})
        self._record_token_snapshot("Added User Query")

    def add_assistant_message(self, assistant_msg: Any):
        """
        Appends the assistant response message directly.
        Preserves provider internal attributes (e.g. Gemini thought_signature).
        """
        self.messages.append(assistant_msg)
        tool_calls = getattr(assistant_msg, "tool_calls", None)
        if tool_calls:
            names = ", ".join(tc.function.name for tc in tool_calls)
            self._record_token_snapshot(f"Assistant Requested Tool(s): [{names}]")
        else:
            self._record_token_snapshot("Final Assistant Answer Synthesized")

    def add_tool_result(self, tool_call_id: str, tool_name: str, result_json_str: str):
        """
        Appends a tool observation message matching the specific tool_call_id.
        Passing results back into context as role 'tool'.
        """
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": result_json_str,
        })
        self._record_token_snapshot(f"Returned Result for: {tool_name}")

    def should_compact(self) -> bool:
        """
        Policy: Trigger compaction if total tokens exceed threshold.
        """
        return self.get_total_tokens() > self.token_compaction_threshold

    def compact_history(self, summary_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Compacts past tool turns into a single executive summary observation.
        Retains:
        1. System prompt (instructions)
        2. Original user question (task statement)
        3. Compacted summary of prior tool findings
        4. Latest 2 turns for immediate context continuity.
        """
        initial_tokens = self.get_total_tokens()
        if len(self.messages) <= 4:
            return {"compacted": False, "reason": "History too short to compact"}

        system_msg = self.messages[0]
        user_msg = self.messages[1]
        recent_turns = self.messages[-2:]

        if not summary_text:
            findings = []
            for m in self.messages[2:-2]:
                role = getattr(m, "role", None) if hasattr(m, "role") else (m.get("role") if isinstance(m, dict) else None)
                if role == "tool":
                    name = getattr(m, "name", "tool") if hasattr(m, "name") else m.get("name", "tool")
                    raw = getattr(m, "content", "") if hasattr(m, "content") else m.get("content", "")
                    try:
                        parsed = json.loads(raw)
                        if "records" in parsed:
                            findings.append(f"{name}: retrieved records {parsed['records']}")
                        elif "content" in parsed:
                            findings.append(f"{name}: read relevant policy sections")
                        elif "result" in parsed:
                            findings.append(f"{name}: computed result {parsed['result']}")
                        else:
                            findings.append(f"{name}: executed")
                    except Exception:
                        findings.append(f"{name}: executed")
            summary_text = " | ".join(findings)

        compacted_context_msg = {
            "role": "user",
            "content": f"[Executive Summary of Prior Tool Executions: {summary_text}]"
        }

        self.messages = [system_msg, user_msg, compacted_context_msg] + recent_turns
        final_tokens = self.get_total_tokens()
        saved = initial_tokens - final_tokens
        reduction_pct = (saved / initial_tokens) * 100 if initial_tokens > 0 else 0

        self._record_token_snapshot(f"Compacted History (-{saved} tokens / -{reduction_pct:.1f}%)")

        return {
            "compacted": True,
            "initial_tokens": initial_tokens,
            "final_tokens": final_tokens,
            "tokens_saved": saved,
            "reduction_percentage": round(reduction_pct, 1),
            "summary_injected": summary_text
        }

    def get_messages(self) -> List[Any]:
        """Returns the current messages list ready for the Chat Completions API."""
        return self.messages
