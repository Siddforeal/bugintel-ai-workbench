from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.result_interpreter import interpret_validation_result
from bugintel.core.result_update_bridge import build_update_plan_from_interpretation


def _state():
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    return build_research_state_from_orchestration(orchestration.to_dict()).to_dict()


def test_bridge_builds_supported_update_plan():
    interpretation = interpret_validation_result(
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=200,
        expected_status=403,
        note="Observed foreign account private data and permission bypass.",
    ).to_dict()

    plan = build_update_plan_from_interpretation(_state(), interpretation)
    data = plan.to_dict()

    assert data["validation_result"] == "supported"
    assert any(action["new_value"] == "report-candidate" for action in data["actions"])
    assert any("Result interpreter suggested supported" in str(action["new_value"]) for action in data["actions"])


def test_bridge_builds_rejected_update_plan():
    interpretation = interpret_validation_result(
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=403,
        expected_status=403,
        note="Access denied. Expected behavior. No sensitive data.",
    ).to_dict()

    plan = build_update_plan_from_interpretation(_state(), interpretation)
    data = plan.to_dict()

    assert data["validation_result"] == "rejected"
    assert any(action["new_value"] == "deprioritized" for action in data["actions"])


def test_bridge_defaults_unknown_result_to_needs_more_evidence():
    interpretation = {
        "endpoint": "/api/accounts/123/users/{id}/permissions",
        "suggested_result": "confirmed",
        "confidence": "low",
        "rationale": "Invalid result should not be trusted.",
    }

    plan = build_update_plan_from_interpretation(_state(), interpretation)
    data = plan.to_dict()

    assert data["validation_result"] == "needs-more-evidence"
    assert any(action["new_value"] == "needs-more-evidence" for action in data["actions"])


def test_bridge_uses_custom_note():
    interpretation = interpret_validation_result(
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=200,
        expected_status=403,
        note="Observed foreign account private data.",
    ).to_dict()

    plan = build_update_plan_from_interpretation(
        _state(),
        interpretation,
        note="Human reviewed and approved this interpretation.",
    )
    data = plan.to_dict()

    assert any(action["new_value"] == "Human reviewed and approved this interpretation." for action in data["actions"])
