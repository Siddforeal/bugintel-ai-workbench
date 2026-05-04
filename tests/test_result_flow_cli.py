import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration


runner = CliRunner()


def _write_research_state(tmp_path):
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    state = build_research_state_from_orchestration(orchestration.to_dict()).to_dict()
    path = tmp_path / "research-state.json"
    path.write_text(json.dumps(state))
    return path


def test_result_flow_cli_writes_updated_state_and_result_json(tmp_path):
    state_file = _write_research_state(tmp_path)
    updated_state = tmp_path / "updated.json"
    result_file = tmp_path / "result-flow.json"

    result = runner.invoke(
        app,
        [
            "result-flow",
            "--research-state",
            str(state_file),
            "--endpoint",
            "/api/accounts/123/users/{id}/permissions",
            "--observed-status",
            "200",
            "--expected-status",
            "403",
            "--note",
            "Observed foreign account private data and permission bypass.",
            "--updated-state",
            str(updated_state),
            "--result-json",
            str(result_file),
        ],
    )

    assert result.exit_code == 0
    assert "Result Flow" in result.output
    assert "supported" in result.output
    assert updated_state.exists()
    assert result_file.exists()

    updated = json.loads(updated_state.read_text())
    flow = json.loads(result_file.read_text())

    assert updated["endpoints"][0]["triage_state"] == "report-candidate"
    assert flow["interpretation"]["suggested_result"] == "supported"
    assert flow["planning_only"] is True


def test_result_flow_cli_missing_state_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "result-flow",
            "--research-state",
            str(tmp_path / "missing.json"),
            "--endpoint",
            "/api/x",
            "--updated-state",
            str(tmp_path / "out.json"),
        ],
    )

    assert result.exit_code == 1
    assert "Research-state JSON not found" in result.output
