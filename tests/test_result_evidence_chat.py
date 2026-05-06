import pytest

from bugintel.core.result_evidence_chat import answer_case_question


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 2,
        "priority_counts": {"high": 1, "low": 1},
        "readiness_counts": {"needs-final-validation": 1, "likely-false-positive": 1},
        "strongest_candidates": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "missing_evidence": [],
                "next_actions": [
                    "Capture own-object, foreign-object, and random-object baselines.",
                    "Confirm sensitive or tenant-specific data before claiming impact.",
                ],
                "source": "manual-json-batch:001.json",
            }
        ],
        "weak_or_rejected_candidates": [
            {
                "endpoint": "/api/accounts/123/users/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "priority": "low",
                "readiness": "likely-false-positive",
                "missing_evidence": [
                    "Evidence proving behavior differs from expected blocking or random-object behavior"
                ],
                "next_actions": [
                    "Compare the candidate with random-object and expected-blocking behavior.",
                    "Reject the candidate if no sensitive data or authorization boundary violation is proven.",
                ],
                "source": "manual-json-batch:002.json",
            }
        ],
        "findings": [],
    }


def test_case_chat_answers_next_tests():
    answer = answer_case_question(_case_summary(), "what should I test next?")
    data = answer.to_dict()

    assert data["intent"] == "next-tests"
    assert "/api/accounts/123/users/999" in data["answer"]
    assert data["cited_endpoints"] == ["/api/accounts/123/users/999"]
    assert data["next_actions"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_case_chat_answers_strongest():
    answer = answer_case_question(_case_summary(), "what is strongest?")

    assert answer.intent == "strongest"
    assert "/api/accounts/123/users/999" in answer.answer
    assert answer.cited_endpoints == ("/api/accounts/123/users/999",)


def test_case_chat_answers_weak():
    answer = answer_case_question(_case_summary(), "what is weak or false positive?")

    assert answer.intent == "weak"
    assert "/api/accounts/123/users/random" in answer.answer
    assert "Do not report" in answer.answer


def test_case_chat_answers_report_ready():
    answer = answer_case_question(_case_summary(), "is this report ready?")

    assert answer.intent == "report-ready"
    assert "/api/accounts/123/users/999" in answer.answer
    assert answer.next_actions


def test_case_chat_answers_missing_evidence():
    answer = answer_case_question(_case_summary(), "what evidence is missing?")

    assert answer.intent == "missing-evidence"
    assert "/api/accounts/123/users/random" in answer.cited_endpoints
    assert "Evidence proving behavior differs" in answer.next_actions[0]


def test_case_chat_answers_do_not_claim():
    answer = answer_case_question(_case_summary(), "what should I not claim?")

    assert answer.intent == "do-not-claim"
    assert "Avoid overclaiming" in answer.answer
    assert any("Do not claim High severity" in item for item in answer.next_actions)


def test_case_chat_general_answer():
    answer = answer_case_question(_case_summary(), "summarize this case")

    assert answer.intent == "general"
    assert "Priority counts" in answer.answer


def test_case_chat_requires_case_summary_kind():
    with pytest.raises(ValueError):
        answer_case_question({"kind": "wrong"}, "what next?")


def test_case_chat_requires_question():
    with pytest.raises(ValueError):
        answer_case_question(_case_summary(), "  ")


def test_case_chat_understands_messy_next_question():
    answer = answer_case_question(_case_summary(), "what should I do now?")

    assert answer.intent == "next-tests"
    assert "/api/accounts/123/users/999" in answer.answer


def test_case_chat_understands_messy_report_ready_question():
    answer = answer_case_question(_case_summary(), "can I submit this? is it reportable?")

    assert answer.intent == "report-ready"
    assert "/api/accounts/123/users/999" in answer.answer


def test_case_chat_understands_messy_missing_evidence_question():
    answer = answer_case_question(_case_summary(), "what proof is missing here?")

    assert answer.intent == "missing-evidence"
    assert "/api/accounts/123/users/random" in answer.cited_endpoints
