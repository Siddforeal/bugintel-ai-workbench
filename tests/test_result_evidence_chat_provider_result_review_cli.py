import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _imported_result():
    return {
        "kind": "result_evidence_case_chat_provider_result",
        "provider_output": "This is not proof.\\n- Validate own-object baseline.\\n- Confirm random-object behavior.",
        "suggested_actions": [
            "Validate own-object baseline.",
            "Confirm random-object behavior.",
        ],
        "warning_flags": [],
        "untrusted_suggestion": True,
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "top_endpoint": "/api/high",
        "cited_endpoints": ["/api/high"],
        "open_next_actions": [
            "Validate own-object baseline.",
            "Confirm random-object behavior.",
        ],
        "missing_evidence": ["Impact proof"],
    }


def _grounded_answer():
    return {
        "kind": "result_evidence_grounded_answer",
        "next_actions": ["Validate own-object baseline."],
        "grounding": [
            {
                "artifact": "case-memory",
                "path": "top_endpoint",
                "value": "/api/high",
            }
        ],
    }


def test_case_chat_provider_result_review_cli_writes_markdown_and_json(tmp_path):
    imported_file = tmp_path / "imported.json"
    memory_file = tmp_path / "memory.json"
    grounded_file = tmp_path / "grounded.json"
    output_file = tmp_path / "review.md"
    json_output = tmp_path / "review.json"

    imported_file.write_text(json.dumps(_imported_result()))
    memory_file.write_text(json.dumps(_case_memory()))
    grounded_file.write_text(json.dumps(_grounded_answer()))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-review",
            "--imported-result",
            str(imported_file),
            "--case-memory",
            str(memory_file),
            "--grounded-answer",
            str(grounded_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Provider Suggestion Review" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_case_chat_provider_result_review"
    assert data["untrusted_suggestion"] is True
    assert data["recommendation"] == "use-as-planning-note-needs-evidence"
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_provider_result_review_cli_flags_overclaims(tmp_path):
    imported = _imported_result()
    imported["provider_output"] = "This is a confirmed vulnerability with high severity."
    imported["warning_flags"] = [
        "overclaim-confirmed-vulnerability",
        "severity-claim-needs-proof",
    ]

    imported_file = tmp_path / "imported.json"
    imported_file.write_text(json.dumps(imported))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-review",
            "--imported-result",
            str(imported_file),
        ],
    )

    assert result.exit_code == 0
    assert "Warning flags" in result.output
    assert "Unsupported claims" in result.output


def test_case_chat_provider_result_review_cli_missing_imported_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-review",
            "--imported-result",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Imported provider result JSON not found" in result.output


def test_case_chat_provider_result_review_cli_wrong_imported_kind(tmp_path):
    imported_file = tmp_path / "imported.json"
    imported_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-provider-result-review",
            "--imported-result",
            str(imported_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid provider result review input" in result.output
