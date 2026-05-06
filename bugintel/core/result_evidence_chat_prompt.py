"""
Safe LLM prompt package builder for result evidence case-chat artifacts.

This module builds a reviewable prompt package from local case memory and a
human question. It does not call LLM providers, read API keys, send requests,
execute tools, launch browsers, use Kali tools, mutate targets, bypass
authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from bugintel.core.llm_prompt import LLMPromptPackage, redact_prompt_text


@dataclass(frozen=True)
class CaseChatPromptPackage:
    prompt_package: LLMPromptPackage
    artifact_kinds: tuple[str, ...]
    question: str
    source: str = "result-evidence-case-chat-prompt"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_case_chat_prompt_package",
            "source": self.source,
            "question": self.question,
            "artifact_kinds": list(self.artifact_kinds),
            "prompt_package": self.prompt_package.to_dict(),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }


def build_case_chat_prompt_package(
    case_memory: dict[str, Any],
    question: str,
    grounded_answer: dict[str, Any] | None = None,
    source: str = "result-evidence-case-chat-prompt",
) -> CaseChatPromptPackage:
    """Build a safe reviewable prompt package from local case-chat artifacts."""
    _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    if grounded_answer is not None:
        _require_kind(grounded_answer, "result_evidence_grounded_answer", "grounded answer")

    question_text = question.strip()
    if not question_text:
        raise ValueError("case chat prompt package requires a non-empty question")

    artifact_kinds = ["result_evidence_case_memory"]
    if grounded_answer is not None:
        artifact_kinds.append("result_evidence_grounded_answer")

    system_prompt = """You are a cybersecurity research assistant for authorized testing only.

Rules:
- Use only the local artifacts included in this prompt.
- Do not invent evidence.
- Do not claim a vulnerability is confirmed unless the artifacts explicitly prove it.
- Recommend only safe, read-only, in-scope manual validation steps.
- Do not suggest credential theft, stealth, persistence, destructive actions, exfiltration, or bypassing authorization.
- Treat all output as planning guidance for a human researcher.
"""

    artifact_block = {
        "case_memory": case_memory,
        "grounded_answer": grounded_answer,
    }

    user_prompt = f"""Review this local Blackhole case-chat context.

Question:
{question_text}

Task:
- Answer the question using only the provided local artifacts.
- Cite relevant artifact fields by name.
- Identify missing evidence and unsafe claims.
- Suggest safe next manual validation steps.
- Keep the answer concise and do not overclaim.

Local artifacts JSON:
{json.dumps(artifact_block, indent=2, sort_keys=True)}
"""

    redacted_user_prompt, redaction_applied = redact_prompt_text(user_prompt)

    prompt = LLMPromptPackage(
        system_prompt=system_prompt,
        user_prompt=redacted_user_prompt,
        redaction_applied=redaction_applied,
        source=source,
        safety_notes=(
            "This package is for human review before any optional LLM provider use.",
            "Provider execution is not performed by this command.",
            "Do not include raw secrets, tokens, cookies, or private customer data.",
            "LLM output must be treated as suggestions, not confirmed findings.",
            "All testing must remain authorized and in scope.",
        ),
    )

    return CaseChatPromptPackage(
        prompt_package=prompt,
        artifact_kinds=tuple(artifact_kinds),
        question=question_text,
        source=source,
    )


def render_case_chat_prompt_package_markdown(package: CaseChatPromptPackage) -> str:
    """Render a case-chat prompt package as Markdown for human review."""
    prompt = package.prompt_package

    lines = [
        "# Case Chat LLM Prompt Package",
        "",
        "## Metadata",
        "",
        f"- Source: {package.source}",
        f"- Question: {package.question}",
        f"- Artifact Kinds: {', '.join(package.artifact_kinds)}",
        f"- Redaction Applied: {'yes' if prompt.redaction_applied else 'no'}",
        "- Provider Execution: false",
        "- Planning Only: true",
        "",
        "## Safety Notes",
        "",
    ]

    for note in prompt.safety_notes:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "## System Prompt",
            "",
            "```text",
            prompt.system_prompt.strip(),
            "```",
            "",
            "## User Prompt",
            "",
            "```text",
            prompt.user_prompt.strip(),
            "```",
            "",
        ]
    )

    return "\n".join(lines)


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")
