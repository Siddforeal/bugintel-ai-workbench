"""
Result evidence finding package builder for Blackhole AI Workbench.

This module builds a local, planning-only finding package from result evidence
batch review JSON. It renders a candidate finding draft, a review report,
metadata, and a human validation checklist. It does not confirm vulnerabilities,
send requests, execute shell commands, launch browsers, use Kali tools, call LLM
providers, mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.result_evidence_finding_draft import render_result_evidence_finding_draft
from bugintel.core.result_evidence_report import render_result_evidence_review_report


@dataclass(frozen=True)
class ResultEvidenceFindingPackage:
    files: dict[str, str]
    metadata: dict[str, Any]
    source: str = "result-evidence-finding-package"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_finding_package",
            "source": self.source,
            "file_count": len(self.files),
            "files": self.files,
            "metadata": self.metadata,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
                "vulnerability_confirmation": False,
            },
        }


def build_result_evidence_finding_package(
    review_data: dict[str, Any],
    finding_title: str = "Candidate Finding Draft",
    include_all: bool = False,
    source: str = "result-evidence-finding-package",
) -> ResultEvidenceFindingPackage:
    """Build a local finding package from result evidence batch review JSON."""
    if not isinstance(review_data, dict):
        raise ValueError("result evidence review data must be an object")

    if review_data.get("kind") != "result_evidence_batch_review":
        raise ValueError("finding package requires kind=result_evidence_batch_review")

    items = review_data.get("items")
    if not isinstance(items, list):
        raise ValueError("finding package requires an items list")

    draft = render_result_evidence_finding_draft(
        review_data,
        title=finding_title,
        include_all=include_all,
        source="result-evidence-finding-package:draft",
    )
    report = render_result_evidence_review_report(
        review_data,
        title="Result Evidence Batch Review Report",
        source="result-evidence-finding-package:review-report",
    )

    selected_items = _selected_items(items, include_all=include_all)
    metadata = _build_metadata(review_data, selected_items, include_all=include_all)
    checklist = _render_submission_checklist(metadata)
    manifest = _render_manifest(metadata)

    files = {
        "finding-draft.md": draft.markdown,
        "review-report.md": report.markdown,
        "submission-checklist.md": checklist,
        "metadata.json": _json_dumps(metadata),
        "manifest.json": _json_dumps(manifest),
    }

    return ResultEvidenceFindingPackage(files=files, metadata=metadata, source=source)


def _selected_items(items: list[Any], include_all: bool) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each review item must be an object")

        if include_all or item.get("suggested_result") == "supported":
            endpoint = str(item.get("endpoint") or "").strip()
            if not endpoint:
                raise ValueError("each selected item requires an endpoint")
            selected.append(item)

    return selected


def _build_metadata(review_data: dict[str, Any], selected_items: list[dict[str, Any]], include_all: bool) -> dict[str, Any]:
    endpoints = [str(item.get("endpoint")) for item in selected_items]

    return {
        "kind": "result_evidence_finding_package_metadata",
        "review_kind": review_data.get("kind"),
        "total_reviewed_items": review_data.get("count", len(review_data.get("items", []))),
        "selected_item_count": len(selected_items),
        "include_all": include_all,
        "supported_count": review_data.get("supported_count", 0),
        "rejected_count": review_data.get("rejected_count", 0),
        "needs_more_evidence_count": review_data.get("needs_more_evidence_count", 0),
        "missing_expected_status_count": review_data.get("missing_expected_status_count", 0),
        "selected_endpoints": endpoints,
        "selected_sources": [str(item.get("source") or "unknown") for item in selected_items],
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": {
            "local_only": True,
            "planning_only": True,
            "network_interaction": False,
            "target_mutation": False,
            "tool_execution": False,
            "llm_provider_calls": False,
            "vulnerability_confirmation": False,
        },
    }


def _render_submission_checklist(metadata: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Submission Checklist")
    lines.append("")
    lines.append("## Package Status")
    lines.append("")
    lines.append("- This package is generated from local result evidence review JSON.")
    lines.append("- This package is planning-only.")
    lines.append("- This package does not confirm a vulnerability.")
    lines.append("- A human researcher must validate the finding before submission.")
    lines.append("")
    lines.append("## Selected Evidence")
    lines.append("")
    lines.append(f"- Selected evidence items: {metadata.get('selected_item_count', 0)}")
    lines.append(f"- Total reviewed items: {metadata.get('total_reviewed_items', 0)}")
    lines.append(f"- Supported candidates in review: {metadata.get('supported_count', 0)}")
    lines.append(f"- Rejected candidates in review: {metadata.get('rejected_count', 0)}")
    lines.append(f"- Needs-more-evidence candidates in review: {metadata.get('needs_more_evidence_count', 0)}")
    lines.append("")

    endpoints = metadata.get("selected_endpoints") or []
    if endpoints:
        lines.append("## Selected Endpoints")
        lines.append("")
        for endpoint in endpoints:
            lines.append(f"- `{endpoint}`")
        lines.append("")

    lines.append("## Required Manual Checks")
    lines.append("")
    lines.append("- Confirm the target and asset are in scope.")
    lines.append("- Confirm testing was performed only on authorized accounts, tenants, objects, or datasets.")
    lines.append("- Confirm own-account baseline behavior.")
    lines.append("- Confirm second-account or foreign-object behavior.")
    lines.append("- Confirm random/non-existent object behavior.")
    lines.append("- Confirm unauthenticated or expired-session behavior only when allowed by program rules.")
    lines.append("- Confirm whether returned data is sensitive, private, or tenant-specific.")
    lines.append("- Confirm the issue is reproducible and not cache/stale-data/test-data behavior.")
    lines.append("- Confirm there is a clear security boundary violation.")
    lines.append("- Confirm no secrets, cookies, tokens, or personal data are included in final submission.")
    lines.append("")
    lines.append("## Evidence Files To Attach Or Preserve")
    lines.append("")
    lines.append("- Raw HTTP request and response pairs.")
    lines.append("- Timestamped terminal output.")
    lines.append("- Screenshots where useful.")
    lines.append("- Account/object ownership notes.")
    lines.append("- Scope reference.")
    lines.append("- Redacted proof-of-concept steps.")
    lines.append("")
    lines.append("## Final Report Reminder")
    lines.append("")
    lines.append("- Use the finding draft as a starting point only.")
    lines.append("- Rewrite the final report manually.")
    lines.append("- Do not claim impact that was not directly proven.")
    lines.append("- Keep reproduction steps minimal, safe, and program-compliant.")
    lines.append("")
    lines.append("## Safety")
    lines.append("")
    lines.append("- Local-only artifact generation.")
    lines.append("- No network interaction.")
    lines.append("- No curl/browser/Kali/tool execution.")
    lines.append("- No target mutation.")
    lines.append("- No LLM provider calls.")
    lines.append("- No automatic vulnerability confirmation.")
    lines.append("")
    return "\n".join(lines)


def _render_manifest(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "result_evidence_finding_package_manifest",
        "files": [
            "finding-draft.md",
            "review-report.md",
            "submission-checklist.md",
            "metadata.json",
            "manifest.json",
        ],
        "metadata_kind": metadata.get("kind"),
        "selected_item_count": metadata.get("selected_item_count", 0),
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": metadata.get("safety", {}),
    }


def _json_dumps(data: dict[str, Any]) -> str:
    import json

    return json.dumps(data, indent=2, sort_keys=True) + "\n"
