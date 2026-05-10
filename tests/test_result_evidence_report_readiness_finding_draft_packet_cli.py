import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _readiness():
    return {
        "kind": "result_evidence_export_bundle_report_readiness_review",
        "recommendation": "not-report-ready-remove-unsafe-items",
        "report_ready_support_notes": [
            {
                "subject": "approved_planning_updates=1",
                "status": "report-support-note",
                "category": "approved-review-package-note",
                "severity": "info",
                "source": "packet_counts",
                "reason": "Bundle contains approved planning notes.",
                "required_action": "Use as review notes only.",
            }
        ],
        "report_blockers": [],
        "missing_evidence": [
            {
                "subject": "evidence_gaps=1",
                "status": "missing-evidence",
                "category": "open-evidence-gap-count",
                "severity": "medium",
                "source": "packet_counts",
                "reason": "Bundle contains open evidence gaps.",
                "required_action": "Close evidence gaps.",
            }
        ],
        "unsafe_or_rejected_items": [
            {
                "subject": "unsafe_or_rejected_items=1",
                "status": "unsafe-or-rejected-blocker",
                "category": "unsafe-or-rejected-items-present",
                "severity": "high",
                "source": "packet_counts",
                "reason": "Bundle contains unsafe or rejected items.",
                "required_action": "Keep unsafe/rejected items blocked.",
            }
        ],
        "artifact_problems": [],
        "overclaim_risks": [],
        "safety_blockers": [],
        "final_report_readiness_checklist": ["Confirm every report claim maps to local evidence."],
        "report_guardrails": ["Do not claim confirmed vulnerability without local proof."],
    }


def test_case_chat_report_readiness_finding_draft_packet_cli_writes_markdown_and_json(tmp_path):
    readiness_file = tmp_path / "report-readiness.json"
    output_file = tmp_path / "finding-draft-packet.md"
    json_output = tmp_path / "finding-draft-packet.json"

    readiness_file.write_text(json.dumps(_readiness()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-report-readiness-finding-draft-packet",
            "--report-readiness",
            str(readiness_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Report Readiness Finding Draft Packet" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_report_readiness_finding_draft_packet"
    assert data["recommendation"] == "do-not-draft-remove-unsafe-items"
    assert len(data["title_candidates"]) == 1
    assert len(data["evidence_checklist"]) >= 1
    assert len(data["blocked_claims"]) >= 2
    assert len(data["do_not_claim_yet"]) >= 2
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_report_readiness_finding_draft_packet_cli_missing_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-report-readiness-finding-draft-packet",
            "--report-readiness",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Export bundle report readiness JSON not found" in result.output


def test_case_chat_report_readiness_finding_draft_packet_cli_wrong_kind(tmp_path):
    readiness_file = tmp_path / "report-readiness.json"
    readiness_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-report-readiness-finding-draft-packet",
            "--report-readiness",
            str(readiness_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid report readiness finding draft packet input" in result.output


def test_case_chat_report_readiness_finding_draft_packet_cli_invalid_json(tmp_path):
    readiness_file = tmp_path / "report-readiness.json"
    readiness_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-report-readiness-finding-draft-packet",
            "--report-readiness",
            str(readiness_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid export bundle report readiness JSON" in result.output
