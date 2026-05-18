import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _session_data():
    return {
        "turn_count": 2,
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
                "question": "What evidence do we need?",
                "answer": "Evidence planning.",
                "target_name": "demo.local",
                "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
                "decision": "blocked-pending-scope-and-controls",
                "approval_status": "blocked-pending-approval",
                "execution_gate": "blocked-manifest-execution-disabled",
                "execution_allowed": False,
                "created_at": "2026-01-01T00:01:00+00:00",
            },
        ],
    }


def test_brain_chat_session_next_step_cli_reads_explicit_session(tmp_path):
    session_file = tmp_path / "brain-chat-session.json"
    output_file = tmp_path / "next-step.md"
    json_output = tmp_path / "next-step.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "brain-chat-session-next-step",
            str(session_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Session Next-Step Plan" in result.output
    assert "Authorization decision diff" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_session_next_step_plan"
    assert data["recommendation"] == "resolve-blockers-before-validation"
    assert data["current_focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_brain_chat_session_next_step_cli_defaults_to_current_directory(tmp_path, monkeypatch):
    session_file = tmp_path / "brain-chat-session.json"
    session_file.write_text(json.dumps(_session_data()), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["brain-chat-session-next-step"])

    assert result.exit_code == 0
    assert "Brain Chat Session Next-Step Plan" in result.output
    assert "resolve-blockers-before-validation" in result.output


def test_brain_chat_session_next_step_cli_missing_file_returns_error(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-session-next-step",
            str(tmp_path / "missing-session.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Brain chat session JSON not found" in result.output
