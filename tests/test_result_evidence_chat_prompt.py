import pytest

from bugintel.core.result_evidence_chat_prompt import (
    build_case_chat_prompt_package,
    render_case_chat_prompt_package_markdown,
)


def _case_memory():
    return {
        "kind": "result_evidence_case_memory",
        "top_endpoint": "/api/high",
        "cited_endpoints": ["/api/high"],
        "open_next_actions": ["Capture own-object baseline."],
        "missing_evidence": ["Random-object baseline"],
        "safety": {
            "local_only": True,
            "llm_provider_calls": False,
            "vulnerability_confirmation": False,
        },
    }


def _grounded_answer():
    return {
        "kind": "result_evidence_grounded_answer",
        "answer": "Not ready yet.",
        "intent": "report-ready",
        "grounding": [
            {
                "artifact": "case-memory",
                "path": "missing_evidence[0]",
                "value": "Random-object baseline",
                "reason": "Shows missing evidence.",
            }
        ],
        "cited_endpoints": ["/api/high"],
        "next_actions": ["Capture random-object baseline."],
    }


def test_build_case_chat_prompt_package_is_safe_and_offline():
    package = build_case_chat_prompt_package(
        _case_memory(),
        "can I submit this?",
        grounded_answer=_grounded_answer(),
    )
    data = package.to_dict()

    assert data["kind"] == "result_evidence_case_chat_prompt_package"
    assert data["question"] == "can I submit this?"
    assert data["artifact_kinds"] == [
        "result_evidence_case_memory",
        "result_evidence_grounded_answer",
    ]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["provider_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False
    assert "Use only the local artifacts" in data["prompt_package"]["system_prompt"]
    assert "Random-object baseline" in data["prompt_package"]["user_prompt"]


def test_build_case_chat_prompt_package_redacts_sensitive_values():
    memory = _case_memory()
    memory["token"] = "secret=supersecret"
    memory["email"] = "sidd@example.com"

    package = build_case_chat_prompt_package(memory, "what next?")
    prompt = package.prompt_package.to_dict()

    assert prompt["redaction_applied"] is True
    assert "sidd@example.com" not in prompt["user_prompt"]
    assert "supersecret" not in prompt["user_prompt"]


def test_render_case_chat_prompt_package_markdown_contains_prompts():
    package = build_case_chat_prompt_package(_case_memory(), "what next?")
    markdown = render_case_chat_prompt_package_markdown(package)

    assert "# Case Chat LLM Prompt Package" in markdown
    assert "Provider Execution: false" in markdown
    assert "## System Prompt" in markdown
    assert "## User Prompt" in markdown
    assert "\\n" not in markdown


def test_build_case_chat_prompt_package_rejects_wrong_memory_kind():
    with pytest.raises(ValueError):
        build_case_chat_prompt_package({"kind": "wrong"}, "what next?")


def test_build_case_chat_prompt_package_rejects_wrong_grounded_kind():
    with pytest.raises(ValueError):
        build_case_chat_prompt_package(_case_memory(), "what next?", grounded_answer={"kind": "wrong"})


def test_build_case_chat_prompt_package_requires_question():
    with pytest.raises(ValueError):
        build_case_chat_prompt_package(_case_memory(), "  ")
