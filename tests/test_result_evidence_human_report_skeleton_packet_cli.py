import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _gate():
    return {
        "kind": "result_evidence_finding_draft_packet_review_gate",
        "recommendation": "do-not-use-for-report-writing-resolve-blocked-claims",
        "title_quality_findings": [
            {
                "subject": "Title blocked until report-readiness blockers are resolved.",
                "category": "title-quality",
                "severity": "high",
                "status": "title-blocked",
                "source": "title_candidates",
                "reason": "Title is blocked.",
                "required_action": "Resolve blockers before using this title.",
            }
        ],
        "evidence_checklist_findings": [],
        "reproduction_gap_findings": [],
        "wording_guardrail_findings": [],
        "blocked_claim_findings": [
            {
                "subject": "unsafe_or_rejected_items=1",
                "category": "unsafe-or-rejected-items-present",
                "severity": "info",
                "status": "blocked-claim-open",
                "source": "packet_counts",
                "reason": "Unsafe item remains open.",
                "required_action": "Keep unsafe item blocked.",
            }
        ],
        "do_not_claim_findings": [],
        "safety_findings": [],
        "approved_writing_support": [],
        "final_review_checklist": ["Confirm no report is generated or submitted by Blackhole."],
        "safety": {
            "report_generation": False,
            "report_submission": False,
            "vulnerability_confirmation": False,
        },
    }


def test_case_chat_human_report_skeleton_packet_cli_writes_markdown_and_json(tmp_path):
    gate_file = tmp_path / "finding-draft-review-gate.json"
    output_file = tmp_path / "human-report-skeleton.md"
    json_output = tmp_path / "human-report-skeleton.json"

    gate_file.write_text(json.dumps(_gate()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-packet",
            "--finding-draft-review-gate",
            str(gate_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Human Report Skeleton Packet" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_human_report_skeleton_packet"
    assert data["recommendation"] == "skeleton-built-but-report-writing-blocked"
    assert data["summary"]["status"] == "blocked-until-review-complete"
    assert data["blocked_claims_do_not_claim"]["status"] == "open-blockers"
    assert data["safety"]["final_report"] is False
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_human_report_skeleton_packet_cli_missing_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-packet",
            "--finding-draft-review-gate",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Finding draft packet review gate JSON not found" in result.output


def test_case_chat_human_report_skeleton_packet_cli_wrong_kind(tmp_path):
    gate_file = tmp_path / "finding-draft-review-gate.json"
    gate_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-packet",
            "--finding-draft-review-gate",
            str(gate_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid human report skeleton packet input" in result.output


def test_case_chat_human_report_skeleton_packet_cli_invalid_json(tmp_path):
    gate_file = tmp_path / "finding-draft-review-gate.json"
    gate_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-packet",
            "--finding-draft-review-gate",
            str(gate_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid finding draft packet review gate JSON" in result.output
