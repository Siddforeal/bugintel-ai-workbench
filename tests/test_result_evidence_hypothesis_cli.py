import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _review_json():
    return {
        "kind": "result_evidence_batch_review",
        "count": 2,
        "supported_count": 1,
        "rejected_count": 1,
        "needs_more_evidence_count": 0,
        "missing_expected_status_count": 0,
        "items": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "suggested_result": "supported",
                "confidence": "medium-high",
                "source": "manual-json-batch:001.json",
                "observed_status": 200,
                "expected_status": 403,
                "signal_count": 5,
                "rationale": "Observed foreign account private data and permission bypass.",
            },
            {
                "endpoint": "/api/accounts/123/users/random",
                "suggested_result": "rejected",
                "confidence": "medium",
                "source": "manual-json-batch:002.json",
                "observed_status": 403,
                "expected_status": 403,
                "signal_count": 3,
                "rationale": "Forbidden expected behavior.",
            },
        ],
    }


def test_result_evidence_hypothesis_cli_writes_markdown_and_json(tmp_path):
    review_file = tmp_path / "review.json"
    output_file = tmp_path / "hypotheses.md"
    json_output = tmp_path / "hypotheses.json"

    review_file.write_text(json.dumps(_review_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-hypothesis",
            str(review_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Hypotheses" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Result Evidence Hypotheses" in markdown
    assert "object-or-tenant-authorization-boundary-candidate" in markdown
    assert "\\n" not in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_hypothesis_set"
    assert data["count"] == 2
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_hypothesis_cli_supported_only(tmp_path):
    review_file = tmp_path / "review.json"
    json_output = tmp_path / "hypotheses.json"

    review_file.write_text(json.dumps(_review_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-hypothesis",
            str(review_file),
            "--supported-only",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["count"] == 1
    assert data["hypotheses"][0]["endpoint"] == "/api/accounts/123/users/999"


def test_result_evidence_hypothesis_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-hypothesis", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Result evidence batch review JSON not found" in result.output


def test_result_evidence_hypothesis_cli_invalid_json_exits_nonzero(tmp_path):
    review_file = tmp_path / "bad.json"
    review_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-hypothesis", str(review_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch review JSON" in result.output


def test_result_evidence_hypothesis_cli_wrong_kind_exits_nonzero(tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({"kind": "wrong", "items": []}))

    result = runner.invoke(app, ["result-evidence-hypothesis", str(review_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence hypothesis input" in result.output
