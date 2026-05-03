from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.research_state_apply import apply_research_state_update_plan
from bugintel.core.research_state_update import build_research_state_update_plan


def _state_and_update(validation_result="supported"):
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    state = build_research_state_from_orchestration(orchestration.to_dict()).to_dict()
    update = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        validation_result,
        note="Validated with controlled accounts.",
    ).to_dict()
    return state, update


def test_apply_supported_update_plan_changes_local_copy():
    state, update = _state_and_update("supported")

    result = apply_research_state_update_plan(state, update)
    data = result.to_dict()
    endpoint = data["updated_research_state"]["endpoints"][0]

    assert data["target_name"] == "demo"
    assert data["validation_result"] == "supported"
    assert data["planning_only"] is True
    assert endpoint["triage_state"] == "report-candidate"
    assert endpoint["validation_note"] == "Validated with controlled accounts."
    assert all(patch["applied"] is True for patch in data["applied_patches"])


def test_apply_rejected_update_plan_deprioritizes():
    state, update = _state_and_update("rejected")

    result = apply_research_state_update_plan(state, update)
    endpoint = result.to_dict()["updated_research_state"]["endpoints"][0]

    assert endpoint["triage_state"] == "deprioritized"
    assert all(hypothesis["status"] == "rejected" for hypothesis in endpoint["hypotheses"])


def test_apply_update_plan_does_not_mutate_original():
    state, update = _state_and_update("supported")

    result = apply_research_state_update_plan(state, update)

    assert state["endpoints"][0]["triage_state"] == "ready-for-manual-validation"
    assert result.to_dict()["updated_research_state"]["endpoints"][0]["triage_state"] == "report-candidate"


def test_apply_unknown_path_marks_patch_not_applied():
    state, update = _state_and_update("supported")
    update["actions"].append({
        "path": "endpoints[/api/accounts/123/users/{id}/permissions].unknown",
        "old_value": None,
        "new_value": "x",
        "reason": "unknown path",
    })

    result = apply_research_state_update_plan(state, update)
    patches = result.to_dict()["applied_patches"]

    assert patches[-1]["applied"] is False
