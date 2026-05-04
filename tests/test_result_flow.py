from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.result_flow import build_result_flow


def _state():
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    return build_research_state_from_orchestration(orchestration.to_dict()).to_dict()


def test_result_flow_supported_updates_local_copy():
    flow = build_result_flow(
        research_state_data=_state(),
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=200,
        expected_status=403,
        note="Observed foreign account private data and permission bypass.",
    )
    data = flow.to_dict()

    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["interpretation"]["suggested_result"] == "supported"
    assert data["update_plan"]["validation_result"] == "supported"

    endpoint_state = data["apply_result"]["updated_research_state"]["endpoints"][0]
    assert endpoint_state["triage_state"] == "report-candidate"


def test_result_flow_rejected_deprioritizes_local_copy():
    flow = build_result_flow(
        research_state_data=_state(),
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=403,
        expected_status=403,
        note="Access denied. Expected behavior. No sensitive data.",
    )
    data = flow.to_dict()

    assert data["interpretation"]["suggested_result"] == "rejected"
    assert data["update_plan"]["validation_result"] == "rejected"

    endpoint_state = data["apply_result"]["updated_research_state"]["endpoints"][0]
    assert endpoint_state["triage_state"] == "deprioritized"


def test_result_flow_needs_more_evidence():
    flow = build_result_flow(
        research_state_data=_state(),
        endpoint="/api/accounts/123/users/{id}/permissions",
        observed_status=404,
        note="Same as random.",
    )
    data = flow.to_dict()

    assert data["interpretation"]["suggested_result"] == "needs-more-evidence"
    assert data["update_plan"]["validation_result"] == "needs-more-evidence"
