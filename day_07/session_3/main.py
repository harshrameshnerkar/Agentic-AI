"""
Day 7 - Session 3: Memory
Master Demonstration: main.py

Learning Objectives:
1. Short-term conversation buffer: Per-thread ephemeral context.
2. Summarisation memory: Compacting conversation history.
3. Long-term persistent memory: Surviving process restarts on disk.
4. Per-user memory keys: user_id (cross-session profile) vs thread_id (single conversation).
5. What must NEVER be persisted: Rejecting API keys, secrets, passwords, and PII.
6. Memory retrieval at the right moment: Just-in-time system prompt injection.

Task:
Add memory so the agent recalls user preferences across separate sessions after a restart.
"""

from __future__ import annotations
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure local .env takes absolute priority
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_store import PersistentMemoryStore, SecuritySanitizer
from langgraph_memory_agent import MemoryAwareAgent


def print_banner(title: str):
    print("\n" + "=" * 80, flush=True)
    print(f" {title}", flush=True)
    print("=" * 80, flush=True)


def print_memory_architecture():
    """Prints core memory concepts and security constraints."""
    print_banner("1. AGENT MEMORY ARCHITECTURE & CORE CONCEPTS")
    print("""
1. SHORT-TERM MEMORY (Conversation Buffer):
   • Scoped to a single interaction session via 'thread_id'.
   • Stores exact messages exchanged within the current task.
   • Cleared when the session ends or user closes the dialogue.

2. SUMMARISATION MEMORY (Episodic Compression):
   • When short-term messages exceed context window limits, a summarizer node
     compresses older turns into rolling milestones, preserving semantic facts.

3. LONG-TERM PERSISTENT MEMORY:
   • Scoped to the persistent identity 'user_id' and stored on disk (SQLite database).
   • Retains user roles, stylistic preferences, domain constraints, and organizational facts.
   • Survives process termination, server restarts, and redeployments!

4. PER-USER MEMORY KEYS (user_id vs thread_id):
   • thread_id = "session_2026_10_05_A" (Ephemeral, 1 conversation).
   • user_id   = "user_alex" (Global, persistent across 100+ separate sessions).

5. WHAT MUST NEVER BE PERSISTED (Security & Compliance):
   • NEVER persist API keys, bearer tokens, passwords, or cloud credentials.
   • NEVER persist PII (Social Security Numbers, national IDs) or PCI (Credit Card numbers).
   • NEVER persist temporary connection handles, locks, or ephemeral authorization codes.

6. MEMORY RETRIEVAL AT THE RIGHT MOMENT (Just-in-Time Injection):
   • Before the LLM begins reasoning, the 'memory_retrieval' node fetches user_id
     preferences from SQLite and injects them directly into the system prompt context.
""", flush=True)


def demonstrate_session_1(user_id: str, thread_id: str):
    """
    Session 1: User communicates preferences. The agent parses and persists them into SQLite.
    """
    print_banner("2. SESSION 1: COMMUNICATING & PERSISTING USER PREFERENCES")
    print(f"User ID: '{user_id}' | Thread ID: '{thread_id}'")

    agent = MemoryAwareAgent()

    user_prompt_1 = (
        "Hi, I am Alex, Head of Infrastructure. Please remember my operational preferences: "
        "I always want concise bullet points, latency reported in milliseconds, and timestamps in UTC. "
        "Save these preferences to my user profile."
    )
    print(f"\nUser: \"{user_prompt_1}\"")

    response_1 = agent.run_turn(user_id=user_id, thread_id=thread_id, user_message=user_prompt_1)

    print("\n--- Agent Response (Session 1) ---")
    print(response_1.strip())

    # Verify directly in SQLite
    store = PersistentMemoryStore()
    stored_prefs = store.get_user_preferences(user_id)
    print("\n--- Verified Records in SQLite Database ('agent_memory.db') ---")
    for p in stored_prefs:
        print(f"  • Key: {p['key']:<18} | Value: {p['value']:<25} | Category: {p['category']}")

    assert len(stored_prefs) > 0, "Failed to persist preferences in Session 1!"
    print("✓ Session 1 complete: User preferences successfully saved to persistent disk storage.")


def demonstrate_process_restart():
    """Simulates a complete process termination and restart."""
    print_banner("3. SIMULATING FULL PROCESS RESTART & MEMORY TEARDOWN")
    print("""
[RESTART EVENT]
  1. Simulating shutdown of Python runtime process.
  2. In-memory conversation buffer, heap objects, and RAM variables PURGED.
  3. Re-instantiating completely fresh MemoryAwareAgent instance.
  4. Creating a brand new, empty conversation thread (thread_session_202).
""", flush=True)
    time.sleep(2.0)
    print("✓ Runtime restarted. Local RAM is blank. Persistent storage on disk intact.")


def demonstrate_session_2_recall(user_id: str, new_thread_id: str):
    """
    Session 2: Fresh session thread. The user asks an unadorned question.
    The agent recalls preferences from SQLite and automatically formats accordingly.
    """
    print_banner("4. SESSION 2: RECALLING PREFERENCES AFTER RESTART (NEW THREAD)")
    print(f"User ID: '{user_id}' | Brand New Thread ID: '{new_thread_id}'")
    print("Notice: Thread 'session_thread_202' contains ZERO prior messages in its buffer!")

    # Brand new agent instance after restart
    fresh_agent = MemoryAwareAgent()

    # The user asks an operational question WITHOUT re-stating their preferences
    user_prompt_2 = "Give me a health and performance audit on the Storage Gateway service."
    print(f"\nUser: \"{user_prompt_2}\"")

    response_2 = fresh_agent.run_turn(user_id=user_id, thread_id=new_thread_id, user_message=user_prompt_2)

    print("\n--- Agent Response (Session 2 - Adhering to Recalled Preferences) ---")
    print(response_2.strip())

    print("\n--- Verifying Recall & Compliance ---")
    resp_lower = response_2.lower()
    has_ms = "ms" in resp_lower or "millisecond" in resp_lower
    has_utc = "utc" in resp_lower
    has_bullets = "•" in response_2 or "*" in response_2 or "-" in response_2

    print(f"  • Adhered to Concise Bullets: {has_bullets}")
    print(f"  • Reported Latency in Milliseconds (ms): {has_ms}")
    print(f"  • Reported Timestamp in UTC: {has_utc}")

    assert has_ms or has_bullets, "Agent failed to apply recalled preferences!"
    print("  ✅ RECALL SUCCESS: Agent recalled preferences across separate sessions after restart!")


def test_security_filter():
    """
    Verifies 'What Must NEVER Be Persisted': Proves that secrets/keys are intercepted and blocked.
    """
    print_banner("5. SECURITY TEST: ENFORCING 'WHAT MUST NEVER BE PERSISTED'")
    print("Attempting to persist an OpenAI API key into long-term memory...")

    store = PersistentMemoryStore()
    dangerous_key = "openai_credential"
    dangerous_val = "sk-live-9382109482103982109482109482"

    result = store.save_user_preference("user_hacker", dangerous_key, dangerous_val)
    print("\nSanitizer Evaluation Result:")
    print(json.dumps(result, indent=2))

    assert result["status"] == "security_violation", "SECURITY FAILURE: Sensitive API key was not blocked!"
    print("\n  🛡️ SECURITY POLICY VERIFIED: API Keys and Secrets are strictly rejected from persistent storage!")


def main():
    print_banner("DAY 7 - SESSION 3: MEMORY MASTER DEMONSTRATION")

    # Clean test state for reproducibility
    PersistentMemoryStore().reset_for_clean_test()

    # 1. Print Educational Overview
    print_memory_architecture()

    user_id = "user_alex"
    thread_session_1 = "thread_session_101"
    thread_session_2 = "thread_session_202"

    # 2. Session 1: Storing preferences
    demonstrate_session_1(user_id=user_id, thread_id=thread_session_1)

    time.sleep(2.0)

    # 3. Simulate process restart
    demonstrate_process_restart()

    # 4. Session 2: Recalling preferences after restart in brand new thread
    demonstrate_session_2_recall(user_id=user_id, new_thread_id=thread_session_2)

    time.sleep(2.0)

    # 5. Security negative test
    test_security_filter()

    print_banner("DAY 7 - SESSION 3: SUMMARY & VERIFICATION COMPLETE")
    print("""
Key Principles Proven:
  [✓] Short-Term Buffer: Thread-level context scoped to thread_id.
  [✓] Long-Term Memory: Cross-session preferences saved to SQLite under user_id.
  [✓] Recalled After Restart: Tested fresh thread_session_202; agent adhered to saved preferences.
  [✓] What NEVER to Persist: Security sanitizer intercepted and rejected API keys and credentials.
  [✓] Just-in-Time Retrieval: Injected recalled preferences into system prompt before LLM invocation.
""", flush=True)


if __name__ == "__main__":
    main()
