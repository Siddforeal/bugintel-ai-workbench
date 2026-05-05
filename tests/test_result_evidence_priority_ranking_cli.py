import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 3,
        "findings": [
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
            },
            {
                "endpoint": "/api/weak",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "priority": "low",
                "readiness": "likely-false-positive",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "confidence": "medium",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
                "source": "manual-json-batch:002.json",
            },
        ],
    }


def test_result_evidence_priority_ranking_cli_writes_markdown_and_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "ranking.md"
    json_output = tmp_path / "ranking.json"

    case_file.write_text(json.dumps(_case_summary()))

    result = runner.invoke(
        app,
        [
            "result-evidence-priority-ranking",
            str(case_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Priority Ranking" in result.output
    assert "Top candidate" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Result Evidence Priority Ranking" in markdown
    assert "\\n" not in markdown
    assert "/api/high" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_priority_ranking"
    assert data["count"] == 2
    assert data["top_candidate"]["endpoint"] == "/api/high"
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_priority_ranking_cli_can_exclude_weak(tmp_path):
    case_file = tmp_path / "case-summary.json"
    json_output = tmp_path / "ranking.json"

    case_file.write_text(json.dumps(_case_summary()))

    result = runner.invoke(
        app,
        [
            "result-evidence-priority-ranking",
            str(case_file),
            "--exclude-weak",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["count"] == 1
    assert data["candidates"][0]["endpoint"] == "/api/high"


def test_result_evidence_priority_ranking_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-priority-ranking", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_result_evidence_priority_ranking_cli_invalid_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-priority-ranking", str(case_file)])

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output


def test_result_evidence_priority_ranking_cli_wrong_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case-summary.json"
    case_file.write_text(json.dumps({"kind": "wrong", "findings": []}))

    result = runner.invoke(app, ["result-evidence-priority-ranking", str(case_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence priority ranking input" in result.output
