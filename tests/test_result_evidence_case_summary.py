import pytest

from bugintel.core.result_evidence_case_summary import build_result_evidence_case_summary


def _sample_validation_plan():
    return {
        "kind": "result_evidence_validation_plan",
        "count": 2,
        "plans": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "confidence": "medium-high",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "priority": "high",
                "source": "manual-json-batch:001.json",
                "steps": [{"title": f"step-{i}"} for i in range(7)],
                "stop_conditions": [
                    "Stop if the asset, endpoint, account, tenant, or object is out of scope.",
                    "Stop before any destructive testing.",
                ],
                "report_readiness_checks": [
                    "Scope is confirmed.",
                    "Own-object baseline is captured.",
                    "Foreign-object or second-account behavior is captured.",
                    "Random-object baseline is captured.",
                    "Raw requests and responses are preserved with secrets redacted.",
                    "The finding draft does not overclaim impact.",
                    "Sensitive or tenant-specific data/state is identified.",
                    "Authorization boundary expectation is explained.",
                    "Reproduction is repeatable with controlled accounts.",
                    "Impact is tied directly to proven evidence.",
                ],
            },
            {
                "endpoint": "/api/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "confidence": "medium",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "priority": "low",
                "source": "manual-json-batch:002.json",
                "steps": [{"title": "Confirm expected blocking"}],
                "stop_conditions": [
                    "Stop if the asset, endpoint, account, tenant, or object is out of scope.",
                    "Stop and mark rejected if all baselines match expected blocking.",
                ],
                "report_readiness_checks": [
                    "Scope is confirmed.",
                    "Random-object baseline is captured.",
                ],
            },
        ],
    }


def test_build_result_evidence_case_summary_classifies_readiness():
    summary = build_result_evidence_case_summary(_sample_validation_plan())
    data = summary.to_dict()

    assert data["kind"] == "result_evidence_case_summary"
    assert data["count"] == 2
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    first = data["findings"][0]
    assert first["readiness"] == "needs-final-validation"
    assert first["priority"] == "high"
    assert first["next_actions"]

    second = data["findings"][1]
    assert second["readiness"] == "likely-false-positive"
    assert second["missing_evidence"] == [
        "Evidence proving behavior differs from expected blocking or random-object behavior"
    ]

    assert len(data["strongest_candidates"]) == 1
    assert len(data["weak_or_rejected_candidates"]) == 1


def test_result_evidence_case_summary_markdown_is_readable():
    summary = build_result_evidence_case_summary(_sample_validation_plan())
    markdown = summary.to_markdown()

    assert "# Case Intelligence Summary" in markdown
    assert "\\n" not in markdown
    assert "Strongest Candidates" in markdown
    assert "Weak / Rejected / Not Reportable Currently" in markdown
    assert "Case-Level Next Actions" in markdown
    assert "It does not confirm vulnerabilities." in markdown


def test_build_result_evidence_case_summary_requires_validation_plan_kind():
    with pytest.raises(ValueError):
        build_result_evidence_case_summary({"kind": "wrong", "plans": []})


def test_build_result_evidence_case_summary_requires_plans_list():
    with pytest.raises(ValueError):
        build_result_evidence_case_summary({"kind": "result_evidence_validation_plan"})


def test_build_result_evidence_case_summary_rejects_non_object_plan():
    with pytest.raises(ValueError):
        build_result_evidence_case_summary({"kind": "result_evidence_validation_plan", "plans": ["bad"]})


def test_build_result_evidence_case_summary_rejects_missing_endpoint():
    with pytest.raises(ValueError):
        build_result_evidence_case_summary(
            {
                "kind": "result_evidence_validation_plan",
                "plans": [{"hypothesis_class": "needs-more-evidence"}],
            }
        )
