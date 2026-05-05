"""
Case intelligence summary for Blackhole AI Workbench result evidence workflows.

This module turns a local result evidence validation plan into a case-level
intelligence summary. It does not confirm vulnerabilities, send requests,
execute shell commands, launch browsers, use Kali tools, call LLM providers,
mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CaseSummaryFinding:
    endpoint: str
    hypothesis_class: str
    priority: str
    readiness: str
    evidence_strength: str
    severity_hint: str
    confidence: str
    summary: str
    missing_evidence: tuple[str, ...]
    next_actions: tuple[str, ...]
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "hypothesis_class": self.hypothesis_class,
            "priority": self.priority,
            "readiness": self.readiness,
            "evidence_strength": self.evidence_strength,
            "severity_hint": self.severity_hint,
            "confidence": self.confidence,
            "summary": self.summary,
            "missing_evidence": list(self.missing_evidence),
            "next_actions": list(self.next_actions),
            "source": self.source,
        }


@dataclass(frozen=True)
class ResultEvidenceCaseSummary:
    findings: tuple[CaseSummaryFinding, ...]
    source: str = "result-evidence-case-summary"
    kind: str = "result_evidence_case_summary"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        readiness_counts: dict[str, int] = {}
        priority_counts: dict[str, int] = {}

        for finding in self.findings:
            readiness_counts[finding.readiness] = readiness_counts.get(finding.readiness, 0) + 1
            priority_counts[finding.priority] = priority_counts.get(finding.priority, 0) + 1

        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.findings),
            "priority_counts": priority_counts,
            "readiness_counts": readiness_counts,
            "strongest_candidates": [
                finding.to_dict()
                for finding in self.findings
                if finding.readiness in {"near-report-ready", "needs-final-validation"}
            ],
            "weak_or_rejected_candidates": [
                finding.to_dict()
                for finding in self.findings
                if finding.readiness in {"likely-false-positive", "not-reportable-currently"}
            ],
            "findings": [finding.to_dict() for finding in self.findings],
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Case Intelligence Summary") -> str:
        data = self.to_dict()
        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Findings reviewed: {data['count']}")
        lines.append("- Planning-only: true")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        lines.append("## Priority Counts")
        lines.append("")
        if data["priority_counts"]:
            for key, value in sorted(data["priority_counts"].items()):
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Readiness Counts")
        lines.append("")
        if data["readiness_counts"]:
            for key, value in sorted(data["readiness_counts"].items()):
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Strongest Candidates")
        lines.append("")
        strongest = data["strongest_candidates"]
        if strongest:
            for finding in strongest:
                lines.extend(_finding_markdown(finding))
        else:
            lines.append("_No near-report-ready candidates were identified._")
            lines.append("")

        lines.append("## Weak / Rejected / Not Reportable Currently")
        lines.append("")
        weak = data["weak_or_rejected_candidates"]
        if weak:
            for finding in weak:
                lines.extend(_finding_markdown(finding))
        else:
            lines.append("_No weak or rejected candidates were identified._")
            lines.append("")

        lines.append("## All Findings")
        lines.append("")
        if self.findings:
            for finding in self.findings:
                lines.extend(_finding_markdown(finding.to_dict()))
        else:
            lines.append("_No findings were present in the validation plan._")
            lines.append("")

        lines.append("## Case-Level Next Actions")
        lines.append("")
        lines.append("- Start with high-priority or medium-high-priority candidates.")
        lines.append("- Complete missing baselines before drafting final impact.")
        lines.append("- Reject candidates that match random-object or expected-blocking behavior.")
        lines.append("- Preserve raw request/response evidence separately.")
        lines.append("- Keep the final report human-written and avoid overclaiming.")
        lines.append("")

        lines.append("## Safety")
        lines.append("")
        lines.append("- This is a local planning summary.")
        lines.append("- It does not execute tests.")
        lines.append("- It does not send requests.")
        lines.append("- It does not mutate targets.")
        lines.append("- It does not bypass authorization.")
        lines.append("- It does not confirm vulnerabilities.")
        lines.append("")

        return "\n".join(lines)


def build_result_evidence_case_summary(
    validation_plan_data: dict[str, Any],
    source: str = "result-evidence-case-summary",
) -> ResultEvidenceCaseSummary:
    """Build a case-level intelligence summary from a local validation plan JSON."""
    if not isinstance(validation_plan_data, dict):
        raise ValueError("validation plan data must be an object")

    if validation_plan_data.get("kind") != "result_evidence_validation_plan":
        raise ValueError("case summary requires kind=result_evidence_validation_plan")

    plans = validation_plan_data.get("plans")
    if not isinstance(plans, list):
        raise ValueError("case summary requires a plans list")

    findings: list[CaseSummaryFinding] = []

    for raw_plan in plans:
        if not isinstance(raw_plan, dict):
            raise ValueError("each validation plan must be an object")

        findings.append(_summarize_plan(raw_plan))

    return ResultEvidenceCaseSummary(findings=tuple(findings), source=source)


def _summarize_plan(plan: dict[str, Any]) -> CaseSummaryFinding:
    endpoint = str(plan.get("endpoint") or "").strip()
    if not endpoint:
        raise ValueError("each validation plan requires an endpoint")

    hypothesis_class = str(plan.get("hypothesis_class") or "needs-more-evidence")
    priority = str(plan.get("priority") or "medium")
    evidence_strength = str(plan.get("evidence_strength") or "weak-candidate")
    severity_hint = str(plan.get("severity_hint") or "needs-validation")
    confidence = str(plan.get("confidence") or "unknown")
    source = str(plan.get("source") or "unknown")

    steps = plan.get("steps") if isinstance(plan.get("steps"), list) else []
    readiness_checks = plan.get("report_readiness_checks") if isinstance(plan.get("report_readiness_checks"), list) else []
    stop_conditions = plan.get("stop_conditions") if isinstance(plan.get("stop_conditions"), list) else []

    readiness = _readiness(hypothesis_class, priority, evidence_strength, severity_hint, steps, readiness_checks)
    missing_evidence = tuple(_missing_evidence(hypothesis_class, readiness_checks, stop_conditions))
    next_actions = tuple(_next_actions(hypothesis_class, readiness, steps))

    return CaseSummaryFinding(
        endpoint=endpoint,
        hypothesis_class=hypothesis_class,
        priority=priority,
        readiness=readiness,
        evidence_strength=evidence_strength,
        severity_hint=severity_hint,
        confidence=confidence,
        summary=_summary_text(hypothesis_class, readiness, priority),
        missing_evidence=missing_evidence,
        next_actions=next_actions,
        source=source,
    )


def _readiness(
    hypothesis_class: str,
    priority: str,
    evidence_strength: str,
    severity_hint: str,
    steps: list[Any],
    readiness_checks: list[Any],
) -> str:
    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return "likely-false-positive"

    if priority == "high" and evidence_strength == "strong-candidate" and "high" in severity_hint:
        return "needs-final-validation"

    if priority in {"high", "medium-high"} and len(steps) >= 5 and len(readiness_checks) >= 8:
        return "needs-final-validation"

    if priority in {"medium", "medium-low"}:
        return "needs-more-evidence"

    return "not-reportable-currently"


def _missing_evidence(
    hypothesis_class: str,
    readiness_checks: list[Any],
    stop_conditions: list[Any],
) -> list[str]:
    missing: list[str] = []

    readiness_text = " ".join(str(item).lower() for item in readiness_checks)
    stop_text = " ".join(str(item).lower() for item in stop_conditions)

    required = {
        "scope": "Scope confirmation",
        "own-object": "Own-object or own-account baseline",
        "foreign-object": "Foreign-object or second-account behavior",
        "random-object": "Random-object baseline",
        "raw requests": "Raw request/response evidence",
        "sensitive": "Sensitive or tenant-specific data identification",
        "impact": "Impact tied directly to proven evidence",
    }

    for keyword, label in required.items():
        if keyword not in readiness_text:
            missing.append(label)

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        missing = ["Evidence proving behavior differs from expected blocking or random-object behavior"]

    if "out of scope" not in stop_text:
        missing.append("Explicit out-of-scope stop condition")

    return missing


def _next_actions(hypothesis_class: str, readiness: str, steps: list[Any]) -> list[str]:
    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return [
            "Compare the candidate with random-object and expected-blocking behavior.",
            "Reject the candidate if no sensitive data or authorization boundary violation is proven.",
        ]

    if readiness == "needs-final-validation":
        return [
            "Complete the highest-value manual validation steps first.",
            "Capture own-object, foreign-object, and random-object baselines.",
            "Confirm sensitive or tenant-specific data before claiming impact.",
            "Prepare final report only after repeatability and scope are confirmed.",
        ]

    if readiness == "needs-more-evidence":
        return [
            "Collect missing baselines and expected behavior.",
            "Clarify whether the response contains private or tenant-specific data.",
            "Run only scoped, read-only, controlled-account validation.",
        ]

    if steps:
        return [
            "Review the generated manual validation steps.",
            "Collect missing evidence before treating this as reportable.",
        ]

    return ["Add more evidence before continuing."]


def _summary_text(hypothesis_class: str, readiness: str, priority: str) -> str:
    if readiness == "likely-false-positive":
        return "Current validation plan suggests expected blocking or a likely false positive."

    if readiness == "needs-final-validation":
        return f"This {priority}-priority candidate may be worth final manual validation before drafting a report."

    if readiness == "needs-more-evidence":
        return "The candidate needs more baselines or clearer evidence before reportability can be assessed."

    return "The candidate is not reportable with current evidence."


def _finding_markdown(finding: dict[str, Any]) -> list[str]:
    lines: list[str] = []

    lines.append(f"### `{finding['endpoint']}`")
    lines.append("")
    lines.append(f"- Hypothesis class: **{finding['hypothesis_class']}**")
    lines.append(f"- Priority: {finding['priority']}")
    lines.append(f"- Readiness: {finding['readiness']}")
    lines.append(f"- Evidence strength: {finding['evidence_strength']}")
    lines.append(f"- Severity hint: {finding['severity_hint']}")
    lines.append(f"- Confidence: {finding['confidence']}")
    lines.append(f"- Source: `{finding['source']}`")
    lines.append(f"- Summary: {finding['summary']}")
    lines.append("")

    lines.append("Missing evidence:")
    missing = finding.get("missing_evidence") or []
    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.append("")

    lines.append("Next actions:")
    actions = finding.get("next_actions") or []
    if actions:
        for item in actions:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.append("")

    return lines
