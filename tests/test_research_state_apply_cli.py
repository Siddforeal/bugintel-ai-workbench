import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.research_state_update import build_research_state_update_plan


runner = CliRunner()


def _write_state_and_update(tmp_path):
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    state = build_research_state_from_orchestration(orchestration.to_dict()).to_dict()
    update = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        "supported",
        note="Validated with controlled accounts.",
    ).to_dict()

    state_file = tmp_path / "research-state.json"
    update_file = tmp_path / "update.json"
    state_file.write_text(json.dumps(state))
    update_file.write_text(json.dumps(update))
    return state_file, update_file


def test_research_state_apply_cli_writes_updated_state(tmp_path):
    state_file, update_file = _write_state_and_update(tmp_path)
    output_file = tmp_path / "research-state.updated.json"
    result_file = tmp_path / "apply-result.json"

    result = runner.invoke(
        app,
        [
            "research-state-apply",
            str(state_file),
            "--update-plan",
            str(update_file),
            "--output-file",
            str(output_file),
            "--result-json",
            str(result_file),
        ],
    )

    assert result.exit_code == 0
    assert "Research State Apply Result" in result.output
    assert "Applied Patches" in result.output
    assert output_file.exists()
    assert result_file.exists()

    updated = json.loads(output_file.read_text())
    result_data = json.loads(result_file.read_text())

    assert updated["endpoints"][0]["triage_state"] == "report-candidate"
    assert updated["endpoints"][0]["validation_note"] == "Validated with controlled accounts."
    assert result_data["planning_only"] is True


def test_research_state_apply_cli_missing_files_exit_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "research-state-apply",
            str(tmp_path / "missing-state.json"),
            "--update-plan",
            str(tmp_path / "missing-update.json"),
            "--output-file",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state JSON not found" in result.output


def test_research_state_apply_cli_invalid_json_exits_nonzero(tmp_path):
    state_file = tmp_path / "state.json"
    update_file = tmp_path / "update.json"
    state_file.write_text("{not json")
    update_file.write_text("{}")

    result = runner.invoke(
        app,
        [
            "research-state-apply",
            str(state_file),
            "--update-plan",
            str(update_file),
            "--output-file",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 2
    assert "Invalid JSON" in result.output
