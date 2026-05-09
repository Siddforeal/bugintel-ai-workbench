import pytest

from bugintel.core.result_evidence_export_bundle_review_gate import (
    build_export_bundle_review_gate,
)


GOOD_SHA = "a" * 64


def _export_bundle():
    return {
        "kind": "result_evidence_reviewed_apply_packet_export_bundle",
        "bundle_id": "reviewed-apply-bundle-test123",
        "recommendation": "export-for-human-review-block-unsafe-items",
        "packet_recommendation": "human-approval-required-block-unsafe-items",
        "packet_counts": {
            "approved_planning_updates": 1,
            "duplicate_updates": 1,
            "blocked_updates": 1,
            "evidence_gaps": 1,
            "unsafe_or_rejected_items": 1,
            "overclaim_risks": 1,
        },
        "included_artifacts": [
            {
                "path": "/tmp/packet.md",
                "role": "packet-markdown",
                "exists": True,
                "size_bytes": 100,
                "sha256": GOOD_SHA,
                "note": "",
            },
            {
                "path": "/tmp/missing.json",
                "role": "packet-json",
                "exists": False,
                "size_bytes": 0,
                "sha256": "",
                "note": "",
            },
            {
                "path": "/tmp/bad-hash.txt",
                "role": "bad-artifact",
                "exists": True,
                "size_bytes": 0,
                "sha256": "not-a-sha",
                "note": "",
            },
        ],
        "human_review_checklist": ["Confirm the export bundle is used as review evidence only."],
        "report_guardrails": ["Bundled planning notes are not vulnerability proof."],
        "safety": {
            "local_only": True,
            "planning_only": True,
            "human_approval_required": True,
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


def test_build_export_bundle_review_gate_flags_risks():
    gate = build_export_bundle_review_gate(_export_bundle())
    data = gate.to_dict()

    assert data["kind"] == "result_evidence_export_bundle_review_gate"
    assert data["recommendation"] == "do-not-use-bundle-until-artifacts-verified"
    assert len(data["missing_artifact_findings"]) == 1
    assert len(data["artifact_integrity_findings"]) == 2
    assert len(data["packet_risk_findings"]) == 3
    assert len(data["evidence_gap_findings"]) == 1
    assert len(data["overclaim_findings"]) == 1
    assert data["safety"]["state_mutation"] is False
    assert data["safety"]["case_memory_write"] is False
    assert data["safety"]["research_state_write"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_export_bundle_review_gate_markdown_is_readable():
    gate = build_export_bundle_review_gate(_export_bundle())
    markdown = gate.to_markdown()

    assert "# Export Bundle Review Gate" in markdown
    assert "Missing Artifacts" in markdown
    assert "Artifact Integrity Findings" in markdown
    assert "Packet Risk Findings" in markdown
    assert "Do not write case memory or research state from this review gate." in markdown
    assert "\\n" not in markdown


def test_export_bundle_review_gate_clean_bundle_is_review_only_safe():
    bundle = _export_bundle()
    bundle["packet_counts"] = {
        "approved_planning_updates": 1,
        "duplicate_updates": 0,
        "blocked_updates": 0,
        "evidence_gaps": 0,
        "unsafe_or_rejected_items": 0,
        "overclaim_risks": 0,
    }
    bundle["included_artifacts"] = [
        {
            "path": "/tmp/packet.md",
            "role": "packet-markdown",
            "exists": True,
            "size_bytes": 100,
            "sha256": GOOD_SHA,
            "note": "",
        }
    ]

    gate = build_export_bundle_review_gate(bundle)
    data = gate.to_dict()

    assert data["recommendation"] == "safe-as-review-package-only"
    assert data["missing_artifact_findings"] == []
    assert data["artifact_integrity_findings"] == []
    assert data["packet_risk_findings"] == []


def test_export_bundle_review_gate_requires_bundle_kind():
    with pytest.raises(ValueError):
        build_export_bundle_review_gate({"kind": "wrong"})


def test_export_bundle_review_gate_requires_packet_counts_object():
    bad = _export_bundle()
    bad["packet_counts"] = []

    with pytest.raises(ValueError):
        build_export_bundle_review_gate(bad)


def test_export_bundle_review_gate_requires_artifact_list():
    bad = _export_bundle()
    bad["included_artifacts"] = {}

    with pytest.raises(ValueError):
        build_export_bundle_review_gate(bad)


def test_export_bundle_review_gate_flags_bad_safety_metadata():
    bad = _export_bundle()
    bad["safety"]["tool_execution"] = True

    gate = build_export_bundle_review_gate(bad)
    data = gate.to_dict()

    assert data["recommendation"] == "do-not-use-bundle-until-safety-metadata-fixed"
    assert len(data["safety_findings"]) == 1
    assert data["safety_findings"][0]["subject"] == "tool_execution"
