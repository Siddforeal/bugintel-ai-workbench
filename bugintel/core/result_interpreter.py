"""
Result interpreter for Blackhole AI Workbench.

This module interprets local, human-provided validation result summaries and
suggests a planning-only validation result. It does not call LLM providers,
send requests, execute shell commands, launch browsers, use Kali tools, mutate
targets, bypass authorization, or execute tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class InterpretationSignal:
    name: str
    weight: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultInterpretation:
    endpoint: str
    suggested_result: str
    confidence: str
    rationale: str
    signals: tuple[InterpretationSignal, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "suggested_result": self.suggested_result,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "signals": [signal.to_dict() for signal in self.signals],
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


def interpret_validation_result(
    endpoint: str,
    observed_status: int | None = None,
    expected_status: int | None = None,
    observed_body: str = "",
    expected_body: str = "",
    note: str = "",
) -> ResultInterpretation:
    """Interpret a human-provided validation result summary."""
    text = " ".join([observed_body, expected_body, note]).lower()
    signals = list(_status_signals(observed_status, expected_status))
    signals.extend(_text_signals(text))

    score = sum(signal.weight for signal in signals)

    has_strong_rejection = any(
        signal.name in {
            "observed-auth-block",
            "negative:expected-behavior",
            "negative:no-sensitive-data",
            "negative:access-denied",
            "negative:forbidden",
        }
        for signal in signals
    )

    if score >= 60:
        suggested = "supported"
        confidence = "medium-high"
        rationale = "Signals suggest the validation may support the hypothesis, but manual review is still required."
    elif score <= -30 and has_strong_rejection:
        suggested = "rejected"
        confidence = "medium"
        rationale = "Signals suggest expected blocking or non-sensitive behavior."
    else:
        suggested = "needs-more-evidence"
        confidence = "medium"
        rationale = "Signals are inconclusive or insufficient for a supported/rejected decision."

    return ResultInterpretation(
        endpoint=endpoint,
        suggested_result=suggested,
        confidence=confidence,
        rationale=rationale,
        signals=tuple(signals),
    )


def _status_signals(observed_status: int | None, expected_status: int | None) -> tuple[InterpretationSignal, ...]:
    signals: list[InterpretationSignal] = []

    if observed_status is None:
        return tuple(signals)

    if expected_status is not None and observed_status != expected_status:
        signals.append(
            InterpretationSignal(
                name="status-differs-from-expected",
                weight=20,
                reason=f"Observed status {observed_status} differs from expected {expected_status}.",
            )
        )

    if observed_status == 200:
        signals.append(
            InterpretationSignal(
                name="observed-success-status",
                weight=20,
                reason="Observed HTTP 200-style success response.",
            )
        )

    if observed_status in {401, 403}:
        signals.append(
            InterpretationSignal(
                name="observed-auth-block",
                weight=-35,
                reason="Observed authentication/authorization blocking status.",
            )
        )

    if observed_status == 404:
        signals.append(
            InterpretationSignal(
                name="observed-not-found",
                weight=-15,
                reason="Observed not-found response; may indicate no accessible object or no oracle.",
            )
        )

    return tuple(signals)


def _text_signals(text: str) -> tuple[InterpretationSignal, ...]:
    signals: list[InterpretationSignal] = []

    positive_keywords = {
        "unauthorized data": 40,
        "foreign account": 35,
        "cross tenant": 35,
        "cross-tenant": 35,
        "other user": 30,
        "private data": 35,
        "permission bypass": 45,
        "accessed": 15,
        "leaked": 40,
        "downloaded": 20,
    }

    negative_keywords = {
        "forbidden": -25,
        "unauthorized": -20,
        "access denied": -25,
        "not allowed": -20,
        "blocked": -20,
        "expected behavior": -30,
        "same as random": -15,
        "no sensitive data": -25,
    }

    for keyword, weight in positive_keywords.items():
        if keyword in text:
            signals.append(
                InterpretationSignal(
                    name=f"positive:{keyword.replace(' ', '-')}",
                    weight=weight,
                    reason=f"Observed positive validation keyword: {keyword}.",
                )
            )

    for keyword, weight in negative_keywords.items():
        if keyword in text:
            signals.append(
                InterpretationSignal(
                    name=f"negative:{keyword.replace(' ', '-')}",
                    weight=weight,
                    reason=f"Observed negative/blocking keyword: {keyword}.",
                )
            )

    return tuple(signals)
