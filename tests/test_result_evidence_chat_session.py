import json

import pytest

from bugintel.core.result_evidence_chat import answer_case_question
from bugintel.core.result_evidence_chat_session import (
    append_case_chat_turn,
    append_case_chat_turn_to_file,
    empty_case_chat_session,
    load_case_chat_session,
    save_case_chat_session,
)


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


def test_empty_case_chat_session_is_safe():
    session = empty_case_chat_session()
    data = session.to_dict()

    assert data["kind"] == "result_evidence_case_chat_session"
    assert data["turn_count"] == 0
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False
    assert session.summary_text() == "No local case-chat turns have been saved yet."


def test_append_case_chat_turn_accumulates_history():
    answer = answer_case_question(_case_summary(), "what should I test next?")
    session = append_case_chat_turn(empty_case_chat_session(), answer)
    data = session.to_dict()

    assert data["turn_count"] == 1
    assert data["turns"][0]["intent"] == "next-tests"
    assert data["cited_endpoints"] == ["/api/accounts/123/users/999"]
    assert data["next_actions"]
    assert "Saved local case-chat turns: 1." in session.summary_text()


def test_save_and_load_case_chat_session(tmp_path):
    path = tmp_path / "session.json"
    first = answer_case_question(_case_summary(), "what should I test next?")
    second = answer_case_question(_case_summary(), "what evidence is missing?")

    session = append_case_chat_turn(empty_case_chat_session(), first)
    session = append_case_chat_turn(session, second)

    save_case_chat_session(path, session)
    loaded = load_case_chat_session(path)

    data = loaded.to_dict()
    assert data["turn_count"] == 2
    assert data["intents"]["next-tests"] == 1
    assert data["intents"]["missing-evidence"] == 1
    assert "/api/accounts/123/users/999" in data["cited_endpoints"]
    assert "/api/accounts/123/users/random" in data["cited_endpoints"]


def test_append_case_chat_turn_to_file_creates_and_updates_session(tmp_path):
    path = tmp_path / "session.json"
    first = answer_case_question(_case_summary(), "what is strongest?")
    second = answer_case_question(_case_summary(), "what should I not claim?")

    session = append_case_chat_turn_to_file(path, first)
    assert session.to_dict()["turn_count"] == 1

    session = append_case_chat_turn_to_file(path, second)
    assert session.to_dict()["turn_count"] == 2

    data = json.loads(path.read_text())
    assert data["turn_count"] == 2
    assert data["safety"]["vulnerability_confirmation"] is False


def test_load_missing_case_chat_session_returns_empty(tmp_path):
    session = load_case_chat_session(tmp_path / "missing.json")

    assert session.to_dict()["turn_count"] == 0


def test_load_case_chat_session_rejects_bad_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json")

    with pytest.raises(ValueError):
        load_case_chat_session(path)


def test_load_case_chat_session_rejects_wrong_kind(tmp_path):
    path = tmp_path / "session.json"
    path.write_text(json.dumps({"kind": "wrong", "turns": []}))

    with pytest.raises(ValueError):
        load_case_chat_session(path)


def test_load_case_chat_session_rejects_missing_turns(tmp_path):
    path = tmp_path / "session.json"
    path.write_text(json.dumps({"kind": "result_evidence_case_chat_session"}))

    with pytest.raises(ValueError):
        load_case_chat_session(path)
