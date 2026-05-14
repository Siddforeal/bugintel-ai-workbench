import json

import pytest

from bugintel.core.brain_chat import build_brain_chat_reply
from bugintel.core.brain_chat_demo_flow import run_brain_chat_demo_flow


def test_run_brain_chat_demo_flow_builds_usable_brain_state(tmp_path):
    endpoints = tmp_path / "endpoints.txt"
    endpoints.write_text(
        "\n".join(
            [
                "/api/accounts/123/users/{id}/permissions",
                "/api/files/{id}/download",
                "/api/status",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "case"
    flow = run_brain_chat_demo_flow(
        endpoints_file=endpoints,
        target_name="demo.local",
        output_dir=output_dir,
    )
    data = flow.to_dict()

    assert data["kind"] == "brain_chat_demo_flow"
    assert data["recommendation"] == "ready-for-brain-chat"
    assert data["target_name"] == "demo.local"
    assert data["focus_endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["safety"]["network_interaction"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["llm_provider_calls"] is False
    assert data["safety"]["vulnerability_confirmation"] is False

    expected_files = [
        "orchestration.json",
        "research-state.json",
        "ai-brain.json",
        "brain-prompt.json",
        "brain-review.json",
        "brain-decision.json",
        "brain-approval.json",
        "tool-request-manifest.json",
        "tool-execution-gate.json",
        "brain-state-export.json",
        "brain-chat-demo-flow.json",
        "brain/03-ai-brain.json",
        "brain/06-brain-decision.json",
        "brain/07-brain-approval.json",
        "brain/09-tool-execution-gate.json",
    ]

    for relative in expected_files:
        assert (output_dir / relative).exists(), relative

    reply = build_brain_chat_reply(
        "What is blocking validation?",
        output_dir / "brain",
    )
    assert "Validation is currently blocked" in reply.answer
    assert reply.focus_endpoint == "/api/accounts/123/users/{id}/permissions"


def test_brain_chat_demo_flow_markdown_is_readable(tmp_path):
    endpoints = tmp_path / "endpoints.txt"
    endpoints.write_text("/api/admin/users\n/api/status\n", encoding="utf-8")

    flow = run_brain_chat_demo_flow(
        endpoints_file=endpoints,
        target_name="demo.local",
        output_dir=tmp_path / "case",
    )
    markdown = flow.to_markdown()

    assert "# Brain Chat Demo Flow" in markdown
    assert "ready-for-brain-chat" in markdown
    assert "blackhole brain-chat" in markdown
    assert "This command builds local planning artifacts only." in markdown
    assert "\\n" not in markdown


def test_brain_chat_demo_flow_requires_endpoint_file(tmp_path):
    with pytest.raises(ValueError):
        run_brain_chat_demo_flow(
            endpoints_file=tmp_path / "missing.txt",
            target_name="demo.local",
            output_dir=tmp_path / "case",
        )


def test_brain_chat_demo_flow_skips_blank_and_comment_lines(tmp_path):
    endpoints = tmp_path / "endpoints.txt"
    endpoints.write_text(
        "\n# comment\n/api/admin/users\n\n/api/status\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "case"
    run_brain_chat_demo_flow(
        endpoints_file=endpoints,
        target_name="demo.local",
        output_dir=output_dir,
    )

    orchestration = json.loads((output_dir / "orchestration.json").read_text())
    assert orchestration["endpoints"] == ["/api/admin/users", "/api/status"]
