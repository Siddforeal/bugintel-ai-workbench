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
                "endpoint": "/api/a",
                "suggested_result": "supported",
                "confidence": "medium-high",
                "source": "manual-json-batch:001.json",
                "observed_status": 200,
                "expected_status": 403,
                "signal_count": 5,
                "rationale": "Signals suggest support.",
            },
            {
                "endpoint": "/api/b",
                "suggested_result": "rejected",
                "confidence": "medium",
                "source": "manual-json-batch:002.json",
                "observed_status": 403,
                "expected_status": 403,
                "signal_count": 3,
                "rationale": "Expected blocking.",
            },
        ],
    }


def test_result_evidence_finding_package_cli_writes_package(tmp_path):
    review_file = tmp_path / "review.json"
    output_dir = tmp_path / "package"

    review_file.write_text(json.dumps(_review_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-finding-package",
            str(review_file),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Finding Package" in result.output
    assert (output_dir / "finding-draft.md").exists()
    assert (output_dir / "review-report.md").exists()
    assert (output_dir / "submission-checklist.md").exists()
    assert (output_dir / "metadata.json").exists()
    assert (output_dir / "manifest.json").exists()

    draft = (output_dir / "finding-draft.md").read_text()
    assert "### 1. `/api/a`" in draft
    assert "/api/b" not in draft

    metadata = json.loads((output_dir / "metadata.json").read_text())
    assert metadata["selected_item_count"] == 1
    assert metadata["selected_endpoints"] == ["/api/a"]
    assert metadata["safety"]["local_only"] is True
    assert metadata["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_finding_package_cli_include_all(tmp_path):
    review_file = tmp_path / "review.json"
    output_dir = tmp_path / "package"

    review_file.write_text(json.dumps(_review_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-finding-package",
            str(review_file),
            "--include-all",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    draft = (output_dir / "finding-draft.md").read_text()
    assert "### 1. `/api/a`" in draft
    assert "### 2. `/api/b`" in draft

    metadata = json.loads((output_dir / "metadata.json").read_text())
    assert metadata["selected_item_count"] == 2
    assert metadata["include_all"] is True


def test_result_evidence_finding_package_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "result-evidence-finding-package",
            str(tmp_path / "missing.json"),
            "--output-dir",
            str(tmp_path / "package"),
        ],
    )

    assert result.exit_code == 1
    assert "Result evidence batch review JSON not found" in result.output


def test_result_evidence_finding_package_cli_invalid_json_exits_nonzero(tmp_path):
    review_file = tmp_path / "bad.json"
    review_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "result-evidence-finding-package",
            str(review_file),
            "--output-dir",
            str(tmp_path / "package"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid result evidence batch review JSON" in result.output


def test_result_evidence_finding_package_cli_wrong_kind_exits_nonzero(tmp_path):
    review_file = tmp_path / "review.json"
    review_file.write_text(json.dumps({"kind": "wrong", "items": []}))

    result = runner.invoke(
        app,
        [
            "result-evidence-finding-package",
            str(review_file),
            "--output-dir",
            str(tmp_path / "package"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid result evidence finding package input" in result.output
