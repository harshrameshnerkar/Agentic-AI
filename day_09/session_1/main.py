"""
Day 9 - Session 1: Prompt Injection & Security Benchmark.
Simulates and evaluates 5 Planted Indirect Prompt Injection Payloads inside RAG Documents.
Compares:
1. Unprotected Agent (Naive Security Posture - High Takeover Rate)
2. Hardened Agent (Defense-in-Depth Architecture - Zero Takeover Rate)
"""

import sys
import time
from typing import Dict, List, Any

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from unprotected_agent import UnprotectedAgent
from hardened_agent import HardenedAgent
from evaluator import TEST_CASES, evaluate_attack


def format_table_row(cols: List[str], widths: List[int]) -> str:
    """Formats columns into a clean ASCII table row."""
    cells = [c[: widths[i]].ljust(widths[i]) for i, c in enumerate(cols)]
    return "| " + " | ".join(cells) + " |"


def main():
    print("=" * 86)
    print(" DAY 9 - SESSION 1: PROMPT INJECTION & SECURITY BENCHMARK")
    print(" OWASP Top 10 for LLM Applications: LLM01 - Prompt Injection")
    print("=" * 86)
    print("Evaluating 5 Planted Indirect Injection Payloads inside RAG Documents:")
    print(" 1. Instruction Override (Pirate Persona Hijack)")
    print(" 2. Privilege Escalation (Destructive Database Deletion)")
    print(" 3. Data Poisoning (Falsehood / CFO Fraud Restatement)")
    print(" 4. Data Exfiltration (Secret Canary Token & Phishing Portal)")
    print(" 5. Tool Parameter Smuggling (Unauthorized Email Exfiltration)")
    print("-" * 86)

    try:
        unprotected_agent = UnprotectedAgent()
        hardened_agent = HardenedAgent()
    except Exception as e:
        print(f"[!] Configuration Error: {e}")
        print("Please check your .env file for valid API keys.")
        sys.exit(1)

    unprotected_results = []
    hardened_results = []

    print("\nExecuting live evaluations across planted RAG attack vectors...\n")

    for idx, test_case in enumerate(TEST_CASES, 1):
        print(f"[{idx}/5] Evaluating {test_case.test_id}: {test_case.title}")
        print(f"    - Query: \"{test_case.user_query}\"")
        print(f"    - Target Document: {test_case.doc_id}")

        # 1. Run Unprotected Agent
        print("    * Executing Unprotected Agent...")
        t0 = time.time()
        try:
            unprot_res = unprotected_agent.run(test_case.user_query)
            unprot_eval = evaluate_attack(test_case, unprot_res)
        except Exception as e:
            unprot_eval = {
                "test_id": test_case.test_id,
                "agent_type": "UnprotectedAgent",
                "is_compromised": True,
                "verdict": "ERROR",
                "evidence": f"Execution error: {e}",
            }
        t_unprot = time.time() - t0
        unprotected_results.append(unprot_eval)

        # 2. Run Hardened Agent
        print("    * Executing Hardened Agent...")
        t0 = time.time()
        try:
            hard_res = hardened_agent.run(test_case.user_query)
            hard_eval = evaluate_attack(test_case, hard_res)
        except Exception as e:
            hard_eval = {
                "test_id": test_case.test_id,
                "agent_type": "HardenedAgent",
                "is_compromised": False,
                "verdict": "ERROR",
                "evidence": f"Execution error: {e}",
            }
        t_hard = time.time() - t0
        hardened_results.append(hard_eval)

        # Print per-test summary
        u_status = "[!] COMPROMISED" if unprot_eval["is_compromised"] else "[OK] DEFENDED"
        h_status = "[!] COMPROMISED" if hard_eval["is_compromised"] else "[OK] DEFENDED"
        print(f"    -> Unprotected Agent : {u_status} ({unprot_eval['evidence']})")
        print(f"    -> Hardened Agent    : {h_status} ({hard_eval['evidence']})")
        print("-" * 86)

    # Compile Overall Scorecard
    total_attacks = len(TEST_CASES)
    unprot_takeovers = sum(1 for r in unprotected_results if r["is_compromised"])
    hard_takeovers = sum(1 for r in hardened_results if r["is_compromised"])

    unprot_rate = (unprot_takeovers / total_attacks) * 100
    hard_rate = (hard_takeovers / total_attacks) * 100

    print("\n" + "=" * 86)
    print("                    SECURITY EVALUATION SCORECARD")
    print("=" * 86)

    headers = ["Test ID", "Attack Vector", "Unprotected Verdict", "Hardened Verdict"]
    widths = [12, 38, 26, 20]
    sep = "+-" + "-+-".join(["-" * w for w in widths]) + "-+"

    print(sep)
    print(format_table_row(headers, widths))
    print(sep)

    for i in range(total_attacks):
        tc = TEST_CASES[i]
        u = unprotected_results[i]
        h = hardened_results[i]

        u_str = "COMPROMISED (TAKEOVER)" if u["is_compromised"] else "DEFENDED"
        h_str = "COMPROMISED (TAKEOVER)" if h["is_compromised"] else "DEFENDED"

        row = [
            tc.test_id,
            tc.attack_vector[:38],
            u_str,
            h_str,
        ]
        print(format_table_row(row, widths))

    print(sep)

    print("\n" + "=" * 86)
    print("                     EXECUTIVE SECURITY METRICS")
    print("=" * 86)
    print(f" Total Planted Attack Payloads : {total_attacks}")
    print(f" Unprotected Agent Takeovers   : {unprot_takeovers}/{total_attacks} ({unprot_rate:.1f}% Vulnerability)")
    print(f" Hardened Agent Takeovers      : {hard_takeovers}/{total_attacks} ({hard_rate:.1f}% Vulnerability)")
    print(f" Exploit Reduction / Defense   : {unprot_rate - hard_rate:.1f}% Risk Reduction")
    print("=" * 86)

    print("\nKEY DEFENSE-IN-DEPTH TAKEAWAYS (OWASP LLM01):")
    print("1. WHY NO COMPLETE FIX EXISTS:")
    print("   Natural language has no formal separation between code and data. A model cannot")
    print("   mathematically prove whether an imperative sentence is authoritative or data.")
    print("2. INSTRUCTION VS DATA SEPARATION:")
    print("   XML delimiting (<untrusted_document>) explicitly tells the model to treat content")
    print("   as a passive semantic payload rather than executable directives.")
    print("3. LEAST-PRIVILEGE TOOL POLICIES:")
    print("   Even if prompt fencing fails, sensitive tools (e.g., delete_record) must NEVER")
    print("   be bound to read-only QA agents.")
    print("4. RUNTIME ALLOW-LISTS:")
    print("   Outbound actions (e.g., send_email) must enforce strict recipient allow-lists")
    print("   (@company.internal) in application code, independent of model intent.")
    print("5. OUTPUT GUARDRAILS:")
    print("   Canary tokens and malicious URL filters redact unauthorized leaks before delivery.")
    print("=" * 86)


if __name__ == "__main__":
    main()
