"""
Brain chat session memory for Blackhole AI Workbench.

This module stores local deterministic brain-chat conversation turns. It does
not call LLM providers, send requests, execute shell commands, launch browsers,
use Kali tools, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from bugintel.core.brain_chat import BrainChatReply


@dataclass(frozen=True)
class BrainChatTurn:
    question: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    decision: str
    approval_status: str
    execution_gate: str
    execution_allowed: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainChatSession:
    turns: tuple[BrainChatTurn, ...] = field(default_factory=tuple)
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_count": len(self.turns),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "turns": [turn.to_dict() for turn in self.turns],
        }


@dataclass(frozen=True)
class BrainChatSessionSummary:
    turn_count: int
    latest_question: str | None
    latest_focus_endpoint: str | None
    latest_decision: str
    latest_approval_status: str
    latest_execution_gate: str
    latest_execution_allowed: bool
    repeated_questions: tuple[str, ...]
    suggested_next_question: str
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_count": self.turn_count,
            "latest_question": self.latest_question,
            "latest_focus_endpoint": self.latest_focus_endpoint,
            "latest_decision": self.latest_decision,
            "latest_approval_status": self.latest_approval_status,
            "latest_execution_gate": self.latest_execution_gate,
            "latest_execution_allowed": self.latest_execution_allowed,
            "repeated_questions": list(self.repeated_questions),
            "suggested_next_question": self.suggested_next_question,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


def load_brain_chat_session(path: Path) -> BrainChatSession:
    if not path.exists():
        return BrainChatSession()

    data = json.loads(path.read_text(encoding="utf-8"))
    turns = []

    for item in data.get("turns", []):
        turns.append(
            BrainChatTurn(
                question=str(item.get("question", "")),
                answer=str(item.get("answer", "")),
                target_name=str(item.get("target_name", "unknown-target")),
                focus_endpoint=item.get("focus_endpoint"),
                decision=str(item.get("decision", "unknown")),
                approval_status=str(item.get("approval_status", "unknown")),
                execution_gate=str(item.get("execution_gate", "unknown")),
                execution_allowed=bool(item.get("execution_allowed", False)),
                created_at=str(item.get("created_at", "")),
            )
        )

    return BrainChatSession(turns=tuple(turns))


def append_brain_chat_turn(session: BrainChatSession, reply: BrainChatReply) -> BrainChatSession:
    turn = BrainChatTurn(
        question=reply.question,
        answer=reply.answer,
        target_name=reply.target_name,
        focus_endpoint=reply.focus_endpoint,
        decision=reply.decision,
        approval_status=reply.approval_status,
        execution_gate=reply.execution_gate,
        execution_allowed=reply.execution_allowed,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return BrainChatSession(turns=session.turns + (turn,))


def save_brain_chat_session(session: BrainChatSession, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_brain_chat_session(session: BrainChatSession) -> BrainChatSessionSummary:
    latest = session.turns[-1] if session.turns else None
    repeated = _repeated_questions(session)

    return BrainChatSessionSummary(
        turn_count=len(session.turns),
        latest_question=latest.question if latest else None,
        latest_focus_endpoint=latest.focus_endpoint if latest else None,
        latest_decision=latest.decision if latest else "unknown",
        latest_approval_status=latest.approval_status if latest else "unknown",
        latest_execution_gate=latest.execution_gate if latest else "unknown",
        latest_execution_allowed=latest.execution_allowed if latest else False,
        repeated_questions=tuple(repeated),
        suggested_next_question=_suggest_next_question(latest, repeated),
        planning_only=session.planning_only,
        execution_state=session.execution_state,
    )


def _repeated_questions(session: BrainChatSession) -> list[str]:
    seen: dict[str, int] = {}
    display: dict[str, str] = {}

    for turn in session.turns:
        normalized = " ".join(turn.question.lower().split())
        if not normalized:
            continue

        seen[normalized] = seen.get(normalized, 0) + 1
        display.setdefault(normalized, turn.question)

    return [display[key] for key, count in seen.items() if count > 1]


def _suggest_next_question(latest: BrainChatTurn | None, repeated_questions: list[str]) -> str:
    if latest is None:
        return "What should I test first?"

    if latest.execution_allowed:
        return "What evidence should I collect next?"

    if latest.decision != "blocked-pending-scope-and-controls":
        return "What evidence do we need?"

    if repeated_questions:
        return "What is blocking validation?"

    return "What approvals are missing?"


def render_brain_chat_session_summary(session: BrainChatSession) -> str:
    summary = summarize_brain_chat_session(session)
    lines = [
        "# Blackhole Brain Chat Session",
        "",
        "## Summary",
        "",
        f"- Turns: `{summary.turn_count}`",
        f"- Execution state: `{summary.execution_state}`",
        f"- Latest question: `{summary.latest_question or 'none'}`",
        f"- Latest focus endpoint: `{summary.latest_focus_endpoint or 'none'}`",
        f"- Latest decision: `{summary.latest_decision}`",
        f"- Latest approval status: `{summary.latest_approval_status}`",
        f"- Latest execution gate: `{summary.latest_execution_gate}`",
        f"- Latest execution allowed: `{summary.latest_execution_allowed}`",
        f"- Suggested next question: `{summary.suggested_next_question}`",
        "",
        "## Repeated Questions",
        "",
    ]

    if summary.repeated_questions:
        for question in summary.repeated_questions:
            lines.append(f"- `{question}`")
    else:
        lines.append("- none")

    lines.append("")

    for index, turn in enumerate(session.turns, start=1):
        lines.append(f"## Turn {index}")
        lines.append("")
        lines.append(f"- Question: `{turn.question}`")
        lines.append(f"- Target: `{turn.target_name}`")
        lines.append(f"- Focus endpoint: `{turn.focus_endpoint or 'none'}`")
        lines.append(f"- Decision: `{turn.decision}`")
        lines.append(f"- Approval status: `{turn.approval_status}`")
        lines.append(f"- Execution gate: `{turn.execution_gate}`")
        lines.append(f"- Execution allowed: `{turn.execution_allowed}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
