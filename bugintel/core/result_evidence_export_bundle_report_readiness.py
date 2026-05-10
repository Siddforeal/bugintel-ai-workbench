"""
Report readiness review for export bundle review gates.

This module reviews a v0.65 export bundle review gate and decides whether the
bundle is ready to support a human-written report draft. It separates report
support notes from blockers, missing evidence, unsafe/rejected items, artifact
problems, overclaim risks, and final report-readiness checklist items.

It does not write reports, write case memory, write research state, call
providers, execute tools, launch browsers, send network requests, mutate
targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReportReadinessItem:
    subject: str
    status: str
    category: str
    severity: str
    source: str
    reason: str
    required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "status": self.status,
            "category": self.category,
            "severity": self.severity,
            "source": self.source,
            "reason": self.reason,
            "required_action": self.required_action,
        }


@dataclass(frozen=True)
class ExportBundleReportReadinessReview:
    recommendation: str
    report_ready_support_notes: tuple[ReportReadinessItem, ...]
    report_blockers: tuple[ReportReadinessItem, ...]
    missing_evidence: tuple[ReportReadinessItem, ...]
    unsafe_or_rejected_items: tuple[ReportReadinessItem, ...]
    artifact_problems: tuple[ReportReadinessItem, ...]
    overclaim_risks: tuple[ReportReadinessItem, ...]
    safety_blockers: tuple[ReportReadinessItem, ...]
    final_report_readiness_checklist: tuple[str, ...]
    report_guardrails: tuple[str, ...]
    source: str = "result-evidence-export-bundle-report-readiness-review"
    planning_only: bool = True
    readiness_state: str = "reviewed_not_reported"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_export_bundle_report_readiness_review",
            "source": self.source,
            "recommendation": self.recommendation,
            "report_ready_support_notes": [
                item.to_dict() for item in self.report_ready_support_notes
            ],
            "report_blockers": [item.to_dict() for item in self.report_blockers],
            "missing_evidence": [item.to_dict() for item in self.missing_evidence],
            "unsafe_or_rejected_items": [
                item.to_dict() for item in self.unsafe_or_rejected_items
            ],
            "artifact_problems": [item.to_dict() for item in self.artifact_problems],
            "overclaim_risks": [item.to_dict() for item in self.overclaim_risks],
            "safety_blockers": [item.to_dict() for item in self.safety_blockers],
            "final_report_readiness_checklist": list(self.final_report_readiness_checklist),
            "report_guardrails": list(self.report_guardrails),
            "planning_only": self.planning_only,
            "readiness_state": self.readiness_state,
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

    def to_markdown(self, title: str = "Export Bundle Report Readiness Review") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            f"- Readiness state: {self.readiness_state}",
            "- Report generation by Blackhole: false",
            "- Report submission by Blackhole: false",
            "- Human approval required: true",
            "- State mutation performed by Blackhole: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Report-Ready Support Notes",
            "",
        ]

        lines.extend(_render_items(self.report_ready_support_notes))
        lines.extend(["", "## Report Blockers", ""])
        lines.extend(_render_items(self.report_blockers))
        lines.extend(["", "## Missing Evidence", ""])
        lines.extend(_render_items(self.missing_evidence))
        lines.extend(["", "## Unsafe / Rejected Items", ""])
        lines.extend(_render_items(self.unsafe_or_rejected_items))
        lines.extend(["", "## Artifact Problems", ""])
        lines.extend(_render_items(self.artifact_problems))
        lines.extend(["", "## Report Overclaim Risks", ""])
        lines.extend(_render_items(self.overclaim_risks))
        lines.extend(["", "## Safety Blockers", ""])
        lines.extend(_render_items(self.safety_blockers))

        lines.extend(["", "## Final Report-Readiness Checklist", ""])
        for item in self.final_report_readiness_checklist:
            lines.append(f"- [ ] {item}")

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
                "- This command reviews report readiness only.",
                "- Do not treat review notes as confirmed vulnerability proof.",
                "- Do not generate or submit a report from this command.",
                "- Do not use bundles with artifact, evidence, overclaim, unsafe, or safety blockers as report-ready.",
                "- Do not write case memory or research state from this review.",
                "",
            ]
        )

        return "\n".join(lines)


def build_export_bundle_report_readiness_review(
    review_gate: dict[str, Any],
    source: str = "result-evidence-export-bundle-report-readiness-review",
) -> ExportBundleReportReadinessReview:
    """Build report-readiness review from an export bundle review gate."""
    _require_kind(
        review_gate,
        "result_evidence_export_bundle_review_gate",
        "export bundle review gate",
    )

    artifact_integrity = _object_list(
        review_gate.get("artifact_integrity_findings"),
        "artifact_integrity_findings",
    )
    missing_artifacts = _object_list(
        review_gate.get("missing_artifact_findings"),
        "missing_artifact_findings",
    )
    packet_risks = _object_list(
        review_gate.get("packet_risk_findings"),
        "packet_risk_findings",
    )
    evidence_gaps = _object_list(
        review_gate.get("evidence_gap_findings"),
        "evidence_gap_findings",
    )
    overclaims = _object_list(
        review_gate.get("overclaim_findings"),
        "overclaim_findings",
    )
    safety_findings = _object_list(
        review_gate.get("safety_findings"),
        "safety_findings",
    )
    approved_notes = _object_list(
        review_gate.get("approved_review_notes"),
        "approved_review_notes",
    )

    artifact_problems = [
        _readiness_item(raw, status="artifact-problem")
        for raw in missing_artifacts + artifact_integrity
    ]

    unsafe_items: list[ReportReadinessItem] = []
    blockers: list[ReportReadinessItem] = []

    for raw in packet_risks:
        category = _optional_text(raw.get("category"), "")
        item = _readiness_item(raw, status="packet-risk")
        if "unsafe" in category or item.severity in {"high", "critical"}:
            unsafe_items.append(
                _readiness_item(raw, status="unsafe-or-rejected-blocker")
            )
        else:
            blockers.append(item)

    missing_evidence = [
        _readiness_item(raw, status="missing-evidence")
        for raw in evidence_gaps
    ]
    overclaim_risks = [
        _readiness_item(raw, status="report-overclaim-risk")
        for raw in overclaims
    ]
    safety_blockers = [
        _readiness_item(raw, status="safety-blocker")
        for raw in safety_findings
    ]

    support_notes: list[ReportReadinessItem] = []
    if not artifact_problems and not unsafe_items and not missing_evidence and not overclaim_risks and not safety_blockers:
        support_notes = [
            _readiness_item(raw, status="report-support-note")
            for raw in approved_notes
        ]

    report_blockers = _dedupe_items(
        blockers
        + [
            item
            for item in artifact_problems + missing_evidence + overclaim_risks + safety_blockers
            if item.severity in {"medium", "high", "critical"}
        ]
    )

    report_guardrails = _dedupe(
        _string_list(review_gate.get("report_guardrails"))
        + [
            "Report readiness review does not generate or submit reports.",
            "Do not claim confirmed vulnerability without local proof.",
            "Do not use unsafe, blocked, missing-evidence, or overclaim items as report-ready.",
            "Do not use artifacts with missing or failed integrity checks in reports.",
        ]
    )

    checklist = _final_checklist(
        support_notes=support_notes,
        report_blockers=report_blockers,
        missing_evidence=missing_evidence,
        unsafe_items=unsafe_items,
        artifact_problems=artifact_problems,
        overclaim_risks=overclaim_risks,
        safety_blockers=safety_blockers,
        review_gate_checklist=_string_list(review_gate.get("human_review_checklist")),
    )

    recommendation = _readiness_recommendation(
        support_notes=support_notes,
        report_blockers=report_blockers,
        missing_evidence=missing_evidence,
        unsafe_items=unsafe_items,
        artifact_problems=artifact_problems,
        overclaim_risks=overclaim_risks,
        safety_blockers=safety_blockers,
    )

    return ExportBundleReportReadinessReview(
        recommendation=recommendation,
        report_ready_support_notes=tuple(_dedupe_items(support_notes)),
        report_blockers=tuple(_dedupe_items(report_blockers)),
        missing_evidence=tuple(_dedupe_items(missing_evidence)),
        unsafe_or_rejected_items=tuple(_dedupe_items(unsafe_items)),
        artifact_problems=tuple(_dedupe_items(artifact_problems)),
        overclaim_risks=tuple(_dedupe_items(overclaim_risks)),
        safety_blockers=tuple(_dedupe_items(safety_blockers)),
        final_report_readiness_checklist=tuple(checklist),
        report_guardrails=tuple(report_guardrails),
        source=source,
    )


def _readiness_recommendation(
    support_notes: list[ReportReadinessItem],
    report_blockers: list[ReportReadinessItem],
    missing_evidence: list[ReportReadinessItem],
    unsafe_items: list[ReportReadinessItem],
    artifact_problems: list[ReportReadinessItem],
    overclaim_risks: list[ReportReadinessItem],
    safety_blockers: list[ReportReadinessItem],
) -> str:
    if safety_blockers:
        return "not-report-ready-fix-safety-metadata"

    if artifact_problems:
        return "not-report-ready-fix-artifact-problems"

    if unsafe_items:
        return "not-report-ready-remove-unsafe-items"

    if missing_evidence or overclaim_risks:
        return "not-report-ready-close-evidence-and-overclaim-gaps"

    if report_blockers:
        return "not-report-ready-resolve-blockers"

    if support_notes:
        return "ready-as-human-report-support-only"

    return "no-report-ready-support-notes"


def _final_checklist(
    support_notes: list[ReportReadinessItem],
    report_blockers: list[ReportReadinessItem],
    missing_evidence: list[ReportReadinessItem],
    unsafe_items: list[ReportReadinessItem],
    artifact_problems: list[ReportReadinessItem],
    overclaim_risks: list[ReportReadinessItem],
    safety_blockers: list[ReportReadinessItem],
    review_gate_checklist: list[str],
) -> list[str]:
    checklist = [
        "Confirm this review is used only to support human report preparation.",
        "Confirm no report is generated or submitted by this command.",
        "Confirm no vulnerability is marked confirmed from bundle metadata.",
        "Confirm all report claims are supported by local evidence.",
    ]

    checklist.extend(review_gate_checklist)

    if support_notes:
        checklist.append("Use report-ready support notes only as human-reviewed context.")

    if artifact_problems:
        checklist.append("Fix artifact presence and integrity problems before report use.")

    if unsafe_items:
        checklist.append("Remove or rewrite unsafe/rejected items before report drafting.")

    if missing_evidence:
        checklist.append("Close missing evidence before report drafting or submission.")

    if overclaim_risks:
        checklist.append("Resolve overclaim risks before writing severity or impact claims.")

    if report_blockers:
        checklist.append("Resolve all report blockers before treating the bundle as report-supporting.")

    if safety_blockers:
        checklist.append("Fix safety metadata before any report-readiness use.")

    return _dedupe(checklist)


def _readiness_item(raw: dict[str, Any], status: str) -> ReportReadinessItem:
    return ReportReadinessItem(
        subject=_optional_text(raw.get("subject"), "unknown subject"),
        status=status,
        category=_optional_text(raw.get("category"), status),
        severity=_optional_text(raw.get("severity"), "info"),
        source=_optional_text(raw.get("source"), "review_gate"),
        reason=_optional_text(raw.get("message"), "No finding message provided."),
        required_action=_optional_text(raw.get("required_action"), "Manual review required."),
    )


def _render_items(items: tuple[ReportReadinessItem, ...]) -> list[str]:
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
        raise ValueError(f"report readiness review requires {label} list")

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


def _dedupe_items(items: list[ReportReadinessItem]) -> list[ReportReadinessItem]:
    seen: set[tuple[str, str, str]] = set()
    output: list[ReportReadinessItem] = []

    for item in items:
        key = (
            item.status.lower(),
            item.subject.lower(),
            item.source.lower(),
        )
        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output
