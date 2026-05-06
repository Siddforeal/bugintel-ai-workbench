import pytest

from bugintel.core.result_evidence_chat_provider_dry_run import build_case_chat_provider_dry_run


def _prompt_package():
    return {
        "kind": "result_evidence_case_chat_prompt_package",
        "prompt_package": {
            "system_prompt": "You are a safe assistant for authorized testing.",
            "user_prompt": "Review local artifacts only and suggest read-only checks.",
            "redaction_applied": False,
            "source": "result-evidence-case-chat-prompt",
            "safety_notes": [
                "Provider execution is not performed by this command.",
                "LLM output must be treated as suggestions, not confirmed findings.",
            ],
        },
    }


def test_case_chat_provider_dry_run_is_disabled_and_local():
    dry_run = build_case_chat_provider_dry_run(_prompt_package())
    data = dry_run.to_dict()

    assert data["kind"] == "result_evidence_case_chat_provider_dry_run"
    assert data["provider_name"] == "disabled"
    assert data["audit_status"] == "pass"
    assert data["gate_allowed"] is False
    assert data["disabled_provider_status"] == "disabled"
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_case_chat_provider_dry_run_reports_blocked_audit():
    package = _prompt_package()
    package["prompt_package"]["user_prompt"] = "token=secret-value"

    dry_run = build_case_chat_provider_dry_run(package)

    assert dry_run.audit_status == "blocked"
    assert dry_run.gate_allowed is False
    assert dry_run.disabled_provider_status == "disabled"


def test_case_chat_provider_dry_run_unsupported_provider():
    dry_run = build_case_chat_provider_dry_run(_prompt_package(), provider_name="openai")

    assert dry_run.provider_name == "openai"
    assert dry_run.gate_allowed is False
    assert "Unsupported LLM provider" in dry_run.gate_reason


def test_case_chat_provider_dry_run_markdown_is_readable():
    dry_run = build_case_chat_provider_dry_run(_prompt_package())
    markdown = dry_run.to_markdown()

    assert "# Case Chat Provider Dry Run" in markdown
    assert "Provider Execution Performed: false" in markdown
    assert "It does not call any real LLM provider." in markdown
    assert "\\n" not in markdown


def test_case_chat_provider_dry_run_rejects_wrong_kind():
    with pytest.raises(ValueError):
        build_case_chat_provider_dry_run({"kind": "wrong"})


def test_case_chat_provider_dry_run_requires_prompt_package_object():
    with pytest.raises(ValueError):
        build_case_chat_provider_dry_run({"kind": "result_evidence_case_chat_prompt_package"})
