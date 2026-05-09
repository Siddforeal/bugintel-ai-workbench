import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _reviewed_apply_packet():
    return {
        "kind": "result_evidence_reviewed_apply_packet",
        "recommendation": "human-approval-required-block-unsafe-items",
        "approved_planning_updates": [
            {
                "action": "Add manual baseline validation note.",
                "status": "approved-planning-note",
                "source_category": "safe-planning-note",
                "source": "case_memory",
                "severity": "info",
                "reason": "Safe planning note.",
                "evidence_needed": [],
                "checklist": ["Confirm this remains a planning note only."],
            }
        ],
        "duplicate_updates": [],
        "blocked_updates": [
            {
                "action": "Check admin role behavior.",
                "status": "blocked-needs-review",
                "source_category": "blocked-update",
                "source": "block_until_local_evidence_exists",
                "severity": "medium",
                "reason": "Blocked item must not be applied automatically.",
                "evidence_needed": ["Admin account baseline"],
                "checklist": ["Close required local evidence before approval."],
            }
        ],
        "evidence_gaps": [],
        "unsafe_or_rejected_items": [
            {
                "action": "Run unsafe command.",
                "status": "unsafe-or-rejected",
                "source_category": "unsafe-or-rejected-update-risk",
                "source": "block_rejected_or_unsafe_action",
                "severity": "high",
                "reason": "Unsafe item must remain blocked.",
                "evidence_needed": ["Manual safety review"],
                "checklist": ["Do not apply this item automatically."],
            }
        ],
        "overclaim_risks": [],
        "report_guardrails": ["Approved planning notes are not vulnerability proof."],
        "human_approval_checklist": ["Confirm this packet is being used as planning input only."],
        "safety": {
            "human_approval_required": True,
            "state_mutation": False,
            "vulnerability_confirmation": False,
        },
    }


def test_case_chat_reviewed_apply_packet_export_bundle_cli_writes_markdown_and_json(tmp_path):
    packet_file = tmp_path / "reviewed-apply-packet.json"
    artifact_file = tmp_path / "packet.md"
    output_file = tmp_path / "bundle.md"
    json_output = tmp_path / "bundle.json"

    packet_file.write_text(json.dumps(_reviewed_apply_packet()), encoding="utf-8")
    artifact_file.write_text("# Packet\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet-export-bundle",
            "--reviewed-apply-packet",
            str(packet_file),
            "--artifact",
            str(artifact_file),
            "--artifact-role",
            "packet-markdown",
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Reviewed Apply Packet Export Bundle" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_reviewed_apply_packet_export_bundle"
    assert data["recommendation"] == "export-for-human-review-block-unsafe-items"
    assert data["packet_counts"]["approved_planning_updates"] == 1
    assert data["packet_counts"]["blocked_updates"] == 1
    assert data["packet_counts"]["unsafe_or_rejected_items"] == 1
    assert len(data["included_artifacts"]) == 1
    assert data["included_artifacts"][0]["role"] == "packet-markdown"
    assert data["included_artifacts"][0]["exists"] is True
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_reviewed_apply_packet_export_bundle_cli_missing_packet_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet-export-bundle",
            "--reviewed-apply-packet",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Reviewed apply packet JSON not found" in result.output


def test_case_chat_reviewed_apply_packet_export_bundle_cli_wrong_packet_kind(tmp_path):
    packet_file = tmp_path / "reviewed-apply-packet.json"
    packet_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet-export-bundle",
            "--reviewed-apply-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid reviewed apply packet export bundle input" in result.output


def test_case_chat_reviewed_apply_packet_export_bundle_cli_invalid_json(tmp_path):
    packet_file = tmp_path / "reviewed-apply-packet.json"
    packet_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-reviewed-apply-packet-export-bundle",
            "--reviewed-apply-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid reviewed apply packet JSON" in result.output
