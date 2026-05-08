import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _apply_preview():
    return {
        "kind": "result_evidence_provider_suggestion_action_plan_apply_preview",
        "recommendation": "preview-approved-updates-but-keep-blocked-items-unapplied",
        "case_memory_updates": [
            {
                "action": "Validate own-object baseline.",
                "preview_operation": "append_manual_next_action",
                "target_artifact": "case_memory",
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            }
        ],
        "research_state_updates": [
            {
                "action": "Validate own-object baseline.",
                "preview_operation": "append_planning_task",
                "target_artifact": "research_state",
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            }
        ],
        "blocked_updates": [
            {
                "action": "Run unsafe command.",
                "preview_operation": "block_rejected_or_unsafe_action",
                "target_artifact": "none",
                "reason": "Unsafe wording.",
                "evidence_needed": ["Manual safety review"],
                "source_status": "unsafe-review-required",
            }
        ],
        "missing_evidence": ["Impact proof"],
        "report_guardrails": ["Do not claim severity until supported by local evidence."],
        "safety": {
            "vulnerability_confirmation": False,
        },
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "missing_evidence": ["Random-object baseline"],
    }


def test_case_chat_action_plan_apply_preview_review_cli_writes_markdown_and_json(tmp_path):
    apply_preview_file = tmp_path / "apply-preview.json"
    memory_file = tmp_path / "case-memory.json"
    output_file = tmp_path / "apply-preview-review.md"
    json_output = tmp_path / "apply-preview-review.json"

    apply_preview_file.write_text(json.dumps(_apply_preview()))
    memory_file.write_text(json.dumps(_case_memory()))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview-review",
            "--apply-preview",
            str(apply_preview_file),
            "--case-memory",
            str(memory_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Action Plan Apply Preview Review" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_action_plan_apply_preview_review"
    assert data["recommendation"] == "do-not-apply-review-unsafe-items"
    assert len(data["blocked_action_findings"]) == 1
    assert len(data["unsafe_update_findings"]) == 1
    assert "Impact proof" in str(data["evidence_gap_findings"])
    assert "Random-object baseline" in str(data["evidence_gap_findings"])
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_action_plan_apply_preview_review_cli_missing_preview_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview-review",
            "--apply-preview",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Action plan apply preview JSON not found" in result.output


def test_case_chat_action_plan_apply_preview_review_cli_wrong_preview_kind(tmp_path):
    apply_preview_file = tmp_path / "apply-preview.json"
    apply_preview_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview-review",
            "--apply-preview",
            str(apply_preview_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid action plan apply preview review input" in result.output


def test_case_chat_action_plan_apply_preview_review_cli_wrong_memory_kind(tmp_path):
    apply_preview_file = tmp_path / "apply-preview.json"
    memory_file = tmp_path / "case-memory.json"

    apply_preview_file.write_text(json.dumps(_apply_preview()))
    memory_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-action-plan-apply-preview-review",
            "--apply-preview",
            str(apply_preview_file),
            "--case-memory",
            str(memory_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid action plan apply preview review input" in result.output
