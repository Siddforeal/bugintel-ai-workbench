"""
Deterministic brain chat for Blackhole AI Workbench.

This module reads existing planning artifacts from a state directory and creates
a local, non-provider chat reply. It does not call LLM providers, send requests,
execute shell commands, launch browsers, use Kali tools, mutate targets, or
bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class BrainChatReply:
    question: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    decision: str
    approval_status: str
    execution_gate: str
    execution_allowed: bool
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_brain_chat_reply(question: str, state_dir: Path) -> BrainChatReply:
    brain = _read_json(state_dir / "03-ai-brain.json")
    decision = _read_json(state_dir / "06-brain-decision.json")
    approval = _read_json(state_dir / "07-brain-approval.json")
    gate = _read_json(state_dir / "09-tool-execution-gate.json")

    focus = _first_focus_item(brain)

    target_name = str(
        brain.get("target_name")
        or decision.get("target_name")
        or approval.get("target_name")
        or gate.get("target_name")
        or "unknown-target"
    )

    focus_endpoint = (
        focus.get("endpoint")
        or decision.get("focus_endpoint")
        or approval.get("focus_endpoint")
        or gate.get("focus_endpoint")
    )
    focus_endpoint = str(focus_endpoint) if focus_endpoint else None

    decision_value = str(decision.get("decision") or "unknown")
    approval_status = str(approval.get("approval_status") or "unknown")
    execution_gate = str(gate.get("gate_decision") or "unknown")
    execution_allowed = bool(gate.get("execution_allowed", False))

    answer = _answer_question(
        question=question,
        target_name=target_name,
        focus=focus,
        decision=decision_value,
        approval_status=approval_status,
        execution_gate=execution_gate,
        execution_allowed=execution_allowed,
    )

    return BrainChatReply(
        question=question,
        answer=answer,
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        decision=decision_value,
        approval_status=approval_status,
        execution_gate=execution_gate,
        execution_allowed=execution_allowed,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _first_focus_item(brain: dict[str, Any]) -> dict[str, Any]:
    queue = brain.get("focus_queue") or []
    if queue and isinstance(queue[0], dict):
        return queue[0]
    return {}



def _route_question(q: str) -> str:
    """Route natural brain-chat questions to deterministic local answer types."""
    normalized = " ".join(q.replace("’", "'").split())

    if normalized in {"hello", "hi", "hey", "yo"}:
        return "hello"

    if any(term in normalized for term in ("execute", "run", "curl", "browser", "kali", "shell", "send request")):
        return "execute"

    if any(term in normalized for term in ("reportable", "submit", "can we report", "ready to report", "valid finding")):
        return "reportable"

    if any(term in normalized for term in ("approval", "approve", "human approval", "missing approval")):
        return "approvals"

    if any(term in normalized for term in ("blocking", "blocked", "can't test", "cant test", "cannot test", "why can't", "why cant", "what is stopping", "validation blocked")):
        return "blockers"

    if any(term in normalized for term in ("evidence", "artifact", "proof", "what do we need", "need to collect")):
        return "evidence"

    if any(term in normalized for term in ("what should i test first", "test first", "start with", "highest priority", "which endpoint", "priority endpoint")):
        return "focus"

    if "why" in normalized or "focus" in normalized:
        return "focus"

    if "status" in normalized or "where" in normalized:
        return "status"

    if "next" in normalized or "what should we do" in normalized:
        return "next"

    return "help"

def _answer_question(
    question: str,
    target_name: str,
    focus: dict[str, Any],
    decision: str,
    approval_status: str,
    execution_gate: str,
    execution_allowed: bool,
) -> str:
    q = question.strip().lower()
    route = _route_question(q)
    endpoint = str(focus.get("endpoint") or "none")
    band = str(focus.get("priority_band") or "unknown")
    score = str(focus.get("priority_score") or 0)
    reason = str(focus.get("reason") or "No focus reason is available.")

    if route == "hello":
        return "\n".join(
            [
                "Hello Sidd. I am Blackhole AI Workbench.",
                "",
                "Current mode: planning-only, human-in-the-loop, scope-safe.",
                f"Target: {target_name}",
                f"Recommended focus endpoint: {endpoint}",
                f"Priority: {band} / {score}",
                f"Current decision: {decision}",
                f"Approval status: {approval_status}",
                f"Execution gate: {execution_gate}",
                f"Execution allowed: {execution_allowed}",
                "",
                "I can help plan the next safe validation step, but I will not execute curl, browser, Kali, network, shell, or LLM-provider actions.",
            ]
        )

    if route == "status":
        return "\n".join(
            [
                f"Target `{target_name}` is loaded.",
                f"Current focus endpoint is `{endpoint}` with priority `{band}/{score}`.",
                f"Decision is `{decision}`.",
                f"Approval status is `{approval_status}`.",
                f"Execution gate is `{execution_gate}`.",
                f"Execution allowed is `{execution_allowed}`.",
            ]
        )

    if route == "next":
        return "\n".join(
            [
                "Next safe step:",
                "",
                "1. Confirm scope and authorization.",
                "2. Confirm controlled accounts, objects, tenants, projects, or files.",
                "3. Confirm redaction plan.",
                "4. Confirm non-destructive validation.",
                "5. Keep execution disabled until a future explicit human-approved execution layer exists.",
            ]
        )

    if route == "focus":
        return "\n".join(
            [
                f"Blackhole is focusing on `{endpoint}`.",
                f"Reason: {reason}",
                f"Priority: `{band}/{score}`.",
                "This is not a confirmed vulnerability. It is only a planning signal.",
            ]
        )

    if route == "blockers":
        return "\n".join(
            [
                "Validation is currently blocked.",
                f"Decision: `{decision}`.",
                f"Approval status: `{approval_status}`.",
                f"Execution gate: `{execution_gate}`.",
                f"Execution allowed: `{execution_allowed}`.",
                "",
                "You need scope confirmation, controlled accounts/objects, human approval, redaction review, and non-destructive validation approval before active testing.",
            ]
        )

    if route == "approvals":
        return "\n".join(
            [
                "Approvals still required before validation:",
                "",
                "- Confirm program scope and authorization.",
                "- Confirm controlled test accounts, tenants, projects, files, or objects.",
                "- Approve evidence collection.",
                "- Confirm redaction plan.",
                "- Confirm non-destructive validation.",
                "",
                f"Current approval status: `{approval_status}`.",
            ]
        )

    if route == "evidence":
        return "\n".join(
            [
                f"For `{endpoint}`, collect evidence only after authorization and approval.",
                "",
                "Useful evidence types:",
                "- scope and authorization proof",
                "- baseline request/response sample",
                "- redaction checklist",
                "- controlled account / role / object matrix",
                "- authorization decision diff",
                "- identifier source map",
                "- owned / foreign / random response matrix",
                "",
                "This is not evidence collection. It is only a planning checklist.",
            ]
        )

    if route == "reportable":
        return "\n".join(
            [
                "This is not reportable yet.",
                f"Current decision: `{decision}`.",
                f"Approval status: `{approval_status}`.",
                "No vulnerability is confirmed from planning state alone.",
                "A report needs local validation evidence, impact proof, redaction, and human review.",
            ]
        )

    if route == "execute":
        return "\n".join(
            [
                "Execution is not allowed from brain-chat.",
                f"Execution gate: `{execution_gate}`.",
                f"Execution allowed: `{execution_allowed}`.",
                "Blackhole can only provide planning guidance until a future explicit human-approved execution layer exists.",
            ]
        )

    return "\n".join(
        [
            "I can answer planning-only questions from the current brain state.",
            "",
            "Try:",
            "- hello",
            "- status",
            "- what should we do next?",
            "- why this endpoint?",
            "- what is blocking validation?",
            "- what approvals are missing?",
            "- what evidence do we need?",
            "- can we execute?",
            "- is this reportable?",
        ]
    )
