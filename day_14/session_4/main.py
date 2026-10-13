"""
Day 14 - Session 04: Incident Response & Operational Safety
Demonstrates:
1. Upstream model drift detection triggering circuit breaker trips.
2. Emergency kill switch action gating (blocking destructive actions).
3. Automated rollback to Last Known Good (LKG) prompt/model configuration.
4. Defensive markdown-strip JSON deserialization.
"""

from __future__ import annotations
import json
import re
from kill_switch_controller import (
    EmergencyKillSwitchController,
    KillSwitchLevel,
    PromptModelConfig,
)


def defensive_json_parser(raw: str):
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def main():
    print("Day 14 Session 04: Incident Response & Operational Kill Switch\n")

    baseline = PromptModelConfig(
        version="v1.0.0-stable",
        model_id="claude-3-5-sonnet-20241022",
        prompt_template="Produce raw JSON tool calls only.",
        max_tokens=2048,
    )
    controller = EmergencyKillSwitchController(
        initial_config=baseline,
        error_threshold=4,
        recovery_time_seconds=15.0,
    )

    # 1. Simulating candidate drift causing parse errors
    regressed = PromptModelConfig(
        version="v1.1.0-candidate",
        model_id="claude-3-5-sonnet-latest",
        prompt_template="Format output in markdown codeblocks.",
        max_tokens=2048,
    )
    controller.deploy_config(regressed)

    for _ in range(4):
        controller.record_provider_result(is_success=False, error_message="JSONDecodeError on markdown fence")

    print(f"Circuit Breaker State: {controller.circuit_state.value}")
    print(f"Kill Switch Level:     {controller.current_level.value}")

    # 2. Verify gating
    _, msg_diag = controller.validate_action_execution("query_telemetry", is_destructive=False)
    _, msg_destr = controller.validate_action_execution("drain_node", is_destructive=True)
    print(f"Read-Only Action:   {msg_diag}")
    print(f"Destructive Action: {msg_destr}")

    # 3. Rollback
    restored = controller.rollback_to_last_known_good(reason="Formatting drift", operator="sre_oncall")
    print(f"Rolled back to LKG: {restored.version}")

    # 4. Defensive parser test
    parsed = defensive_json_parser("```json\n{\"action\": \"query_telemetry\"}\n```")
    print(f"Defensive JSON parser result: {parsed}")
    assert parsed["action"] == "query_telemetry"

    print("\nIncident response and safety controls verified.")


if __name__ == "__main__":
    main()
