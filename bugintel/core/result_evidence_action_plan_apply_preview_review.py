"""
Reviewer for action plan apply previews.

This module reviews a v0.61 action plan apply preview before any future state
write exists. It flags duplicate update candidates, blocked updates, missing
evidence, unsafe/rejected actions, and report overclaim risks.

It does not write case memory, write research state, call providers, execute
tools, launch browsers, send network requests, mutate targets, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApplyPreviewReviewFinding:
    category: str
    severity: str
    message: str
    action: str
    source: str
    evidence_needed: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "action": self.action,
            "source": self.source,
            "evidence_needed": list(self.evidence_needed),
        }


@dataclass(frozen=True)
class ActionPlanApplyPreviewReview:
    recommendation: str
    duplicate_update_candidates: tuple[ApplyPreviewReviewFinding, ...]
    blocked_action_findings: tuple[ApplyPreviewReviewFinding, ...]
    evidence_gap_findings: tuple[ApplyPreviewReviewFinding, ...]
    unsafe_update_findings: tuple[ApplyPreviewReviewFinding, ...]
    overclaim_risks: tuple[ApplyPreviewReviewFinding, ...]
    safe_planning_notes: tuple[ApplyPreviewReviewFinding, ...]
    report_guardrails: tuple[str, ...]
    source: str = "result-evidence-action-plan-apply-preview-review"
    planning_only: bool = True
    review_state: str = "reviewed_not_applied"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_action_plan_apply_preview_review",
            "source": self.source,
            "recommendation": self.recommendation,
            "duplicate_update_candidates": [
                finding.to_dict() for finding in self.duplicate_update_candidates
            ],
            "blocked_action_findings": [
                finding.to_dict() for finding in self.blocked_action_findings
            ],
            "evidence_gap_findings": [
                finding.to_dict() for finding in self.evidence_gap_findings
            ],
            "unsafe_update_findings": [
                finding.to_dict() for finding in self.unsafe_update_findings
            ],
            "overclaim_risks": [finding.to_dict() for finding in self.overclaim_risks],
            "safe_planning_notes": [finding.to_dict() for finding in self.safe_planning_notes],
            "report_guardrails": list(self.report_guardrails),
            "planning_only": self.planning_only,
            "review_state": self.review_state,
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

    def to_markdown(self, title: str = "Action Plan Apply Preview Review") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: {self.recommendation}",
            "- State mutation performed by Blackhole: false",
            "- Case memory write: false",
            "- Research state write: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Duplicate Update Candidates",
            "",
        ]

        lines.extend(_render_findings(self.duplicate_update_candidates))
        lines.extend(["", "## Blocked Actions", ""])
        lines.extend(_render_findings(self.blocked_action_findings))
        lines.extend(["", "## Evidence Gaps", ""])
        lines.extend(_render_findings(self.evidence_gap_findings))
        lines.extend(["", "## Unsafe / Rejected Update Risks", ""])
        lines.extend(_render_findings(self.unsafe_update_findings))
        lines.extend(["", "## Report Overclaim Risks", ""])
        lines.extend(_render_findings(self.overclaim_risks))
        lines.extend(["", "## Safe Planning Notes", ""])
        lines.extend(_render_findings(self.safe_planning_notes))

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
                "- This command reviews an apply preview only.",
                "- Do not write case memory from this review.",
                "- Do not write research state from this review.",
                "- Do not treat preview candidates as vulnerability proof.",
                "- Close duplicate, evidence, and safety findings before any future apply step.",
                "",
            ]
        )

        return "\n".join(lines)


def build_action_plan_apply_preview_review(
    apply_preview: dict[str, Any],
    case_memory: dict[str, Any] | None = None,
    source: str = "result-evidence-action-plan-apply-preview-review",
) -> ActionPlanApplyPreviewReview:
    """Review a safe apply preview before any state-writing command exists."""
    _require_kind(
        apply_preview,
        "result_evidence_provider_suggestion_action_plan_apply_preview",
        "action plan apply preview",
    )

    if case_memory is not None:
        _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    case_memory_updates = _object_list(apply_preview.get("case_memory_updates"), "case_memory_updates")
    research_state_updates = _object_list(
        apply_preview.get("research_state_updates"),
        "research_state_updates",
    )
    blocked_updates = _object_list(apply_preview.get("blocked_updates"), "blocked_updates")

    missing_evidence = _dedupe(_string_list(apply_preview.get("missing_evidence")))
    if case_memory is not None:
        missing_evidence = _dedupe(missing_evidence + _string_list(case_memory.get("missing_evidence")))

    input_report_guardrails = _string_list(apply_preview.get("report_guardrails"))
    report_guardrails = _dedupe(
        input_report_guardrails
        + [
            "Apply preview review does not mutate case memory or research state.",
            "Do not use blocked updates until evidence gaps and safety concerns are closed.",
            "Do not claim a vulnerability from apply preview candidates.",
        ]
    )

    all_update_candidates = case_memory_updates + research_state_updates

    duplicate_findings = _duplicate_findings(
        all_update_candidates,
        existing_case_memory_actions=_known_case_memory_actions(case_memory),
    )
    blocked_findings = _blocked_findings(blocked_updates)
    evidence_findings = _evidence_gap_findings(missing_evidence, blocked_updates)
    unsafe_findings = _unsafe_update_findings(all_update_candidates, blocked_updates)
    overclaim_findings = _overclaim_findings(apply_preview, missing_evidence, input_report_guardrails)
    safe_notes = _safe_planning_notes(all_update_candidates, duplicate_findings, unsafe_findings)

    recommendation = _review_recommendation(
        duplicate_findings=duplicate_findings,
        blocked_findings=blocked_findings,
        evidence_findings=evidence_findings,
        unsafe_findings=unsafe_findings,
        overclaim_findings=overclaim_findings,
        safe_notes=safe_notes,
    )

    return ActionPlanApplyPreviewReview(
        recommendation=recommendation,
        duplicate_update_candidates=tuple(duplicate_findings),
        blocked_action_findings=tuple(blocked_findings),
        evidence_gap_findings=tuple(evidence_findings),
        unsafe_update_findings=tuple(unsafe_findings),
        overclaim_risks=tuple(overclaim_findings),
        safe_planning_notes=tuple(safe_notes),
        report_guardrails=tuple(report_guardrails),
        source=source,
    )


def _review_recommendation(
    duplicate_findings: list[ApplyPreviewReviewFinding],
    blocked_findings: list[ApplyPreviewReviewFinding],
    evidence_findings: list[ApplyPreviewReviewFinding],
    unsafe_findings: list[ApplyPreviewReviewFinding],
    overclaim_findings: list[ApplyPreviewReviewFinding],
    safe_notes: list[ApplyPreviewReviewFinding],
) -> str:
    if unsafe_findings:
        return "do-not-apply-review-unsafe-items"

    if blocked_findings or evidence_findings or overclaim_findings:
        if safe_notes:
            return "use-safe-items-as-planning-notes-only"
        return "hold-all-updates-until-evidence-gaps-close"

    if duplicate_findings:
        return "dedupe-before-use-as-planning-note"

    if safe_notes:
        return "safe-to-use-as-planning-note"

    return "no-actionable-preview-updates"


def _duplicate_findings(
    update_candidates: list[dict[str, Any]],
    existing_case_memory_actions: list[str],
) -> list[ApplyPreviewReviewFinding]:
    findings: list[ApplyPreviewReviewFinding] = []
    seen: dict[tuple[str, str], str] = {}

    for raw in update_candidates:
        action = _optional_text(raw.get("action"), "")
        target = _optional_text(raw.get("target_artifact"), "unknown")
        if not action:
            continue

        key = (target.lower(), _normalize_action(action))
        if key in seen:
            findings.append(
                ApplyPreviewReviewFinding(
                    category="duplicate-update-candidate",
                    severity="low",
                    message="Duplicate update candidate appears in the same target artifact.",
                    action=action,
                    source=target,
                    evidence_needed=(),
                )
            )
        else:
            seen[key] = action

    existing = {_normalize_action(action) for action in existing_case_memory_actions}
    for raw in update_candidates:
        action = _optional_text(raw.get("action"), "")
        target = _optional_text(raw.get("target_artifact"), "unknown")
        if not action:
            continue

        if target == "case_memory" and _normalize_action(action) in existing:
            findings.append(
                ApplyPreviewReviewFinding(
                    category="duplicate-existing-case-memory-action",
                    severity="low",
                    message="Candidate appears to already exist in case memory.",
                    action=action,
                    source="case_memory",
                    evidence_needed=(),
                )
            )

    return findings


def _blocked_findings(blocked_updates: list[dict[str, Any]]) -> list[ApplyPreviewReviewFinding]:
    findings: list[ApplyPreviewReviewFinding] = []

    for raw in blocked_updates:
        action = _optional_text(raw.get("action"), "blocked action")
        operation = _optional_text(raw.get("preview_operation"), "blocked")
        status = _optional_text(raw.get("source_status"), "blocked")
        evidence = _string_list(raw.get("evidence_needed"))

        findings.append(
            ApplyPreviewReviewFinding(
                category="blocked-update",
                severity="high" if _looks_unsafe(operation + " " + status + " " + action) else "medium",
                message="Update is blocked and must not be applied automatically.",
                action=action,
                source=operation,
                evidence_needed=tuple(evidence or ["Local evidence and manual review"]),
            )
        )

    return findings


def _evidence_gap_findings(
    missing_evidence: list[str],
    blocked_updates: list[dict[str, Any]],
) -> list[ApplyPreviewReviewFinding]:
    findings: list[ApplyPreviewReviewFinding] = []

    for evidence in missing_evidence:
        findings.append(
            ApplyPreviewReviewFinding(
                category="missing-evidence",
                severity="medium",
                message="Missing evidence must be closed before any report or future apply step.",
                action=evidence,
                source="missing_evidence",
                evidence_needed=(evidence,),
            )
        )

    for raw in blocked_updates:
        for evidence in _string_list(raw.get("evidence_needed")):
            findings.append(
                ApplyPreviewReviewFinding(
                    category="blocked-action-evidence-gap",
                    severity="medium",
                    message="Blocked action still requires local evidence.",
                    action=_optional_text(raw.get("action"), "blocked action"),
                    source=_optional_text(raw.get("preview_operation"), "blocked"),
                    evidence_needed=(evidence,),
                )
            )

    return _dedupe_findings(findings)


def _unsafe_update_findings(
    update_candidates: list[dict[str, Any]],
    blocked_updates: list[dict[str, Any]],
) -> list[ApplyPreviewReviewFinding]:
    findings: list[ApplyPreviewReviewFinding] = []

    for raw in update_candidates + blocked_updates:
        action = _optional_text(raw.get("action"), "")
        operation = _optional_text(raw.get("preview_operation"), "")
        status = _optional_text(raw.get("source_status"), "")
        combined = " ".join([action, operation, status])

        if not _looks_unsafe(combined):
            continue

        findings.append(
            ApplyPreviewReviewFinding(
                category="unsafe-or-rejected-update-risk",
                severity="high",
                message="Candidate contains unsafe, rejected, or execution-like wording.",
                action=action or "unknown action",
                source=operation or status or "apply_preview",
                evidence_needed=tuple(_string_list(raw.get("evidence_needed")) or ["Manual safety review"]),
            )
        )

    return _dedupe_findings(findings)


def _overclaim_findings(
    apply_preview: dict[str, Any],
    missing_evidence: list[str],
    report_guardrails: list[str],
) -> list[ApplyPreviewReviewFinding]:
    findings: list[ApplyPreviewReviewFinding] = []

    safety = apply_preview.get("safety")
    if isinstance(safety, dict) and safety.get("vulnerability_confirmation") is not False:
        findings.append(
            ApplyPreviewReviewFinding(
                category="safety-metadata-risk",
                severity="high",
                message="Apply preview safety metadata does not explicitly keep vulnerability confirmation false.",
                action="vulnerability_confirmation",
                source="safety",
                evidence_needed=("Correct safety metadata before use",),
            )
        )

    for guardrail in report_guardrails:
        if _mentions_overclaim_risk(guardrail):
            findings.append(
                ApplyPreviewReviewFinding(
                    category="report-overclaim-risk",
                    severity="medium",
                    message="Report guardrail warns about possible overclaiming.",
                    action=guardrail,
                    source="report_guardrails",
                    evidence_needed=tuple(missing_evidence or ["Local proof before report wording"]),
                )
            )

    if missing_evidence:
        findings.append(
            ApplyPreviewReviewFinding(
                category="report-overclaim-risk",
                severity="medium",
                message="Missing evidence creates report overclaim risk.",
                action="missing evidence remains open",
                source="missing_evidence",
                evidence_needed=tuple(missing_evidence),
            )
        )

    return _dedupe_findings(findings)


def _safe_planning_notes(
    update_candidates: list[dict[str, Any]],
    duplicate_findings: list[ApplyPreviewReviewFinding],
    unsafe_findings: list[ApplyPreviewReviewFinding],
) -> list[ApplyPreviewReviewFinding]:
    duplicate_keys = {_normalize_action(item.action) for item in duplicate_findings}
    unsafe_keys = {_normalize_action(item.action) for item in unsafe_findings}

    notes: list[ApplyPreviewReviewFinding] = []
    for raw in update_candidates:
        action = _optional_text(raw.get("action"), "")
        if not action:
            continue

        normalized = _normalize_action(action)
        if normalized in unsafe_keys:
            continue

        notes.append(
            ApplyPreviewReviewFinding(
                category="safe-planning-note",
                severity="info",
                message="Candidate can be kept as a manual planning note after human review.",
                action=action,
                source=_optional_text(raw.get("target_artifact"), "unknown"),
                evidence_needed=tuple(_string_list(raw.get("evidence_needed"))),
            )
        )

    if duplicate_keys:
        notes = [note for note in notes if _normalize_action(note.action) not in duplicate_keys] + [
            note for note in notes if _normalize_action(note.action) in duplicate_keys
        ]

    return _dedupe_findings(notes)


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


def _render_findings(findings: tuple[ApplyPreviewReviewFinding, ...]) -> list[str]:
    if not findings:
        return ["- none"]

    lines: list[str] = []
    for finding in findings:
        lines.append(f"- **{finding.severity} / {finding.category}**: {finding.action}")
        lines.append(f"  - Source: {finding.source}")
        lines.append(f"  - Finding: {finding.message}")
        if finding.evidence_needed:
            lines.append("  - Evidence needed:")
            for evidence in finding.evidence_needed:
                lines.append(f"    - {evidence}")

    return lines


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"apply preview requires {label} list")

    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"each {label} item must be an object")
        output.append(item)

    return output


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _optional_text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _normalize_action(value: str) -> str:
    return " ".join(value.lower().split())


def _looks_unsafe(value: str) -> bool:
    lowered = value.lower()
    unsafe_terms = (
        "unsafe",
        "rejected",
        "execute",
        "run command",
        "dump data",
        "bypass authorization",
        "exploit automatically",
        "mutate",
        "delete",
        "write state",
    )
    return any(term in lowered for term in unsafe_terms)


def _mentions_overclaim_risk(value: str) -> bool:
    lowered = value.lower()
    risky_terms = (
        "confirmed vulnerability",
        "claim",
        "severity",
        "proof",
        "report",
        "overclaim",
        "do not claim",
        "evidence",
    )
    return any(term in lowered for term in risky_terms)


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


def _dedupe_findings(findings: list[ApplyPreviewReviewFinding]) -> list[ApplyPreviewReviewFinding]:
    seen: set[tuple[str, str, str]] = set()
    output: list[ApplyPreviewReviewFinding] = []

    for finding in findings:
        key = (
            finding.category.lower(),
            finding.action.lower(),
            finding.source.lower(),
        )
        if key in seen:
            continue

        seen.add(key)
        output.append(finding)

    return output
