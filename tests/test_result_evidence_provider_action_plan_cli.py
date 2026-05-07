import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _provider_review():
    return {
        "kind": "result_evidence_case_chat_provider_result_review",
        "recommendation": "use-as-planning-note-needs-evidence",
        "reviewed_actions": [
            {
                "action": "Validate own-object baseline.",
                "status": "supported-planning-action",
                "reason": "Action overlaps with local next-action evidence.",
            },
            {
                "action": "Check admin role behavior.",
                "status": "needs-local-evidence",
                "reason": "Action is not directly supported by local artifacts.",
            },
            {
                "action": "Run this command to dump data.",
                "status": "unsafe-review-required",
                "reason": "Action wording appears unsafe.",
            },
        ],
        "warning_flags": ["manual-command-review-needed"],
        "unsupported_claims": ["Provider output includes severity wording that must be proven."],
        "missing_evidence": ["Impact proof"],
        "untrusted_suggestion": True,
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "missing_evidence": ["Random-object baseline"],
    }


def test_case_chat_suggestion_action_plan_cli_writes_markdown_and_json(tmp_path):
    review_file = tmp_path / "provider-review.json"
    memory_file = tmp_path / "case-memory.json"
    output_file = tmp_path / "action-plan.md"
    json_output = tmp_path / "action-plan.json"

    review_file.write_text(json.dumps(_provider_review()))
    memory_file.write_text(json.dumps(_case_memory()))

    result = runner.invoke(
        app,
        [
            "case-chat-suggestion-action-plan",
            "--provider-review",
            str(review_file),
            "--case-memory",
            str(memory_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Provider Suggestion Action Plan" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_provider_suggestion_action_plan"
    assert data["recommendation"] == "reject-unsafe-or-overclaimed-actions"
    assert len(data["approved_actions"]) == 1
    assert len(data["evidence_needed_actions"]) == 1
    assert len(data["rejected_actions"]) == 1
    assert "Impact proof" in data["missing_evidence"]
    assert "Random-object baseline" in data["missing_evidence"]
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_suggestion_action_plan_cli_missing_review_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-suggestion-action-plan",
            "--provider-review",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Provider result review JSON not found" in result.output


def test_case_chat_suggestion_action_plan_cli_wrong_review_kind(tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-suggestion-action-plan",
            "--provider-review",
            str(review_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid suggestion action plan input" in result.output


def test_case_chat_suggestion_action_plan_cli_wrong_memory_kind(tmp_path):
    review_file = tmp_path / "provider-review.json"
    memory_file = tmp_path / "case-memory.json"

    review_file.write_text(json.dumps(_provider_review()))
    memory_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-suggestion-action-plan",
            "--provider-review",
            str(review_file),
            "--case-memory",
            str(memory_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid suggestion action plan input" in result.output
