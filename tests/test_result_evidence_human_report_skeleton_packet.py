import pytest

from bugintel.core.result_evidence_human_report_skeleton_packet import (
    build_human_report_skeleton_packet,
)


def _blocked_gate():
    return {
        "kind": "result_evidence_finding_draft_packet_review_gate",
        "recommendation": "do-not-use-for-report-writing-resolve-blocked-claims",
        "title_quality_findings": [
            {
                "subject": "Title blocked until report-readiness blockers are resolved.",
                "category": "title-quality",
                "severity": "high",
                "status": "title-blocked",
                "source": "title_candidates",
                "reason": "Title is blocked.",
                "required_action": "Resolve blockers before using this title.",
            }
        ],
        "evidence_checklist_findings": [
            {
                "subject": "evidence_gaps=1",
                "category": "evidence-checklist",
                "severity": "medium",
                "status": "evidence-required-before-writing",
                "source": "packet_counts",
                "reason": "Evidence gap remains open.",
                "required_action": "Close evidence gaps.",
            }
        ],
        "reproduction_gap_findings": [
            {
                "subject": "Reproduction plan blocked until all blockers are resolved.",
                "category": "reproduction-plan",
                "severity": "info",
                "status": "reproduction-blocked",
                "source": "report_readiness_review",
                "reason": "Reproduction is blocked.",
                "required_action": "Resolve blockers.",
            }
        ],
        "wording_guardrail_findings": [
            {
                "subject": "Do not state High/Critical severity while blockers remain open.",
                "category": "severity-wording",
                "severity": "info",
                "status": "wording-overclaim-review-required",
                "source": "report_readiness_review",
                "reason": "Open blockers prevent severity wording.",
                "required_action": "Resolve blockers before severity.",
            }
        ],
        "blocked_claim_findings": [
            {
                "subject": "unsafe_or_rejected_items=1",
                "category": "unsafe-or-rejected-items-present",
                "severity": "info",
                "status": "blocked-claim-open",
                "source": "packet_counts",
                "reason": "Unsafe item remains open.",
                "required_action": "Keep unsafe item blocked.",
            }
        ],
        "do_not_claim_findings": [
            {
                "subject": "Do not claim the finding is confirmed until all blockers are resolved.",
                "category": "global-do-not-claim-yet",
                "severity": "info",
                "status": "do-not-claim-open",
                "source": "report_readiness_review",
                "reason": "Do not claim item remains open.",
                "required_action": "Resolve blockers.",
            }
        ],
        "safety_findings": [],
        "approved_writing_support": [],
        "final_review_checklist": ["Confirm no report is generated or submitted by Blackhole."],
        "safety": {
            "report_generation": False,
            "report_submission": False,
            "vulnerability_confirmation": False,
        },
    }


def _clean_gate():
    return {
        "kind": "result_evidence_finding_draft_packet_review_gate",
        "recommendation": "safe-as-human-writing-support-only",
        "title_quality_findings": [],
        "evidence_checklist_findings": [],
        "reproduction_gap_findings": [
            {
                "subject": "Placeholder: write manual reproduction steps from verified local evidence only.",
                "category": "reproduction-plan",
                "severity": "info",
                "status": "human-reproduction-writing-required",
                "source": "reproduction_plan_placeholders",
                "reason": "Steps are placeholders.",
                "required_action": "Replace placeholder with verified steps.",
            }
        ],
        "wording_guardrail_findings": [],
        "blocked_claim_findings": [],
        "do_not_claim_findings": [],
        "safety_findings": [],
        "approved_writing_support": [
            {
                "subject": "title candidates",
                "category": "approved-writing-support",
                "severity": "info",
                "status": "review-support-only",
                "source": "title_candidates",
                "reason": "Title candidates exist.",
                "required_action": "Human rewrites final title.",
            },
            {
                "subject": "evidence checklist",
                "category": "approved-writing-support",
                "severity": "info",
                "status": "review-support-only",
                "source": "evidence_checklist",
                "reason": "Evidence checklist exists.",
                "required_action": "Human confirms evidence.",
            },
        ],
        "final_review_checklist": ["Use approved writing support only as human-reviewed context."],
        "safety": {
            "report_generation": False,
            "report_submission": False,
            "vulnerability_confirmation": False,
        },
    }


def test_build_human_report_skeleton_packet_blocks_unready_gate():
    packet = build_human_report_skeleton_packet(_blocked_gate())
    data = packet.to_dict()

    assert data["kind"] == "result_evidence_human_report_skeleton_packet"
    assert data["recommendation"] == "skeleton-built-but-report-writing-blocked"
    assert data["summary"]["status"] == "blocked-until-review-complete"
    assert data["impact"]["status"] == "blocked-until-impact-evidence"
    assert data["steps_to_reproduce"]["status"] == "blocked-until-reproduction-verified"
    assert data["evidence"]["status"] == "blocked-until-evidence-complete"
    assert data["blocked_claims_do_not_claim"]["status"] == "open-blockers"
    assert data["safety"]["final_report"] is False
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_human_report_skeleton_packet_markdown_is_readable():
    packet = build_human_report_skeleton_packet(_blocked_gate())
    markdown = packet.to_markdown()

    assert "# Human Report Skeleton Packet" in markdown
    assert "## Summary" in markdown
    assert "## Steps to Reproduce" in markdown
    assert "## Blocked Claims / Do Not Claim" in markdown
    assert "This command builds a report skeleton packet only." in markdown
    assert "\\n" not in markdown


def test_human_report_skeleton_packet_clean_gate_is_skeleton_only():
    packet = build_human_report_skeleton_packet(_clean_gate())
    data = packet.to_dict()

    assert data["recommendation"] == "ready-as-human-report-skeleton-only"
    assert data["summary"]["status"] == "human-write-required"
    assert data["impact"]["status"] == "human-write-required"
    assert data["blocked_claims_do_not_claim"]["status"] == "none-open"
    assert "title candidates" in str(data["summary"]["source_items"])
    assert data["safety"]["final_report"] is False


def test_human_report_skeleton_packet_safety_blocker_wins():
    bad = _clean_gate()
    bad["safety_findings"] = [
        {
            "subject": "report_generation",
            "category": "safety-metadata",
            "severity": "high",
            "status": "unsafe-safety-metadata",
            "source": "safety",
            "reason": "Safety metadata unsafe.",
            "required_action": "Regenerate with report_generation=false.",
        }
    ]

    packet = build_human_report_skeleton_packet(bad)
    data = packet.to_dict()

    assert data["recommendation"] == "do-not-build-report-fix-safety-metadata"
    assert data["summary"]["status"] == "blocked-until-review-complete"


def test_human_report_skeleton_packet_requires_kind():
    with pytest.raises(ValueError):
        build_human_report_skeleton_packet({"kind": "wrong"})


def test_human_report_skeleton_packet_requires_lists():
    bad = {
        "kind": "result_evidence_finding_draft_packet_review_gate",
        "title_quality_findings": [],
        "evidence_checklist_findings": [],
        "reproduction_gap_findings": [],
        "wording_guardrail_findings": [],
        "blocked_claim_findings": [],
        "do_not_claim_findings": [],
        "safety_findings": [],
    }

    with pytest.raises(ValueError):
        build_human_report_skeleton_packet(bad)
