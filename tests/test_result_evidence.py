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

def test_import_result_evidence_batch_normalizes_directory(tmp_path):
    from bugintel.core.result_evidence import import_result_evidence_batch

    first = tmp_path / "001.json"
    second = tmp_path / "002.json"

    first.write_text('{"endpoint": "/api/a", "observed_status": "200", "expected_status": 403}')
    second.write_text('{"url": "/api/b", "status_code": 404, "note": "same as random"}')

    batch = import_result_evidence_batch(tmp_path)
    data = batch.to_dict()

    assert data["kind"] == "result_evidence_batch"
    assert data["count"] == 2
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["evidence"][0]["endpoint"] == "/api/a"
    assert data["evidence"][0]["observed_status"] == 200
    assert data["evidence"][1]["endpoint"] == "/api/b"
    assert data["evidence"][1]["observed_status"] == 404
    assert data["safety"]["local_only"] is True
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["target_mutation"] is False


def test_import_result_evidence_batch_missing_directory_raises(tmp_path):
    from bugintel.core.result_evidence import import_result_evidence_batch

    with pytest.raises(FileNotFoundError):
        import_result_evidence_batch(tmp_path / "missing")


def test_import_result_evidence_batch_rejects_invalid_json(tmp_path):
    from bugintel.core.result_evidence import import_result_evidence_batch

    bad = tmp_path / "bad.json"
    bad.write_text("{not json")

    with pytest.raises(ValueError):
        import_result_evidence_batch(tmp_path)
