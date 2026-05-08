import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _action_plan():
    return {
        "kind": "result_evidence_provider_suggestion_action_plan",
        "recommendation": "reject-unsafe-or-overclaimed-actions",
        "approved_actions": [
            {
                "action": "Validate own-object baseline.",
                "status": "supported-planning-action",
                "manual_order": 1,
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
            },
        ],
        "evidence_needed_actions": [
            {
                "action": "Check admin role behavior.",
                "status": "needs-local-evidence",
                "manual_order": 2,
                "reason": "Needs role-specific local evidence.",
                "evidence_needed": ["Admin account baseline"],
            },
        ],
        "rejected_actions": [
            {
                "action": "Run unsafe command.",
                "status": "unsafe-review-required",
                "manual_order": 3,
                "reason": "Unsafe wording.",
                "evidence_needed": ["Manual safety review"],
            },
        ],
        "missing_evidence": ["Impact proof"],
        "report_guardrails": ["Do not claim severity until supported by local evidence."],
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "missing_evidence": ["Random-object baseline"],
    }


def test_case_chat_action_plan_apply_preview_cli_writes_markdown_and_json(tmp_path):
    action_plan_file = tmp_path / "action-plan.json"
    memory_file = tmp_path / "case-memory.json"
    output_file = tmp_path / "apply-preview.md"
    json_output = tmp_path / "apply-preview.json"

    action_plan_file.write_text(json.dumps(_action_plan()))
    memory_file.write_text(json.dumps(_case_memory()))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview",
            "--action-plan",
            str(action_plan_file),
            "--case-memory",
            str(memory_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Action Plan Apply Preview" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_provider_suggestion_action_plan_apply_preview"
    assert data["recommendation"] == "preview-approved-updates-but-keep-blocked-items-unapplied"
    assert len(data["case_memory_updates"]) == 1
    assert len(data["research_state_updates"]) == 1
    assert len(data["blocked_updates"]) == 2
    assert "Impact proof" in data["missing_evidence"]
    assert "Random-object baseline" in data["missing_evidence"]
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_action_plan_apply_preview_cli_missing_action_plan_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview",
            "--action-plan",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Suggestion action plan JSON not found" in result.output


def test_case_chat_action_plan_apply_preview_cli_wrong_action_plan_kind(tmp_path):
    action_plan_file = tmp_path / "action-plan.json"
    action_plan_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview",
            "--action-plan",
            str(action_plan_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid action plan apply preview input" in result.output


def test_case_chat_action_plan_apply_preview_cli_wrong_memory_kind(tmp_path):
    action_plan_file = tmp_path / "action-plan.json"
    memory_file = tmp_path / "case-memory.json"

    action_plan_file.write_text(json.dumps(_action_plan()))
    memory_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview",
            "--action-plan",
            str(action_plan_file),
            "--case-memory",
            str(memory_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid action plan apply preview input" in result.output
