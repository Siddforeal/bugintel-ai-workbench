import json

import pytest

from bugintel.core.brain_state_export import (
    EXPECTED_BRAIN_STATE_FILES,
    build_brain_state_export,
)


def _write_json(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_build_brain_state_export_copies_expected_numbered_files(tmp_path):
    ai_brain = _write_json(
        tmp_path / "ai-brain.json",
        {
            "target_name": "demo.local",
            "focus_queue": [
                {
                    "endpoint": "/api/accounts/123/users/{id}/permissions",
                    "priority_band": "critical",
                    "priority_score": 80,
                }
            ],
        },
    )
    decision = _write_json(
        tmp_path / "brain-decision.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
            "decision": "blocked-pending-scope-and-controls",
        },
    )
    approval = _write_json(
        tmp_path / "brain-approval.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
            "approval_status": "blocked-pending-approval",
        },
    )
    gate = _write_json(
        tmp_path / "tool-execution-gate.json",
        {
            "target_name": "demo.local",
            "focus_endpoint": "/api/accounts/123/users/{id}/permissions",
            "gate_decision": "blocked-manifest-execution-disabled",
            "execution_allowed": False,
        },
    )

    output_dir = tmp_path / "brain"
    export = build_brain_state_export(
        ai_brain=ai_brain,
        brain_decision=decision,
        brain_approval=approval,
        tool_execution_gate=gate,
        output_dir=output_dir,
    )
    data = export.to_dict()

    assert data["kind"] == "brain_state_export"
    assert data["recommendation"] == "ready-for-brain-chat"
    assert data["safety"]["file_copy_only"] is True
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    for filename in EXPECTED_BRAIN_STATE_FILES.values():
        assert (output_dir / filename).exists()

    copied_ai = json.loads((output_dir / "03-ai-brain.json").read_text())
    assert copied_ai["target_name"] == "demo.local"


def test_brain_state_export_markdown_is_readable(tmp_path):
    ai_brain = _write_json(tmp_path / "ai.json", {"target_name": "demo"})
    decision = _write_json(tmp_path / "decision.json", {"target_name": "demo"})
    approval = _write_json(tmp_path / "approval.json", {"target_name": "demo"})
    gate = _write_json(tmp_path / "gate.json", {"target_name": "demo"})

    export = build_brain_state_export(
        ai_brain=ai_brain,
        brain_decision=decision,
        brain_approval=approval,
        tool_execution_gate=gate,
        output_dir=tmp_path / "brain",
    )
    markdown = export.to_markdown()

    assert "# Brain State Export" in markdown
    assert "03-ai-brain.json" in markdown
    assert "09-tool-execution-gate.json" in markdown
    assert "This command only prepares a local brain-chat state directory." in markdown
    assert "\\n" not in markdown


def test_brain_state_export_requires_existing_inputs(tmp_path):
    with pytest.raises(ValueError):
        build_brain_state_export(
            ai_brain=tmp_path / "missing-ai.json",
            brain_decision=tmp_path / "missing-decision.json",
            brain_approval=tmp_path / "missing-approval.json",
            tool_execution_gate=tmp_path / "missing-gate.json",
            output_dir=tmp_path / "brain",
        )


def test_brain_state_export_rejects_invalid_json(tmp_path):
    ai_brain = tmp_path / "ai.json"
    ai_brain.write_text("{not-json", encoding="utf-8")

    valid = _write_json(tmp_path / "valid.json", {})

    with pytest.raises(ValueError):
        build_brain_state_export(
            ai_brain=ai_brain,
            brain_decision=valid,
            brain_approval=valid,
            tool_execution_gate=valid,
            output_dir=tmp_path / "brain",
        )
