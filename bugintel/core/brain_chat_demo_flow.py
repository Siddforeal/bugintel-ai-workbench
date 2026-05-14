"""
Brain chat demo flow builder.

This module runs the local planning-only demo chain from an endpoints file to a
ready-to-use brain-chat state directory.

It creates:
- orchestration.json
- research-state.json / research-state.md
- ai-brain.json
- brain-prompt.json
- brain-review.json
- brain-decision.json
- brain-approval.json
- tool-request-manifest.json
- tool-execution-gate.json
- brain state directory with 03/06/07/09 numbered files

It does not send network requests, execute tools, run curl, launch browsers,
call LLM providers, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.ai_brain import build_ai_brain_plan, render_ai_brain_plan_markdown
from bugintel.core.brain_approval import build_brain_approval_packet, render_brain_approval_packet_markdown
from bugintel.core.brain_decision import build_brain_decision_gate, render_brain_decision_gate_markdown
from bugintel.core.brain_prompt import build_brain_prompt_package, render_brain_prompt_package_markdown
from bugintel.core.brain_review import build_brain_review, render_brain_review_markdown
from bugintel.core.brain_state_export import build_brain_state_export
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration, render_research_state_markdown
from bugintel.core.task_tree import render_tree
from bugintel.core.tool_execution_gate import build_tool_execution_gate, render_tool_execution_gate_markdown
from bugintel.core.tool_request_manifest import build_tool_request_manifest, render_tool_request_manifest_markdown


@dataclass(frozen=True)
class BrainChatDemoFlowArtifact:
    role: str
    path: str
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "path": self.path,
            "exists": self.exists,
        }


@dataclass(frozen=True)
class BrainChatDemoFlow:
    target_name: str
    output_dir: str
    brain_state_dir: str
    focus_endpoint: str | None
    recommendation: str
    artifacts: tuple[BrainChatDemoFlowArtifact, ...]
    source: str = "brain-chat-demo-flow"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_demo_flow",
            "source": self.source,
            "target_name": self.target_name,
            "output_dir": self.output_dir,
            "brain_state_dir": self.brain_state_dir,
            "focus_endpoint": self.focus_endpoint,
            "recommendation": self.recommendation,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "curl_execution": False,
                "kali_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Demo Flow") -> str:
        lines = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Output directory: `{self.output_dir}`",
            f"- Brain state directory: `{self.brain_state_dir}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Recommendation: `{self.recommendation}`",
            "- Planning-only: true",
            "- Tool execution: false",
            "- Provider execution: false",
            "- Vulnerability confirmation: false",
            "",
            "## Artifacts",
            "",
        ]

        for artifact in self.artifacts:
            lines.append(f"- **{artifact.role}**: `{artifact.path}` exists=`{artifact.exists}`")

        lines.extend(
            [
                "",
                "## Next Step",
                "",
                "Use `brain-chat` with the exported brain state directory:",
                "",
                "```bash",
                f'blackhole brain-chat "What should I test first?" --state-dir {self.brain_state_dir}',
                "```",
                "",
                "## Safety",
                "",
                "- This command builds local planning artifacts only.",
                "- It does not execute tools, send requests, launch browsers, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def run_brain_chat_demo_flow(
    endpoints_file: Path,
    target_name: str,
    output_dir: Path,
    source: str = "brain-chat-demo-flow",
) -> BrainChatDemoFlow:
    """Run the local planning-only chain from endpoints.txt to brain-chat state."""
    if not endpoints_file.exists():
        raise ValueError(f"endpoints file not found: {endpoints_file}")

    output_dir.mkdir(parents=True, exist_ok=True)
    brain_state_dir = output_dir / "brain"

    endpoint_values = _endpoint_values_from_text(endpoints_file.read_text(encoding="utf-8", errors="replace"))

    orchestration = create_orchestration_plan(target_name=target_name, endpoints=endpoint_values)
    orchestration_data = orchestration.to_dict()
    _write_json(output_dir / "orchestration.json", orchestration_data)
    (output_dir / "orchestration-tree.txt").write_text(render_tree(orchestration.root) + "\n", encoding="utf-8")

    research_state = build_research_state_from_orchestration(orchestration_data)
    research_state_data = research_state.to_dict()
    _write_json(output_dir / "research-state.json", research_state_data)
    (output_dir / "research-state.md").write_text(render_research_state_markdown(research_state) + "\n", encoding="utf-8")

    ai_brain = build_ai_brain_plan(research_state_data)
    ai_brain_data = ai_brain.to_dict()
    _write_json(output_dir / "ai-brain.json", ai_brain_data)
    (output_dir / "ai-brain.md").write_text(render_ai_brain_plan_markdown(ai_brain) + "\n", encoding="utf-8")

    brain_prompt = build_brain_prompt_package(ai_brain_data)
    brain_prompt_data = brain_prompt.to_dict()
    _write_json(output_dir / "brain-prompt.json", brain_prompt_data)
    (output_dir / "brain-prompt.md").write_text(render_brain_prompt_package_markdown(brain_prompt) + "\n", encoding="utf-8")

    brain_review = build_brain_review(brain_prompt_data)
    brain_review_data = brain_review.to_dict()
    _write_json(output_dir / "brain-review.json", brain_review_data)
    (output_dir / "brain-review.md").write_text(render_brain_review_markdown(brain_review) + "\n", encoding="utf-8")

    brain_decision = build_brain_decision_gate(brain_review_data)
    brain_decision_data = brain_decision.to_dict()
    _write_json(output_dir / "brain-decision.json", brain_decision_data)
    (output_dir / "brain-decision.md").write_text(render_brain_decision_gate_markdown(brain_decision) + "\n", encoding="utf-8")

    brain_approval = build_brain_approval_packet(brain_decision_data)
    brain_approval_data = brain_approval.to_dict()
    _write_json(output_dir / "brain-approval.json", brain_approval_data)
    (output_dir / "brain-approval.md").write_text(render_brain_approval_packet_markdown(brain_approval) + "\n", encoding="utf-8")

    tool_manifest = build_tool_request_manifest(brain_approval_data)
    tool_manifest_data = tool_manifest.to_dict()
    _write_json(output_dir / "tool-request-manifest.json", tool_manifest_data)
    (output_dir / "tool-request-manifest.md").write_text(render_tool_request_manifest_markdown(tool_manifest) + "\n", encoding="utf-8")

    tool_gate = build_tool_execution_gate(tool_manifest_data)
    tool_gate_data = tool_gate.to_dict()
    _write_json(output_dir / "tool-execution-gate.json", tool_gate_data)
    (output_dir / "tool-execution-gate.md").write_text(render_tool_execution_gate_markdown(tool_gate) + "\n", encoding="utf-8")

    brain_export = build_brain_state_export(
        ai_brain=output_dir / "ai-brain.json",
        brain_decision=output_dir / "brain-decision.json",
        brain_approval=output_dir / "brain-approval.json",
        tool_execution_gate=output_dir / "tool-execution-gate.json",
        output_dir=brain_state_dir,
    )
    _write_json(output_dir / "brain-state-export.json", brain_export.to_dict())
    (output_dir / "brain-state-export.md").write_text(brain_export.to_markdown() + "\n", encoding="utf-8")

    artifacts = tuple(
        BrainChatDemoFlowArtifact(role=path.stem, path=str(path), exists=path.exists())
        for path in sorted(output_dir.glob("*"))
        if path.is_file()
    )

    focus_endpoint = _focus_endpoint(ai_brain_data)
    recommendation = "ready-for-brain-chat" if (brain_state_dir / "03-ai-brain.json").exists() else "demo-flow-incomplete"

    flow = BrainChatDemoFlow(
        target_name=target_name,
        output_dir=str(output_dir),
        brain_state_dir=str(brain_state_dir),
        focus_endpoint=focus_endpoint,
        recommendation=recommendation,
        artifacts=artifacts,
        source=source,
    )

    _write_json(output_dir / "brain-chat-demo-flow.json", flow.to_dict())
    (output_dir / "brain-chat-demo-flow.md").write_text(flow.to_markdown() + "\n", encoding="utf-8")

    return flow


def _endpoint_values_from_text(text: str) -> list[str]:
    endpoints: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        endpoints.append(line)

    return endpoints


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _focus_endpoint(ai_brain_data: dict[str, Any]) -> str | None:
    queue = ai_brain_data.get("focus_queue")
    if isinstance(queue, list) and queue and isinstance(queue[0], dict):
        endpoint = queue[0].get("endpoint")
        if endpoint:
            return str(endpoint)
    return None
