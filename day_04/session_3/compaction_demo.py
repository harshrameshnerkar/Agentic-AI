"""
compaction_demo.py
==================
Educational Demonstration of Context Growth & History Summarization (Compaction).

Addresses:
- Why token growth causes degradation and cost explosion.
- When to trigger history summarization (token threshold / turn count).
- How to preserve critical instructions & latest context while compressing bulky tool results.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import json
from history_manager import ConversationHistoryManager

def run_compaction_experiment():
    print("=" * 80)
    print("DEMO: CONTEXT EXPANSION & HISTORY COMPACTION (WHEN TO SUMMARISE)")
    print("=" * 80)

    system_prompt = "You are an autonomous AI agent managing enterprise database queries and policies."
    manager = ConversationHistoryManager(system_prompt=system_prompt, token_compaction_threshold=600)

    # 1. User starts with initial query
    manager.add_user_message("Analyze all senior engineering salaries, check the Q3 bonus policy, and compute the total bonus liability.")

    # 2. Step 1: Bulky Database Observation
    manager.add_assistant_tool_calls(
        tool_calls=[],
        thought_content="I will query the database for all Engineering department employees."
    )
    # Simulate a verbose database result (many rows)
    bulky_db_payload = {
        "status": "success",
        "records": [
            {"id": 101, "name": "Marcus Vance", "department": "Engineering", "role": "Senior DevOps Engineer", "salary": 135000},
            {"id": 102, "name": "Sarah Connor", "department": "Engineering", "role": "Principal Systems Architect", "salary": 165000},
            {"id": 106, "name": "Maya Patel", "department": "Engineering", "role": "Software Engineer II", "salary": 110000},
            {"id": 107, "name": "Kevin Reed", "department": "Engineering", "role": "Senior Frontend Engineer", "salary": 140000},
            {"id": 108, "name": "Rachel Kim", "department": "Engineering", "role": "Staff Infrastructure Engineer", "salary": 180000},
        ]
    }
    manager.add_tool_result("call_1", "query_database", json.dumps(bulky_db_payload))

    # 3. Step 2: Bulky File Policy Observation
    manager.add_assistant_tool_calls(
        tool_calls=[],
        thought_content="Now I will read the entire compensation bonus policy file to find multiplier rates."
    )
    bulky_policy_text = """
    Enterprise Compensation Policy 2026.
    Engineering Department Tiers:
    - Executive: 25%
    - Principal/Staff: 20%
    - Senior: 12%
    - Mid-Level: 8%
    - Junior: 5%
    Detailed filing requirements: All allocations must include employee ID, verified tax withholding, 
    manager signoff from Department Head, and HR approval via ticket before payroll cutoff date.
    """ * 3  # Repeated to simulate token bloat
    manager.add_tool_result("call_2", "read_file", json.dumps({"status": "success", "content": bulky_policy_text}))

    # 4. Step 3: Calculation turn
    manager.add_assistant_tool_calls(
        tool_calls=[],
        thought_content="Calculating total bonus liability: Marcus (135k*0.12=16.2k) + Sarah (165k*0.20=33k) + Kevin (140k*0.12=16.8k) + Rachel (180k*0.20=36k) = 102,000."
    )
    manager.add_tool_result("call_3", "calculator", json.dumps({"status": "success", "result": 102000}))

    # Inspect Token Growth Before Compaction
    tokens_before = manager.get_total_tokens()
    print("\n[+] Current Context State:")
    print(f"  * Total Messages in Buffer: {len(manager.messages)}")
    print(f"  * Total Tokens in Context:  {tokens_before} tokens")
    print(f"  * Should Compact Policy Met: {manager.should_compact()} (Threshold: {manager.token_compaction_threshold} tokens)")

    # Execute Compaction
    print("\n[!] Triggering Context Compaction...")
    compaction_report = manager.compact_history()

    tokens_after = manager.get_total_tokens()
    print("\n[OK] Post-Compaction State:")
    print(f"  * Total Messages in Buffer: {len(manager.messages)}")
    print(f"  * Tokens After Compaction:  {tokens_after} tokens")
    print(f"  * Tokens Saved:             {compaction_report['tokens_saved']} tokens")
    print(f"  * Reduction Percentage:     {compaction_report['reduction_percentage']}%")
    print(f"  * Injected Summary:         {compaction_report['summary_injected']}")
    print("=" * 80)


if __name__ == "__main__":
    run_compaction_experiment()
