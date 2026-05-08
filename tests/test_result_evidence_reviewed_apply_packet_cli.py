import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _apply_preview_review():
    return {
        "kind": "result_evidence_action_plan_apply_preview_review",
        "recommendation": "do-not-apply-review-unsafe-items",
        "duplicate_update_candidates": [
            {
                "category": "duplicate-existing-case-memory-action",
                "severity": "low",
                "message": "Candidate appears to already exist in case memory.",
                "action": "Validate own-object baseline.",
                "source": "case_memory",
                "evidence_needed": [],
            }
        ],
        "blocked_action_findings": [
            {
                "category": "blocked-update",
                "severity": "medium",
                "message": "Update is blocked and must not be applied automatically.",
                "action": "Check admin role behavior.",
                "source": "block_until_local_evidence_exists",
                "evidence_needed": ["Admin account baseline"],
            }
        ],
        "evidence_gap_findings": [
            {
                "category": "missing-evidence",
                "severity": "medium",
                "message": "Missing evidence must be closed before any report or future apply step.",
                "action": "Impact proof",
                "source": "missing_evidence",
                "evidence_needed": ["Impact proof"],
            }
        ],
        "unsafe_update_findings": [
            {
                "category": "unsafe-or-rejected-update-risk",
                "severity": "high",
                "message": "Candidate contains unsafe, rejected, or execution-like wording.",
                "action": "Run unsafe command.",
                "source": "block_rejected_or_unsafe_action",
                "evidence_needed": ["Manual safety review"],
            }
        ],
        "overclaim_risks": [],
        "safe_planning_notes": [
            {
                "category": "safe-planning-note",
                "severity": "info",
                "message": "Candidate can be kept as a manual planning note after human review.",
                "action": "Add manual baseline validation note.",
                "source": "case_memory",
                "evidence_needed": [],
            }
        ],
        "report_guardrails": ["Do not claim a vulnerability from apply preview candidates."],
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "manual_next_actions": ["Validate own-object baseline."],
    }


def test_case_chat_reviewed_apply_packet_cli_writes_markdown_and_json(tmp_path):
    review_file = tmp_path / "apply-preview-review.json"
    memory_file = tmp_path / "case-memory.json"
    output_file = tmp_path / "reviewed-apply-packet.md"
    json_output = tmp_path / "reviewed-apply-packet.json"

    review_file.write_text(json.dumps(_apply_preview_review()))
    memory_file.write_text(json.dumps(_case_memory()))

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet",
            "--apply-preview-review",
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
    assert "Reviewed Apply Packet" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_reviewed_apply_packet"
    assert data["recommendation"] == "human-approval-required-block-unsafe-items"
    assert len(data["approved_planning_updates"]) == 1
    assert len(data["blocked_updates"]) == 1
    assert len(data["evidence_gaps"]) == 1
    assert len(data["unsafe_or_rejected_items"]) == 1
    assert data["safety"]["human_approval_required"] is True
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_reviewed_apply_packet_cli_missing_review_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet",
            "--apply-preview-review",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Action plan apply preview review JSON not found" in result.output


def test_case_chat_reviewed_apply_packet_cli_wrong_review_kind(tmp_path):
    review_file = tmp_path / "apply-preview-review.json"
    review_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet",
            "--apply-preview-review",
            str(review_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid reviewed apply packet input" in result.output


def test_case_chat_reviewed_apply_packet_cli_wrong_memory_kind(tmp_path):
    review_file = tmp_path / "apply-preview-review.json"
    memory_file = tmp_path / "case-memory.json"

    review_file.write_text(json.dumps(_apply_preview_review()))
    memory_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet",
            "--apply-preview-review",
            str(review_file),
            "--case-memory",
            str(memory_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid reviewed apply packet input" in result.output
