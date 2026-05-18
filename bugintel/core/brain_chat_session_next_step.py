"""
Brain chat session next-step planner.

This module turns a brain-chat session summary into a small deterministic
planning packet. It does not call providers, execute tools, send requests,
launch browsers, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_session import BrainChatSession, summarize_brain_chat_session


@dataclass(frozen=True)
class BrainChatSessionNextStepPlan:
    next_question: str
    current_focus_endpoint: str | None
    current_blocker: str
    next_evidence: tuple[str, ...]
    do_not_do_yet: tuple[str, ...]
    recommendation: str
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-session-next-step-plan"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_session_next_step_plan",
            "source": self.source,
            "recommendation": self.recommendation,
            "next_question": self.next_question,
            "current_focus_endpoint": self.current_focus_endpoint,
            "current_blocker": self.current_blocker,
            "next_evidence": list(self.next_evidence),
            "do_not_do_yet": list(self.do_not_do_yet),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Session Next-Step Plan") -> str:
        lines = [
            f"# {title}",
            "",
            "## Status",
            "",
            f"- Recommendation: `{self.recommendation}`",
            f"- Focus endpoint: `{self.current_focus_endpoint or 'none'}`",
            f"- Current blocker: `{self.current_blocker}`",
            f"- Next question: `{self.next_question}`",
            "- Planning-only: true",
            "- Tool execution: false",
            "- Provider execution: false",
            "- Vulnerability confirmation: false",
            "",
            "## Next Evidence",
            "",
        ]

        for item in self.next_evidence:
            lines.append(f"- {item}")

        lines.extend(["", "## Do Not Do Yet", ""])

        for item in self.do_not_do_yet:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This plan is local and planning-only.",
                "- It does not execute tools, send requests, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_chat_session_next_step_plan(
    session: BrainChatSession,
    source: str = "brain-chat-session-next-step-plan",
) -> BrainChatSessionNextStepPlan:
    summary = summarize_brain_chat_session(session)

    current_blocker = _current_blocker(summary.latest_decision, summary.latest_approval_status, summary.latest_execution_gate)
    next_evidence = _next_evidence(summary.latest_focus_endpoint)
    do_not_do = (
        "Do not run curl, browser, Kali, shell, or network actions from this planning step.",
        "Do not claim a confirmed vulnerability from planning state.",
        "Do not submit a report without local validation evidence, impact proof, redaction, and human review.",
    )

    recommendation = (
        "resolve-blockers-before-validation"
        if not summary.latest_execution_allowed
        else "collect-approved-evidence-next"
    )

    return BrainChatSessionNextStepPlan(
        next_question=summary.suggested_next_question,
        current_focus_endpoint=summary.latest_focus_endpoint,
        current_blocker=current_blocker,
        next_evidence=tuple(next_evidence),
        do_not_do_yet=do_not_do,
        recommendation=recommendation,
        source=source,
    )


def _current_blocker(decision: str, approval_status: str, execution_gate: str) -> str:
    if decision == "blocked-pending-scope-and-controls":
        return "Scope, controlled test objects/accounts, and human approval are still required."

    if approval_status.startswith("blocked"):
        return "Human approval is still required."

    if execution_gate.startswith("blocked"):
        return "Execution gate is still blocking tool/network actions."

    return "No blocker was detected in the latest session summary."


def _next_evidence(focus_endpoint: str | None) -> list[str]:
    endpoint = focus_endpoint or "current focus endpoint"
    return [
        f"Scope and authorization proof for `{endpoint}`",
        "Baseline request/response sample",
        "Redaction checklist",
        "Controlled account / role / object matrix",
        "Authorization decision diff",
        "Identifier source map",
        "Owned / foreign / random response matrix",
    ]
