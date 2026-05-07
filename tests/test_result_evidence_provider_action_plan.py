import pytest

from bugintel.core.result_evidence_provider_action_plan import build_provider_suggestion_action_plan


def _provider_review():
    return {
        "kind": "result_evidence_case_chat_provider_result_review",
        "recommendation": "use-as-planning-note-needs-evidence",
        "reviewed_actions": [
            {
                "action": "Validate own-object baseline.",
                "status": "supported-planning-action",
                "reason": "Action overlaps with local next-action evidence.",
            },
            {
                "action": "Check admin role behavior.",
                "status": "needs-local-evidence",
                "reason": "Action is not directly supported by local artifacts.",
            },
            {
                "action": "Run this command to dump data.",
                "status": "unsafe-review-required",
                "reason": "Action wording appears unsafe.",
            },
        ],
        "warning_flags": ["manual-command-review-needed"],
        "unsupported_claims": ["Provider output includes severity wording that must be proven."],
        "missing_evidence": ["Impact proof"],
        "untrusted_suggestion": True,
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "missing_evidence": ["Random-object baseline"],
    }


def test_build_provider_suggestion_action_plan_splits_actions():
    plan = build_provider_suggestion_action_plan(_provider_review(), case_memory=_case_memory())
    data = plan.to_dict()

    assert data["kind"] == "result_evidence_provider_suggestion_action_plan"
    assert data["recommendation"] == "reject-unsafe-or-overclaimed-actions"
    assert len(data["approved_actions"]) == 1
    assert len(data["evidence_needed_actions"]) == 1
    assert len(data["rejected_actions"]) == 1
    assert "Impact proof" in data["missing_evidence"]
    assert "Random-object baseline" in data["missing_evidence"]
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_provider_suggestion_action_plan_markdown_is_readable():
    plan = build_provider_suggestion_action_plan(_provider_review(), case_memory=_case_memory())
    markdown = plan.to_markdown()

    assert "# Provider Suggestion Action Plan" in markdown
    assert "Approved Planning Actions" in markdown
    assert "Actions Needing Local Evidence" in markdown
    assert "Rejected / Unsafe Actions" in markdown
    assert "Do not execute any action automatically." in markdown
    assert "\\n" not in markdown


def test_build_provider_suggestion_action_plan_requires_review_kind():
    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan({"kind": "wrong"})


def test_build_provider_suggestion_action_plan_requires_actions_list():
    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan(
            {
                "kind": "result_evidence_case_chat_provider_result_review",
            }
        )


def test_build_provider_suggestion_action_plan_rejects_action_without_text():
    with pytest.raises(ValueError):
        build_provider_suggestion_action_plan(
            {
                "kind": "result_evidence_case_chat_provider_result_review",
                "reviewed_actions": [{"status": "needs-local-evidence"}],
            }
        )
