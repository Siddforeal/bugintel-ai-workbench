import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def _validation_plan_json():
    return {
        "kind": "result_evidence_validation_plan",
        "count": 2,
        "plans": [
            {
                "endpoint": "/api/accounts/123/users/999",
                "hypothesis_class": "object-or-tenant-authorization-boundary-candidate",
                "confidence": "medium-high",
                "evidence_strength": "strong-candidate",
                "severity_hint": "candidate-high-if-sensitive-data-confirmed",
                "priority": "high",
                "source": "manual-json-batch:001.json",
                "steps": [{"title": f"step-{i}"} for i in range(7)],
                "stop_conditions": [
                    "Stop if the asset, endpoint, account, tenant, or object is out of scope.",
                    "Stop before destructive testing.",
                ],
                "report_readiness_checks": [
                    "Scope is confirmed.",
                    "Own-object baseline is captured.",
                    "Foreign-object or second-account behavior is captured.",
                    "Random-object baseline is captured.",
                    "Raw requests and responses are preserved with secrets redacted.",
                    "The finding draft does not overclaim impact.",
                    "Sensitive or tenant-specific data/state is identified.",
                    "Authorization boundary expectation is explained.",
                    "Reproduction is repeatable with controlled accounts.",
                    "Impact is tied directly to proven evidence.",
                ],
            },
            {
                "endpoint": "/api/random",
                "hypothesis_class": "likely-expected-blocking-or-false-positive",
                "confidence": "medium",
                "evidence_strength": "weak-for-finding",
                "severity_hint": "not-reportable-with-current-evidence",
                "priority": "low",
                "source": "manual-json-batch:002.json",
                "steps": [{"title": "Confirm expected blocking"}],
                "stop_conditions": [
                    "Stop if the asset, endpoint, account, tenant, or object is out of scope.",
                    "Stop and mark rejected if all baselines match expected blocking.",
                ],
                "report_readiness_checks": [
                    "Scope is confirmed.",
                    "Random-object baseline is captured.",
                ],
            },
        ],
    }


def test_result_evidence_case_summary_cli_writes_markdown_and_json(tmp_path):
    validation_plan_file = tmp_path / "validation-plan.json"
    output_file = tmp_path / "case-summary.md"
    json_output = tmp_path / "case-summary.json"

    validation_plan_file.write_text(json.dumps(_validation_plan_json()))

    result = runner.invoke(
        app,
        [
            "result-evidence-case-summary",
            str(validation_plan_file),
            "--output-file",
            str(output_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Evidence Case Summary" in result.output
    assert output_file.exists()
    assert json_output.exists()

    markdown = output_file.read_text()
    assert "# Case Intelligence Summary" in markdown
    assert "\\n" not in markdown
    assert "Strongest Candidates" in markdown
    assert "Case-Level Next Actions" in markdown

    data = json.loads(json_output.read_text())
    assert data["kind"] == "result_evidence_case_summary"
    assert data["count"] == 2
    assert len(data["strongest_candidates"]) == 1
    assert len(data["weak_or_rejected_candidates"]) == 1
    assert data["safety"]["local_only"] is True
    assert data["safety"]["vulnerability_confirmation"] is False


def test_result_evidence_case_summary_cli_missing_file_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["result-evidence-case-summary", str(tmp_path / "missing.json")])

    assert result.exit_code == 1
    assert "Result evidence validation plan JSON not found" in result.output


def test_result_evidence_case_summary_cli_invalid_json_exits_nonzero(tmp_path):
    validation_plan_file = tmp_path / "bad.json"
    validation_plan_file.write_text("{not json")

    result = runner.invoke(app, ["result-evidence-case-summary", str(validation_plan_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence validation plan JSON" in result.output


def test_result_evidence_case_summary_cli_wrong_kind_exits_nonzero(tmp_path):
    validation_plan_file = tmp_path / "validation-plan.json"
    validation_plan_file.write_text(json.dumps({"kind": "wrong", "plans": []}))

    result = runner.invoke(app, ["result-evidence-case-summary", str(validation_plan_file)])

    assert result.exit_code == 2
    assert "Invalid result evidence case summary input" in result.output
