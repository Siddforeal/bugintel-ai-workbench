import pytest

from bugintel.core.result_evidence_action_plan_apply_preview import (
    build_provider_suggestion_action_plan_apply_preview,
)


def _action_plan():
    return {
        "kind": "result_evidence_provider_suggestion_action_plan",
        "recommendation": "reject-unsafe-or-overclaimed-actions",
        "approved_actions": [
            {
                "action": "Validate own-object baseline.",
                "status": "supported-planning-action",
                "manual_order": 1,
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
            },
        ],
        "evidence_needed_actions": [
            {
                "action": "Check admin role behavior.",
                "status": "needs-local-evidence",
                "manual_order": 2,
                "reason": "Needs role-specific local evidence.",
                "evidence_needed": ["Admin account baseline"],
            },
        ],
        "rejected_actions": [
            {
                "action": "Run unsafe command.",
                "status": "unsafe-review-required",
                "manual_order": 3,
                "reason": "Unsafe wording.",
                "evidence_needed": ["Manual safety review"],
            },
        ],
        "missing_evidence": ["Impact proof"],
        "report_guardrails": ["Do not claim severity until supported by local evidence."],
        "planning_only": True,
        "execution_state": "not_executed",
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "missing_evidence": ["Random-object baseline"],
    }


def test_build_action_plan_apply_preview_splits_update_candidates():
    preview = build_provider_suggestion_action_plan_apply_preview(
        _action_plan(),
        case_memory=_case_memory(),
    )
    data = preview.to_dict()

    assert data["kind"] == "result_evidence_provider_suggestion_action_plan_apply_preview"
    assert data["recommendation"] == "preview-approved-updates-but-keep-blocked-items-unapplied"
    assert len(data["case_memory_updates"]) == 1
    assert len(data["research_state_updates"]) == 1
    assert len(data["blocked_updates"]) == 2
    assert data["case_memory_updates"][0]["preview_operation"] == "append_manual_next_action"
    assert data["research_state_updates"][0]["preview_operation"] == "append_planning_task"
    assert data["blocked_updates"][0]["target_artifact"] == "none"
    assert "Impact proof" in data["missing_evidence"]
    assert "Random-object baseline" in data["missing_evidence"]
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["case_memory_write"] is False
    assert data["safety"]["research_state_write"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_action_plan_apply_preview_markdown_is_readable():
    preview = build_provider_suggestion_action_plan_apply_preview(_action_plan())
    markdown = preview.to_markdown()

    assert "# Action Plan Apply Preview" in markdown
    assert "Case Memory Update Preview" in markdown
    assert "Research State Update Preview" in markdown
    assert "Blocked / Not Applied" in markdown
    assert "Do not write case memory from this command." in markdown
    assert "\\n" not in markdown


def test_action_plan_apply_preview_requires_action_plan_kind():
    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan_apply_preview({"kind": "wrong"})


def test_action_plan_apply_preview_requires_case_memory_kind():
    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan_apply_preview(
            _action_plan(),
            case_memory={"kind": "wrong"},
        )


def test_action_plan_apply_preview_requires_action_lists():
    bad = {
        "kind": "result_evidence_provider_suggestion_action_plan",
        "approved_actions": [],
        "evidence_needed_actions": [],
    }

    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan_apply_preview(bad)


def test_action_plan_apply_preview_rejects_approved_action_without_text():
    bad = {
        "kind": "result_evidence_provider_suggestion_action_plan",
        "approved_actions": [{"status": "supported-planning-action"}],
        "evidence_needed_actions": [],
        "rejected_actions": [],
    }

    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan_apply_preview(bad)
