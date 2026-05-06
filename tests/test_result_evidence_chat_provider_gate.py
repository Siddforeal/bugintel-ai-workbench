import pytest

from bugintel.core.result_evidence_chat_provider_gate import build_case_chat_provider_gate


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


def test_case_chat_provider_gate_blocks_disabled_provider():
    gate = build_case_chat_provider_gate(_prompt_package())
    data = gate.to_dict()

    assert data["kind"] == "result_evidence_case_chat_provider_gate"
    assert data["allowed"] is False
    assert data["provider_name"] == "disabled"
    assert data["audit_status"] == "pass"
    assert "disabled" in data["reason"]
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False


def test_case_chat_provider_gate_blocks_unsupported_provider():
    gate = build_case_chat_provider_gate(_prompt_package(), provider_name="openai")

    assert gate.allowed is False
    assert gate.provider_name == "openai"
    assert "Unsupported LLM provider" in gate.reason


def test_case_chat_provider_gate_audits_sensitive_prompt():
    package = _prompt_package()
    package["prompt_package"]["user_prompt"] = "token=secret-value"

    gate = build_case_chat_provider_gate(package)

    assert gate.allowed is False
    assert gate.audit_status == "blocked"


def test_case_chat_provider_gate_markdown_is_readable():
    gate = build_case_chat_provider_gate(_prompt_package())
    markdown = gate.to_markdown()

    assert "# Case Chat Provider Gate" in markdown
    assert "Provider Execution Performed: false" in markdown
    assert "It does not call any LLM provider." in markdown
    assert "\\n" not in markdown


def test_case_chat_provider_gate_rejects_wrong_kind():
    with pytest.raises(ValueError):
        build_case_chat_provider_gate({"kind": "wrong"})


def test_case_chat_provider_gate_requires_prompt_package_object():
    with pytest.raises(ValueError):
        build_case_chat_provider_gate({"kind": "result_evidence_case_chat_prompt_package"})
