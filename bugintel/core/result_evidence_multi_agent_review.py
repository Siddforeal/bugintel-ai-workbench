"""
Multi-agent review planner for Blackhole AI Workbench result evidence rankings.

This module turns a local result evidence priority ranking into deterministic
specialist review plans. It is local-only and planning-only. It does not call
LLM providers, send requests, execute tools, launch browsers, use Kali tools,
mutate targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentReviewTask:
    agent: str
    focus: str
    questions: tuple[str, ...]
    checklist: tuple[str, ...]
    risk_flags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "focus": self.focus,
            "questions": list(self.questions),
            "checklist": list(self.checklist),
            "risk_flags": list(self.risk_flags),
        }


@dataclass(frozen=True)
class CandidateMultiAgentReviewPlan:
    endpoint: str
    rank: int
    score: int
    priority: str
    readiness: str
    hypothesis_class: str
    source: str
    agents: tuple[AgentReviewTask, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "rank": self.rank,
            "score": self.score,
            "priority": self.priority,
            "readiness": self.readiness,
            "hypothesis_class": self.hypothesis_class,
            "source": self.source,
            "agents": [agent.to_dict() for agent in self.agents],
            "agent_count": len(self.agents),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class ResultEvidenceMultiAgentReviewPlan:
    plans: tuple[CandidateMultiAgentReviewPlan, ...]
    source: str = "result-evidence-multi-agent-review"
    kind: str = "result_evidence_multi_agent_review_plan"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.plans),
            "plans": [plan.to_dict() for plan in self.plans],
            "total_agent_tasks": sum(len(plan.agents) for plan in self.plans),
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

    def to_markdown(self, title: str = "Multi-Agent Review Plan") -> str:
        data = self.to_dict()
        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Candidate plans: {data['count']}")
        lines.append(f"- Total agent tasks: {data['total_agent_tasks']}")
        lines.append("- Planning-only: true")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        if not self.plans:
            lines.append("_No candidate review plans were generated._")
            lines.append("")
        else:
            for plan in self.plans:
                lines.append(f"## Candidate {plan.rank}: `{plan.endpoint}`")
                lines.append("")
                lines.append(f"- Score: {plan.score}")
                lines.append(f"- Priority: {plan.priority}")
                lines.append(f"- Readiness: {plan.readiness}")
                lines.append(f"- Hypothesis class: {plan.hypothesis_class}")
                lines.append(f"- Source: `{plan.source}`")
                lines.append("")

                for agent in plan.agents:
                    lines.append(f"### {agent.agent}")
                    lines.append("")
                    lines.append(f"- Focus: {agent.focus}")
                    lines.append("")
                    lines.append("Questions:")
                    for question in agent.questions:
                        lines.append(f"- {question}")
                    lines.append("")
                    lines.append("Checklist:")
                    for item in agent.checklist:
                        lines.append(f"- {item}")
                    lines.append("")
                    lines.append("Risk flags:")
                    for flag in agent.risk_flags:
                        lines.append(f"- {flag}")
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


def build_result_evidence_multi_agent_review_plan(
    ranking_data: dict[str, Any],
    include_low_priority: bool = True,
    source: str = "result-evidence-multi-agent-review",
) -> ResultEvidenceMultiAgentReviewPlan:
    """Build specialist review plans from a local result evidence priority ranking."""
    if not isinstance(ranking_data, dict):
        raise ValueError("priority ranking data must be an object")

    if ranking_data.get("kind") != "result_evidence_priority_ranking":
        raise ValueError("multi-agent review requires kind=result_evidence_priority_ranking")

    candidates = ranking_data.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("multi-agent review requires a candidates list")

    plans: list[CandidateMultiAgentReviewPlan] = []

    for raw_candidate in candidates:
        if not isinstance(raw_candidate, dict):
            raise ValueError("each ranked candidate must be an object")

        if not include_low_priority and _is_low_priority(raw_candidate):
            continue

        plans.append(_build_candidate_plan(raw_candidate))

    return ResultEvidenceMultiAgentReviewPlan(plans=tuple(plans), source=source)


def _build_candidate_plan(candidate: dict[str, Any]) -> CandidateMultiAgentReviewPlan:
    endpoint = str(candidate.get("endpoint") or "").strip()
    if not endpoint:
        raise ValueError("each ranked candidate requires an endpoint")

    hypothesis_class = str(candidate.get("hypothesis_class") or "unknown")
    readiness = str(candidate.get("readiness") or "unknown")
    priority = str(candidate.get("priority") or "unknown")
    source = str(candidate.get("source") or "unknown")
    rank = _optional_int(candidate.get("rank")) or 0
    score = _optional_int(candidate.get("score")) or 0
    missing_evidence = tuple(_string_list(candidate.get("missing_evidence")))
    next_actions = tuple(_string_list(candidate.get("next_actions")))

    agents = (
        _authorization_reviewer(hypothesis_class, missing_evidence),
        _false_positive_reviewer(readiness, missing_evidence),
        _impact_reviewer(hypothesis_class, missing_evidence),
        _evidence_reviewer(missing_evidence, next_actions),
        _report_reviewer(priority, readiness),
    )

    return CandidateMultiAgentReviewPlan(
        endpoint=endpoint,
        rank=rank,
        score=score,
        priority=priority,
        readiness=readiness,
        hypothesis_class=hypothesis_class,
        source=source,
        agents=agents,
    )


def _authorization_reviewer(hypothesis_class: str, missing_evidence: tuple[str, ...]) -> AgentReviewTask:
    risk_flags = ["authorization-boundary-unknown"]

    if "authorization" in hypothesis_class or "tenant" in hypothesis_class or "cross" in hypothesis_class:
        risk_flags.append("possible-object-or-tenant-boundary-issue")

    if missing_evidence:
        risk_flags.append("missing-baseline-evidence")

    return AgentReviewTask(
        agent="authz-reviewer",
        focus="Authorization, ownership, tenant, and object-boundary review.",
        questions=(
            "Does the candidate cross an account, tenant, user, role, or object boundary?",
            "Is the expected behavior clearly 401, 403, or no access?",
            "Are own-object, foreign-object, random-object, and session baselines available?",
        ),
        checklist=(
            "Confirm the target and account/object identifiers are in scope.",
            "Compare own-object and foreign-object responses.",
            "Compare foreign-object and random-object behavior.",
            "Check whether shared roles, public objects, or inherited permissions explain access.",
        ),
        risk_flags=tuple(risk_flags),
    )


def _false_positive_reviewer(readiness: str, missing_evidence: tuple[str, ...]) -> AgentReviewTask:
    risk_flags = []

    if readiness in {"likely-false-positive", "not-reportable-currently"}:
        risk_flags.append("likely-false-positive")

    if missing_evidence:
        risk_flags.append("missing-evidence-before-reporting")

    return AgentReviewTask(
        agent="false-positive-reviewer",
        focus="False-positive, expected behavior, and random-baseline review.",
        questions=(
            "Does this behavior match random-object behavior?",
            "Does this behavior match expected blocking?",
            "Is there any sensitive or ownership-specific data in the response?",
        ),
        checklist=(
            "Compare against random or nonexistent object baseline.",
            "Check whether errors, redirects, empty bodies, or generic responses are being overinterpreted.",
            "Reject the candidate if no security boundary violation is proven.",
        ),
        risk_flags=tuple(risk_flags or ["false-positive-risk-not-yet-reviewed"]),
    )


def _impact_reviewer(hypothesis_class: str, missing_evidence: tuple[str, ...]) -> AgentReviewTask:
    risk_flags = []

    if "information" in hypothesis_class:
        risk_flags.append("data-sensitivity-needs-review")

    if "authorization" in hypothesis_class or "tenant" in hypothesis_class:
        risk_flags.append("impact-depends-on-sensitive-or-tenant-specific-data")

    if missing_evidence:
        risk_flags.append("impact-not-ready-with-missing-evidence")

    return AgentReviewTask(
        agent="impact-reviewer",
        focus="Impact, data sensitivity, attacker prerequisites, and severity review.",
        questions=(
            "What exact data or state is exposed?",
            "Who can access it and under what privileges?",
            "What is the realistic attacker prerequisite?",
            "Can severity be justified without overclaiming?",
        ),
        checklist=(
            "Identify field names and data class using redacted evidence.",
            "Tie impact to proven returned data or state change only.",
            "Avoid High severity unless sensitive data or strong boundary impact is proven.",
        ),
        risk_flags=tuple(risk_flags or ["impact-not-yet-established"]),
    )


def _evidence_reviewer(missing_evidence: tuple[str, ...], next_actions: tuple[str, ...]) -> AgentReviewTask:
    risk_flags = []

    if missing_evidence:
        risk_flags.append("missing-evidence-present")

    if not next_actions:
        risk_flags.append("no-next-actions-provided")

    return AgentReviewTask(
        agent="evidence-reviewer",
        focus="Raw evidence completeness, redaction, reproducibility, and artifact quality.",
        questions=(
            "Are raw requests and responses preserved?",
            "Are secrets, cookies, tokens, and personal data redacted?",
            "Are timestamps, account roles, object IDs, and baselines documented?",
        ),
        checklist=(
            "Preserve raw request/response pairs separately.",
            "Add screenshots only where they clarify impact.",
            "Document account ownership and object ownership.",
            "Close missing evidence before report submission.",
        ),
        risk_flags=tuple(risk_flags or ["evidence-quality-review-needed"]),
    )


def _report_reviewer(priority: str, readiness: str) -> AgentReviewTask:
    risk_flags = []

    if readiness != "near-report-ready":
        risk_flags.append("not-final-report-ready")

    if priority in {"high", "medium-high"}:
        risk_flags.append("priority-candidate-needs-careful-report-wording")

    return AgentReviewTask(
        agent="report-reviewer",
        focus="Report wording, claim boundaries, reproduction clarity, and submission readiness.",
        questions=(
            "Does the report title match only what is proven?",
            "Are reproduction steps safe, minimal, and scoped?",
            "Does the impact section avoid unsupported claims?",
        ),
        checklist=(
            "State that evidence was collected from controlled accounts only.",
            "Avoid claiming exploitability beyond what was reproduced.",
            "Include limitations and false-positive checks.",
            "Use redacted evidence and avoid secrets.",
        ),
        risk_flags=tuple(risk_flags or ["report-review-needed"]),
    )


def _is_low_priority(candidate: dict[str, Any]) -> bool:
    return str(candidate.get("priority") or "") == "low" or str(candidate.get("readiness") or "") in {
        "likely-false-positive",
        "not-reportable-currently",
    }


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
