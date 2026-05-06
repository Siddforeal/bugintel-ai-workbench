"""
Natural question intent normalization for Blackhole AI Workbench.

This module maps messy human research questions to deterministic local intents.
It does not call LLM providers, send requests, execute tools, launch browsers,
use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QuestionIntent:
    original_question: str
    normalized_question: str
    intent: str
    confidence: str
    matched_terms: tuple[str, ...]
    source: str = "result-evidence-question-intent"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_question_intent",
            "source": self.source,
            "original_question": self.original_question,
            "normalized_question": self.normalized_question,
            "intent": self.intent,
            "confidence": self.confidence,
            "matched_terms": list(self.matched_terms),
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


def normalize_question_intent(question: str, source: str = "result-evidence-question-intent") -> QuestionIntent:
    """Normalize a messy human research question into a deterministic local intent."""
    original = question
    normalized = _normalize_text(question)

    if not normalized:
        raise ValueError("question intent requires a non-empty question")

    rules = [
        (
            "next-tests",
            (
                "what should i test next",
                "what should i do now",
                "what do i do now",
                "next step",
                "next test",
                "test next",
                "what now",
                "where should i continue",
                "which command next",
                "what command should i run",
                "how to validate",
                "validation next",
            ),
        ),
        (
            "strongest",
            (
                "strongest",
                "best finding",
                "best candidate",
                "highest priority",
                "most important",
                "which one is valid",
                "which one is strongest",
                "top candidate",
                "best one",
                "strong report",
            ),
        ),
        (
            "weak",
            (
                "weak",
                "false positive",
                "false-positive",
                "rejected",
                "not reportable",
                "duplicate risk",
                "is this useless",
                "is this invalid",
                "which one should i ignore",
            ),
        ),
        (
            "report-ready",
            (
                "report ready",
                "ready to report",
                "ready for report",
                "can i submit",
                "should i submit",
                "is this reportable",
                "is it reportable",
                "can we report",
                "submit this",
                "submission ready",
                "valid bug",
                "valid vulnerability",
            ),
        ),
        (
            "missing-evidence",
            (
                "missing evidence",
                "what proof is missing",
                "what evidence is missing",
                "what is missing",
                "missing proof",
                "need proof",
                "need evidence",
                "what do we need",
                "what is blocking",
                "blocker",
                "blocked",
            ),
        ),
        (
            "do-not-claim",
            (
                "not claim",
                "do not claim",
                "dont claim",
                "don't claim",
                "avoid claiming",
                "overclaim",
                "what should i avoid",
                "what not to say",
                "what should i not say",
                "report wording risk",
            ),
        ),
        (
            "reviewers",
            (
                "reviewer",
                "reviewers",
                "agent",
                "agents",
                "multi agent",
                "multi-agent",
                "what do reviewers think",
                "what do agents think",
                "specialist review",
            ),
        ),
        (
            "final-report-focus",
            (
                "final report",
                "report focus",
                "focus on",
                "what should the report",
                "what should final report focus",
                "report title",
                "title should",
                "write report around",
            ),
        ),
        (
            "session-summary",
            (
                "session",
                "history",
                "previous question",
                "chat memory",
                "what did i ask",
                "what did we discuss",
                "summarize memory",
            ),
        ),
    ]

    best_intent = "general"
    best_matches: list[str] = []

    for intent, terms in rules:
        matches = [term for term in terms if term in normalized]
        if matches and len(matches) > len(best_matches):
            best_intent = intent
            best_matches = matches

    confidence = "medium" if best_matches else "low"

    # Small extra keyword fallback for very short user questions.
    if not best_matches:
        keyword_map = {
            "next": "next-tests",
            "strong": "strongest",
            "best": "strongest",
            "submit": "report-ready",
            "report": "report-ready",
            "missing": "missing-evidence",
            "proof": "missing-evidence",
            "claim": "do-not-claim",
            "reviewer": "reviewers",
            "agent": "reviewers",
            "memory": "session-summary",
        }

        for keyword, intent in keyword_map.items():
            if keyword in normalized.split():
                best_intent = intent
                best_matches = [keyword]
                confidence = "low-medium"
                break

    return QuestionIntent(
        original_question=original,
        normalized_question=normalized,
        intent=best_intent,
        confidence=confidence,
        matched_terms=tuple(best_matches),
        source=source,
    )


def _normalize_text(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9' -]+", " ", text)
    text = re.sub(r"\\s+", " ", text)
    return text.strip()
