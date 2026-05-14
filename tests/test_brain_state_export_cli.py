import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_brain_state_export_cli_writes_expected_files_and_outputs(tmp_path):
    ai = _write_json(
        tmp_path / "ai-brain.json",
        {
            "target_name": "demo.local",
            "focus_queue": [{"endpoint": "/api/accounts/123/users/{id}/permissions"}],
        },
    )
    decision = _write_json(
        tmp_path / "brain-decision.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
        },
    )
    approval = _write_json(
        tmp_path / "brain-approval.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
        },
    )
    gate = _write_json(
        tmp_path / "tool-execution-gate.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
            "execution_allowed": False,
        },
    )

    output_dir = tmp_path / "brain"
    output_file = tmp_path / "brain-export.md"
    json_output = tmp_path / "brain-export.json"

    result = runner.invoke(
        app,
        [
            "brain-state-export",
            "--ai-brain",
            str(ai),
            "--brain-decision",
            str(decision),
            "--brain-approval",
            str(approval),
            "--tool-execution-gate",
            str(gate),
            "--output-dir",
            str(output_dir),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Brain State Export" in result.output
    assert (output_dir / "03-ai-brain.json").exists()
    assert (output_dir / "06-brain-decision.json").exists()
    assert (output_dir / "07-brain-approval.json").exists()
    assert (output_dir / "09-tool-execution-gate.json").exists()
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["kind"] == "brain_state_export"
    assert data["recommendation"] == "ready-for-brain-chat"
    assert data["safety"]["file_copy_only"] is True
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_brain_state_export_cli_missing_file_returns_error(tmp_path):
    valid = _write_json(tmp_path / "valid.json", {})

    result = runner.invoke(
        app,
        [
            "brain-state-export",
            "--ai-brain",
            str(tmp_path / "missing.json"),
            "--brain-decision",
            str(valid),
            "--brain-approval",
            str(valid),
            "--tool-execution-gate",
            str(valid),
            "--output-dir",
            str(tmp_path / "brain"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid brain state export input" in result.output


def test_brain_state_export_cli_invalid_json_returns_error(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")
    valid = _write_json(tmp_path / "valid.json", {})

    result = runner.invoke(
        app,
        [
            "brain-state-export",
            "--ai-brain",
            str(invalid),
            "--brain-decision",
            str(valid),
            "--brain-approval",
            str(valid),
            "--tool-execution-gate",
            str(valid),
            "--output-dir",
            str(tmp_path / "brain"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid brain state export input" in result.output
