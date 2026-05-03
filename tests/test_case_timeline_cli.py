import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_case_timeline_cli_writes_markdown_and_json(tmp_path):
    (tmp_path / "01-orchestration.json").write_text(json.dumps({
        "target_name": "demo",
        "endpoints": ["/api/a", "/api/b"],
        "assignments": [{"agent": "x"}],
    }))
    (tmp_path / "06-brain-decision.json").write_text(json.dumps({
        "target_name": "demo",
        "decision": "blocked-pending-scope-and-controls",
        "reportable": False,
    }))

    output_file = tmp_path / "timeline.md"
    json_output = tmp_path / "timeline.json"

    result = runner.invoke(
        app,
        [
            "case-timeline",
            str(tmp_path),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Case Timeline" in result.output
    assert "Timeline Events" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["target_name"] == "demo"
    assert data["event_count"] == 2
    assert data["planning_only"] is True


def test_case_timeline_cli_missing_dir_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["case-timeline", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Case directory not found" in result.output
