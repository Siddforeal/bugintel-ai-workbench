import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _session_data():
    return {
        "turn_count": 3,
        "planning_only": True,
        "execution_state": "not_executed",
        "turns": [
            {
                "question": "What should I test first?",
                "answer": "Focus endpoint.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:00:00+00:00",
            },
            {
                "question": "What is blocking validation?",
                "answer": "Validation is blocked.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:01:00+00:00",
            },
            {
                "question": "What should I test first?",
                "answer": "Focus endpoint.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:02:00+00:00",
            },
        ],
    }


def test_brain_chat_session_summary_cli_reads_explicit_session(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    output_file = tmp_path / "summary.md"
    json_output = tmp_path / "summary.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-session-summary",
            str(session_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Session Summary" in result.output
    assert "What should I test first?" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["turn_count"] == 3
    assert data["latest_question"] == "What should I test first?"
    assert data["latest_focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["repeated_questions"] == ["What should I test first?"]


def test_brain_chat_session_summary_cli_defaults_to_current_directory(tmp_path, monkeypatch):
    session_file = tmp_path / "brain-chat-session.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["brain-chat-session-summary"])

    assert result.exit_code == 0
    assert "Brain Chat Session Summary" in result.output
    assert "blocked-manifest-execution-disabled" in result.output


def test_brain_chat_session_summary_cli_missing_file_returns_error(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-session-summary",
            str(tmp_path / "missing-session.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Brain chat session JSON not found" in result.output
