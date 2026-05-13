import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _section(
    name,
    status="human-write-required",
    placeholder="[Human writes from verified evidence only.]",
    source_items=None,
    guidance=None,
):
    return {
        "name": name,
        "status": status,
        "purpose": f"{name} section purpose.",
        "placeholder": placeholder,
        "guidance": guidance or ["Use local evidence only."],
        "source_items": source_items or [],
    }


def _skeleton():
    return {
        "kind": "result_evidence_human_report_skeleton_packet",
        "recommendation": "skeleton-built-but-report-writing-blocked",
        "summary": _section(
            "Summary",
            status="blocked-until-review-complete",
            source_items=["Title blocked until report-readiness blockers are resolved."],
        ),
        "impact": _section(
            "Impact",
            status="blocked-until-impact-evidence",
            guidance=["Do not claim practical impact without local evidence."],
            source_items=["unsafe_or_rejected_items=1"],
        ),
        "steps_to_reproduce": _section("Steps to Reproduce"),
        "evidence": _section("Evidence", source_items=["evidence_gaps=1"]),
        "affected_assets": _section("Affected Assets"),
        "severity_rationale": _section(
            "Severity Rationale",
            status="blocked-until-severity-evidence",
            guidance=["Do not state High/Critical unless evidence supports it."],
        ),
        "remediation": _section("Remediation"),
        "blocked_claims_do_not_claim": _section(
            "Blocked Claims / Do Not Claim",
            status="open-blockers",
            source_items=["Do not claim the finding is confirmed until all blockers are resolved."],
        ),
        "human_final_writing_checklist": [
            "Confirm this packet is a skeleton only, not a final report."
        ],
        "safety": {
            "local_only": True,
            "planning_only": True,
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
            "final_report": False,
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


def test_case_chat_human_report_skeleton_review_gate_cli_writes_markdown_and_json(tmp_path):
    skeleton_file = tmp_path / "human-report-skeleton.json"
    output_file = tmp_path / "human-report-skeleton-review.md"
    json_output = tmp_path / "human-report-skeleton-review.json"

    skeleton_file.write_text(json.dumps(_skeleton()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-review-gate",
            "--human-report-skeleton",
            str(skeleton_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Human Report Skeleton Review Gate" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_human_report_skeleton_review_gate"
    assert data["recommendation"] == "do-not-use-skeleton-resolve-blockers"
    assert len(data["blocker_leakage_findings"]) >= 1
    assert len(data["blocked_do_not_claim_findings"]) >= 1
    assert data["safety"]["final_report"] is False
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_human_report_skeleton_review_gate_cli_missing_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-review-gate",
            "--human-report-skeleton",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Human report skeleton packet JSON not found" in result.output


def test_case_chat_human_report_skeleton_review_gate_cli_wrong_kind(tmp_path):
    skeleton_file = tmp_path / "human-report-skeleton.json"
    skeleton_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-review-gate",
            "--human-report-skeleton",
            str(skeleton_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid human report skeleton review gate input" in result.output


def test_case_chat_human_report_skeleton_review_gate_cli_invalid_json(tmp_path):
    skeleton_file = tmp_path / "human-report-skeleton.json"
    skeleton_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-human-report-skeleton-review-gate",
            "--human-report-skeleton",
            str(skeleton_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid human report skeleton packet JSON" in result.output
