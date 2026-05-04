"""
Result evidence importer for Blackhole AI Workbench.

This module normalizes local, human-provided result evidence JSON into a
standard structure that can feed interpret-result or result-flow. It does not
send requests, execute shell commands, launch browsers, use Kali tools, call
LLM providers, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
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


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
