"""
Day 07 - Session 03: Agent Memory & Cross-Session Persistence
Demonstrates persisting user preferences in SQLite, recalling them across
restarts in a new thread, and preventing sensitive secrets from being stored.
"""

from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

from memory_store import PersistentMemoryStore
from langgraph_memory_agent import MemoryAwareAgent


def session_1_store_preferences(user_id: str, thread_id: str):
    print("\n--- Session 1: Storing Preferences ---")
    agent = MemoryAwareAgent()
    prompt = (
        "Hi, I am Alex. Remember my operational preferences: "
        "always use concise bullet points and report latency in milliseconds (ms). "
        "Save these to my user profile."
    )
    print(f"User: {prompt}")
    reply = agent.run_turn(user_id=user_id, thread_id=thread_id, user_message=prompt)
    print(f"Agent:\n{reply.strip()}")

    # Verify directly in SQLite
    store = PersistentMemoryStore()
    prefs = store.get_user_preferences(user_id)
    print(f"Saved preferences in SQLite: {[p['key'] for p in prefs]}")
    assert len(prefs) > 0, "Preferences were not saved."


def session_2_recall_after_restart(user_id: str, new_thread_id: str):
    print("\n--- Session 2: Recalling Preferences in New Session (Simulating Restart) ---")
    fresh_agent = MemoryAwareAgent()
    prompt = "Give me a health check report on the Storage Gateway service."
    print(f"User (in new thread {new_thread_id}): {prompt}")

    reply = fresh_agent.run_turn(user_id=user_id, thread_id=new_thread_id, user_message=prompt)
    print(f"Agent:\n{reply.strip()}")

    resp_lower = reply.lower()
    has_ms = "ms" in resp_lower or "millisecond" in resp_lower
    has_bullets = any(b in reply for b in ["•", "*", "-"])
    print(f"Adhered to saved preferences (ms: {has_ms}, bullets: {has_bullets})")


def test_security_sanitizer():
    print("\n--- Security Check: Rejecting Sensitive Credentials ---")
    store = PersistentMemoryStore()
    result = store.save_user_preference("user_test", "api_key", "sk-live-1234567890abcdef")
    print(f"Attempting to store secret: Status = {result['status']} ({result.get('message', '')})")
    assert result["status"] == "security_violation", "Security check failed: secret was not blocked!"


def main():
    # Reset test database for clean run
    PersistentMemoryStore().reset_for_clean_test()

    user_id = "user_alex"
    session_1_store_preferences(user_id=user_id, thread_id="thread-01")
    session_2_recall_after_restart(user_id=user_id, new_thread_id="thread-02")
    test_security_sanitizer()

    print("\nMemory persistence and security checks verified.")


if __name__ == "__main__":
    main()
