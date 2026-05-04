"""
Result evidence finding draft renderer for Blackhole AI Workbench.

This module renders local result evidence batch review JSON into a candidate
finding draft for human review. It does not confirm vulnerabilities, send
requests, execute shell commands, launch browsers, use Kali tools, call LLM
providers, mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResultEvidenceFindingDraft:
    markdown: str
    selected_count: int
    source: str = "result-evidence-finding-draft"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_finding_draft",
            "source": self.source,
            "selected_count": self.selected_count,
            "markdown": self.markdown,
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


def render_result_evidence_finding_draft(
    review_data: dict[str, Any],
    title: str = "Candidate Finding Draft",
    include_all: bool = False,
    source: str = "result-evidence-finding-draft",
) -> ResultEvidenceFindingDraft:
    """Render a planning-only candidate finding draft from batch review JSON."""
    if not isinstance(review_data, dict):
        raise ValueError("result evidence review data must be an object")

    if review_data.get("kind") != "result_evidence_batch_review":
        raise ValueError("finding draft requires kind=result_evidence_batch_review")

    items = review_data.get("items")
    if not isinstance(items, list):
        raise ValueError("finding draft requires an items list")

    selected_items = _select_items(items, include_all=include_all)

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append("This is a **candidate finding draft** generated from local saved evidence.")
    lines.append("It is not a vulnerability confirmation. A human researcher must verify scope, authorization, reproducibility, and impact before reporting.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Source review kind: `{review_data.get('kind')}`")
    lines.append(f"- Total reviewed evidence items: {review_data.get('count', len(items))}")
    lines.append(f"- Selected evidence items in this draft: {len(selected_items)}")
    lines.append(f"- Supported candidates in review: {review_data.get('supported_count', 0)}")
    lines.append(f"- Rejected candidates in review: {review_data.get('rejected_count', 0)}")
    lines.append(f"- Needs-more-evidence candidates in review: {review_data.get('needs_more_evidence_count', 0)}")
    lines.append(f"- Missing expected status count: {review_data.get('missing_expected_status_count', 0)}")
    lines.append("")
    lines.append("## Candidate Title")
    lines.append("")
    lines.append("_Replace this with a precise, program-safe title after manual validation._")
    lines.append("")
    lines.append("Example format:")
    lines.append("")
    lines.append("> Improper Authorization Allows Access to Another User's Resource via `<endpoint>`")
    lines.append("")
    lines.append("## Candidate Description")
    lines.append("")
    lines.append("Based on the local evidence review, one or more observations may indicate behavior worth manual validation.")
    lines.append("The researcher should confirm whether the observed response differs from the expected authorization boundary and whether sensitive data or unauthorized state access is actually present.")
    lines.append("")
    lines.append("## Affected Evidence Items")
    lines.append("")

    if not selected_items:
        lines.append("_No supported evidence items were selected. Use `--include-all` if a broader draft is needed._")
        lines.append("")
    else:
        for index, item in enumerate(selected_items, start=1):
            endpoint = _required_text(item, "endpoint", "each selected item requires an endpoint")
            suggested_result = str(item.get("suggested_result") or "needs-more-evidence")
            confidence = str(item.get("confidence") or "unknown")
            source_label = str(item.get("source") or "unknown")
            observed_status = _display_value(item.get("observed_status"))
            expected_status = _display_value(item.get("expected_status"))
            signal_count = _display_value(item.get("signal_count"))
            rationale = str(item.get("rationale") or "").strip() or "No rationale provided."

            lines.append(f"### {index}. `{endpoint}`")
            lines.append("")
            lines.append(f"- Review suggestion: **{suggested_result}**")
            lines.append(f"- Confidence: {confidence}")
            lines.append(f"- Source: `{source_label}`")
            lines.append(f"- Observed status: {observed_status}")
            lines.append(f"- Expected status: {expected_status}")
            lines.append(f"- Signal count: {signal_count}")
            lines.append(f"- Review rationale: {rationale}")
            lines.append("")

    lines.append("## Manual Validation Checklist")
    lines.append("")
    lines.append("- Confirm the target, endpoint, and asset are in scope.")
    lines.append("- Reproduce with a controlled own-account baseline.")
    lines.append("- Reproduce with a controlled second account or authorized test object.")
    lines.append("- Compare against a random/non-existent object baseline.")
    lines.append("- Compare against an unauthenticated or expired-session baseline when allowed.")
    lines.append("- Confirm whether any returned data is sensitive, private, or tenant-specific.")
    lines.append("- Confirm whether the behavior is repeatable and not caused by cache, stale state, or test data.")
    lines.append("- Preserve raw HTTP requests, responses, timestamps, account IDs, object IDs, and screenshots separately.")
    lines.append("- Remove secrets, tokens, cookies, and personal data before submission.")
    lines.append("")
    lines.append("## Proof of Concept Draft")
    lines.append("")
    lines.append("1. Log in as the authorized baseline account and capture the expected own-object behavior.")
    lines.append("2. Log in as the second controlled account and attempt the same object/resource access.")
    lines.append("3. Compare observed status, response body, and object ownership indicators.")
    lines.append("4. Repeat using a random object ID to rule out generic behavior or false positives.")
    lines.append("5. Document only the minimum evidence needed to demonstrate the authorization boundary issue.")
    lines.append("")
    lines.append("## Impact Hypothesis")
    lines.append("")
    lines.append("_Replace this after manual validation._")
    lines.append("")
    lines.append("Potential impact may include unauthorized access to private account, project, object, or tenant data if the supported candidate is confirmed.")
    lines.append("Do not claim impact until the evidence proves the affected data type, attacker prerequisites, and authorization boundary.")
    lines.append("")
    lines.append("## Limitations / Open Questions")
    lines.append("")
    lines.append("- This draft was generated from local review JSON only.")
    lines.append("- The result is planning-only.")
    lines.append("- The evidence still requires human validation.")
    lines.append("- The generated draft does not prove exploitability by itself.")
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

    return ResultEvidenceFindingDraft(
        markdown="\n".join(lines),
        selected_count=len(selected_items),
        source=source,
    )


def _select_items(items: list[Any], include_all: bool) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each review item must be an object")

        if include_all or item.get("suggested_result") == "supported":
            selected.append(item)

    return selected


def _required_text(item: dict[str, Any], key: str, error: str) -> str:
    value = str(item.get(key) or "").strip()
    if not value:
        raise ValueError(error)
    return value


def _display_value(value: Any) -> str:
    if value is None:
        return "not provided"
    return str(value)
