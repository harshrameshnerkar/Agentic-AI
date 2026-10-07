"""
Emergency Kill Switch and Automated Rollback Controller for Production Agents.
Provides multi-level kill switches, provider circuit breakers, and configuration rollback.
"""

from enum import Enum
from typing import Dict, Optional, Any, Callable
import datetime


class KillSwitchLevel(str, Enum):
    NORMAL = "NORMAL"  # All tools and models operating normally
    READ_ONLY = "READ_ONLY"  # Destructive/mutating tools blocked, read-only permitted
    MANDATORY_HITL = "MANDATORY_HITL"  # All tool calls require human approval
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"  # Agent completely frozen, returns fallback response


class CircuitBreakerState(str, Enum):
    CLOSED = "CLOSED"  # Healthy, traffic flows
    OPEN = "OPEN"  # Tripped, traffic blocked / redirected to fallback
    HALF_OPEN = "HALF_OPEN"  # Probing for recovery


class PromptModelConfig:
    def __init__(self, version: str, model_id: str, prompt_template: str, max_tokens: int = 2048):
        self.version = version
        self.model_id = model_id
        self.prompt_template = prompt_template
        self.max_tokens = max_tokens
        self.updated_at = datetime.datetime.now(datetime.timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "model_id": self.model_id,
            "prompt_template": self.prompt_template,
            "max_tokens": self.max_tokens,
            "updated_at": self.updated_at.isoformat(),
        }


class EmergencyKillSwitchController:
    """
    Central operational safety controller for agentic deployments.
    Manages operational kill switch levels, provider circuit breakers, and configuration rollbacks.
    """

    def __init__(
        self,
        initial_config: PromptModelConfig,
        error_threshold: int = 5,
        recovery_time_seconds: float = 30.0,
    ) -> None:
        self.current_level = KillSwitchLevel.NORMAL
        self.active_config = initial_config
        self.config_history: Dict[str, PromptModelConfig] = {initial_config.version: initial_config}
        self.last_known_good_version: str = initial_config.version

        # Circuit breaker parameters
        self.circuit_state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.error_threshold = error_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.last_failure_time: Optional[datetime.datetime] = None

        # Audit log of safety actions
        self.safety_audit_log: list[Dict[str, Any]] = []

    def set_kill_switch(self, level: KillSwitchLevel, reason: str, operator: str = "sre_oncall") -> None:
        """Sets the global operational kill switch level."""
        previous = self.current_level
        self.current_level = level
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event": "KILL_SWITCH_ENGAGED",
            "previous_level": previous.value,
            "new_level": level.value,
            "reason": reason,
            "operator": operator,
        }
        self.safety_audit_log.append(event)

    def record_provider_result(self, is_success: bool, error_message: Optional[str] = None) -> None:
        """Tracks provider errors and trips circuit breaker when threshold is crossed."""
        now = datetime.datetime.now(datetime.timezone.utc)

        if is_success:
            if self.circuit_state == CircuitBreakerState.HALF_OPEN:
                self.circuit_state = CircuitBreakerState.CLOSED
                self.consecutive_failures = 0
                self._log_event("CIRCUIT_BREAKER_RESET", "Provider recovered, circuit breaker closed.")
            elif self.circuit_state == CircuitBreakerState.CLOSED:
                self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.last_failure_time = now

            if self.circuit_state == CircuitBreakerState.CLOSED and self.consecutive_failures >= self.error_threshold:
                self.circuit_state = CircuitBreakerState.OPEN
                self.set_kill_switch(
                    KillSwitchLevel.READ_ONLY,
                    reason=f"Provider circuit breaker tripped: {self.consecutive_failures} consecutive failures. Error: {error_message}",
                    operator="circuit_breaker_daemon",
                )
                self._log_event("CIRCUIT_BREAKER_TRIPPED", f"Tripped after {self.consecutive_failures} failures.")

    def check_circuit_breaker(self) -> CircuitBreakerState:
        """Evaluates circuit breaker state and checks if cooloff recovery time has elapsed."""
        if self.circuit_state == CircuitBreakerState.OPEN and self.last_failure_time:
            elapsed = (datetime.datetime.now(datetime.timezone.utc) - self.last_failure_time).total_seconds()
            if elapsed >= self.recovery_time_seconds:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                self._log_event("CIRCUIT_BREAKER_PROBING", "Cooloff expired. Entering HALF_OPEN state.")
        return self.circuit_state

    def deploy_config(self, new_config: PromptModelConfig) -> None:
        """Deploys a new prompt/model configuration version."""
        self.config_history[new_config.version] = new_config
        self.active_config = new_config
        self._log_event("CONFIG_DEPLOYED", f"Deployed configuration version {new_config.version}")

    def rollback_to_version(self, target_version: str, reason: str, operator: str = "sre_oncall") -> PromptModelConfig:
        """Rolls back prompt/model configuration to a specific target version."""
        if target_version not in self.config_history:
            raise ValueError(f"Version '{target_version}' not found in configuration history.")

        previous_version = self.active_config.version
        self.active_config = self.config_history[target_version]
        self._log_event(
            "CONFIG_ROLLBACK",
            f"Rolled back from {previous_version} to {target_version}. Reason: {reason}. Operator: {operator}",
        )
        return self.active_config

    def rollback_to_last_known_good(self, reason: str, operator: str = "sre_oncall") -> PromptModelConfig:
        """Emergency rollback to the last verified stable version."""
        return self.rollback_to_version(self.last_known_good_version, reason, operator)

    def mark_current_as_known_good(self) -> None:
        """Marks active configuration as the verified baseline."""
        self.last_known_good_version = self.active_config.version
        self._log_event("BASELINE_VERIFIED", f"Marked {self.active_config.version} as last known good.")

    def validate_action_execution(self, tool_name: str, is_destructive: bool) -> tuple[bool, str]:
        """
        Policy enforcement gate:
        Checks whether tool execution is permitted under current kill switch level.
        """
        if self.current_level == KillSwitchLevel.EMERGENCY_SHUTDOWN:
            return False, "BLOCKED: Emergency kill switch engaged. All agent execution suspended."

        if self.current_level == KillSwitchLevel.READ_ONLY and is_destructive:
            return False, f"BLOCKED: Kill switch is in READ_ONLY mode. Destructive action '{tool_name}' prohibited."

        if self.current_level == KillSwitchLevel.MANDATORY_HITL:
            return False, f"ESCALATED: Mandatory HITL mode active. Tool '{tool_name}' queued for human approval."

        return True, "ALLOWED: Execution permitted."

    def _log_event(self, event_type: str, details: str) -> None:
        self.safety_audit_log.append({
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event": event_type,
            "details": details,
        })
