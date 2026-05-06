import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_chat_context_router_cli_writes_markdown_and_json(tmp_path):
    artifact_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "route.md"
    json_output = tmp_path / "route.json"

    artifact_file.write_text(json.dumps({"kind": "result_evidence_case_summary"}))

    result = runner.invoke(
        app,
        [
            "chat-context-router",
            str(artifact_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Chat Context Router" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Chat Context Route" in markdown
    assert "\\n" not in markdown
    assert "case-chat-context" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_chat_context_route"
    assert data["artifact_kind"] == "result_evidence_case_summary"
    assert data["recommended_command"] == "case-chat-context"
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_chat_context_router_cli_priority_ranking(tmp_path):
    artifact_file = tmp_path / "ranking.json"
    json_output = tmp_path / "route.json"

    artifact_file.write_text(json.dumps({"kind": "result_evidence_priority_ranking"}))

    result = runner.invoke(
        app,
        [
            "chat-context-router",
            str(artifact_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["artifact_label"] == "Priority ranking"
    assert data["recommended_command"] == "result-evidence-multi-agent-review"


def test_chat_context_router_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["chat-context-router", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Artifact JSON not found" in result.output


def test_chat_context_router_cli_invalid_json_exits_nonzero(tmp_path):
    artifact_file = tmp_path / "bad.json"
    artifact_file.write_text("{not json")

    result = runner.invoke(app, ["chat-context-router", str(artifact_file)])

    assert result.exit_code == 2
    assert "Invalid artifact JSON" in result.output


def test_chat_context_router_cli_missing_kind_exits_nonzero(tmp_path):
    artifact_file = tmp_path / "artifact.json"
    artifact_file.write_text(json.dumps({}))

    result = runner.invoke(app, ["chat-context-router", str(artifact_file)])

    assert result.exit_code == 2
    assert "Invalid chat context router input" in result.output
