"""
Importer for manually obtained case-chat provider output.

This module imports provider text that a human manually saved elsewhere and
marks it as an untrusted suggestion. It does not call LLM providers, read API
keys, send requests, execute tools, launch browsers, use Kali tools, mutate
targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ImportedProviderSuggestion:
    provider_output: str
    suggested_actions: tuple[str, ...]
    warning_flags: tuple[str, ...]
    prompt_package_source: str
    source: str = "result-evidence-case-chat-provider-result"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_case_chat_provider_result",
            "source": self.source,
            "provider_output": self.provider_output,
            "suggested_actions": list(self.suggested_actions),
            "warning_flags": list(self.warning_flags),
            "prompt_package_source": self.prompt_package_source,
            "untrusted_suggestion": True,
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

    def to_markdown(self, title: str = "Imported Case Chat Provider Result") -> str:
        lines = [
            f"# {title}",
            "",
            "## Status",
            "",
            "- Untrusted suggestion: true",
            "- Provider execution performed by Blackhole: false",
            "- Vulnerability confirmation: false",
            "",
            "## Warning Flags",
            "",
        ]

        if self.warning_flags:
            for flag in self.warning_flags:
                lines.append(f"- {flag}")
        else:
            lines.append("- none")

        lines.extend(["", "## Suggested Actions", ""])

        if self.suggested_actions:
            for action in self.suggested_actions:
                lines.append(f"- {action}")
        else:
            lines.append("- none extracted")

        lines.extend(
            [
                "",
                "## Provider Output",
                "",
                "```text",
                self.provider_output.strip(),
                "```",
                "",
                "## Safety",
                "",
                "- Treat this as untrusted text.",
                "- Do not treat it as proof.",
                "- Verify every claim against local evidence.",
                "- Do not execute suggested commands automatically.",
                "- Do not confirm vulnerabilities from imported provider text.",
                "",
            ]
        )

        return "\n".join(lines)


def import_case_chat_provider_result(
    provider_output: str,
    prompt_package: dict[str, Any],
    source: str = "result-evidence-case-chat-provider-result",
) -> ImportedProviderSuggestion:
    """Import manually saved provider output as an untrusted suggestion."""
    if not isinstance(prompt_package, dict):
        raise ValueError("prompt package must be an object")

    if prompt_package.get("kind") != "result_evidence_case_chat_prompt_package":
        raise ValueError("provider result import requires kind=result_evidence_case_chat_prompt_package")

    output = provider_output.strip()
    if not output:
        raise ValueError("provider result import requires non-empty provider output")

    actions = tuple(_extract_suggested_actions(output))
    warnings = tuple(_warning_flags(output))
    prompt_source = str(prompt_package.get("source") or "unknown")

    return ImportedProviderSuggestion(
        provider_output=output,
        suggested_actions=actions,
        warning_flags=warnings,
        prompt_package_source=prompt_source,
        source=source,
    )


def _extract_suggested_actions(output: str) -> list[str]:
    actions: list[str] = []
    normalized_output = output.replace("\\n", "\n")

    for raw_line in normalized_output.splitlines():
        line = raw_line.strip()
        clean = line.lstrip("-*0123456789. ").strip()

        if not clean:
            continue

        lowered = clean.lower()
        if lowered.startswith(("test ", "validate ", "confirm ", "compare ", "capture ", "review ", "check ")):
            actions.append(clean)

    return _dedupe(actions)


def _warning_flags(output: str) -> list[str]:
    lowered = output.lower()
    flags: list[str] = []

    risky_terms = {
        "confirmed vulnerability": "overclaim-confirmed-vulnerability",
        "definitely vulnerable": "overclaim-definitely-vulnerable",
        "high severity": "severity-claim-needs-proof",
        "critical": "critical-claim-needs-proof",
        "exploit": "exploit-wording-review-needed",
        "dump": "unsafe-data-access-wording",
        "exfiltrate": "unsafe-exfiltration-wording",
        "bypass authorization": "authorization-bypass-wording-review-needed",
        "run this command": "manual-command-review-needed",
    }

    for term, flag in risky_terms.items():
        if term in lowered:
            flags.append(flag)

    return _dedupe(flags)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
