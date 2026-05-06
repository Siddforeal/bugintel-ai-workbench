import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
            }
        ],
        "weak_or_rejected_candidates": [
            {
                "endpoint": "/api/weak",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
            }
        ],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "top_candidate": {"endpoint": "/api/high", "score": 120},
        "candidates": [{"endpoint": "/api/high"}, {"endpoint": "/api/weak"}],
    }


def test_case_memory_build_cli_writes_json_and_markdown(tmp_path):
    case_file = tmp_path / "case-summary.json"
    ranking_file = tmp_path / "ranking.json"
    output_file = tmp_path / "case-memory.json"
    markdown_file = tmp_path / "case-memory.md"

    case_file.write_text(json.dumps(_case_summary()))
    ranking_file.write_text(json.dumps(_ranking()))

    result = runner.invoke(
        app,
        [
            "case-memory-build",
            "--case-summary",
            str(case_file),
            "--ranking",
            str(ranking_file),
            "--output-file",
            str(output_file),
            "--markdown-output",
            str(markdown_file),
        ],
    )

    assert result.exit_code == 0
    assert "Multi-Artifact Case Memory" in result.output
    assert output_file.exists()
    assert markdown_file.exists()

    data = json.loads(output_file.read_text())
    assert data["kind"] == "result_evidence_case_memory"
    assert data["top_endpoint"] == "/api/high"
    assert "/api/high" in data["cited_endpoints"]
    assert "/api/weak" in data["cited_endpoints"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    markdown = markdown_file.read_text()
    assert "# Multi-Artifact Case Memory" in markdown
    assert "\\n" not in markdown


def test_case_memory_build_cli_requires_artifact(tmp_path):
    output_file = tmp_path / "case-memory.json"

    result = runner.invoke(
        app,
        [
            "case-memory-build",
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case memory input" in result.output


def test_case_memory_build_cli_missing_file_exits_nonzero(tmp_path):
    output_file = tmp_path / "case-memory.json"

    result = runner.invoke(
        app,
        [
            "case-memory-build",
            "--case-summary",
            str(tmp_path / "missing.json"),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_memory_build_cli_wrong_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "case-memory.json"

    case_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-memory-build",
            "--case-summary",
            str(case_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case memory input" in result.output
