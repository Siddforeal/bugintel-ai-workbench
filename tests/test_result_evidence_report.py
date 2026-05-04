import pytest

from bugintel.core.result_evidence_report import render_result_evidence_review_report


def test_render_result_evidence_review_report_outputs_markdown():
    report = render_result_evidence_review_report(
        {
            "kind": "result_evidence_batch_review",
            "count": 2,
            "supported_count": 1,
            "rejected_count": 1,
            "needs_more_evidence_count": 0,
            "missing_expected_status_count": 0,
            "items": [
                {
                    "endpoint": "/api/a",
                    "suggested_result": "supported",
                    "confidence": "medium-high",
                    "source": "manual-json-batch:001.json",
                    "observed_status": 200,
                    "expected_status": 403,
                    "signal_count": 5,
                    "rationale": "Signals suggest the validation may support the hypothesis.",
                },
                {
                    "endpoint": "/api/b",
                    "suggested_result": "rejected",
                    "confidence": "medium",
                    "source": "manual-json-batch:002.json",
                    "observed_status": 403,
                    "expected_status": 403,
                    "signal_count": 3,
                    "rationale": "Signals suggest expected blocking.",
                },
            ],
        }
    )

    data = report.to_dict()

    assert data["kind"] == "result_evidence_review_report"
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["network_interaction"] is False
    assert "# Result Evidence Batch Review Report" in report.markdown
    assert "\\n" not in report.markdown
    assert len(report.markdown.splitlines()) > 20
    assert "- Total evidence items: 2" in report.markdown
    assert "- Supported candidates: 1" in report.markdown
    assert "### 1. `/api/a`" in report.markdown
    assert "Suggested result: **supported**" in report.markdown
    assert "### 2. `/api/b`" in report.markdown
    assert "Do not treat this report as a vulnerability confirmation" in report.markdown


def test_render_result_evidence_review_report_rejects_wrong_kind():
    with pytest.raises(ValueError):
        render_result_evidence_review_report({"kind": "wrong", "items": []})


def test_render_result_evidence_review_report_requires_items_list():
    with pytest.raises(ValueError):
        render_result_evidence_review_report({"kind": "result_evidence_batch_review"})


def test_render_result_evidence_review_report_rejects_item_without_endpoint():
    with pytest.raises(ValueError):
        render_result_evidence_review_report(
            {
                "kind": "result_evidence_batch_review",
                "items": [{"suggested_result": "supported"}],
            }
        )
