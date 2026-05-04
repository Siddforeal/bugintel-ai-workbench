import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.result_interpreter import interpret_validation_result


runner = CliRunner()


def _write_state_and_interpretation(tmp_path):
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    state = build_research_state_from_orchestration(orchestration.to_dict()).to_dict()
    interpretation = interpret_validation_result(
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=200,
        expected_status=403,
        note="Observed foreign account private data and permission bypass.",
    ).to_dict()

    state_file = tmp_path / "research-state.json"
    interpretation_file = tmp_path / "interpretation.json"
    state_file.write_text(json.dumps(state))
    interpretation_file.write_text(json.dumps(interpretation))
    return state_file, interpretation_file


def test_result_to_state_update_cli_writes_outputs(tmp_path):
    state_file, interpretation_file = _write_state_and_interpretation(tmp_path)
    output_file = tmp_path / "update.md"
    json_output = tmp_path / "update.json"

    result = runner.invoke(
        app,
        [
            "result-to-state-update",
            "--research-state",
            str(state_file),
            "--interpretation",
            str(interpretation_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result to State Update" in result.output
    assert output_file.exists()
    assert json_output.exists()

    data = json.loads(json_output.read_text())
    assert data["validation_result"] == "supported"
    assert any(action["new_value"] == "report-candidate" for action in data["actions"])


def test_result_to_state_update_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "result-to-state-update",
            "--research-state",
            str(tmp_path / "missing-state.json"),
            "--interpretation",
            str(tmp_path / "missing-interpretation.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state JSON not found" in result.output
