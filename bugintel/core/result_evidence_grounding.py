"""
Evidence snippet grounding for Blackhole AI Workbench local chat.

This module extracts small, deterministic grounding snippets from local result
evidence artifacts. It does not call LLM providers, send requests, execute
tools, launch browsers, use Kali tools, mutate targets, bypass authorization,
or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GroundingSnippet:
    artifact: str
    path: str
    value: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "path": self.path,
            "value": self.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    intent: str
    grounding: tuple[GroundingSnippet, ...]
    cited_endpoints: tuple[str, ...]
    next_actions: tuple[str, ...]
    source: str = "result-evidence-grounded-answer"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_grounded_answer",
            "source": self.source,
            "answer": self.answer,
            "intent": self.intent,
            "grounding": [snippet.to_dict() for snippet in self.grounding],
            "cited_endpoints": list(self.cited_endpoints),
            "next_actions": list(self.next_actions),
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


def build_grounded_answer(
    answer: str,
    intent: str,
    cited_endpoints: list[str] | tuple[str, ...],
    next_actions: list[str] | tuple[str, ...],
    case_summary: dict[str, Any],
    ranking: dict[str, Any] | None = None,
    multi_agent_review: dict[str, Any] | None = None,
    report_assistant: dict[str, Any] | None = None,
    source: str = "result-evidence-grounded-answer",
) -> GroundedAnswer:
    """Attach deterministic local artifact snippets to a local chat answer."""
    if not isinstance(case_summary, dict):
        raise ValueError("grounding requires a case summary object")

    if case_summary.get("kind") != "result_evidence_case_summary":
        raise ValueError("grounding requires kind=result_evidence_case_summary")

    snippets: list[GroundingSnippet] = []

    snippets.extend(_case_summary_snippets(case_summary))

    if ranking is not None:
        _require_kind(ranking, "result_evidence_priority_ranking", "priority ranking")
        snippets.extend(_ranking_snippets(ranking))

    if multi_agent_review is not None:
        _require_kind(multi_agent_review, "result_evidence_multi_agent_review_plan", "multi-agent review")
        snippets.extend(_multi_agent_snippets(multi_agent_review))

    if report_assistant is not None:
        _require_kind(report_assistant, "result_evidence_report_assistant", "report assistant")
        snippets.extend(_report_assistant_snippets(report_assistant))

    return GroundedAnswer(
        answer=answer,
        intent=intent,
        grounding=tuple(snippets),
        cited_endpoints=tuple(_dedupe([str(item) for item in cited_endpoints if str(item).strip()])),
        next_actions=tuple(_dedupe([str(item) for item in next_actions if str(item).strip()])),
        source=source,
    )


def _case_summary_snippets(case_summary: dict[str, Any]) -> list[GroundingSnippet]:
    snippets: list[GroundingSnippet] = []

    snippets.append(
        GroundingSnippet(
            artifact="case-summary",
            path="kind",
            value=str(case_summary.get("kind")),
            reason="Confirms the base artifact used for the answer.",
        )
    )

    strongest = _objects(case_summary.get("strongest_candidates"))
    if strongest:
        first = strongest[0]
        snippets.append(
            GroundingSnippet(
                artifact="case-summary",
                path="strongest_candidates[0].endpoint",
                value=str(first.get("endpoint")),
                reason="Identifies the strongest candidate endpoint.",
            )
        )
        snippets.append(
            GroundingSnippet(
                artifact="case-summary",
                path="strongest_candidates[0].readiness",
                value=str(first.get("readiness")),
                reason="Shows current report readiness for the strongest candidate.",
            )
        )
        snippets.append(
            GroundingSnippet(
                artifact="case-summary",
                path="strongest_candidates[0].priority",
                value=str(first.get("priority")),
                reason="Shows priority for the strongest candidate.",
            )
        )

    weak = _objects(case_summary.get("weak_or_rejected_candidates"))
    if weak:
        first = weak[0]
        snippets.append(
            GroundingSnippet(
                artifact="case-summary",
                path="weak_or_rejected_candidates[0].endpoint",
                value=str(first.get("endpoint")),
                reason="Identifies the leading weak or likely false-positive candidate.",
            )
        )
        missing = _string_list(first.get("missing_evidence"))
        if missing:
            snippets.append(
                GroundingSnippet(
                    artifact="case-summary",
                    path="weak_or_rejected_candidates[0].missing_evidence[0]",
                    value=missing[0],
                    reason="Shows evidence still needed before treating weak candidate as reportable.",
                )
            )

    return snippets


def _ranking_snippets(ranking: dict[str, Any]) -> list[GroundingSnippet]:
    snippets: list[GroundingSnippet] = []

    top = ranking.get("top_candidate")
    if isinstance(top, dict):
        if top.get("endpoint"):
            snippets.append(
                GroundingSnippet(
                    artifact="priority-ranking",
                    path="top_candidate.endpoint",
                    value=str(top.get("endpoint")),
                    reason="Shows the top ranked candidate.",
                )
            )

        if top.get("score") is not None:
            snippets.append(
                GroundingSnippet(
                    artifact="priority-ranking",
                    path="top_candidate.score",
                    value=str(top.get("score")),
                    reason="Shows the ranking score for the top candidate.",
                )
            )

        if top.get("readiness"):
            snippets.append(
                GroundingSnippet(
                    artifact="priority-ranking",
                    path="top_candidate.readiness",
                    value=str(top.get("readiness")),
                    reason="Shows report-readiness from ranking data.",
                )
            )

    return snippets


def _multi_agent_snippets(multi_agent_review: dict[str, Any]) -> list[GroundingSnippet]:
    snippets: list[GroundingSnippet] = []
    plans = _objects(multi_agent_review.get("plans"))

    if not plans:
        return snippets

    agents = _objects(plans[0].get("agents"))
    if agents:
        agent_names = [str(agent.get("agent")) for agent in agents if agent.get("agent")]
        snippets.append(
            GroundingSnippet(
                artifact="multi-agent-review",
                path="plans[0].agents[].agent",
                value=", ".join(agent_names),
                reason="Shows specialist reviewers available for the candidate.",
            )
        )

        risk_flags: list[str] = []
        for agent in agents:
            risk_flags.extend(_string_list(agent.get("risk_flags")))

        if risk_flags:
            snippets.append(
                GroundingSnippet(
                    artifact="multi-agent-review",
                    path="plans[0].agents[].risk_flags",
                    value=", ".join(_dedupe(risk_flags)),
                    reason="Shows specialist risk flags used by the answer.",
                )
            )

    return snippets


def _report_assistant_snippets(report_assistant: dict[str, Any]) -> list[GroundingSnippet]:
    snippets: list[GroundingSnippet] = []

    readiness = report_assistant.get("readiness")
    if readiness:
        snippets.append(
            GroundingSnippet(
                artifact="report-assistant",
                path="readiness",
                value=str(readiness),
                reason="Shows readiness from the report assistant artifact.",
            )
        )

    titles = _string_list(report_assistant.get("title_candidates"))
    if titles:
        snippets.append(
            GroundingSnippet(
                artifact="report-assistant",
                path="title_candidates[0]",
                value=titles[0],
                reason="Shows the title candidate used for report focus.",
            )
        )

    endpoints = _string_list(report_assistant.get("affected_endpoints"))
    if endpoints:
        snippets.append(
            GroundingSnippet(
                artifact="report-assistant",
                path="affected_endpoints[0]",
                value=endpoints[0],
                reason="Shows affected endpoint listed by the report assistant.",
            )
        )

    return snippets


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
