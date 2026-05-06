"""
Case-to-report assistant for Blackhole AI Workbench result evidence workflows.

This module turns local case-summary, priority-ranking, and multi-agent review
JSON into a human-review report skeleton. It does not confirm vulnerabilities,
call LLM providers, send requests, execute tools, launch browsers, use Kali
tools, mutate targets, bypass authorization, or interact with targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseReportAssistantDraft:
    markdown: str
    title_candidates: tuple[str, ...]
    affected_endpoints: tuple[str, ...]
    readiness: str
    source: str = "result-evidence-report-assistant"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "result_evidence_report_assistant",
            "source": self.source,
            "title_candidates": list(self.title_candidates),
            "affected_endpoints": list(self.affected_endpoints),
            "readiness": self.readiness,
            "markdown": self.markdown,
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


def build_case_report_assistant_draft(
    case_summary: dict[str, Any],
    ranking: dict[str, Any] | None = None,
    multi_agent_review: dict[str, Any] | None = None,
    source: str = "result-evidence-report-assistant",
) -> CaseReportAssistantDraft:
    """Build a planning-only report skeleton from local case intelligence artifacts."""
    _require_kind(case_summary, "result_evidence_case_summary", "case summary")

    if ranking is not None:
        _require_kind(ranking, "result_evidence_priority_ranking", "priority ranking")

    if multi_agent_review is not None:
        _require_kind(multi_agent_review, "result_evidence_multi_agent_review_plan", "multi-agent review")

    candidate = _select_primary_candidate(case_summary, ranking)
    endpoint = str(candidate.get("endpoint") or "").strip()

    if not endpoint:
        raise ValueError("report assistant requires at least one candidate endpoint")

    hypothesis_class = str(candidate.get("hypothesis_class") or "unknown")
    priority = str(candidate.get("priority") or "unknown")
    readiness = str(candidate.get("readiness") or "unknown")
    severity_hint = str(candidate.get("severity_hint") or "needs-validation")
    confidence = str(candidate.get("confidence") or "unknown")
    evidence_strength = str(candidate.get("evidence_strength") or "unknown")
    source_label = str(candidate.get("source") or "unknown")
    missing_evidence = _string_list(candidate.get("missing_evidence"))
    next_actions = _string_list(candidate.get("next_actions"))

    title_candidates = tuple(_title_candidates(endpoint, hypothesis_class))
    affected_endpoints = tuple(_affected_endpoints(case_summary, ranking, endpoint))
    agent_notes = _agent_notes(multi_agent_review, endpoint)

    markdown = _render_markdown(
        endpoint=endpoint,
        hypothesis_class=hypothesis_class,
        priority=priority,
        readiness=readiness,
        severity_hint=severity_hint,
        confidence=confidence,
        evidence_strength=evidence_strength,
        source_label=source_label,
        title_candidates=title_candidates,
        affected_endpoints=affected_endpoints,
        missing_evidence=missing_evidence,
        next_actions=next_actions,
        agent_notes=agent_notes,
    )

    return CaseReportAssistantDraft(
        markdown=markdown,
        title_candidates=title_candidates,
        affected_endpoints=affected_endpoints,
        readiness=readiness,
        source=source,
    )


def _require_kind(data: dict[str, Any], expected: str, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")

    if data.get("kind") != expected:
        raise ValueError(f"{label} requires kind={expected}")


def _select_primary_candidate(case_summary: dict[str, Any], ranking: dict[str, Any] | None) -> dict[str, Any]:
    if ranking is not None:
        top = ranking.get("top_candidate")
        if isinstance(top, dict) and str(top.get("endpoint") or "").strip():
            return top

        candidates = ranking.get("candidates")
        if isinstance(candidates, list):
            for candidate in candidates:
                if isinstance(candidate, dict) and str(candidate.get("endpoint") or "").strip():
                    return candidate

    strongest = case_summary.get("strongest_candidates")
    if isinstance(strongest, list):
        for candidate in strongest:
            if isinstance(candidate, dict) and str(candidate.get("endpoint") or "").strip():
                return candidate

    findings = case_summary.get("findings")
    if isinstance(findings, list):
        for candidate in findings:
            if isinstance(candidate, dict) and str(candidate.get("endpoint") or "").strip():
                return candidate

    raise ValueError("report assistant requires at least one candidate endpoint")


def _title_candidates(endpoint: str, hypothesis_class: str) -> list[str]:
    if "tenant" in hypothesis_class or "cross-account" in hypothesis_class or "cross-tenant" in hypothesis_class:
        return [
            f"Possible Cross-Account Authorization Boundary Issue on `{endpoint}`",
            f"Potential Tenant/Object Authorization Inconsistency via `{endpoint}`",
        ]

    if "information-disclosure" in hypothesis_class:
        return [
            f"Potential Information Disclosure via `{endpoint}`",
            f"Possible Exposure of Private Data Through `{endpoint}`",
        ]

    if "authorization" in hypothesis_class:
        return [
            f"Possible Improper Authorization on `{endpoint}`",
            f"Potential Object Authorization Bypass via `{endpoint}`",
        ]

    return [
        f"Candidate Security Finding on `{endpoint}`",
        f"Potential Access-Control Issue Requiring Manual Validation on `{endpoint}`",
    ]


def _affected_endpoints(case_summary: dict[str, Any], ranking: dict[str, Any] | None, fallback: str) -> list[str]:
    endpoints: list[str] = []

    if ranking is not None:
        candidates = ranking.get("candidates")
        if isinstance(candidates, list):
            for item in candidates:
                if isinstance(item, dict):
                    endpoint = str(item.get("endpoint") or "").strip()
                    if endpoint:
                        endpoints.append(endpoint)

    if not endpoints:
        findings = case_summary.get("findings")
        if isinstance(findings, list):
            for item in findings:
                if isinstance(item, dict):
                    endpoint = str(item.get("endpoint") or "").strip()
                    if endpoint:
                        endpoints.append(endpoint)

    if not endpoints:
        endpoints.append(fallback)

    return _dedupe(endpoints)


def _agent_notes(multi_agent_review: dict[str, Any] | None, endpoint: str) -> list[str]:
    if multi_agent_review is None:
        return ["No multi-agent review artifact was provided. Run result-evidence-multi-agent-review for specialist checks."]

    notes: list[str] = []
    plans = multi_agent_review.get("plans")

    if not isinstance(plans, list):
        return ["Multi-agent review artifact did not contain plans."]

    for plan in plans:
        if not isinstance(plan, dict):
            continue

        if str(plan.get("endpoint") or "") != endpoint:
            continue

        agents = plan.get("agents")
        if not isinstance(agents, list):
            continue

        for agent in agents:
            if not isinstance(agent, dict):
                continue

            name = str(agent.get("agent") or "unknown-agent")
            flags = _string_list(agent.get("risk_flags"))
            if flags:
                notes.append(f"{name}: {', '.join(flags)}")
            else:
                notes.append(f"{name}: no risk flags listed")

    return notes or ["No matching multi-agent review plan was found for the primary endpoint."]


def _render_markdown(
    *,
    endpoint: str,
    hypothesis_class: str,
    priority: str,
    readiness: str,
    severity_hint: str,
    confidence: str,
    evidence_strength: str,
    source_label: str,
    title_candidates: tuple[str, ...],
    affected_endpoints: tuple[str, ...],
    missing_evidence: list[str],
    next_actions: list[str],
    agent_notes: list[str],
) -> str:
    lines: list[str] = []

    lines.append("# Case-to-Report Assistant Draft")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append("This is a **planning-only report skeleton** generated from local artifacts.")
    lines.append("It is not a vulnerability confirmation. A human researcher must validate scope, reproducibility, authorization boundaries, and impact before submission.")
    lines.append("")

    lines.append("## Candidate Title Options")
    lines.append("")
    for title in title_candidates:
        lines.append(f"- {title}")
    lines.append("")

    lines.append("## Primary Candidate")
    lines.append("")
    lines.append(f"- Endpoint: `{endpoint}`")
    lines.append(f"- Hypothesis class: {hypothesis_class}")
    lines.append(f"- Priority: {priority}")
    lines.append(f"- Readiness: {readiness}")
    lines.append(f"- Evidence strength: {evidence_strength}")
    lines.append(f"- Severity hint: {severity_hint}")
    lines.append(f"- Confidence: {confidence}")
    lines.append(f"- Source: `{source_label}`")
    lines.append("")

    lines.append("## Affected Endpoint Candidates")
    lines.append("")
    for item in affected_endpoints:
        lines.append(f"- `{item}`")
    lines.append("")

    lines.append("## Summary Draft")
    lines.append("")
    lines.append(f"The local evidence workflow identified `{endpoint}` as the primary candidate for manual report review.")
    lines.append("The current artifacts suggest this may involve an authorization or access-control boundary, but the final report must only claim what is proven by scoped, repeatable evidence.")
    lines.append("")

    lines.append("## Proof-of-Concept Skeleton")
    lines.append("")
    lines.append("1. Confirm the target and affected asset are in scope.")
    lines.append("2. Capture a valid own-account or own-object baseline.")
    lines.append("3. Capture second-account or foreign-object behavior using controlled test data.")
    lines.append("4. Compare against a random or nonexistent object baseline.")
    lines.append("5. Confirm whether any private, sensitive, tenant-specific, or ownership-specific data is returned.")
    lines.append("6. Preserve raw request/response pairs with secrets and personal data redacted.")
    lines.append("")

    lines.append("## Evidence Checklist")
    lines.append("")
    checks = [
        "Scope confirmation",
        "Own-object baseline",
        "Foreign-object or second-account baseline",
        "Random-object baseline",
        "Raw request/response evidence",
        "Response comparison table",
        "Sensitive data or ownership marker explanation",
        "Redaction pass for tokens, cookies, secrets, and personal data",
    ]
    for item in checks:
        lines.append(f"- [ ] {item}")
    lines.append("")

    lines.append("## Missing Evidence")
    lines.append("")
    if missing_evidence:
        for item in missing_evidence:
            lines.append(f"- {item}")
    else:
        lines.append("- No missing evidence was listed in the primary candidate artifact. Still manually verify raw evidence before reporting.")
    lines.append("")

    lines.append("## Specialist Review Notes")
    lines.append("")
    for note in agent_notes:
        lines.append(f"- {note}")
    lines.append("")

    lines.append("## Next Actions")
    lines.append("")
    if next_actions:
        for item in next_actions:
            lines.append(f"- {item}")
    else:
        lines.append("- Complete manual validation before drafting final impact.")
    lines.append("")

    lines.append("## Impact Wording Guardrails")
    lines.append("")
    lines.append("- Do not claim High severity unless sensitive data, authorization boundary, and repeatability are proven.")
    lines.append("- Do not claim cross-tenant or cross-account impact unless ownership is verified.")
    lines.append("- Do not claim data exposure without showing the affected data class.")
    lines.append("- Do not include secrets, tokens, cookies, or unnecessary personal data.")
    lines.append("- Do not submit candidates that match expected blocking or random-object behavior.")
    lines.append("")

    lines.append("## Final Report Readiness")
    lines.append("")
    if readiness in {"near-report-ready", "needs-final-validation"}:
        lines.append("This candidate may be worth final manual validation before writing the final report.")
    else:
        lines.append("This candidate is not report-ready with the current local artifacts.")
    lines.append("")

    lines.append("## Safety")
    lines.append("")
    lines.append("- Local-only report skeleton.")
    lines.append("- Planning-only output.")
    lines.append("- No network interaction.")
    lines.append("- No tool execution.")
    lines.append("- No LLM provider calls.")
    lines.append("- No vulnerability confirmation.")
    lines.append("")

    return "\n".join(lines)


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
