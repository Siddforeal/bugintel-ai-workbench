import pytest

from bugintel.core.result_evidence_hypothesis import generate_result_evidence_hypotheses


def _sample_review():
    return {
        "kind": "result_evidence_batch_review",
        "count": 3,
        "supported_count": 1,
        "rejected_count": 1,
        "needs_more_evidence_count": 1,
        "missing_expected_status_count": 1,
        "items": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "suggested_result": "supported",
                "confidence": "medium-high",
                "source": "manual-json-batch:001.json",
                "observed_status": 200,
                "expected_status": 403,
                "signal_count": 5,
                "rationale": "Observed foreign account private data and permission bypass.",
            },
            {
                "endpoint": "/api/accounts/123/users/random",
                "suggested_result": "rejected",
                "confidence": "medium",
                "source": "manual-json-batch:002.json",
                "observed_status": 403,
                "expected_status": 403,
                "signal_count": 3,
                "rationale": "Forbidden expected behavior.",
            },
            {
                "endpoint": "/api/accounts/123/users/missing",
                "suggested_result": "needs-more-evidence",
                "confidence": "medium",
                "source": "manual-json-batch:003.json",
                "observed_status": 404,
                "expected_status": None,
                "signal_count": 2,
                "rationale": "Same as random.",
            },
        ],
    }


def test_generate_result_evidence_hypotheses_classifies_items():
    result = generate_result_evidence_hypotheses(_sample_review())
    data = result.to_dict()

    assert data["kind"] == "result_evidence_hypothesis_set"
    assert data["count"] == 3
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    first = data["hypotheses"][0]
    assert first["hypothesis_class"] == "object-or-tenant-authorization-boundary-candidate"
    assert first["confidence"] == "medium-high"
    assert first["evidence_strength"] == "strong-candidate"
    assert first["severity_hint"] == "candidate-high-if-sensitive-data-confirmed"
    assert first["next_manual_tests"]

    second = data["hypotheses"][1]
    assert second["hypothesis_class"] == "likely-expected-blocking-or-false-positive"
    assert second["severity_hint"] == "not-reportable-with-current-evidence"

    third = data["hypotheses"][2]
    assert third["hypothesis_class"] == "likely-expected-blocking-or-false-positive"


def test_generate_result_evidence_hypotheses_supported_only():
    result = generate_result_evidence_hypotheses(_sample_review(), supported_only=True)

    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].endpoint == "/api/accounts/123/users/999"


def test_result_evidence_hypothesis_markdown_is_readable():
    result = generate_result_evidence_hypotheses(_sample_review())
    markdown = result.to_markdown()

    assert "# Result Evidence Hypotheses" in markdown
    assert "\\n" not in markdown
    assert "object-or-tenant-authorization-boundary-candidate" in markdown
    assert "Next manual tests" in markdown
    assert "No vulnerability confirmation" in markdown


def test_generate_result_evidence_hypotheses_requires_review_kind():
    with pytest.raises(ValueError):
        generate_result_evidence_hypotheses({"kind": "wrong", "items": []})


def test_generate_result_evidence_hypotheses_requires_items_list():
    with pytest.raises(ValueError):
        generate_result_evidence_hypotheses({"kind": "result_evidence_batch_review"})


def test_generate_result_evidence_hypotheses_rejects_non_object_items():
    with pytest.raises(ValueError):
        generate_result_evidence_hypotheses({"kind": "result_evidence_batch_review", "items": ["bad"]})


def test_generate_result_evidence_hypotheses_rejects_missing_endpoint():
    with pytest.raises(ValueError):
        generate_result_evidence_hypotheses(
            {
                "kind": "result_evidence_batch_review",
                "items": [{"suggested_result": "supported"}],
            }
        )
