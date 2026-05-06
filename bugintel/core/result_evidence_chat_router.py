"""
Chat context router for Blackhole AI Workbench result evidence artifacts.

This module inspects a local JSON artifact and returns deterministic routing
guidance: artifact kind, supported question styles, recommended next command,
and safe next actions. It is local-only and planning-only. It does not call LLM
providers, send requests, execute tools, launch browsers, use Kali tools,
mutate targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatContextRoute:
    artifact_kind: str
    artifact_label: str
    recommended_command: str
    supported_questions: tuple[str, ...]
    next_actions: tuple[str, ...]
    source: str = "result-evidence-chat-context-router"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_chat_context_route",
            "source": self.source,
            "artifact_kind": self.artifact_kind,
            "artifact_label": self.artifact_label,
            "recommended_command": self.recommended_command,
            "supported_questions": list(self.supported_questions),
            "next_actions": list(self.next_actions),
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

    def to_markdown(self, title: str = "Chat Context Route") -> str:
        lines: list[str] = []

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Artifact")
        lines.append("")
        lines.append(f"- Kind: `{self.artifact_kind}`")
        lines.append(f"- Label: {self.artifact_label}")
        lines.append(f"- Recommended command: `{self.recommended_command}`")
        lines.append("")
        lines.append("## Supported Questions")
        lines.append("")
        for question in self.supported_questions:
            lines.append(f"- {question}")
        lines.append("")
        lines.append("## Safe Next Actions")
        lines.append("")
        for action in self.next_actions:
            lines.append(f"- {action}")
        lines.append("")
        lines.append("## Safety")
        lines.append("")
        lines.append("- Local-only artifact routing.")
        lines.append("- Planning-only output.")
        lines.append("- No LLM provider calls.")
        lines.append("- No target interaction.")
        lines.append("- No vulnerability confirmation.")
        lines.append("")

        return "\n".join(lines)


def route_chat_context(
    artifact: dict[str, Any],
    source: str = "result-evidence-chat-context-router",
) -> ChatContextRoute:
    """Route a local result evidence artifact to the best chat/review command."""
    if not isinstance(artifact, dict):
        raise ValueError("chat context router artifact must be an object")

    artifact_kind = str(artifact.get("kind") or "").strip()
    if not artifact_kind:
        raise ValueError("chat context router requires an artifact kind")

    if artifact_kind == "result_evidence_case_summary":
        return ChatContextRoute(
            artifact_kind=artifact_kind,
            artifact_label="Case intelligence summary",
            recommended_command="case-chat-context",
            supported_questions=(
                "what should I test next?",
                "what is strongest?",
                "what is weak?",
                "what evidence is missing?",
                "is this ready to report?",
                "what should I not claim?",
            ),
            next_actions=(
                "Run result-evidence-priority-ranking to rank candidates.",
                "Run case-chat-context for local research questions.",
                "Run result-evidence-review-report or case-report-assistant after validation.",
            ),
            source=source,
        )

    if artifact_kind == "result_evidence_priority_ranking":
        return ChatContextRoute(
            artifact_kind=artifact_kind,
            artifact_label="Priority ranking",
            recommended_command="result-evidence-multi-agent-review",
            supported_questions=(
                "which candidate is highest priority?",
                "which candidates should I ignore?",
                "why is this ranked first?",
                "what should I review next?",
            ),
            next_actions=(
                "Run result-evidence-multi-agent-review for specialist review tasks.",
                "Use --exclude-low-priority if you want to focus on stronger candidates.",
                "Use the top candidate as the starting point for case-chat-context.",
            ),
            source=source,
        )

    if artifact_kind == "result_evidence_multi_agent_review_plan":
        return ChatContextRoute(
            artifact_kind=artifact_kind,
            artifact_label="Multi-agent review plan",
            recommended_command="case-chat-context",
            supported_questions=(
                "what do reviewers think?",
                "which reviewer should I start with?",
                "what risk flags matter?",
                "what should be fixed before reporting?",
            ),
            next_actions=(
                "Start with authz-reviewer and false-positive-reviewer.",
                "Use evidence-reviewer to close raw evidence and redaction gaps.",
                "Use report-reviewer before final submission.",
            ),
            source=source,
        )

    if artifact_kind == "result_evidence_report_assistant":
        return ChatContextRoute(
            artifact_kind=artifact_kind,
            artifact_label="Case-to-report assistant draft",
            recommended_command="case-chat-context",
            supported_questions=(
                "what should the final report focus on?",
                "is this ready to report?",
                "what should I not claim?",
                "what title should I use?",
            ),
            next_actions=(
                "Manually validate all baselines before using the draft.",
                "Use impact wording guardrails before final report writing.",
                "Do not submit until scope, evidence, and impact are confirmed.",
            ),
            source=source,
        )

    if artifact_kind == "result_evidence_case_chat_session":
        return ChatContextRoute(
            artifact_kind=artifact_kind,
            artifact_label="Local case-chat session memory",
            recommended_command="case-chat-context",
            supported_questions=(
                "summarize chat memory",
                "what did I ask before?",
                "what endpoints have been cited?",
                "what next actions remain open?",
            ),
            next_actions=(
                "Continue using case-chat or case-chat-context with --session-file.",
                "Review accumulated next actions before more testing.",
                "Use session memory only as planning context, not proof.",
            ),
            source=source,
        )

    return ChatContextRoute(
        artifact_kind=artifact_kind,
        artifact_label="Unknown or unsupported artifact",
        recommended_command="manual-review",
        supported_questions=(
            "what kind of artifact is this?",
            "is this supported by the router?",
        ),
        next_actions=(
            "Check the artifact kind field.",
            "Use a supported result evidence artifact for local chat routing.",
            "Do not treat unsupported artifacts as vulnerability evidence.",
        ),
        source=source,
    )
