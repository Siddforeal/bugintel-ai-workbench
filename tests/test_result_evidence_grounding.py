import pytest

from bugintel.core.result_evidence_grounding import build_grounded_answer


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "readiness": "needs-final-validation",
                "priority": "high",
            }
        ],
        "weak_or_rejected_candidates": [
            {
                "endpoint": "/api/weak",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
            }
        ],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "top_candidate": {
            "endpoint": "/api/high",
            "score": 120,
            "readiness": "needs-final-validation",
        },
    }


def _multi_agent():
    return {
        "kind": "result_evidence_multi_agent_review_plan",
        "plans": [
            {
                "endpoint": "/api/high",
                "agents": [
                    {
                        "agent": "authz-reviewer",
                        "risk_flags": ["possible-object-or-tenant-boundary-issue"],
                    },
                    {
                        "agent": "report-reviewer",
                        "risk_flags": ["priority-candidate-needs-careful-report-wording"],
                    },
                ],
            }
        ],
    }


def _report_assistant():
    return {
        "kind": "result_evidence_report_assistant",
        "readiness": "needs-final-validation",
        "title_candidates": [
            "Possible Cross-Account Authorization Boundary Issue on `/api/high`"
        ],
        "affected_endpoints": ["/api/high"],
    }


def test_build_grounded_answer_collects_snippets():
    grounded = build_grounded_answer(
        answer="Focus on /api/high.",
        intent="final-report-focus",
        cited_endpoints=["/api/high"],
        next_actions=["Validate baselines."],
        case_summary=_case_summary(),
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
        report_assistant=_report_assistant(),
    )
    data = grounded.to_dict()

    assert data["kind"] == "result_evidence_grounded_answer"
    assert data["intent"] == "final-report-focus"
    assert data["cited_endpoints"] == ["/api/high"]
    assert data["next_actions"] == ["Validate baselines."]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    paths = [item["path"] for item in data["grounding"]]
    assert "strongest_candidates[0].endpoint" in paths
    assert "top_candidate.score" in paths
    assert "plans[0].agents[].risk_flags" in paths
    assert "title_candidates[0]" in paths


def test_build_grounded_answer_requires_case_summary_kind():
    with pytest.raises(ValueError):
        build_grounded_answer(
            answer="x",
            intent="general",
            cited_endpoints=[],
            next_actions=[],
            case_summary={"kind": "wrong"},
        )


def test_build_grounded_answer_rejects_wrong_ranking_kind():
    with pytest.raises(ValueError):
        build_grounded_answer(
            answer="x",
            intent="general",
            cited_endpoints=[],
            next_actions=[],
            case_summary=_case_summary(),
            ranking={"kind": "wrong"},
        )
