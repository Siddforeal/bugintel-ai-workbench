"""
Case timeline builder for Blackhole AI Workbench.

This module builds a local, planning-only timeline from Blackhole case artifacts.
It does not call LLM providers, send requests, execute shell commands, launch
browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class CaseTimelineEvent:
    order: int
    event_type: str
    title: str
    source_file: str
    summary: str
    status: str = "recorded"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaseTimeline:
    target_name: str
    event_count: int
    events: tuple[CaseTimelineEvent, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "event_count": self.event_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "events": [event.to_dict() for event in self.events],
            "markdown": render_case_timeline_markdown(self),
        }


ARTIFACT_ORDER = (
    ("01-orchestration.json", "orchestration", "Orchestration plan created"),
    ("02-research-state.json", "research-state", "Research state created"),
    ("03-ai-brain.json", "ai-brain", "AI brain plan created"),
    ("04-brain-prompt.json", "brain-prompt", "Brain prompt package created"),
    ("05-brain-review.json", "brain-review", "Brain review created"),
    ("06-brain-decision.json", "brain-decision", "Brain decision gate created"),
    ("07-brain-approval.json", "brain-approval", "Human approval packet created"),
    ("08-tool-request-manifest.json", "tool-request-manifest", "Tool request manifest created"),
    ("09-tool-execution-gate.json", "tool-execution-gate", "Tool execution gate created"),
    ("brain-chat-session.json", "brain-chat-session", "Brain chat session recorded"),
    ("research-state-update.json", "research-state-update", "Research state update planned"),
    ("research-state-apply-result.json", "research-state-apply", "Research state update applied to local copy"),
)


def build_case_timeline(case_dir: Path) -> CaseTimeline:
    """Build a timeline from known Blackhole case artifacts in a local directory."""
    events: list[CaseTimelineEvent] = []

    for order, (filename, event_type, title) in enumerate(ARTIFACT_ORDER, start=1):
        path = case_dir / filename
        if not path.exists():
            continue

        data = _read_json(path)
        events.append(
            CaseTimelineEvent(
                order=len(events) + 1,
                event_type=event_type,
                title=title,
                source_file=str(path),
                summary=_summary_for_event(event_type, data),
            )
        )

    target_name = _target_from_events(events)
    return CaseTimeline(
        target_name=target_name,
        event_count=len(events),
        events=tuple(events),
    )


def render_case_timeline_markdown(timeline: CaseTimeline) -> str:
    """Render a case timeline as Markdown."""
    lines = [
        f"# Blackhole Case Timeline: {timeline.target_name}",
        "",
        "> Local planning-only timeline. No tools are executed.",
        "",
        f"- Target: `{timeline.target_name}`",
        f"- Events: `{timeline.event_count}`",
        f"- Execution state: `{timeline.execution_state}`",
        "",
        "## Timeline",
        "",
        "| # | Type | Title | Summary |",
        "|---:|---|---|---|",
    ]

    for event in timeline.events:
        lines.append(
            f"| {event.order} | `{event.event_type}` | {event.title} | {event.summary} |"
        )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This timeline is generated from local case artifacts only.",
            "It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _summary_for_event(event_type: str, data: dict[str, Any]) -> str:
    if event_type == "orchestration":
        return f"Endpoints: {len(data.get('endpoints') or [])}; assignments: {len(data.get('assignments') or [])}."

    if event_type == "research-state":
        return f"Endpoints in memory: {data.get('endpoint_count', 0)}; decisions: {len(data.get('decisions') or [])}."

    if event_type == "ai-brain":
        return f"Focus items: {len(data.get('focus_queue') or [])}; safety gates: {len(data.get('safety_gates') or [])}."

    if event_type == "brain-prompt":
        return f"Messages: {data.get('message_count', 0)}; focus endpoint: {data.get('focus_endpoint') or 'none'}."

    if event_type == "brain-review":
        return f"Sections: {len(data.get('sections') or [])}; focus endpoint: {data.get('focus_endpoint') or 'none'}."

    if event_type == "brain-decision":
        return f"Decision: {data.get('decision', 'unknown')}; reportable: {data.get('reportable', False)}."

    if event_type == "brain-approval":
        return f"Approval status: {data.get('approval_status', 'unknown')}; required: {data.get('approval_required', False)}."

    if event_type == "tool-request-manifest":
        return f"Tool requests: {len(data.get('requests') or [])}; execution allowed: {data.get('execution_allowed', False)}."

    if event_type == "tool-execution-gate":
        return f"Gate decision: {data.get('gate_decision', 'unknown')}; execution allowed: {data.get('execution_allowed', False)}."

    if event_type == "brain-chat-session":
        return f"Chat turns: {data.get('turn_count', 0)}."

    if event_type == "research-state-update":
        return f"Validation result: {data.get('validation_result', 'unknown')}; actions: {len(data.get('actions') or [])}."

    if event_type == "research-state-apply":
        return f"Applied patches: {len(data.get('applied_patches') or [])}; result: {data.get('validation_result', 'unknown')}."

    return "Artifact recorded."


def _target_from_events(events: list[CaseTimelineEvent]) -> str:
    for event in events:
        summary = event.summary
        # target is not encoded in the summary consistently; read from source as fallback
        try:
            data = _read_json(Path(event.source_file))
        except Exception:
            continue
        target = data.get("target_name")
        if target:
            return str(target)
    return "unknown-target"
