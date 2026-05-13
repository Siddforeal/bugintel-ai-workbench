import pytest

from bugintel.core.result_evidence_human_report_skeleton_review_gate import (
    build_human_report_skeleton_review_gate,
)


def _section(
    name,
    status="human-write-required",
    placeholder="[Human writes from verified evidence only.]",
    source_items=None,
    guidance=None,
):
    return {
        "name": name,
        "status": status,
        "purpose": f"{name} section purpose.",
        "placeholder": placeholder,
        "guidance": guidance or ["Use local evidence only."],
        "source_items": source_items or [],
    }


def _blocked_skeleton():
    return {
        "kind": "result_evidence_human_report_skeleton_packet",
        "recommendation": "skeleton-built-but-report-writing-blocked",
        "summary": _section(
            "Summary",
            status="blocked-until-review-complete",
            source_items=["Title blocked until report-readiness blockers are resolved."],
        ),
        "impact": _section(
            "Impact",
            status="blocked-until-impact-evidence",
            guidance=["Do not claim practical impact without local evidence."],
            source_items=["unsafe_or_rejected_items=1"],
        ),
        "steps_to_reproduce": _section(
            "Steps to Reproduce",
            status="blocked-until-reproduction-verified",
            source_items=["Reproduction plan blocked until all blockers are resolved."],
        ),
        "evidence": _section(
            "Evidence",
            status="blocked-until-evidence-complete",
            source_items=["evidence_gaps=1"],
        ),
        "affected_assets": _section(
            "Affected Assets",
            status="human-write-required",
            source_items=[],
        ),
        "severity_rationale": _section(
            "Severity Rationale",
            status="blocked-until-severity-evidence",
            guidance=["Do not state High/Critical unless evidence supports it."],
            source_items=["severity blocked"],
        ),
        "remediation": _section(
            "Remediation",
            status="human-write-required",
            source_items=[],
        ),
        "blocked_claims_do_not_claim": _section(
            "Blocked Claims / Do Not Claim",
            status="open-blockers",
            source_items=["Do not claim the finding is confirmed until all blockers are resolved."],
        ),
        "human_final_writing_checklist": [
            "Confirm this packet is a skeleton only, not a final report."
        ],
        "safety": {
            "local_only": True,
            "planning_only": True,
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
            "final_report": False,
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


def _clean_skeleton():
    return {
        "kind": "result_evidence_human_report_skeleton_packet",
        "recommendation": "ready-as-human-report-skeleton-only",
        "summary": _section("Summary", source_items=["title candidates"]),
        "impact": _section(
            "Impact",
            guidance=["Tie every impact sentence to local proof."],
            source_items=[],
        ),
        "steps_to_reproduce": _section(
            "Steps to Reproduce",
            source_items=["reproduction placeholders"],
        ),
        "evidence": _section(
            "Evidence",
            source_items=["evidence checklist"],
        ),
        "affected_assets": _section("Affected Assets", source_items=["title candidates"]),
        "severity_rationale": _section(
            "Severity Rationale",
            guidance=["Use conservative severity wording."],
            source_items=[],
        ),
        "remediation": _section("Remediation", source_items=[]),
        "blocked_claims_do_not_claim": _section(
            "Blocked Claims / Do Not Claim",
            status="none-open",
            source_items=[],
        ),
        "human_final_writing_checklist": [
            "Have a human write and review the final report wording."
        ],
        "safety": {
            "local_only": True,
            "planning_only": True,
            "human_approval_required": True,
            "report_generation": False,
            "report_submission": False,
            "final_report": False,
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


def test_build_human_report_skeleton_review_gate_flags_blockers():
    gate = build_human_report_skeleton_review_gate(_blocked_skeleton())
    data = gate.to_dict()

    assert data["kind"] == "result_evidence_human_report_skeleton_review_gate"
    assert data["recommendation"] == "do-not-use-skeleton-resolve-blockers"
    assert len(data["blocker_leakage_findings"]) >= 1
    assert len(data["blocked_do_not_claim_findings"]) >= 1
    assert len(data["approved_skeleton_sections"]) >= 1
    assert data["safety"]["final_report"] is False
    assert data["safety"]["report_generation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_human_report_skeleton_review_gate_markdown_is_readable():
    gate = build_human_report_skeleton_review_gate(_blocked_skeleton())
    markdown = gate.to_markdown()

    assert "# Human Report Skeleton Review Gate" in markdown
    assert "Section Completeness Findings" in markdown
    assert "Blocked / Do-Not-Claim Findings" in markdown
    assert "Approved Skeleton Sections" in markdown
    assert "Do not treat this review as a final report." in markdown
    assert "\\n" not in markdown


def test_human_report_skeleton_review_gate_clean_skeleton_is_safe_scaffold():
    gate = build_human_report_skeleton_review_gate(_clean_skeleton())
    data = gate.to_dict()

    assert data["recommendation"] == "safe-as-human-report-skeleton-only"
    assert data["section_completeness_findings"] == []
    assert data["blocker_leakage_findings"] == []
    assert data["blocked_do_not_claim_findings"] == []
    assert len(data["approved_skeleton_sections"]) >= 6


def test_human_report_skeleton_review_gate_safety_blocker_wins():
    bad = _clean_skeleton()
    bad["safety"]["report_generation"] = True

    gate = build_human_report_skeleton_review_gate(bad)
    data = gate.to_dict()

    assert data["recommendation"] == "do-not-use-skeleton-fix-safety-metadata"
    assert len(data["safety_findings"]) == 1
    assert data["safety_findings"][0]["subject"] == "report_generation"


def test_human_report_skeleton_review_gate_requires_kind():
    with pytest.raises(ValueError):
        build_human_report_skeleton_review_gate({"kind": "wrong"})


def test_human_report_skeleton_review_gate_requires_sections():
    bad = _clean_skeleton()
    del bad["summary"]

    with pytest.raises(ValueError):
        build_human_report_skeleton_review_gate(bad)
