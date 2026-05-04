"""
Result evidence review report renderer for Blackhole AI Workbench.

This module renders local, planning-only result evidence batch review JSON into
a human-readable Markdown report. It does not send requests, execute shell
commands, launch browsers, use Kali tools, call LLM providers, mutate targets,
bypass authorization, or confirm vulnerabilities automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResultEvidenceReviewReport:
    markdown: str
    source: str = "result-evidence-review-report"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_review_report",
            "source": self.source,
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
            },
        }


def render_result_evidence_review_report(
    review_data: dict[str, Any],
    title: str = "Result Evidence Batch Review Report",
    source: str = "result-evidence-review-report",
) -> ResultEvidenceReviewReport:
    """Render a planning-only Markdown report from result evidence batch review JSON."""
    if not isinstance(review_data, dict):
        raise ValueError("result evidence review data must be an object")

    if review_data.get("kind") != "result_evidence_batch_review":
        raise ValueError("result evidence review report requires kind=result_evidence_batch_review")

    items = review_data.get("items")
    if not isinstance(items, list):
        raise ValueError("result evidence review report requires an items list")

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total evidence items: {review_data.get('count', len(items))}")
    lines.append(f"- Supported candidates: {review_data.get('supported_count', 0)}")
    lines.append(f"- Rejected candidates: {review_data.get('rejected_count', 0)}")
    lines.append(f"- Needs more evidence: {review_data.get('needs_more_evidence_count', 0)}")
    lines.append(f"- Missing expected status: {review_data.get('missing_expected_status_count', 0)}")
    lines.append("")
    lines.append("## Safety")
    lines.append("")
    lines.append("- Local-only review artifact.")
    lines.append("- Planning-only output.")
    lines.append("- No network interaction.")
    lines.append("- No curl/browser/Kali/tool execution.")
    lines.append("- No target mutation.")
    lines.append("- No LLM provider calls.")
    lines.append("- No automatic vulnerability confirmation.")
    lines.append("")
    lines.append("## Evidence Items")
    lines.append("")

    if not items:
        lines.append("_No evidence items were present in the review._")
        lines.append("")
    else:
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError("each review item must be an object")

            endpoint = str(item.get("endpoint") or "").strip()
            if not endpoint:
                raise ValueError("each review item requires an endpoint")

            suggested_result = str(item.get("suggested_result") or "needs-more-evidence")
            confidence = str(item.get("confidence") or "unknown")
            source_label = str(item.get("source") or "unknown")
            observed_status = _display_value(item.get("observed_status"))
            expected_status = _display_value(item.get("expected_status"))
            signal_count = _display_value(item.get("signal_count"))
            rationale = str(item.get("rationale") or "").strip() or "No rationale provided."

            lines.append(f"### {index}. `{endpoint}`")
            lines.append("")
            lines.append(f"- Suggested result: **{suggested_result}**")
            lines.append(f"- Confidence: {confidence}")
            lines.append(f"- Source: `{source_label}`")
            lines.append(f"- Observed status: {observed_status}")
            lines.append(f"- Expected status: {expected_status}")
            lines.append(f"- Signal count: {signal_count}")
            lines.append(f"- Rationale: {rationale}")
            lines.append("")

    lines.append("## Recommended Human Review")
    lines.append("")
    lines.append("- Re-check every supported candidate manually before reporting.")
    lines.append("- Confirm authorization scope, account boundaries, and object ownership.")
    lines.append("- Compare own-object, foreign-object, random-object, and unauthenticated baselines.")
    lines.append("- Preserve raw request/response evidence separately.")
    lines.append("- Do not treat this report as a vulnerability confirmation by itself.")
    lines.append("")

    return ResultEvidenceReviewReport(markdown="\n".join(lines), source=source)


def _display_value(value: Any) -> str:
    if value is None:
        return "not provided"
    return str(value)
