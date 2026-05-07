"""
Review bridge for imported case-chat provider suggestions.

This module compares manually imported provider output against local evidence
artifacts and marks suggestions as safe planning notes, needs evidence, or
unsafe/overclaimed. It does not call LLM providers, send requests, execute
tools, launch browsers, use Kali tools, mutate targets, bypass authorization,
or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewedProviderAction:
    action: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ProviderSuggestionReview:
    recommendation: str
    reviewed_actions: tuple[ReviewedProviderAction, ...]
    warning_flags: tuple[str, ...]
    supported_by_local_evidence: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    source: str = "result-evidence-case-chat-provider-result-review"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_case_chat_provider_result_review",
            "source": self.source,
            "recommendation": self.recommendation,
            "reviewed_actions": [item.to_dict() for item in self.reviewed_actions],
            "warning_flags": list(self.warning_flags),
            "supported_by_local_evidence": list(self.supported_by_local_evidence),
            "unsupported_claims": list(self.unsupported_claims),
            "missing_evidence": list(self.missing_evidence),
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

    def to_markdown(self, title: str = "Provider Suggestion Review") -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "## Status",
            "",
            "- Untrusted suggestion: true",
            f"- Recommendation: {self.recommendation}",
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

        lines.extend(["", "## Reviewed Actions", ""])

        if self.reviewed_actions:
            for item in self.reviewed_actions:
                lines.append(f"- **{item.status}**: {item.action}")
                lines.append(f"  - Reason: {item.reason}")
        else:
            lines.append("- none")

        lines.extend(["", "## Supported By Local Evidence", ""])

        if self.supported_by_local_evidence:
            for item in self.supported_by_local_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Unsupported Claims", ""])

        if self.unsupported_claims:
            for item in self.unsupported_claims:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence", ""])

        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none listed")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- Treat imported provider output as untrusted.",
                "- Verify every suggestion against local evidence.",
                "- Do not execute suggested commands automatically.",
                "- Do not confirm vulnerabilities from provider text.",
                "",
            ]
        )

        return "\n".join(lines)


def review_case_chat_provider_result(
    imported_result: dict[str, Any],
    case_memory: dict[str, Any] | None = None,
    grounded_answer: dict[str, Any] | None = None,
    source: str = "result-evidence-case-chat-provider-result-review",
) -> ProviderSuggestionReview:
    """Review imported provider output against local evidence artifacts."""
    _require_kind(imported_result, "result_evidence_case_chat_provider_result", "imported provider result")

    if case_memory is not None:
        _require_kind(case_memory, "result_evidence_case_memory", "case memory")

    if grounded_answer is not None:
        _require_kind(grounded_answer, "result_evidence_grounded_answer", "grounded answer")

    suggested_actions = _string_list(imported_result.get("suggested_actions"))
    warning_flags = _string_list(imported_result.get("warning_flags"))
    provider_output = str(imported_result.get("provider_output") or "")

    local_actions = _local_actions(case_memory, grounded_answer)
    missing_evidence = _missing_evidence(case_memory, grounded_answer)

    reviewed_actions = tuple(_review_actions(suggested_actions, local_actions))
    supported = tuple(_supported_evidence(case_memory, grounded_answer))
    unsupported = tuple(_unsupported_claims(provider_output, warning_flags))

    recommendation = _recommendation(warning_flags, unsupported, missing_evidence, reviewed_actions)

    return ProviderSuggestionReview(
        recommendation=recommendation,
        reviewed_actions=reviewed_actions,
        warning_flags=tuple(warning_flags),
        supported_by_local_evidence=supported,
        unsupported_claims=unsupported,
        missing_evidence=tuple(missing_evidence),
        source=source,
    )


def _review_actions(suggested_actions: list[str], local_actions: list[str]) -> list[ReviewedProviderAction]:
    reviewed: list[ReviewedProviderAction] = []

    for action in suggested_actions:
        if _unsafe_action(action):
            reviewed.append(
                ReviewedProviderAction(
                    action=action,
                    status="unsafe-review-required",
                    reason="Action wording appears command-like, destructive, or unsafe for automatic execution.",
                )
            )
            continue

        if _matches_local_action(action, local_actions):
            reviewed.append(
                ReviewedProviderAction(
                    action=action,
                    status="supported-planning-action",
                    reason="Action overlaps with local next-action evidence.",
                )
            )
        else:
            reviewed.append(
                ReviewedProviderAction(
                    action=action,
                    status="needs-local-evidence",
                    reason="Action is not directly supported by local next-action artifacts.",
                )
            )

    return reviewed


def _unsafe_action(action: str) -> bool:
    lowered = action.lower()
    unsafe_terms = (
        "run this command",
        "delete ",
        "drop ",
        "destroy ",
        "wipe ",
        "dump ",
        "exfiltrate",
        "steal ",
        "bypass authorization",
        "disable safety",
    )
    return any(term in lowered for term in unsafe_terms)


def _matches_local_action(action: str, local_actions: list[str]) -> bool:
    action_tokens = set(_tokens(action))

    for local_action in local_actions:
        local_tokens = set(_tokens(local_action))
        if not local_tokens:
            continue

        overlap = action_tokens & local_tokens
        if len(overlap) >= 2:
            return True

    return False


def _local_actions(case_memory: dict[str, Any] | None, grounded_answer: dict[str, Any] | None) -> list[str]:
    actions: list[str] = []

    if case_memory:
        actions.extend(_string_list(case_memory.get("open_next_actions")))

    if grounded_answer:
        actions.extend(_string_list(grounded_answer.get("next_actions")))

    return _dedupe(actions)


def _missing_evidence(case_memory: dict[str, Any] | None, grounded_answer: dict[str, Any] | None) -> list[str]:
    missing: list[str] = []

    if case_memory:
        missing.extend(_string_list(case_memory.get("missing_evidence")))

    if grounded_answer:
        for snippet in _objects(grounded_answer.get("grounding")):
            if "missing_evidence" in str(snippet.get("path") or ""):
                value = str(snippet.get("value") or "").strip()
                if value:
                    missing.append(value)

    return _dedupe(missing)


def _supported_evidence(case_memory: dict[str, Any] | None, grounded_answer: dict[str, Any] | None) -> list[str]:
    supported: list[str] = []

    if case_memory:
        top_endpoint = str(case_memory.get("top_endpoint") or "").strip()
        if top_endpoint:
            supported.append(f"case_memory.top_endpoint={top_endpoint}")

        for endpoint in _string_list(case_memory.get("cited_endpoints")):
            supported.append(f"case_memory.cited_endpoints contains {endpoint}")

    if grounded_answer:
        for snippet in _objects(grounded_answer.get("grounding")):
            artifact = str(snippet.get("artifact") or "artifact")
            path = str(snippet.get("path") or "path")
            value = str(snippet.get("value") or "")
            if value:
                supported.append(f"{artifact}.{path}={value}")

    return _dedupe(supported)


def _unsupported_claims(provider_output: str, warning_flags: list[str]) -> list[str]:
    claims: list[str] = []

    if warning_flags:
        for flag in warning_flags:
            claims.append(f"Provider output contains warning flag: {flag}")

    lowered = provider_output.lower()
    if "confirmed vulnerability" in lowered or "definitely vulnerable" in lowered:
        claims.append("Provider output claims confirmation without local proof.")

    if "high severity" in lowered or "critical" in lowered:
        claims.append("Provider output includes severity wording that must be proven.")

    return _dedupe(claims)


def _recommendation(
    warning_flags: list[str],
    unsupported_claims: tuple[str, ...],
    missing_evidence: list[str],
    reviewed_actions: tuple[ReviewedProviderAction, ...],
) -> str:
    if warning_flags or unsupported_claims:
        return "reject-unsafe-or-overclaimed-parts"

    if any(action.status == "unsafe-review-required" for action in reviewed_actions):
        return "manual-safety-review-required"

    if missing_evidence or any(action.status == "needs-local-evidence" for action in reviewed_actions):
        return "use-as-planning-note-needs-evidence"

    return "use-as-planning-note"


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _tokens(value: str) -> list[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return [token for token in cleaned.split() if len(token) >= 4]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result
