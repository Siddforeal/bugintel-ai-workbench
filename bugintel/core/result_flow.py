"""
Result flow for Blackhole AI Workbench.

This module combines result interpretation, research-state update planning, and
local research-state patch application. It does not call LLM providers, send
requests, execute shell commands, launch browsers, use Kali tools, mutate
targets, bypass authorization, or execute tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.result_interpreter import ResultInterpretation, interpret_validation_result
from bugintel.core.result_update_bridge import build_update_plan_from_interpretation
from bugintel.core.research_state_apply import (
    ResearchStateApplyResult,
    apply_research_state_update_plan,
)
from bugintel.core.research_state_update import ResearchStateUpdatePlan


@dataclass(frozen=True)
class ResultFlow:
    endpoint: str
    interpretation: ResultInterpretation
    update_plan: ResearchStateUpdatePlan
    apply_result: ResearchStateApplyResult
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "interpretation": self.interpretation.to_dict(),
            "update_plan": self.update_plan.to_dict(),
            "apply_result": self.apply_result.to_dict(),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


def build_result_flow(
    research_state_data: dict[str, Any],
    endpoint: str,
    observed_status: int | None = None,
    expected_status: int | None = None,
    observed_body: str = "",
    expected_body: str = "",
    note: str = "",
) -> ResultFlow:
    """Build a complete local result flow from manual validation summary."""
    interpretation = interpret_validation_result(
        endpoint=endpoint,
        observed_status=observed_status,
        expected_status=expected_status,
        observed_body=observed_body,
        expected_body=expected_body,
        note=note,
    )

    update_plan = build_update_plan_from_interpretation(
        research_state_data=research_state_data,
        interpretation_data=interpretation.to_dict(),
        note=note,
    )

    apply_result = apply_research_state_update_plan(
        research_state_data=research_state_data,
        update_plan_data=update_plan.to_dict(),
    )

    return ResultFlow(
        endpoint=endpoint,
        interpretation=interpretation,
        update_plan=update_plan,
        apply_result=apply_result,
    )
