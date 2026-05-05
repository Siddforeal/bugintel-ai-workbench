"""
Manual validation planner for Blackhole AI Workbench result evidence hypotheses.

This module turns local, planning-only evidence hypotheses into a structured
manual validation plan. It does not confirm vulnerabilities, send requests,
execute shell commands, launch browsers, use Kali tools, call LLM providers,
mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationStep:
    title: str
    purpose: str
    action: str
    expected_evidence: str
    safety_note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HypothesisValidationPlan:
    endpoint: str
    hypothesis_class: str
    confidence: str
    evidence_strength: str
    severity_hint: str
    priority: str
    source: str
    steps: tuple[ValidationStep, ...]
    stop_conditions: tuple[str, ...]
    report_readiness_checks: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "hypothesis_class": self.hypothesis_class,
            "confidence": self.confidence,
            "evidence_strength": self.evidence_strength,
            "severity_hint": self.severity_hint,
            "priority": self.priority,
            "source": self.source,
            "steps": [step.to_dict() for step in self.steps],
            "stop_conditions": list(self.stop_conditions),
            "report_readiness_checks": list(self.report_readiness_checks),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class ResultEvidenceValidationPlan:
    plans: tuple[HypothesisValidationPlan, ...]
    source: str = "result-evidence-validation-plan"
    kind: str = "result_evidence_validation_plan"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        priority_counts: dict[str, int] = {}

        for plan in self.plans:
            priority_counts[plan.priority] = priority_counts.get(plan.priority, 0) + 1

        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.plans),
            "priority_counts": priority_counts,
            "plans": [plan.to_dict() for plan in self.plans],
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

    def to_markdown(self, title: str = "Manual Validation Plan") -> str:
        data = self.to_dict()
        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Validation plans: {data['count']}")
        lines.append("- Planning-only: true")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        lines.append("## Priority Counts")
        lines.append("")
        if data["priority_counts"]:
            for priority, count in sorted(data["priority_counts"].items()):
                lines.append(f"- {priority}: {count}")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Plans")
        lines.append("")

        if not self.plans:
            lines.append("_No validation plans were generated._")
            lines.append("")
        else:
            for index, plan in enumerate(self.plans, start=1):
                lines.append(f"### {index}. `{plan.endpoint}`")
                lines.append("")
                lines.append(f"- Hypothesis class: **{plan.hypothesis_class}**")
                lines.append(f"- Confidence: {plan.confidence}")
                lines.append(f"- Evidence strength: {plan.evidence_strength}")
                lines.append(f"- Severity hint: {plan.severity_hint}")
                lines.append(f"- Priority: {plan.priority}")
                lines.append(f"- Source: `{plan.source}`")
                lines.append("")
                lines.append("#### Manual Steps")
                lines.append("")
                for step_index, step in enumerate(plan.steps, start=1):
                    lines.append(f"{step_index}. **{step.title}**")
                    lines.append(f"   - Purpose: {step.purpose}")
                    lines.append(f"   - Action: {step.action}")
                    lines.append(f"   - Expected evidence: {step.expected_evidence}")
                    lines.append(f"   - Safety: {step.safety_note}")
                lines.append("")
                lines.append("#### Stop Conditions")
                lines.append("")
                for item in plan.stop_conditions:
                    lines.append(f"- {item}")
                lines.append("")
                lines.append("#### Report Readiness Checks")
                lines.append("")
                for item in plan.report_readiness_checks:
                    lines.append(f"- {item}")
                lines.append("")

        lines.append("## Safety")
        lines.append("")
        lines.append("- This is a local planning artifact.")
        lines.append("- It does not execute tests.")
        lines.append("- It does not send requests.")
        lines.append("- It does not mutate targets.")
        lines.append("- It does not bypass authorization.")
        lines.append("- It does not confirm vulnerabilities.")
        lines.append("")

        return "\n".join(lines)


def build_result_evidence_validation_plan(
    hypothesis_data: dict[str, Any],
    high_priority_only: bool = False,
    source: str = "result-evidence-validation-plan",
) -> ResultEvidenceValidationPlan:
    """Build a manual validation plan from local result evidence hypotheses."""
    if not isinstance(hypothesis_data, dict):
        raise ValueError("hypothesis data must be an object")

    if hypothesis_data.get("kind") != "result_evidence_hypothesis_set":
        raise ValueError("validation plan requires kind=result_evidence_hypothesis_set")

    hypotheses = hypothesis_data.get("hypotheses")
    if not isinstance(hypotheses, list):
        raise ValueError("validation plan requires a hypotheses list")

    plans: list[HypothesisValidationPlan] = []

    for raw_hypothesis in hypotheses:
        if not isinstance(raw_hypothesis, dict):
            raise ValueError("each hypothesis must be an object")

        plan = _build_plan_for_hypothesis(raw_hypothesis)

        if high_priority_only and plan.priority not in {"high", "medium-high"}:
            continue

        plans.append(plan)

    return ResultEvidenceValidationPlan(plans=tuple(plans), source=source)


def _build_plan_for_hypothesis(hypothesis: dict[str, Any]) -> HypothesisValidationPlan:
    endpoint = str(hypothesis.get("endpoint") or "").strip()
    if not endpoint:
        raise ValueError("each hypothesis requires an endpoint")

    hypothesis_class = str(hypothesis.get("hypothesis_class") or "needs-more-evidence")
    confidence = str(hypothesis.get("confidence") or "unknown")
    evidence_strength = str(hypothesis.get("evidence_strength") or "weak-candidate")
    severity_hint = str(hypothesis.get("severity_hint") or "needs-validation")
    source = str(hypothesis.get("source") or "unknown")

    priority = _priority(hypothesis_class, evidence_strength, severity_hint)
    steps = _steps_for_hypothesis(hypothesis_class)
    stop_conditions = _stop_conditions(hypothesis_class)
    readiness_checks = _report_readiness_checks(hypothesis_class)

    return HypothesisValidationPlan(
        endpoint=endpoint,
        hypothesis_class=hypothesis_class,
        confidence=confidence,
        evidence_strength=evidence_strength,
        severity_hint=severity_hint,
        priority=priority,
        source=source,
        steps=tuple(steps),
        stop_conditions=tuple(stop_conditions),
        report_readiness_checks=tuple(readiness_checks),
    )


def _priority(hypothesis_class: str, evidence_strength: str, severity_hint: str) -> str:
    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return "low"

    if evidence_strength == "strong-candidate" and "high" in severity_hint:
        return "high"

    if evidence_strength in {"strong-candidate", "medium-candidate"}:
        return "medium-high"

    if hypothesis_class == "needs-more-evidence":
        return "medium-low"

    return "medium"


def _steps_for_hypothesis(hypothesis_class: str) -> list[ValidationStep]:
    common = [
        ValidationStep(
            title="Confirm scope and authorization",
            purpose="Ensure the target, account, tenant, endpoint, and data are permitted by the program rules.",
            action="Review program scope and confirm all test accounts, objects, and identifiers are controlled or authorized.",
            expected_evidence="A short scope note identifying the allowed asset and controlled test accounts.",
            safety_note="Do not proceed if the asset, account, tenant, or data is out of scope.",
        ),
        ValidationStep(
            title="Capture own-object baseline",
            purpose="Establish expected behavior for an object the tester is allowed to access.",
            action="Record the own-account or own-object request and response using a controlled account.",
            expected_evidence="Raw request/response pair showing legitimate access and relevant ownership indicators.",
            safety_note="Redact cookies, bearer tokens, API keys, and personal data before storing or sharing evidence.",
        ),
        ValidationStep(
            title="Capture foreign-object or second-account behavior",
            purpose="Check whether the suspected boundary issue appears when using a different controlled account or object.",
            action="Repeat the same request pattern against the second controlled account/object where allowed.",
            expected_evidence="Raw request/response pair showing observed status, response body, object identifiers, and ownership markers.",
            safety_note="Use only accounts and objects you control or are explicitly authorized to test.",
        ),
        ValidationStep(
            title="Capture random-object baseline",
            purpose="Rule out generic success, generic error, object-not-found behavior, or false positives.",
            action="Repeat the request with a random or known-nonexistent object identifier.",
            expected_evidence="Raw request/response pair showing whether the suspected response differs from random-object behavior.",
            safety_note="Avoid brute force or identifier enumeration.",
        ),
    ]

    if hypothesis_class in {
        "object-or-tenant-authorization-boundary-candidate",
        "cross-account-or-cross-tenant-access-candidate",
        "authorization-bypass-candidate",
    }:
        return common + [
            ValidationStep(
                title="Compare authorization boundary",
                purpose="Determine whether the foreign-object behavior violates an expected authorization boundary.",
                action="Compare own-object, foreign-object, random-object, and unauthenticated or expired-session baselines where allowed.",
                expected_evidence="A concise comparison table of statuses, response sizes, sensitive fields, and ownership markers.",
                safety_note="Do not attempt privilege escalation or destructive actions.",
            ),
            ValidationStep(
                title="Verify sensitive or tenant-specific data",
                purpose="Confirm whether returned data is actually private, tenant-specific, or security relevant.",
                action="Identify the exact fields returned and map them to account, project, user, tenant, or object ownership.",
                expected_evidence="Redacted field-level evidence showing why the data should not be accessible.",
                safety_note="Minimize collection and redact personal or sensitive values.",
            ),
            ValidationStep(
                title="Check role and session assumptions",
                purpose="Rule out expected access caused by shared roles, public objects, inherited permissions, or stale sessions.",
                action="Repeat the comparison with the lowest-privileged controlled role and a fresh session when permitted.",
                expected_evidence="Role/session notes showing the minimum privileges needed to reproduce.",
                safety_note="Stay within program-permitted accounts and roles.",
            ),
        ]

    if hypothesis_class == "information-disclosure-candidate":
        return common + [
            ValidationStep(
                title="Identify exposed data type",
                purpose="Determine whether the exposed fields are sensitive, private, internal, or tenant-specific.",
                action="List only field names and redacted examples needed to prove the data class.",
                expected_evidence="A redacted field list and explanation of why the fields are sensitive.",
                safety_note="Do not store unnecessary personal data or secrets.",
            ),
            ValidationStep(
                title="Check access prerequisites",
                purpose="Determine who can access the data and under what conditions.",
                action="Compare authenticated, lower-privileged, expired-session, and unauthenticated behavior only where allowed.",
                expected_evidence="A minimal access matrix showing which controlled contexts can access the data.",
                safety_note="Do not test accounts or roles you do not own or have authorization to use.",
            ),
        ]

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return [
            ValidationStep(
                title="Confirm expected blocking",
                purpose="Verify that the behavior matches expected access control or generic random-object behavior.",
                action="Compare the suspected response to own-object, foreign-object, and random-object baselines.",
                expected_evidence="Evidence showing whether the response is meaningfully different from expected blocking.",
                safety_note="Do not report if no security boundary violation is proven.",
            ),
            ValidationStep(
                title="Search for missing evidence",
                purpose="Determine whether any reportable impact is actually present.",
                action="Check for sensitive fields, ownership mismatch, or unauthorized state access in existing saved evidence only.",
                expected_evidence="A conclusion note explaining why the item is rejected or what evidence is missing.",
                safety_note="Avoid extra target probing unless explicitly in scope and necessary.",
            ),
        ]

    return common + [
        ValidationStep(
            title="Collect missing expected behavior",
            purpose="Fill the gaps that prevent classification.",
            action="Capture expected status, expected body shape, and ownership markers for legitimate and blocked cases.",
            expected_evidence="Expected behavior notes and raw redacted examples.",
            safety_note="Keep validation read-only and scoped.",
        ),
    ]


def _stop_conditions(hypothesis_class: str) -> list[str]:
    base = [
        "Stop if the asset, endpoint, account, tenant, or object is out of scope.",
        "Stop if reproduction requires accounts, roles, or data you are not authorized to use.",
        "Stop if the behavior matches random-object or expected blocking behavior.",
        "Stop if no sensitive, private, tenant-specific, or security-relevant data/state is exposed.",
    ]

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return base + [
            "Stop and mark rejected if all baselines match expected blocking.",
        ]

    return base + [
        "Stop before any destructive, state-changing, or high-volume testing.",
        "Stop if additional testing would require bypassing rate limits or access controls.",
    ]


def _report_readiness_checks(hypothesis_class: str) -> list[str]:
    checks = [
        "Scope is confirmed.",
        "Own-object baseline is captured.",
        "Foreign-object or second-account behavior is captured.",
        "Random-object baseline is captured.",
        "Raw requests and responses are preserved with secrets redacted.",
        "The finding draft does not overclaim impact.",
    ]

    if hypothesis_class != "likely-expected-blocking-or-false-positive":
        checks.extend(
            [
                "Sensitive or tenant-specific data/state is identified.",
                "Authorization boundary expectation is explained.",
                "Reproduction is repeatable with controlled accounts.",
                "Impact is tied directly to proven evidence.",
            ]
        )

    return checks
