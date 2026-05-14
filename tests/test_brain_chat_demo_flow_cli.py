import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_brain_chat_demo_flow_cli_writes_artifacts_and_outputs(tmp_path):
    endpoints = tmp_path / "endpoints.txt"
    endpoints.write_text(
        "/api/accounts/123/users/{id}/permissions\n/api/status\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "case"
    output_file = tmp_path / "flow.md"
    json_output = tmp_path / "flow.json"

    result = runner.invoke(
        app,
        [
            "brain-chat-demo-flow",
            str(endpoints),
            "--target",
            "demo.local",
            "--output-dir",
            str(output_dir),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain Chat Demo Flow" in result.output
    assert "ready-for-brain-chat" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_chat_demo_flow"
    assert data["recommendation"] == "ready-for-brain-chat"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    assert (output_dir / "brain" / "03-ai-brain.json").exists()
    assert (output_dir / "brain" / "06-brain-decision.json").exists()
    assert (output_dir / "brain" / "07-brain-approval.json").exists()
    assert (output_dir / "brain" / "09-tool-execution-gate.json").exists()


def test_brain_chat_demo_flow_cli_missing_file_returns_error(tmp_path):
    result = runner.invoke(
        app,
        [
            "brain-chat-demo-flow",
            str(tmp_path / "missing.txt"),
            "--output-dir",
            str(tmp_path / "case"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid brain chat demo flow input" in result.output
