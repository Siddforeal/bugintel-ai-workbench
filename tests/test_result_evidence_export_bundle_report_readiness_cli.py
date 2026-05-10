import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _review_gate():
    return {
        "kind": "result_evidence_export_bundle_review_gate",
        "recommendation": "use-only-for-internal-review-block-high-risk-items",
        "artifact_integrity_findings": [],
        "missing_artifact_findings": [],
        "packet_risk_findings": [
            {
                "category": "unsafe-or-rejected-items-present",
                "severity": "high",
                "message": "Bundle contains unsafe or rejected items.",
                "subject": "unsafe_or_rejected_items=1",
                "source": "packet_counts",
                "required_action": "Keep unsafe/rejected items blocked.",
            }
        ],
        "evidence_gap_findings": [
            {
                "category": "open-evidence-gap-count",
                "severity": "medium",
                "message": "Bundle contains open evidence gaps.",
                "subject": "evidence_gaps=1",
                "source": "packet_counts",
                "required_action": "Close evidence gaps.",
            }
        ],
        "overclaim_findings": [],
        "safety_findings": [],
        "approved_review_notes": [
            {
                "category": "approved-review-package-note",
                "severity": "info",
                "message": "Bundle contains approved planning notes.",
                "subject": "approved_planning_updates=1",
                "source": "packet_counts",
                "required_action": "Use these as review notes only.",
            }
        ],
        "report_guardrails": ["Do not use bundle artifacts as vulnerability proof without local validation."],
        "human_review_checklist": ["Confirm every included artifact exists and has an integrity hash."],
    }


def test_case_chat_export_bundle_report_readiness_review_cli_writes_markdown_and_json(tmp_path):
    gate_file = tmp_path / "review-gate.json"
    output_file = tmp_path / "report-readiness.md"
    json_output = tmp_path / "report-readiness.json"

    gate_file.write_text(json.dumps(_review_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-report-readiness-review",
            "--review-gate",
            str(gate_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Export Bundle Report Readiness Review" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_export_bundle_report_readiness_review"
    assert data["recommendation"] == "not-report-ready-remove-unsafe-items"
    assert len(data["unsafe_or_rejected_items"]) == 1
    assert len(data["missing_evidence"]) == 1
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_export_bundle_report_readiness_review_cli_missing_gate_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-report-readiness-review",
            "--review-gate",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Export bundle review gate JSON not found" in result.output


def test_case_chat_export_bundle_report_readiness_review_cli_wrong_gate_kind(tmp_path):
    gate_file = tmp_path / "review-gate.json"
    gate_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-report-readiness-review",
            "--review-gate",
            str(gate_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid export bundle report readiness input" in result.output


def test_case_chat_export_bundle_report_readiness_review_cli_invalid_json(tmp_path):
    gate_file = tmp_path / "review-gate.json"
    gate_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-export-bundle-report-readiness-review",
            "--review-gate",
            str(gate_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid export bundle review gate JSON" in result.output
