import pytest

from bugintel.core.result_evidence_priority_ranking import build_result_evidence_priority_ranking


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 3,
        "findings": [
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
            },
            {
                "endpoint": "/api/medium",
                "hypothesis_class": "information-disclosure-candidate",
                "priority": "medium-high",
                "readiness": "needs-more-evidence",
                "evidence_strength": "medium-candidate",
                "severity_hint": "candidate-medium-to-high-depending-data-sensitivity",
                "confidence": "medium",
                "missing_evidence": ["Random-object baseline"],
                "next_actions": ["Collect missing baseline."],
                "source": "manual-json-batch:002.json",
            },
            {
                "endpoint": "/api/weak",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "priority": "low",
                "readiness": "likely-false-positive",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "confidence": "medium",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
                "source": "manual-json-batch:003.json",
            },
        ],
    }


def test_build_result_evidence_priority_ranking_orders_candidates():
    ranking = build_result_evidence_priority_ranking(_case_summary())
    data = ranking.to_dict()

    assert data["kind"] == "result_evidence_priority_ranking"
    assert data["count"] == 3
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    assert data["top_candidate"]["endpoint"] == "/api/high"
    assert data["candidates"][0]["rank"] == 1
    assert data["candidates"][0]["score"] > data["candidates"][1]["score"]
    assert data["candidates"][1]["score"] > data["candidates"][2]["score"]
    assert data["candidates"][2]["endpoint"] == "/api/weak"


def test_build_result_evidence_priority_ranking_can_exclude_weak():
    ranking = build_result_evidence_priority_ranking(_case_summary(), include_weak=False)
    data = ranking.to_dict()

    assert data["count"] == 2
    assert [item["endpoint"] for item in data["candidates"]] == ["/api/high", "/api/medium"]


def test_result_evidence_priority_ranking_markdown_is_readable():
    ranking = build_result_evidence_priority_ranking(_case_summary())
    markdown = ranking.to_markdown()

    assert "# Result Evidence Priority Ranking" in markdown
    assert "\\n" not in markdown
    assert "Top Candidate" in markdown
    assert "/api/high" in markdown
    assert "likely_false_positive_penalty" in markdown
    assert "It does not confirm vulnerabilities." in markdown


def test_build_result_evidence_priority_ranking_requires_case_summary_kind():
    with pytest.raises(ValueError):
        build_result_evidence_priority_ranking({"kind": "wrong", "findings": []})


def test_build_result_evidence_priority_ranking_requires_findings_list():
    with pytest.raises(ValueError):
        build_result_evidence_priority_ranking({"kind": "result_evidence_case_summary"})


def test_build_result_evidence_priority_ranking_rejects_non_object_finding():
    with pytest.raises(ValueError):
        build_result_evidence_priority_ranking({"kind": "result_evidence_case_summary", "findings": ["bad"]})


def test_build_result_evidence_priority_ranking_rejects_missing_endpoint():
    with pytest.raises(ValueError):
        build_result_evidence_priority_ranking(
            {
                "kind": "result_evidence_case_summary",
                "findings": [{"priority": "high"}],
            }
        )
