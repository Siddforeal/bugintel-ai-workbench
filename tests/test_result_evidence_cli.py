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


def test_import_result_evidence_batch_cli_writes_json(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    output_file = tmp_path / "batch.json"

    (evidence_dir / "001.json").write_text(json.dumps({
        "endpoint": "/api/a",
        "observed_status": "200",
        "expected_status": 403,
    }))
    (evidence_dir / "002.json").write_text(json.dumps({
        "url": "/api/b",
        "status_code": 404,
        "note": "same as random",
    }))

    result = runner.invoke(
        app,
        [
            "import-result-evidence-batch",
            str(evidence_dir),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Normalized Result Evidence Batch" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["kind"] == "result_evidence_batch"
    assert data["count"] == 2
    assert data["evidence"][0]["endpoint"] == "/api/a"
    assert data["evidence"][0]["observed_status"] == 200
    assert data["evidence"][1]["endpoint"] == "/api/b"
    assert data["evidence"][1]["observed_status"] == 404
    assert data["safety"]["local_only"] is True
    assert data["safety"]["network_interaction"] is False


def test_import_result_evidence_batch_cli_missing_directory_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["import-result-evidence-batch", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Evidence directory not found" in result.output


def test_import_result_evidence_batch_cli_invalid_json_exits_nonzero(tmp_path):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / "bad.json").write_text("{not json")

    result = runner.invoke(app, ["import-result-evidence-batch", str(evidence_dir)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch" in result.output


def test_review_result_evidence_batch_cli_writes_json(tmp_path):
    batch_file = tmp_path / "batch.json"
    output_file = tmp_path / "review.json"

    batch_file.write_text(json.dumps({
        "kind": "result_evidence_batch",
        "evidence": [
            {
                "endpoint": "/api/a",
                "observed_status": 200,
                "expected_status": 403,
                "note": "Observed foreign account private data and permission bypass.",
            },
            {
                "endpoint": "/api/b",
                "observed_status": 403,
                "expected_status": 403,
                "note": "Forbidden expected behavior.",
            },
        ],
    }))

    result = runner.invoke(
        app,
        [
            "review-result-evidence-batch",
            str(batch_file),
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Batch Review" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["kind"] == "result_evidence_batch_review"
    assert data["count"] == 2
    assert data["supported_count"] == 1
    assert data["rejected_count"] == 1
    assert data["safety"]["local_only"] is True
    assert data["safety"]["network_interaction"] is False


def test_review_result_evidence_batch_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["review-result-evidence-batch", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Result evidence batch JSON not found" in result.output


def test_review_result_evidence_batch_cli_invalid_json_exits_nonzero(tmp_path):
    batch_file = tmp_path / "bad.json"
    batch_file.write_text("{not json")

    result = runner.invoke(app, ["review-result-evidence-batch", str(batch_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch JSON" in result.output


def test_review_result_evidence_batch_cli_missing_evidence_exits_nonzero(tmp_path):
    batch_file = tmp_path / "batch.json"
    batch_file.write_text(json.dumps({"kind": "result_evidence_batch"}))

    result = runner.invoke(app, ["review-result-evidence-batch", str(batch_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence batch review input" in result.output
