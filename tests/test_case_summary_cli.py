import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_case_summary_cli_writes_markdown_and_json(tmp_path):
    timeline_file = tmp_path / "case-timeline.json"
    output_file = tmp_path / "case-summary.md"
    json_output = tmp_path / "case-summary.json"

    timeline_file.write_text(json.dumps({
        "target_name": "demo",
        "events": [
            {"event_type": "orchestration"},
            {"event_type": "research-state"},
            {"event_type": "tool-execution-gate"},
        ],
    }))

    result = runner.invoke(
        app,
        [
            "case-summary",
            str(timeline_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Case Summary" in result.output
    assert "Key Points" in result.output
    assert "Recommended Next Steps" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["target_name"] == "demo"
    assert data["current_state"] == "execution-gated"
    assert data["planning_only"] is True


def test_case_summary_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["case-summary", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Case timeline JSON not found" in result.output


def test_case_summary_cli_invalid_json_exits_nonzero(tmp_path):
    timeline_file = tmp_path / "bad.json"
    timeline_file.write_text("{not json")

    result = runner.invoke(app, ["case-summary", str(timeline_file)])

    assert result.exit_code == 2
    assert "Invalid case timeline JSON" in result.output
