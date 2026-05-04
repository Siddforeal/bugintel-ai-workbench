import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_import_result_evidence_cli_writes_json(tmp_path):
    evidence_file = tmp_path / "evidence.json"
    output_file = tmp_path / "normalized.json"

    evidence_file.write_text(json.dumps({
        "endpoint": "/api/accounts/123/users/{id}/permissions",
        "observed_status": "200",
        "expected_status": 403,
        "note": "Observed foreign account private data.",
    }))

    result = runner.invoke(
        app,
        [
            "import-result-evidence",
            str(evidence_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Normalized Result Evidence" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["observed_status"] == 200
    assert data["expected_status"] == 403
    assert data["planning_only"] is True


def test_import_result_evidence_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["import-result-evidence", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Evidence JSON not found" in result.output


def test_import_result_evidence_cli_invalid_json_exits_nonzero(tmp_path):
    evidence_file = tmp_path / "bad.json"
    evidence_file.write_text("{not json")

    result = runner.invoke(app, ["import-result-evidence", str(evidence_file)])

    assert result.exit_code == 2
    assert "Invalid evidence JSON" in result.output


def test_import_result_evidence_cli_missing_endpoint_exits_nonzero(tmp_path):
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(json.dumps({"observed_status": 200}))

    result = runner.invoke(app, ["import-result-evidence", str(evidence_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence" in result.output
