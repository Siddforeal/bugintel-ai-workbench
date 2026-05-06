import pytest

from bugintel.core.result_evidence_multi_agent_review import build_result_evidence_multi_agent_review_plan


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "count": 2,
        "candidates": [
            {
                "rank": 1,
                "endpoint": "/api/high",
                "score": 120,
                "priority": "high",
                "readiness": "needs-final-validation",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "reason": "priority=high",
                "source": "manual-json-batch:001.json",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
            },
            {
                "rank": 2,
                "endpoint": "/api/weak",
                "score": -80,
                "priority": "low",
                "readiness": "likely-false-positive",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "confidence": "medium",
                "reason": "likely_false_positive_penalty",
                "source": "manual-json-batch:002.json",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
            },
        ],
    }


def test_build_result_evidence_multi_agent_review_plan_creates_agents():
    plan = build_result_evidence_multi_agent_review_plan(_ranking())
    data = plan.to_dict()

    assert data["kind"] == "result_evidence_multi_agent_review_plan"
    assert data["count"] == 2
    assert data["total_agent_tasks"] == 10
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    first = data["plans"][0]
    assert first["endpoint"] == "/api/high"
    assert first["agent_count"] == 5
    assert [agent["agent"] for agent in first["agents"]] == [
        "authz-reviewer",
        "false-positive-reviewer",
        "impact-reviewer",
        "evidence-reviewer",
        "report-reviewer",
    ]


def test_build_result_evidence_multi_agent_review_plan_can_skip_low_priority():
    plan = build_result_evidence_multi_agent_review_plan(_ranking(), include_low_priority=False)
    data = plan.to_dict()

    assert data["count"] == 1
    assert data["plans"][0]["endpoint"] == "/api/high"


def test_result_evidence_multi_agent_review_markdown_is_readable():
    plan = build_result_evidence_multi_agent_review_plan(_ranking())
    markdown = plan.to_markdown()

    assert "# Multi-Agent Review Plan" in markdown
    assert "\\n" not in markdown
    assert "authz-reviewer" in markdown
    assert "false-positive-reviewer" in markdown
    assert "impact-reviewer" in markdown
    assert "evidence-reviewer" in markdown
    assert "report-reviewer" in markdown
    assert "It does not confirm vulnerabilities." in markdown


def test_build_result_evidence_multi_agent_review_plan_requires_ranking_kind():
    with pytest.raises(ValueError):
        build_result_evidence_multi_agent_review_plan({"kind": "wrong", "candidates": []})


def test_build_result_evidence_multi_agent_review_plan_requires_candidates_list():
    with pytest.raises(ValueError):
        build_result_evidence_multi_agent_review_plan({"kind": "result_evidence_priority_ranking"})


def test_build_result_evidence_multi_agent_review_plan_rejects_non_object_candidate():
    with pytest.raises(ValueError):
        build_result_evidence_multi_agent_review_plan(
            {"kind": "result_evidence_priority_ranking", "candidates": ["bad"]}
        )


def test_build_result_evidence_multi_agent_review_plan_rejects_missing_endpoint():
    with pytest.raises(ValueError):
        build_result_evidence_multi_agent_review_plan(
            {
                "kind": "result_evidence_priority_ranking",
                "candidates": [{"rank": 1, "priority": "high"}],
            }
        )
