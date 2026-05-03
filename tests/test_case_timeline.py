import json

from bugintel.core.case_timeline import build_case_timeline, render_case_timeline_markdown


def test_build_case_timeline_from_known_artifacts(tmp_path):
    (tmp_path / "01-orchestration.json").write_text(json.dumps({
        "target_name": "demo",
        "endpoints": ["/api/a", "/api/b"],
        "assignments": [{"agent": "x"}],
    }))
    (tmp_path / "02-research-state.json").write_text(json.dumps({
        "target_name": "demo",
        "endpoint_count": 2,
        "decisions": [{"name": "scope"}],
    }))
    (tmp_path / "06-brain-decision.json").write_text(json.dumps({
        "target_name": "demo",
        "decision": "blocked-pending-scope-and-controls",
        "reportable": False,
    }))
    (tmp_path / "09-tool-execution-gate.json").write_text(json.dumps({
        "target_name": "demo",
        "gate_decision": "blocked-manifest-execution-disabled",
        "execution_allowed": False,
    }))

    timeline = build_case_timeline(tmp_path)
    data = timeline.to_dict()

    assert data["target_name"] == "demo"
    assert data["event_count"] == 4
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["events"][0]["event_type"] == "orchestration"
    assert data["events"][-1]["event_type"] == "tool-execution-gate"


def test_render_case_timeline_markdown(tmp_path):
    (tmp_path / "01-orchestration.json").write_text(json.dumps({
        "target_name": "demo",
        "endpoints": ["/api/a"],
        "assignments": [],
    }))

    timeline = build_case_timeline(tmp_path)
    markdown = render_case_timeline_markdown(timeline)

    assert "# Blackhole Case Timeline: demo" in markdown
    assert "orchestration" in markdown
    assert "Endpoints: 1" in markdown
    assert "No tools are executed" in markdown


def test_case_timeline_handles_empty_directory(tmp_path):
    timeline = build_case_timeline(tmp_path)
    data = timeline.to_dict()

    assert data["target_name"] == "unknown-target"
    assert data["event_count"] == 0
    assert data["events"] == []
