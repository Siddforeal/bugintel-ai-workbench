"""
Finding draft packet builder for report-readiness reviews.

This module turns a v0.66 export bundle report-readiness review into a safe
human report-draft packet. It prepares title candidates, evidence checklist
items, reproduction placeholders, impact/severity wording guardrails, blocked
claims, and a final human writing checklist.

It does not generate reports, submit reports, write case memory, write research
state, call providers, execute tools, launch browsers, send network requests,
mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FindingDraftPacketItem:
    text: str
    category: str
    status: str
    source: str
    reason: str
    required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "category": self.category,
            "status": self.status,
            "source": self.source,
            "reason": self.reason,
            "required_action": self.required_action,
        }


@dataclass(frozen=True)
class ReportReadinessFindingDraftPacket:
    recommendation: str
    title_candidates: tuple[FindingDraftPacketItem, ...]
    evidence_checklist: tuple[FindingDraftPacketItem, ...]
    reproduction_plan_placeholders: tuple[FindingDraftPacketItem, ...]
    impact_wording_guardrails: tuple[FindingDraftPacketItem, ...]
    severity_wording_guardrails: tuple[FindingDraftPacketItem, ...]
    blocked_claims: tuple[FindingDraftPacketItem, ...]
    do_not_claim_yet: tuple[FindingDraftPacketItem, ...]
    final_human_writing_checklist: tuple[str, ...]
    source: str = "result-evidence-report-readiness-finding-draft-packet"
    planning_only: bool = True
    draft_state: str = "packet_built_not_report_generated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_report_readiness_finding_draft_packet",
            "source": self.source,
            "recommendation": self.recommendation,
            "title_candidates": [item.to_dict() for item in self.title_candidates],
            "evidence_checklist": [item.to_dict() for item in self.evidence_checklist],
            "reproduction_plan_placeholders": [
                item.to_dict() for item in self.reproduction_plan_placeholders
            ],
            "impact_wording_guardrails": [
                item.to_dict() for item in self.impact_wording_guardrails
            ],
            "severity_wording_guardrails": [
                item.to_dict() for item in self.severity_wording_guardrails
            ],
            "blocked_claims": [item.to_dict() for item in self.blocked_claims],
            "do_not_claim_yet": [item.to_dict() for item in self.do_not_claim_yet],
            "final_human_writing_checklist": list(self.final_human_writing_checklist),
            "planning_only": self.planning_only,
            "draft_state": self.draft_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "human_approval_required": True,
                "report_generation": False,
                "report_submission": False,
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

    def to_markdown(self, title: str = "Report Readiness Finding Draft Packet") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            f"- Draft state: {self.draft_state}",
            "- Report generation by Blackhole: false",
            "- Report submission by Blackhole: false",
            "- Human approval required: true",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Title Candidates",
            "",
        ]

        lines.extend(_render_items(self.title_candidates))
        lines.extend(["", "## Evidence Checklist", ""])
        lines.extend(_render_items(self.evidence_checklist))
        lines.extend(["", "## Reproduction Plan Placeholders", ""])
        lines.extend(_render_items(self.reproduction_plan_placeholders))
        lines.extend(["", "## Impact Wording Guardrails", ""])
        lines.extend(_render_items(self.impact_wording_guardrails))
        lines.extend(["", "## Severity Wording Guardrails", ""])
        lines.extend(_render_items(self.severity_wording_guardrails))
        lines.extend(["", "## Blocked Claims", ""])
        lines.extend(_render_items(self.blocked_claims))
        lines.extend(["", "## Do Not Claim Yet", ""])
        lines.extend(_render_items(self.do_not_claim_yet))

        lines.extend(["", "## Final Human Writing Checklist", ""])
        for item in self.final_human_writing_checklist:
            lines.append(f"- [ ] {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This command builds a draft packet only.",
                "- Do not treat this packet as a generated report.",
                "- Do not submit anything from this packet without human writing and evidence review.",
                "- Do not claim impact, severity, or vulnerability confirmation unless local evidence supports it.",
                "- Do not write case memory or research state from this packet.",
                "",
            ]
        )

        return "\n".join(lines)


def build_report_readiness_finding_draft_packet(
    report_readiness_review: dict[str, Any],
    source: str = "result-evidence-report-readiness-finding-draft-packet",
) -> ReportReadinessFindingDraftPacket:
    """Build a safe human report-draft packet from a report-readiness review."""
    _require_kind(
        report_readiness_review,
        "result_evidence_export_bundle_report_readiness_review",
        "export bundle report readiness review",
    )

    support_notes = _object_list(
        report_readiness_review.get("report_ready_support_notes"),
        "report_ready_support_notes",
    )
    report_blockers = _object_list(
        report_readiness_review.get("report_blockers"),
        "report_blockers",
    )
    missing_evidence = _object_list(
        report_readiness_review.get("missing_evidence"),
        "missing_evidence",
    )
    unsafe_items = _object_list(
        report_readiness_review.get("unsafe_or_rejected_items"),
        "unsafe_or_rejected_items",
    )
    artifact_problems = _object_list(
        report_readiness_review.get("artifact_problems"),
        "artifact_problems",
    )
    overclaim_risks = _object_list(
        report_readiness_review.get("overclaim_risks"),
        "overclaim_risks",
    )
    safety_blockers = _object_list(
        report_readiness_review.get("safety_blockers"),
        "safety_blockers",
    )

    blockers = report_blockers + missing_evidence + unsafe_items + artifact_problems + overclaim_risks + safety_blockers

    title_candidates = _title_candidates(support_notes, blockers)
    evidence_checklist = _evidence_checklist(support_notes, missing_evidence, artifact_problems)
    reproduction_placeholders = _reproduction_placeholders(support_notes, blockers)
    impact_guardrails = _impact_guardrails(report_readiness_review, support_notes, blockers, overclaim_risks)
    severity_guardrails = _severity_guardrails(report_readiness_review, blockers, overclaim_risks)
    blocked_claims = _blocked_claims(blockers)
    do_not_claim = _do_not_claim_yet(missing_evidence, unsafe_items, artifact_problems, overclaim_risks, safety_blockers)
    final_checklist = _final_writing_checklist(
        report_readiness_review,
        title_candidates=title_candidates,
        evidence_checklist=evidence_checklist,
        reproduction_placeholders=reproduction_placeholders,
        blocked_claims=blocked_claims,
        do_not_claim=do_not_claim,
    )

    recommendation = _draft_packet_recommendation(
        support_notes=support_notes,
        blockers=blockers,
        missing_evidence=missing_evidence,
        unsafe_items=unsafe_items,
        artifact_problems=artifact_problems,
        overclaim_risks=overclaim_risks,
        safety_blockers=safety_blockers,
    )

    return ReportReadinessFindingDraftPacket(
        recommendation=recommendation,
        title_candidates=tuple(_dedupe_items(title_candidates)),
        evidence_checklist=tuple(_dedupe_items(evidence_checklist)),
        reproduction_plan_placeholders=tuple(_dedupe_items(reproduction_placeholders)),
        impact_wording_guardrails=tuple(_dedupe_items(impact_guardrails)),
        severity_wording_guardrails=tuple(_dedupe_items(severity_guardrails)),
        blocked_claims=tuple(_dedupe_items(blocked_claims)),
        do_not_claim_yet=tuple(_dedupe_items(do_not_claim)),
        final_human_writing_checklist=tuple(final_checklist),
        source=source,
    )


def _draft_packet_recommendation(
    support_notes: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    unsafe_items: list[dict[str, Any]],
    artifact_problems: list[dict[str, Any]],
    overclaim_risks: list[dict[str, Any]],
    safety_blockers: list[dict[str, Any]],
) -> str:
    if safety_blockers:
        return "do-not-draft-fix-safety-metadata"

    if artifact_problems:
        return "do-not-draft-fix-artifacts"

    if unsafe_items:
        return "do-not-draft-remove-unsafe-items"

    if missing_evidence or overclaim_risks:
        return "draft-packet-blocked-close-evidence-and-overclaim-gaps"

    if blockers:
        return "draft-packet-blocked-resolve-report-blockers"

    if support_notes:
        return "ready-for-human-written-draft-packet"

    return "no-draftable-report-support-notes"


def _title_candidates(
    support_notes: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    if blockers:
        return [
            FindingDraftPacketItem(
                text="Title blocked until report-readiness blockers are resolved.",
                category="title-blocked",
                status="blocked",
                source="report_readiness_review",
                reason="The readiness review still contains blockers.",
                required_action="Resolve blockers before choosing a report title.",
            )
        ]

    if not support_notes:
        return []

    candidates: list[FindingDraftPacketItem] = []
    for note in support_notes:
        subject = _optional_text(note.get("subject"), "validated behavior")
        candidates.append(
            FindingDraftPacketItem(
                text=f"Human-reviewed finding draft: {subject}",
                category="title-candidate",
                status="human-write-required",
                source=_optional_text(note.get("source"), "report_ready_support_notes"),
                reason="Built from a report-ready support note.",
                required_action="Human must rewrite title to match confirmed local evidence.",
            )
        )

    return candidates


def _evidence_checklist(
    support_notes: list[dict[str, Any]],
    missing_evidence: list[dict[str, Any]],
    artifact_problems: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    checklist: list[FindingDraftPacketItem] = []

    for note in support_notes:
        checklist.append(
            FindingDraftPacketItem(
                text=f"Attach local evidence for: {_optional_text(note.get('subject'), 'support note')}",
                category="evidence-checklist",
                status="required-before-report",
                source=_optional_text(note.get("source"), "report_ready_support_notes"),
                reason=_optional_text(note.get("reason"), "Support note requires local evidence."),
                required_action="Map this note to concrete local evidence before drafting.",
            )
        )

    for item in missing_evidence:
        checklist.append(_from_readiness_item(item, status="missing-evidence-required"))

    for item in artifact_problems:
        checklist.append(_from_readiness_item(item, status="artifact-evidence-fix-required"))

    return checklist


def _reproduction_placeholders(
    support_notes: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    if blockers:
        return [
            FindingDraftPacketItem(
                text="Reproduction plan blocked until all blockers are resolved.",
                category="reproduction-plan-placeholder",
                status="blocked",
                source="report_readiness_review",
                reason="Readiness review contains blockers.",
                required_action="Resolve blockers before writing reproduction steps.",
            )
        ]

    if not support_notes:
        return []

    return [
        FindingDraftPacketItem(
            text="Placeholder: write manual reproduction steps from verified local evidence only.",
            category="reproduction-plan-placeholder",
            status="human-write-required",
            source="report_ready_support_notes",
            reason="A report-ready support note exists, but steps must be written by a human.",
            required_action="Add commands, requests, responses, screenshots, and expected/actual behavior only after verification.",
        )
    ]


def _impact_guardrails(
    report_readiness_review: dict[str, Any],
    support_notes: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    overclaim_risks: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    guardrails = [
        FindingDraftPacketItem(
            text="Do not claim practical impact until local evidence demonstrates it.",
            category="impact-wording-guardrail",
            status="guardrail",
            source="report_guardrails",
            reason="Impact must be evidence-based.",
            required_action="Tie every impact sentence to local proof.",
        )
    ]

    for guardrail in _string_list(report_readiness_review.get("report_guardrails")):
        guardrails.append(
            FindingDraftPacketItem(
                text=guardrail,
                category="impact-wording-guardrail",
                status="guardrail",
                source="report_guardrails",
                reason="Inherited from report-readiness review.",
                required_action="Apply this guardrail when writing impact.",
            )
        )

    for item in overclaim_risks:
        guardrails.append(_from_readiness_item(item, status="impact-overclaim-blocker"))

    if blockers and support_notes:
        guardrails.append(
            FindingDraftPacketItem(
                text="Support notes exist, but blockers mean impact wording must stay conditional or omitted.",
                category="impact-wording-guardrail",
                status="blocked",
                source="report_readiness_review",
                reason="The readiness review has unresolved blockers.",
                required_action="Resolve blockers before writing impact claims.",
            )
        )

    return guardrails


def _severity_guardrails(
    report_readiness_review: dict[str, Any],
    blockers: list[dict[str, Any]],
    overclaim_risks: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    guardrails = [
        FindingDraftPacketItem(
            text="Do not assign severity until exploitability and impact are proven locally.",
            category="severity-wording-guardrail",
            status="guardrail",
            source="report_guardrails",
            reason="Severity must follow evidence, not assumptions.",
            required_action="Use conservative severity wording until proof is complete.",
        )
    ]

    for item in overclaim_risks:
        guardrails.append(_from_readiness_item(item, status="severity-overclaim-blocker"))

    if blockers:
        guardrails.append(
            FindingDraftPacketItem(
                text="Do not state High/Critical severity while report-readiness blockers remain open.",
                category="severity-wording-guardrail",
                status="blocked",
                source="report_readiness_review",
                reason="Open blockers prevent reliable severity wording.",
                required_action="Resolve blockers before writing severity.",
            )
        )

    if not _string_list(report_readiness_review.get("report_guardrails")):
        guardrails.append(
            FindingDraftPacketItem(
                text="No additional report guardrails were provided; keep severity wording evidence-limited.",
                category="severity-wording-guardrail",
                status="guardrail",
                source="report_guardrails",
                reason="Default safety guardrail.",
                required_action="Avoid severity claims without local proof.",
            )
        )

    return guardrails


def _blocked_claims(blockers: list[dict[str, Any]]) -> list[FindingDraftPacketItem]:
    return [_from_readiness_item(item, status="blocked-claim") for item in blockers]


def _do_not_claim_yet(
    missing_evidence: list[dict[str, Any]],
    unsafe_items: list[dict[str, Any]],
    artifact_problems: list[dict[str, Any]],
    overclaim_risks: list[dict[str, Any]],
    safety_blockers: list[dict[str, Any]],
) -> list[FindingDraftPacketItem]:
    output: list[FindingDraftPacketItem] = []

    sections = [
        (missing_evidence, "missing-evidence-do-not-claim"),
        (unsafe_items, "unsafe-item-do-not-claim"),
        (artifact_problems, "artifact-problem-do-not-claim"),
        (overclaim_risks, "overclaim-risk-do-not-claim"),
        (safety_blockers, "safety-blocker-do-not-claim"),
    ]

    for items, status in sections:
        output.extend(_from_readiness_item(item, status=status) for item in items)

    if output:
        output.append(
            FindingDraftPacketItem(
                text="Do not claim the finding is confirmed until all blockers are resolved.",
                category="global-do-not-claim-yet",
                status="blocked",
                source="report_readiness_review",
                reason="One or more readiness blockers remain open.",
                required_action="Resolve every blocker and re-run readiness review.",
            )
        )

    return output


def _final_writing_checklist(
    report_readiness_review: dict[str, Any],
    title_candidates: list[FindingDraftPacketItem],
    evidence_checklist: list[FindingDraftPacketItem],
    reproduction_placeholders: list[FindingDraftPacketItem],
    blocked_claims: list[FindingDraftPacketItem],
    do_not_claim: list[FindingDraftPacketItem],
) -> list[str]:
    checklist = [
        "Confirm this packet is used only as human writing guidance.",
        "Confirm no report was generated or submitted by Blackhole.",
        "Confirm no vulnerability is marked confirmed from this packet.",
        "Confirm every report claim maps to local evidence.",
    ]

    checklist.extend(_string_list(report_readiness_review.get("final_report_readiness_checklist")))

    if title_candidates:
        checklist.append("Rewrite title candidates manually to match verified evidence.")

    if evidence_checklist:
        checklist.append("Attach or cite all required evidence before drafting.")

    if reproduction_placeholders:
        checklist.append("Write reproduction steps manually from verified local actions only.")

    if blocked_claims:
        checklist.append("Remove or resolve blocked claims before final report writing.")

    if do_not_claim:
        checklist.append("Keep do-not-claim-yet items out of the report until revalidated.")

    checklist.append("Have a human perform the final report wording and severity review.")

    return _dedupe(checklist)


def _from_readiness_item(raw: dict[str, Any], status: str) -> FindingDraftPacketItem:
    return FindingDraftPacketItem(
        text=_optional_text(raw.get("subject"), "unknown subject"),
        category=_optional_text(raw.get("category"), status),
        status=status,
        source=_optional_text(raw.get("source"), "report_readiness_review"),
        reason=_optional_text(raw.get("reason"), _optional_text(raw.get("message"), "Manual review required.")),
        required_action=_optional_text(raw.get("required_action"), "Manual review required."),
    )


def _render_items(items: tuple[FindingDraftPacketItem, ...]) -> list[str]:
    if not items:
        return ["- none"]

    lines: list[str] = []
    for item in items:
        lines.append(f"- **{item.status} / {item.category}**: {item.text}")
        lines.append(f"  - Source: {item.source}")
        lines.append(f"  - Reason: {item.reason}")
        lines.append(f"  - Required action: {item.required_action}")

    return lines


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"finding draft packet requires {label} list")

    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"each {label} item must be an object")
        output.append(item)

    return output


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


def _dedupe_items(items: list[FindingDraftPacketItem]) -> list[FindingDraftPacketItem]:
    seen: set[tuple[str, str, str]] = set()
    output: list[FindingDraftPacketItem] = []

    for item in items:
        key = (
            item.status.lower(),
            item.category.lower(),
            item.text.lower(),
        )
        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output
