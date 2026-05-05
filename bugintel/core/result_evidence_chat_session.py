"""
Local case-chat session memory for Blackhole AI Workbench.

This module stores deterministic local research chat turns in a JSON session
file. It does not call LLM providers, send requests, execute tools, launch
browsers, use Kali tools, mutate targets, bypass authorization, or confirm
vulnerabilities automatically.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bugintel.core.result_evidence_chat import CaseChatAnswer


@dataclass(frozen=True)
class CaseChatSessionTurn:
    question: str
    answer: str
    intent: str
    cited_endpoints: tuple[str, ...]
    next_actions: tuple[str, ...]
    created_at: str
    source: str = "result-evidence-case-chat-session"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "intent": self.intent,
            "cited_endpoints": list(self.cited_endpoints),
            "next_actions": list(self.next_actions),
            "created_at": self.created_at,
            "source": self.source,
        }


@dataclass(frozen=True)
class CaseChatSession:
    turns: tuple[CaseChatSessionTurn, ...]
    source: str = "result-evidence-case-chat-session"
    kind: str = "result_evidence_case_chat_session"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        cited_endpoints: list[str] = []
        next_actions: list[str] = []
        intents: dict[str, int] = {}

        for turn in self.turns:
            cited_endpoints.extend(turn.cited_endpoints)
            next_actions.extend(turn.next_actions)
            intents[turn.intent] = intents.get(turn.intent, 0) + 1

        return {
            "kind": self.kind,
            "source": self.source,
            "turn_count": len(self.turns),
            "turns": [turn.to_dict() for turn in self.turns],
            "intents": intents,
            "cited_endpoints": _dedupe(cited_endpoints),
            "next_actions": _dedupe(next_actions),
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

    def summary_text(self) -> str:
        data = self.to_dict()

        if data["turn_count"] == 0:
            return "No local case-chat turns have been saved yet."

        endpoints = data["cited_endpoints"]
        actions = data["next_actions"]

        parts = [
            f"Saved local case-chat turns: {data['turn_count']}.",
            f"Observed intents: {data['intents']}.",
        ]

        if endpoints:
            parts.append(f"Cited endpoints: {', '.join(endpoints)}.")

        if actions:
            parts.append(f"Open next actions: {len(actions)}.")

        return " ".join(parts)


def empty_case_chat_session(source: str = "result-evidence-case-chat-session") -> CaseChatSession:
    return CaseChatSession(turns=(), source=source)


def load_case_chat_session(path: Path, source: str = "result-evidence-case-chat-session") -> CaseChatSession:
    """Load a local case-chat session JSON file. Missing files return an empty session."""
    if not path.exists():
        return empty_case_chat_session(source=source)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid case chat session JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("case chat session JSON must be an object")

    if data.get("kind") != "result_evidence_case_chat_session":
        raise ValueError("case chat session requires kind=result_evidence_case_chat_session")

    turns_data = data.get("turns")
    if not isinstance(turns_data, list):
        raise ValueError("case chat session requires a turns list")

    turns: list[CaseChatSessionTurn] = []

    for raw_turn in turns_data:
        if not isinstance(raw_turn, dict):
            raise ValueError("each case chat session turn must be an object")

        turns.append(
            CaseChatSessionTurn(
                question=str(raw_turn.get("question") or ""),
                answer=str(raw_turn.get("answer") or ""),
                intent=str(raw_turn.get("intent") or "general"),
                cited_endpoints=tuple(_string_list(raw_turn.get("cited_endpoints"))),
                next_actions=tuple(_string_list(raw_turn.get("next_actions"))),
                created_at=str(raw_turn.get("created_at") or ""),
                source=str(raw_turn.get("source") or source),
            )
        )

    return CaseChatSession(turns=tuple(turns), source=str(data.get("source") or source))


def append_case_chat_turn(
    session: CaseChatSession,
    answer: CaseChatAnswer,
    source: str = "result-evidence-case-chat-session",
) -> CaseChatSession:
    """Append a local case-chat answer to a session."""
    turn = CaseChatSessionTurn(
        question=answer.question,
        answer=answer.answer,
        intent=answer.intent,
        cited_endpoints=tuple(answer.cited_endpoints),
        next_actions=tuple(answer.next_actions),
        created_at=datetime.now(timezone.utc).isoformat(),
        source=source,
    )

    return CaseChatSession(turns=session.turns + (turn,), source=session.source)


def save_case_chat_session(path: Path, session: CaseChatSession) -> None:
    """Save a local case-chat session JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_case_chat_turn_to_file(path: Path, answer: CaseChatAnswer) -> CaseChatSession:
    """Load, append, save, and return a local case-chat session."""
    session = load_case_chat_session(path)
    updated = append_case_chat_turn(session, answer)
    save_case_chat_session(path, updated)
    return updated


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
