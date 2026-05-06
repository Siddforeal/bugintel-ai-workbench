import pytest

from bugintel.core.result_evidence_question_intent import normalize_question_intent


def test_question_intent_normalizes_next_tests_messy_question():
    result = normalize_question_intent("bro what should I do now?")

    assert result.intent == "next-tests"
    assert result.normalized_question == "bro what should i do now"
    assert "what should i do now" in result.matched_terms
    assert result.to_dict()["safety"]["llm_provider_calls"] is False


def test_question_intent_normalizes_report_ready():
    result = normalize_question_intent("can I submit this? is it reportable?")

    assert result.intent == "report-ready"
    assert result.confidence == "medium"


def test_question_intent_normalizes_missing_evidence():
    result = normalize_question_intent("what proof is missing here?")

    assert result.intent == "missing-evidence"


def test_question_intent_normalizes_do_not_claim():
    result = normalize_question_intent("what should I avoid saying in report?")

    assert result.intent == "do-not-claim"


def test_question_intent_normalizes_reviewers():
    result = normalize_question_intent("what do agents think about this?")

    assert result.intent == "reviewers"


def test_question_intent_normalizes_final_report_focus():
    result = normalize_question_intent("what should final report focus on?")

    assert result.intent == "final-report-focus"


def test_question_intent_normalizes_session_summary():
    result = normalize_question_intent("summarize chat memory")

    assert result.intent == "session-summary"


def test_question_intent_uses_keyword_fallback():
    result = normalize_question_intent("proof?")

    assert result.intent == "missing-evidence"
    assert result.confidence == "low-medium"


def test_question_intent_general_for_unknown_question():
    result = normalize_question_intent("hello there")

    assert result.intent == "general"
    assert result.confidence == "low"


def test_question_intent_rejects_empty_question():
    with pytest.raises(ValueError):
        normalize_question_intent("  ")
