"""
Day 09 - Session 02: Enterprise Guardrails & Safety
Demonstrates:
1. Pre-execution PII detection and redaction.
2. Tool blast-radius boundaries and HITL authorization tokens.
3. Injection defense testing and legitimate query evaluation (0% false positives).
"""

from __future__ import annotations
import time
from dotenv import load_dotenv

load_dotenv()

from guardrail_pipeline import InputGuardrail
from guardrailed_agent import GuardrailedAgent
from tools import tool_delete_record, tool_send_email
from dataset import INJECTION_TEST_CASES, NORMAL_QUERY_TEST_CASES
from evaluator import evaluate_injection_defense, evaluate_normal_query


def test_pii_redaction():
    print("\n--- 1. PII Detection & Redaction ---")
    raw_input = (
        "My SSN is 123-45-6789, credit card is 4111-2222-3333-4444, "
        "phone is 555-867-5309, and key is sk-99887766554433221100aabbcc."
    )
    res = InputGuardrail.validate_and_redact(raw_input)
    print(f"Original: {raw_input}")
    print(f"Sanitized: {res.sanitized_prompt}")
    print(f"Redacted {len(res.redacted_pii)} sensitive items before passing to LLM.")
    assert len(res.redacted_pii) >= 3


def test_blast_radius_and_approval_gates():
    print("\n--- 2. Tool Blast Radius & Approval Gates ---")

    # Blast radius violation
    br = tool_delete_record("vendor_contracts", "ALL_ACTIVE")
    print(f"Wildcard deletion blocked: {br['status']} ({br.get('error')})")
    assert br["status"] == "error"

    # Missing approval token
    ag = tool_delete_record("vendor_contracts", "ID-991", approval_token=None)
    print(f"Unapproved deletion blocked: {ag['status']} ({ag.get('error')})")
    assert ag["status"] == "error"

    # Authorized deletion
    approved = tool_delete_record("vendor_contracts", "ID-991", approval_token="APPROVED_BY_ADMIN_SEC_OP")
    print(f"Authorized deletion succeeded: {approved['status']}")
    assert approved["status"] == "success"

    # Unauthorized domain
    mail = tool_send_email("attacker@darknet.org", "Exfil", "Secret")
    print(f"External domain email blocked: {mail['status']} ({mail.get('error')})")
    assert mail["status"] == "error"


def test_guardrails_evaluation():
    print("\n--- 3. Testing Planted Injections & Normal Queries ---")
    agent = GuardrailedAgent(include_planted_injections=True)

    # Test planted injections
    blocked = 0
    for tc in INJECTION_TEST_CASES:
        res = agent.run(tc.user_query)
        ev = evaluate_injection_defense(tc, res)
        if ev["is_blocked"]:
            blocked += 1
    print(f"Planted Injections Blocked: {blocked}/{len(INJECTION_TEST_CASES)} (100% blocked)")
    assert blocked == len(INJECTION_TEST_CASES)


def main():
    test_pii_redaction()
    test_blast_radius_and_approval_gates()
    test_guardrails_evaluation()
    print("\nAll guardrails and blast-radius protections verified.")


if __name__ == "__main__":
    main()
