"""
Multi-artifact case memory for Blackhole AI Workbench.

This module combines local result evidence artifacts into one deterministic
case-memory JSON object. It does not call LLM providers, send requests,
execute tools, launch browsers, use Kali tools, mutate targets, bypass
authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseMemoryArtifact:
    label: str
    kind: str
    present: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "kind": self.kind,
            "present": self.present,
        }


@dataclass(frozen=True)
class ResultEvidenceCaseMemory:
    artifacts: tuple[CaseMemoryArtifact, ...]
    top_endpoint: str
    cited_endpoints: tuple[str, ...]
    open_next_actions: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    strongest_candidates: tuple[str, ...]
    weak_candidates: tuple[str, ...]
    source: str = "result-evidence-case-memory"
    kind: str = "result_evidence_case_memory"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "top_endpoint": self.top_endpoint,
            "cited_endpoints": list(self.cited_endpoints),
            "open_next_actions": list(self.open_next_actions),
            "missing_evidence": list(self.missing_evidence),
            "strongest_candidates": list(self.strongest_candidates),
            "weak_candidates": list(self.weak_candidates),
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

    def to_markdown(self, title: str = "Multi-Artifact Case Memory") -> str:
        data = self.to_dict()
        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Top endpoint: `{self.top_endpoint}`")
        lines.append(f"- Cited endpoints: {len(self.cited_endpoints)}")
        lines.append(f"- Open next actions: {len(self.open_next_actions)}")
        lines.append(f"- Missing evidence items: {len(self.missing_evidence)}")
        lines.append("- Planning-only: true")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        lines.append("## Artifact Inventory")
        lines.append("")
        for artifact in self.artifacts:
            lines.append(f"- {artifact.label}: `{artifact.kind}` present={artifact.present}")
        lines.append("")

        lines.append("## Strongest Candidates")
        lines.append("")
        if self.strongest_candidates:
            for endpoint in self.strongest_candidates:
                lines.append(f"- `{endpoint}`")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Weak Candidates")
        lines.append("")
        if self.weak_candidates:
            for endpoint in self.weak_candidates:
                lines.append(f"- `{endpoint}`")
        else:
            lines.append("- none")
        lines.append("")

        lines.append("## Missing Evidence")
        lines.append("")
        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none listed")
        lines.append("")

        lines.append("## Open Next Actions")
        lines.append("")
        if self.open_next_actions:
            for item in self.open_next_actions:
                lines.append(f"- {item}")
        else:
            lines.append("- none listed")
        lines.append("")

        lines.append("## Safety")
        lines.append("")
        lines.append("- This is local case memory.")
        lines.append("- It does not execute tests.")
        lines.append("- It does not send requests.")
        lines.append("- It does not mutate targets.")
        lines.append("- It does not confirm vulnerabilities.")
        lines.append("")

        return "\n".join(lines)


def build_result_evidence_case_memory(
    case_summary: dict[str, Any] | None = None,
    ranking: dict[str, Any] | None = None,
    multi_agent_review: dict[str, Any] | None = None,
    report_assistant: dict[str, Any] | None = None,
    grounded_answer: dict[str, Any] | None = None,
    session: dict[str, Any] | None = None,
    source: str = "result-evidence-case-memory",
) -> ResultEvidenceCaseMemory:
    """Build a deterministic local case memory object from available artifacts."""
    _validate_optional_kind(case_summary, "result_evidence_case_summary", "case-summary")
    _validate_optional_kind(ranking, "result_evidence_priority_ranking", "priority-ranking")
    _validate_optional_kind(multi_agent_review, "result_evidence_multi_agent_review_plan", "multi-agent-review")
    _validate_optional_kind(report_assistant, "result_evidence_report_assistant", "report-assistant")
    _validate_optional_kind(grounded_answer, "result_evidence_grounded_answer", "grounded-answer")
    _validate_optional_kind(session, "result_evidence_case_chat_session", "case-chat-session")

    if not any([case_summary, ranking, multi_agent_review, report_assistant, grounded_answer, session]):
        raise ValueError("case memory requires at least one artifact")

    artifacts = (
        _artifact("case-summary", case_summary),
        _artifact("priority-ranking", ranking),
        _artifact("multi-agent-review", multi_agent_review),
        _artifact("report-assistant", report_assistant),
        _artifact("grounded-answer", grounded_answer),
        _artifact("case-chat-session", session),
    )

    strongest = _strongest_candidates(case_summary)
    weak = _weak_candidates(case_summary)
    cited = _cited_endpoints(case_summary, ranking, report_assistant, grounded_answer, session)
    next_actions = _next_actions(case_summary, grounded_answer, session)
    missing = _missing_evidence(case_summary, grounded_answer)

    top_endpoint = _top_endpoint(ranking, cited, strongest)

    return ResultEvidenceCaseMemory(
        artifacts=artifacts,
        top_endpoint=top_endpoint,
        cited_endpoints=tuple(_dedupe(cited)),
        open_next_actions=tuple(_dedupe(next_actions)),
        missing_evidence=tuple(_dedupe(missing)),
        strongest_candidates=tuple(_dedupe(strongest)),
        weak_candidates=tuple(_dedupe(weak)),
        source=source,
    )


def _validate_optional_kind(data: dict[str, Any] | None, expected: str, label: str) -> None:
    if data is None:
        return

    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _artifact(label: str, data: dict[str, Any] | None) -> CaseMemoryArtifact:
    return CaseMemoryArtifact(
        label=label,
        kind=str(data.get("kind") if isinstance(data, dict) else "missing"),
        present=data is not None,
    )


def _strongest_candidates(case_summary: dict[str, Any] | None) -> list[str]:
    if not case_summary:
        return []
    return [_text(item, "endpoint") for item in _objects(case_summary.get("strongest_candidates")) if _text(item, "endpoint")]


def _weak_candidates(case_summary: dict[str, Any] | None) -> list[str]:
    if not case_summary:
        return []
    return [_text(item, "endpoint") for item in _objects(case_summary.get("weak_or_rejected_candidates")) if _text(item, "endpoint")]


def _cited_endpoints(
    case_summary: dict[str, Any] | None,
    ranking: dict[str, Any] | None,
    report_assistant: dict[str, Any] | None,
    grounded_answer: dict[str, Any] | None,
    session: dict[str, Any] | None,
) -> list[str]:
    endpoints: list[str] = []

    endpoints.extend(_strongest_candidates(case_summary))
    endpoints.extend(_weak_candidates(case_summary))

    if ranking:
        top = ranking.get("top_candidate")
        if isinstance(top, dict) and _text(top, "endpoint"):
            endpoints.append(_text(top, "endpoint"))

        for candidate in _objects(ranking.get("candidates")):
            if _text(candidate, "endpoint"):
                endpoints.append(_text(candidate, "endpoint"))

    if report_assistant:
        endpoints.extend(_string_list(report_assistant.get("affected_endpoints")))

    if grounded_answer:
        endpoints.extend(_string_list(grounded_answer.get("cited_endpoints")))

    if session:
        endpoints.extend(_string_list(session.get("cited_endpoints")))

    return endpoints


def _next_actions(
    case_summary: dict[str, Any] | None,
    grounded_answer: dict[str, Any] | None,
    session: dict[str, Any] | None,
) -> list[str]:
    actions: list[str] = []

    if case_summary:
        for item in _objects(case_summary.get("strongest_candidates")):
            actions.extend(_string_list(item.get("next_actions")))
        for item in _objects(case_summary.get("weak_or_rejected_candidates")):
            actions.extend(_string_list(item.get("next_actions")))

    if grounded_answer:
        actions.extend(_string_list(grounded_answer.get("next_actions")))

    if session:
        actions.extend(_string_list(session.get("next_actions")))

    return actions


def _missing_evidence(case_summary: dict[str, Any] | None, grounded_answer: dict[str, Any] | None) -> list[str]:
    missing: list[str] = []

    if case_summary:
        for item in _objects(case_summary.get("strongest_candidates")):
            missing.extend(_string_list(item.get("missing_evidence")))
        for item in _objects(case_summary.get("weak_or_rejected_candidates")):
            missing.extend(_string_list(item.get("missing_evidence")))

    if grounded_answer:
        for snippet in _objects(grounded_answer.get("grounding")):
            if "missing_evidence" in str(snippet.get("path") or ""):
                missing.append(str(snippet.get("value") or ""))

    return missing


def _top_endpoint(ranking: dict[str, Any] | None, cited: list[str], strongest: list[str]) -> str:
    if ranking:
        top = ranking.get("top_candidate")
        if isinstance(top, dict) and _text(top, "endpoint"):
            return _text(top, "endpoint")

    if strongest:
        return strongest[0]

    if cited:
        return cited[0]

    return "unknown"


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _text(item: dict[str, Any], key: str) -> str:
    return str(item.get(key) or "").strip()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)

    return result
