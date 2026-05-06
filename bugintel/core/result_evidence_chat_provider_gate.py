"""
Provider gate for case-chat LLM prompt packages.

This module checks whether a case-chat prompt package would be allowed to use a
future LLM provider. It does not call any provider, read API keys, send
requests, execute tools, launch browsers, use Kali tools, mutate targets,
bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.llm_prompt import LLMPromptPackage
from bugintel.core.llm_provider_config import LLMProviderConfig, check_prompt_audit_gate, validate_provider_config
from bugintel.core.llm_safety import audit_llm_prompt_package


@dataclass(frozen=True)
class CaseChatProviderGate:
    allowed: bool
    provider_name: str
    reason: str
    audit_status: str
    required_actions: tuple[str, ...]
    source: str = "result-evidence-case-chat-provider-gate"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_case_chat_provider_gate",
            "source": self.source,
            "allowed": self.allowed,
            "provider_name": self.provider_name,
            "reason": self.reason,
            "audit_status": self.audit_status,
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

    def to_markdown(self, title: str = "Case Chat Provider Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Allowed: {str(self.allowed).lower()}",
            f"- Provider: {self.provider_name}",
            f"- Audit Status: {self.audit_status}",
            f"- Reason: {self.reason}",
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
                "- This gate is local-only.",
                "- It does not call any LLM provider.",
                "- It does not read API keys.",
                "- It does not send requests.",
                "- It does not execute tools.",
                "- It does not confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_chat_provider_gate(
    prompt_package_data: dict[str, Any],
    provider_name: str = "disabled",
    allow_provider_execution: bool = False,
    require_prompt_audit_pass: bool = True,
    model: str = "",
    source: str = "result-evidence-case-chat-provider-gate",
) -> CaseChatProviderGate:
    """Build a local provider gate decision for a case-chat prompt package."""
    if not isinstance(prompt_package_data, dict):
        raise ValueError("case chat prompt package data must be an object")

    if prompt_package_data.get("kind") != "result_evidence_case_chat_prompt_package":
        raise ValueError("provider gate requires kind=result_evidence_case_chat_prompt_package")

    prompt_data = prompt_package_data.get("prompt_package")
    if not isinstance(prompt_data, dict):
        raise ValueError("provider gate requires prompt_package object")

    prompt = LLMPromptPackage(
        system_prompt=str(prompt_data.get("system_prompt") or ""),
        user_prompt=str(prompt_data.get("user_prompt") or ""),
        redaction_applied=bool(prompt_data.get("redaction_applied")),
        source=str(prompt_data.get("source") or "result-evidence-case-chat-prompt"),
        safety_notes=tuple(str(item) for item in prompt_data.get("safety_notes", ()) if str(item).strip()),
    )

    audit_report = audit_llm_prompt_package(prompt)
    config = LLMProviderConfig(
        provider_name=provider_name,
        allow_provider_execution=allow_provider_execution,
        require_prompt_audit_pass=require_prompt_audit_pass,
        model=model,
    )

    # With provider_name=disabled, validate_provider_config intentionally blocks.
    if provider_name == "disabled":
        gate = validate_provider_config(config)
    else:
        gate = check_prompt_audit_gate(config, audit_report)

    return CaseChatProviderGate(
        allowed=gate.allowed,
        provider_name=gate.provider_name,
        reason=gate.reason,
        audit_status=audit_report.status,
        required_actions=gate.required_actions,
        source=source,
    )
