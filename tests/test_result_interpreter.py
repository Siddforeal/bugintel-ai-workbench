from bugintel.core.result_interpreter import interpret_validation_result


def test_interpreter_suggests_supported_for_positive_signals():
    result = interpret_validation_result(
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=200,
        expected_status=403,
        note="Observed foreign account private data and permission bypass.",
    )
    data = result.to_dict()

    assert data["suggested_result"] == "supported"
    assert data["planning_only"] is True
    assert any(signal["name"] == "status-differs-from-expected" for signal in data["signals"])
    assert any(signal["name"].startswith("positive:") for signal in data["signals"])


def test_interpreter_suggests_rejected_for_blocked_expected_behavior():
    result = interpret_validation_result(
        endpoint="/api/files/{id}/download",
        observed_status=403,
        expected_status=403,
        note="Access denied. Expected behavior. No sensitive data.",
    )
    data = result.to_dict()

    assert data["suggested_result"] == "rejected"
    assert any(signal["name"] == "observed-auth-block" for signal in data["signals"])


def test_interpreter_suggests_needs_more_evidence_for_inconclusive_result():
    result = interpret_validation_result(
        endpoint="/api/status",
        observed_status=404,
        expected_status=None,
        note="Same as random.",
    )
    data = result.to_dict()

    assert data["suggested_result"] == "needs-more-evidence"


def test_interpreter_handles_empty_input():
    result = interpret_validation_result(endpoint="/api/unknown")
    data = result.to_dict()

    assert data["suggested_result"] == "needs-more-evidence"
    assert data["signals"] == []
