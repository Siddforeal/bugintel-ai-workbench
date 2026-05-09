import pytest

from bugintel.core.result_evidence_reviewed_apply_packet_export_bundle import (
    build_bundle_artifact_from_path,
    build_reviewed_apply_packet_export_bundle,
)


def _reviewed_apply_packet():
    return {
        "kind": "result_evidence_reviewed_apply_packet",
        "recommendation": "human-approval-required-block-unsafe-items",
        "approved_planning_updates": [
            {
                "action": "Add manual baseline validation note.",
                "status": "approved-planning-note",
                "source_category": "safe-planning-note",
                "source": "case_memory",
                "severity": "info",
                "reason": "Safe planning note.",
                "evidence_needed": [],
                "checklist": ["Confirm this remains a planning note only."],
            }
        ],
        "duplicate_updates": [],
        "blocked_updates": [
            {
                "action": "Check admin role behavior.",
                "status": "blocked-needs-review",
                "source_category": "blocked-update",
                "source": "block_until_local_evidence_exists",
                "severity": "medium",
                "reason": "Blocked item must not be applied automatically.",
                "evidence_needed": ["Admin account baseline"],
                "checklist": ["Close required local evidence before approval."],
            }
        ],
        "evidence_gaps": [
            {
                "action": "Impact proof",
                "status": "evidence-gap-open",
                "source_category": "missing-evidence",
                "source": "missing_evidence",
                "severity": "medium",
                "reason": "Evidence gap must be closed.",
                "evidence_needed": ["Impact proof"],
                "checklist": ["Collect local evidence."],
            }
        ],
        "unsafe_or_rejected_items": [
            {
                "action": "Run unsafe command.",
                "status": "unsafe-or-rejected",
                "source_category": "unsafe-or-rejected-update-risk",
                "source": "block_rejected_or_unsafe_action",
                "severity": "high",
                "reason": "Unsafe item must remain blocked.",
                "evidence_needed": ["Manual safety review"],
                "checklist": ["Do not apply this item automatically."],
            }
        ],
        "overclaim_risks": [],
        "report_guardrails": ["Approved planning notes are not vulnerability proof."],
        "human_approval_checklist": ["Confirm this packet is being used as planning input only."],
        "safety": {
            "human_approval_required": True,
            "state_mutation": False,
            "case_memory_write": False,
            "research_state_write": False,
            "vulnerability_confirmation": False,
        },
    }


def test_build_reviewed_apply_packet_export_bundle_summarizes_packet(tmp_path):
    artifact = tmp_path / "reviewed-apply-packet.json"
    artifact.write_text("packet evidence\n", encoding="utf-8")

    artifact_ref = build_bundle_artifact_from_path(artifact, role="reviewed-apply-packet").to_dict()
    bundle = build_reviewed_apply_packet_export_bundle(
        _reviewed_apply_packet(),
        artifact_refs=[artifact_ref],
    )
    data = bundle.to_dict()

    assert data["kind"] == "result_evidence_reviewed_apply_packet_export_bundle"
    assert data["bundle_id"].startswith("reviewed-apply-bundle-")
    assert data["recommendation"] == "export-for-human-review-block-unsafe-items"
    assert data["packet_counts"]["approved_planning_updates"] == 1
    assert data["packet_counts"]["blocked_updates"] == 1
    assert data["packet_counts"]["evidence_gaps"] == 1
    assert data["packet_counts"]["unsafe_or_rejected_items"] == 1
    assert len(data["included_artifacts"]) == 1
    assert data["included_artifacts"][0]["exists"] is True
    assert data["included_artifacts"][0]["sha256"]
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["case_memory_write"] is False
    assert data["safety"]["research_state_write"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_reviewed_apply_packet_export_bundle_markdown_is_readable(tmp_path):
    artifact = tmp_path / "packet.md"
    artifact.write_text("# Packet\n", encoding="utf-8")

    artifact_ref = build_bundle_artifact_from_path(artifact, role="packet-markdown").to_dict()
    bundle = build_reviewed_apply_packet_export_bundle(
        _reviewed_apply_packet(),
        artifact_refs=[artifact_ref],
    )
    markdown = bundle.to_markdown()

    assert "# Reviewed Apply Packet Export Bundle" in markdown
    assert "Packet Counts" in markdown
    assert "Included Artifacts" in markdown
    assert "Human Review Checklist" in markdown
    assert "Do not write case memory from this bundle." in markdown
    assert "\\n" not in markdown


def test_reviewed_apply_packet_export_bundle_clean_packet_ready_to_export():
    packet = _reviewed_apply_packet()
    packet["blocked_updates"] = []
    packet["evidence_gaps"] = []
    packet["unsafe_or_rejected_items"] = []
    packet["overclaim_risks"] = []
    packet["recommendation"] = "ready-for-human-approval-as-planning-notes"

    bundle = build_reviewed_apply_packet_export_bundle(packet)
    data = bundle.to_dict()

    assert data["recommendation"] == "ready-to-export-reviewed-packet-summary"
    assert data["packet_counts"]["approved_planning_updates"] == 1
    assert data["included_artifacts"] == []


def test_reviewed_apply_packet_export_bundle_requires_packet_kind():
    with pytest.raises(ValueError):
        build_reviewed_apply_packet_export_bundle({"kind": "wrong"})


def test_reviewed_apply_packet_export_bundle_requires_lists():
    bad = {
        "kind": "result_evidence_reviewed_apply_packet",
        "approved_planning_updates": [],
        "duplicate_updates": [],
        "blocked_updates": [],
        "evidence_gaps": [],
        "unsafe_or_rejected_items": [],
    }

    with pytest.raises(ValueError):
        build_reviewed_apply_packet_export_bundle(bad)


def test_reviewed_apply_packet_export_bundle_rejects_bad_artifact_ref():
    with pytest.raises(ValueError):
        build_reviewed_apply_packet_export_bundle(
            _reviewed_apply_packet(),
            artifact_refs=[{"role": "missing-path"}],
        )
