"""
Strong local research chat for Blackhole AI Workbench result evidence artifacts.

This module answers deterministic local research questions from multiple local
artifacts together: case summary, priority ranking, multi-agent review, report
assistant output, and optional case-chat session memory.

It does not call LLM providers, send requests, execute tools, launch browsers,
use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.result_evidence_chat import answer_case_question
from bugintel.core.result_evidence_question_intent import normalize_question_intent


@dataclass(frozen=True)
class CaseChatContextAnswer:
    question: str
    answer: str
    intent: str
    cited_endpoints: tuple[str, ...]
    next_actions: tuple[str, ...]
    included_artifacts: tuple[str, ...]
    source: str = "result-evidence-case-chat-context"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cited_endpoints"] = list(self.cited_endpoints)
        data["next_actions"] = list(self.next_actions)
        data["included_artifacts"] = list(self.included_artifacts)
        data["safety"] = {
            "local_only": True,
            "planning_only": True,
            "network_interaction": False,
            "target_mutation": False,
            "tool_execution": False,
            "llm_provider_calls": False,
            "vulnerability_confirmation": False,
        }
        return data


def answer_case_context_question(
    case_summary: dict[str, Any],
    question: str,
    ranking: dict[str, Any] | None = None,
    multi_agent_review: dict[str, Any] | None = None,
    report_assistant: dict[str, Any] | None = None,
    session: dict[str, Any] | None = None,
    source: str = "result-evidence-case-chat-context",
) -> CaseChatContextAnswer:
    """Answer a stronger local research question from multiple local artifacts."""
    _require_kind(case_summary, "result_evidence_case_summary", "case summary")

    if ranking is not None:
        _require_kind(ranking, "result_evidence_priority_ranking", "priority ranking")

    if multi_agent_review is not None:
        _require_kind(multi_agent_review, "result_evidence_multi_agent_review_plan", "multi-agent review")

    if report_assistant is not None:
        _require_kind(report_assistant, "result_evidence_report_assistant", "report assistant")

    if session is not None:
        _require_kind(session, "result_evidence_case_chat_session", "case chat session")

    question_text = question.strip()
    if not question_text:
        raise ValueError("case chat context requires a non-empty question")

    intent_result = normalize_question_intent(question_text)
    intent = _detect_context_intent(intent_result.normalized_question, fallback_intent=intent_result.intent)
    included = _included_artifacts(ranking, multi_agent_review, report_assistant, session)

    if intent == "reviewers":
        answer, endpoints, actions = _answer_reviewers(case_summary, ranking, multi_agent_review)
    elif intent == "final-report-focus":
        answer, endpoints, actions = _answer_final_report_focus(case_summary, ranking, multi_agent_review, report_assistant)
    elif intent == "session-summary":
        answer, endpoints, actions = _answer_session_summary(session)
    elif intent == "report-ready":
        answer, endpoints, actions = _answer_context_report_ready(case_summary, ranking, multi_agent_review, report_assistant)
    else:
        base = answer_case_question(case_summary, question_text)
        answer = _enrich_base_answer(base.answer, ranking, multi_agent_review, report_assistant, session)
        endpoints = list(base.cited_endpoints)
        actions = list(base.next_actions)
        intent = base.intent

    return CaseChatContextAnswer(
        question=question_text,
        answer=answer,
        intent=intent,
        cited_endpoints=tuple(_dedupe(endpoints)),
        next_actions=tuple(_dedupe(actions)),
        included_artifacts=tuple(included),
        source=source,
    )


def _detect_context_intent(question: str, fallback_intent: str = "general") -> str:
    if any(phrase in question for phrase in ["reviewer", "reviewers", "agent", "agents", "multi-agent", "what do reviewers think"]):
        return "reviewers"

    if any(phrase in question for phrase in ["final report", "report focus", "focus on", "what should the report"]):
        return "final-report-focus"

    if any(phrase in question for phrase in ["session", "history", "previous question", "chat memory"]):
        return "session-summary"

    if any(phrase in question for phrase in ["report ready", "ready to report", "submit", "submission ready"]):
        return "report-ready"

    return "delegate" if fallback_intent == "general" else fallback_intent


def _included_artifacts(
    ranking: dict[str, Any] | None,
    multi_agent_review: dict[str, Any] | None,
    report_assistant: dict[str, Any] | None,
    session: dict[str, Any] | None,
) -> list[str]:
    artifacts = ["case-summary"]

    if ranking is not None:
        artifacts.append("priority-ranking")

    if multi_agent_review is not None:
        artifacts.append("multi-agent-review")

    if report_assistant is not None:
        artifacts.append("report-assistant")

    if session is not None:
        artifacts.append("case-chat-session")

    return artifacts


def _answer_reviewers(
    case_summary: dict[str, Any],
    ranking: dict[str, Any] | None,
    multi_agent_review: dict[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    endpoint = _top_endpoint(case_summary, ranking)

    if multi_agent_review is None:
        return (
            f"No multi-agent review artifact was provided. For `{endpoint}`, run result-evidence-multi-agent-review to get authz, false-positive, impact, evidence, and report-review tasks.",
            [endpoint],
            ["Run result-evidence-multi-agent-review on the priority ranking artifact."],
        )

    plan = _matching_agent_plan(multi_agent_review, endpoint)
    if not plan:
        return (
            f"No matching multi-agent review plan was found for `{endpoint}`.",
            [endpoint],
            ["Regenerate the multi-agent review using the same priority ranking artifact."],
        )

    agents = _objects(plan.get("agents"))
    agent_names = [str(agent.get("agent") or "unknown-agent") for agent in agents]
    risk_flags = []
    for agent in agents:
        risk_flags.extend(_string_list(agent.get("risk_flags")))

    answer = (
        f"For `{endpoint}`, specialist reviewers available are: {', '.join(agent_names)}. "
        f"Key risk flags: {', '.join(_dedupe(risk_flags)) if risk_flags else 'none listed'}."
    )

    actions = [
        "Start with authz-reviewer and false-positive-reviewer before impact wording.",
        "Use evidence-reviewer to close raw evidence and redaction gaps.",
        "Use report-reviewer before submitting any final report.",
    ]

    return answer, [endpoint], actions


def _answer_final_report_focus(
    case_summary: dict[str, Any],
    ranking: dict[str, Any] | None,
    multi_agent_review: dict[str, Any] | None,
    report_assistant: dict[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    endpoint = _top_endpoint(case_summary, ranking)

    title_options = []
    readiness = "unknown"

    if report_assistant is not None:
        title_options = _string_list(report_assistant.get("title_candidates"))
        readiness = str(report_assistant.get("readiness") or "unknown")
    else:
        candidate = _top_candidate(case_summary, ranking)
        readiness = str(candidate.get("readiness") or "unknown")

    answer = (
        f"The final report should focus on `{endpoint}` only if manual validation confirms the authorization boundary and impact. "
        f"Current readiness is `{readiness}`. "
    )

    if title_options:
        answer += f"Best title candidate: {title_options[0]}"
    else:
        answer += "Generate a report assistant artifact for title options and PoC skeleton."

    actions = [
        "Keep the report title limited to what is proven.",
        "Use the PoC skeleton only after validating baselines.",
        "Do not claim impact until sensitive data or unauthorized state is confirmed.",
    ]

    if multi_agent_review is None:
        actions.append("Run multi-agent review before final report wording.")

    return answer, [endpoint], actions


def _answer_session_summary(session: dict[str, Any] | None) -> tuple[str, list[str], list[str]]:
    if session is None:
        return (
            "No case-chat session artifact was provided.",
            [],
            ["Use case-chat --session-file to start collecting local chat memory."],
        )

    turn_count = session.get("turn_count", 0)
    intents = session.get("intents") if isinstance(session.get("intents"), dict) else {}
    cited = _string_list(session.get("cited_endpoints"))
    actions = _string_list(session.get("next_actions"))

    answer = (
        f"The local chat session contains {turn_count} turn(s). "
        f"Observed intents: {intents}. "
        f"Cited endpoints: {', '.join(cited) if cited else 'none'}."
    )

    return answer, cited, actions


def _answer_context_report_ready(
    case_summary: dict[str, Any],
    ranking: dict[str, Any] | None,
    multi_agent_review: dict[str, Any] | None,
    report_assistant: dict[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    endpoint = _top_endpoint(case_summary, ranking)
    candidate = _top_candidate(case_summary, ranking)
    readiness = str(candidate.get("readiness") or "unknown")
    missing = _string_list(candidate.get("missing_evidence"))

    if report_assistant is not None and str(report_assistant.get("readiness") or ""):
        readiness = str(report_assistant.get("readiness"))

    actions = [
        "Confirm scope.",
        "Confirm own-object baseline.",
        "Confirm foreign-object or second-account behavior.",
        "Confirm random-object baseline.",
        "Confirm sensitive or tenant-specific data before claiming impact.",
    ]

    if multi_agent_review is None:
        actions.append("Run multi-agent review before final submission.")

    if missing:
        answer = f"`{endpoint}` is not report-ready yet. Missing evidence remains: {', '.join(missing)}."
        return answer, [endpoint], _dedupe(missing + actions)

    answer = (
        f"`{endpoint}` may be close to report-ready if all baselines and raw evidence are manually verified. "
        "Do not submit until the final human report confirms scope, reproducibility, and impact."
    )
    return answer, [endpoint], actions


def _enrich_base_answer(
    base_answer: str,
    ranking: dict[str, Any] | None,
    multi_agent_review: dict[str, Any] | None,
    report_assistant: dict[str, Any] | None,
    session: dict[str, Any] | None,
) -> str:
    extras: list[str] = []

    if ranking is not None:
        top = ranking.get("top_candidate")
        if isinstance(top, dict) and top.get("endpoint"):
            extras.append(f"Priority ranking top candidate: `{top.get('endpoint')}` score={top.get('score')}.")

    if multi_agent_review is not None:
        extras.append("Multi-agent review is available for specialist checks.")

    if report_assistant is not None:
        extras.append("Report assistant artifact is available for report skeleton and wording guardrails.")

    if session is not None:
        extras.append(f"Chat session turns: {session.get('turn_count', 0)}.")

    if extras:
        return base_answer + " " + " ".join(extras)

    return base_answer


def _top_endpoint(case_summary: dict[str, Any], ranking: dict[str, Any] | None) -> str:
    candidate = _top_candidate(case_summary, ranking)
    return str(candidate.get("endpoint") or "unknown")


def _top_candidate(case_summary: dict[str, Any], ranking: dict[str, Any] | None) -> dict[str, Any]:
    if ranking is not None:
        top = ranking.get("top_candidate")
        if isinstance(top, dict) and top.get("endpoint"):
            return top

        candidates = ranking.get("candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict) and item.get("endpoint"):
                    return item

    strongest = case_summary.get("strongest_candidates")
    if isinstance(strongest, list):
        for item in strongest:
            if isinstance(item, dict) and item.get("endpoint"):
                return item

    findings = case_summary.get("findings")
    if isinstance(findings, list):
        for item in findings:
            if isinstance(item, dict) and item.get("endpoint"):
                return item

    return {}


def _matching_agent_plan(multi_agent_review: dict[str, Any], endpoint: str) -> dict[str, Any] | None:
    plans = multi_agent_review.get("plans")
    if not isinstance(plans, list):
        return None

    for plan in plans:
        if isinstance(plan, dict) and str(plan.get("endpoint") or "") == endpoint:
            return plan

    return None


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
