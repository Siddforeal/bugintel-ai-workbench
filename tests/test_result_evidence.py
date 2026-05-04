import pytest

from bugintel.core.result_evidence import import_result_evidence


def test_import_result_evidence_normalizes_fields():
    evidence = import_result_evidence(
        {
            "endpoint": "/api/accounts/123/users/{id}/permissions",
            "observed_status": "200",
            "expected_status": 403,
            "note": "Observed foreign account private data.",
        }
    )
    data = evidence.to_dict()

    assert data["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["observed_status"] == 200
    assert data["expected_status"] == 403
    assert data["note"] == "Observed foreign account private data."
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"


def test_import_result_evidence_accepts_url_and_status_code_alias():
    evidence = import_result_evidence(
        {
            "url": "https://example.com/api/status",
            "status_code": 404,
            "body": "same as random",
        },
        source="http-sample",
    )
    data = evidence.to_dict()

    assert data["endpoint"] == "https://example.com/api/status"
    assert data["observed_status"] == 404
    assert data["observed_body"] == "same as random"
    assert data["source"] == "http-sample"


def test_import_result_evidence_missing_endpoint_raises():
    with pytest.raises(ValueError):
        import_result_evidence({"observed_status": 200})


def test_import_result_evidence_invalid_status_becomes_none():
    evidence = import_result_evidence(
        {
            "endpoint": "/api/test",
            "observed_status": "not-int",
        }
    )

    assert evidence.observed_status is None
