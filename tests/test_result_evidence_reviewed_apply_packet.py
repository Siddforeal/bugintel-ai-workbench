import pytest

from bugintel.core.result_evidence_reviewed_apply_packet import build_reviewed_apply_packet


def _apply_preview_review():
    return {
        "kind": "result_evidence_action_plan_apply_preview_review",
        "recommendation": "do-not-apply-review-unsafe-items",
        "duplicate_update_candidates": [
            {
                "category": "duplicate-existing-case-memory-action",
                "severity": "low",
                "message": "Candidate appears to already exist in case memory.",
                "action": "Validate own-object baseline.",
                "source": "case_memory",
                "evidence_needed": [],
            }
        ],
        "blocked_action_findings": [
            {
                "category": "blocked-update",
                "severity": "medium",
                "message": "Update is blocked and must not be applied automatically.",
                "action": "Check admin role behavior.",
                "source": "block_until_local_evidence_exists",
                "evidence_needed": ["Admin account baseline"],
            }
        ],
        "evidence_gap_findings": [
            {
                "category": "missing-evidence",
                "severity": "medium",
                "message": "Missing evidence must be closed before any report or future apply step.",
                "action": "Impact proof",
                "source": "missing_evidence",
                "evidence_needed": ["Impact proof"],
            }
        ],
        "unsafe_update_findings": [
            {
                "category": "unsafe-or-rejected-update-risk",
                "severity": "high",
                "message": "Candidate contains unsafe, rejected, or execution-like wording.",
                "action": "Run unsafe command.",
                "source": "block_rejected_or_unsafe_action",
                "evidence_needed": ["Manual safety review"],
            }
        ],
        "overclaim_risks": [
            {
                "category": "report-overclaim-risk",
                "severity": "medium",
                "message": "Missing evidence creates report overclaim risk.",
                "action": "missing evidence remains open",
                "source": "missing_evidence",
                "evidence_needed": ["Impact proof"],
            }
        ],
        "safe_planning_notes": [
            {
                "category": "safe-planning-note",
                "severity": "info",
                "message": "Candidate can be kept as a manual planning note after human review.",
                "action": "Validate own-object baseline.",
                "source": "case_memory",
                "evidence_needed": [],
            },
            {
                "category": "safe-planning-note",
                "severity": "info",
                "message": "Candidate can be kept as a manual planning note after human review.",
                "action": "Add manual baseline validation note.",
                "source": "case_memory",
                "evidence_needed": [],
            },
        ],
        "report_guardrails": ["Do not claim a vulnerability from apply preview candidates."],
        "safety": {
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "vulnerability_confirmation": False,
        },
    }


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "manual_next_actions": ["Validate own-object baseline."],
    }


def test_build_reviewed_apply_packet_splits_approval_sections():
    packet = build_reviewed_apply_packet(_apply_preview_review(), case_memory=_case_memory())
    data = packet.to_dict()

    assert data["kind"] == "result_evidence_reviewed_apply_packet"
    assert data["recommendation"] == "human-approval-required-block-unsafe-items"
    assert len(data["approved_planning_updates"]) == 1
    assert data["approved_planning_updates"][0]["action"] == "Add manual baseline validation note."
    assert len(data["duplicate_updates"]) >= 1
    assert len(data["blocked_updates"]) == 1
    assert len(data["evidence_gaps"]) == 1
    assert len(data["unsafe_or_rejected_items"]) == 1
    assert len(data["overclaim_risks"]) == 1
    assert data["safety"]["human_approval_required"] is True
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["case_memory_write"] is False
    assert data["safety"]["research_state_write"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_reviewed_apply_packet_markdown_is_readable():
    packet = build_reviewed_apply_packet(_apply_preview_review(), case_memory=_case_memory())
    markdown = packet.to_markdown()

    assert "# Reviewed Apply Packet" in markdown
    assert "Approved Planning-Note Updates" in markdown
    assert "Duplicate Updates" in markdown
    assert "Unsafe / Rejected Items" in markdown
    assert "Human Approval Checklist" in markdown
    assert "Do not write case memory from this packet." in markdown
    assert "\\n" not in markdown


def test_reviewed_apply_packet_clean_review_ready_for_human_approval():
    clean = {
        "kind": "result_evidence_action_plan_apply_preview_review",
        "duplicate_update_candidates": [],
        "blocked_action_findings": [],
        "evidence_gap_findings": [],
        "unsafe_update_findings": [],
        "overclaim_risks": [],
        "safe_planning_notes": [
            {
                "category": "safe-planning-note",
                "severity": "info",
                "message": "Candidate can be kept as a manual planning note after human review.",
                "action": "Add manual baseline validation note.",
                "source": "case_memory",
                "evidence_needed": [],
            }
        ],
        "report_guardrails": [],
        "safety": {
            "vulnerability_confirmation": False,
        },
    }

    packet = build_reviewed_apply_packet(clean)
    data = packet.to_dict()

    assert data["recommendation"] == "ready-for-human-approval-as-planning-notes"
    assert len(data["approved_planning_updates"]) == 1
    assert data["duplicate_updates"] == []
    assert data["blocked_updates"] == []
    assert data["unsafe_or_rejected_items"] == []


def test_reviewed_apply_packet_requires_review_kind():
    with pytest.raises(ValueError):
        build_reviewed_apply_packet({"kind": "wrong"})


def test_reviewed_apply_packet_requires_case_memory_kind():
    with pytest.raises(ValueError):
        build_reviewed_apply_packet(
            _apply_preview_review(),
            case_memory={"kind": "wrong"},
        )


def test_reviewed_apply_packet_requires_lists():
    bad = {
        "kind": "result_evidence_action_plan_apply_preview_review",
        "duplicate_update_candidates": [],
        "blocked_action_findings": [],
        "evidence_gap_findings": [],
        "unsafe_update_findings": [],
        "overclaim_risks": [],
    }

    with pytest.raises(ValueError):
        build_reviewed_apply_packet(bad)


def test_reviewed_apply_packet_rejects_safe_note_without_action():
    bad = {
        "kind": "result_evidence_action_plan_apply_preview_review",
        "duplicate_update_candidates": [],
        "blocked_action_findings": [],
        "evidence_gap_findings": [],
        "unsafe_update_findings": [],
        "overclaim_risks": [],
        "safe_planning_notes": [{"category": "safe-planning-note"}],
    }

    with pytest.raises(ValueError):
        build_reviewed_apply_packet(bad)
