import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_result_evidence_review_report_cli_writes_markdown_and_json(tmp_path):
    review_file = tmp_path / "review.json"
    output_file = tmp_path / "review.md"
    json_output = tmp_path / "report.json"

    review_file.write_text(json.dumps({
        "kind": "result_evidence_batch_review",
        "count": 1,
        "supported_count": 1,
        "rejected_count": 0,
        "needs_more_evidence_count": 0,
        "missing_expected_status_count": 0,
        "items": [
            {
                "endpoint": "/api/a",
                "suggested_result": "supported",
                "confidence": "medium-high",
                "source": "manual-json-batch:001.json",
                "observed_status": 200,
                "expected_status": 403,
                "signal_count": 5,
                "rationale": "Signals suggest support.",
            }
        ],
    }))

    result = runner.invoke(
        app,
        [
            "result-evidence-review-report",
            str(review_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Review Report" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Result Evidence Batch Review Report" in markdown
    assert "### 1. `/api/a`" in markdown
    assert "Suggested result: **supported**" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_review_report"
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True


def test_result_evidence_review_report_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-review-report", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Result evidence batch review JSON not found" in result.output


def test_result_evidence_review_report_cli_invalid_json_exits_nonzero(tmp_path):
    review_file = tmp_path / "bad.json"
    review_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-review-report", str(review_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch review JSON" in result.output


def test_result_evidence_review_report_cli_wrong_kind_exits_nonzero(tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({"kind": "wrong", "items": []}))

    result = runner.invoke(app, ["result-evidence-review-report", str(review_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch review report input" in result.output
