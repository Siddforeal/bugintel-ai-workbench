import json

from typer.testing import CliRunner

from bugintel.cli import app


runner = CliRunner()


def test_interpret_result_cli_writes_json(tmp_path):
    output = tmp_path / "interpretation.json"

    result = runner.invoke(
        app,
        [
            "interpret-result",
            "--endpoint",
            "/api/accounts/123/users/{id}/permissions",
            "--observed-status",
            "200",
            "--expected-status",
            "403",
            "--note",
            "Observed foreign account private data and permission bypass.",
            "--json-output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "Result Interpretation" in result.output
    assert "supported" in result.output
    assert output.exists()

    data = json.loads(output.read_text())
    assert data["suggested_result"] == "supported"
    assert data["planning_only"] is True
    assert data["signals"]


def test_interpret_result_cli_rejected_for_blocked_case():
    result = runner.invoke(
        app,
        [
            "interpret-result",
            "--endpoint",
            "/api/files/{id}/download",
            "--observed-status",
            "403",
            "--expected-status",
            "403",
            "--note",
            "Access denied. Expected behavior. No sensitive data.",
        ],
    )

    assert result.exit_code == 0
    assert "rejected" in result.output


def test_interpret_result_cli_needs_more_evidence_for_inconclusive_case():
    result = runner.invoke(
        app,
        [
            "interpret-result",
            "--endpoint",
            "/api/status",
            "--observed-status",
            "404",
            "--note",
            "Same as random.",
        ],
    )

    assert result.exit_code == 0
    assert "needs-more-evidence" in result.output
