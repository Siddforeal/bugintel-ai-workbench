"""
Export bundle builder for reviewed apply packets.

This module turns a v0.63 reviewed apply packet into a local export bundle
manifest. It summarizes the packet, references included local artifacts, and
keeps safety metadata for human review.

It does not write case memory, write research state, call providers, execute
tools, launch browsers, send network requests, mutate targets, or confirm
vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReviewedApplyPacketBundleArtifact:
    path: str
    role: str
    exists: bool
    size_bytes: int
    sha256: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "note": self.note,
        }


@dataclass(frozen=True)
class ReviewedApplyPacketExportBundle:
    bundle_id: str
    recommendation: str
    packet_recommendation: str
    packet_counts: dict[str, int]
    included_artifacts: tuple[ReviewedApplyPacketBundleArtifact, ...]
    human_review_checklist: tuple[str, ...]
    report_guardrails: tuple[str, ...]
    source: str = "result-evidence-reviewed-apply-packet-export-bundle"
    planning_only: bool = True
    export_state: str = "manifest_built_not_applied"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_reviewed_apply_packet_export_bundle",
            "source": self.source,
            "bundle_id": self.bundle_id,
            "recommendation": self.recommendation,
            "packet_recommendation": self.packet_recommendation,
            "packet_counts": dict(self.packet_counts),
            "included_artifacts": [artifact.to_dict() for artifact in self.included_artifacts],
            "human_review_checklist": list(self.human_review_checklist),
            "report_guardrails": list(self.report_guardrails),
            "planning_only": self.planning_only,
            "export_state": self.export_state,
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

    def to_markdown(self, title: str = "Reviewed Apply Packet Export Bundle") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Bundle ID: {self.bundle_id}",
            f"- Recommendation: {self.recommendation}",
            f"- Packet recommendation: {self.packet_recommendation}",
            f"- Export state: {self.export_state}",
            "- Human approval required: true",
            "- State mutation performed by Blackhole: false",
            "- Case memory write: false",
            "- Research state write: false",
            "- Vulnerability confirmation: false",
            "- Planning-only: true",
            "",
            "## Packet Counts",
            "",
        ]

        for key, value in self.packet_counts.items():
            lines.append(f"- {key}: {value}")

        lines.extend(["", "## Included Artifacts", ""])

        if self.included_artifacts:
            for artifact in self.included_artifacts:
                lines.append(f"- **{artifact.role}**: {artifact.path}")
                lines.append(f"  - Exists: {str(artifact.exists).lower()}")
                lines.append(f"  - Size bytes: {artifact.size_bytes}")
                lines.append(f"  - SHA256: {artifact.sha256 or 'not available'}")
                if artifact.note:
                    lines.append(f"  - Note: {artifact.note}")
        else:
            lines.append("- none")

        lines.extend(["", "## Human Review Checklist", ""])
        for item in self.human_review_checklist:
            lines.append(f"- [ ] {item}")

        lines.extend(["", "## Report Guardrails", ""])
        if self.report_guardrails:
            for guardrail in self.report_guardrails:
                lines.append(f"- {guardrail}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This bundle is a local export manifest only.",
                "- Do not write case memory from this bundle.",
                "- Do not write research state from this bundle.",
                "- Do not treat bundled planning notes as vulnerability proof.",
                "- Do not apply unsafe, blocked, duplicate, or evidence-gap items automatically.",
                "",
            ]
        )

        return "\n".join(lines)


def build_reviewed_apply_packet_export_bundle(
    reviewed_apply_packet: dict[str, Any],
    artifact_refs: list[dict[str, Any]] | None = None,
    source: str = "result-evidence-reviewed-apply-packet-export-bundle",
) -> ReviewedApplyPacketExportBundle:
    """Build a local export bundle manifest from a reviewed apply packet."""
    _require_kind(
        reviewed_apply_packet,
        "result_evidence_reviewed_apply_packet",
        "reviewed apply packet",
    )

    approved = _object_list(reviewed_apply_packet.get("approved_planning_updates"), "approved_planning_updates")
    duplicates = _object_list(reviewed_apply_packet.get("duplicate_updates"), "duplicate_updates")
    blocked = _object_list(reviewed_apply_packet.get("blocked_updates"), "blocked_updates")
    evidence_gaps = _object_list(reviewed_apply_packet.get("evidence_gaps"), "evidence_gaps")
    unsafe = _object_list(reviewed_apply_packet.get("unsafe_or_rejected_items"), "unsafe_or_rejected_items")
    overclaims = _object_list(reviewed_apply_packet.get("overclaim_risks"), "overclaim_risks")

    packet_counts = {
        "approved_planning_updates": len(approved),
        "duplicate_updates": len(duplicates),
        "blocked_updates": len(blocked),
        "evidence_gaps": len(evidence_gaps),
        "unsafe_or_rejected_items": len(unsafe),
        "overclaim_risks": len(overclaims),
    }

    artifacts = tuple(_artifact_from_ref(ref) for ref in (artifact_refs or []))

    human_review_checklist = _dedupe(
        _string_list(reviewed_apply_packet.get("human_approval_checklist"))
        + [
            "Confirm the export bundle is used as review evidence only.",
            "Confirm no state file is written by this bundle step.",
            "Confirm included artifacts are local files intended for review.",
            "Confirm no vulnerability is marked as confirmed from this bundle.",
        ]
    )

    report_guardrails = _dedupe(
        _string_list(reviewed_apply_packet.get("report_guardrails"))
        + [
            "Export bundle does not mutate case memory or research state.",
            "Human approval is required before any future apply step.",
            "Bundled planning notes are not vulnerability proof.",
        ]
    )

    packet_recommendation = _optional_text(reviewed_apply_packet.get("recommendation"), "no-packet-recommendation")
    recommendation = _bundle_recommendation(packet_counts, artifacts)
    bundle_id = _bundle_id(packet_recommendation, packet_counts, artifacts)

    return ReviewedApplyPacketExportBundle(
        bundle_id=bundle_id,
        recommendation=recommendation,
        packet_recommendation=packet_recommendation,
        packet_counts=packet_counts,
        included_artifacts=artifacts,
        human_review_checklist=tuple(human_review_checklist),
        report_guardrails=tuple(report_guardrails),
        source=source,
    )


def build_bundle_artifact_from_path(
    path: Path,
    role: str = "supporting-artifact",
    note: str = "",
) -> ReviewedApplyPacketBundleArtifact:
    """Build a local artifact reference for the export bundle manifest."""
    exists = path.exists()
    is_file = path.is_file()
    size_bytes = path.stat().st_size if is_file else 0
    digest = _sha256_file(path) if is_file else ""

    return ReviewedApplyPacketBundleArtifact(
        path=str(path),
        role=role,
        exists=exists,
        size_bytes=size_bytes,
        sha256=digest,
        note=note,
    )


def _bundle_recommendation(
    packet_counts: dict[str, int],
    artifacts: tuple[ReviewedApplyPacketBundleArtifact, ...],
) -> str:
    if packet_counts["unsafe_or_rejected_items"]:
        return "export-for-human-review-block-unsafe-items"

    if packet_counts["blocked_updates"] or packet_counts["evidence_gaps"] or packet_counts["overclaim_risks"]:
        return "export-for-human-review-with-open-items"

    if packet_counts["duplicate_updates"]:
        return "export-for-human-review-after-deduplication"

    if packet_counts["approved_planning_updates"]:
        if artifacts:
            return "ready-to-export-reviewed-approval-bundle"
        return "ready-to-export-reviewed-packet-summary"

    return "export-empty-reviewed-packet-summary"


def _bundle_id(
    packet_recommendation: str,
    packet_counts: dict[str, int],
    artifacts: tuple[ReviewedApplyPacketBundleArtifact, ...],
) -> str:
    material = {
        "packet_recommendation": packet_recommendation,
        "packet_counts": packet_counts,
        "artifacts": [
            {
                "path": artifact.path,
                "role": artifact.role,
                "sha256": artifact.sha256,
                "size_bytes": artifact.size_bytes,
            }
            for artifact in artifacts
        ],
    }
    digest = sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
    return f"reviewed-apply-bundle-{digest[:12]}"


def _artifact_from_ref(ref: dict[str, Any]) -> ReviewedApplyPacketBundleArtifact:
    if not isinstance(ref, dict):
        raise ValueError("each artifact reference must be an object")

    path = _required_text(ref, "path", "artifact reference")
    return ReviewedApplyPacketBundleArtifact(
        path=path,
        role=_optional_text(ref.get("role"), "supporting-artifact"),
        exists=bool(ref.get("exists", False)),
        size_bytes=_int_value(ref.get("size_bytes")),
        sha256=_optional_text(ref.get("sha256"), ""),
        note=_optional_text(ref.get("note"), ""),
    )


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _object_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"reviewed apply packet requires {label} list")

    output: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"each {label} item must be an object")
        output.append(item)

    return output


def _required_text(data: dict[str, Any], key: str, label: str) -> str:
    value = str(data.get(key) or "").strip()
    if not value:
        raise ValueError(f"each {label} requires {key} text")
    return value


def _optional_text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _int_value(value: Any) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return 0
    return max(integer, 0)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        normalized = item.strip()
        if not normalized:
            continue

        key = normalized.lower()
        if key in seen:
            continue

        seen.add(key)
        output.append(normalized)

    return output
