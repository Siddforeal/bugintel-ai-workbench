import pytest

from bugintel.core.result_evidence_chat_router import route_chat_context


def test_route_chat_context_case_summary():
    route = route_chat_context({"kind": "result_evidence_case_summary"})
    data = route.to_dict()

    assert data["kind"] == "result_evidence_chat_context_route"
    assert data["artifact_kind"] == "result_evidence_case_summary"
    assert data["recommended_command"] == "case-chat-context"
    assert "what should I test next?" in data["supported_questions"]
    assert data["safety"]["local_only"] is True
    assert data["safety"]["llm_provider_calls"] is False


def test_route_chat_context_priority_ranking():
    route = route_chat_context({"kind": "result_evidence_priority_ranking"})

    assert route.artifact_label == "Priority ranking"
    assert route.recommended_command == "result-evidence-multi-agent-review"
    assert any("highest priority" in question for question in route.supported_questions)


def test_route_chat_context_multi_agent_review():
    route = route_chat_context({"kind": "result_evidence_multi_agent_review_plan"})

    assert route.artifact_label == "Multi-agent review plan"
    assert route.recommended_command == "case-chat-context"
    assert "what do reviewers think?" in route.supported_questions


def test_route_chat_context_report_assistant():
    route = route_chat_context({"kind": "result_evidence_report_assistant"})

    assert route.artifact_label == "Case-to-report assistant draft"
    assert "what should the final report focus on?" in route.supported_questions


def test_route_chat_context_session_memory():
    route = route_chat_context({"kind": "result_evidence_case_chat_session"})

    assert route.artifact_label == "Local case-chat session memory"
    assert "summarize chat memory" in route.supported_questions


def test_route_chat_context_unknown_kind_is_safe():
    route = route_chat_context({"kind": "unknown_artifact"})
    data = route.to_dict()

    assert data["artifact_label"] == "Unknown or unsupported artifact"
    assert data["recommended_command"] == "manual-review"
    assert data["safety"]["vulnerability_confirmation"] is False


def test_route_chat_context_markdown_is_readable():
    route = route_chat_context({"kind": "result_evidence_case_summary"})
    markdown = route.to_markdown()

    assert "# Chat Context Route" in markdown
    assert "\\n" not in markdown
    assert "case-chat-context" in markdown
    assert "No LLM provider calls." in markdown


def test_route_chat_context_requires_object():
    with pytest.raises(ValueError):
        route_chat_context("bad")  # type: ignore[arg-type]


def test_route_chat_context_requires_kind():
    with pytest.raises(ValueError):
        route_chat_context({})
