import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _case_summary():
    return {
        "kind": "result_evidence_case_summary",
        "count": 2,
        "priority_counts": {"high": 1, "low": 1},
        "readiness_counts": {"needs-final-validation": 1, "likely-false-positive": 1},
        "strongest_candidates": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "priority": "high",
                "readiness": "needs-final-validation",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "confidence": "medium-high",
                "missing_evidence": [],
                "next_actions": [
                    "Capture own-object, foreign-object, and random-object baselines.",
                    "Confirm sensitive or tenant-specific data before claiming impact.",
                ],
                "source": "manual-json-batch:001.json",
            }
        ],
        "weak_or_rejected_candidates": [
            {
                "endpoint": "/api/accounts/123/users/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "priority": "low",
                "readiness": "likely-false-positive",
                "missing_evidence": [
                    "Evidence proving behavior differs from expected blocking or random-object behavior"
                ],
                "next_actions": [
                    "Compare the candidate with random-object and expected-blocking behavior.",
                    "Reject the candidate if no sensitive data or authorization boundary violation is proven.",
                ],
                "source": "manual-json-batch:002.json",
            }
        ],
        "findings": [],
    }


def test_case_chat_cli_writes_json(tmp_path):
    case_file = tmp_path / "case-summary.json"
    output_file = tmp_path / "case-chat.json"
    case_file.write_text(json.dumps(_case_summary()))

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what should I test next?",
            "--json-output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert "Local Research Chat" in result.output
    assert "Answer" in result.output
    assert output_file.exists()

    data = json.loads(output_file.read_text())
    assert data["intent"] == "next-tests"
    assert data["cited_endpoints"] == ["/api/accounts/123/users/999"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_case_chat_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(
        app,
        [
            "case-chat",
            str(tmp_path / "missing.json"),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 1
    assert "Case summary JSON not found" in result.output


def test_case_chat_cli_invalid_json_exits_nonzero(tmp_path):
    case_file = tmp_path / "bad.json"
    case_file.write_text("{not json")

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case summary JSON" in result.output


def test_case_chat_cli_wrong_kind_exits_nonzero(tmp_path):
    case_file = tmp_path / "case.json"
    case_file.write_text(json.dumps({"kind": "wrong"}))

    result = runner.invoke(
        app,
        [
            "case-chat",
            str(case_file),
            "--question",
            "what next?",
        ],
    )

    assert result.exit_code == 2
    assert "Invalid case chat input" in result.output
