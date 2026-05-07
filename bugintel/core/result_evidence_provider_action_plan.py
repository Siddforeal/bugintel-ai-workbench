"""
Action planner for reviewed case-chat provider suggestions.

This module turns a reviewed imported provider suggestion into a safe local
manual action plan. It does not call LLM providers, send requests, execute
tools, launch browsers, use Kali tools, mutate targets, bypass authorization,
or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SuggestionActionPlanItem:
    action: str
    status: str
    manual_order: int
    reason: str
    evidence_needed: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "status": self.status,
            "manual_order": self.manual_order,
            "reason": self.reason,
            "evidence_needed": list(self.evidence_needed),
        }


@dataclass(frozen=True)
class ProviderSuggestionActionPlan:
    recommendation: str
    approved_actions: tuple[SuggestionActionPlanItem, ...]
    evidence_needed_actions: tuple[SuggestionActionPlanItem, ...]
    rejected_actions: tuple[SuggestionActionPlanItem, ...]
    missing_evidence: tuple[str, ...]
    report_guardrails: tuple[str, ...]
    source: str = "result-evidence-provider-suggestion-action-plan"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_provider_suggestion_action_plan",
            "source": self.source,
            "recommendation": self.recommendation,
            "approved_actions": [item.to_dict() for item in self.approved_actions],
            "evidence_needed_actions": [item.to_dict() for item in self.evidence_needed_actions],
            "rejected_actions": [item.to_dict() for item in self.rejected_actions],
            "missing_evidence": list(self.missing_evidence),
            "report_guardrails": list(self.report_guardrails),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Provider Suggestion Action Plan") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            "- Provider execution performed by Blackhole: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Approved Planning Actions",
            "",
        ]

        if self.approved_actions:
            for item in self.approved_actions:
                lines.extend(_render_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Actions Needing Local Evidence", ""])

        if self.evidence_needed_actions:
            for item in self.evidence_needed_actions:
                lines.extend(_render_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected / Unsafe Actions", ""])

        if self.rejected_actions:
            for item in self.rejected_actions:
                lines.extend(_render_item(item))
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence To Close", ""])

        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none listed")

        lines.extend(["", "## Report Wording Guardrails", ""])

        for guardrail in self.report_guardrails:
            lines.append(f"- {guardrail}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- Treat provider suggestions as untrusted planning input.",
                "- Do not execute any action automatically.",
                "- Verify every action against local evidence.",
                "- Do not confirm vulnerabilities from provider text.",
                "",
            ]
        )

        return "\n".join(lines)


def build_provider_suggestion_action_plan(
    provider_review: dict[str, Any],
    case_memory: dict[str, Any] | None = None,
    source: str = "result-evidence-provider-suggestion-action-plan",
) -> ProviderSuggestionActionPlan:
    """Build a safe manual action plan from a reviewed provider suggestion."""
    _require_kind(provider_review, "result_evidence_case_chat_provider_result_review", "provider review")

    if case_memory is not None:
        _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    reviewed_actions = provider_review.get("reviewed_actions")
    if not isinstance(reviewed_actions, list):
        raise ValueError("provider review requires reviewed_actions list")

    missing_evidence = _dedupe(_string_list(provider_review.get("missing_evidence")))
    if case_memory is not None:
        missing_evidence = _dedupe(missing_evidence + _string_list(case_memory.get("missing_evidence")))

    approved: list[SuggestionActionPlanItem] = []
    needs_evidence: list[SuggestionActionPlanItem] = []
    rejected: list[SuggestionActionPlanItem] = []

    order = 1
    for raw in reviewed_actions:
        if not isinstance(raw, dict):
            raise ValueError("each reviewed action must be an object")

        action = str(raw.get("action") or "").strip()
        status = str(raw.get("status") or "").strip()
        reason = str(raw.get("reason") or "").strip() or "No reason provided."

        if not action:
            raise ValueError("each reviewed action requires action text")

        item = SuggestionActionPlanItem(
            action=action,
            status=status,
            manual_order=order,
            reason=reason,
            evidence_needed=tuple(_evidence_needed_for_status(status, missing_evidence)),
        )
        order += 1

        if status == "supported-planning-action":
            approved.append(item)
        elif status == "needs-local-evidence":
            needs_evidence.append(item)
        else:
            rejected.append(item)

    recommendation = _plan_recommendation(provider_review, approved, needs_evidence, rejected, missing_evidence)
    guardrails = _report_guardrails(provider_review, missing_evidence)

    return ProviderSuggestionActionPlan(
        recommendation=recommendation,
        approved_actions=tuple(approved),
        evidence_needed_actions=tuple(needs_evidence),
        rejected_actions=tuple(rejected),
        missing_evidence=tuple(missing_evidence),
        report_guardrails=tuple(guardrails),
        source=source,
    )


def _plan_recommendation(
    provider_review: dict[str, Any],
    approved: list[SuggestionActionPlanItem],
    needs_evidence: list[SuggestionActionPlanItem],
    rejected: list[SuggestionActionPlanItem],
    missing_evidence: list[str],
) -> str:
    review_recommendation = str(provider_review.get("recommendation") or "")

    if "reject" in review_recommendation or rejected:
        return "reject-unsafe-or-overclaimed-actions"

    if missing_evidence or needs_evidence:
        return "execute-approved-manual-actions-and-close-evidence-gaps"

    if approved:
        return "execute-approved-manual-actions"

    return "no-actionable-suggestions"


def _evidence_needed_for_status(status: str, missing_evidence: list[str]) -> list[str]:
    if status == "supported-planning-action":
        return []

    if status == "needs-local-evidence":
        return missing_evidence or ["Local evidence supporting this action"]

    return ["Manual safety review before using this suggestion"]


def _report_guardrails(provider_review: dict[str, Any], missing_evidence: list[str]) -> list[str]:
    guardrails = [
        "Do not claim a confirmed vulnerability from provider suggestions.",
        "Do not claim severity until supported by local evidence.",
        "Do not include provider text as proof.",
        "Only use approved actions as manual planning notes.",
        "Keep final report human-written and evidence-based.",
    ]

    warning_flags = _string_list(provider_review.get("warning_flags"))
    unsupported_claims = _string_list(provider_review.get("unsupported_claims"))

    if warning_flags:
        guardrails.append("Provider output contains warning flags; remove or rewrite unsafe claims.")

    if unsupported_claims:
        guardrails.append("Provider output contains unsupported claims; verify or omit them.")

    if missing_evidence:
        guardrails.append("Close missing evidence before submitting a report.")

    return _dedupe(guardrails)


def _render_item(item: SuggestionActionPlanItem) -> list[str]:
    lines = [
        f"- {item.manual_order}. **{item.status}**: {item.action}",
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


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result
