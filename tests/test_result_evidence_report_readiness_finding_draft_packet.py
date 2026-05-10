import pytest

from bugintel.core.result_evidence_report_readiness_finding_draft_packet import (
    build_report_readiness_finding_draft_packet,
)


def _blocked_readiness():
    return {
        "kind": "result_evidence_export_bundle_report_readiness_review",
        "recommendation": "not-report-ready-fix-artifact-problems",
        "report_ready_support_notes": [
            {
                "subject": "approved_planning_updates=1",
                "status": "report-support-note",
                "category": "approved-review-package-note",
                "severity": "info",
                "source": "packet_counts",
                "reason": "Bundle contains approved planning notes.",
                "required_action": "Use as review notes only.",
            }
        ],
        "report_blockers": [
            {
                "subject": "blocked_updates=1",
                "status": "packet-risk",
                "category": "blocked-updates-present",
                "severity": "medium",
                "source": "packet_counts",
                "reason": "Bundle contains blocked updates.",
                "required_action": "Keep blocked updates out of report use.",
            }
        ],
        "missing_evidence": [
            {
                "subject": "evidence_gaps=1",
                "status": "missing-evidence",
                "category": "open-evidence-gap-count",
                "severity": "medium",
                "source": "packet_counts",
                "reason": "Bundle contains open evidence gaps.",
                "required_action": "Close evidence gaps.",
            }
        ],
        "unsafe_or_rejected_items": [
            {
                "subject": "unsafe_or_rejected_items=1",
                "status": "unsafe-or-rejected-blocker",
                "category": "unsafe-or-rejected-items-present",
                "severity": "high",
                "source": "packet_counts",
                "reason": "Bundle contains unsafe or rejected items.",
                "required_action": "Keep unsafe/rejected items blocked.",
            }
        ],
        "artifact_problems": [
            {
                "subject": "/tmp/missing.json",
                "status": "artifact-problem",
                "category": "missing-artifact",
                "severity": "high",
                "source": "packet-json",
                "reason": "Included artifact is marked missing.",
                "required_action": "Regenerate or remove artifact reference.",
            }
        ],
        "overclaim_risks": [
            {
                "subject": "overclaim_risks=1",
                "status": "report-overclaim-risk",
                "category": "open-overclaim-risk-count",
                "severity": "medium",
                "source": "packet_counts",
                "reason": "Bundle contains report overclaim risks.",
                "required_action": "Resolve overclaim risks.",
            }
        ],
        "safety_blockers": [],
        "final_report_readiness_checklist": ["Confirm every report claim maps to local evidence."],
        "report_guardrails": ["Do not claim confirmed vulnerability without local proof."],
        "safety": {
            "report_generation": False,
            "report_submission": False,
            "vulnerability_confirmation": False,
        },
    }


def test_build_report_readiness_finding_draft_packet_blocks_unready_review():
    packet = build_report_readiness_finding_draft_packet(_blocked_readiness())
    data = packet.to_dict()

    assert data["kind"] == "result_evidence_report_readiness_finding_draft_packet"
    assert data["recommendation"] == "do-not-draft-fix-artifacts"
    assert len(data["title_candidates"]) == 1
    assert data["title_candidates"][0]["status"] == "blocked"
    assert len(data["evidence_checklist"]) >= 2
    assert len(data["reproduction_plan_placeholders"]) == 1
    assert data["reproduction_plan_placeholders"][0]["status"] == "blocked"
    assert len(data["blocked_claims"]) >= 4
    assert len(data["do_not_claim_yet"]) >= 5
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_report_readiness_finding_draft_packet_markdown_is_readable():
    packet = build_report_readiness_finding_draft_packet(_blocked_readiness())
    markdown = packet.to_markdown()

    assert "# Report Readiness Finding Draft Packet" in markdown
    assert "Title Candidates" in markdown
    assert "Evidence Checklist" in markdown
    assert "Reproduction Plan Placeholders" in markdown
    assert "Do Not Claim Yet" in markdown
    assert "Do not treat this packet as a generated report." in markdown
    assert "\\n" not in markdown


def test_report_readiness_finding_draft_packet_clean_review_ready():
    clean = {
        "kind": "result_evidence_export_bundle_report_readiness_review",
        "recommendation": "ready-as-human-report-support-only",
        "report_ready_support_notes": [
            {
                "subject": "approved_planning_updates=1",
                "status": "report-support-note",
                "category": "approved-review-package-note",
                "severity": "info",
                "source": "packet_counts",
                "reason": "Bundle contains approved planning notes.",
                "required_action": "Use as review notes only.",
            }
        ],
        "report_blockers": [],
        "missing_evidence": [],
        "unsafe_or_rejected_items": [],
        "artifact_problems": [],
        "overclaim_risks": [],
        "safety_blockers": [],
        "final_report_readiness_checklist": [],
        "report_guardrails": [],
    }

    packet = build_report_readiness_finding_draft_packet(clean)
    data = packet.to_dict()

    assert data["recommendation"] == "ready-for-human-written-draft-packet"
    assert len(data["title_candidates"]) == 1
    assert data["title_candidates"][0]["status"] == "human-write-required"
    assert len(data["evidence_checklist"]) == 1
    assert len(data["reproduction_plan_placeholders"]) == 1
    assert data["blocked_claims"] == []
    assert data["do_not_claim_yet"] == []


def test_report_readiness_finding_draft_packet_safety_blocker_wins():
    bad = _blocked_readiness()
    bad["safety_blockers"] = [
        {
            "subject": "tool_execution",
            "status": "safety-blocker",
            "category": "unsafe-safety-metadata",
            "severity": "high",
            "source": "safety",
            "reason": "Safety metadata is unsafe.",
            "required_action": "Regenerate with tool_execution=false.",
        }
    ]

    packet = build_report_readiness_finding_draft_packet(bad)
    data = packet.to_dict()

    assert data["recommendation"] == "do-not-draft-fix-safety-metadata"
    assert "tool_execution" in str(data["do_not_claim_yet"])


def test_report_readiness_finding_draft_packet_requires_kind():
    with pytest.raises(ValueError):
        build_report_readiness_finding_draft_packet({"kind": "wrong"})


def test_report_readiness_finding_draft_packet_requires_lists():
    bad = {
        "kind": "result_evidence_export_bundle_report_readiness_review",
        "report_ready_support_notes": [],
        "report_blockers": [],
        "missing_evidence": [],
        "unsafe_or_rejected_items": [],
        "artifact_problems": [],
        "overclaim_risks": [],
    }

    with pytest.raises(ValueError):
        build_report_readiness_finding_draft_packet(bad)
