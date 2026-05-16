import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _write_state(tmp_path):
    (tmp_path / "03-ai-brain.json").write_text(json.dumps({
        "target_name": "demo",
        "focus_queue": [
            {
                "endpoint": "/api/accounts/123/users/{id}/permissions",
                "priority_band": "critical",
                "priority_score": 80,
                "reason": "High-signal endpoint with open hypotheses.",
            }
        ],
    }))
    (tmp_path / "06-brain-decision.json").write_text(json.dumps({
        "decision": "blocked-pending-scope-and-controls",
    }))
    (tmp_path / "07-brain-approval.json").write_text(json.dumps({
        "approval_status": "blocked-pending-approval",
    }))
    (tmp_path / "09-tool-execution-gate.json").write_text(json.dumps({
        "gate_decision": "blocked-manifest-execution-disabled",
        "execution_allowed": False,
    }))


def test_brain_chat_cli_prints_reply(tmp_path):
    _write_state(tmp_path)

    result = runner.invoke(app, ["brain-chat", "hello", "--state-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert "Blackhole:" in result.output
    assert "Hello Sidd" in result.output
    assert "blocked-manifest-execution-disabled" in result.output


def test_brain_chat_cli_writes_json(tmp_path):
    _write_state(tmp_path)
    output = tmp_path / "reply.json"

    result = runner.invoke(
        app,
        ["brain-chat", "status", "--state-dir", str(tmp_path), "--json-output", str(output)],
    )

    assert result.exit_code == 0
    data = json.loads(output.read_text())
    assert data["target_name"] == "demo"
    assert data["planning_only"] is True
    assert "Current focus endpoint" in data["answer"]


def test_brain_chat_cli_appends_session(tmp_path):
    _write_state(tmp_path)
    session_file = tmp_path / "session.json"

    first = runner.invoke(
        app,
        ["brain-chat", "hello", "--state-dir", str(tmp_path), "--session", str(session_file)],
    )
    second = runner.invoke(
        app,
        ["brain-chat", "status", "--state-dir", str(tmp_path), "--session", str(session_file)],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Saved brain chat session" in second.output

    data = json.loads(session_file.read_text())
    assert data["turn_count"] == 2
    assert data["planning_only"] is True
    assert data["turns"][0]["question"] == "hello"
    assert data["turns"][1]["question"] == "status"


def test_brain_chat_cli_resolves_case_dir(tmp_path):
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()
    _write_state(brain_dir)

    result = runner.invoke(
        app,
        [
            "brain-chat",
            "What should I test first?",
            "--case-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "/api/accounts/123/users/{id}/permissions" in result.output
    assert "critical/80" in result.output


def test_brain_chat_cli_auto_discovers_brain_subdirectory(tmp_path, monkeypatch):
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()
    _write_state(brain_dir)

    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat",
            "What should I test first?",
        ],
    )

    assert result.exit_code == 0
    assert "/api/accounts/123/users/{id}/permissions" in result.output
    assert "critical/80" in result.output


def test_brain_chat_cli_auto_saves_session_for_case_dir(tmp_path):
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()
    _write_state(brain_dir)

    result = runner.invoke(
        app,
        [
            "brain-chat",
            "What should I test first?",
            "--case-dir",
            str(tmp_path),
        ],
    )

    session_file = tmp_path / "brain-chat-session.json"

    assert result.exit_code == 0
    assert "Saved brain chat session" in result.output
    assert session_file.exists()

    data = json.loads(session_file.read_text())
    assert data["turn_count"] == 1
    assert data["turns"][0]["question"] == "What should I test first?"


def test_brain_chat_cli_auto_saves_session_from_case_cwd(tmp_path, monkeypatch):
    brain_dir = tmp_path / "brain"
    brain_dir.mkdir()
    _write_state(brain_dir)

    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat",
            "What evidence do we need?",
        ],
    )

    session_file = tmp_path / "brain-chat-session.json"

    assert result.exit_code == 0
    assert "Saved brain chat session" in result.output
    assert session_file.exists()

    data = json.loads(session_file.read_text())
    assert data["turn_count"] == 1
    assert data["turns"][0]["question"] == "What evidence do we need?"


def test_brain_chat_cli_state_dir_does_not_auto_save_session(tmp_path):
    _write_state(tmp_path)

    result = runner.invoke(
        app,
        [
            "brain-chat",
            "What should I test first?",
            "--state-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Saved brain chat session" not in result.output
    assert not (tmp_path / "brain-chat-session.json").exists()
