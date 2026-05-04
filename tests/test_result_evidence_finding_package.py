import json

import pytest

from bugintel.core.result_evidence_finding_package import build_result_evidence_finding_package


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


def test_build_result_evidence_finding_package_creates_expected_files():
    package = build_result_evidence_finding_package(_sample_review())
    data = package.to_dict()

    assert data["kind"] == "result_evidence_finding_package"
    assert data["file_count"] == 5
    assert data["planning_only"] is True
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False

    assert set(package.files) == {
        "finding-draft.md",
        "review-report.md",
        "submission-checklist.md",
        "metadata.json",
        "manifest.json",
    }

    assert "# Candidate Finding Draft" in package.files["finding-draft.md"]
    assert "### 1. `/api/a`" in package.files["finding-draft.md"]
    assert "/api/b" not in package.files["finding-draft.md"]
    assert "# Result Evidence Batch Review Report" in package.files["review-report.md"]
    assert "# Submission Checklist" in package.files["submission-checklist.md"]

    metadata = json.loads(package.files["metadata.json"])
    assert metadata["selected_item_count"] == 1
    assert metadata["selected_endpoints"] == ["/api/a"]
    assert metadata["safety"]["network_interaction"] is False

    manifest = json.loads(package.files["manifest.json"])
    assert manifest["kind"] == "result_evidence_finding_package_manifest"
    assert "finding-draft.md" in manifest["files"]


def test_build_result_evidence_finding_package_include_all():
    package = build_result_evidence_finding_package(_sample_review(), include_all=True)
    metadata = json.loads(package.files["metadata.json"])

    assert metadata["selected_item_count"] == 3
    assert metadata["include_all"] is True
    assert metadata["selected_endpoints"] == ["/api/a", "/api/b", "/api/c"]
    assert "### 2. `/api/b`" in package.files["finding-draft.md"]
    assert "### 3. `/api/c`" in package.files["finding-draft.md"]


def test_build_result_evidence_finding_package_requires_review_kind():
    with pytest.raises(ValueError):
        build_result_evidence_finding_package({"kind": "wrong", "items": []})


def test_build_result_evidence_finding_package_requires_items_list():
    with pytest.raises(ValueError):
        build_result_evidence_finding_package({"kind": "result_evidence_batch_review"})


def test_build_result_evidence_finding_package_rejects_selected_item_without_endpoint():
    with pytest.raises(ValueError):
        build_result_evidence_finding_package(
            {
                "kind": "result_evidence_batch_review",
                "items": [{"suggested_result": "supported"}],
            }
        )
