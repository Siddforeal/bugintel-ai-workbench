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


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
