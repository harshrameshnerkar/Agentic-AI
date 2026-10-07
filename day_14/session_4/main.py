"""
Incident Response & Operational Safety CLI (Day 14 - Session 4).
Demonstrates emergency kill switches, provider circuit breakers,
automated prompt/model rollbacks, and incident runbook enforcement.
"""

import os
import argparse
import json
import re
from typing import Dict, Any

from day_14.session_4.kill_switch_controller import (
    EmergencyKillSwitchController,
    KillSwitchLevel,
    CircuitBreakerState,
    PromptModelConfig,
)


def print_banner(title: str) -> None:
    print("\n" + "=" * 95)
    print(f"{title:^95}")
    print("=" * 95)


def get_default_controller() -> EmergencyKillSwitchController:
    # Baseline verified config (v1.0.0)
    baseline_config = PromptModelConfig(
        version="v1.0.0-stable",
        model_id="claude-3-5-sonnet-20241022",
        prompt_template="You are an SRE incident remediation assistant. Produce raw JSON tool calls only.",
        max_tokens=2048,
    )
    controller = EmergencyKillSwitchController(
        initial_config=baseline_config,
        error_threshold=4,
        recovery_time_seconds=15.0,
    )
    return controller


def defensive_json_parser(raw_response: str) -> Dict[str, Any]:
    """
    Defensive JSON Deserializer implemented following Postmortem INC-2026-0929.
    Strips markdown code fences (```json ... ```) to prevent unhandled parse crashes.
    """
    cleaned = raw_response.strip()
    # Strip leading ```json or ``` and trailing ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def simulate_incident_workflow(controller: EmergencyKillSwitchController) -> None:
    """
    Simulates INC-2026-0929:
    1. Upstream model formatting drift emitting markdown-wrapped JSON.
    2. Naive parser fails, accumulating consecutive errors.
    3. Circuit breaker trips to OPEN.
    4. Kill Switch engages to READ_ONLY.
    5. Rogue destructive action blocked by safety policy.
    6. Rollback to stable verified baseline config.
    """
    print_banner("1. SIMULATING SILENT UPSTREAM PROVIDER DRIFT (INC-2026-0929)")
    print("Active Configuration: version =", controller.active_config.version, "| model =", controller.active_config.model_id)
    print("Initial Kill Switch State :", controller.current_level.value)
    print("Initial Circuit Breaker   :", controller.circuit_state.value)

    # Deploy an experimental prompt version that triggers formatting drift
    regressed_config = PromptModelConfig(
        version="v1.1.0-candidate",
        model_id="claude-3-5-sonnet-latest",  # Floating tag risk!
        prompt_template="Be conversational and format output clearly in markdown codeblocks.",
        max_tokens=2048,
    )
    controller.deploy_config(regressed_config)
    print("\n[DEPLOY] Deployed new candidate configuration:", regressed_config.version)

    # Simulated provider outputs with markdown codeblocks
    simulated_raw_outputs = [
        "```json\n{\"action\": \"check_metrics\", \"service\": \"payment-core\"}\n```",
        "```json\n{\"action\": \"read_logs\", \"service\": \"inventory-api\"}\n```",
        "```json\n{\"action\": \"inspect_k8s_events\", \"namespace\": \"prod\"}\n```",
        "```json\n{\"action\": \"drain_node\", \"node\": \"worker-compute-04\"}\n```",
    ]

    print("\nSimulating 4 consecutive incoming requests processed by unhardened tool dispatcher...")
    for i, raw_output in enumerate(simulated_raw_outputs, 1):
        try:
            # Emulate brittle unhardened parser: json.loads fails on leading ```
            json.loads(raw_output)
            controller.record_provider_result(is_success=True)
            print(f"  Request {i}: [SUCCESS] Parsed cleanly.")
        except json.JSONDecodeError as err:
            controller.record_provider_result(is_success=False, error_message=str(err))
            print(f"  Request {i}: [FAIL] JSONDecodeError: Failed on leading markdown fence '```json'")

    print("\n" + "-" * 95)
    print("Circuit Breaker State Post-Incident :", controller.circuit_state.value)
    print("Kill Switch Level Post-Incident     :", controller.current_level.value)
    print("-" * 95)

    print_banner("2. VERIFYING KILL SWITCH ACTION ENFORCEMENT GATE")
    # Test 1: Read-only action should be permitted under READ_ONLY
    allowed_diag, msg_diag = controller.validate_action_execution("query_telemetry", is_destructive=False)
    print(f"Tool 'query_telemetry' (is_destructive=False) -> {msg_diag}")

    # Test 2: Destructive action MUST BE BLOCKED under READ_ONLY
    allowed_destr, msg_destr = controller.validate_action_execution("drain_node", is_destructive=True)
    print(f"Tool 'drain_node'       (is_destructive=True)  -> {msg_destr}")

    print_banner("3. AUTOMATED ROLLBACK TO LAST KNOWN GOOD (LKG) CONFIGURATION")
    print(f"Pre-Rollback Active Version : {controller.active_config.version}")
    restored = controller.rollback_to_last_known_good(
        reason="Incident INC-2026-0929: Floating tag caused formatting drift",
        operator="sre_incident_commander",
    )
    print(f"Post-Rollback Active Version: {restored.version} (Model: {restored.model_id})")

    # Test defensive parser post-mitigation
    print_banner("4. VERIFYING DEFENSIVE PARSER MITIGATION (ACT-01)")
    test_fence = "```json\n{\"action\": \"query_telemetry\", \"status\": \"resolved\"}\n```"
    parsed_safely = defensive_json_parser(test_fence)
    print(f"Raw Input Payload     : {repr(test_fence)}")
    print(f"Defensively Deserialized: {parsed_safely}")
    print("[PASS] Schema successfully parsed without JSONDecodeError crashes.")

    # Reset kill switch
    controller.set_kill_switch(KillSwitchLevel.NORMAL, reason="Mitigation verified, incident closed.")
    print("\n[RECOVER] Kill switch restored to NORMAL. Operations resumed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Incident Response, Kill Switch & Rollback Manager")
    parser.add_argument("--simulate-incident", action="store_true", help="Run full incident & rollback simulation")
    parser.add_argument("--set-kill-switch", type=str, choices=["NORMAL", "READ_ONLY", "MANDATORY_HITL", "EMERGENCY_SHUTDOWN"], help="Set kill switch level")
    parser.add_argument("--reason", type=str, default="Manual SRE intervention", help="Reason for kill switch action")
    parser.add_argument("--rollback-lkg", action="store_true", help="Emergency rollback to Last Known Good version")
    parser.add_argument("--show-runbook", action="store_true", help="Display Incident Runbook summary")
    parser.add_argument("--show-postmortem", action="store_true", help="Display Postmortem INC-2026-0929 summary")

    args = parser.parse_args()
    controller = get_default_controller()

    if args.set_kill_switch:
        level = KillSwitchLevel(args.set_kill_switch)
        controller.set_kill_switch(level, reason=args.reason)
        print(f"[ACTION] Operational Kill Switch updated to: {controller.current_level.value}")
        print(f"Reason: {args.reason}")
        return

    if args.rollback_lkg:
        restored = controller.rollback_to_last_known_good(reason=args.reason)
        print(f"[ACTION] Successfully rolled back to LKG version: {restored.version} ({restored.model_id})")
        return

    if args.show_runbook:
        runbook_path = os.path.join(os.path.dirname(__file__), "incident_runbook.md")
        if os.path.exists(runbook_path):
            with open(runbook_path, "r", encoding="utf-8") as f:
                print(f.read()[:1500] + "\n...[Full runbook in incident_runbook.md]...")
        return

    if args.show_postmortem:
        pm_path = os.path.join(os.path.dirname(__file__), "postmortem_incident_inc042.md")
        if os.path.exists(pm_path):
            with open(pm_path, "r", encoding="utf-8") as f:
                print(f.read()[:1500] + "\n...[Full postmortem in postmortem_incident_inc042.md]...")
        return

    # Default action: run full simulation
    simulate_incident_workflow(controller)


if __name__ == "__main__":
    main()
