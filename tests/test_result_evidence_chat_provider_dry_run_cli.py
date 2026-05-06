import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _prompt_package():
    return {
        "kind": "result_evidence_case_chat_prompt_package",
        "prompt_package": {
            "system_prompt": "You are a safe assistant for authorized testing.",
            "user_prompt": "Review local artifacts only and suggest read-only checks.",
            "redaction_applied": False,
            "source": "result-evidence-case-chat-prompt",
            "safety_notes": [
                "Provider execution is not performed by this command.",
                "LLM output must be treated as suggestions, not confirmed findings.",
            ],
        },
    }


def test_case_chat_provider_dry_run_cli_writes_markdown_and_json(tmp_path):
    prompt_file = tmp_path / "prompt.json"
    output_file = tmp_path / "dry-run.md"
    json_output = tmp_path / "dry-run.json"

    prompt_file.write_text(json.dumps(_prompt_package()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-dry-run",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Case Chat Provider Dry Run" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_case_chat_provider_dry_run"
    assert data["provider_name"] == "disabled"
    assert data["audit_status"] == "pass"
    assert data["gate_allowed"] is False
    assert data["disabled_provider_status"] == "disabled"
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False


def test_case_chat_provider_dry_run_cli_unsupported_provider(tmp_path):
    prompt_file = tmp_path / "prompt.json"
    prompt_file.write_text(json.dumps(_prompt_package()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-dry-run",
            str(prompt_file),
            "--provider",
            "openai",
        ],
    )

    assert result.exit_code == 0
    assert "Unsupported LLM provider" in result.output


def test_case_chat_provider_dry_run_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["case-chat-provider-dry-run", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Case chat prompt package JSON not found" in result.output


def test_case_chat_provider_dry_run_cli_invalid_json_exits_nonzero(tmp_path):
    prompt_file = tmp_path / "bad.json"
    prompt_file.write_text("{not json")

    result = runner.invoke(app, ["case-chat-provider-dry-run", str(prompt_file)])

    assert result.exit_code == 2
    assert "Invalid case chat prompt package JSON" in result.output


def test_case_chat_provider_dry_run_cli_wrong_kind_exits_nonzero(tmp_path):
    prompt_file = tmp_path / "prompt.json"
    prompt_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(app, ["case-chat-provider-dry-run", str(prompt_file)])

    assert result.exit_code == 2
    assert "Invalid case chat provider dry-run input" in result.output
