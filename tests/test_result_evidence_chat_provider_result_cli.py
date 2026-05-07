import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _prompt_package():
    return {
        "kind": "result_evidence_case_chat_prompt_package",
        "source": "result-evidence-case-chat-prompt",
        "prompt_package": {
            "system_prompt": "safe",
            "user_prompt": "safe",
            "redaction_applied": False,
        },
    }


def test_case_chat_provider_result_import_cli_writes_markdown_and_json(tmp_path):
    provider_file = tmp_path / "provider-output.txt"
    prompt_file = tmp_path / "prompt.json"
    output_file = tmp_path / "import.md"
    json_output = tmp_path / "import.json"

    provider_file.write_text(
        "This is not proof.\\n- Validate own-object baseline.\\n- Confirm random-object behavior."
    )
    prompt_file.write_text(json.dumps(_prompt_package()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-import",
            "--provider-result",
            str(provider_file),
            "--prompt-package",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Imported Case Chat Provider Result" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_case_chat_provider_result"
    assert data["untrusted_suggestion"] is True
    assert "Validate own-object baseline." in data["suggested_actions"]
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_provider_result_import_cli_flags_warnings(tmp_path):
    provider_file = tmp_path / "provider-output.txt"
    prompt_file = tmp_path / "prompt.json"
    json_output = tmp_path / "import.json"

    provider_file.write_text("This is a confirmed vulnerability with high severity. Run this command.")
    prompt_file.write_text(json.dumps(_prompt_package()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-import",
            "--provider-result",
            str(provider_file),
            "--prompt-package",
            str(prompt_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Warning flags" in result.output

    data = json.loads(json_output.read_text())
    assert "overclaim-confirmed-vulnerability" in data["warning_flags"]
    assert "severity-claim-needs-proof" in data["warning_flags"]


def test_case_chat_provider_result_import_cli_missing_provider_file(tmp_path):
    prompt_file = tmp_path / "prompt.json"
    prompt_file.write_text(json.dumps(_prompt_package()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-import",
            "--provider-result",
            str(tmp_path / "missing.txt"),
            "--prompt-package",
            str(prompt_file),
        ],
    )

    assert result.exit_code == 1
    assert "Provider result text not found" in result.output


def test_case_chat_provider_result_import_cli_wrong_prompt_kind(tmp_path):
    provider_file = tmp_path / "provider-output.txt"
    prompt_file = tmp_path / "prompt.json"

    provider_file.write_text("Review the evidence.")
    prompt_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-import",
            "--provider-result",
            str(provider_file),
            "--prompt-package",
            str(prompt_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid provider result import input" in result.output
