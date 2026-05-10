"""
Review gate for report-readiness finding draft packets.

This module reviews a v0.67 finding draft packet before human report writing.
It checks title quality, evidence checklist completeness, reproduction
placeholder gaps, impact/severity overclaim risk, blocked claims,
do-not-claim-yet items, and whether the packet is safe only as writing support.

It does not generate reports, submit reports, write case memory, write research
state, call providers, execute tools, launch browsers, send network requests,
mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FindingDraftPacketReviewItem:
    subject: str
    category: str
    severity: str
    status: str
    source: str
    reason: str
    required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "category": self.category,
            "severity": self.severity,
            "status": self.status,
            "source": self.source,
            "reason": self.reason,
            "required_action": self.required_action,
        }


@dataclass(frozen=True)
class FindingDraftPacketReviewGate:
    recommendation: str
    title_quality_findings: tuple[FindingDraftPacketReviewItem, ...]
    evidence_checklist_findings: tuple[FindingDraftPacketReviewItem, ...]
    reproduction_gap_findings: tuple[FindingDraftPacketReviewItem, ...]
    wording_guardrail_findings: tuple[FindingDraftPacketReviewItem, ...]
    blocked_claim_findings: tuple[FindingDraftPacketReviewItem, ...]
    do_not_claim_findings: tuple[FindingDraftPacketReviewItem, ...]
    safety_findings: tuple[FindingDraftPacketReviewItem, ...]
    approved_writing_support: tuple[FindingDraftPacketReviewItem, ...]
    final_review_checklist: tuple[str, ...]
    source: str = "result-evidence-finding-draft-packet-review-gate"
    planning_only: bool = True
    gate_state: str = "reviewed_not_report_generated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_finding_draft_packet_review_gate",
            "source": self.source,
            "recommendation": self.recommendation,
            "title_quality_findings": [
                item.to_dict() for item in self.title_quality_findings
            ],
            "evidence_checklist_findings": [
                item.to_dict() for item in self.evidence_checklist_findings
            ],
            "reproduction_gap_findings": [
                item.to_dict() for item in self.reproduction_gap_findings
            ],
            "wording_guardrail_findings": [
                item.to_dict() for item in self.wording_guardrail_findings
            ],
            "blocked_claim_findings": [
                item.to_dict() for item in self.blocked_claim_findings
            ],
            "do_not_claim_findings": [
                item.to_dict() for item in self.do_not_claim_findings
            ],
            "safety_findings": [item.to_dict() for item in self.safety_findings],
            "approved_writing_support": [
                item.to_dict() for item in self.approved_writing_support
            ],
            "final_review_checklist": list(self.final_review_checklist),
            "planning_only": self.planning_only,
            "gate_state": self.gate_state,
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

    def to_markdown(self, title: str = "Finding Draft Packet Review Gate") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            f"- Gate state: {self.gate_state}",
            "- Report generation by Blackhole: false",
            "- Report submission by Blackhole: false",
            "- Human approval required: true",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Title Quality Findings",
            "",
        ]

        lines.extend(_render_items(self.title_quality_findings))
        lines.extend(["", "## Evidence Checklist Findings", ""])
        lines.extend(_render_items(self.evidence_checklist_findings))
        lines.extend(["", "## Reproduction Gap Findings", ""])
        lines.extend(_render_items(self.reproduction_gap_findings))
        lines.extend(["", "## Wording Guardrail Findings", ""])
        lines.extend(_render_items(self.wording_guardrail_findings))
        lines.extend(["", "## Blocked Claim Findings", ""])
        lines.extend(_render_items(self.blocked_claim_findings))
        lines.extend(["", "## Do-Not-Claim Findings", ""])
        lines.extend(_render_items(self.do_not_claim_findings))
        lines.extend(["", "## Safety Findings", ""])
        lines.extend(_render_items(self.safety_findings))
        lines.extend(["", "## Approved Writing Support", ""])
        lines.extend(_render_items(self.approved_writing_support))

        lines.extend(["", "## Final Review Checklist", ""])
        for item in self.final_review_checklist:
            lines.append(f"- [ ] {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This command reviews a finding draft packet only.",
                "- Do not treat this review as a generated report.",
                "- Do not submit anything from this review.",
                "- Do not claim impact, severity, or vulnerability confirmation unless local evidence supports it.",
                "- Do not write case memory or research state from this review gate.",
                "",
            ]
        )

        return "\n".join(lines)


def build_finding_draft_packet_review_gate(
    finding_draft_packet: dict[str, Any],
    source: str = "result-evidence-finding-draft-packet-review-gate",
) -> FindingDraftPacketReviewGate:
    """Review a finding draft packet before human report writing."""
    _require_kind(
        finding_draft_packet,
        "result_evidence_report_readiness_finding_draft_packet",
        "finding draft packet",
    )

    title_candidates = _object_list(finding_draft_packet.get("title_candidates"), "title_candidates")
    evidence_checklist = _object_list(finding_draft_packet.get("evidence_checklist"), "evidence_checklist")
    reproduction_placeholders = _object_list(
        finding_draft_packet.get("reproduction_plan_placeholders"),
        "reproduction_plan_placeholders",
    )
    impact_guardrails = _object_list(
        finding_draft_packet.get("impact_wording_guardrails"),
        "impact_wording_guardrails",
    )
    severity_guardrails = _object_list(
        finding_draft_packet.get("severity_wording_guardrails"),
        "severity_wording_guardrails",
    )
    blocked_claims = _object_list(finding_draft_packet.get("blocked_claims"), "blocked_claims")
    do_not_claim = _object_list(finding_draft_packet.get("do_not_claim_yet"), "do_not_claim_yet")

    title_findings = _title_quality_findings(title_candidates)
    evidence_findings = _evidence_checklist_findings(evidence_checklist)
    reproduction_findings = _reproduction_gap_findings(reproduction_placeholders)
    wording_findings = _wording_guardrail_findings(impact_guardrails, severity_guardrails)
    blocked_findings = [_review_item(raw, status="blocked-claim-open") for raw in blocked_claims]
    do_not_claim_findings = [_review_item(raw, status="do-not-claim-open") for raw in do_not_claim]
    safety_findings = _safety_findings(finding_draft_packet)

    approved_support = _approved_writing_support(
        title_candidates=title_candidates,
        evidence_checklist=evidence_checklist,
        reproduction_placeholders=reproduction_placeholders,
        title_findings=title_findings,
        evidence_findings=evidence_findings,
        reproduction_findings=reproduction_findings,
        blocked_findings=blocked_findings,
        do_not_claim_findings=do_not_claim_findings,
        safety_findings=safety_findings,
    )

    checklist = _final_review_checklist(
        finding_draft_packet,
        title_findings=title_findings,
        evidence_findings=evidence_findings,
        reproduction_findings=reproduction_findings,
        wording_findings=wording_findings,
        blocked_findings=blocked_findings,
        do_not_claim_findings=do_not_claim_findings,
        safety_findings=safety_findings,
        approved_support=approved_support,
    )

    recommendation = _review_recommendation(
        title_findings=title_findings,
        evidence_findings=evidence_findings,
        reproduction_findings=reproduction_findings,
        blocked_findings=blocked_findings,
        do_not_claim_findings=do_not_claim_findings,
        safety_findings=safety_findings,
        approved_support=approved_support,
    )

    return FindingDraftPacketReviewGate(
        recommendation=recommendation,
        title_quality_findings=tuple(_dedupe_items(title_findings)),
        evidence_checklist_findings=tuple(_dedupe_items(evidence_findings)),
        reproduction_gap_findings=tuple(_dedupe_items(reproduction_findings)),
        wording_guardrail_findings=tuple(_dedupe_items(wording_findings)),
        blocked_claim_findings=tuple(_dedupe_items(blocked_findings)),
        do_not_claim_findings=tuple(_dedupe_items(do_not_claim_findings)),
        safety_findings=tuple(_dedupe_items(safety_findings)),
        approved_writing_support=tuple(_dedupe_items(approved_support)),
        final_review_checklist=tuple(checklist),
        source=source,
    )


def _review_recommendation(
    title_findings: list[FindingDraftPacketReviewItem],
    evidence_findings: list[FindingDraftPacketReviewItem],
    reproduction_findings: list[FindingDraftPacketReviewItem],
    blocked_findings: list[FindingDraftPacketReviewItem],
    do_not_claim_findings: list[FindingDraftPacketReviewItem],
    safety_findings: list[FindingDraftPacketReviewItem],
    approved_support: list[FindingDraftPacketReviewItem],
) -> str:
    if safety_findings:
        return "do-not-use-packet-fix-safety-metadata"

    if blocked_findings or do_not_claim_findings:
        return "do-not-use-for-report-writing-resolve-blocked-claims"

    blocking_gap_findings = [
        item
        for item in evidence_findings + reproduction_findings
        if item.severity in {"medium", "high", "critical"}
    ]
    if blocking_gap_findings:
        return "use-only-after-evidence-and-reproduction-gaps-close"

    high_title_findings = [item for item in title_findings if item.severity in {"high", "critical"}]
    if high_title_findings:
        return "revise-title-before-human-writing"

    if approved_support:
        return "safe-as-human-writing-support-only"

    return "no-writing-support-ready"


def _title_quality_findings(title_candidates: list[dict[str, Any]]) -> list[FindingDraftPacketReviewItem]:
    findings: list[FindingDraftPacketReviewItem] = []

    if not title_candidates:
        return [
            FindingDraftPacketReviewItem(
                subject="missing title candidate",
                category="title-quality",
                severity="medium",
                status="title-missing",
                source="title_candidates",
                reason="The packet does not contain a title candidate.",
                required_action="Add a human-written title candidate after evidence is verified.",
            )
        ]

    for raw in title_candidates:
        text = _optional_text(raw.get("text"), "")
        status = _optional_text(raw.get("status"), "")
        lowered = text.lower()

        if not text:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject="empty title candidate",
                    category="title-quality",
                    severity="high",
                    status="title-empty",
                    source="title_candidates",
                    reason="A title candidate is empty.",
                    required_action="Replace empty title candidate with human-written wording.",
                )
            )
            continue

        if "blocked" in status or "blocked" in lowered:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject=text,
                    category="title-quality",
                    severity="high",
                    status="title-blocked",
                    source=_optional_text(raw.get("source"), "title_candidates"),
                    reason="Title is blocked until readiness issues are resolved.",
                    required_action="Resolve blockers before using this title.",
                )
            )

        if "critical" in lowered or "high" in lowered:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject=text,
                    category="title-quality",
                    severity="medium",
                    status="severity-in-title-review-required",
                    source=_optional_text(raw.get("source"), "title_candidates"),
                    reason="Title appears to include severity wording.",
                    required_action="Remove severity from title unless local evidence fully supports it.",
                )
            )

        if len(text) > 140:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject=text,
                    category="title-quality",
                    severity="low",
                    status="title-too-long",
                    source=_optional_text(raw.get("source"), "title_candidates"),
                    reason="Title candidate is too long for a strong report title.",
                    required_action="Shorten the title during human writing.",
                )
            )

    return findings


def _evidence_checklist_findings(evidence_checklist: list[dict[str, Any]]) -> list[FindingDraftPacketReviewItem]:
    if not evidence_checklist:
        return [
            FindingDraftPacketReviewItem(
                subject="missing evidence checklist",
                category="evidence-checklist",
                severity="high",
                status="evidence-checklist-missing",
                source="evidence_checklist",
                reason="The packet does not contain evidence checklist items.",
                required_action="Add required local evidence before writing a report.",
            )
        ]

    findings: list[FindingDraftPacketReviewItem] = []
    for raw in evidence_checklist:
        text = _optional_text(raw.get("text"), "")
        status = _optional_text(raw.get("status"), "")
        if "missing" in status or "fix" in status:
            findings.append(_review_item(raw, status="evidence-required-before-writing"))

        if not text:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject="empty evidence item",
                    category="evidence-checklist",
                    severity="medium",
                    status="empty-evidence-item",
                    source="evidence_checklist",
                    reason="Evidence checklist contains an empty item.",
                    required_action="Replace with a concrete evidence requirement.",
                )
            )

    return _dedupe_items(findings)


def _reproduction_gap_findings(reproduction_placeholders: list[dict[str, Any]]) -> list[FindingDraftPacketReviewItem]:
    if not reproduction_placeholders:
        return [
            FindingDraftPacketReviewItem(
                subject="missing reproduction plan placeholder",
                category="reproduction-plan",
                severity="medium",
                status="reproduction-placeholder-missing",
                source="reproduction_plan_placeholders",
                reason="The packet does not include reproduction planning support.",
                required_action="Add human-written reproduction placeholders after local validation.",
            )
        ]

    findings: list[FindingDraftPacketReviewItem] = []
    for raw in reproduction_placeholders:
        text = _optional_text(raw.get("text"), "")
        status = _optional_text(raw.get("status"), "")
        lowered = text.lower()

        if "blocked" in status or "blocked" in lowered:
            findings.append(_review_item(raw, status="reproduction-blocked"))

        if "placeholder" in lowered:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject=text,
                    category="reproduction-plan",
                    severity="info",
                    status="human-reproduction-writing-required",
                    source=_optional_text(raw.get("source"), "reproduction_plan_placeholders"),
                    reason="Reproduction steps are placeholders and must be written by a human.",
                    required_action="Replace placeholder with verified steps, requests, responses, and evidence.",
                )
            )

    return _dedupe_items(findings)


def _wording_guardrail_findings(
    impact_guardrails: list[dict[str, Any]],
    severity_guardrails: list[dict[str, Any]],
) -> list[FindingDraftPacketReviewItem]:
    findings: list[FindingDraftPacketReviewItem] = []

    if not impact_guardrails:
        findings.append(
            FindingDraftPacketReviewItem(
                subject="missing impact wording guardrails",
                category="impact-wording",
                severity="medium",
                status="impact-guardrails-missing",
                source="impact_wording_guardrails",
                reason="Impact wording guardrails are missing.",
                required_action="Add guardrails before report writing.",
            )
        )

    if not severity_guardrails:
        findings.append(
            FindingDraftPacketReviewItem(
                subject="missing severity wording guardrails",
                category="severity-wording",
                severity="medium",
                status="severity-guardrails-missing",
                source="severity_wording_guardrails",
                reason="Severity wording guardrails are missing.",
                required_action="Add guardrails before report writing.",
            )
        )

    for raw in impact_guardrails + severity_guardrails:
        status = _optional_text(raw.get("status"), "")
        text = _optional_text(raw.get("text"), "")
        if "blocked" in status or "overclaim" in status or "do not claim" in text.lower():
            findings.append(_review_item(raw, status="wording-overclaim-review-required"))

    return _dedupe_items(findings)


def _approved_writing_support(
    title_candidates: list[dict[str, Any]],
    evidence_checklist: list[dict[str, Any]],
    reproduction_placeholders: list[dict[str, Any]],
    title_findings: list[FindingDraftPacketReviewItem],
    evidence_findings: list[FindingDraftPacketReviewItem],
    reproduction_findings: list[FindingDraftPacketReviewItem],
    blocked_findings: list[FindingDraftPacketReviewItem],
    do_not_claim_findings: list[FindingDraftPacketReviewItem],
    safety_findings: list[FindingDraftPacketReviewItem],
) -> list[FindingDraftPacketReviewItem]:
    if blocked_findings or do_not_claim_findings or safety_findings:
        return []

    high_or_medium = [
        item
        for item in title_findings + evidence_findings + reproduction_findings
        if item.severity in {"medium", "high", "critical"}
    ]
    if high_or_medium:
        return []

    support: list[FindingDraftPacketReviewItem] = []

    if title_candidates:
        support.append(
            FindingDraftPacketReviewItem(
                subject="title candidates",
                category="approved-writing-support",
                severity="info",
                status="review-support-only",
                source="title_candidates",
                reason="Title candidates exist and are not blocked.",
                required_action="Human must rewrite the final title from verified evidence.",
            )
        )

    if evidence_checklist:
        support.append(
            FindingDraftPacketReviewItem(
                subject="evidence checklist",
                category="approved-writing-support",
                severity="info",
                status="review-support-only",
                source="evidence_checklist",
                reason="Evidence checklist exists for human review.",
                required_action="Human must confirm every evidence item before writing.",
            )
        )

    if reproduction_placeholders:
        support.append(
            FindingDraftPacketReviewItem(
                subject="reproduction placeholders",
                category="approved-writing-support",
                severity="info",
                status="review-support-only",
                source="reproduction_plan_placeholders",
                reason="Reproduction planning support exists.",
                required_action="Human must replace placeholders with verified reproduction steps.",
            )
        )

    return support


def _safety_findings(packet: dict[str, Any]) -> list[FindingDraftPacketReviewItem]:
    safety = packet.get("safety")
    if not isinstance(safety, dict):
        return [
            FindingDraftPacketReviewItem(
                subject="safety",
                category="safety-metadata",
                severity="high",
                status="missing-safety-metadata",
                source="safety",
                reason="Finding draft packet is missing safety metadata.",
                required_action="Regenerate the packet with explicit safety metadata.",
            )
        ]

    required_false = [
        "report_generation",
        "report_submission",
        "state_mutation",
        "case_memory_write",
        "research_state_write",
        "network_interaction",
        "target_mutation",
        "tool_execution",
        "browser_execution",
        "llm_provider_calls",
        "provider_execution",
        "vulnerability_confirmation",
    ]

    findings: list[FindingDraftPacketReviewItem] = []
    for key in required_false:
        if safety.get(key) is not False:
            findings.append(
                FindingDraftPacketReviewItem(
                    subject=key,
                    category="safety-metadata",
                    severity="high",
                    status="unsafe-safety-metadata",
                    source="safety",
                    reason=f"Safety metadata must keep {key}=false.",
                    required_action="Regenerate the packet with all execution, mutation, reporting, and confirmation flags false.",
                )
            )

    if safety.get("human_approval_required") is not True:
        findings.append(
            FindingDraftPacketReviewItem(
                subject="human_approval_required",
                category="safety-metadata",
                severity="medium",
                status="missing-human-approval-required",
                source="safety",
                reason="Human approval must be required before any report writing.",
                required_action="Regenerate the packet with human_approval_required=true.",
            )
        )

    return findings


def _final_review_checklist(
    packet: dict[str, Any],
    title_findings: list[FindingDraftPacketReviewItem],
    evidence_findings: list[FindingDraftPacketReviewItem],
    reproduction_findings: list[FindingDraftPacketReviewItem],
    wording_findings: list[FindingDraftPacketReviewItem],
    blocked_findings: list[FindingDraftPacketReviewItem],
    do_not_claim_findings: list[FindingDraftPacketReviewItem],
    safety_findings: list[FindingDraftPacketReviewItem],
    approved_support: list[FindingDraftPacketReviewItem],
) -> list[str]:
    checklist = [
        "Confirm this review gate is used only as human writing support.",
        "Confirm no report is generated or submitted by Blackhole.",
        "Confirm no vulnerability is marked confirmed from this packet.",
        "Confirm every title, impact, severity, and reproduction claim maps to local evidence.",
    ]

    checklist.extend(_string_list(packet.get("final_human_writing_checklist")))

    if title_findings:
        checklist.append("Resolve title quality findings before human report writing.")

    if evidence_findings:
        checklist.append("Close evidence checklist findings before report writing.")

    if reproduction_findings:
        checklist.append("Replace reproduction placeholders with verified manual steps.")

    if wording_findings:
        checklist.append("Apply impact and severity wording guardrails before drafting.")

    if blocked_findings:
        checklist.append("Remove blocked claims before report writing.")

    if do_not_claim_findings:
        checklist.append("Keep do-not-claim-yet items out of the report until revalidated.")

    if safety_findings:
        checklist.append("Fix safety metadata before using this packet.")

    if approved_support:
        checklist.append("Use approved writing support only as human-reviewed context.")

    return _dedupe(checklist)


def _review_item(raw: dict[str, Any], status: str) -> FindingDraftPacketReviewItem:
    return FindingDraftPacketReviewItem(
        subject=_optional_text(raw.get("text"), _optional_text(raw.get("subject"), "unknown subject")),
        category=_optional_text(raw.get("category"), status),
        severity=_optional_text(raw.get("severity"), "info"),
        status=status,
        source=_optional_text(raw.get("source"), "finding_draft_packet"),
        reason=_optional_text(raw.get("reason"), "Manual review required."),
        required_action=_optional_text(raw.get("required_action"), "Manual review required."),
    )


def _render_items(items: tuple[FindingDraftPacketReviewItem, ...]) -> list[str]:
    if not items:
        return ["- none"]

    lines: list[str] = []
    for item in items:
        lines.append(f"- **{item.status} / {item.severity}**: {item.subject}")
        lines.append(f"  - Category: {item.category}")
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
        raise ValueError(f"finding draft packet review gate requires {label} list")

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


def _dedupe_items(items: list[FindingDraftPacketReviewItem]) -> list[FindingDraftPacketReviewItem]:
    seen: set[tuple[str, str, str]] = set()
    output: list[FindingDraftPacketReviewItem] = []

    for item in items:
        key = (
            item.status.lower(),
            item.category.lower(),
            item.subject.lower(),
        )
        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output
