from bugintel.core.case_summary import build_case_summary, render_case_summary_markdown


def test_case_summary_from_execution_gated_timeline():
    timeline = {
        "target_name": "demo",
        "events": [
            {"event_type": "orchestration"},
            {"event_type": "research-state"},
            {"event_type": "ai-brain"},
            {"event_type": "brain-review"},
            {"event_type": "brain-decision"},
            {"event_type": "brain-approval"},
            {"event_type": "tool-request-manifest"},
            {"event_type": "tool-execution-gate"},
        ],
    }

    summary = build_case_summary(timeline)
    data = summary.to_dict()

    assert data["target_name"] == "demo"
    assert data["event_count"] == 8
    assert data["current_state"] == "execution-gated"
    assert data["planning_only"] is True
    assert any("execution gate" in point.lower() for point in data["key_points"])
    assert any("execution disabled" in step.lower() for step in data["recommended_next_steps"])


def test_case_summary_from_empty_timeline():
    summary = build_case_summary({"target_name": "empty", "events": []})
    data = summary.to_dict()

    assert data["target_name"] == "empty"
    assert data["event_count"] == 0
    assert data["current_state"] == "empty"
    assert "No Blackhole case artifacts were present." in data["key_points"]


def test_render_case_summary_markdown():
    summary = build_case_summary({
        "target_name": "demo",
        "events": [{"event_type": "brain-decision"}],
    })
    markdown = render_case_summary_markdown(summary)

    assert "# Blackhole Case Summary: demo" in markdown
    assert "decision-gated" in markdown
    assert "Recommended Next Steps" in markdown
    assert "No tools are executed" in markdown
