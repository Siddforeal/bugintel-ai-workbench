"""
Priority ranking for Blackhole AI Workbench result evidence case summaries.

This module ranks local case-summary findings so a human researcher can decide
what deserves attention first. It is deterministic and local-only. It does not
call LLM providers, send requests, execute tools, launch browsers, use Kali
tools, mutate targets, bypass authorization, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PriorityRankedCandidate:
    rank: int
    endpoint: str
    score: int
    priority: str
    readiness: str
    hypothesis_class: str
    evidence_strength: str
    severity_hint: str
    confidence: str
    reason: str
    source: str
    missing_evidence: tuple[str, ...]
    next_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing_evidence"] = list(self.missing_evidence)
        data["next_actions"] = list(self.next_actions)
        return data


@dataclass(frozen=True)
class ResultEvidencePriorityRanking:
    candidates: tuple[PriorityRankedCandidate, ...]
    source: str = "result-evidence-priority-ranking"
    kind: str = "result_evidence_priority_ranking"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        top = self.candidates[0].to_dict() if self.candidates else None

        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.candidates),
            "top_candidate": top,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
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

    def to_markdown(self, title: str = "Result Evidence Priority Ranking") -> str:
        lines: list[str] = []
        data = self.to_dict()

        lines.append(f"# {title}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Ranked candidates: {data['count']}")
        lines.append("- Planning-only: true")
        lines.append("- Vulnerability confirmation: false")
        lines.append("")

        if data["top_candidate"]:
            top = data["top_candidate"]
            lines.append("## Top Candidate")
            lines.append("")
            lines.append(f"- Endpoint: `{top['endpoint']}`")
            lines.append(f"- Score: {top['score']}")
            lines.append(f"- Priority: {top['priority']}")
            lines.append(f"- Readiness: {top['readiness']}")
            lines.append(f"- Hypothesis class: {top['hypothesis_class']}")
            lines.append(f"- Reason: {top['reason']}")
            lines.append("")

        lines.append("## Ranked Candidates")
        lines.append("")

        if not self.candidates:
            lines.append("_No candidates were present in the case summary._")
            lines.append("")
        else:
            for candidate in self.candidates:
                lines.append(f"### {candidate.rank}. `{candidate.endpoint}`")
                lines.append("")
                lines.append(f"- Score: {candidate.score}")
                lines.append(f"- Priority: {candidate.priority}")
                lines.append(f"- Readiness: {candidate.readiness}")
                lines.append(f"- Evidence strength: {candidate.evidence_strength}")
                lines.append(f"- Severity hint: {candidate.severity_hint}")
                lines.append(f"- Confidence: {candidate.confidence}")
                lines.append(f"- Hypothesis class: **{candidate.hypothesis_class}**")
                lines.append(f"- Source: `{candidate.source}`")
                lines.append(f"- Reason: {candidate.reason}")
                lines.append("")

                lines.append("Missing evidence:")
                if candidate.missing_evidence:
                    for item in candidate.missing_evidence:
                        lines.append(f"- {item}")
                else:
                    lines.append("- none")
                lines.append("")

                lines.append("Next actions:")
                if candidate.next_actions:
                    for item in candidate.next_actions:
                        lines.append(f"- {item}")
                else:
                    lines.append("- none")
                lines.append("")

        lines.append("## Safety")
        lines.append("")
        lines.append("- This is a local ranking artifact.")
        lines.append("- It does not execute tests.")
        lines.append("- It does not send requests.")
        lines.append("- It does not mutate targets.")
        lines.append("- It does not confirm vulnerabilities.")
        lines.append("")

        return "\n".join(lines)


def build_result_evidence_priority_ranking(
    case_summary_data: dict[str, Any],
    include_weak: bool = True,
    source: str = "result-evidence-priority-ranking",
) -> ResultEvidencePriorityRanking:
    """Rank local case-summary findings by report-readiness and evidence strength."""
    if not isinstance(case_summary_data, dict):
        raise ValueError("case summary data must be an object")

    if case_summary_data.get("kind") != "result_evidence_case_summary":
        raise ValueError("priority ranking requires kind=result_evidence_case_summary")

    findings = case_summary_data.get("findings")
    if not isinstance(findings, list):
        raise ValueError("priority ranking requires a findings list")

    scored: list[tuple[int, dict[str, Any], str]] = []

    for raw_finding in findings:
        if not isinstance(raw_finding, dict):
            raise ValueError("each case summary finding must be an object")

        endpoint = str(raw_finding.get("endpoint") or "").strip()
        if not endpoint:
            raise ValueError("each case summary finding requires an endpoint")

        if not include_weak and _is_weak(raw_finding):
            continue

        score, reason = _score_finding(raw_finding)
        scored.append((score, raw_finding, reason))

    scored.sort(key=lambda item: (-item[0], str(item[1].get("endpoint") or "")))

    candidates: list[PriorityRankedCandidate] = []
    for rank, (score, finding, reason) in enumerate(scored, start=1):
        candidates.append(
            PriorityRankedCandidate(
                rank=rank,
                endpoint=str(finding.get("endpoint") or ""),
                score=score,
                priority=str(finding.get("priority") or "unknown"),
                readiness=str(finding.get("readiness") or "unknown"),
                hypothesis_class=str(finding.get("hypothesis_class") or "unknown"),
                evidence_strength=str(finding.get("evidence_strength") or "unknown"),
                severity_hint=str(finding.get("severity_hint") or "unknown"),
                confidence=str(finding.get("confidence") or "unknown"),
                reason=reason,
                source=str(finding.get("source") or "unknown"),
                missing_evidence=tuple(_string_list(finding.get("missing_evidence"))),
                next_actions=tuple(_string_list(finding.get("next_actions"))),
            )
        )

    return ResultEvidencePriorityRanking(candidates=tuple(candidates), source=source)


def _score_finding(finding: dict[str, Any]) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []

    priority = str(finding.get("priority") or "")
    readiness = str(finding.get("readiness") or "")
    evidence_strength = str(finding.get("evidence_strength") or "")
    severity_hint = str(finding.get("severity_hint") or "")
    hypothesis_class = str(finding.get("hypothesis_class") or "")
    missing_evidence = _string_list(finding.get("missing_evidence"))

    priority_scores = {
        "high": 40,
        "medium-high": 30,
        "medium": 20,
        "medium-low": 10,
        "low": 0,
    }
    score += priority_scores.get(priority, 0)
    if priority:
        reasons.append(f"priority={priority}")

    readiness_scores = {
        "near-report-ready": 45,
        "needs-final-validation": 35,
        "needs-more-evidence": 10,
        "not-reportable-currently": -30,
        "likely-false-positive": -50,
    }
    score += readiness_scores.get(readiness, 0)
    if readiness:
        reasons.append(f"readiness={readiness}")

    evidence_scores = {
        "strong-candidate": 30,
        "medium-candidate": 20,
        "weak-candidate": 5,
        "weak-for-finding": -20,
    }
    score += evidence_scores.get(evidence_strength, 0)
    if evidence_strength:
        reasons.append(f"evidence_strength={evidence_strength}")

    if "high" in severity_hint:
        score += 15
        reasons.append("severity_hint_mentions_high")

    if hypothesis_class == "likely-expected-blocking-or-false-positive":
        score -= 40
        reasons.append("likely_false_positive_penalty")

    if missing_evidence:
        score -= min(20, len(missing_evidence) * 5)
        reasons.append(f"missing_evidence={len(missing_evidence)}")

    return score, "; ".join(reasons) if reasons else "No ranking signals were present."


def _is_weak(finding: dict[str, Any]) -> bool:
    return str(finding.get("readiness") or "") in {
        "likely-false-positive",
        "not-reportable-currently",
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
