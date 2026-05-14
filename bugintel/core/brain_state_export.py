"""
Brain state export builder for brain-chat.

This module copies generated Blackhole brain artifacts into the numbered file
layout expected by brain-chat:

03-ai-brain.json
06-brain-decision.json
07-brain-approval.json
09-tool-execution-gate.json

It does not execute tools, call providers, send requests, launch browsers,
mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EXPECTED_BRAIN_STATE_FILES = {
    "ai_brain": "03-ai-brain.json",
    "brain_decision": "06-brain-decision.json",
    "brain_approval": "07-brain-approval.json",
    "tool_execution_gate": "09-tool-execution-gate.json",
}


@dataclass(frozen=True)
class BrainStateExportItem:
    role: str
    source_path: str
    output_path: str
    exists: bool
    copied: bool
    target_name: str
    focus_endpoint: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "exists": self.exists,
            "copied": self.copied,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
        }


@dataclass(frozen=True)
class BrainStateExport:
    output_dir: str
    exported_items: tuple[BrainStateExportItem, ...]
    recommendation: str
    source: str = "brain-state-export"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_state_export",
            "source": self.source,
            "output_dir": self.output_dir,
            "recommendation": self.recommendation,
            "exported_items": [item.to_dict() for item in self.exported_items],
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "expected_files": dict(EXPECTED_BRAIN_STATE_FILES),
            "safety": {
                "local_only": True,
                "planning_only": True,
                "file_copy_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain State Export") -> str:
        lines = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Output directory: `{self.output_dir}`",
            f"- Recommendation: `{self.recommendation}`",
            "- File copy only: true",
            "- Tool execution: false",
            "- Provider execution: false",
            "- Vulnerability confirmation: false",
            "",
            "## Exported Files",
            "",
        ]

        for item in self.exported_items:
            lines.extend(
                [
                    f"- **{item.role}**",
                    f"  - Source: `{item.source_path}`",
                    f"  - Output: `{item.output_path}`",
                    f"  - Exists: `{item.exists}`",
                    f"  - Copied: `{item.copied}`",
                    f"  - Target: `{item.target_name}`",
                    f"  - Focus endpoint: `{item.focus_endpoint or 'none'}`",
                ]
            )

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This command only prepares a local brain-chat state directory.",
                "- It does not execute tools, send requests, launch browsers, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_state_export(
    ai_brain: Path,
    brain_decision: Path,
    brain_approval: Path,
    tool_execution_gate: Path,
    output_dir: Path,
    source: str = "brain-state-export",
) -> BrainStateExport:
    """Copy brain artifacts into the state-dir format expected by brain-chat."""
    sources = {
        "ai_brain": ai_brain,
        "brain_decision": brain_decision,
        "brain_approval": brain_approval,
        "tool_execution_gate": tool_execution_gate,
    }

    output_dir.mkdir(parents=True, exist_ok=True)

    exported: list[BrainStateExportItem] = []
    for role, source_path in sources.items():
        if not source_path.exists():
            raise ValueError(f"{role} JSON not found: {source_path}")

        data = _read_json_object(source_path, role)
        output_path = output_dir / EXPECTED_BRAIN_STATE_FILES[role]
        shutil.copyfile(source_path, output_path)

        exported.append(
            BrainStateExportItem(
                role=role,
                source_path=str(source_path),
                output_path=str(output_path),
                exists=output_path.exists(),
                copied=True,
                target_name=_target_name(data),
                focus_endpoint=_focus_endpoint(data),
            )
        )

    recommendation = (
        "ready-for-brain-chat"
        if all(item.exists and item.copied for item in exported)
        else "export-incomplete"
    )

    return BrainStateExport(
        output_dir=str(output_dir),
        exported_items=tuple(exported),
        recommendation=recommendation,
        source=source,
    )


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label} JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{label} JSON must be an object")

    return data


def _target_name(data: dict[str, Any]) -> str:
    return str(data.get("target_name") or data.get("target") or "unknown-target")


def _focus_endpoint(data: dict[str, Any]) -> str | None:
    value = data.get("focus_endpoint")
    if value:
        return str(value)

    queue = data.get("focus_queue")
    if isinstance(queue, list) and queue and isinstance(queue[0], dict):
        endpoint = queue[0].get("endpoint")
        if endpoint:
            return str(endpoint)

    return None
