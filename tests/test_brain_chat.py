import json

from bugintel.core.brain_chat import build_brain_chat_reply


def _write_state(tmp_path):
    (tmp_path / "03-ai-brain.json").write_text(json.dumps({
        "target_name": "demo",
        "focus_queue": [
            {
                "endpoint": "/api/accounts/123/users/{id}/permissions",
                "priority_band": "critical",
                "priority_score": 80,
                "reason": "High-signal endpoint with open hypotheses.",
            }
        ],
    }))
    (tmp_path / "06-brain-decision.json").write_text(json.dumps({
        "decision": "blocked-pending-scope-and-controls",
    }))
    (tmp_path / "07-brain-approval.json").write_text(json.dumps({
        "approval_status": "blocked-pending-approval",
    }))
    (tmp_path / "09-tool-execution-gate.json").write_text(json.dumps({
        "gate_decision": "blocked-manifest-execution-disabled",
        "execution_allowed": False,
    }))


def test_brain_chat_replies_to_hello(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("hello", tmp_path)
    data = reply.to_dict()

    assert data["target_name"] == "demo"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["execution_allowed"] is False
    assert "Hello Sidd" in data["answer"]
    assert "blocked-manifest-execution-disabled" in data["answer"]


def test_brain_chat_status_reply(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("status", tmp_path)

    assert "Current focus endpoint" in reply.answer
    assert "critical/80" in reply.answer


def test_brain_chat_next_step_reply(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("what should we do next?", tmp_path)

    assert "Confirm scope and authorization" in reply.answer
    assert "Keep execution disabled" in reply.answer


def test_brain_chat_execution_refusal(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("can we run curl?", tmp_path)

    assert "Execution is not allowed" in reply.answer
    assert "human-approved execution layer" in reply.answer


def test_brain_chat_handles_missing_state(tmp_path):
    reply = build_brain_chat_reply("hello", tmp_path)

    assert reply.target_name == "unknown-target"
    assert reply.focus_endpoint is None
    assert "Hello Sidd" in reply.answer


def test_brain_chat_routes_blocking_validation_question(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("What is blocking validation right now?", tmp_path)

    assert "Validation is currently blocked" in reply.answer
    assert "blocked-pending-scope-and-controls" in reply.answer
    assert "blocked-pending-approval" in reply.answer


def test_brain_chat_routes_approval_question(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("What approvals are missing?", tmp_path)

    assert "Approvals still required" in reply.answer
    assert "scope" in reply.answer.lower()
    assert "controlled" in reply.answer.lower()


def test_brain_chat_routes_evidence_question(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("What evidence do we need?", tmp_path)

    assert "Useful evidence types" in reply.answer
    assert "baseline request/response sample" in reply.answer
    assert "authorization decision diff" in reply.answer


def test_brain_chat_routes_reportability_question(tmp_path):
    _write_state(tmp_path)

    reply = build_brain_chat_reply("Is this reportable?", tmp_path)

    assert "not reportable yet" in reply.answer.lower()
    assert "No vulnerability is confirmed" in reply.answer
