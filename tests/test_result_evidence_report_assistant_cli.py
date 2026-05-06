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
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
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
            "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
            "priority": "high",
            "readiness": "needs-final-validation",
            "evidence_strength": "strong-candidate",
            "severity_hint": "candidate-high-if-sensitive-data-confirmed",
            "confidence": "medium-high",
            "missing_evidence": [],
            "next_actions": ["Capture own-object baseline."],
            "source": "manual-json-batch:001.json",
        },
        "candidates": [
            {
                "endpoint": "/api/high",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
                "source": "manual-json-batch:001.json",
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


def test_case_report_assistant_cli_writes_markdown_and_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"
    multi_agent_file = tmp_path / "multi-agent.json"
    output_file = tmp_path / "report-assistant.md"
    json_output = tmp_path / "report-assistant.json"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps(_ranking()))
    multi_agent_file.write_text(json.dumps(_multi_agent()))

    result = runner.invoke(
        app,
        [
            "case-report-assistant",
            str(case_file),
            "--ranking",
            str(ranking_file),
            "--multi-agent-review",
            str(multi_agent_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Case-to-Report Assistant" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Case-to-Report Assistant Draft" in markdown
    assert "\\n" not in markdown
    assert "Candidate Title Options" in markdown
    assert "Proof-of-Concept Skeleton" in markdown
    assert "authz-reviewer" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_report_assistant"
    assert data["readiness"] == "needs-final-validation"
    assert data["affected_endpoints"] == ["/api/high"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_report_assistant_cli_case_only(tmp_path):
    case_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "report-assistant.md"

    case_file.write_text(json.dumps(_case_summary()))

    result = runner.invoke(
        app,
        [
            "case-report-assistant",
            str(case_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.exists()
    assert "No multi-agent review artifact was provided" in output_file.read_text()


def test_case_report_assistant_cli_missing_case_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["case-report-assistant", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_report_assistant_cli_invalid_case_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(app, ["case-report-assistant", str(case_file)])

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output


def test_case_report_assistant_cli_wrong_ranking_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-report-assistant",
            str(case_file),
            "--ranking",
            str(ranking_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case report assistant input" in result.output
