"""
Evaluation Engine: Trajectory Auditing, Final-Answer Evaluation & Failure Taxonomy.
Evaluates agent runs against:
1. Tool Selection Accuracy
2. Argument Accuracy
3. Prerequisite Trajectory Ordering
4. Step Count & Efficiency Limits
5. Final-Answer Semantic Correctness
6. Automated Failure Taxonomy Classification
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from test_cases import TestCase


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    prompt: str
    passed: bool
    trajectory_passed: bool
    final_answer_passed: bool
    tools_called: List[str]
    expected_tools: List[str]
    steps_taken: int
    max_allowed_steps: int
    failure_category: Optional[str] = None
    failure_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class AgentEvaluator:
    """Evaluates agent execution runs across Trajectory and Final Answer dimensions."""

    @classmethod
    def evaluate_case(cls, test_case: TestCase, run_result: Dict[str, Any]) -> EvaluationResult:
        trajectory = run_result.get("trajectory", [])
        tools_called = [step["tool_name"] for step in trajectory]
        final_answer = run_result.get("final_answer", "").lower()
        steps_taken = run_result.get("turns_taken", len(trajectory))

        failure_category = None
        failure_reason = None

        # -------------------------------------------------------------------
        # 1. Trajectory Evaluation: Tool Selection
        # -------------------------------------------------------------------
        missing_tools = [t for t in test_case.expected_tools if t not in tools_called]
        if missing_tools:
            failure_category = "WRONG_TOOL_SELECTION"
            failure_reason = f"Required tool(s) not invoked: {missing_tools}. Tools called: {tools_called}"

        # -------------------------------------------------------------------
        # 2. Trajectory Evaluation: Forbidden Tools Check
        # -------------------------------------------------------------------
        if not failure_category:
            forbidden_used = [t for t in test_case.forbidden_tools if t in tools_called]
            if forbidden_used:
                failure_category = "FORBIDDEN_TOOL_VIOLATION"
                failure_reason = f"Agent invoked forbidden tool(s): {forbidden_used}."

        # -------------------------------------------------------------------
        # 3. Trajectory Evaluation: Argument Accuracy Check
        # -------------------------------------------------------------------
        if not failure_category and test_case.expected_arg_matches:
            for exp_key, exp_val in test_case.expected_arg_matches.items():
                found_arg = False
                for step in trajectory:
                    args = step.get("args", {})
                    # Check if key and value match
                    if exp_key in args and exp_val.lower() in str(args[exp_key]).lower():
                        found_arg = True
                        break
                if not found_arg:
                    failure_category = "ARGUMENT_MALFORMED_ERROR"
                    failure_reason = f"Expected tool argument '{exp_key}={exp_val}' not found in any tool call."
                    break

        # -------------------------------------------------------------------
        # 4. Trajectory Evaluation: Multi-Step Ordering Check
        # -------------------------------------------------------------------
        if not failure_category and len(test_case.expected_tools) > 1:
            # Check if expected tools appear in relative sequence
            indices = []
            for exp_tool in test_case.expected_tools:
                if exp_tool in tools_called:
                    indices.append(tools_called.index(exp_tool))
            if indices != sorted(indices):
                failure_category = "TRAJECTORY_ORDERING_ERROR"
                failure_reason = f"Tools called out of required prerequisite order: {tools_called} vs {test_case.expected_tools}"

        # -------------------------------------------------------------------
        # 5. Trajectory Evaluation: Step Count Budget
        # -------------------------------------------------------------------
        if not failure_category and steps_taken > test_case.max_allowed_steps:
            failure_category = "STEP_LIMIT_EXCEEDED"
            failure_reason = f"Steps taken ({steps_taken}) exceeded budget ({test_case.max_allowed_steps})."

        trajectory_passed = (failure_category is None)

        # -------------------------------------------------------------------
        # 6. Final-Answer Evaluation: Keyword & Semantic Grounding
        # -------------------------------------------------------------------
        final_answer_passed = True
        missing_keywords = []

        if test_case.expected_final_keywords:
            clean_answer = final_answer.replace(",", "")
            any_matched = any(
                kw.lower() in final_answer or kw.lower().replace(",", "") in clean_answer
                for kw in test_case.expected_final_keywords
            )
            if not any_matched:
                final_answer_passed = False
                if not failure_category:
                    failure_category = "INACCURATE_FINAL_ANSWER"
                    failure_reason = f"Final answer missing expected facts: {test_case.expected_final_keywords}."

        # Overall Task Success requires BOTH Trajectory and Final Answer
        overall_passed = trajectory_passed and final_answer_passed

        return EvaluationResult(
            case_id=test_case.case_id,
            category=test_case.category,
            prompt=test_case.prompt,
            passed=overall_passed,
            trajectory_passed=trajectory_passed,
            final_answer_passed=final_answer_passed,
            tools_called=tools_called,
            expected_tools=test_case.expected_tools,
            steps_taken=steps_taken,
            max_allowed_steps=test_case.max_allowed_steps,
            failure_category=failure_category,
            failure_reason=failure_reason,
            details={
                "missing_tools": missing_tools,
                "missing_keywords": missing_keywords,
                "final_answer_snippet": final_answer[:100] + "..." if len(final_answer) > 100 else final_answer,
            },
        )
