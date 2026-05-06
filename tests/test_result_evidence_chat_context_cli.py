import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 1,
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
                "source": "manual-json-batch:001.json",
            }
        ],
        "weak_or_rejected_candidates": [],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "count": 1,
        "top_candidate": {
            "endpoint": "/api/high",
            "score": 120,
            "readiness": "needs-final-validation",
            "missing_evidence": [],
        },
        "candidates": [
            {
                "endpoint": "/api/high",
                "score": 120,
                "readiness": "needs-final-validation",
                "missing_evidence": [],
            }
        ],
    }


def _multi_agent():
    return {
        "kind": "result_evidence_multi_agent_review_plan",
        "count": 1,
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
        "title_candidates": [
            "Possible Cross-Account Authorization Boundary Issue on `/api/high`"
        ],
        "affected_endpoints": ["/api/high"],
    }


def test_case_chat_context_cli_writes_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"
    multi_agent_file = tmp_path / "multi-agent.json"
    report_file = tmp_path / "report-assistant.json"
    output_file = tmp_path / "strong-chat.json"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps(_ranking()))
    multi_agent_file.write_text(json.dumps(_multi_agent()))
    report_file.write_text(json.dumps(_report_assistant()))

    result = runner.invoke(
        app,
        [
            "case-chat-context",
            str(case_file),
            "--question",
            "what should the final report focus on?",
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
    assert "Strong Local Research Chat" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["intent"] == "final-report-focus"
    assert data["cited_endpoints"] == ["/api/high"]
    assert "priority-ranking" in data["included_artifacts"]
    assert "multi-agent-review" in data["included_artifacts"]
    assert "report-assistant" in data["included_artifacts"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_case_chat_context_cli_missing_case_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat-context",
            str(tmp_path / "missing.json"),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_chat_context_cli_invalid_case_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "case-chat-context",
            str(case_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output


def test_case_chat_context_cli_wrong_optional_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat-context",
            str(case_file),
            "--question",
            "what next?",
            "--ranking",
            str(ranking_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case chat context input" in result.output
