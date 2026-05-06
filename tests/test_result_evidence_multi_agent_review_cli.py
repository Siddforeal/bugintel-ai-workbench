import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "count": 2,
        "candidates": [
            {
                "rank": 1,
                "endpoint": "/api/high",
                "score": 120,
                "priority": "high",
                "readiness": "needs-final-validation",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "reason": "priority=high",
                "source": "manual-json-batch:001.json",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
            },
            {
                "rank": 2,
                "endpoint": "/api/weak",
                "score": -80,
                "priority": "low",
                "readiness": "likely-false-positive",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "confidence": "medium",
                "reason": "likely_false_positive_penalty",
                "source": "manual-json-batch:002.json",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
            },
        ],
    }


def test_result_evidence_multi_agent_review_cli_writes_markdown_and_json(tmp_path):
    ranking_file = tmp_path / "ranking.json"
    output_file = tmp_path / "multi-agent-review.md"
    json_output = tmp_path / "multi-agent-review.json"

    ranking_file.write_text(json.dumps(_ranking()))

    result = runner.invoke(
        app,
        [
            "result-evidence-multi-agent-review",
            str(ranking_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Multi-Agent Review" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Multi-Agent Review Plan" in markdown
    assert "\\n" not in markdown
    assert "authz-reviewer" in markdown
    assert "report-reviewer" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_multi_agent_review_plan"
    assert data["count"] == 2
    assert data["total_agent_tasks"] == 10
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_multi_agent_review_cli_can_exclude_low_priority(tmp_path):
    ranking_file = tmp_path / "ranking.json"
    json_output = tmp_path / "multi-agent-review.json"

    ranking_file.write_text(json.dumps(_ranking()))

    result = runner.invoke(
        app,
        [
            "result-evidence-multi-agent-review",
            str(ranking_file),
            "--exclude-low-priority",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["count"] == 1
    assert data["plans"][0]["endpoint"] == "/api/high"


def test_result_evidence_multi_agent_review_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-multi-agent-review", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Priority ranking JSON not found" in result.output


def test_result_evidence_multi_agent_review_cli_invalid_json_exits_nonzero(tmp_path):
    ranking_file = tmp_path / "bad.json"
    ranking_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-multi-agent-review", str(ranking_file)])

    assert result.exit_code == 2
    assert "Invalid priority ranking JSON" in result.output


def test_result_evidence_multi_agent_review_cli_wrong_kind_exits_nonzero(tmp_path):
    ranking_file = tmp_path / "ranking.json"
    ranking_file.write_text(json.dumps({"kind": "wrong", "candidates": []}))

    result = runner.invoke(app, ["result-evidence-multi-agent-review", str(ranking_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence multi-agent review input" in result.output
