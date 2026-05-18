from bugintel.core.brain_chat import BrainChatReply
from bugintel.core.brain_chat_session import BrainChatSession, append_brain_chat_turn
from bugintel.core.brain_chat_session_next_step import build_brain_chat_session_next_step_plan


def _reply(question="What evidence do we need?"):
    return BrainChatReply(
        question=question,
        answer="Evidence planning answer.",
        target_name="demo.local",
        focus_endpoint="/api/accounts/123/users/{id}/permissions",
        decision="blocked-pending-scope-and-controls",
        approval_status="blocked-pending-approval",
        execution_gate="blocked-manifest-execution-disabled",
        execution_allowed=False,
    )


def test_brain_chat_session_next_step_plan_from_blocked_session():
    session = BrainChatSession()
    session = append_brain_chat_turn(session, _reply("What should I test first?"))
    session = append_brain_chat_turn(session, _reply("What evidence do we need?"))

    plan = build_brain_chat_session_next_step_plan(session)
    data = plan.to_dict()

    assert data["kind"] == "brain_chat_session_next_step_plan"
    assert data["recommendation"] == "resolve-blockers-before-validation"
    assert data["current_focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert "Scope" in data["current_blocker"]
    assert "Authorization decision diff" in data["next_evidence"]
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_brain_chat_session_next_step_markdown_is_readable():
    session = append_brain_chat_turn(BrainChatSession(), _reply())
    plan = build_brain_chat_session_next_step_plan(session)
    markdown = plan.to_markdown()

    assert "# Brain Chat Session Next-Step Plan" in markdown
    assert "Next Evidence" in markdown
    assert "Do Not Do Yet" in markdown
    assert "\\n" not in markdown
