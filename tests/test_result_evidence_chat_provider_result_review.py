import pytest

from bugintel.core.result_evidence_chat_provider_result_review import review_case_chat_provider_result


def _imported_result():
    return {
        "kind": "result_evidence_case_chat_provider_result",
        "provider_output": "This is not proof.\n- Validate own-object baseline.\n- Confirm random-object behavior.",
        "suggested_actions": [
            "Validate own-object baseline.",
            "Confirm random-object behavior.",
        ],
        "warning_flags": [],
        "untrusted_suggestion": True,
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "top_endpoint": "/api/high",
        "cited_endpoints": ["/api/high"],
        "open_next_actions": [
            "Validate own-object baseline.",
            "Confirm random-object behavior.",
        ],
        "missing_evidence": ["Impact proof"],
    }


def _grounded_answer():
    return {
        "kind": "result_evidence_grounded_answer",
        "next_actions": ["Validate own-object baseline."],
        "grounding": [
            {
                "artifact": "case-memory",
                "path": "top_endpoint",
                "value": "/api/high",
            },
            {
                "artifact": "case-memory",
                "path": "missing_evidence[0]",
                "value": "Impact proof",
            },
        ],
    }


def test_review_provider_result_marks_supported_actions_and_missing_evidence():
    review = review_case_chat_provider_result(
        _imported_result(),
        case_memory=_case_memory(),
        grounded_answer=_grounded_answer(),
    )
    data = review.to_dict()

    assert data["kind"] == "result_evidence_case_chat_provider_result_review"
    assert data["recommendation"] == "use-as-planning-note-needs-evidence"
    assert data["untrusted_suggestion"] is True
    assert data["missing_evidence"] == ["Impact proof"]
    assert data["reviewed_actions"][0]["status"] == "supported-planning-action"
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_review_provider_result_rejects_overclaims():
    imported = _imported_result()
    imported["provider_output"] = "This is a confirmed vulnerability with high severity."
    imported["warning_flags"] = [
        "overclaim-confirmed-vulnerability",
        "severity-claim-needs-proof",
    ]

    review = review_case_chat_provider_result(imported, case_memory=_case_memory())
    data = review.to_dict()

    assert data["recommendation"] == "reject-unsafe-or-overclaimed-parts"
    assert "Provider output contains warning flag: overclaim-confirmed-vulnerability" in data["unsupported_claims"]


def test_review_provider_result_markdown_is_readable():
    review = review_case_chat_provider_result(_imported_result(), case_memory=_case_memory())
    markdown = review.to_markdown()

    assert "# Provider Suggestion Review" in markdown
    assert "Untrusted suggestion: true" in markdown
    assert "Provider execution performed by Blackhole: false" in markdown
    assert "\\n" not in markdown


def test_review_provider_result_rejects_wrong_imported_kind():
    with pytest.raises(ValueError):
        review_case_chat_provider_result({"kind": "wrong"})


def test_review_provider_result_rejects_wrong_case_memory_kind():
    with pytest.raises(ValueError):
        review_case_chat_provider_result(_imported_result(), case_memory={"kind": "wrong"})


def test_review_provider_result_rejects_wrong_grounded_kind():
    with pytest.raises(ValueError):
        review_case_chat_provider_result(_imported_result(), grounded_answer={"kind": "wrong"})
