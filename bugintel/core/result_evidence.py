"""
Result evidence importer for Blackhole AI Workbench.

This module normalizes local, human-provided result evidence JSON into a
standard structure that can feed interpret-result or result-flow. It does not
send requests, execute shell commands, launch browsers, use Kali tools, call
LLM providers, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from bugintel.core.result_interpreter import interpret_validation_result


@dataclass(frozen=True)
class ResultEvidence:
    endpoint: str
    observed_status: int | None = None
    expected_status: int | None = None
    observed_body: str = ""
    expected_body: str = ""
    note: str = ""
    source: str = "manual-json"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def import_result_evidence(data: dict[str, Any], source: str = "manual-json") -> ResultEvidence:
    """Normalize result evidence JSON."""
    endpoint = str(data.get("endpoint") or data.get("url") or "").strip()

    if not endpoint:
        raise ValueError("result evidence requires an endpoint or url field")

    return ResultEvidence(
        endpoint=endpoint,
        observed_status=_optional_int(data.get("observed_status", data.get("status_code"))),
        expected_status=_optional_int(data.get("expected_status")),
        observed_body=str(data.get("observed_body") or data.get("body") or ""),
        expected_body=str(data.get("expected_body") or ""),
        note=str(data.get("note") or data.get("notes") or ""),
        source=source,
    )


@dataclass(frozen=True)
class ResultEvidenceBatch:
    evidence: list[ResultEvidence]
    source: str = "manual-json-batch"
    kind: str = "result_evidence_batch"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "count": len(self.evidence),
            "source": self.source,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "evidence": [item.to_dict() for item in self.evidence],
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
            },
        }


def import_result_evidence_batch(
    evidence_dir: Path,
    source: str = "manual-json-batch",
    pattern: str = "*.json",
) -> ResultEvidenceBatch:
    """Normalize all matching local result evidence JSON files in a directory."""
    if not evidence_dir.exists():
        raise FileNotFoundError(f"evidence directory not found: {evidence_dir}")

    if not evidence_dir.is_dir():
        raise NotADirectoryError(f"evidence path is not a directory: {evidence_dir}")

    evidence_items: list[ResultEvidence] = []

    for evidence_file in sorted(evidence_dir.glob(pattern)):
        if not evidence_file.is_file():
            continue

        try:
            data = __import__("json").loads(evidence_file.read_text(encoding="utf-8"))
        except __import__("json").JSONDecodeError as exc:
            raise ValueError(f"invalid evidence JSON in {evidence_file}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"evidence JSON must be an object: {evidence_file}")

        evidence_items.append(import_result_evidence(data, source=f"{source}:{evidence_file.name}"))

    return ResultEvidenceBatch(evidence=evidence_items, source=source)


@dataclass(frozen=True)
class ResultEvidenceBatchReviewItem:
    endpoint: str
    suggested_result: str
    confidence: str
    source: str
    observed_status: int | None = None
    expected_status: int | None = None
    signal_count: int = 0
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultEvidenceBatchReview:
    items: list[ResultEvidenceBatchReviewItem]
    source: str = "result-evidence-batch-review"
    kind: str = "result_evidence_batch_review"
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        supported = [item for item in self.items if item.suggested_result == "supported"]
        rejected = [item for item in self.items if item.suggested_result == "rejected"]
        needs_more = [item for item in self.items if item.suggested_result == "needs-more-evidence"]
        missing_expected_status = [item for item in self.items if item.expected_status is None]

        return {
            "kind": self.kind,
            "source": self.source,
            "count": len(self.items),
            "supported_count": len(supported),
            "rejected_count": len(rejected),
            "needs_more_evidence_count": len(needs_more),
            "missing_expected_status_count": len(missing_expected_status),
            "endpoints": [item.endpoint for item in self.items],
            "items": [item.to_dict() for item in self.items],
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "llm_provider_calls": False,
            },
        }


def review_result_evidence_batch(data: dict[str, Any], source: str = "result-evidence-batch-review") -> ResultEvidenceBatchReview:
    """Review a normalized result evidence batch using local planning-only interpretation."""
    evidence_list = data.get("evidence")

    if not isinstance(evidence_list, list):
        raise ValueError("result evidence batch requires an evidence list")

    review_items: list[ResultEvidenceBatchReviewItem] = []

    for raw_item in evidence_list:
        if not isinstance(raw_item, dict):
            raise ValueError("each evidence batch item must be an object")

        evidence = import_result_evidence(raw_item, source=str(raw_item.get("source") or source))
        interpretation = interpret_validation_result(
            endpoint=evidence.endpoint,
            observed_status=evidence.observed_status,
            expected_status=evidence.expected_status,
            observed_body=evidence.observed_body,
            expected_body=evidence.expected_body,
            note=evidence.note,
        )

        review_items.append(
            ResultEvidenceBatchReviewItem(
                endpoint=evidence.endpoint,
                suggested_result=interpretation.suggested_result,
                confidence=interpretation.confidence,
                source=evidence.source,
                observed_status=evidence.observed_status,
                expected_status=evidence.expected_status,
                signal_count=len(interpretation.signals),
                rationale=interpretation.rationale,
            )
        )

    return ResultEvidenceBatchReview(items=review_items, source=source)


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
