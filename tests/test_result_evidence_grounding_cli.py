import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "readiness": "needs-final-validation",
                "priority": "high",
                "missing_evidence": [],
                "next_actions": ["Validate baselines."],
            }
        ],
        "weak_or_rejected_candidates": [],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "top_candidate": {
            "endpoint": "/api/high",
            "score": 120,
            "readiness": "needs-final-validation",
        },
        "candidates": [],
    }


def _multi_agent():
    return {
        "kind": "result_evidence_multi_agent_review_plan",
        "plans": [
            {
                "endpoint": "/api/high",
                "agents": [
                    {
                        "agent": "authz-reviewer",
                        "risk_flags": ["possible-object-or-tenant-boundary-issue"],
                    }
                ],
            }
        ],
    }


def _report_assistant():
    return {
        "kind": "result_evidence_report_assistant",
        "readiness": "needs-final-validation",
        "title_candidates": ["Possible Authorization Issue on `/api/high`"],
        "affected_endpoints": ["/api/high"],
    }


def test_case_chat_grounded_cli_writes_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"
    multi_agent_file = tmp_path / "multi-agent.json"
    report_file = tmp_path / "report.json"
    output_file = tmp_path / "grounded.json"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps(_ranking()))
    multi_agent_file.write_text(json.dumps(_multi_agent()))
    report_file.write_text(json.dumps(_report_assistant()))

    result = runner.invoke(
        app,
        [
            "case-chat-grounded",
            str(case_file),
            "--question",
            "can I submit this?",
            "--ranking",
            str(ranking_file),
            "--multi-agent-review",
            str(multi_agent_file),
            "--report-assistant",
            str(report_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Grounded Local Research Chat" in result.output
    assert "Grounding" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["kind"] == "result_evidence_grounded_answer"
    assert data["intent"] == "report-ready"
    assert data["cited_endpoints"] == ["/api/high"]
    assert data["grounding"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_grounded_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["case-chat-grounded", str(tmp_path / "missing.json"), "--question", "what now?"])

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_chat_grounded_cli_invalid_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(app, ["case-chat-grounded", str(case_file), "--question", "what now?"])

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output
