"""
Review gate for reviewed apply packet export bundles.

This module reviews a v0.64 reviewed apply packet export bundle before it is
used in a report or future workflow. It flags missing artifacts, artifact
integrity issues, unsafe packet counts, evidence gaps, overclaim risks, and
safety metadata concerns.

It does not write case memory, write research state, call providers, execute
tools, launch browsers, send network requests, mutate targets, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExportBundleReviewFinding:
    category: str
    severity: str
    message: str
    subject: str
    source: str
    required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "subject": self.subject,
            "source": self.source,
            "required_action": self.required_action,
        }


@dataclass(frozen=True)
class ExportBundleReviewGate:
    recommendation: str
    artifact_integrity_findings: tuple[ExportBundleReviewFinding, ...]
    missing_artifact_findings: tuple[ExportBundleReviewFinding, ...]
    packet_risk_findings: tuple[ExportBundleReviewFinding, ...]
    evidence_gap_findings: tuple[ExportBundleReviewFinding, ...]
    overclaim_findings: tuple[ExportBundleReviewFinding, ...]
    safety_findings: tuple[ExportBundleReviewFinding, ...]
    approved_review_notes: tuple[ExportBundleReviewFinding, ...]
    report_guardrails: tuple[str, ...]
    human_review_checklist: tuple[str, ...]
    source: str = "result-evidence-export-bundle-review-gate"
    planning_only: bool = True
    gate_state: str = "reviewed_not_used"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_export_bundle_review_gate",
            "source": self.source,
            "recommendation": self.recommendation,
            "artifact_integrity_findings": [
                finding.to_dict() for finding in self.artifact_integrity_findings
            ],
            "missing_artifact_findings": [
                finding.to_dict() for finding in self.missing_artifact_findings
            ],
            "packet_risk_findings": [
                finding.to_dict() for finding in self.packet_risk_findings
            ],
            "evidence_gap_findings": [
                finding.to_dict() for finding in self.evidence_gap_findings
            ],
            "overclaim_findings": [
                finding.to_dict() for finding in self.overclaim_findings
            ],
            "safety_findings": [finding.to_dict() for finding in self.safety_findings],
            "approved_review_notes": [
                finding.to_dict() for finding in self.approved_review_notes
            ],
            "report_guardrails": list(self.report_guardrails),
            "human_review_checklist": list(self.human_review_checklist),
            "planning_only": self.planning_only,
            "gate_state": self.gate_state,
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

    def to_markdown(self, title: str = "Export Bundle Review Gate") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            f"- Gate state: {self.gate_state}",
            "- Human approval required: true",
            "- State mutation performed by Blackhole: false",
            "- Case memory write: false",
            "- Research state write: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Missing Artifacts",
            "",
        ]

        lines.extend(_render_findings(self.missing_artifact_findings))
        lines.extend(["", "## Artifact Integrity Findings", ""])
        lines.extend(_render_findings(self.artifact_integrity_findings))
        lines.extend(["", "## Packet Risk Findings", ""])
        lines.extend(_render_findings(self.packet_risk_findings))
        lines.extend(["", "## Evidence Gap Findings", ""])
        lines.extend(_render_findings(self.evidence_gap_findings))
        lines.extend(["", "## Report Overclaim Findings", ""])
        lines.extend(_render_findings(self.overclaim_findings))
        lines.extend(["", "## Safety Metadata Findings", ""])
        lines.extend(_render_findings(self.safety_findings))
        lines.extend(["", "## Approved Review Notes", ""])
        lines.extend(_render_findings(self.approved_review_notes))

        lines.extend(["", "## Human Review Checklist", ""])
        for item in self.human_review_checklist:
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
                "- This command reviews an export bundle only.",
                "- Do not treat the bundle as vulnerability proof.",
                "- Do not use a bundle with missing artifacts in a report.",
                "- Do not use a bundle with unsafe, blocked, evidence-gap, or overclaim findings without manual review.",
                "- Do not write case memory or research state from this review gate.",
                "",
            ]
        )

        return "\n".join(lines)


def build_export_bundle_review_gate(
    export_bundle: dict[str, Any],
    source: str = "result-evidence-export-bundle-review-gate",
) -> ExportBundleReviewGate:
    """Build a review gate from a reviewed apply packet export bundle."""
    _require_kind(
        export_bundle,
        "result_evidence_reviewed_apply_packet_export_bundle",
        "reviewed apply packet export bundle",
    )

    packet_counts = export_bundle.get("packet_counts")
    if not isinstance(packet_counts, dict):
        raise ValueError("export bundle requires packet_counts object")

    included_artifacts = _object_list(export_bundle.get("included_artifacts"), "included_artifacts")

    missing_artifacts = _missing_artifact_findings(included_artifacts)
    artifact_integrity = _artifact_integrity_findings(included_artifacts)
    packet_risks = _packet_risk_findings(packet_counts)
    evidence_gaps = _count_finding(
        packet_counts,
        key="evidence_gaps",
        category="open-evidence-gap-count",
        severity="medium",
        message="Export bundle contains open evidence gaps.",
        required_action="Close evidence gaps before report or future workflow use.",
    )
    overclaims = _count_finding(
        packet_counts,
        key="overclaim_risks",
        category="open-overclaim-risk-count",
        severity="medium",
        message="Export bundle contains report overclaim risks.",
        required_action="Remove or resolve overclaim risks before report use.",
    )
    safety_findings = _safety_findings(export_bundle)
    approved_notes = _approved_review_notes(export_bundle, packet_counts, included_artifacts)

    report_guardrails = _dedupe(
        _string_list(export_bundle.get("report_guardrails"))
        + [
            "Export bundle review gate does not mutate case memory or research state.",
            "Do not use bundle artifacts as vulnerability proof without local validation.",
            "Do not use missing or integrity-failed artifacts in reports.",
        ]
    )

    human_review_checklist = _dedupe(
        _string_list(export_bundle.get("human_review_checklist"))
        + [
            "Confirm every included artifact exists and has an integrity hash.",
            "Confirm unsafe, blocked, evidence-gap, and overclaim counts are understood.",
            "Confirm the bundle is used as a review package only.",
            "Confirm no vulnerability is marked confirmed from this bundle.",
        ]
    )

    recommendation = _gate_recommendation(
        missing_artifacts=missing_artifacts,
        artifact_integrity=artifact_integrity,
        packet_risks=packet_risks,
        evidence_gaps=evidence_gaps,
        overclaims=overclaims,
        safety_findings=safety_findings,
        approved_notes=approved_notes,
    )

    return ExportBundleReviewGate(
        recommendation=recommendation,
        artifact_integrity_findings=tuple(artifact_integrity),
        missing_artifact_findings=tuple(missing_artifacts),
        packet_risk_findings=tuple(packet_risks),
        evidence_gap_findings=tuple(evidence_gaps),
        overclaim_findings=tuple(overclaims),
        safety_findings=tuple(safety_findings),
        approved_review_notes=tuple(approved_notes),
        report_guardrails=tuple(report_guardrails),
        human_review_checklist=tuple(human_review_checklist),
        source=source,
    )


def _gate_recommendation(
    missing_artifacts: list[ExportBundleReviewFinding],
    artifact_integrity: list[ExportBundleReviewFinding],
    packet_risks: list[ExportBundleReviewFinding],
    evidence_gaps: list[ExportBundleReviewFinding],
    overclaims: list[ExportBundleReviewFinding],
    safety_findings: list[ExportBundleReviewFinding],
    approved_notes: list[ExportBundleReviewFinding],
) -> str:
    high_risk = [
        finding
        for finding in (
            missing_artifacts
            + artifact_integrity
            + packet_risks
            + evidence_gaps
            + overclaims
            + safety_findings
        )
        if finding.severity in {"high", "critical"}
    ]

    if safety_findings:
        return "do-not-use-bundle-until-safety-metadata-fixed"

    if missing_artifacts or artifact_integrity:
        return "do-not-use-bundle-until-artifacts-verified"

    if high_risk:
        return "use-only-for-internal-review-block-high-risk-items"

    if packet_risks or evidence_gaps or overclaims:
        return "use-only-for-internal-review-with-open-items"

    if approved_notes:
        return "safe-as-review-package-only"

    return "no-actionable-bundle-content"


def _missing_artifact_findings(artifacts: list[dict[str, Any]]) -> list[ExportBundleReviewFinding]:
    findings: list[ExportBundleReviewFinding] = []

    for raw in artifacts:
        path = _optional_text(raw.get("path"), "unknown artifact")
        exists = bool(raw.get("exists", False))
        if exists:
            continue

        findings.append(
            ExportBundleReviewFinding(
                category="missing-artifact",
                severity="high",
                message="Included artifact is marked missing in the bundle manifest.",
                subject=path,
                source=_optional_text(raw.get("role"), "artifact"),
                required_action="Regenerate or remove this artifact reference before using the bundle.",
            )
        )

    return findings


def _artifact_integrity_findings(artifacts: list[dict[str, Any]]) -> list[ExportBundleReviewFinding]:
    findings: list[ExportBundleReviewFinding] = []
    seen_paths: set[str] = set()

    for raw in artifacts:
        path = _optional_text(raw.get("path"), "unknown artifact")
        role = _optional_text(raw.get("role"), "artifact")
        exists = bool(raw.get("exists", False))
        size_bytes = _int_value(raw.get("size_bytes"))
        digest = _optional_text(raw.get("sha256"), "")

        normalized_path = path.lower()
        if normalized_path in seen_paths:
            findings.append(
                ExportBundleReviewFinding(
                    category="duplicate-artifact-reference",
                    severity="low",
                    message="Artifact path appears more than once in the bundle manifest.",
                    subject=path,
                    source=role,
                    required_action="Deduplicate artifact references before sharing the bundle.",
                )
            )
        seen_paths.add(normalized_path)

        if not exists:
            continue

        if size_bytes <= 0:
            findings.append(
                ExportBundleReviewFinding(
                    category="empty-artifact",
                    severity="medium",
                    message="Artifact is marked present but has zero size.",
                    subject=path,
                    source=role,
                    required_action="Regenerate the artifact and rebuild the bundle.",
                )
            )

        if not _looks_like_sha256(digest):
            findings.append(
                ExportBundleReviewFinding(
                    category="missing-or-invalid-artifact-hash",
                    severity="medium",
                    message="Artifact is marked present but lacks a valid SHA256 hash.",
                    subject=path,
                    source=role,
                    required_action="Rebuild the artifact reference with a valid SHA256 hash.",
                )
            )

    return findings


def _packet_risk_findings(packet_counts: dict[str, Any]) -> list[ExportBundleReviewFinding]:
    findings: list[ExportBundleReviewFinding] = []

    rules = [
        (
            "unsafe_or_rejected_items",
            "unsafe-or-rejected-items-present",
            "high",
            "Export bundle contains unsafe or rejected items.",
            "Keep unsafe/rejected items blocked and remove them from report-ready material.",
        ),
        (
            "blocked_updates",
            "blocked-updates-present",
            "medium",
            "Export bundle contains blocked updates.",
            "Keep blocked updates out of any future workflow until manually approved.",
        ),
        (
            "duplicate_updates",
            "duplicate-updates-present",
            "low",
            "Export bundle contains duplicate updates.",
            "Deduplicate before future workflow or report use.",
        ),
    ]

    for key, category, severity, message, required_action in rules:
        findings.extend(
            _count_finding(
                packet_counts,
                key=key,
                category=category,
                severity=severity,
                message=message,
                required_action=required_action,
            )
        )

    return findings


def _count_finding(
    packet_counts: dict[str, Any],
    key: str,
    category: str,
    severity: str,
    message: str,
    required_action: str,
) -> list[ExportBundleReviewFinding]:
    count = _int_value(packet_counts.get(key))
    if count <= 0:
        return []

    return [
        ExportBundleReviewFinding(
            category=category,
            severity=severity,
            message=message,
            subject=f"{key}={count}",
            source="packet_counts",
            required_action=required_action,
        )
    ]


def _safety_findings(export_bundle: dict[str, Any]) -> list[ExportBundleReviewFinding]:
    safety = export_bundle.get("safety")
    if not isinstance(safety, dict):
        return [
            ExportBundleReviewFinding(
                category="missing-safety-metadata",
                severity="high",
                message="Export bundle is missing safety metadata.",
                subject="safety",
                source="export_bundle",
                required_action="Regenerate the bundle with explicit safety metadata.",
            )
        ]

    required_false = [
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

    findings: list[ExportBundleReviewFinding] = []

    for key in required_false:
        if safety.get(key) is not False:
            findings.append(
                ExportBundleReviewFinding(
                    category="unsafe-safety-metadata",
                    severity="high",
                    message=f"Safety metadata must keep {key}=false.",
                    subject=key,
                    source="safety",
                    required_action="Regenerate the bundle and keep all execution/mutation flags false.",
                )
            )

    if safety.get("human_approval_required") is not True:
        findings.append(
            ExportBundleReviewFinding(
                category="missing-human-approval-required",
                severity="medium",
                message="Safety metadata must require human approval.",
                subject="human_approval_required",
                source="safety",
                required_action="Regenerate the bundle with human approval required.",
            )
        )

    return findings


def _approved_review_notes(
    export_bundle: dict[str, Any],
    packet_counts: dict[str, Any],
    artifacts: list[dict[str, Any]],
) -> list[ExportBundleReviewFinding]:
    notes: list[ExportBundleReviewFinding] = []

    approved_count = _int_value(packet_counts.get("approved_planning_updates"))
    if approved_count > 0:
        notes.append(
            ExportBundleReviewFinding(
                category="approved-review-package-note",
                severity="info",
                message="Bundle contains approved planning-note updates for human review.",
                subject=f"approved_planning_updates={approved_count}",
                source="packet_counts",
                required_action="Use these as review notes only, not vulnerability proof.",
            )
        )

    if artifacts:
        notes.append(
            ExportBundleReviewFinding(
                category="artifact-reference-summary",
                severity="info",
                message="Bundle contains local artifact references for review.",
                subject=f"included_artifacts={len(artifacts)}",
                source="included_artifacts",
                required_action="Verify artifacts before report or external sharing.",
            )
        )

    bundle_id = _optional_text(export_bundle.get("bundle_id"), "")
    if bundle_id:
        notes.append(
            ExportBundleReviewFinding(
                category="bundle-id-present",
                severity="info",
                message="Bundle has a stable manifest identifier.",
                subject=bundle_id,
                source="bundle_id",
                required_action="Keep bundle ID with exported review materials.",
            )
        )

    return notes


def _render_findings(findings: tuple[ExportBundleReviewFinding, ...]) -> list[str]:
    if not findings:
        return ["- none"]

    lines: list[str] = []
    for finding in findings:
        lines.append(f"- **{finding.severity} / {finding.category}**: {finding.subject}")
        lines.append(f"  - Source: {finding.source}")
        lines.append(f"  - Finding: {finding.message}")
        lines.append(f"  - Required action: {finding.required_action}")

    return lines


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"export bundle requires {label} list")

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


def _int_value(value: Any) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return 0
    return max(integer, 0)


def _looks_like_sha256(value: str) -> bool:
    if len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


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
