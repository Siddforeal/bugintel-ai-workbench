import pytest

from bugintel.core.result_evidence_chat_provider_result import import_case_chat_provider_result


def _prompt_package():
    return {
        "kind": "result_evidence_case_chat_prompt_package",
        "source": "result-evidence-case-chat-prompt",
        "prompt_package": {
            "system_prompt": "safe",
            "user_prompt": "safe",
            "redaction_applied": False,
        },
    }


def test_import_case_chat_provider_result_marks_untrusted():
    imported = import_case_chat_provider_result(
        """
        This may be useful.
        - Validate own-object baseline.
        - Confirm random-object behavior.
        Do not submit until verified.
        """,
        _prompt_package(),
    )
    data = imported.to_dict()

    assert data["kind"] == "result_evidence_case_chat_provider_result"
    assert data["untrusted_suggestion"] is True
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False
    assert "Validate own-object baseline." in data["suggested_actions"]
    assert "Confirm random-object behavior." in data["suggested_actions"]


def test_import_case_chat_provider_result_flags_overclaims():
    imported = import_case_chat_provider_result(
        "This is a confirmed vulnerability with high severity. Run this command.",
        _prompt_package(),
    )
    data = imported.to_dict()

    assert "overclaim-confirmed-vulnerability" in data["warning_flags"]
    assert "severity-claim-needs-proof" in data["warning_flags"]
    assert "manual-command-review-needed" in data["warning_flags"]


def test_import_case_chat_provider_result_markdown_is_readable():
    imported = import_case_chat_provider_result("Review the evidence.", _prompt_package())
    markdown = imported.to_markdown()

    assert "# Imported Case Chat Provider Result" in markdown
    assert "Untrusted suggestion: true" in markdown
    assert "Provider execution performed by Blackhole: false" in markdown
    assert "\\n" not in markdown


def test_import_case_chat_provider_result_rejects_wrong_prompt_kind():
    with pytest.raises(ValueError):
        import_case_chat_provider_result("output", {"kind": "wrong"})


def test_import_case_chat_provider_result_requires_output():
    with pytest.raises(ValueError):
        import_case_chat_provider_result("  ", _prompt_package())
