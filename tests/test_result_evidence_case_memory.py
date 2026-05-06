import pytest

from bugintel.core.result_evidence_case_memory import build_result_evidence_case_memory


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "strongest_candidates": [
            {
                "endpoint": "/api/high",
                "missing_evidence": [],
                "next_actions": ["Capture own-object baseline."],
            }
        ],
        "weak_or_rejected_candidates": [
            {
                "endpoint": "/api/weak",
                "missing_evidence": ["Evidence proving behavior differs from blocking"],
                "next_actions": ["Reject if it matches random behavior."],
            }
        ],
        "findings": [],
    }


def _ranking():
    return {
        "kind": "result_evidence_priority_ranking",
        "top_candidate": {"endpoint": "/api/high", "score": 120},
        "candidates": [
            {"endpoint": "/api/high"},
            {"endpoint": "/api/weak"},
        ],
    }


def _report_assistant():
    return {
        "kind": "result_evidence_report_assistant",
        "affected_endpoints": ["/api/high"],
    }


def _grounded_answer():
    return {
        "kind": "result_evidence_grounded_answer",
        "cited_endpoints": ["/api/high"],
        "next_actions": ["Validate baselines."],
        "grounding": [
            {
                "artifact": "case-summary",
                "path": "weak_or_rejected_candidates[0].missing_evidence[0]",
                "value": "Evidence proving behavior differs from blocking",
            }
        ],
    }


def _session():
    return {
        "kind": "result_evidence_case_chat_session",
        "cited_endpoints": ["/api/high"],
        "next_actions": ["Open action from chat."],
        "turns": [],
    }


def test_build_result_evidence_case_memory_combines_artifacts():
    memory = build_result_evidence_case_memory(
        case_summary=_case_summary(),
        ranking=_ranking(),
        report_assistant=_report_assistant(),
        grounded_answer=_grounded_answer(),
        session=_session(),
    )
    data = memory.to_dict()

    assert data["kind"] == "result_evidence_case_memory"
    assert data["top_endpoint"] == "/api/high"
    assert data["strongest_candidates"] == ["/api/high"]
    assert data["weak_candidates"] == ["/api/weak"]
    assert "/api/high" in data["cited_endpoints"]
    assert "/api/weak" in data["cited_endpoints"]
    assert "Capture own-object baseline." in data["open_next_actions"]
    assert "Validate baselines." in data["open_next_actions"]
    assert "Evidence proving behavior differs from blocking" in data["missing_evidence"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_case_memory_markdown_is_readable():
    memory = build_result_evidence_case_memory(case_summary=_case_summary(), ranking=_ranking())
    markdown = memory.to_markdown()

    assert "# Multi-Artifact Case Memory" in markdown
    assert "\\n" not in markdown
    assert "/api/high" in markdown
    assert "Artifact Inventory" in markdown
    assert "It does not confirm vulnerabilities." in markdown


def test_build_result_evidence_case_memory_requires_at_least_one_artifact():
    with pytest.raises(ValueError):
        build_result_evidence_case_memory()


def test_build_result_evidence_case_memory_rejects_wrong_kind():
    with pytest.raises(ValueError):
        build_result_evidence_case_memory(case_summary={"kind": "wrong"})
