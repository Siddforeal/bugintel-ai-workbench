"""
Provider dry-run for case-chat LLM prompt packages.

This module performs a local dry-run for a case-chat prompt package:
prompt safety audit, provider gate decision, and disabled provider stub result.

It does not call real LLM providers, read API keys, send requests, execute
tools, launch browsers, use Kali tools, mutate targets, bypass authorization,
or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.llm_prompt import LLMPromptPackage
from bugintel.core.llm_provider import run_disabled_llm_provider
from bugintel.core.llm_safety import audit_llm_prompt_package
from bugintel.core.result_evidence_chat_provider_gate import build_case_chat_provider_gate


@dataclass(frozen=True)
class CaseChatProviderDryRun:
    provider_name: str
    audit_status: str
    gate_allowed: bool
    gate_reason: str
    disabled_provider_status: str
    disabled_provider_reason: str
    required_actions: tuple[str, ...]
    source: str = "result-evidence-case-chat-provider-dry-run"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_case_chat_provider_dry_run",
            "source": self.source,
            "provider_name": self.provider_name,
            "audit_status": self.audit_status,
            "gate_allowed": self.gate_allowed,
            "gate_reason": self.gate_reason,
            "disabled_provider_status": self.disabled_provider_status,
            "disabled_provider_reason": self.disabled_provider_reason,
            "required_actions": list(self.required_actions),
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

    def to_markdown(self, title: str = "Case Chat Provider Dry Run") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Provider: {self.provider_name}",
            f"- Prompt Audit Status: {self.audit_status}",
            f"- Gate Allowed: {str(self.gate_allowed).lower()}",
            f"- Gate Reason: {self.gate_reason}",
            f"- Disabled Provider Status: {self.disabled_provider_status}",
            f"- Disabled Provider Reason: {self.disabled_provider_reason}",
            "- Provider Execution Performed: false",
            "",
            "## Required Actions",
            "",
        ]

        if self.required_actions:
            for action in self.required_actions:
                lines.append(f"- {action}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This is a local dry-run only.",
                "- It does not call any real LLM provider.",
                "- It does not read API keys.",
                "- It does not send requests.",
                "- It does not execute tools.",
                "- It does not confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_chat_provider_dry_run(
    prompt_package_data: dict[str, Any],
    provider_name: str = "disabled",
    allow_provider_execution: bool = False,
    require_prompt_audit_pass: bool = True,
    model: str = "",
    source: str = "result-evidence-case-chat-provider-dry-run",
) -> CaseChatProviderDryRun:
    """Build a local dry-run report for a case-chat prompt package."""
    if not isinstance(prompt_package_data, dict):
        raise ValueError("case chat prompt package data must be an object")

    if prompt_package_data.get("kind") != "result_evidence_case_chat_prompt_package":
        raise ValueError("provider dry-run requires kind=result_evidence_case_chat_prompt_package")

    prompt_data = prompt_package_data.get("prompt_package")
    if not isinstance(prompt_data, dict):
        raise ValueError("provider dry-run requires prompt_package object")

    prompt = LLMPromptPackage(
        system_prompt=str(prompt_data.get("system_prompt") or ""),
        user_prompt=str(prompt_data.get("user_prompt") or ""),
        redaction_applied=bool(prompt_data.get("redaction_applied")),
        source=str(prompt_data.get("source") or "result-evidence-case-chat-prompt"),
        safety_notes=tuple(str(item) for item in prompt_data.get("safety_notes", ()) if str(item).strip()),
    )

    audit = audit_llm_prompt_package(prompt)
    gate = build_case_chat_provider_gate(
        prompt_package_data,
        provider_name=provider_name,
        allow_provider_execution=allow_provider_execution,
        require_prompt_audit_pass=require_prompt_audit_pass,
        model=model,
    )
    disabled_result = run_disabled_llm_provider(prompt)

    return CaseChatProviderDryRun(
        provider_name=gate.provider_name,
        audit_status=audit.status,
        gate_allowed=gate.allowed,
        gate_reason=gate.reason,
        disabled_provider_status=disabled_result.status,
        disabled_provider_reason=disabled_result.reason,
        required_actions=gate.required_actions,
        source=source,
    )
