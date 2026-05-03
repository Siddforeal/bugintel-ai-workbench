"""
Research state patch applier for Blackhole AI Workbench.

This module applies a planning-only research-state update plan to a local copy
of research-state JSON. It does not call LLM providers, send requests, execute
shell commands, launch browsers, use Kali tools, mutate targets, or bypass
authorization.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AppliedResearchStatePatch:
    path: str
    old_value: str | int | bool | None
    new_value: str | int | bool | None
    applied: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchStateApplyResult:
    target_name: str
    endpoint: str
    validation_result: str
    applied_patches: tuple[AppliedResearchStatePatch, ...]
    updated_research_state: dict[str, Any]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "validation_result": self.validation_result,
            "applied_patches": [patch.to_dict() for patch in self.applied_patches],
            "updated_research_state": self.updated_research_state,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


def apply_research_state_update_plan(
    research_state_data: dict[str, Any],
    update_plan_data: dict[str, Any],
) -> ResearchStateApplyResult:
    """Apply a research-state update plan to a local research-state copy."""
    updated = deepcopy(research_state_data)
    target_name = str(update_plan_data.get("target_name") or updated.get("target_name") or "unknown-target")
    endpoint = str(update_plan_data.get("endpoint") or "")
    validation_result = str(update_plan_data.get("validation_result") or "unknown")

    endpoint_state = _find_endpoint_state(updated, endpoint)
    patches: list[AppliedResearchStatePatch] = []

    for action in update_plan_data.get("actions") or []:
        path = str(action.get("path") or "")
        old_value = action.get("old_value")
        new_value = action.get("new_value")
        reason = str(action.get("reason") or "")

        applied = _apply_action(endpoint_state, path, new_value)

        patches.append(
            AppliedResearchStatePatch(
                path=path,
                old_value=old_value,
                new_value=new_value,
                applied=applied,
                reason=reason,
            )
        )

    return ResearchStateApplyResult(
        target_name=target_name,
        endpoint=endpoint,
        validation_result=validation_result,
        applied_patches=tuple(patches),
        updated_research_state=updated,
    )


def _find_endpoint_state(research_state_data: dict[str, Any], endpoint: str) -> dict[str, Any]:
    for item in research_state_data.get("endpoints") or []:
        if item.get("endpoint") == endpoint:
            return item

    new_item = {
        "endpoint": endpoint,
        "triage_state": "unknown",
        "hypotheses": [],
        "artifacts": [],
        "planning_only": True,
        "execution_state": "not_executed",
    }
    research_state_data.setdefault("endpoints", []).append(new_item)
    research_state_data["endpoint_count"] = len(research_state_data["endpoints"])
    return new_item


def _apply_action(endpoint_state: dict[str, Any], path: str, new_value: Any) -> bool:
    if ".triage_state" in path:
        endpoint_state["triage_state"] = new_value
        return True

    if ".validation_note" in path:
        endpoint_state["validation_note"] = new_value
        return True

    hypothesis_index = _extract_index(path, ".hypotheses[")
    if hypothesis_index is not None:
        hypotheses = endpoint_state.setdefault("hypotheses", [])
        if hypothesis_index < len(hypotheses):
            hypotheses[hypothesis_index]["status"] = new_value
            return True
        return False

    artifact_index = _extract_index(path, ".artifacts[")
    if artifact_index is not None:
        artifacts = endpoint_state.setdefault("artifacts", [])
        if artifact_index < len(artifacts):
            artifacts[artifact_index]["status"] = new_value
            return True
        return False

    return False


def _extract_index(path: str, marker: str) -> int | None:
    if marker not in path:
        return None

    tail = path.split(marker, 1)[1]
    raw_index = tail.split("]", 1)[0]

    try:
        return int(raw_index)
    except ValueError:
        return None
