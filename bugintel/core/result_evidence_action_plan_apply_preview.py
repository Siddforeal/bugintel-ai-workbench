"""
Apply preview for reviewed provider suggestion action plans.

This module turns a v0.60 provider suggestion action plan into a safe local
preview of what could be added to case memory or research state. It does not
write case memory, write research state, call providers, execute tools, launch
browsers, send network requests, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionPlanApplyPreviewItem:
    action: str
    preview_operation: str
    target_artifact: str
    reason: str
    evidence_needed: tuple[str, ...]
    source_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "preview_operation": self.preview_operation,
            "target_artifact": self.target_artifact,
            "reason": self.reason,
            "evidence_needed": list(self.evidence_needed),
            "source_status": self.source_status,
        }


@dataclass(frozen=True)
class ActionPlanApplyPreview:
    recommendation: str
    case_memory_updates: tuple[ActionPlanApplyPreviewItem, ...]
    research_state_updates: tuple[ActionPlanApplyPreviewItem, ...]
    blocked_updates: tuple[ActionPlanApplyPreviewItem, ...]
    missing_evidence: tuple[str, ...]
    report_guardrails: tuple[str, ...]
    source: str = "result-evidence-provider-suggestion-action-plan-apply-preview"
    planning_only: bool = True
    application_state: str = "not_applied"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_provider_suggestion_action_plan_apply_preview",
            "source": self.source,
            "recommendation": self.recommendation,
            "case_memory_updates": [item.to_dict() for item in self.case_memory_updates],
            "research_state_updates": [item.to_dict() for item in self.research_state_updates],
            "blocked_updates": [item.to_dict() for item in self.blocked_updates],
            "missing_evidence": list(self.missing_evidence),
            "report_guardrails": list(self.report_guardrails),
            "planning_only": self.planning_only,
            "application_state": self.application_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "state_mutation": False,
                "case_memory_write": False,
                "research_state_write": False,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Action Plan Apply Preview") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            "- Application performed by Blackhole: false",
            "- Case memory write: false",
            "- Research state write: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Case Memory Update Preview",
            "",
        ]

        if self.case_memory_updates:
            for item in self.case_memory_updates:
                lines.extend(_render_preview_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Research State Update Preview", ""])

        if self.research_state_updates:
            for item in self.research_state_updates:
                lines.extend(_render_preview_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Blocked / Not Applied", ""])

        if self.blocked_updates:
            for item in self.blocked_updates:
                lines.extend(_render_preview_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence", ""])

        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none listed")

        lines.extend(["", "## Report Guardrails", ""])

        if self.report_guardrails:
            for guardrail in self.report_guardrails:
                lines.append(f"- {guardrail}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This is an apply preview only.",
                "- Do not write case memory from this command.",
                "- Do not write research state from this command.",
                "- Do not execute provider suggestions automatically.",
                "- Verify every suggested update against local evidence.",
                "",
            ]
        )

        return "\n".join(lines)


def build_provider_suggestion_action_plan_apply_preview(
    action_plan: dict[str, Any],
    case_memory: dict[str, Any] | None = None,
    source: str = "result-evidence-provider-suggestion-action-plan-apply-preview",
) -> ActionPlanApplyPreview:
    """Build a safe apply preview from a provider suggestion action plan."""
    _require_kind(
        action_plan,
        "result_evidence_provider_suggestion_action_plan",
        "provider suggestion action plan",
    )

    if case_memory is not None:
        _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    approved_actions = _object_list(action_plan.get("approved_actions"), "approved_actions")
    evidence_needed_actions = _object_list(
        action_plan.get("evidence_needed_actions"),
        "evidence_needed_actions",
    )
    rejected_actions = _object_list(action_plan.get("rejected_actions"), "rejected_actions")

    missing_evidence = _dedupe(_string_list(action_plan.get("missing_evidence")))
    if case_memory is not None:
        missing_evidence = _dedupe(missing_evidence + _string_list(case_memory.get("missing_evidence")))

    guardrails = _dedupe(
        _string_list(action_plan.get("report_guardrails"))
        + [
            "Apply preview does not mutate case memory or research state.",
            "Only approved planning actions can become update candidates.",
            "Evidence-needed and rejected actions stay blocked until manually reviewed.",
        ]
    )

    case_memory_updates: list[ActionPlanApplyPreviewItem] = []
    research_state_updates: list[ActionPlanApplyPreviewItem] = []
    blocked_updates: list[ActionPlanApplyPreviewItem] = []

    for raw in approved_actions:
        action = _required_text(raw, "action", "approved action")
        reason = _optional_text(raw.get("reason"), "Approved by provider suggestion review.")
        status = _optional_text(raw.get("status"), "supported-planning-action")

        case_memory_updates.append(
            ActionPlanApplyPreviewItem(
                action=action,
                preview_operation="append_manual_next_action",
                target_artifact="case_memory",
                reason=reason,
                evidence_needed=tuple(_string_list(raw.get("evidence_needed"))),
                source_status=status,
            )
        )
        research_state_updates.append(
            ActionPlanApplyPreviewItem(
                action=action,
                preview_operation="append_planning_task",
                target_artifact="research_state",
                reason=reason,
                evidence_needed=tuple(_string_list(raw.get("evidence_needed"))),
                source_status=status,
            )
        )

    for raw in evidence_needed_actions:
        blocked_updates.append(
            _blocked_item(
                raw,
                preview_operation="block_until_local_evidence_exists",
                default_reason="Action needs local evidence before it can be applied.",
                fallback_evidence=missing_evidence,
            )
        )

    for raw in rejected_actions:
        blocked_updates.append(
            _blocked_item(
                raw,
                preview_operation="block_rejected_or_unsafe_action",
                default_reason="Action was rejected or requires safety review.",
                fallback_evidence=["Manual safety review before using this suggestion"],
            )
        )

    recommendation = _preview_recommendation(
        case_memory_updates,
        research_state_updates,
        blocked_updates,
        missing_evidence,
    )

    return ActionPlanApplyPreview(
        recommendation=recommendation,
        case_memory_updates=tuple(case_memory_updates),
        research_state_updates=tuple(research_state_updates),
        blocked_updates=tuple(blocked_updates),
        missing_evidence=tuple(missing_evidence),
        report_guardrails=tuple(guardrails),
        source=source,
    )


def _preview_recommendation(
    case_memory_updates: list[ActionPlanApplyPreviewItem],
    research_state_updates: list[ActionPlanApplyPreviewItem],
    blocked_updates: list[ActionPlanApplyPreviewItem],
    missing_evidence: list[str],
) -> str:
    if blocked_updates or missing_evidence:
        if case_memory_updates or research_state_updates:
            return "preview-approved-updates-but-keep-blocked-items-unapplied"
        return "no-updates-until-evidence-gaps-close"

    if case_memory_updates or research_state_updates:
        return "preview-approved-updates"

    return "no-applicable-updates"


def _blocked_item(
    raw: dict[str, Any],
    preview_operation: str,
    default_reason: str,
    fallback_evidence: list[str],
) -> ActionPlanApplyPreviewItem:
    action = _required_text(raw, "action", "blocked action")
    reason = _optional_text(raw.get("reason"), default_reason)
    status = _optional_text(raw.get("status"), "blocked")
    evidence = _string_list(raw.get("evidence_needed")) or fallback_evidence

    return ActionPlanApplyPreviewItem(
        action=action,
        preview_operation=preview_operation,
        target_artifact="none",
        reason=reason,
        evidence_needed=tuple(_dedupe(evidence)),
        source_status=status,
    )


def _render_preview_item(item: ActionPlanApplyPreviewItem) -> list[str]:
    lines = [
        f"- **{item.preview_operation}**: {item.action}",
        f"  - Target artifact: {item.target_artifact}",
        f"  - Source status: {item.source_status}",
        f"  - Reason: {item.reason}",
    ]

    if item.evidence_needed:
        lines.append("  - Evidence needed:")
        for evidence in item.evidence_needed:
            lines.append(f"    - {evidence}")

    return lines


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"action plan requires {label} list")

    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"each {label} item must be an object")
        output.append(item)

    return output


def _required_text(data: dict[str, Any], key: str, label: str) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        raise ValueError(f"each {label} requires {key} text")
    return value


def _optional_text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        normalized = item.strip()
        if not normalized:
            continue

        key = normalized.lower()
        if key in seen:
            continue

        seen.add(key)
        output.append(normalized)

    return output
