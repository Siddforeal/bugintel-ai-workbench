"""
Local research chat for Blackhole AI Workbench result evidence artifacts.

This module answers simple researcher questions from local case-summary JSON.
It is deterministic and local-only. It does not call LLM providers, send
requests, execute tools, launch browsers, use Kali tools, mutate targets,
bypass authorization, or confirm vulnerabilities automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.result_evidence_question_intent import normalize_question_intent


@dataclass(frozen=True)
class CaseChatAnswer:
    question: str
    answer: str
    intent: str
    cited_endpoints: tuple[str, ...]
    next_actions: tuple[str, ...]
    source: str = "result-evidence-case-chat"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["cited_endpoints"] = list(self.cited_endpoints)
        data["next_actions"] = list(self.next_actions)
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


def answer_case_question(
    artifact: dict[str, Any],
    question: str,
    source: str = "result-evidence-case-chat",
) -> CaseChatAnswer:
    """Answer a local research question from a case summary artifact."""
    if not isinstance(artifact, dict):
        raise ValueError("case chat artifact must be an object")

    if artifact.get("kind") != "result_evidence_case_summary":
        raise ValueError("case chat currently requires kind=result_evidence_case_summary")

    question_text = question.strip()
    if not question_text:
        raise ValueError("case chat requires a non-empty question")

    findings = artifact.get("findings")
    if not isinstance(findings, list):
        raise ValueError("case summary requires a findings list")

    intent_result = normalize_question_intent(question_text)
    intent = intent_result.intent

    if intent == "next-tests":
        answer, endpoints, actions = _answer_next_tests(artifact, findings)
    elif intent == "strongest":
        answer, endpoints, actions = _answer_strongest(artifact)
    elif intent == "weak":
        answer, endpoints, actions = _answer_weak(artifact)
    elif intent == "report-ready":
        answer, endpoints, actions = _answer_report_ready(artifact, findings)
    elif intent == "missing-evidence":
        answer, endpoints, actions = _answer_missing_evidence(artifact, findings)
    elif intent == "do-not-claim":
        answer, endpoints, actions = _answer_do_not_claim(artifact, findings)
    else:
        answer, endpoints, actions = _answer_general(artifact, findings)

    return CaseChatAnswer(
        question=question_text,
        answer=answer,
        intent=intent,
        cited_endpoints=tuple(endpoints),
        next_actions=tuple(actions),
        source=source,
    )


def _detect_intent(question: str) -> str:
    if any(phrase in question for phrase in ["test next", "next test", "next step", "what should i test"]):
        return "next-tests"

    if any(phrase in question for phrase in ["strongest", "best", "highest priority", "most important"]):
        return "strongest"

    if any(phrase in question for phrase in ["weak", "false positive", "rejected", "not reportable"]):
        return "weak"

    if any(phrase in question for phrase in ["report ready", "ready to report", "submit", "submission ready"]):
        return "report-ready"

    if any(phrase in question for phrase in ["missing", "evidence missing", "what evidence"]):
        return "missing-evidence"

    if any(phrase in question for phrase in ["not claim", "do not claim", "avoid claiming", "overclaim"]):
        return "do-not-claim"

    return "general"


def _answer_next_tests(artifact: dict[str, Any], findings: list[Any]) -> tuple[str, list[str], list[str]]:
    strongest = _objects(artifact.get("strongest_candidates"))
    target = strongest[0] if strongest else _first_object(findings)

    if not target:
        return (
            "No findings are present in the case summary, so there is nothing to test yet.",
            [],
            ["Import and review evidence before asking for next tests."],
        )

    endpoint = _text(target, "endpoint")
    actions = _string_list(target.get("next_actions"))

    if not actions:
        actions = [
            "Capture own-object baseline.",
            "Capture foreign-object or second-account behavior.",
            "Capture random-object baseline.",
            "Confirm sensitive or tenant-specific data before claiming impact.",
        ]

    answer = (
        f"Start with `{endpoint}` because it is the strongest available candidate in the case summary. "
        "Complete the highest-value manual checks first: own-object baseline, foreign-object behavior, "
        "random-object baseline, and sensitive-data confirmation. Keep testing read-only and scoped."
    )

    return answer, [endpoint], actions


def _answer_strongest(artifact: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    strongest = _objects(artifact.get("strongest_candidates"))

    if not strongest:
        return (
            "There are no strongest candidates marked in this case summary.",
            [],
            ["Collect more evidence or improve the validation plan before report drafting."],
        )

    endpoints = [_text(item, "endpoint") for item in strongest]
    first = strongest[0]

    answer = (
        f"The strongest candidate is `{_text(first, 'endpoint')}`. "
        f"Readiness is `{_text(first, 'readiness')}`, priority is `{_text(first, 'priority')}`, "
        f"and hypothesis class is `{_text(first, 'hypothesis_class')}`. "
        "Treat it as a candidate only until manual validation proves scope, reproducibility, and impact."
    )

    return answer, endpoints, _string_list(first.get("next_actions"))


def _answer_weak(artifact: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    weak = _objects(artifact.get("weak_or_rejected_candidates"))

    if not weak:
        return (
            "No weak or rejected candidates are marked in this case summary.",
            [],
            ["Continue validating strongest candidates first."],
        )

    endpoints = [_text(item, "endpoint") for item in weak]
    first = weak[0]

    answer = (
        f"The weakest or likely false-positive candidate is `{_text(first, 'endpoint')}`. "
        f"Readiness is `{_text(first, 'readiness')}` and hypothesis class is `{_text(first, 'hypothesis_class')}`. "
        "Do not report it unless new evidence proves behavior differs from expected blocking or random-object behavior."
    )

    return answer, endpoints, _string_list(first.get("next_actions"))


def _answer_report_ready(artifact: dict[str, Any], findings: list[Any]) -> tuple[str, list[str], list[str]]:
    strongest = _objects(artifact.get("strongest_candidates"))
    ready = [
        item for item in strongest
        if _text(item, "readiness") in {"near-report-ready", "needs-final-validation"}
    ]

    if not ready:
        return (
            "This case is not report-ready yet. No near-report-ready or final-validation candidates were found.",
            [],
            [
                "Complete missing baselines.",
                "Confirm sensitive or tenant-specific data.",
                "Preserve raw request/response evidence.",
            ],
        )

    endpoints = [_text(item, "endpoint") for item in ready]
    missing = []
    for item in ready:
        missing.extend(_string_list(item.get("missing_evidence")))

    if missing:
        answer = (
            "This case has candidates worth final validation, but it is not submission-ready until missing evidence is closed. "
            f"Primary candidate: `{endpoints[0]}`."
        )
        return answer, endpoints, _dedupe(missing)

    answer = (
        f"`{endpoints[0]}` may be close to report-ready, but the final report still needs human validation, "
        "raw evidence review, scope confirmation, and impact confirmation."
    )
    return answer, endpoints, ["Manually verify all report-readiness checks before submission."]


def _answer_missing_evidence(artifact: dict[str, Any], findings: list[Any]) -> tuple[str, list[str], list[str]]:
    endpoints: list[str] = []
    missing: list[str] = []

    case_items: list[dict[str, Any]] = []
    case_items.extend(_objects(artifact.get("strongest_candidates")))
    case_items.extend(_objects(artifact.get("weak_or_rejected_candidates")))
    case_items.extend(_objects(findings))

    for item in case_items:
        endpoint = _text(item, "endpoint")
        item_missing = _string_list(item.get("missing_evidence"))
        if endpoint and item_missing:
            endpoints.append(endpoint)
            missing.extend(item_missing)

    if not missing:
        return (
            "The case summary does not list missing evidence for the current strongest candidate.",
            [],
            ["Still manually verify raw requests, responses, scope, and impact before reporting."],
        )

    answer = "The case is missing evidence that should be closed before report submission."
    return answer, _dedupe(endpoints), _dedupe(missing)


def _answer_do_not_claim(artifact: dict[str, Any], findings: list[Any]) -> tuple[str, list[str], list[str]]:
    endpoints = [_text(item, "endpoint") for item in _objects(findings)]

    claims = [
        "Do not claim the vulnerability is confirmed from this summary alone.",
        "Do not claim High severity until sensitive data, authorization boundary, and repeatability are proven.",
        "Do not claim cross-tenant or cross-account impact unless ownership is verified.",
        "Do not include secrets, cookies, tokens, or unnecessary personal data in the report.",
        "Do not report candidates that match expected blocking or random-object behavior.",
    ]

    answer = (
        "Avoid overclaiming. This artifact is planning-only and does not prove a vulnerability by itself. "
        "Only claim impact that is directly supported by scoped, repeatable, redacted evidence."
    )

    return answer, endpoints, claims


def _answer_general(artifact: dict[str, Any], findings: list[Any]) -> tuple[str, list[str], list[str]]:
    count = len(_objects(findings))
    priority_counts = artifact.get("priority_counts") if isinstance(artifact.get("priority_counts"), dict) else {}
    readiness_counts = artifact.get("readiness_counts") if isinstance(artifact.get("readiness_counts"), dict) else {}

    answer = (
        f"This case summary contains {count} finding(s). "
        f"Priority counts: {priority_counts}. Readiness counts: {readiness_counts}. "
        "Ask what to test next, what is strongest, what is weak, what evidence is missing, or whether it is report-ready."
    )

    return answer, [], [
        "Review strongest candidates first.",
        "Close missing evidence.",
        "Avoid reporting likely false positives.",
    ]


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_object(value: list[Any]) -> dict[str, Any] | None:
    for item in value:
        if isinstance(item, dict):
            return item
    return None


def _text(item: dict[str, Any], key: str) -> str:
    return str(item.get(key) or "").strip()


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
