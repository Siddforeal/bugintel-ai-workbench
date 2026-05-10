import pytest

from bugintel.core.result_evidence_export_bundle_report_readiness import (
    build_export_bundle_report_readiness_review,
)


def _review_gate():
    return {
        "kind": "result_evidence_export_bundle_review_gate",
        "recommendation": "do-not-use-bundle-until-artifacts-verified",
        "artifact_integrity_findings": [
            {
                "category": "missing-or-invalid-artifact-hash",
                "severity": "medium",
                "message": "Artifact lacks a valid SHA256 hash.",
                "subject": "/tmp/bad-hash.txt",
                "source": "bad-artifact",
                "required_action": "Rebuild artifact hash.",
            }
        ],
        "missing_artifact_findings": [
            {
                "category": "missing-artifact",
                "severity": "high",
                "message": "Included artifact is marked missing.",
                "subject": "/tmp/missing.json",
                "source": "packet-json",
                "required_action": "Regenerate or remove artifact reference.",
            }
        ],
        "packet_risk_findings": [
            {
                "category": "unsafe-or-rejected-items-present",
                "severity": "high",
                "message": "Bundle contains unsafe or rejected items.",
                "subject": "unsafe_or_rejected_items=1",
                "source": "packet_counts",
                "required_action": "Keep unsafe/rejected items blocked.",
            },
            {
                "category": "blocked-updates-present",
                "severity": "medium",
                "message": "Bundle contains blocked updates.",
                "subject": "blocked_updates=1",
                "source": "packet_counts",
                "required_action": "Keep blocked updates out of report use.",
            },
        ],
        "evidence_gap_findings": [
            {
                "category": "open-evidence-gap-count",
                "severity": "medium",
                "message": "Bundle contains open evidence gaps.",
                "subject": "evidence_gaps=1",
                "source": "packet_counts",
                "required_action": "Close evidence gaps.",
            }
        ],
        "overclaim_findings": [
            {
                "category": "open-overclaim-risk-count",
                "severity": "medium",
                "message": "Bundle contains report overclaim risks.",
                "subject": "overclaim_risks=1",
                "source": "packet_counts",
                "required_action": "Resolve overclaim risks.",
            }
        ],
        "safety_findings": [],
        "approved_review_notes": [
            {
                "category": "approved-review-package-note",
                "severity": "info",
                "message": "Bundle contains approved planning notes.",
                "subject": "approved_planning_updates=1",
                "source": "packet_counts",
                "required_action": "Use as review notes only.",
            }
        ],
        "report_guardrails": ["Do not use bundle artifacts as vulnerability proof without local validation."],
        "human_review_checklist": ["Confirm every included artifact exists and has an integrity hash."],
        "safety": {
            "state_mutation": False,
            "vulnerability_confirmation": False,
        },
    }


def test_build_export_bundle_report_readiness_review_splits_sections():
    review = build_export_bundle_report_readiness_review(_review_gate())
    data = review.to_dict()

    assert data["kind"] == "result_evidence_export_bundle_report_readiness_review"
    assert data["recommendation"] == "not-report-ready-fix-artifact-problems"
    assert len(data["artifact_problems"]) == 2
    assert len(data["missing_evidence"]) == 1
    assert len(data["unsafe_or_rejected_items"]) == 1
    assert len(data["overclaim_risks"]) == 1
    assert len(data["report_blockers"]) >= 4
    assert data["report_ready_support_notes"] == []
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_export_bundle_report_readiness_markdown_is_readable():
    review = build_export_bundle_report_readiness_review(_review_gate())
    markdown = review.to_markdown()

    assert "# Export Bundle Report Readiness Review" in markdown
    assert "Report-Ready Support Notes" in markdown
    assert "Report Blockers" in markdown
    assert "Artifact Problems" in markdown
    assert "Final Report-Readiness Checklist" in markdown
    assert "Do not generate or submit a report from this command." in markdown
    assert "\\n" not in markdown


def test_export_bundle_report_readiness_clean_gate_is_report_support_only():
    clean = {
        "kind": "result_evidence_export_bundle_review_gate",
        "artifact_integrity_findings": [],
        "missing_artifact_findings": [],
        "packet_risk_findings": [],
        "evidence_gap_findings": [],
        "overclaim_findings": [],
        "safety_findings": [],
        "approved_review_notes": [
            {
                "category": "approved-review-package-note",
                "severity": "info",
                "message": "Bundle contains approved planning notes.",
                "subject": "approved_planning_updates=1",
                "source": "packet_counts",
                "required_action": "Use these as review notes only.",
            }
        ],
        "report_guardrails": [],
        "human_review_checklist": [],
    }

    review = build_export_bundle_report_readiness_review(clean)
    data = review.to_dict()

    assert data["recommendation"] == "ready-as-human-report-support-only"
    assert len(data["report_ready_support_notes"]) == 1
    assert data["report_blockers"] == []
    assert data["artifact_problems"] == []
    assert data["unsafe_or_rejected_items"] == []


def test_export_bundle_report_readiness_safety_blocker_wins():
    bad = _review_gate()
    bad["safety_findings"] = [
        {
            "category": "unsafe-safety-metadata",
            "severity": "high",
            "message": "Safety metadata is unsafe.",
            "subject": "tool_execution",
            "source": "safety",
            "required_action": "Regenerate with tool_execution=false.",
        }
    ]

    review = build_export_bundle_report_readiness_review(bad)
    data = review.to_dict()

    assert data["recommendation"] == "not-report-ready-fix-safety-metadata"
    assert len(data["safety_blockers"]) == 1


def test_export_bundle_report_readiness_requires_gate_kind():
    with pytest.raises(ValueError):
        build_export_bundle_report_readiness_review({"kind": "wrong"})


def test_export_bundle_report_readiness_requires_lists():
    bad = {
        "kind": "result_evidence_export_bundle_review_gate",
        "artifact_integrity_findings": [],
        "missing_artifact_findings": [],
        "packet_risk_findings": [],
        "evidence_gap_findings": [],
        "overclaim_findings": [],
        "safety_findings": [],
    }

    with pytest.raises(ValueError):
        build_export_bundle_report_readiness_review(bad)
