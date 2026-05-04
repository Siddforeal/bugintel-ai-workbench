"""
Result-to-state update bridge for Blackhole AI Workbench.

This module converts result interpretation JSON into a research-state update
plan. It does not call LLM providers, send requests, execute shell commands,
launch browsers, use Kali tools, mutate targets, bypass authorization, or
execute tools.
"""

from __future__ import annotations

from typing import Any

from bugintel.core.research_state_update import (
    ResearchStateUpdatePlan,
    build_research_state_update_plan,
)


def build_update_plan_from_interpretation(
    research_state_data: dict[str, Any],
    interpretation_data: dict[str, Any],
    note: str = "",
) -> ResearchStateUpdatePlan:
    """Build a research-state update plan from result interpretation JSON."""
    endpoint = str(interpretation_data.get("endpoint") or "")
    suggested_result = str(interpretation_data.get("suggested_result") or "needs-more-evidence")

    if suggested_result not in {"supported", "rejected", "needs-more-evidence"}:
        suggested_result = "needs-more-evidence"

    bridge_note = note or _default_note(interpretation_data)

    return build_research_state_update_plan(
        research_state_data=research_state_data,
        endpoint=endpoint,
        validation_result=suggested_result,
        note=bridge_note,
    )


def _default_note(interpretation_data: dict[str, Any]) -> str:
    suggested = str(interpretation_data.get("suggested_result") or "needs-more-evidence")
    confidence = str(interpretation_data.get("confidence") or "unknown")
    rationale = str(interpretation_data.get("rationale") or "")

    return (
        f"Result interpreter suggested {suggested} "
        f"with {confidence} confidence. {rationale}"
    ).strip()
