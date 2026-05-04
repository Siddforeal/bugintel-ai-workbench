import pytest

from bugintel.core.result_evidence_finding_draft import render_result_evidence_finding_draft


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
                "endpoint": "/api/a",
                "suggested_result": "supported",
                "confidence": "medium-high",
                "source": "manual-json-batch:001.json",
                "observed_status": 200,
                "expected_status": 403,
                "signal_count": 5,
                "rationale": "Signals suggest support.",
            },
            {
                "endpoint": "/api/b",
                "suggested_result": "rejected",
                "confidence": "medium",
                "source": "manual-json-batch:002.json",
                "observed_status": 403,
                "expected_status": 403,
                "signal_count": 3,
                "rationale": "Expected blocking.",
            },
            {
                "endpoint": "/api/c",
                "suggested_result": "needs-more-evidence",
                "confidence": "medium",
                "source": "manual-json-batch:003.json",
                "observed_status": 404,
                "expected_status": None,
                "signal_count": 2,
                "rationale": "Inconclusive.",
            },
        ],
    }


def test_render_result_evidence_finding_draft_selects_supported_by_default():
    draft = render_result_evidence_finding_draft(_sample_review())
    data = draft.to_dict()

    assert data["kind"] == "result_evidence_finding_draft"
    assert data["selected_count"] == 1
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False
    assert "# Candidate Finding Draft" in draft.markdown
    assert "\\n" not in draft.markdown
    assert len(draft.markdown.splitlines()) > 40
    assert "### 1. `/api/a`" in draft.markdown
    assert "/api/b" not in draft.markdown
    assert "Manual Validation Checklist" in draft.markdown
    assert "It is not a vulnerability confirmation" in draft.markdown


def test_render_result_evidence_finding_draft_can_include_all_items():
    draft = render_result_evidence_finding_draft(_sample_review(), include_all=True)

    assert draft.selected_count == 3
    assert "### 1. `/api/a`" in draft.markdown
    assert "### 2. `/api/b`" in draft.markdown
    assert "### 3. `/api/c`" in draft.markdown


def test_render_result_evidence_finding_draft_requires_review_kind():
    with pytest.raises(ValueError):
        render_result_evidence_finding_draft({"kind": "wrong", "items": []})


def test_render_result_evidence_finding_draft_requires_items_list():
    with pytest.raises(ValueError):
        render_result_evidence_finding_draft({"kind": "result_evidence_batch_review"})


def test_render_result_evidence_finding_draft_rejects_item_without_endpoint():
    with pytest.raises(ValueError):
        render_result_evidence_finding_draft(
            {
                "kind": "result_evidence_batch_review",
                "items": [{"suggested_result": "supported"}],
            }
        )
