import pytest

from bugintel.core.result_evidence_finding_draft_packet_review_gate import (
    build_finding_draft_packet_review_gate,
)


def _blocked_packet():
    return {
        "kind": "result_evidence_report_readiness_finding_draft_packet",
        "recommendation": "do-not-draft-remove-unsafe-items",
        "title_candidates": [
            {
                "text": "Title blocked until report-readiness blockers are resolved.",
                "category": "title-blocked",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "The readiness review still contains blockers.",
                "required_action": "Resolve blockers before choosing a report title.",
            }
        ],
        "evidence_checklist": [
            {
                "text": "evidence_gaps=1",
                "category": "open-evidence-gap-count",
                "status": "missing-evidence-required",
                "source": "packet_counts",
                "reason": "Bundle contains open evidence gaps.",
                "required_action": "Close evidence gaps.",
            }
        ],
        "reproduction_plan_placeholders": [
            {
                "text": "Reproduction plan blocked until all blockers are resolved.",
                "category": "reproduction-plan-placeholder",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "Readiness review contains blockers.",
                "required_action": "Resolve blockers before writing reproduction steps.",
            }
        ],
        "impact_wording_guardrails": [
            {
                "text": "Do not claim practical impact until local evidence demonstrates it.",
                "category": "impact-wording-guardrail",
                "status": "guardrail",
                "source": "report_guardrails",
                "reason": "Impact must be evidence-based.",
                "required_action": "Tie every impact sentence to local proof.",
            }
        ],
        "severity_wording_guardrails": [
            {
                "text": "Do not state High/Critical severity while blockers remain open.",
                "category": "severity-wording-guardrail",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "Open blockers prevent reliable severity wording.",
                "required_action": "Resolve blockers before writing severity.",
            }
        ],
        "blocked_claims": [
            {
                "text": "unsafe_or_rejected_items=1",
                "category": "unsafe-or-rejected-items-present",
                "status": "blocked-claim",
                "source": "packet_counts",
                "reason": "Bundle contains unsafe or rejected items.",
                "required_action": "Keep unsafe/rejected items blocked.",
            }
        ],
        "do_not_claim_yet": [
            {
                "text": "Do not claim the finding is confirmed until all blockers are resolved.",
                "category": "global-do-not-claim-yet",
                "status": "blocked",
                "source": "report_readiness_review",
                "reason": "One or more readiness blockers remain open.",
                "required_action": "Resolve every blocker and re-run readiness review.",
            }
        ],
        "final_human_writing_checklist": ["Confirm no report was generated or submitted by Blackhole."],
        "safety": {
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "network_interaction": False,
            "target_mutation": False,
            "tool_execution": False,
            "browser_execution": False,
            "llm_provider_calls": False,
            "provider_execution": False,
            "vulnerability_confirmation": False,
        },
    }


def _clean_packet():
    return {
        "kind": "result_evidence_report_readiness_finding_draft_packet",
        "recommendation": "ready-for-human-written-draft-packet",
        "title_candidates": [
            {
                "text": "Human-reviewed finding draft: approved_planning_updates=1",
                "category": "title-candidate",
                "status": "human-write-required",
                "source": "packet_counts",
                "reason": "Built from a report-ready support note.",
                "required_action": "Human must rewrite title to match confirmed local evidence.",
            }
        ],
        "evidence_checklist": [
            {
                "text": "Attach local evidence for: approved_planning_updates=1",
                "category": "evidence-checklist",
                "status": "review-note",
                "source": "packet_counts",
                "reason": "Support note requires local evidence.",
                "required_action": "Map this note to concrete local evidence before drafting.",
            }
        ],
        "reproduction_plan_placeholders": [
            {
                "text": "Placeholder: write manual reproduction steps from verified local evidence only.",
                "category": "reproduction-plan-placeholder",
                "status": "human-write-required",
                "source": "report_ready_support_notes",
                "reason": "Steps must be written by a human.",
                "required_action": "Add verified requests, responses, and evidence.",
            }
        ],
        "impact_wording_guardrails": [
            {
                "text": "Do not claim practical impact until local evidence demonstrates it.",
                "category": "impact-wording-guardrail",
                "status": "guardrail",
                "source": "report_guardrails",
                "reason": "Impact must be evidence-based.",
                "required_action": "Tie every impact sentence to local proof.",
            }
        ],
        "severity_wording_guardrails": [
            {
                "text": "Do not assign severity until exploitability and impact are proven locally.",
                "category": "severity-wording-guardrail",
                "status": "guardrail",
                "source": "report_guardrails",
                "reason": "Severity must follow evidence.",
                "required_action": "Use conservative severity wording.",
            }
        ],
        "blocked_claims": [],
        "do_not_claim_yet": [],
        "final_human_writing_checklist": ["Have a human perform final report wording."],
        "safety": {
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "network_interaction": False,
            "target_mutation": False,
            "tool_execution": False,
            "browser_execution": False,
            "llm_provider_calls": False,
            "provider_execution": False,
            "vulnerability_confirmation": False,
        },
    }


def test_build_finding_draft_packet_review_gate_flags_blockers():
    gate = build_finding_draft_packet_review_gate(_blocked_packet())
    data = gate.to_dict()

    assert data["kind"] == "result_evidence_finding_draft_packet_review_gate"
    assert data["recommendation"] == "do-not-use-for-report-writing-resolve-blocked-claims"
    assert len(data["title_quality_findings"]) >= 1
    assert len(data["evidence_checklist_findings"]) >= 1
    assert len(data["reproduction_gap_findings"]) >= 1
    assert len(data["blocked_claim_findings"]) == 1
    assert len(data["do_not_claim_findings"]) == 1
    assert data["approved_writing_support"] == []
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_finding_draft_packet_review_gate_markdown_is_readable():
    gate = build_finding_draft_packet_review_gate(_blocked_packet())
    markdown = gate.to_markdown()

    assert "# Finding Draft Packet Review Gate" in markdown
    assert "Title Quality Findings" in markdown
    assert "Evidence Checklist Findings" in markdown
    assert "Do-Not-Claim Findings" in markdown
    assert "Do not treat this review as a generated report." in markdown
    assert "\\n" not in markdown


def test_finding_draft_packet_review_gate_clean_packet_is_writing_support_only():
    gate = build_finding_draft_packet_review_gate(_clean_packet())
    data = gate.to_dict()

    assert data["recommendation"] == "safe-as-human-writing-support-only"
    assert data["title_quality_findings"] == []
    assert data["blocked_claim_findings"] == []
    assert data["do_not_claim_findings"] == []
    assert len(data["approved_writing_support"]) >= 2


def test_finding_draft_packet_review_gate_safety_blocker_wins():
    bad = _clean_packet()
    bad["safety"]["report_generation"] = True

    gate = build_finding_draft_packet_review_gate(bad)
    data = gate.to_dict()

    assert data["recommendation"] == "do-not-use-packet-fix-safety-metadata"
    assert len(data["safety_findings"]) == 1
    assert data["safety_findings"][0]["subject"] == "report_generation"


def test_finding_draft_packet_review_gate_requires_kind():
    with pytest.raises(ValueError):
        build_finding_draft_packet_review_gate({"kind": "wrong"})


def test_finding_draft_packet_review_gate_requires_lists():
    bad = {
        "kind": "result_evidence_report_readiness_finding_draft_packet",
        "title_candidates": [],
        "evidence_checklist": [],
        "reproduction_plan_placeholders": [],
        "impact_wording_guardrails": [],
        "severity_wording_guardrails": [],
        "blocked_claims": [],
    }

    with pytest.raises(ValueError):
        build_finding_draft_packet_review_gate(bad)
