import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _packet():
    return {
        "kind": "result_evidence_report_readiness_finding_draft_packet",
        "recommendation": "do-not-draft-remove-unsafe-items",
        "title_candidates": [
            {
                "text": "Title blocked until report-readiness blockers are resolved.",
                "category": "title-blocked",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "The readiness review still contains blockers.",
                "required_action": "Resolve blockers before choosing a report title.",
            }
        ],
        "evidence_checklist": [
            {
                "text": "evidence_gaps=1",
                "category": "open-evidence-gap-count",
                "status": "missing-evidence-required",
                "source": "packet_counts",
                "reason": "Bundle contains open evidence gaps.",
                "required_action": "Close evidence gaps.",
            }
        ],
        "reproduction_plan_placeholders": [
            {
                "text": "Reproduction plan blocked until all blockers are resolved.",
                "category": "reproduction-plan-placeholder",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "Readiness review contains blockers.",
                "required_action": "Resolve blockers before writing reproduction steps.",
            }
        ],
        "impact_wording_guardrails": [
            {
                "text": "Do not claim practical impact until local evidence demonstrates it.",
                "category": "impact-wording-guardrail",
                "status": "guardrail",
                "source": "report_guardrails",
                "reason": "Impact must be evidence-based.",
                "required_action": "Tie every impact sentence to local proof.",
            }
        ],
        "severity_wording_guardrails": [
            {
                "text": "Do not state High/Critical severity while blockers remain open.",
                "category": "severity-wording-guardrail",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "Open blockers prevent reliable severity wording.",
                "required_action": "Resolve blockers before writing severity.",
            }
        ],
        "blocked_claims": [
            {
                "text": "unsafe_or_rejected_items=1",
                "category": "unsafe-or-rejected-items-present",
                "status": "blocked-claim",
                "source": "packet_counts",
                "reason": "Bundle contains unsafe or rejected items.",
                "required_action": "Keep unsafe/rejected items blocked.",
            }
        ],
        "do_not_claim_yet": [
            {
                "text": "Do not claim the finding is confirmed until all blockers are resolved.",
                "category": "global-do-not-claim-yet",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "One or more readiness blockers remain open.",
                "required_action": "Resolve every blocker and re-run readiness review.",
            }
        ],
        "final_human_writing_checklist": ["Confirm no report was generated or submitted by Blackhole."],
        "safety": {
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
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


def test_case_chat_finding_draft_packet_review_gate_cli_writes_markdown_and_json(tmp_path):
    packet_file = tmp_path / "finding-draft-packet.json"
    output_file = tmp_path / "finding-draft-packet-review.md"
    json_output = tmp_path / "finding-draft-packet-review.json"

    packet_file.write_text(json.dumps(_packet()), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-finding-draft-packet-review-gate",
            "--finding-draft-packet",
            str(packet_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Finding Draft Packet Review Gate" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_finding_draft_packet_review_gate"
    assert data["recommendation"] == "do-not-use-for-report-writing-resolve-blocked-claims"
    assert len(data["blocked_claim_findings"]) == 1
    assert len(data["do_not_claim_findings"]) == 1
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_finding_draft_packet_review_gate_cli_missing_file(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-finding-draft-packet-review-gate",
            "--finding-draft-packet",
            str(tmp_path / "missing.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Finding draft packet JSON not found" in result.output


def test_case_chat_finding_draft_packet_review_gate_cli_wrong_kind(tmp_path):
    packet_file = tmp_path / "finding-draft-packet.json"
    packet_file.write_text(json.dumps({"kind": "wrong"}), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-finding-draft-packet-review-gate",
            "--finding-draft-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid finding draft packet review gate input" in result.output


def test_case_chat_finding_draft_packet_review_gate_cli_invalid_json(tmp_path):
    packet_file = tmp_path / "finding-draft-packet.json"
    packet_file.write_text("{not-json", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "case-chat-finding-draft-packet-review-gate",
            "--finding-draft-packet",
            str(packet_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid finding draft packet JSON" in result.output
