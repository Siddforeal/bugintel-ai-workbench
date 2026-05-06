import pytest

from bugintel.core.result_evidence_report_assistant import build_case_report_assistant_draft


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 1,
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
                "source": "manual-json-batch:001.json",
            }
        ],
        "weak_or_rejected_candidates": [],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "count": 1,
        "top_candidate": {
            "endpoint": "/api/high",
            "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
            "priority": "high",
            "readiness": "needs-final-validation",
            "evidence_strength": "strong-candidate",
            "severity_hint": "candidate-high-if-sensitive-data-confirmed",
            "confidence": "medium-high",
            "missing_evidence": [],
            "next_actions": ["Capture own-object baseline."],
            "source": "manual-json-batch:001.json",
        },
        "candidates": [
            {
                "endpoint": "/api/high",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
                "source": "manual-json-batch:001.json",
            }
        ],
    }


def _multi_agent():
    return {
        "kind": "result_evidence_multi_agent_review_plan",
        "count": 1,
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


def test_build_case_report_assistant_draft_uses_ranking_and_agents():
    draft = build_case_report_assistant_draft(
        _case_summary(),
        ranking=_ranking(),
        multi_agent_review=_multi_agent(),
    )
    data = draft.to_dict()

    assert data["kind"] == "result_evidence_report_assistant"
    assert data["readiness"] == "needs-final-validation"
    assert data["affected_endpoints"] == ["/api/high"]
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    assert "# Case-to-Report Assistant Draft" in draft.markdown
    assert "\\n" not in draft.markdown
    assert "Candidate Title Options" in draft.markdown
    assert "Proof-of-Concept Skeleton" in draft.markdown
    assert "Impact Wording Guardrails" in draft.markdown
    assert "authz-reviewer" in draft.markdown
    assert "No vulnerability confirmation." in draft.markdown


def test_build_case_report_assistant_draft_can_use_case_summary_only():
    draft = build_case_report_assistant_draft(_case_summary())

    assert draft.affected_endpoints == ("/api/high",)
    assert "No multi-agent review artifact was provided" in draft.markdown


def test_build_case_report_assistant_draft_rejects_wrong_case_kind():
    with pytest.raises(ValueError):
        build_case_report_assistant_draft({"kind": "wrong"})


def test_build_case_report_assistant_draft_rejects_wrong_ranking_kind():
    with pytest.raises(ValueError):
        build_case_report_assistant_draft(_case_summary(), ranking={"kind": "wrong"})


def test_build_case_report_assistant_draft_rejects_wrong_multi_agent_kind():
    with pytest.raises(ValueError):
        build_case_report_assistant_draft(_case_summary(), multi_agent_review={"kind": "wrong"})


def test_build_case_report_assistant_draft_requires_candidate_endpoint():
    with pytest.raises(ValueError):
        build_case_report_assistant_draft(
            {
                "kind": "result_evidence_case_summary",
                "strongest_candidates": [],
                "findings": [],
            }
        )
