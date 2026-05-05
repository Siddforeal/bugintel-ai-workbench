"""
Evidence-to-hypothesis engine for Blackhole AI Workbench.

This module turns local result evidence batch review JSON into planning-only
security hypotheses. It does not confirm vulnerabilities, send requests,
execute shell commands, launch browsers, use Kali tools, call LLM providers,
mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ResultEvidenceHypothesisSignal:
    name: str
    weight: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultEvidenceHypothesis:
    endpoint: str
    hypothesis_class: str
    confidence: str
    evidence_strength: str
    severity_hint: str
    reason: str
    suggested_result: str
    source: str
    observed_status: int | None = None
    expected_status: int | None = None
    signals: tuple[ResultEvidenceHypothesisSignal, ...] = ()
    next_manual_tests: tuple[str, ...] = ()
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "hypothesis_class": self.hypothesis_class,
            "confidence": self.confidence,
            "evidence_strength": self.evidence_strength,
            "severity_hint": self.severity_hint,
            "reason": self.reason,
            "suggested_result": self.suggested_result,
            "source": self.source,
            "observed_status": self.observed_status,
            "expected_status": self.expected_status,
            "signals": [signal.to_dict() for signal in self.signals],
            "next_manual_tests": list(self.next_manual_tests),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class ResultEvidenceHypothesisSet:
    hypotheses: tuple[ResultEvidenceHypothesis, ...]
    source: str = "result-evidence-hypothesis"
    kind: str = "result_evidence_hypothesis_set"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        class_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}

        for hypothesis in self.hypotheses:
            class_counts[hypothesis.hypothesis_class] = class_counts.get(hypothesis.hypothesis_class, 0) + 1
            severity_counts[hypothesis.severity_hint] = severity_counts.get(hypothesis.severity_hint, 0) + 1

        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.hypotheses),
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "class_counts": class_counts,
            "severity_counts": severity_counts,
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

    def to_markdown(self, title: str = "Result Evidence Hypotheses") -> str:
        lines: list[str] = []
        data = self.to_dict()

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Hypotheses: {data['count']}")
        lines.append(f"- Planning-only: {self.planning_only}")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        lines.append("## Class Counts")
        lines.append("")
        if data["class_counts"]:
            for key, value in sorted(data["class_counts"].items()):
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Hypotheses")
        lines.append("")

        if not self.hypotheses:
            lines.append("_No hypotheses generated._")
            lines.append("")
        else:
            for index, hypothesis in enumerate(self.hypotheses, start=1):
                lines.append(f"### {index}. `{hypothesis.endpoint}`")
                lines.append("")
                lines.append(f"- Hypothesis class: **{hypothesis.hypothesis_class}**")
                lines.append(f"- Confidence: {hypothesis.confidence}")
                lines.append(f"- Evidence strength: {hypothesis.evidence_strength}")
                lines.append(f"- Severity hint: {hypothesis.severity_hint}")
                lines.append(f"- Review suggestion: {hypothesis.suggested_result}")
                lines.append(f"- Source: `{hypothesis.source}`")
                lines.append(f"- Observed status: {_display_value(hypothesis.observed_status)}")
                lines.append(f"- Expected status: {_display_value(hypothesis.expected_status)}")
                lines.append(f"- Reason: {hypothesis.reason}")
                lines.append("")
                lines.append("Signals:")
                for signal in hypothesis.signals:
                    lines.append(f"- {signal.name} ({signal.weight}): {signal.reason}")
                lines.append("")
                lines.append("Next manual tests:")
                for test in hypothesis.next_manual_tests:
                    lines.append(f"- {test}")
                lines.append("")

        lines.append("## Safety")
        lines.append("")
        lines.append("- Local-only hypothesis generation.")
        lines.append("- Planning-only output.")
        lines.append("- No target interaction.")
        lines.append("- No tool execution.")
        lines.append("- No LLM provider calls.")
        lines.append("- No vulnerability confirmation.")
        lines.append("")

        return "\n".join(lines)


def generate_result_evidence_hypotheses(
    review_data: dict[str, Any],
    supported_only: bool = False,
    source: str = "result-evidence-hypothesis",
) -> ResultEvidenceHypothesisSet:
    """Generate planning-only security hypotheses from local batch review JSON."""
    if not isinstance(review_data, dict):
        raise ValueError("result evidence review data must be an object")

    if review_data.get("kind") != "result_evidence_batch_review":
        raise ValueError("hypothesis generation requires kind=result_evidence_batch_review")

    items = review_data.get("items")
    if not isinstance(items, list):
        raise ValueError("hypothesis generation requires an items list")

    hypotheses: list[ResultEvidenceHypothesis] = []

    for raw_item in items:
        if not isinstance(raw_item, dict):
            raise ValueError("each review item must be an object")

        suggested_result = str(raw_item.get("suggested_result") or "needs-more-evidence")

        if supported_only and suggested_result != "supported":
            continue

        hypotheses.append(_hypothesize_item(raw_item))

    return ResultEvidenceHypothesisSet(hypotheses=tuple(hypotheses), source=source)


def _hypothesize_item(item: dict[str, Any]) -> ResultEvidenceHypothesis:
    endpoint = str(item.get("endpoint") or "").strip()
    if not endpoint:
        raise ValueError("each review item requires an endpoint")

    suggested_result = str(item.get("suggested_result") or "needs-more-evidence")
    source = str(item.get("source") or "unknown")
    observed_status = _optional_int(item.get("observed_status"))
    expected_status = _optional_int(item.get("expected_status"))
    rationale = str(item.get("rationale") or "")
    text = " ".join([endpoint, source, rationale]).lower()

    signals = list(_base_signals(suggested_result, observed_status, expected_status, text))
    score = sum(signal.weight for signal in signals)

    hypothesis_class = _hypothesis_class(suggested_result, observed_status, expected_status, text, score)
    confidence = _confidence(suggested_result, score)
    evidence_strength = _evidence_strength(suggested_result, score)
    severity_hint = _severity_hint(hypothesis_class, evidence_strength)
    reason = _reason(hypothesis_class, suggested_result, observed_status, expected_status)
    next_tests = _next_manual_tests(hypothesis_class)

    return ResultEvidenceHypothesis(
        endpoint=endpoint,
        hypothesis_class=hypothesis_class,
        confidence=confidence,
        evidence_strength=evidence_strength,
        severity_hint=severity_hint,
        reason=reason,
        suggested_result=suggested_result,
        source=source,
        observed_status=observed_status,
        expected_status=expected_status,
        signals=tuple(signals),
        next_manual_tests=tuple(next_tests),
    )


def _base_signals(
    suggested_result: str,
    observed_status: int | None,
    expected_status: int | None,
    text: str,
) -> tuple[ResultEvidenceHypothesisSignal, ...]:
    signals: list[ResultEvidenceHypothesisSignal] = []

    if suggested_result == "supported":
        signals.append(ResultEvidenceHypothesisSignal("review-supported", 45, "Batch review suggested this item may be supported."))

    if suggested_result == "rejected":
        signals.append(ResultEvidenceHypothesisSignal("review-rejected", -50, "Batch review suggested expected blocking or non-sensitive behavior."))

    if suggested_result == "needs-more-evidence":
        signals.append(ResultEvidenceHypothesisSignal("review-needs-more-evidence", 0, "Batch review marked this item as inconclusive."))

    if observed_status is not None and expected_status is not None and observed_status != expected_status:
        signals.append(
            ResultEvidenceHypothesisSignal(
                "status-differs-from-expected",
                25,
                f"Observed status {observed_status} differs from expected status {expected_status}.",
            )
        )

    if observed_status == 200:
        signals.append(ResultEvidenceHypothesisSignal("observed-success", 15, "Observed a success-style response."))

    if expected_status in {401, 403} and observed_status == 200:
        signals.append(
            ResultEvidenceHypothesisSignal(
                "success-where-auth-block-expected",
                45,
                "Observed success where authentication or authorization blocking was expected.",
            )
        )

    if observed_status in {401, 403}:
        signals.append(ResultEvidenceHypothesisSignal("observed-auth-block", -30, "Observed authentication or authorization blocking."))

    if observed_status == 404:
        signals.append(ResultEvidenceHypothesisSignal("observed-not-found", -10, "Observed not-found behavior; random-object baseline may be needed."))

    keyword_weights = {
        "foreign account": 30,
        "cross tenant": 35,
        "cross-tenant": 35,
        "other user": 25,
        "private data": 30,
        "permission bypass": 45,
        "unauthorized data": 40,
        "sensitive": 20,
        "same as random": -20,
        "expected blocking": -25,
        "expected behavior": -25,
        "forbidden": -20,
    }

    for keyword, weight in keyword_weights.items():
        if keyword in text:
            signals.append(
                ResultEvidenceHypothesisSignal(
                    f"keyword:{keyword.replace(' ', '-')}",
                    weight,
                    f"Observed review keyword: {keyword}.",
                )
            )

    return tuple(signals)


def _hypothesis_class(
    suggested_result: str,
    observed_status: int | None,
    expected_status: int | None,
    text: str,
    score: int,
) -> str:
    if suggested_result == "rejected" or score <= -30:
        return "likely-expected-blocking-or-false-positive"

    if expected_status in {401, 403} and observed_status == 200:
        return "object-or-tenant-authorization-boundary-candidate"

    if "foreign account" in text or "cross tenant" in text or "cross-tenant" in text or "other user" in text:
        return "cross-account-or-cross-tenant-access-candidate"

    if "private data" in text or "unauthorized data" in text or "sensitive" in text:
        return "information-disclosure-candidate"

    if suggested_result == "supported" and score >= 60:
        return "authorization-bypass-candidate"

    return "needs-more-evidence"


def _confidence(suggested_result: str, score: int) -> str:
    if suggested_result == "rejected":
        return "medium"

    if score >= 100:
        return "medium-high"

    if score >= 60:
        return "medium"

    return "low-medium"


def _evidence_strength(suggested_result: str, score: int) -> str:
    if suggested_result == "rejected":
        return "weak-for-finding"

    if score >= 100:
        return "strong-candidate"

    if score >= 60:
        return "medium-candidate"

    return "weak-candidate"


def _severity_hint(hypothesis_class: str, evidence_strength: str) -> str:
    if hypothesis_class in {
        "object-or-tenant-authorization-boundary-candidate",
        "cross-account-or-cross-tenant-access-candidate",
    } and evidence_strength in {"strong-candidate", "medium-candidate"}:
        return "candidate-high-if-sensitive-data-confirmed"

    if hypothesis_class == "information-disclosure-candidate":
        return "candidate-medium-to-high-depending-data-sensitivity"

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return "not-reportable-with-current-evidence"

    return "needs-validation"


def _reason(
    hypothesis_class: str,
    suggested_result: str,
    observed_status: int | None,
    expected_status: int | None,
) -> str:
    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return "Current signals suggest expected blocking, random-like behavior, or insufficient reportability."

    if hypothesis_class == "object-or-tenant-authorization-boundary-candidate":
        return f"Observed status {observed_status} where status {expected_status} was expected, suggesting a possible authorization boundary inconsistency."

    if hypothesis_class == "cross-account-or-cross-tenant-access-candidate":
        return "Review signals mention foreign-account, cross-tenant, or other-user access patterns."

    if hypothesis_class == "information-disclosure-candidate":
        return "Review signals mention private, sensitive, or unauthorized data exposure."

    if suggested_result == "supported":
        return "Review signals may support a security hypothesis, but manual validation is still required."

    return "Current evidence is inconclusive and should be validated with additional baselines."


def _next_manual_tests(hypothesis_class: str) -> list[str]:
    common = [
        "Confirm the target and asset are in scope.",
        "Reproduce the own-object or own-account baseline.",
        "Reproduce the second-account or foreign-object behavior.",
        "Compare against a random or non-existent object baseline.",
        "Preserve raw request and response evidence with secrets redacted.",
    ]

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        return [
            "Confirm whether the observed response exactly matches expected blocking behavior.",
            "Compare foreign-object behavior with random-object behavior.",
            "Check whether any sensitive data or ownership-specific data is actually returned.",
            "Do not report unless new evidence proves a security boundary violation.",
        ]

    if hypothesis_class == "object-or-tenant-authorization-boundary-candidate":
        return common + [
            "Verify object ownership identifiers in the response.",
            "Check role/account/tenant boundaries with controlled test accounts.",
            "Confirm whether the same request should require 401/403 for the foreign object.",
        ]

    if hypothesis_class == "cross-account-or-cross-tenant-access-candidate":
        return common + [
            "Confirm the affected object belongs to another account or tenant.",
            "Verify whether tenant-specific identifiers or private fields are returned.",
            "Check whether lower-privileged roles can reproduce the same behavior.",
        ]

    if hypothesis_class == "information-disclosure-candidate":
        return common + [
            "Identify the exact data type exposed.",
            "Confirm whether the data is private, sensitive, or tenant-specific.",
            "Check whether unauthenticated or lower-privileged users can access the same data.",
        ]

    return common + [
        "Collect missing expected status and expected body baselines.",
        "Check unauthenticated and expired-session behavior only when allowed.",
        "Add more evidence before deciding reportability.",
    ]


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _display_value(value: Any) -> str:
    if value is None:
        return "not provided"
    return str(value)
