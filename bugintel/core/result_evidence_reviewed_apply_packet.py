"""
Reviewed apply packet for case-chat apply preview reviews.

This module turns a v0.62 apply-preview review into a final human approval
packet. It separates approved planning-note updates, duplicate items, blocked
items, evidence gaps, unsafe/rejected items, report guardrails, and a final
human approval checklist.

It does not write case memory, write research state, call providers, execute
tools, launch browsers, send network requests, mutate targets, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewedApplyPacketItem:
    action: str
    status: str
    source_category: str
    source: str
    severity: str
    reason: str
    evidence_needed: tuple[str, ...]
    checklist: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "status": self.status,
            "source_category": self.source_category,
            "source": self.source,
            "severity": self.severity,
            "reason": self.reason,
            "evidence_needed": list(self.evidence_needed),
            "checklist": list(self.checklist),
        }


@dataclass(frozen=True)
class ReviewedApplyPacket:
    recommendation: str
    approved_planning_updates: tuple[ReviewedApplyPacketItem, ...]
    duplicate_updates: tuple[ReviewedApplyPacketItem, ...]
    blocked_updates: tuple[ReviewedApplyPacketItem, ...]
    evidence_gaps: tuple[ReviewedApplyPacketItem, ...]
    unsafe_or_rejected_items: tuple[ReviewedApplyPacketItem, ...]
    overclaim_risks: tuple[ReviewedApplyPacketItem, ...]
    report_guardrails: tuple[str, ...]
    human_approval_checklist: tuple[str, ...]
    source: str = "result-evidence-reviewed-apply-packet"
    planning_only: bool = True
    approval_state: str = "awaiting_human_approval"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_reviewed_apply_packet",
            "source": self.source,
            "recommendation": self.recommendation,
            "approved_planning_updates": [
                item.to_dict() for item in self.approved_planning_updates
            ],
            "duplicate_updates": [item.to_dict() for item in self.duplicate_updates],
            "blocked_updates": [item.to_dict() for item in self.blocked_updates],
            "evidence_gaps": [item.to_dict() for item in self.evidence_gaps],
            "unsafe_or_rejected_items": [
                item.to_dict() for item in self.unsafe_or_rejected_items
            ],
            "overclaim_risks": [item.to_dict() for item in self.overclaim_risks],
            "report_guardrails": list(self.report_guardrails),
            "human_approval_checklist": list(self.human_approval_checklist),
            "planning_only": self.planning_only,
            "approval_state": self.approval_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "human_approval_required": True,
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

    def to_markdown(self, title: str = "Reviewed Apply Packet") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            f"- Approval state: {self.approval_state}",
            "- Human approval required: true",
            "- State mutation performed by Blackhole: false",
            "- Case memory write: false",
            "- Research state write: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Approved Planning-Note Updates",
            "",
        ]

        lines.extend(_render_items(self.approved_planning_updates))
        lines.extend(["", "## Duplicate Updates", ""])
        lines.extend(_render_items(self.duplicate_updates))
        lines.extend(["", "## Blocked Updates", ""])
        lines.extend(_render_items(self.blocked_updates))
        lines.extend(["", "## Evidence Gaps", ""])
        lines.extend(_render_items(self.evidence_gaps))
        lines.extend(["", "## Unsafe / Rejected Items", ""])
        lines.extend(_render_items(self.unsafe_or_rejected_items))
        lines.extend(["", "## Report Overclaim Risks", ""])
        lines.extend(_render_items(self.overclaim_risks))

        lines.extend(["", "## Report Guardrails", ""])
        if self.report_guardrails:
            for guardrail in self.report_guardrails:
                lines.append(f"- {guardrail}")
        else:
            lines.append("- none")

        lines.extend(["", "## Human Approval Checklist", ""])
        for item in self.human_approval_checklist:
            lines.append(f"- [ ] {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This packet is for human approval only.",
                "- Do not write case memory from this packet.",
                "- Do not write research state from this packet.",
                "- Do not treat approved planning notes as vulnerability proof.",
                "- Do not apply unsafe, blocked, duplicate, or evidence-gap items automatically.",
                "",
            ]
        )

        return "\n".join(lines)


def build_reviewed_apply_packet(
    apply_preview_review: dict[str, Any],
    case_memory: dict[str, Any] | None = None,
    source: str = "result-evidence-reviewed-apply-packet",
) -> ReviewedApplyPacket:
    """Build a final human approval packet from an apply-preview review."""
    _require_kind(
        apply_preview_review,
        "result_evidence_action_plan_apply_preview_review",
        "action plan apply preview review",
    )

    if case_memory is not None:
        _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    duplicate_findings = _object_list(
        apply_preview_review.get("duplicate_update_candidates"),
        "duplicate_update_candidates",
    )
    blocked_findings = _object_list(
        apply_preview_review.get("blocked_action_findings"),
        "blocked_action_findings",
    )
    evidence_gap_findings = _object_list(
        apply_preview_review.get("evidence_gap_findings"),
        "evidence_gap_findings",
    )
    unsafe_findings = _object_list(
        apply_preview_review.get("unsafe_update_findings"),
        "unsafe_update_findings",
    )
    overclaim_findings = _object_list(
        apply_preview_review.get("overclaim_risks"),
        "overclaim_risks",
    )
    safe_notes = _object_list(
        apply_preview_review.get("safe_planning_notes"),
        "safe_planning_notes",
    )

    report_guardrails = _dedupe(
        _string_list(apply_preview_review.get("report_guardrails"))
        + [
            "Reviewed apply packet does not mutate case memory or research state.",
            "Human approval is required before any future apply step.",
            "Approved planning notes are not vulnerability proof.",
        ]
    )

    existing_case_memory_actions = _known_case_memory_actions(case_memory)
    duplicate_actions = {
        _normalize_action(_optional_text(item.get("action"), ""))
        for item in duplicate_findings
        if _optional_text(item.get("action"), "")
    }
    unsafe_actions = {
        _normalize_action(_optional_text(item.get("action"), ""))
        for item in unsafe_findings
        if _optional_text(item.get("action"), "")
    }
    existing_actions = {_normalize_action(action) for action in existing_case_memory_actions}

    approved_updates: list[ReviewedApplyPacketItem] = []
    duplicate_updates: list[ReviewedApplyPacketItem] = []
    blocked_updates: list[ReviewedApplyPacketItem] = []
    evidence_gaps: list[ReviewedApplyPacketItem] = []
    unsafe_items: list[ReviewedApplyPacketItem] = []
    overclaim_items: list[ReviewedApplyPacketItem] = []

    for raw in safe_notes:
        action = _required_text(raw, "action", "safe planning note")
        normalized = _normalize_action(action)

        item = _packet_item(
            raw,
            status="approved-planning-note",
            default_reason="Safe planning note from apply-preview review.",
            checklist=(
                "Confirm this remains a planning note only.",
                "Verify it does not duplicate existing case memory.",
                "Do not treat it as vulnerability proof.",
            ),
        )

        if normalized in duplicate_actions or normalized in existing_actions:
            duplicate_updates.append(
                _packet_item(
                    raw,
                    status="duplicate-review-required",
                    default_reason="Safe note overlaps with duplicate findings or existing case memory.",
                    checklist=(
                        "Compare against existing case memory.",
                        "Keep only one copy if a future apply step is built.",
                    ),
                )
            )
        elif normalized in unsafe_actions:
            unsafe_items.append(
                _packet_item(
                    raw,
                    status="unsafe-review-required",
                    default_reason="Safe note overlaps with unsafe findings.",
                    checklist=(
                        "Manually review the unsafe wording.",
                        "Do not approve this item until the risk is removed.",
                    ),
                )
            )
        else:
            approved_updates.append(item)

    duplicate_updates.extend(
        _packet_item(
            raw,
            status="duplicate-review-required",
            default_reason="Duplicate update candidate requires manual deduplication.",
            checklist=(
                "Check whether this already exists in case memory.",
                "Do not approve duplicate state updates.",
            ),
        )
        for raw in duplicate_findings
    )

    blocked_updates.extend(
        _packet_item(
            raw,
            status="blocked-needs-review",
            default_reason="Blocked item must not be applied automatically.",
            checklist=(
                "Close required local evidence before approval.",
                "Keep this blocked until a human explicitly approves it.",
            ),
        )
        for raw in blocked_findings
    )

    evidence_gaps.extend(
        _packet_item(
            raw,
            status="evidence-gap-open",
            default_reason="Evidence gap must be closed before report or future apply.",
            checklist=(
                "Collect local evidence.",
                "Re-run review after evidence is available.",
            ),
        )
        for raw in evidence_gap_findings
    )

    unsafe_items.extend(
        _packet_item(
            raw,
            status="unsafe-or-rejected",
            default_reason="Unsafe or rejected item must remain blocked.",
            checklist=(
                "Do not apply this item automatically.",
                "Rewrite or remove unsafe wording before any future approval.",
            ),
        )
        for raw in unsafe_findings
    )

    overclaim_items.extend(
        _packet_item(
            raw,
            status="report-overclaim-risk",
            default_reason="Report overclaim risk must be resolved before submission.",
            checklist=(
                "Do not claim confirmed vulnerability without local proof.",
                "Do not claim severity until evidence supports it.",
            ),
        )
        for raw in overclaim_findings
    )

    recommendation = _packet_recommendation(
        approved_updates=approved_updates,
        duplicate_updates=duplicate_updates,
        blocked_updates=blocked_updates,
        evidence_gaps=evidence_gaps,
        unsafe_items=unsafe_items,
        overclaim_items=overclaim_items,
    )

    checklist = _approval_checklist(
        approved_updates=approved_updates,
        duplicate_updates=duplicate_updates,
        blocked_updates=blocked_updates,
        evidence_gaps=evidence_gaps,
        unsafe_items=unsafe_items,
        overclaim_items=overclaim_items,
    )

    return ReviewedApplyPacket(
        recommendation=recommendation,
        approved_planning_updates=tuple(_dedupe_items(approved_updates)),
        duplicate_updates=tuple(_dedupe_items(duplicate_updates)),
        blocked_updates=tuple(_dedupe_items(blocked_updates)),
        evidence_gaps=tuple(_dedupe_items(evidence_gaps)),
        unsafe_or_rejected_items=tuple(_dedupe_items(unsafe_items)),
        overclaim_risks=tuple(_dedupe_items(overclaim_items)),
        report_guardrails=tuple(report_guardrails),
        human_approval_checklist=tuple(checklist),
        source=source,
    )


def _packet_recommendation(
    approved_updates: list[ReviewedApplyPacketItem],
    duplicate_updates: list[ReviewedApplyPacketItem],
    blocked_updates: list[ReviewedApplyPacketItem],
    evidence_gaps: list[ReviewedApplyPacketItem],
    unsafe_items: list[ReviewedApplyPacketItem],
    overclaim_items: list[ReviewedApplyPacketItem],
) -> str:
    if unsafe_items:
        return "human-approval-required-block-unsafe-items"

    if blocked_updates or evidence_gaps or overclaim_items:
        if approved_updates:
            return "approve-safe-planning-notes-only"
        return "hold-packet-until-evidence-gaps-close"

    if duplicate_updates:
        if approved_updates:
            return "approve-safe-notes-after-deduplication"
        return "dedupe-before-approval"

    if approved_updates:
        return "ready-for-human-approval-as-planning-notes"

    return "no-items-ready-for-approval"


def _approval_checklist(
    approved_updates: list[ReviewedApplyPacketItem],
    duplicate_updates: list[ReviewedApplyPacketItem],
    blocked_updates: list[ReviewedApplyPacketItem],
    evidence_gaps: list[ReviewedApplyPacketItem],
    unsafe_items: list[ReviewedApplyPacketItem],
    overclaim_items: list[ReviewedApplyPacketItem],
) -> list[str]:
    checklist = [
        "Confirm this packet is being used as planning input only.",
        "Confirm no state file is written by this command.",
        "Confirm no provider, browser, curl, Kali, or network action is executed.",
        "Confirm no vulnerability is marked as confirmed from this packet.",
    ]

    if approved_updates:
        checklist.append("Review approved planning-note updates before any future apply workflow.")

    if duplicate_updates:
        checklist.append("Deduplicate repeated or existing updates before future approval.")

    if blocked_updates:
        checklist.append("Keep blocked updates out of any future apply workflow until reviewed.")

    if evidence_gaps:
        checklist.append("Close evidence gaps before reporting or applying related items.")

    if unsafe_items:
        checklist.append("Reject or rewrite unsafe/rejected items before any future approval.")

    if overclaim_items:
        checklist.append("Remove report overclaim risks before drafting or submitting reports.")

    return _dedupe(checklist)


def _packet_item(
    raw: dict[str, Any],
    status: str,
    default_reason: str,
    checklist: tuple[str, ...],
) -> ReviewedApplyPacketItem:
    action = _required_text(raw, "action", "packet item")
    return ReviewedApplyPacketItem(
        action=action,
        status=status,
        source_category=_optional_text(raw.get("category"), status),
        source=_optional_text(raw.get("source"), "apply_preview_review"),
        severity=_optional_text(raw.get("severity"), "info"),
        reason=_optional_text(raw.get("message"), default_reason),
        evidence_needed=tuple(_string_list(raw.get("evidence_needed"))),
        checklist=checklist,
    )


def _known_case_memory_actions(case_memory: dict[str, Any] | None) -> list[str]:
    if not case_memory:
        return []

    candidates: list[str] = []
    for key in (
        "manual_next_actions",
        "next_actions",
        "planning_tasks",
        "research_tasks",
        "approved_actions",
    ):
        value = case_memory.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    candidates.append(item)
                elif isinstance(item, dict):
                    text = _optional_text(item.get("action"), "") or _optional_text(item.get("title"), "")
                    if text:
                        candidates.append(text)

    return _dedupe(candidates)


def _render_items(items: tuple[ReviewedApplyPacketItem, ...]) -> list[str]:
    if not items:
        return ["- none"]

    lines: list[str] = []
    for item in items:
        lines.append(f"- **{item.status} / {item.severity}**: {item.action}")
        lines.append(f"  - Source category: {item.source_category}")
        lines.append(f"  - Source: {item.source}")
        lines.append(f"  - Reason: {item.reason}")
        if item.evidence_needed:
            lines.append("  - Evidence needed:")
            for evidence in item.evidence_needed:
                lines.append(f"    - {evidence}")
        if item.checklist:
            lines.append("  - Checklist:")
            for check in item.checklist:
                lines.append(f"    - [ ] {check}")

    return lines


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"apply preview review requires {label} list")

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


def _normalize_action(value: str) -> str:
    return " ".join(value.lower().split())


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


def _dedupe_items(items: list[ReviewedApplyPacketItem]) -> list[ReviewedApplyPacketItem]:
    seen: set[tuple[str, str, str]] = set()
    output: list[ReviewedApplyPacketItem] = []

    for item in items:
        key = (
            item.status.lower(),
            item.action.lower(),
            item.source.lower(),
        )
        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output
