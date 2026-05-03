"""
Case summary builder for Blackhole AI Workbench.

This module builds a local, planning-only case summary from case timeline JSON.
It does not call LLM providers, send requests, execute shell commands, launch
browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CaseSummary:
    target_name: str
    event_count: int
    current_state: str
    key_points: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "event_count": self.event_count,
            "current_state": self.current_state,
            "key_points": list(self.key_points),
            "recommended_next_steps": list(self.recommended_next_steps),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_case_summary_markdown(self),
        }


def build_case_summary(timeline_data: dict[str, Any]) -> CaseSummary:
    """Build a concise case summary from case timeline JSON."""
    target_name = str(timeline_data.get("target_name") or "unknown-target")
    events = list(timeline_data.get("events") or [])

    event_types = {str(event.get("event_type")) for event in events}

    return CaseSummary(
        target_name=target_name,
        event_count=len(events),
        current_state=_current_state(event_types, events),
        key_points=tuple(_key_points(event_types, events)),
        recommended_next_steps=tuple(_recommended_next_steps(event_types, events)),
    )


def render_case_summary_markdown(summary: CaseSummary) -> str:
    """Render a case summary as Markdown."""
    lines = [
        f"# Blackhole Case Summary: {summary.target_name}",
        "",
        "> Local planning-only case summary. No tools are executed.",
        "",
        f"- Target: `{summary.target_name}`",
        f"- Timeline events: `{summary.event_count}`",
        f"- Current state: `{summary.current_state}`",
        f"- Execution state: `{summary.execution_state}`",
        "",
        "## Key Points",
        "",
    ]

    for point in summary.key_points:
        lines.append(f"- {point}")

    lines.extend(["", "## Recommended Next Steps", ""])

    for step in summary.recommended_next_steps:
        lines.append(f"- [ ] {step}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This summary is generated from local planning artifacts only.",
            "It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _current_state(event_types: set[str], events: list[dict[str, Any]]) -> str:
    if "tool-execution-gate" in event_types:
        return "execution-gated"
    if "tool-request-manifest" in event_types:
        return "tool-requests-planned"
    if "brain-approval" in event_types:
        return "approval-required"
    if "brain-decision" in event_types:
        return "decision-gated"
    if "brain-review" in event_types:
        return "reasoning-reviewed"
    if "ai-brain" in event_types:
        return "brain-planned"
    if "research-state" in event_types:
        return "case-memory-created"
    if "orchestration" in event_types:
        return "orchestrated"
    return "empty"


def _key_points(event_types: set[str], events: list[dict[str, Any]]) -> list[str]:
    points: list[str] = []

    if "orchestration" in event_types:
        points.append("Orchestration was created from discovered or supplied endpoints.")

    if "research-state" in event_types:
        points.append("Research state / case memory was created.")

    if "ai-brain" in event_types:
        points.append("AI brain planning generated a focus queue and safety gates.")

    if "brain-review" in event_types:
        points.append("Brain review generated a planning-only reasoning draft.")

    if "brain-decision" in event_types:
        points.append("Brain decision gate evaluated blockers and reportability.")

    if "brain-approval" in event_types:
        points.append("Human approval packet was created before any future validation.")

    if "tool-request-manifest" in event_types:
        points.append("Tool request manifest was prepared with execution disabled.")

    if "tool-execution-gate" in event_types:
        points.append("Tool execution gate kept execution disabled.")

    if "research-state-apply" in event_types:
        points.append("Research state update was applied to a local copy.")

    if not points:
        points.append("No Blackhole case artifacts were present.")

    return points


def _recommended_next_steps(event_types: set[str], events: list[dict[str, Any]]) -> list[str]:
    if "tool-execution-gate" in event_types:
        return [
            "Review execution gate blockers.",
            "Confirm scope, controlled assets, redaction, and non-destructive mode.",
            "Keep execution disabled until an explicit future execution layer exists.",
        ]

    if "brain-approval" in event_types:
        return [
            "Review approval packet.",
            "Resolve scope, controlled account, redaction, and approval items.",
            "Do not execute tools from the approval packet.",
        ]

    if "brain-decision" in event_types:
        return [
            "Review decision blockers.",
            "Prepare an approval packet before any future validation.",
            "Keep reportability false until manually validated evidence exists.",
        ]

    if "brain-review" in event_types:
        return [
            "Review the recommended focus endpoint.",
            "Check evidence artifacts and stop conditions.",
            "Generate a decision gate before validation.",
        ]

    if "research-state" in event_types:
        return [
            "Generate an AI brain plan from research state.",
            "Review focus queue and hypotheses.",
        ]

    if "orchestration" in event_types:
        return [
            "Generate research state / case memory.",
            "Review endpoint priorities and attack-surface groups.",
        ]

    return ["Create an orchestration plan first."]
