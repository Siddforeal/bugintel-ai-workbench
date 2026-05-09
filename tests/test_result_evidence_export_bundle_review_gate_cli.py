import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()
GOOD_SHA = "a" * 64


def _export_bundle():
    return {
        "kind": "result_evidence_reviewed_apply_packet_export_bundle",
        "bundle_id": "reviewed-apply-bundle-test123",
        "recommendation": "export-for-human-review-block-unsafe-items",
        "packet_recommendation": "human-approval-required-block-unsafe-items",
        "packet_counts": {
            "approved_planning_updates": 1,
            "duplicate_updates": 0,
            "blocked_updates": 1,
            "evidence_gaps": 1,
            "unsafe_or_rejected_items": 1,
            "overclaim_risks": 0,
        },
        "included_artifacts": [
            {
                "path": "/tmp/packet.md",
                "role": "packet-markdown",
                "exists": True,
                "size_bytes": 100,
                "sha256": GOOD_SHA,
                "note": "",
            }
        ],
        "human_review_checklist": ["Confirm the export bundle is used as review evidence only."],
        "report_guardrails": ["Bundled planning notes are not vulnerability proof."],
        "safety": {
            "local_only": True,
            "planning_only": True,
            "human_approval_required": True,
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "network_interaction": False,
            "target_mutation": False,
            "tool_execution": False,
            "browser_execution": False,
            "llm_provider_calls": False,
            "provider_execution": False,
            "vulnerability_confirmation": False,
        },
    }


def test_case_chat_export_bundle_review_gate_cli_writes_markdown_and_json(tmp_path):
    bundle_file = tmp_path / "export-bundle.json"
    output_file = tmp_path / "export-bundle-review.md"
    json_output = tmp_path / "export-bundle-review.json"

    bundle_file.write_text(json.dumps(_export_bundle()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-review-gate",
            "--export-bundle",
            str(bundle_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Export Bundle Review Gate" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_export_bundle_review_gate"
    assert data["recommendation"] == "use-only-for-internal-review-block-high-risk-items"
    assert len(data["packet_risk_findings"]) == 2
    assert len(data["evidence_gap_findings"]) == 1
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_export_bundle_review_gate_cli_missing_bundle_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-review-gate",
            "--export-bundle",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Export bundle JSON not found" in result.output


def test_case_chat_export_bundle_review_gate_cli_wrong_bundle_kind(tmp_path):
    bundle_file = tmp_path / "export-bundle.json"
    bundle_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-review-gate",
            "--export-bundle",
            str(bundle_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid export bundle review gate input" in result.output


def test_case_chat_export_bundle_review_gate_cli_invalid_json(tmp_path):
    bundle_file = tmp_path / "export-bundle.json"
    bundle_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-review-gate",
            "--export-bundle",
            str(bundle_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid export bundle JSON" in result.output
