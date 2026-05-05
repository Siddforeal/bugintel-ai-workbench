import pytest

from bugintel.core.result_evidence_validation_plan import build_result_evidence_validation_plan


def _sample_hypotheses():
    return {
        "kind": "result_evidence_hypothesis_set",
        "count": 3,
        "hypotheses": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "confidence": "medium-high",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "source": "manual-json-batch:001.json",
            },
            {
                "endpoint": "/api/private/data",
                "hypothesis_class": "information-disclosure-candidate",
                "confidence": "medium",
                "evidence_strength": "medium-candidate",
                "severity_hint": "candidate-medium-to-high-depending-data-sensitivity",
                "source": "manual-json-batch:002.json",
            },
            {
                "endpoint": "/api/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "confidence": "medium",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "source": "manual-json-batch:003.json",
            },
        ],
    }


def test_build_result_evidence_validation_plan_creates_steps():
    result = build_result_evidence_validation_plan(_sample_hypotheses())
    data = result.to_dict()

    assert data["kind"] == "result_evidence_validation_plan"
    assert data["count"] == 3
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    first = data["plans"][0]
    assert first["priority"] == "high"
    assert first["hypothesis_class"] == "object-or-tenant-authorization-boundary-candidate"
    assert len(first["steps"]) >= 7
    assert first["stop_conditions"]
    assert first["report_readiness_checks"]

    third = data["plans"][2]
    assert third["priority"] == "low"
    assert len(third["steps"]) == 2


def test_build_result_evidence_validation_plan_high_priority_only():
    result = build_result_evidence_validation_plan(_sample_hypotheses(), high_priority_only=True)

    assert len(result.plans) == 2
    assert result.plans[0].endpoint == "/api/accounts/123/users/999"
    assert result.plans[1].endpoint == "/api/private/data"


def test_result_evidence_validation_plan_markdown_is_readable():
    result = build_result_evidence_validation_plan(_sample_hypotheses())
    markdown = result.to_markdown()

    assert "# Manual Validation Plan" in markdown
    assert "\\n" not in markdown
    assert "object-or-tenant-authorization-boundary-candidate" in markdown
    assert "Manual Steps" in markdown
    assert "Stop Conditions" in markdown
    assert "Report Readiness Checks" in markdown
    assert "It does not confirm vulnerabilities." in markdown


def test_build_result_evidence_validation_plan_requires_hypothesis_kind():
    with pytest.raises(ValueError):
        build_result_evidence_validation_plan({"kind": "wrong", "hypotheses": []})


def test_build_result_evidence_validation_plan_requires_hypotheses_list():
    with pytest.raises(ValueError):
        build_result_evidence_validation_plan({"kind": "result_evidence_hypothesis_set"})


def test_build_result_evidence_validation_plan_rejects_non_object_hypothesis():
    with pytest.raises(ValueError):
        build_result_evidence_validation_plan({"kind": "result_evidence_hypothesis_set", "hypotheses": ["bad"]})


def test_build_result_evidence_validation_plan_rejects_missing_endpoint():
    with pytest.raises(ValueError):
        build_result_evidence_validation_plan(
            {
                "kind": "result_evidence_hypothesis_set",
                "hypotheses": [{"hypothesis_class": "needs-more-evidence"}],
            }
        )
