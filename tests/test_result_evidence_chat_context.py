import pytest

from bugintel.core.result_evidence_chat_context import answer_case_context_question


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 1,
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
                "source": "manual-json-batch:001.json",
            }
        ],
        "weak_or_rejected_candidates": [],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "count": 1,
        "top_candidate": {
            "endpoint": "/api/high",
            "score": 120,
            "readiness": "needs-final-validation",
            "missing_evidence": [],
        },
        "candidates": [
            {
                "endpoint": "/api/high",
                "score": 120,
                "readiness": "needs-final-validation",
                "missing_evidence": [],
            }
        ],
    }


def _multi_agent():
    return {
        "kind": "result_evidence_multi_agent_review_plan",
        "count": 1,
        "plans": [
            {
                "endpoint": "/api/high",
                "agents": [
                    {
                        "agent": "authz-reviewer",
                        "risk_flags": ["possible-object-or-tenant-boundary-issue"],
                    },
                    {
                        "agent": "report-reviewer",
                        "risk_flags": ["priority-candidate-needs-careful-report-wording"],
                    },
                ],
            }
        ],
    }


def _report_assistant():
    return {
        "kind": "result_evidence_report_assistant",
        "readiness": "needs-final-validation",
        "title_candidates": [
            "Possible Cross-Account Authorization Boundary Issue on `/api/high`"
        ],
        "affected_endpoints": ["/api/high"],
    }


def _session():
    return {
        "kind": "result_evidence_case_chat_session",
        "turn_count": 2,
        "intents": {"next-tests": 1, "missing-evidence": 1},
        "cited_endpoints": ["/api/high"],
        "next_actions": ["Capture own-object baseline."],
        "turns": [],
    }


def test_context_chat_answers_reviewer_question():
    answer = answer_case_context_question(
        _case_summary(),
        "what do reviewers think?",
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
    )
    data = answer.to_dict()

    assert data["intent"] == "reviewers"
    assert data["included_artifacts"] == ["case-summary", "priority-ranking", "multi-agent-review"]
    assert data["cited_endpoints"] == ["/api/high"]
    assert "authz-reviewer" in data["answer"]
    assert data["safety"]["llm_provider_calls"] is False


def test_context_chat_answers_final_report_focus():
    answer = answer_case_context_question(
        _case_summary(),
        "what should the final report focus on?",
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
        report_assistant=_report_assistant(),
    )

    assert answer.intent == "final-report-focus"
    assert "/api/high" in answer.answer
    assert "Best title candidate" in answer.answer
    assert "report-assistant" in answer.included_artifacts


def test_context_chat_answers_report_ready():
    answer = answer_case_context_question(
        _case_summary(),
        "is this ready to report?",
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
        report_assistant=_report_assistant(),
    )

    assert answer.intent == "report-ready"
    assert "/api/high" in answer.answer
    assert answer.next_actions


def test_context_chat_answers_session_summary():
    answer = answer_case_context_question(
        _case_summary(),
        "summarize chat memory",
        session=_session(),
    )

    assert answer.intent == "session-summary"
    assert "2 turn" in answer.answer
    assert answer.cited_endpoints == ("/api/high",)


def test_context_chat_delegates_basic_questions():
    answer = answer_case_context_question(
        _case_summary(),
        "what should I test next?",
        ranking=_ranking(),
    )

    assert answer.intent == "next-tests"
    assert "Priority ranking top candidate" in answer.answer
    assert answer.cited_endpoints == ("/api/high",)


def test_context_chat_requires_case_summary_kind():
    with pytest.raises(ValueError):
        answer_case_context_question({"kind": "wrong"}, "what next?")


def test_context_chat_requires_non_empty_question():
    with pytest.raises(ValueError):
        answer_case_context_question(_case_summary(), "  ")


def test_context_chat_rejects_wrong_optional_artifact_kind():
    with pytest.raises(ValueError):
        answer_case_context_question(_case_summary(), "what next?", ranking={"kind": "wrong"})


def test_context_chat_understands_messy_reviewers_question():
    answer = answer_case_context_question(
        _case_summary(),
        "bro what do agents think?",
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
    )

    assert answer.intent == "reviewers"
    assert "authz-reviewer" in answer.answer


def test_context_chat_understands_messy_final_report_question():
    answer = answer_case_context_question(
        _case_summary(),
        "what should final report focus on?",
        ranking=_ranking(),
        report_assistant=_report_assistant(),
    )

    assert answer.intent == "final-report-focus"
    assert "Best title candidate" in answer.answer
