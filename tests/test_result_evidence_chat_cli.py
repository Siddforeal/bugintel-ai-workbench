import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


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


def test_case_chat_cli_writes_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "case-chat.json"
    case_file.write_text(json.dumps(_case_summary()))

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what should I test next?",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Local Research Chat" in result.output
    assert "Answer" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["intent"] == "next-tests"
    assert data["cited_endpoints"] == ["/api/accounts/123/users/999"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_case_chat_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat",
            str(tmp_path / "missing.json"),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_chat_cli_invalid_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output


def test_case_chat_cli_wrong_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case chat input" in result.output


def test_case_chat_cli_appends_session_file(tmp_path):
    case_file = tmp_path / "case-summary.json"
    session_file = tmp_path / "case-chat-session.json"
    output_file = tmp_path / "case-chat-answer.json"

    case_file.write_text(json.dumps(_case_summary()))

    first = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what should I test next?",
            "--session-file",
            str(session_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert first.exit_code == 0
    assert "Saved case chat session" in first.output
    assert session_file.exists()
    assert output_file.exists()

    second = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what evidence is missing?",
            "--session-file",
            str(session_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert second.exit_code == 0
    data = json.loads(session_file.read_text())
    assert data["kind"] == "result_evidence_case_chat_session"
    assert data["turn_count"] == 2
    assert data["intents"]["next-tests"] == 1
    assert data["intents"]["missing-evidence"] == 1
    assert "/api/accounts/123/users/999" in data["cited_endpoints"]
    assert "/api/accounts/123/users/random" in data["cited_endpoints"]
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    answer_data = json.loads(output_file.read_text())
    assert "session" in answer_data
    assert answer_data["session"]["turn_count"] == 2


def test_case_chat_cli_rejects_invalid_session_file(tmp_path):
    case_file = tmp_path / "case-summary.json"
    session_file = tmp_path / "bad-session.json"

    case_file.write_text(json.dumps(_case_summary()))
    session_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what should I test next?",
            "--session-file",
            str(session_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case chat session file" in result.output
