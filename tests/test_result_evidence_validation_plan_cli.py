import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _hypothesis_json():
    return {
        "kind": "result_evidence_hypothesis_set",
        "count": 2,
        "hypotheses": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "confidence": "medium-high",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "source": "manual-json-batch:001.json",
            },
            {
                "endpoint": "/api/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "confidence": "medium",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "source": "manual-json-batch:002.json",
            },
        ],
    }


def test_result_evidence_validation_plan_cli_writes_markdown_and_json(tmp_path):
    hypothesis_file = tmp_path / "hypotheses.json"
    output_file = tmp_path / "validation-plan.md"
    json_output = tmp_path / "validation-plan.json"

    hypothesis_file.write_text(json.dumps(_hypothesis_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-validation-plan",
            str(hypothesis_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Validation Plan" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Manual Validation Plan" in markdown
    assert "\\n" not in markdown
    assert "Manual Steps" in markdown
    assert "Report Readiness Checks" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_validation_plan"
    assert data["count"] == 2
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_validation_plan_cli_high_priority_only(tmp_path):
    hypothesis_file = tmp_path / "hypotheses.json"
    json_output = tmp_path / "validation-plan.json"

    hypothesis_file.write_text(json.dumps(_hypothesis_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-validation-plan",
            str(hypothesis_file),
            "--high-priority-only",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    data = json.loads(json_output.read_text())
    assert data["count"] == 1
    assert data["plans"][0]["endpoint"] == "/api/accounts/123/users/999"


def test_result_evidence_validation_plan_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-validation-plan", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Result evidence hypothesis JSON not found" in result.output


def test_result_evidence_validation_plan_cli_invalid_json_exits_nonzero(tmp_path):
    hypothesis_file = tmp_path / "bad.json"
    hypothesis_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-validation-plan", str(hypothesis_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence hypothesis JSON" in result.output


def test_result_evidence_validation_plan_cli_wrong_kind_exits_nonzero(tmp_path):
    hypothesis_file = tmp_path / "hypotheses.json"
    hypothesis_file.write_text(json.dumps({"kind": "wrong", "hypotheses": []}))

    result = runner.invoke(app, ["result-evidence-validation-plan", str(hypothesis_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence validation plan input" in result.output
