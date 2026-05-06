import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "top_endpoint": "/api/high",
        "cited_endpoints": ["/api/high"],
        "open_next_actions": ["Capture own-object baseline."],
        "missing_evidence": ["Random-object baseline"],
        "safety": {
            "local_only": True,
            "llm_provider_calls": False,
            "vulnerability_confirmation": False,
        },
    }


def _grounded_answer():
    return {
        "kind": "result_evidence_grounded_answer",
        "answer": "Not ready yet.",
        "intent": "report-ready",
        "grounding": [
            {
                "artifact": "case-memory",
                "path": "missing_evidence[0]",
                "value": "Random-object baseline",
                "reason": "Shows missing evidence.",
            }
        ],
        "cited_endpoints": ["/api/high"],
        "next_actions": ["Capture random-object baseline."],
    }


def test_case_chat_prompt_package_cli_writes_markdown_and_json(tmp_path):
    memory_file = tmp_path / "case-memory.json"
    grounded_file = tmp_path / "grounded.json"
    output_file = tmp_path / "prompt.md"
    json_output = tmp_path / "prompt.json"

    memory_file.write_text(json.dumps(_case_memory()))
    grounded_file.write_text(json.dumps(_grounded_answer()))

    result = runner.invoke(
        app,
        [
            "case-chat-prompt-package",
            "--case-memory",
            str(memory_file),
            "--question",
            "can I submit this?",
            "--grounded-answer",
            str(grounded_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Case Chat Prompt Package" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Case Chat LLM Prompt Package" in markdown
    assert "Provider Execution: false" in markdown
    assert "## User Prompt" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_case_chat_prompt_package"
    assert data["question"] == "can I submit this?"
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_prompt_package_cli_missing_memory_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-prompt-package",
            "--case-memory",
            str(tmp_path / "missing.json"),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 1
    assert "Case memory JSON not found" in result.output


def test_case_chat_prompt_package_cli_invalid_memory_json_exits_nonzero(tmp_path):
    memory_file = tmp_path / "bad.json"
    memory_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "case-chat-prompt-package",
            "--case-memory",
            str(memory_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case memory JSON" in result.output


def test_case_chat_prompt_package_cli_wrong_memory_kind_exits_nonzero(tmp_path):
    memory_file = tmp_path / "memory.json"
    memory_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-prompt-package",
            "--case-memory",
            str(memory_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case chat prompt package input" in result.output
