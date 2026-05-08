import pytest

from bugintel.core.result_evidence_action_plan_apply_preview_review import (
    build_action_plan_apply_preview_review,
)


def _apply_preview():
    return {
        "kind": "result_evidence_provider_suggestion_action_plan_apply_preview",
        "recommendation": "preview-approved-updates-but-keep-blocked-items-unapplied",
        "case_memory_updates": [
            {
                "action": "Validate own-object baseline.",
                "preview_operation": "append_manual_next_action",
                "target_artifact": "case_memory",
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            },
            {
                "action": "Validate own-object baseline.",
                "preview_operation": "append_manual_next_action",
                "target_artifact": "case_memory",
                "reason": "Duplicate candidate.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            },
        ],
        "research_state_updates": [
            {
                "action": "Validate own-object baseline.",
                "preview_operation": "append_planning_task",
                "target_artifact": "research_state",
                "reason": "Action overlaps with local evidence.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            },
        ],
        "blocked_updates": [
            {
                "action": "Check admin role behavior.",
                "preview_operation": "block_until_local_evidence_exists",
                "target_artifact": "none",
                "reason": "Needs role-specific local evidence.",
                "evidence_needed": ["Admin account baseline"],
                "source_status": "needs-local-evidence",
            },
            {
                "action": "Run unsafe command.",
                "preview_operation": "block_rejected_or_unsafe_action",
                "target_artifact": "none",
                "reason": "Unsafe wording.",
                "evidence_needed": ["Manual safety review"],
                "source_status": "unsafe-review-required",
            },
        ],
        "missing_evidence": ["Impact proof"],
        "report_guardrails": ["Do not claim severity until supported by local evidence."],
        "safety": {
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "vulnerability_confirmation": False,
        },
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "manual_next_actions": ["Validate own-object baseline."],
        "missing_evidence": ["Random-object baseline"],
    }


def test_build_action_plan_apply_preview_review_flags_risks():
    review = build_action_plan_apply_preview_review(
        _apply_preview(),
        case_memory=_case_memory(),
    )
    data = review.to_dict()

    assert data["kind"] == "result_evidence_action_plan_apply_preview_review"
    assert data["recommendation"] == "do-not-apply-review-unsafe-items"
    assert len(data["duplicate_update_candidates"]) >= 2
    assert len(data["blocked_action_findings"]) == 2
    assert len(data["unsafe_update_findings"]) == 1
    assert data["unsafe_update_findings"][0]["action"] == "Run unsafe command."
    assert "Impact proof" in str(data["evidence_gap_findings"])
    assert "Random-object baseline" in str(data["evidence_gap_findings"])
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["case_memory_write"] is False
    assert data["safety"]["research_state_write"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_action_plan_apply_preview_review_markdown_is_readable():
    review = build_action_plan_apply_preview_review(_apply_preview(), case_memory=_case_memory())
    markdown = review.to_markdown()

    assert "# Action Plan Apply Preview Review" in markdown
    assert "Duplicate Update Candidates" in markdown
    assert "Blocked Actions" in markdown
    assert "Evidence Gaps" in markdown
    assert "Report Overclaim Risks" in markdown
    assert "Do not write case memory from this review." in markdown
    assert "\\n" not in markdown


def test_action_plan_apply_preview_review_clean_preview_allows_planning_note():
    clean = {
        "kind": "result_evidence_provider_suggestion_action_plan_apply_preview",
        "case_memory_updates": [
            {
                "action": "Add manual baseline validation note.",
                "preview_operation": "append_manual_next_action",
                "target_artifact": "case_memory",
                "reason": "Safe planning note.",
                "evidence_needed": [],
                "source_status": "supported-planning-action",
            },
        ],
        "research_state_updates": [],
        "blocked_updates": [],
        "missing_evidence": [],
        "report_guardrails": [],
        "safety": {
            "vulnerability_confirmation": False,
        },
    }

    review = build_action_plan_apply_preview_review(clean)
    data = review.to_dict()

    assert data["recommendation"] == "safe-to-use-as-planning-note"
    assert len(data["safe_planning_notes"]) == 1
    assert data["blocked_action_findings"] == []
    assert data["unsafe_update_findings"] == []


def test_action_plan_apply_preview_review_requires_preview_kind():
    with pytest.raises(ValueError):
        build_action_plan_apply_preview_review({"kind": "wrong"})


def test_action_plan_apply_preview_review_requires_case_memory_kind():
    with pytest.raises(ValueError):
        build_action_plan_apply_preview_review(
            _apply_preview(),
            case_memory={"kind": "wrong"},
        )


def test_action_plan_apply_preview_review_requires_candidate_lists():
    bad = {
        "kind": "result_evidence_provider_suggestion_action_plan_apply_preview",
        "case_memory_updates": [],
        "research_state_updates": [],
    }

    with pytest.raises(ValueError):
        build_action_plan_apply_preview_review(bad)
