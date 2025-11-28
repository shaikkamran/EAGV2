from __future__ import annotations

import json
from typing import Iterable, Sequence

from agent.agentSession import Step

__all__ = [
    "build_perception_context",
    "build_decision_context",
]


def _stringify(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def build_perception_context(
    *,
    original_user_query: str,
    plan_from_decision_agent: Sequence[str] | None = None,
    current_step_index: int | str | None = None,
    result_of_current_step: str | None = None,
    current_state: str | None = None,
) -> dict:
    plan_text = "\n".join(plan_from_decision_agent) if plan_from_decision_agent else "No plan yet - initial query state"
    state_label = current_state or ("Initial" if not plan_from_decision_agent else "Intermediary")
    if current_step_index is None:
        step_index_value = "N/A - Initial state" if not plan_from_decision_agent else "0"
    else:
        step_index_value = str(current_step_index)
    step_result_text = (
        result_of_current_step
        or ("No result yet - initial query state" if not plan_from_decision_agent else "Result not captured for this step.")
    )

    return {
        "current_state": state_label,
        "original_user_query": original_user_query,
        "plan_from_decision_agent": plan_text,
        "current_step_index": step_index_value,
        "result_of_current_step": step_result_text,
    }


def build_decision_context(
    *,
    plan_mode: str,
    planning_strategy: str,
    original_user_query: str,
    perception_object: dict,
    current_plan_text: Sequence[str] | None,
    completed_steps: Sequence[Step] | None,
    recent_step_feedback: str | None,
    available_tools: Iterable[str] | None,
) -> dict:
    plan_text = "\n".join(current_plan_text) if current_plan_text else "[]"
    completed = [step.to_dict() for step in completed_steps] if completed_steps else []
    tools_text = "\n".join(available_tools) if available_tools else "No registered tools."
    feedback_text = recent_step_feedback or "No feedback yet."

    return {
        "plan_mode": plan_mode,
        "planning_strategy": planning_strategy,
        "original_user_query": original_user_query,
        "perception_object": _stringify(perception_object),
        "current_plan_text": plan_text,
        "completed_steps": _stringify(completed),
        "recent_step_feedback": feedback_text,
        "available_tools": tools_text,
    }

