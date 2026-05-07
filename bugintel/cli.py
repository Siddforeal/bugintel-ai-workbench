"""
Blackhole AI Workbench CLI.

Commands:
- version
- scope-check
- mine-endpoints
- compare-responses
- build-tree
- plan-curl
- run-curl
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.markup import escape
from bugintel.ui.intro import IntroConfig, show_intro

from bugintel.agents.report_agent import save_evidence_report
from bugintel.agents.recon_agent import analyze_html
from bugintel.agents.web_recon_agent import run_website_recon
from bugintel.agents.js_agent import collect_js_sources
from bugintel.agents.ios_agent import analyze_ios_plist
from bugintel.agents.android_agent import analyze_android_manifest
from bugintel.analyzers.endpoint_miner import mine_endpoints
from bugintel.analyzers.http_parser import parse_http_response
from bugintel.analyzers.response_diff import compare_responses, summarize_response
from bugintel.core.evidence_store import EvidenceStore
from bugintel.core.scope_guard import load_scope_from_dict
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.endpoint_investigation import build_endpoint_investigation_profile
from bugintel.core.endpoint_priority import prioritize_endpoints, score_endpoint
from bugintel.core.attack_surface import build_attack_surface_map
from bugintel.core.evidence_requirements import build_evidence_requirement_plan
from bugintel.core.evidence_workspace import build_evidence_workspace_manifest, materialize_evidence_workspace
from bugintel.core.report_draft import build_report_draft, render_report_draft_markdown
from bugintel.core.validation_runbook import build_validation_runbook, render_validation_runbook_markdown
from bugintel.core.research_state import build_research_state_from_orchestration, render_research_state_markdown
from bugintel.core.research_state_update import build_research_state_update_plan, render_research_state_update_plan_markdown
from bugintel.core.result_interpreter import interpret_validation_result
from bugintel.core.result_evidence import import_result_evidence, import_result_evidence_batch, review_result_evidence_batch
from bugintel.core.result_evidence_report import render_result_evidence_review_report
from bugintel.core.result_evidence_finding_draft import render_result_evidence_finding_draft
from bugintel.core.result_evidence_finding_package import build_result_evidence_finding_package
from bugintel.core.result_evidence_hypothesis import generate_result_evidence_hypotheses
from bugintel.core.result_evidence_validation_plan import build_result_evidence_validation_plan
from bugintel.core.result_evidence_case_summary import build_result_evidence_case_summary
from bugintel.core.result_evidence_chat import answer_case_question
from bugintel.core.result_evidence_chat_session import append_case_chat_turn_to_file
from bugintel.core.result_evidence_priority_ranking import build_result_evidence_priority_ranking
from bugintel.core.result_evidence_multi_agent_review import build_result_evidence_multi_agent_review_plan
from bugintel.core.result_evidence_report_assistant import build_case_report_assistant_draft
from bugintel.core.result_evidence_chat_context import answer_case_context_question
from bugintel.core.result_evidence_grounding import build_grounded_answer
from bugintel.core.result_evidence_case_memory import build_result_evidence_case_memory
from bugintel.core.result_evidence_chat_prompt import build_case_chat_prompt_package, render_case_chat_prompt_package_markdown
from bugintel.core.result_evidence_chat_provider_gate import build_case_chat_provider_gate
from bugintel.core.result_evidence_chat_provider_dry_run import build_case_chat_provider_dry_run
from bugintel.core.result_evidence_chat_provider_result import import_case_chat_provider_result
from bugintel.core.result_evidence_chat_router import route_chat_context
from bugintel.core.result_update_bridge import build_update_plan_from_interpretation
from bugintel.core.result_flow import build_result_flow
from bugintel.core.research_state_apply import apply_research_state_update_plan
from bugintel.core.case_timeline import build_case_timeline, render_case_timeline_markdown
from bugintel.core.case_summary import build_case_summary, render_case_summary_markdown
from bugintel.core.ai_brain import build_ai_brain_plan, render_ai_brain_plan_markdown
from bugintel.core.brain_prompt import build_brain_prompt_package, render_brain_prompt_package_markdown
from bugintel.core.brain_review import build_brain_review, render_brain_review_markdown
from bugintel.core.brain_decision import build_brain_decision_gate, render_brain_decision_gate_markdown
from bugintel.core.brain_approval import build_brain_approval_packet, render_brain_approval_packet_markdown
from bugintel.core.tool_request_manifest import build_tool_request_manifest, render_tool_request_manifest_markdown
from bugintel.core.tool_execution_gate import build_tool_execution_gate, render_tool_execution_gate_markdown
from bugintel.core.brain_chat import build_brain_chat_reply
from bugintel.core.brain_chat_session import append_brain_chat_turn, load_brain_chat_session, save_brain_chat_session
from bugintel.core.task_tree import build_endpoint_task_tree, render_tree
from bugintel.core.research_planner import build_research_plan_from_browser_evidence, render_research_plan_markdown, ResearchPlan, ResearchHypothesis, ResearchRecommendation, EvidenceReference
from bugintel.core.llm_prompt import LLMPromptPackage, build_llm_prompt_package_from_research_plan, render_llm_prompt_package_markdown
from bugintel.core.llm_provider import run_disabled_llm_provider
from bugintel.core.llm_provider_config import LLMProviderConfig, validate_provider_config
from bugintel.core.llm_safety import audit_llm_prompt_package, render_llm_prompt_safety_markdown
from bugintel.integrations.kali_runner import build_curl_plan, execute_curl_plan
from bugintel.integrations.playwright_runner import (
    BrowserAction,
    BrowserCaptureResult,
    BrowserExecutionConfig,
    BrowserPlan,
    PlaywrightArtifactPlan,
    PlaywrightExecutionRequest,
    PlaywrightExecutionSafetyError,
    build_browser_plan,
    build_playwright_adapter_context,
    build_playwright_execution_preview,
    build_playwright_execution_request,
    execute_playwright_plan,
    load_browser_capture_result_from_artifacts,
)
from bugintel.integrations.web_fetcher import fetch_web_page
from bugintel.integrations.har_importer import load_har

app = typer.Typer(
    name="bugintel",
    help="Blackhole AI Workbench: human-in-the-loop vulnerability discovery and bug intelligence.",
no_args_is_help=False,
)

console = Console()





def _print_evidence_requirements_table(evidence_requirement_plan, title: str = "Evidence Requirements") -> None:
    """Print evidence requirement counts when an orchestration plan includes them."""
    if evidence_requirement_plan is None or not evidence_requirement_plan.endpoint_plans:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Requirements", justify="right")
    table.add_column("Redaction", justify="right")
    table.add_column("Approval", justify="right")

    for index, endpoint_plan in enumerate(evidence_requirement_plan.endpoint_plans, start=1):
        redaction_count = sum(1 for requirement in endpoint_plan.requirements if requirement.redaction_required)
        approval_count = sum(1 for requirement in endpoint_plan.requirements if requirement.human_approval_required)

        table.add_row(
            str(index),
            endpoint_plan.endpoint,
            str(len(endpoint_plan.requirements)),
            str(redaction_count),
            str(approval_count),
        )

    console.print(table)

def _print_attack_surface_table(attack_surface_map, title: str = "Attack Surface Groups") -> None:
    """Print attack-surface groups when an orchestration plan includes them."""
    if attack_surface_map is None or not attack_surface_map.groups:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Group")
    table.add_column("Count", justify="right")
    table.add_column("Max Score", justify="right")
    table.add_column("Priority Hint")

    for index, group in enumerate(attack_surface_map.groups, start=1):
        table.add_row(
            str(index),
            group.spec.name,
            str(group.count),
            str(group.max_score),
            group.spec.priority_hint,
        )

    console.print(table)

def _endpoint_values_from_text(text: str) -> list[str]:
    """Extract endpoints from mined text plus plain endpoint-list lines."""
    mined = [endpoint.value for endpoint in mine_endpoints(text)]
    line_candidates = []

    for line in text.splitlines():
        value = line.strip()

        if not value or value.startswith("#"):
            continue

        if value.startswith("/") or value.startswith("http://") or value.startswith("https://"):
            line_candidates.append(value)

    return sorted(set(mined + line_candidates))

def _print_endpoint_priority_table(priorities, title: str = "Endpoint Priorities") -> None:
    """Print endpoint priority scores when an orchestration plan includes them."""
    if not priorities:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Band")
    table.add_column("Endpoint")
    table.add_column("Top Signals")

    for index, item in enumerate(priorities, start=1):
        top_signals = ", ".join(signal.name for signal in item.signals[:3])
        table.add_row(
            str(index),
            str(item.score),
            item.band,
            item.endpoint,
            top_signals or "none",
        )

    console.print(table)




@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Blackhole AI Workbench."""
    if ctx.invoked_subcommand is None:
        show_intro(
            config=IntroConfig(
                version="0.58.0",
                force=True,
            )
        )
        raise typer.Exit()


@app.command("intro")
def intro_command():
    """Show the Blackhole startup intro."""
    show_intro(
        config=IntroConfig(
            version="0.58.0",
            force=True,
        )
    )


@app.command()
def version():
    """Show Blackhole version."""
    console.print("[bold green]Blackhole AI Workbench[/bold green] version 0.58.0")


@app.command("scope-check")
def scope_check(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to check against scope."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method to check."),
):
    """Check whether a URL and HTTP method are allowed by the target scope."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    decision = scope.is_url_allowed(url, method)

    table = Table(title="Scope Guard Decision")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if decision.allowed else "NO")
    table.add_row("Reason", decision.reason)

    console.print(table)

    if not decision.allowed:
        raise typer.Exit(code=2)


@app.command("mine-endpoints")
def mine_endpoints_command(
    input_file: Path = typer.Argument(..., help="File to scan for endpoints."),
):
    """Extract API-like endpoints from JavaScript, HTML, HAR text, logs, or Burp exports."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoints = mine_endpoints(text)

    table = Table(title=f"Endpoint Mining Results: {input_file}")
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Category")
    table.add_column("Source")

    for index, endpoint in enumerate(endpoints, start=1):
        table.add_row(str(index), endpoint.value, endpoint.category, endpoint.source)

    console.print(table)
    console.print(f"[bold]Total endpoints:[/bold] {len(endpoints)}")


@app.command("compare-responses")
def compare_responses_command(
    baseline_file: Path = typer.Argument(..., help="Baseline response JSON file."),
    candidate_file: Path = typer.Argument(..., help="Candidate response JSON file."),
):
    """Compare two HTTP response records for security-relevant differences."""
    if not baseline_file.exists():
        console.print(f"[bold red]Baseline file not found:[/bold red] {baseline_file}")
        raise typer.Exit(code=1)

    if not candidate_file.exists():
        console.print(f"[bold red]Candidate file not found:[/bold red] {candidate_file}")
        raise typer.Exit(code=1)

    baseline_data = json.loads(baseline_file.read_text(encoding="utf-8"))
    candidate_data = json.loads(candidate_file.read_text(encoding="utf-8"))

    baseline = summarize_response(
        baseline_data.get("status_code"),
        baseline_data.get("headers", {}),
        baseline_data.get("body", ""),
    )

    candidate = summarize_response(
        candidate_data.get("status_code"),
        candidate_data.get("headers", {}),
        candidate_data.get("body", ""),
    )

    comparison = compare_responses(baseline, candidate)

    table = Table(title="Response Diff Analysis")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Baseline status", str(comparison.baseline_status))
    table.add_row("Candidate status", str(comparison.candidate_status))
    table.add_row("Same status", str(comparison.same_status))
    table.add_row("Size delta", str(comparison.size_delta))
    table.add_row("Size ratio", str(comparison.size_ratio))
    table.add_row("JSON key overlap", str(comparison.json_key_overlap))
    table.add_row("Signals", ", ".join(comparison.signals) if comparison.signals else "none")
    table.add_row("Verdict", comparison.verdict)

    console.print(table)


@app.command("build-tree")
def build_tree_command(
    input_file: Path = typer.Argument(..., help="File containing JS/HTML/HAR/log text to mine endpoints from."),
    target_name: str = typer.Option("demo-lab", "--target", "-t", help="Target/workspace name."),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Optional output file for rendered tree."),
):
    """Build a research task tree from discovered endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)

    root = build_endpoint_task_tree(target_name=target_name, endpoints=endpoint_values)
    rendered = render_tree(root)

    console.print(f"[bold green]Built task tree for:[/bold green] {target_name}")
    console.print(f"[bold]Endpoints discovered:[/bold] {len(endpoint_values)}")
    console.print()
    console.print(rendered)

    if output_file:
        output_file.write_text(rendered, encoding="utf-8")
        console.print()
        console.print(f"[bold green]Saved tree to:[/bold green] {output_file}")



@app.command("endpoint-investigation")
def endpoint_investigation_command(
    endpoint: str = typer.Argument(..., help="Endpoint path or URL to classify and expand into investigation tasks."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save endpoint investigation profile JSON.",
    ),
):
    """Build a planning-only endpoint investigation profile."""
    profile = build_endpoint_investigation_profile(endpoint)
    data = profile.to_dict()

    summary = Table(title="Endpoint Investigation Profile")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", profile.endpoint)
    summary.add_row("Normalized path", profile.normalized_path)
    summary.add_row("Categories", ", ".join(profile.categories))
    summary.add_row("Planned tasks", str(len(profile.tasks)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    console.print("[bold]Task types:[/bold] " + ", ".join(task.task_type for task in profile.tasks))

    task_table = Table(title="Planned Investigation Tasks")
    task_table.add_column("#", justify="right")
    task_table.add_column("Task")
    task_table.add_column("Type")
    task_table.add_column("Priority")
    task_table.add_column("Agent")
    task_table.add_column("Human Approval")

    for index, task in enumerate(profile.tasks, start=1):
        task_table.add_row(
            str(index),
            task.title,
            task.task_type,
            task.priority,
            task.agent_hint,
            "YES" if task.requires_human_approval else "NO",
        )

    console.print(task_table)
    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a reviewable plan. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved endpoint investigation JSON:[/bold green] {json_output}")

















@app.command("brain-chat")
def brain_chat_command(
    question: str = typer.Argument(..., help="Question to ask the local deterministic brain."),
    state_dir: Path = typer.Option(
        Path("."),
        "--state-dir",
        help="Directory containing generated Blackhole brain artifacts.",
    ),
    session: Path | None = typer.Option(
        None,
        "--session",
        help="Optional session JSON file to append this brain-chat turn.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain-chat reply.",
    ),
):
    """Ask the local planning-only brain state a deterministic question."""
    reply = build_brain_chat_reply(question, state_dir)
    data = reply.to_dict()

    console.print("[bold green]Blackhole:[/bold green]")
    console.print(reply.answer)

    if session:
        current_session = load_brain_chat_session(session)
        updated_session = append_brain_chat_turn(current_session, reply)
        save_brain_chat_session(updated_session, session)
        console.print(
            f"[bold green]Saved brain chat session:[/bold green] {session} "
            f"({len(updated_session.turns)} turn(s))"
        )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] brain-chat is local and planning-only. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("tool-execution-gate")
def tool_execution_gate_command(
    tool_request_manifest_json: Path = typer.Argument(..., help="Path to tool-request-manifest JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the tool execution gate.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured tool execution gate.",
    ),
):
    """Build a planning-only tool execution gate from tool-request-manifest JSON."""
    if not tool_request_manifest_json.exists():
        console.print(f"[bold red]Tool request manifest JSON not found:[/bold red] {tool_request_manifest_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(tool_request_manifest_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid tool request manifest JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Tool request manifest JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    gate = build_tool_execution_gate(data)
    markdown = render_tool_execution_gate_markdown(gate)
    gate_data = gate.to_dict()

    summary = Table(title="Tool Execution Gate")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", gate.target_name)
    summary.add_row("Focus endpoint", gate.focus_endpoint or "none")
    summary.add_row("Gate decision", gate.gate_decision)
    summary.add_row("Execution allowed", str(gate.execution_allowed))
    summary.add_row("Gate items", str(len(gate.gate_items)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no tool, curl, browser, network, Kali, shell, or LLM execution")
    console.print(summary)

    items_table = Table(title="Execution Gate Items")
    items_table.add_column("#", justify="right")
    items_table.add_column("Family")
    items_table.add_column("Request")
    items_table.add_column("Gate Status")

    for index, item in enumerate(gate.gate_items, start=1):
        items_table.add_row(
            str(index),
            item.tool_family,
            item.request_name,
            item.gate_status,
        )

    console.print(items_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved tool execution gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved tool execution gate JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only execution gate. "
        "It does not execute tools, send requests, run shell commands, launch browsers, call LLM providers, or use Kali tools."
    )


@app.command("tool-request-manifest")
def tool_request_manifest_command(
    brain_approval_json: Path = typer.Argument(..., help="Path to brain-approval JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the tool request manifest.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured tool request manifest.",
    ),
):
    """Build a planning-only tool request manifest from brain-approval JSON."""
    if not brain_approval_json.exists():
        console.print(f"[bold red]Brain approval JSON not found:[/bold red] {brain_approval_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_approval_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain approval JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain approval JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    manifest = build_tool_request_manifest(data)
    markdown = render_tool_request_manifest_markdown(manifest)
    manifest_data = manifest.to_dict()

    summary = Table(title="Tool Request Manifest")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", manifest.target_name)
    summary.add_row("Focus endpoint", manifest.focus_endpoint or "none")
    summary.add_row("Source approval status", manifest.source_approval_status)
    summary.add_row("Tool requests", str(len(manifest.requests)))
    summary.add_row("Execution allowed", str(manifest.execution_allowed))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no tool, curl, browser, network, Kali, shell, or LLM execution")
    console.print(summary)

    requests_table = Table(title="Tool Requests")
    requests_table.add_column("#", justify="right")
    requests_table.add_column("Family")
    requests_table.add_column("Request")
    requests_table.add_column("Approval")
    requests_table.add_column("Execution")

    for index, request in enumerate(manifest.requests, start=1):
        requests_table.add_row(
            str(index),
            request.tool_family,
            request.name,
            "YES" if request.requires_human_approval else "NO",
            "YES" if request.execution_allowed else "NO",
        )

    console.print(requests_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved tool request manifest Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved tool request manifest JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only tool request manifest. "
        "It does not execute tools, send requests, run shell commands, launch browsers, call LLM providers, or use Kali tools."
    )


@app.command("brain-approval")
def brain_approval_command(
    brain_decision_json: Path = typer.Argument(..., help="Path to brain-decision JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the human approval packet.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured human approval packet.",
    ),
):
    """Build a planning-only human approval packet from brain-decision JSON."""
    if not brain_decision_json.exists():
        console.print(f"[bold red]Brain decision JSON not found:[/bold red] {brain_decision_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_decision_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain decision JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain decision JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    packet = build_brain_approval_packet(data)
    markdown = render_brain_approval_packet_markdown(packet)
    packet_data = packet.to_dict()

    summary = Table(title="Human Approval Packet")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", packet.target_name)
    summary.add_row("Focus endpoint", packet.focus_endpoint or "none")
    summary.add_row("Source decision", packet.source_decision)
    summary.add_row("Approval status", packet.approval_status)
    summary.add_row("Approval required", str(packet.approval_required))
    summary.add_row("Reportable", str(packet.reportable))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    items_table = Table(title="Approval Items")
    items_table.add_column("#", justify="right")
    items_table.add_column("Category")
    items_table.add_column("Item")
    items_table.add_column("Required")
    items_table.add_column("Source")

    for index, item in enumerate(packet.approval_items, start=1):
        items_table.add_row(
            str(index),
            item.category,
            item.name,
            str(item.required),
            item.source_blocker or "manual",
        )

    console.print(items_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain approval Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(packet_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain approval JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only human approval packet. "
        "It does not confirm vulnerabilities, call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-decision")
def brain_decision_command(
    brain_review_json: Path = typer.Argument(..., help="Path to brain-review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the brain decision gate.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain decision gate.",
    ),
):
    """Build a planning-only decision gate from brain-review JSON."""
    if not brain_review_json.exists():
        console.print(f"[bold red]Brain review JSON not found:[/bold red] {brain_review_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_review_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    gate = build_brain_decision_gate(data)
    markdown = render_brain_decision_gate_markdown(gate)
    gate_data = gate.to_dict()

    summary = Table(title="Brain Decision Gate")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", gate.target_name)
    summary.add_row("Focus endpoint", gate.focus_endpoint or "none")
    summary.add_row("Decision", gate.decision)
    summary.add_row("Reportable", str(gate.reportable))
    summary.add_row("Blockers", str(len(gate.blockers)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    blockers_table = Table(title="Decision Blockers")
    blockers_table.add_column("#", justify="right")
    blockers_table.add_column("Blocker")
    blockers_table.add_column("Severity")
    blockers_table.add_column("Reason")

    for index, blocker in enumerate(gate.blockers, start=1):
        blockers_table.add_row(str(index), blocker.name, blocker.severity, blocker.reason)

    console.print(blockers_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain decision Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain decision JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only decision gate. "
        "It does not confirm vulnerabilities, call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-review")
def brain_review_command(
    brain_prompt_json: Path = typer.Argument(..., help="Path to brain-prompt JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the brain review.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain review.",
    ),
):
    """Build a planning-only reasoning review from brain-prompt JSON."""
    if not brain_prompt_json.exists():
        console.print(f"[bold red]Brain prompt JSON not found:[/bold red] {brain_prompt_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_prompt_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain prompt JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain prompt JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    review = build_brain_review(data)
    markdown = render_brain_review_markdown(review)
    review_data = review.to_dict()

    summary = Table(title="Brain Review")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", review.target_name)
    summary.add_row("Focus endpoint", review.focus_endpoint or "none")
    summary.add_row("Sections", str(len(review.sections)))
    summary.add_row("Safety gates", str(len(review.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    section_table = Table(title="Brain Review Sections")
    section_table.add_column("#", justify="right")
    section_table.add_column("Section")

    for index, section in enumerate(review.sections, start=1):
        section_table.add_row(str(index), section.title)

    console.print(section_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain review JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only reasoning review. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-prompt")
def brain_prompt_command(
    ai_brain_json: Path = typer.Argument(..., help="Path to AI brain plan JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the prompt package.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured prompt package.",
    ),
):
    """Build a planning-only LLM brain prompt package from AI brain JSON."""
    if not ai_brain_json.exists():
        console.print(f"[bold red]AI brain JSON not found:[/bold red] {ai_brain_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(ai_brain_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid AI brain JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]AI brain JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = build_brain_prompt_package(data)
    markdown = render_brain_prompt_package_markdown(package)
    package_data = package.to_dict()

    summary = Table(title="LLM Brain Prompt Package")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", package.target_name)
    summary.add_row("Focus endpoint", package.focus_endpoint or "none")
    summary.add_row("Messages", str(package.message_count))
    summary.add_row("Safety gates", str(len(package.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    messages_table = Table(title="Prompt Messages")
    messages_table.add_column("#", justify="right")
    messages_table.add_column("Role")
    messages_table.add_column("Characters", justify="right")

    for index, message in enumerate(package.messages, start=1):
        messages_table.add_row(str(index), message.role, str(len(message.content)))

    console.print(messages_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain prompt Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(package_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain prompt JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a provider-ready prompt package. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("ai-brain")
def ai_brain_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the AI brain plan.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured AI brain plan.",
    ),
):
    """Build a planning-only AI brain plan from research-state JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_ai_brain_plan(data)
    markdown = render_ai_brain_plan_markdown(plan)
    plan_data = plan.to_dict()

    summary = Table(title="AI Brain Plan")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", plan.target_name)
    summary.add_row("Focus items", str(len(plan.focus_queue)))
    summary.add_row("Global actions", str(len(plan.global_actions)))
    summary.add_row("Safety gates", str(len(plan.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no curl, browser, network, Kali, or LLM provider execution")
    console.print(summary)

    focus_table = Table(title="AI Brain Focus Queue")
    focus_table.add_column("#", justify="right")
    focus_table.add_column("Endpoint")
    focus_table.add_column("Priority")
    focus_table.add_column("Triage")
    focus_table.add_column("Actions", justify="right")
    focus_table.add_column("Reason")

    for index, item in enumerate(plan.focus_queue, start=1):
        focus_table.add_row(
            str(index),
            item.endpoint,
            f"{item.priority_band}/{item.priority_score}",
            item.triage_state,
            str(len(item.next_actions)),
            item.reason,
        )

    console.print(focus_table)

    gates_table = Table(title="AI Brain Safety Gates")
    gates_table.add_column("#", justify="right")
    gates_table.add_column("Gate")

    for index, gate in enumerate(plan.safety_gates, start=1):
        gates_table.add_row(str(index), gate)

    console.print(gates_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved AI brain plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved AI brain plan JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only AI brain plan. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )






@app.command("case-summary")
def case_summary_command(
    case_timeline_json: Path = typer.Argument(..., help="Path to case-timeline JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the case summary.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured case summary.",
    ),
):
    """Build a planning-only case summary from case-timeline JSON."""
    if not case_timeline_json.exists():
        console.print(f"[bold red]Case timeline JSON not found:[/bold red] {case_timeline_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_timeline_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case timeline JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case timeline JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    summary_obj = build_case_summary(data)
    markdown = render_case_summary_markdown(summary_obj)
    summary_data = summary_obj.to_dict()

    summary_table = Table(title="Case Summary")
    summary_table.add_column("Field", style="bold")
    summary_table.add_column("Value")
    summary_table.add_row("Target", summary_obj.target_name)
    summary_table.add_row("Events", str(summary_obj.event_count))
    summary_table.add_row("Current state", summary_obj.current_state)
    summary_table.add_row("Execution", "planning-only; local artifacts only")
    console.print(summary_table)

    points_table = Table(title="Key Points")
    points_table.add_column("#", justify="right")
    points_table.add_column("Point")

    for index, point in enumerate(summary_obj.key_points, start=1):
        points_table.add_row(str(index), point)

    console.print(points_table)

    steps_table = Table(title="Recommended Next Steps")
    steps_table.add_column("#", justify="right")
    steps_table.add_column("Step")

    for index, step in enumerate(summary_obj.recommended_next_steps, start=1):
        steps_table.add_row(str(index), step)

    console.print(steps_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case summary JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reads local case timeline artifacts. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("case-timeline")
def case_timeline_command(
    case_dir: Path = typer.Argument(..., help="Directory containing Blackhole case artifacts."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the case timeline.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured case timeline.",
    ),
):
    """Build a planning-only case timeline from local Blackhole artifacts."""
    if not case_dir.exists():
        console.print(f"[bold red]Case directory not found:[/bold red] {case_dir}")
        raise typer.Exit(code=1)

    timeline = build_case_timeline(case_dir)
    markdown = render_case_timeline_markdown(timeline)
    data = timeline.to_dict()

    summary = Table(title="Case Timeline")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", timeline.target_name)
    summary.add_row("Events", str(timeline.event_count))
    summary.add_row("Execution", "planning-only; local artifacts only")
    console.print(summary)

    events_table = Table(title="Timeline Events")
    events_table.add_column("#", justify="right")
    events_table.add_column("Type")
    events_table.add_column("Title")
    events_table.add_column("Summary")

    for event in timeline.events:
        events_table.add_row(
            str(event.order),
            event.event_type,
            event.title,
            event.summary,
        )

    console.print(events_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case timeline Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case timeline JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reads local case artifacts. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("research-state-apply")
def research_state_apply_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    update_plan: Path = typer.Option(..., "--update-plan", help="Path to research-state-update JSON."),
    output_file: Path = typer.Option(..., "--output-file", "--output", help="Output path for updated research-state JSON."),
    result_json: Path | None = typer.Option(None, "--result-json", help="Optional path to write full apply result JSON."),
):
    """Apply a research-state update plan to a local copy of research-state JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    if not update_plan.exists():
        console.print(f"[bold red]Update plan JSON not found:[/bold red] {update_plan}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
        plan_data = json.loads(update_plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict) or not isinstance(plan_data, dict):
        console.print("[bold red]Research-state and update-plan JSON must both be objects.[/bold red]")
        raise typer.Exit(code=2)

    result = apply_research_state_update_plan(state_data, plan_data)
    result_data = result.to_dict()

    summary = Table(title="Research State Apply Result")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", result.target_name)
    summary.add_row("Endpoint", result.endpoint)
    summary.add_row("Validation result", result.validation_result)
    summary.add_row("Patches", str(len(result.applied_patches)))
    summary.add_row("Execution", "local-only; no network, browser, shell, Kali, tool, or LLM execution")
    console.print(summary)

    patches_table = Table(title="Applied Patches")
    patches_table.add_column("#", justify="right")
    patches_table.add_column("Path")
    patches_table.add_column("Applied")
    patches_table.add_column("New Value")

    for index, patch in enumerate(result.applied_patches, start=1):
        patches_table.add_row(
            str(index),
            escape(patch.path),
            str(patch.applied),
            escape(str(patch.new_value)),
        )

    console.print(patches_table)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result.updated_research_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    console.print(f"[bold green]Saved updated research-state JSON:[/bold green] {output_file}")

    if result_json:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(result_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved apply result JSON:[/bold green] {result_json}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only writes a local updated copy. "
        "It does not mutate the original file or execute tools."
    )





@app.command("result-flow")
def result_flow_command(
    research_state_json: Path = typer.Option(..., "--research-state", help="Path to research-state JSON."),
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint that was manually validated."),
    observed_status: int | None = typer.Option(None, "--observed-status", help="Observed HTTP status code."),
    expected_status: int | None = typer.Option(None, "--expected-status", help="Expected HTTP status code."),
    observed_body: str = typer.Option("", "--observed-body", help="Short observed response/body note."),
    expected_body: str = typer.Option("", "--expected-body", help="Short expected response/body note."),
    note: str = typer.Option("", "--note", help="Human validation note."),
    updated_state: Path = typer.Option(..., "--updated-state", help="Path to write updated research-state JSON."),
    result_json: Path | None = typer.Option(None, "--result-json", help="Optional path to write full result-flow JSON."),
):
    """Run local interpretation -> state update planning -> local state apply."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    flow = build_result_flow(
        research_state_data=state_data,
        endpoint=endpoint,
        observed_status=observed_status,
        expected_status=expected_status,
        observed_body=observed_body,
        expected_body=expected_body,
        note=note,
    )
    flow_data = flow.to_dict()

    summary = Table(title="Result Flow")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", endpoint)
    summary.add_row("Suggested result", flow.interpretation.suggested_result)
    summary.add_row("Confidence", flow.interpretation.confidence)
    summary.add_row("Update validation result", flow.update_plan.validation_result)
    summary.add_row("Applied patches", str(len(flow.apply_result.applied_patches)))
    summary.add_row("Execution", "local-only; no target interaction")
    console.print(summary)

    updated_state.parent.mkdir(parents=True, exist_ok=True)
    updated_state.write_text(
        json.dumps(flow.apply_result.updated_research_state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    console.print(f"[bold green]Saved updated research-state JSON:[/bold green] {updated_state}")

    if result_json:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(flow_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result-flow JSON:[/bold green] {result_json}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only interprets a human-provided result summary and writes a local updated state copy. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-to-state-update")
def result_to_state_update_command(
    research_state_json: Path = typer.Option(..., "--research-state", help="Path to research-state JSON."),
    interpretation_json: Path = typer.Option(..., "--interpretation", help="Path to interpret-result JSON."),
    note: str = typer.Option("", "--note", help="Optional human override note."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a research-state update plan from result interpretation JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    if not interpretation_json.exists():
        console.print(f"[bold red]Interpretation JSON not found:[/bold red] {interpretation_json}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
        interpretation_data = json.loads(interpretation_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict) or not isinstance(interpretation_data, dict):
        console.print("[bold red]Research-state and interpretation JSON must both be objects.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_update_plan_from_interpretation(
        research_state_data=state_data,
        interpretation_data=interpretation_data,
        note=note,
    )
    markdown = render_research_state_update_plan_markdown(plan)
    plan_data = plan.to_dict()

    table = Table(title="Result to State Update")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", plan.target_name)
    table.add_row("Endpoint", plan.endpoint)
    table.add_row("Validation result", plan.validation_result)
    table.add_row("Actions", str(len(plan.actions)))
    table.add_row("Execution", "planning-only; no state mutation or tool execution")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved state update Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved state update JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only converts interpretation into a reviewable state-update plan. "
        "It does not mutate research-state files automatically."
    )



@app.command("import-result-evidence")
def import_result_evidence_command(
    evidence_file: Path = typer.Argument(..., help="Path to local result evidence JSON."),
    source: str = typer.Option("manual-json", "--source", help="Evidence source label."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for normalized result evidence.",
    ),
):
    """Normalize local result evidence JSON for interpret-result/result-flow."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence JSON not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(evidence_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid evidence JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Evidence JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        evidence = import_result_evidence(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence:[/bold red] {exc}")
        raise typer.Exit(code=2)

    evidence_data = evidence.to_dict()

    table = Table(title="Normalized Result Evidence")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Endpoint", escape(evidence.endpoint))
    table.add_row("Observed status", str(evidence.observed_status))
    table.add_row("Expected status", str(evidence.expected_status))
    table.add_row("Source", evidence.source)
    table.add_row("Execution", "planning-only; local evidence normalization only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(evidence_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved normalized result evidence JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(evidence_data, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only normalizes local evidence JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("import-result-evidence-batch")
def import_result_evidence_batch_command(
    evidence_dir: Path = typer.Argument(..., help="Directory containing local result evidence JSON files."),
    source: str = typer.Option("manual-json-batch", "--source", help="Evidence batch source label."),
    pattern: str = typer.Option("*.json", "--pattern", help="Glob pattern for evidence JSON files."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for normalized result evidence batch.",
    ),
):
    """Normalize a directory of local result evidence JSON files."""
    try:
        batch = import_result_evidence_batch(evidence_dir, source=source, pattern=pattern)
    except FileNotFoundError as exc:
        console.print(f"[bold red]Evidence directory not found:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except NotADirectoryError as exc:
        console.print(f"[bold red]Evidence path is not a directory:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch:[/bold red] {exc}")
        raise typer.Exit(code=2)

    batch_data = batch.to_dict()

    table = Table(title="Normalized Result Evidence Batch")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Directory", str(evidence_dir))
    table.add_row("Pattern", pattern)
    table.add_row("Count", str(batch_data["count"]))
    table.add_row("Source", batch.source)
    table.add_row("Execution", "planning-only; local evidence normalization only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(batch_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved normalized result evidence batch JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(batch_data, indent=2, sort_keys=True))


@app.command("review-result-evidence-batch")
def review_result_evidence_batch_command(
    batch_file: Path = typer.Argument(..., help="Path to normalized result evidence batch JSON."),
    source: str = typer.Option("result-evidence-batch-review", "--source", help="Batch review source label."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for result evidence batch review.",
    ),
):
    """Review a normalized result evidence batch using planning-only interpretation."""
    if not batch_file.exists():
        console.print(f"[bold red]Result evidence batch JSON not found:[/bold red] {batch_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(batch_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        review = review_result_evidence_batch(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    review_data = review.to_dict()

    table = Table(title="Result Evidence Batch Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Batch file", str(batch_file))
    table.add_row("Count", str(review_data["count"]))
    table.add_row("Supported", str(review_data["supported_count"]))
    table.add_row("Rejected", str(review_data["rejected_count"]))
    table.add_row("Needs more evidence", str(review_data["needs_more_evidence_count"]))
    table.add_row("Missing expected status", str(review_data["missing_expected_status_count"]))
    table.add_row("Execution", "planning-only; local batch review only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence batch review JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(review_data, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews local batch evidence. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-review-report")
def result_evidence_review_report_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path containing the rendered Markdown.",
    ),
    title: str = typer.Option("Result Evidence Batch Review Report", "--title", help="Markdown report title."),
    source: str = typer.Option("result-evidence-review-report", "--source", help="Report source label."),
):
    """Render a local result evidence batch review JSON into a planning-only Markdown report."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        report = render_result_evidence_review_report(data, title=title, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch review report input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    report_data = report.to_dict()

    table = Table(title="Result Evidence Review Report")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Markdown lines", str(len(report.markdown.splitlines())))
    table.add_row("Execution", "planning-only; local Markdown rendering only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence review report JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(report.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders local review JSON into Markdown. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-finding-draft")
def result_evidence_finding_draft_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path containing the rendered Markdown.",
    ),
    title: str = typer.Option("Candidate Finding Draft", "--title", help="Markdown draft title."),
    include_all: bool = typer.Option(False, "--include-all", help="Include rejected and needs-more-evidence items."),
    source: str = typer.Option("result-evidence-finding-draft", "--source", help="Draft source label."),
):
    """Render a planning-only candidate finding draft from batch review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        draft = render_result_evidence_finding_draft(
            data,
            title=title,
            include_all=include_all,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence finding draft input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    draft_data = draft.to_dict()

    table = Table(title="Result Evidence Finding Draft")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Selected evidence items", str(draft.selected_count))
    table.add_row("Markdown lines", str(len(draft.markdown.splitlines())))
    table.add_row("Execution", "planning-only; local draft rendering only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(draft.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence finding draft Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence finding draft JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(draft.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders local review JSON into a candidate draft. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-finding-package")
def result_evidence_finding_package_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_dir: Path = typer.Option(..., "--output-dir", "--output", help="Directory to write the finding package."),
    finding_title: str = typer.Option("Candidate Finding Draft", "--title", help="Finding draft title."),
    include_all: bool = typer.Option(False, "--include-all", help="Include rejected and needs-more-evidence items."),
    source: str = typer.Option("result-evidence-finding-package", "--source", help="Package source label."),
):
    """Build a local finding package from result evidence batch review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        package = build_result_evidence_finding_package(
            data,
            finding_title=finding_title,
            include_all=include_all,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence finding package input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output_dir.mkdir(parents=True, exist_ok=True)

    for relative_name, content in package.files.items():
        output_path = output_dir / relative_name
        output_path.write_text(content, encoding="utf-8")

    package_data = package.to_dict()

    table = Table(title="Result Evidence Finding Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Output directory", str(output_dir))
    table.add_row("Files", str(package_data["file_count"]))
    table.add_row("Selected evidence items", str(package.metadata["selected_item_count"]))
    table.add_row("Execution", "planning-only; local package generation only")
    console.print(table)

    console.print(f"[bold green]Saved result evidence finding package:[/bold green] {output_dir}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only writes local package artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-hypothesis")
def result_evidence_hypothesis_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    supported_only: bool = typer.Option(False, "--supported-only", help="Generate hypotheses only for supported review items."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-hypothesis", "--source", help="Hypothesis source label."),
):
    """Generate planning-only security hypotheses from local result evidence review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        hypotheses = generate_result_evidence_hypotheses(
            data,
            supported_only=supported_only,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence hypothesis input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    hypothesis_data = hypotheses.to_dict()
    markdown = hypotheses.to_markdown()

    table = Table(title="Result Evidence Hypotheses")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Hypotheses", str(hypothesis_data["count"]))
    table.add_row("Supported only", str(supported_only))
    table.add_row("Execution", "planning-only; local hypothesis generation only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence hypotheses Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(hypothesis_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence hypotheses JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only generates planning-only local hypotheses. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-validation-plan")
def result_evidence_validation_plan_command(
    hypothesis_file: Path = typer.Argument(..., help="Path to result evidence hypothesis JSON."),
    high_priority_only: bool = typer.Option(False, "--high-priority-only", help="Include only high and medium-high priority plans."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-validation-plan", "--source", help="Validation plan source label."),
):
    """Build a planning-only manual validation plan from result evidence hypotheses."""
    if not hypothesis_file.exists():
        console.print(f"[bold red]Result evidence hypothesis JSON not found:[/bold red] {hypothesis_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(hypothesis_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence hypothesis JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence hypothesis JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_result_evidence_validation_plan(
            data,
            high_priority_only=high_priority_only,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence validation plan input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    plan_data = plan.to_dict()
    markdown = plan.to_markdown()

    table = Table(title="Result Evidence Validation Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Hypothesis file", str(hypothesis_file))
    table.add_row("Plans", str(plan_data["count"]))
    table.add_row("High priority only", str(high_priority_only))
    table.add_row("Execution", "planning-only; local validation planning only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence validation plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence validation plan JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only generates a local manual validation plan. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-case-summary")
def result_evidence_case_summary_command(
    validation_plan_file: Path = typer.Argument(..., help="Path to result evidence validation plan JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-case-summary", "--source", help="Case summary source label."),
):
    """Build a case-level intelligence summary from a local validation plan JSON."""
    if not validation_plan_file.exists():
        console.print(f"[bold red]Result evidence validation plan JSON not found:[/bold red] {validation_plan_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(validation_plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence validation plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence validation plan JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        summary = build_result_evidence_case_summary(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence case summary input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    summary_data = summary.to_dict()
    markdown = summary.to_markdown()

    table = Table(title="Result Evidence Case Summary")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Validation plan file", str(validation_plan_file))
    table.add_row("Findings", str(summary_data["count"]))
    table.add_row("Strongest candidates", str(len(summary_data["strongest_candidates"])))
    table.add_row("Weak/rejected candidates", str(len(summary_data["weak_or_rejected_candidates"])))
    table.add_row("Execution", "planning-only; local case summary only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence case summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence case summary JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only summarizes local validation plan JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat")
def case_chat_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer from the case summary."),
    session_file: Path | None = typer.Option(
        None,
        "--session-file",
        help="Optional local JSON session file to append this case-chat turn.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Answer a local research question from a case summary JSON artifact."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        answer = answer_case_question(data, question)
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    answer_data = answer.to_dict()

    table = Table(title="Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", answer.intent)
    table.add_row("Cited endpoints", str(len(answer.cited_endpoints)))
    table.add_row("Next actions", str(len(answer.next_actions)))
    table.add_row("Execution", "planning-only; local artifact chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(answer.answer)

    if answer.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in answer.next_actions:
            console.print(f"- {item}")

    if session_file:
        try:
            session = append_case_chat_turn_to_file(session_file, answer)
        except ValueError as exc:
            console.print(f"[bold red]Invalid case chat session file:[/bold red] {exc}")
            raise typer.Exit(code=2)

        answer_data["session"] = session.to_dict()
        console.print(f"[bold green]Saved case chat session:[/bold green] {session_file}")
        console.print(f"[bold green]Session summary:[/bold green] {session.summary_text()}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(answer_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local case-summary JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-priority-ranking")
def result_evidence_priority_ranking_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    include_weak: bool = typer.Option(True, "--include-weak/--exclude-weak", help="Include weak or likely false-positive candidates."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-priority-ranking", "--source", help="Priority ranking source label."),
):
    """Rank local case-summary candidates by priority, readiness, and evidence strength."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        ranking = build_result_evidence_priority_ranking(
            data,
            include_weak=include_weak,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence priority ranking input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    ranking_data = ranking.to_dict()
    markdown = ranking.to_markdown()

    table = Table(title="Result Evidence Priority Ranking")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Candidates", str(ranking_data["count"]))
    table.add_row("Include weak", str(include_weak))
    table.add_row("Execution", "planning-only; local ranking only")
    console.print(table)

    if ranking_data["top_candidate"]:
        top = ranking_data["top_candidate"]
        console.print(f"[bold green]Top candidate:[/bold green] {top['endpoint']} score={top['score']}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence priority ranking Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(ranking_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence priority ranking JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only ranks local case-summary candidates. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-multi-agent-review")
def result_evidence_multi_agent_review_command(
    ranking_file: Path = typer.Argument(..., help="Path to result evidence priority ranking JSON."),
    include_low_priority: bool = typer.Option(
        True,
        "--include-low-priority/--exclude-low-priority",
        help="Include low priority or likely false-positive candidates.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-multi-agent-review", "--source", help="Multi-agent review source label."),
):
    """Build specialist review plans from a local result evidence priority ranking."""
    if not ranking_file.exists():
        console.print(f"[bold red]Priority ranking JSON not found:[/bold red] {ranking_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(ranking_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid priority ranking JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Priority ranking JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_result_evidence_multi_agent_review_plan(
            data,
            include_low_priority=include_low_priority,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence multi-agent review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    plan_data = plan.to_dict()
    markdown = plan.to_markdown()

    table = Table(title="Result Evidence Multi-Agent Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Ranking file", str(ranking_file))
    table.add_row("Candidate plans", str(plan_data["count"]))
    table.add_row("Agent tasks", str(plan_data["total_agent_tasks"]))
    table.add_row("Include low priority", str(include_low_priority))
    table.add_row("Execution", "planning-only; local specialist review planning only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence multi-agent review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence multi-agent review JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local specialist review plans. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-report-assistant")
def case_report_assistant_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    ranking_file: Path | None = typer.Option(
        None,
        "--ranking",
        help="Optional result evidence priority ranking JSON.",
    ),
    multi_agent_review_file: Path | None = typer.Option(
        None,
        "--multi-agent-review",
        help="Optional result evidence multi-agent review JSON.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-report-assistant", "--source", help="Report assistant source label."),
):
    """Build a planning-only report skeleton from local case intelligence artifacts."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    ranking = None
    if ranking_file:
        if not ranking_file.exists():
            console.print(f"[bold red]Priority ranking JSON not found:[/bold red] {ranking_file}")
            raise typer.Exit(code=1)

        try:
            ranking = json.loads(ranking_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid priority ranking JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(ranking, dict):
            console.print("[bold red]Priority ranking JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    multi_agent_review = None
    if multi_agent_review_file:
        if not multi_agent_review_file.exists():
            console.print(f"[bold red]Multi-agent review JSON not found:[/bold red] {multi_agent_review_file}")
            raise typer.Exit(code=1)

        try:
            multi_agent_review = json.loads(multi_agent_review_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid multi-agent review JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(multi_agent_review, dict):
            console.print("[bold red]Multi-agent review JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        draft = build_case_report_assistant_draft(
            case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case report assistant input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    draft_data = draft.to_dict()

    table = Table(title="Case-to-Report Assistant")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Affected endpoints", str(len(draft.affected_endpoints)))
    table.add_row("Title candidates", str(len(draft.title_candidates)))
    table.add_row("Readiness", draft.readiness)
    table.add_row("Execution", "planning-only; local report skeleton only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(draft.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case report assistant Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case report assistant JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(draft.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders a local report skeleton. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-context")
def case_chat_context_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer from multiple artifacts."),
    ranking_file: Path | None = typer.Option(
        None,
        "--ranking",
        help="Optional result evidence priority ranking JSON.",
    ),
    multi_agent_review_file: Path | None = typer.Option(
        None,
        "--multi-agent-review",
        help="Optional result evidence multi-agent review JSON.",
    ),
    report_assistant_file: Path | None = typer.Option(
        None,
        "--report-assistant",
        help="Optional case-report-assistant JSON.",
    ),
    session_file: Path | None = typer.Option(
        None,
        "--session-file",
        help="Optional local case-chat session JSON.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-case-chat-context", "--source", help="Context chat source label."),
):
    """Answer a stronger local research question from multiple case artifacts."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")
    session = load_optional_json(session_file, "Case chat session")

    try:
        answer = answer_case_context_question(
            case_summary,
            question,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
            session=session,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat context input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    answer_data = answer.to_dict()

    table = Table(title="Strong Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", answer.intent)
    table.add_row("Included artifacts", ", ".join(answer.included_artifacts))
    table.add_row("Cited endpoints", str(len(answer.cited_endpoints)))
    table.add_row("Next actions", str(len(answer.next_actions)))
    table.add_row("Execution", "planning-only; local multi-artifact chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(answer.answer)

    if answer.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in answer.next_actions:
            console.print(f"- {item}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(answer_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat context JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local case artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("chat-context-router")
def chat_context_router_command(
    artifact_file: Path = typer.Argument(..., help="Path to a local result evidence artifact JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-chat-context-router", "--source", help="Router source label."),
):
    """Route a local artifact to supported chat/review commands and questions."""
    if not artifact_file.exists():
        console.print(f"[bold red]Artifact JSON not found:[/bold red] {artifact_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(artifact_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid artifact JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Artifact JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        route = route_chat_context(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid chat context router input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    route_data = route.to_dict()
    markdown = route.to_markdown()

    table = Table(title="Chat Context Router")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Artifact", str(artifact_file))
    table.add_row("Artifact kind", route.artifact_kind)
    table.add_row("Recommended command", route.recommended_command)
    table.add_row("Supported questions", str(len(route.supported_questions)))
    table.add_row("Execution", "planning-only; local artifact routing only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved chat context route Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(route_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved chat context route JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only routes local artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-grounded")
def case_chat_grounded_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer with grounding snippets."),
    ranking_file: Path | None = typer.Option(None, "--ranking", help="Optional result evidence priority ranking JSON."),
    multi_agent_review_file: Path | None = typer.Option(None, "--multi-agent-review", help="Optional multi-agent review JSON."),
    report_assistant_file: Path | None = typer.Option(None, "--report-assistant", help="Optional report assistant JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Answer from local case artifacts and include deterministic grounding snippets."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")

    try:
        answer = answer_case_context_question(
            case_summary,
            question,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
        )
        grounded = build_grounded_answer(
            answer=answer.answer,
            intent=answer.intent,
            cited_endpoints=answer.cited_endpoints,
            next_actions=answer.next_actions,
            case_summary=case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid grounded case chat input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    grounded_data = grounded.to_dict()

    table = Table(title="Grounded Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", grounded.intent)
    table.add_row("Cited endpoints", str(len(grounded.cited_endpoints)))
    table.add_row("Grounding snippets", str(len(grounded.grounding)))
    table.add_row("Execution", "planning-only; local grounded chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(grounded.answer)

    if grounded.grounding:
        console.print()
        console.print("[bold]Grounding[/bold]")
        for snippet in grounded.grounding[:12]:
            console.print(f"- {snippet.artifact}:{snippet.path} = {snippet.value}")

    if grounded.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in grounded.next_actions:
            console.print(f"- {item}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(grounded_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved grounded case chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local artifacts and local snippets. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-memory-build")
def case_memory_build_command(
    case_summary_file: Path | None = typer.Option(None, "--case-summary", help="Optional result evidence case summary JSON."),
    ranking_file: Path | None = typer.Option(None, "--ranking", help="Optional result evidence priority ranking JSON."),
    multi_agent_review_file: Path | None = typer.Option(None, "--multi-agent-review", help="Optional multi-agent review JSON."),
    report_assistant_file: Path | None = typer.Option(None, "--report-assistant", help="Optional report assistant JSON."),
    grounded_answer_file: Path | None = typer.Option(None, "--grounded-answer", help="Optional grounded answer JSON."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional case-chat session JSON."),
    output_file: Path = typer.Option(..., "--output-file", "--output", help="Path to write case memory JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional Markdown output path."),
):
    """Build a local multi-artifact case memory JSON file."""
    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    case_summary = load_optional_json(case_summary_file, "Case summary")
    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")
    grounded_answer = load_optional_json(grounded_answer_file, "Grounded answer")
    session = load_optional_json(session_file, "Case chat session")

    try:
        memory = build_result_evidence_case_memory(
            case_summary=case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
            grounded_answer=grounded_answer,
            session=session,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case memory input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    memory_data = memory.to_dict()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(memory_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    table = Table(title="Multi-Artifact Case Memory")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Output file", str(output_file))
    table.add_row("Top endpoint", memory.top_endpoint)
    table.add_row("Cited endpoints", str(len(memory.cited_endpoints)))
    table.add_row("Open next actions", str(len(memory.open_next_actions)))
    table.add_row("Missing evidence", str(len(memory.missing_evidence)))
    table.add_row("Execution", "planning-only; local case memory build only")
    console.print(table)
    console.print(f"[bold green]Saved case memory JSON:[/bold green] {output_file}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(memory.to_markdown() + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case memory Markdown:[/bold green] {markdown_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local case memory from local artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-prompt-package")
def case_chat_prompt_package_command(
    case_memory_file: Path = typer.Option(..., "--case-memory", help="Path to result evidence case memory JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Question to package for optional LLM review."),
    grounded_answer_file: Path | None = typer.Option(None, "--grounded-answer", help="Optional grounded answer JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a safe reviewable LLM prompt package from local case-chat artifacts without calling a provider."""
    if not case_memory_file.exists():
        console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
        raise typer.Exit(code=1)

    try:
        case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_memory, dict):
        console.print("[bold red]Case memory JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    grounded_answer = None
    if grounded_answer_file:
        if not grounded_answer_file.exists():
            console.print(f"[bold red]Grounded answer JSON not found:[/bold red] {grounded_answer_file}")
            raise typer.Exit(code=1)

        try:
            grounded_answer = json.loads(grounded_answer_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid grounded answer JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(grounded_answer, dict):
            console.print("[bold red]Grounded answer JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        package = build_case_chat_prompt_package(
            case_memory=case_memory,
            question=question,
            grounded_answer=grounded_answer,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat prompt package input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    package_data = package.to_dict()
    markdown = render_case_chat_prompt_package_markdown(package)

    table = Table(title="Case Chat Prompt Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case memory", str(case_memory_file))
    table.add_row("Question", package.question)
    table.add_row("Artifact kinds", ", ".join(package.artifact_kinds))
    table.add_row("Redaction applied", str(package.prompt_package.redaction_applied))
    table.add_row("Provider execution", "false")
    table.add_row("Execution", "planning-only; local prompt packaging only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat prompt Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(package_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat prompt JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local reviewable prompt package. "
        "It does not call LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-gate")
def case_chat_provider_gate_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to case-chat prompt package JSON."),
    provider_name: str = typer.Option("disabled", "--provider", help="Future LLM provider name. Current default is disabled."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Check the local provider gate for a case-chat prompt package without calling any provider."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        gate = build_case_chat_provider_gate(
            data,
            provider_name=provider_name,
            allow_provider_execution=allow_provider_execution,
            require_prompt_audit_pass=require_prompt_audit_pass,
            model=model,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat provider gate input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    gate_data = gate.to_dict()
    markdown = gate.to_markdown()

    table = Table(title="Case Chat Provider Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", gate.provider_name)
    table.add_row("Allowed", str(gate.allowed))
    table.add_row("Audit status", gate.audit_status)
    table.add_row("Reason", gate.reason)
    table.add_row("Provider execution performed", "false")
    console.print(table)

    if gate.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in gate.required_actions:
            console.print(f"- {action}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only checks a local provider gate. "
        "It does not call LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-dry-run")
def case_chat_provider_dry_run_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to case-chat prompt package JSON."),
    provider_name: str = typer.Option("disabled", "--provider", help="Future LLM provider name. Current default is disabled."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a real provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Dry-run the local prompt audit, provider gate, and disabled provider stub."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        dry_run = build_case_chat_provider_dry_run(
            data,
            provider_name=provider_name,
            allow_provider_execution=allow_provider_execution,
            require_prompt_audit_pass=require_prompt_audit_pass,
            model=model,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat provider dry-run input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    dry_run_data = dry_run.to_dict()
    markdown = dry_run.to_markdown()

    table = Table(title="Case Chat Provider Dry Run")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", dry_run.provider_name)
    table.add_row("Audit status", dry_run.audit_status)
    table.add_row("Gate allowed", str(dry_run.gate_allowed))
    table.add_row("Gate reason", dry_run.gate_reason)
    table.add_row("Disabled provider status", dry_run.disabled_provider_status)
    table.add_row("Provider execution performed", "false")
    console.print(table)

    if dry_run.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in dry_run.required_actions:
            console.print(f"- {action}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider dry-run Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(dry_run_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider dry-run JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only performs a local dry-run. "
        "It does not call real LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-result-import")
def case_chat_provider_result_import_command(
    provider_result_file: Path = typer.Option(..., "--provider-result", help="Path to manually saved provider output text."),
    prompt_package_file: Path = typer.Option(..., "--prompt-package", help="Path to case-chat prompt package JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import manually saved provider output as an untrusted local suggestion."""
    if not provider_result_file.exists():
        console.print(f"[bold red]Provider result text not found:[/bold red] {provider_result_file}")
        raise typer.Exit(code=1)

    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    provider_output = provider_result_file.read_text(encoding="utf-8")

    try:
        prompt_package = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(prompt_package, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        imported = import_case_chat_provider_result(provider_output, prompt_package)
    except ValueError as exc:
        console.print(f"[bold red]Invalid provider result import input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    imported_data = imported.to_dict()
    markdown = imported.to_markdown()

    table = Table(title="Imported Case Chat Provider Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider result", str(provider_result_file))
    table.add_row("Prompt package", str(prompt_package_file))
    table.add_row("Suggested actions", str(len(imported.suggested_actions)))
    table.add_row("Warning flags", str(len(imported.warning_flags)))
    table.add_row("Untrusted suggestion", "true")
    table.add_row("Provider execution by Blackhole", "false")
    console.print(table)

    if imported.warning_flags:
        console.print("[bold yellow]Warning flags:[/bold yellow]")
        for flag in imported.warning_flags:
            console.print(f"- {flag}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved imported provider result Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(imported_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved imported provider result JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports local provider output as an untrusted suggestion. "
        "It does not call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("interpret-result")
def interpret_result_command(
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint that was manually validated."),
    observed_status: int | None = typer.Option(None, "--observed-status", help="Observed HTTP status code."),
    expected_status: int | None = typer.Option(None, "--expected-status", help="Expected HTTP status code."),
    observed_body: str = typer.Option("", "--observed-body", help="Short observed response/body note."),
    expected_body: str = typer.Option("", "--expected-body", help="Short expected response/body note."),
    note: str = typer.Option("", "--note", help="Human validation note."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Interpret a manual validation result summary."""
    result = interpret_validation_result(
        endpoint=endpoint,
        observed_status=observed_status,
        expected_status=expected_status,
        observed_body=observed_body,
        expected_body=expected_body,
        note=note,
    )
    data = result.to_dict()

    table = Table(title="Result Interpretation")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Endpoint", endpoint)
    table.add_row("Suggested result", result.suggested_result)
    table.add_row("Confidence", result.confidence)
    table.add_row("Rationale", result.rationale)
    table.add_row("Signals", str(len(result.signals)))
    table.add_row("Execution", "planning-only; no request execution")
    console.print(table)

    signals_table = Table(title="Interpretation Signals")
    signals_table.add_column("#", justify="right")
    signals_table.add_column("Signal")
    signals_table.add_column("Weight", justify="right")
    signals_table.add_column("Reason")

    for index, signal in enumerate(result.signals, start=1):
        signals_table.add_row(
            str(index),
            signal.name,
            str(signal.weight),
            signal.reason,
        )

    console.print(signals_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result interpretation JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only interprets a human-provided result summary. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("research-state-update")
def research_state_update_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint to update in the research state."),
    validation_result: str = typer.Option(
        ...,
        "--validation-result",
        help="Manual validation result: supported, rejected, needs-more-evidence, or deprioritize.",
    ),
    note: str = typer.Option("", "--note", help="Optional human validation note."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the update plan.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured update plan.",
    ),
):
    """Build a planning-only research-state update plan."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_research_state_update_plan(
            data,
            endpoint=endpoint,
            validation_result=validation_result,
            note=note,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid validation result:[/bold red] {exc}")
        raise typer.Exit(code=2)

    markdown = render_research_state_update_plan_markdown(plan)
    plan_data = plan.to_dict()

    summary = Table(title="Research State Update Plan")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", plan.target_name)
    summary.add_row("Endpoint", plan.endpoint)
    summary.add_row("Validation result", plan.validation_result)
    summary.add_row("Actions", str(len(plan.actions)))
    summary.add_row("Human review required", str(plan.required_human_review))
    summary.add_row("Execution", "planning-only; no state mutation, tool execution, network, browser, Kali, shell, or LLM execution")
    console.print(summary)

    actions_table = Table(title="Proposed State Updates")
    actions_table.add_column("#", justify="right")
    actions_table.add_column("Path")
    actions_table.add_column("Old")
    actions_table.add_column("New")
    actions_table.add_column("Reason")

    for index, action in enumerate(plan.actions, start=1):
        actions_table.add_row(
            str(index),
            escape(action.path),
            escape(str(action.old_value)),
            escape(str(action.new_value)),
            escape(action.reason),
        )

    console.print(actions_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research-state update Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research-state update JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only proposes research-state updates. "
        "It does not mutate files automatically or execute tools."
    )


@app.command("research-state")
def research_state_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the research state summary.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured research state.",
    ),
):
    """Build planning-only research state / case memory from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    state = build_research_state_from_orchestration(data)
    markdown = render_research_state_markdown(state)
    state_data = state.to_dict()

    summary = Table(title="Research State / Case Memory")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", state.target_name)
    summary.add_row("Endpoints", str(state.endpoint_count))
    summary.add_row("Decisions", str(len(state.decisions)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    endpoint_table = Table(title="Research State Endpoints")
    endpoint_table.add_column("#", justify="right")
    endpoint_table.add_column("Endpoint")
    endpoint_table.add_column("Priority")
    endpoint_table.add_column("Triage")
    endpoint_table.add_column("Hypotheses", justify="right")
    endpoint_table.add_column("Artifacts", justify="right")

    for index, endpoint_state in enumerate(state.endpoints, start=1):
        endpoint_table.add_row(
            str(index),
            endpoint_state.endpoint,
            f"{endpoint_state.priority_band}/{endpoint_state.priority_score}",
            endpoint_state.triage_state,
            str(len(endpoint_state.hypotheses)),
            str(len(endpoint_state.artifacts)),
        )

    console.print(endpoint_table)

    decision_table = Table(title="Research State Decisions")
    decision_table.add_column("#", justify="right")
    decision_table.add_column("Decision")
    decision_table.add_column("Status")
    decision_table.add_column("Rationale")

    for index, decision in enumerate(state.decisions, start=1):
        decision_table.add_row(
            str(index),
            decision.name,
            decision.status,
            decision.rationale,
        )

    console.print(decision_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research state Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(state_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research state JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates planning-only case memory. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("validation-runbook")
def validation_runbook_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the validation runbook.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured validation runbook.",
    ),
):
    """Build a planning-only validation runbook from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    runbook = build_validation_runbook(data)
    markdown = render_validation_runbook_markdown(runbook)
    runbook_data = runbook.to_dict()

    summary = Table(title="Validation Runbook")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", runbook.target_name)
    summary.add_row("Endpoint runbooks", str(runbook.endpoint_count))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    endpoint_table = Table(title="Validation Runbook Endpoints")
    endpoint_table.add_column("#", justify="right")
    endpoint_table.add_column("Endpoint")
    endpoint_table.add_column("Priority")
    endpoint_table.add_column("Steps", justify="right")
    endpoint_table.add_column("Approval Steps", justify="right")

    for index, endpoint_runbook in enumerate(runbook.endpoint_runbooks, start=1):
        approval_count = sum(1 for step in endpoint_runbook.steps if step.human_approval_required)
        endpoint_table.add_row(
            str(index),
            endpoint_runbook.endpoint,
            f"{endpoint_runbook.priority_band}/{endpoint_runbook.priority_score}",
            str(len(endpoint_runbook.steps)),
            str(approval_count),
        )

    console.print(endpoint_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation runbook Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(runbook_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation runbook JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a manual validation runbook. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("report-draft")
def report_draft_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the report draft.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured report draft.",
    ),
):
    """Build a planning-only report draft from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    draft = build_report_draft(data)
    markdown = render_report_draft_markdown(draft)
    draft_data = draft.to_dict()

    summary = Table(title="Report Draft")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Title", draft.title)
    summary.add_row("Target", draft.target_name)
    summary.add_row("Endpoints", str(draft.endpoint_count))
    summary.add_row("Sections", str(len(draft.sections)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    section_table = Table(title="Report Draft Sections")
    section_table.add_column("#", justify="right")
    section_table.add_column("Section")

    for index, section in enumerate(draft.sections, start=1):
        section_table.add_row(str(index), section.title)

    console.print(section_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved report draft Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved report draft JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a report skeleton. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("evidence-workspace")
def evidence_workspace_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON containing evidence requirements."),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "--out",
        help="Directory where the local evidence workspace should be created.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the workspace manifest without creating files.",
    ),
):
    """Create a local evidence workspace from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    manifest = build_evidence_workspace_manifest(data, output_dir)
    manifest_data = manifest.to_dict()

    summary = Table(title="Evidence Workspace")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", manifest.target_name)
    summary.add_row("Output dir", manifest.workspace_root)
    summary.add_row("Endpoints", str(manifest.endpoint_count))
    summary.add_row("Mode", "dry-run" if dry_run else "write-files")
    summary.add_row("Execution", "local-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    files_table = Table(title="Workspace Files")
    files_table.add_column("#", justify="right")
    files_table.add_column("Path")
    files_table.add_column("Purpose")

    all_files = list(manifest.files)
    for endpoint in manifest.endpoints:
        all_files.extend(endpoint.files)

    for index, file in enumerate(all_files, start=1):
        files_table.add_row(str(index), file.path, file.purpose)

    console.print(files_table)

    if dry_run:
        console.print("[bold yellow]Dry run:[/bold yellow] no files were created.")
    else:
        materialize_evidence_workspace(manifest)
        console.print(f"[bold green]Evidence workspace created:[/bold green] {output_dir}")

    manifest_path = output_dir / "manifest.json"
    console.print(f"[bold]Manifest path:[/bold] {manifest_path}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates local planning files. "
        "It does not send requests, execute shell commands against targets, launch browsers, or call LLM providers."
    )


@app.command("evidence-requirements")
def evidence_requirements_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save evidence requirements JSON.",
    ),
):
    """Build planning-only evidence requirements for endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)
    plan = build_evidence_requirement_plan(endpoint_values)
    data = plan.to_dict()

    summary = Table(title="Evidence Requirements Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Input file", str(input_file))
    summary.add_row("Endpoints", str(plan.endpoint_count))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    requirement_names = sorted({
        requirement.name
        for endpoint_plan in plan.endpoint_plans
        for requirement in endpoint_plan.requirements
    })
    console.print("[bold]Requirement names:[/bold] " + ", ".join(requirement_names))

    for endpoint_plan in plan.endpoint_plans:
        endpoint_table = Table(title=f"Evidence Requirements: {endpoint_plan.endpoint}")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Requirement")
        endpoint_table.add_column("Artifact")
        endpoint_table.add_column("Sensitivity")
        endpoint_table.add_column("Redact")
        endpoint_table.add_column("Approval")

        for index, requirement in enumerate(endpoint_plan.requirements, start=1):
            endpoint_table.add_row(
                str(index),
                requirement.name,
                requirement.artifact_type,
                requirement.sensitivity,
                "YES" if requirement.redaction_required else "NO",
                "YES" if requirement.human_approval_required else "NO",
            )

        console.print(endpoint_table)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only plans evidence collection. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved evidence requirements JSON:[/bold green] {json_output}")


@app.command("attack-surface")
def attack_surface_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save attack surface grouping JSON.",
    ),
):
    """Group endpoints into planning-only attack-surface buckets."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)
    surface = build_attack_surface_map(endpoint_values)
    data = surface.to_dict()

    summary = Table(title="Attack Surface Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Input file", str(input_file))
    summary.add_row("Endpoints", str(surface.endpoint_count))
    summary.add_row("Groups", str(len(surface.groups)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    group_table = Table(title="Attack Surface Groups")
    group_table.add_column("#", justify="right")
    group_table.add_column("Group")
    group_table.add_column("Count", justify="right")
    group_table.add_column("Max Score", justify="right")
    group_table.add_column("Avg Score", justify="right")
    group_table.add_column("Priority Hint")

    for index, group in enumerate(surface.groups, start=1):
        group_table.add_row(
            str(index),
            group.spec.name,
            str(group.count),
            str(group.max_score),
            str(group.average_score),
            group.spec.priority_hint,
        )

    console.print(group_table)

    for group in surface.groups:
        endpoint_table = Table(title=f"{group.spec.title} ({group.spec.name})")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Score", justify="right")
        endpoint_table.add_column("Band")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(group.endpoints, start=1):
            endpoint_table.add_row(
                str(index),
                str(endpoint.score),
                endpoint.band,
                endpoint.endpoint,
            )

        console.print(endpoint_table)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only groups endpoint strings. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved attack surface JSON:[/bold green] {json_output}")


@app.command("endpoint-priority")
def endpoint_priority_command(
    endpoint: str = typer.Argument(..., help="Endpoint path or URL to score."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save endpoint priority JSON.",
    ),
):
    """Score one endpoint using planning-only priority heuristics."""
    result = score_endpoint(endpoint)
    data = result.to_dict()

    summary = Table(title="Endpoint Priority Score")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", result.endpoint)
    summary.add_row("Normalized path", result.normalized_path)
    summary.add_row("Score", str(result.score))
    summary.add_row("Band", result.band)
    summary.add_row("Categories", ", ".join(result.categories))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    console.print("[bold]Signal names:[/bold] " + ", ".join(signal.name for signal in result.signals))

    signal_table = Table(title="Priority Signals")
    signal_table.add_column("#", justify="right")
    signal_table.add_column("Signal")
    signal_table.add_column("Points", justify="right")
    signal_table.add_column("Reason")

    for index, signal in enumerate(result.signals, start=1):
        signal_table.add_row(
            str(index),
            signal.name,
            str(signal.points),
            signal.reason,
        )

    console.print(signal_table)

    if result.recommended_next_steps:
        console.print("[bold]Recommended next steps:[/bold]")
        for step in result.recommended_next_steps:
            console.print(f"- {step}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only scores and explains priority. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved endpoint priority JSON:[/bold green] {json_output}")


@app.command("prioritize-endpoints")
def prioritize_endpoints_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save prioritized endpoint JSON.",
    ),
):
    """Score and sort endpoints from highest to lowest priority."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    mined = [endpoint.value for endpoint in mine_endpoints(text)]
    line_candidates = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    endpoint_values = sorted(set(mined + line_candidates))
    results = prioritize_endpoints(endpoint_values)
    data = {
        "input_file": str(input_file),
        "endpoint_count": len(results),
        "planning_only": True,
        "execution_state": "not_executed",
        "results": [result.to_dict() for result in results],
    }

    summary = Table(title="Prioritized Endpoints")
    summary.add_column("#", justify="right")
    summary.add_column("Score", justify="right")
    summary.add_column("Band")
    summary.add_column("Endpoint")

    for index, result in enumerate(results, start=1):
        summary.add_row(
            str(index),
            str(result.score),
            result.band,
            result.endpoint,
        )

    console.print(summary)

    console.print("[bold]Priority order:[/bold]")
    for index, result in enumerate(results, start=1):
        console.print(f"{index}. [{result.band}] {result.score} - {result.endpoint}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only ranks endpoint strings. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved prioritized endpoint JSON:[/bold green] {json_output}")


@app.command("plan-curl")
def plan_curl_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to build a safe curl plan for."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum curl execution time in seconds."),
):
    """Build a safe curl command plan after Scope Guard approval."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    plan = build_curl_plan(scope=scope, url=url, method=method, timeout=timeout)

    table = Table(title="Safe Curl Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Human approval required", "YES" if plan.requires_human_approval else "NO")
    table.add_row("Command", plan.command_text if plan.command_text else "not generated")

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)


@app.command("run-curl")
def run_curl_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to request with safe curl execution."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum curl execution time in seconds."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Actually execute after Scope Guard approval."),
):
    """Execute a safe curl request only after Scope Guard approval and explicit --yes."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    plan = build_curl_plan(scope=scope, url=url, method=method, timeout=timeout)

    table = Table(title="Safe Curl Execution")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Command", plan.command_text if plan.command_text else "not generated")
    table.add_row("Execution requested", "YES" if yes else "NO")

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)

    if not yes:
        console.print()
        console.print("[yellow]Preview only.[/yellow] Re-run with [bold]--yes[/bold] to execute.")
        return

    result = execute_curl_plan(plan)
    parsed = parse_http_response(result.stdout)
    summary = summarize_response(parsed.status_code, parsed.headers, parsed.body)

    store = EvidenceStore()
    evidence_path = store.save_http_evidence(
        target_name=scope.target_name,
        task_name=f"curl {method.upper()} {url}",
        url=url,
        method=method,
        request={"command": result.command_text},
        response_headers=parsed.headers,
        response_body=parsed.body,
        status_code=parsed.status_code,
        notes="Captured by bugintel run-curl",
    )

    console.print()
    console.print(f"[bold]Exit code:[/bold] {result.exit_code}")
    console.print(f"[bold]Parsed status:[/bold] {parsed.status_code}")
    console.print(f"[bold]Body size:[/bold] {summary.body_size} bytes")
    console.print(f"[bold]Interesting keywords:[/bold] {', '.join(summary.interesting_keywords) if summary.interesting_keywords else 'none'}")
    console.print(f"[bold green]Evidence saved:[/bold green] {evidence_path}")

    if result.stdout:
        console.print()
        console.print("[bold green]STDOUT preview:[/bold green]")
        console.print(result.stdout[:4000])

    if result.stderr:
        console.print()
        console.print("[bold red]STDERR preview:[/bold red]")
        console.print(result.stderr[:2000])


@app.command("generate-report")
def generate_report_command(
    evidence_file: Path = typer.Argument(..., help="Evidence JSON file to convert into Markdown."),
    output_file: Path = typer.Option(..., "--output", "-o", help="Output Markdown report path."),
):
    """Generate a Markdown evidence report from saved evidence JSON."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence file not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    saved = save_evidence_report(evidence_file, output_file)

    console.print(f"[bold green]Report generated:[/bold green] {saved}")


@app.command("save-browser-capture")
def save_browser_capture_command(
    capture_file: Path = typer.Argument(..., help="Browser capture result JSON file to save as evidence."),
):
    """
    Save a browser capture result JSON as redacted browser evidence.

    This command does not execute a browser. It stores output from a future
    Playwright/DevTools/browser capture adapter using the browser evidence model.
    """
    if not capture_file.exists():
        console.print(f"[bold red]Browser capture file not found:[/bold red] {capture_file}")
        raise typer.Exit(code=1)

    data = json.loads(capture_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser"]
    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        console.print(
            "[bold red]Browser capture file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    result = BrowserCaptureResult(
        target_name=str(data["target_name"]),
        task_name=str(data["task_name"]),
        start_url=str(data["start_url"]),
        browser=str(data["browser"]),
        network_events=list(data.get("network_events") or []),
        screenshots=list(data.get("screenshots") or []),
        html_snapshots=list(data.get("html_snapshots") or []),
        execution_output=dict(data.get("execution_output") or {}),
        notes=str(data.get("notes") or "Captured by bugintel save-browser-capture"),
    )

    store = EvidenceStore()
    evidence_path = store.save_browser_evidence(**result.to_evidence_kwargs())

    console.print(f"[bold green]Browser evidence saved:[/bold green] {evidence_path}")




def _research_plan_from_dict(data: dict) -> ResearchPlan:
    hypotheses = []

    for item in data.get("hypotheses", []):
        evidence_refs = tuple(
            EvidenceReference(
                evidence_type=str(ref.get("evidence_type", "")),
                source=str(ref.get("source", "")),
                locator=str(ref.get("locator", "")),
                summary=str(ref.get("summary", "")),
                tags=tuple(ref.get("tags", [])),
            )
            for ref in item.get("evidence", [])
            if isinstance(ref, dict)
        )

        hypotheses.append(
            ResearchHypothesis(
                title=str(item.get("title", "")),
                category=str(item.get("category", "")),
                rationale=str(item.get("rationale", "")),
                confidence=str(item.get("confidence", "medium")),
                evidence=evidence_refs,
                suggested_tests=tuple(item.get("suggested_tests", [])),
                tags=tuple(item.get("tags", [])),
            )
        )

    recommendations = []

    for item in data.get("recommendations", []):
        recommendations.append(
            ResearchRecommendation(
                priority=int(item.get("priority", 1)),
                title=str(item.get("title", "")),
                reason=str(item.get("reason", "")),
                next_actions=tuple(item.get("next_actions", [])),
                related_hypotheses=tuple(item.get("related_hypotheses", [])),
                safety_notes=tuple(item.get("safety_notes", [])),
            )
        )

    return ResearchPlan(
        target_name=str(data.get("target_name", "unknown-target")),
        source_evidence_type=str(data.get("source_evidence_type", "browser")),
        generated_by=str(data.get("generated_by", "deterministic")),
        hypotheses=tuple(hypotheses),
        recommendations=tuple(recommendations),
        safety_notes=tuple(data.get("safety_notes", ())),
    )



def _llm_prompt_package_from_dict(data: dict) -> LLMPromptPackage:
    safety_notes = data.get("safety_notes", ())

    return LLMPromptPackage(
        system_prompt=str(data.get("system_prompt", "")),
        user_prompt=str(data.get("user_prompt", "")),
        redaction_applied=bool(data.get("redaction_applied", False)),
        source=str(data.get("source", "research_plan")),
        safety_notes=tuple(safety_notes),
    )



@app.command("audit-llm-prompt")
def audit_llm_prompt_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to LLM prompt package JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the prompt safety audit JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the prompt safety audit Markdown."),
):
    """Audit an LLM prompt package locally before provider use."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]LLM prompt package file not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid LLM prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]LLM prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = _llm_prompt_package_from_dict(data)
    report = audit_llm_prompt_package(package)
    report_data = report.to_dict()

    table = Table(title="LLM Prompt Safety Audit")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Status", report.status)
    table.add_row("Findings", str(report.finding_count))
    table.add_row("High", str(report.high_count))
    table.add_row("Medium", str(report.medium_count))
    table.add_row("Low", str(report.low_count))

    console.print(table)

    if report.findings:
        findings_table = Table(title="Prompt Safety Findings")
        findings_table.add_column("Severity", style="bold")
        findings_table.add_column("Category")
        findings_table.add_column("Label")
        findings_table.add_column("Evidence")

        for finding in report.findings:
            findings_table.add_row(
                finding.severity,
                finding.category,
                finding.label,
                finding.evidence,
            )

        console.print(findings_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(report_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt safety audit JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_llm_prompt_safety_markdown(report),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt safety audit Markdown saved:[/bold green] {markdown_output}")



@app.command("llm-provider-status")
def llm_provider_status_command(
    provider_name: str = typer.Option("disabled", "--provider", help="LLM provider name to validate."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    timeout_seconds: int = typer.Option(30, "--timeout-seconds", help="Future provider timeout setting."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save provider gate status JSON.",
    ),
):
    """Show the disabled-by-default LLM provider gate status."""
    config = LLMProviderConfig(
        provider_name=provider_name,
        allow_provider_execution=allow_provider_execution,
        require_prompt_audit_pass=require_prompt_audit_pass,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    gate = validate_provider_config(config)
    payload = {
        "config": config.to_dict(),
        "gate": gate.to_dict(),
        "notes": (
            "This command only validates configuration. "
            "It does not read API keys, call providers, make network requests, or execute commands."
        ),
    }

    table = Table(title="LLM Provider Gate Status")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", gate.provider_name)
    table.add_row("Allowed", str(gate.allowed))
    table.add_row("Reason", gate.reason)
    table.add_row("Require prompt audit pass", str(config.require_prompt_audit_pass))
    table.add_row("Model", config.model or "<unset>")
    table.add_row("Timeout seconds", str(config.timeout_seconds))
    console.print(table)

    if gate.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in gate.required_actions:
            console.print(f"- {action}")

    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        console.print(f"[bold green]LLM provider gate status JSON saved:[/bold green] {json_output}")


@app.command("run-llm-provider")
def run_llm_provider_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to LLM prompt package JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the disabled provider result JSON."),
):
    """Run the disabled-by-default LLM provider stub."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]LLM prompt package file not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid LLM prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]LLM prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = _llm_prompt_package_from_dict(data)
    result = run_disabled_llm_provider(package)
    result_data = result.to_dict()

    table = Table(title="LLM Provider Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Provider", result.provider_name)
    table.add_row("Status", result.status)
    table.add_row("Reason", result.reason)
    table.add_row("Model", result.model or "-")
    table.add_row("Output Bytes", str(len(result.output_text.encode("utf-8"))))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM provider result JSON saved:[/bold green] {json_output}")


@app.command("build-llm-prompt")
def build_llm_prompt_command(
    research_plan_file: Path = typer.Argument(..., help="Path to deterministic research plan JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the LLM prompt package JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the LLM prompt package Markdown."),
):
    """Build a safe reviewable LLM prompt package from a deterministic research plan."""
    if not research_plan_file.exists():
        console.print(f"[bold red]Research plan file not found:[/bold red] {research_plan_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research plan JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = _research_plan_from_dict(data)
    package = build_llm_prompt_package_from_research_plan(plan)
    package_data = package.to_dict()

    table = Table(title="LLM Prompt Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Source", package.source)
    table.add_row("Redaction Applied", "YES" if package.redaction_applied else "NO")
    table.add_row("Safety Notes", str(len(package.safety_notes)))
    table.add_row("System Prompt Bytes", str(len(package.system_prompt.encode("utf-8"))))
    table.add_row("User Prompt Bytes", str(len(package.user_prompt.encode("utf-8"))))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(package_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt package JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_llm_prompt_package_markdown(package),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt package Markdown saved:[/bold green] {markdown_output}")


@app.command("plan-research")
def plan_research_command(
    evidence_file: Path = typer.Argument(..., help="Path to browser evidence or browser capture-result JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the research plan JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the research plan Markdown report."),
):
    """Build a deterministic research plan from existing browser evidence."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence file not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    try:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON evidence file:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(evidence, dict):
        console.print("[bold red]Evidence JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_research_plan_from_browser_evidence(evidence)
    plan_data = plan.to_dict()

    table = Table(title="Research Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", plan.target_name)
    table.add_row("Source Evidence Type", plan.source_evidence_type)
    table.add_row("Generated By", plan.generated_by)
    table.add_row("Hypotheses", str(len(plan.hypotheses)))
    table.add_row("Recommendations", str(len(plan.recommendations)))

    console.print(table)

    if plan.hypotheses:
        hypothesis_table = Table(title="Research Hypotheses")
        hypothesis_table.add_column("Category", style="bold")
        hypothesis_table.add_column("Confidence")
        hypothesis_table.add_column("Title")

        for hypothesis in plan.hypotheses:
            hypothesis_table.add_row(
                hypothesis.category,
                hypothesis.confidence,
                hypothesis.title,
            )

        console.print(hypothesis_table)

    if plan.recommendations:
        recommendation_table = Table(title="Research Recommendations")
        recommendation_table.add_column("Priority", style="bold")
        recommendation_table.add_column("Title")
        recommendation_table.add_column("Reason")

        for recommendation in plan.recommendations:
            recommendation_table.add_row(
                str(recommendation.priority),
                recommendation.title,
                recommendation.reason,
            )

        console.print(recommendation_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(plan_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Research plan JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_research_plan_markdown(plan),
            encoding="utf-8",
        )
        console.print(f"[bold green]Research plan Markdown saved:[/bold green] {markdown_output}")


@app.command("orchestrate")
def orchestrate_command(
    input_file: Path = typer.Argument(..., help="File containing JS/HTML/HAR/log text to mine endpoints from."),
    target_name: str = typer.Option("demo-lab", "--target", "-t", help="Target/workspace name."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for the orchestration plan."),
):
    """Create a multi-agent research plan from discovered endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)

    plan = create_orchestration_plan(
        target_name=target_name,
        endpoints=endpoint_values,
    )

    rendered = render_tree(plan.root)

    console.print(f"[bold green]Created orchestration plan for:[/bold green] {target_name}")
    console.print(f"[bold]Endpoints discovered:[/bold] {len(plan.endpoints)}")
    console.print(f"[bold]Agent assignments:[/bold] {len(plan.assignments)}")
    console.print()
    console.print(rendered)

    table = Table(title="Agent Assignments")
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Agent")
    table.add_column("Mode")
    table.add_column("Human Approval")

    for index, assignment in enumerate(plan.assignments, start=1):
        table.add_row(
            str(index),
            assignment.endpoint,
            assignment.agent_name,
            assignment.mode,
            "YES" if assignment.requires_human_approval else "NO",
        )

    console.print()
    console.print(table)

    _print_endpoint_priority_table(plan.endpoint_priorities)
    _print_attack_surface_table(plan.attack_surface_map)
    _print_evidence_requirements_table(plan.evidence_requirement_plan)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
        console.print()
        console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("analyze-html")
def analyze_html_command(
    html_file: Path = typer.Argument(..., help="HTML file to analyze."),
    base_url: str = typer.Option(..., "--base-url", help="Base URL used to resolve relative links."),
):
    """Passively analyze HTML for links, scripts, forms, and endpoints."""
    if not html_file.exists():
        console.print(f"[bold red]HTML file not found:[/bold red] {html_file}")
        raise typer.Exit(code=1)

    html = html_file.read_text(encoding="utf-8", errors="replace")
    result = analyze_html(base_url=base_url, html=html)

    summary = Table(title="Website Recon Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("Links", str(len(result.links)))
    summary.add_row("Scripts", str(len(result.scripts)))
    summary.add_row("Forms", str(len(result.forms)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.links:
        table = Table(title="Links")
        table.add_column("#", justify="right")
        table.add_column("URL")
        for index, link in enumerate(result.links, start=1):
            table.add_row(str(index), link)
        console.print(table)

    if result.scripts:
        table = Table(title="JavaScript Sources")
        table.add_column("#", justify="right")
        table.add_column("Script URL")
        for index, script in enumerate(result.scripts, start=1):
            table.add_row(str(index), script)
        console.print(table)

    if result.forms:
        table = Table(title="Forms")
        table.add_column("#", justify="right")
        table.add_column("Method")
        table.add_column("Action")
        table.add_column("Inputs")
        for index, form in enumerate(result.forms, start=1):
            table.add_row(str(index), form.method, form.action, ", ".join(form.inputs))
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("fetch-page")
def fetch_page_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to fetch and analyze."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
):
    """Fetch one in-scope web page, analyze HTML, and save evidence."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    result = fetch_web_page(scope=scope, url=url, timeout=timeout)

    table = Table(title="Website Fetch Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Allowed", "YES" if result.allowed else "NO")
    table.add_row("Reason", result.reason)
    table.add_row("Final URL", result.final_url or "none")
    table.add_row("Status", str(result.status_code) if result.status_code is not None else "none")
    table.add_row("Error", result.error or "none")

    console.print(table)

    if not result.allowed:
        raise typer.Exit(code=2)

    if result.error:
        raise typer.Exit(code=3)

    recon = analyze_html(base_url=result.final_url or url, html=result.text)

    summary = Table(title="Passive HTML Analysis")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("Links", str(len(recon.links)))
    summary.add_row("Scripts", str(len(recon.scripts)))
    summary.add_row("Forms", str(len(recon.forms)))
    summary.add_row("Endpoints", str(len(recon.endpoints)))

    console.print(summary)

    if recon.endpoints:
        endpoint_table = Table(title="Discovered Endpoints")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(recon.endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)

    store = EvidenceStore()
    evidence_path = store.save_http_evidence(
        target_name=scope.target_name,
        task_name=f"fetch page {url}",
        url=url,
        method="GET",
        request={"url": url, "type": "website_fetch"},
        response_headers=result.headers,
        response_body=result.text,
        status_code=result.status_code,
        notes="Captured by bugintel fetch-page",
    )

    console.print(f"[bold green]Evidence saved:[/bold green] {evidence_path}")


@app.command("collect-js")
def collect_js_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    page_url: str = typer.Argument(..., help="Page URL to fetch, analyze, and collect JS from."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
):
    """Fetch one in-scope page, collect JavaScript sources, and mine JS endpoints."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    page = fetch_web_page(scope=scope, url=page_url, timeout=timeout)

    table = Table(title="Page Fetch")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", scope.target_name)
    table.add_row("Page URL", page_url)
    table.add_row("Allowed", "YES" if page.allowed else "NO")
    table.add_row("Reason", page.reason)
    table.add_row("Status", str(page.status_code) if page.status_code is not None else "none")
    table.add_row("Error", page.error or "none")
    console.print(table)

    if not page.allowed:
        raise typer.Exit(code=2)

    if page.error:
        raise typer.Exit(code=3)

    result = collect_js_sources(
        scope=scope,
        page_url=page.final_url or page_url,
        html=page.text,
        timeout=timeout,
    )

    summary = Table(title="JavaScript Collection Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Scripts discovered", str(result.script_count))
    summary.add_row("Script fetch results", str(len(result.sources)))
    summary.add_row("Unique JS endpoints", str(len(result.all_endpoints)))
    console.print(summary)

    if result.sources:
        sources_table = Table(title="JavaScript Sources")
        sources_table.add_column("#", justify="right")
        sources_table.add_column("URL")
        sources_table.add_column("Allowed")
        sources_table.add_column("Status")
        sources_table.add_column("Endpoints")
        sources_table.add_column("Reason/Error")

        for index, source in enumerate(result.sources, start=1):
            reason_error = source.error or source.reason
            sources_table.add_row(
                str(index),
                source.url,
                "YES" if source.allowed else "NO",
                str(source.status_code) if source.status_code is not None else "none",
                str(len(source.endpoints)),
                reason_error,
            )

        console.print(sources_table)

    if result.all_endpoints:
        endpoint_table = Table(title="Endpoints Mined from JavaScript")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(result.all_endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)


@app.command("web-recon")
def web_recon_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    page_url: str = typer.Argument(..., help="Page URL to run website recon against."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for orchestration plan."),
):
    """Run Website Mode pipeline: fetch page, analyze HTML, collect JS, mine endpoints, orchestrate."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    result = run_website_recon(
        scope=scope,
        page_url=page_url,
        timeout=timeout,
    )

    fetch_table = Table(title="Website Recon Fetch")
    fetch_table.add_column("Field", style="bold")
    fetch_table.add_column("Value")
    fetch_table.add_row("Target", scope.target_name)
    fetch_table.add_row("Page URL", page_url)
    fetch_table.add_row("Allowed", "YES" if result.fetch.allowed else "NO")
    fetch_table.add_row("Reason", result.fetch.reason)
    fetch_table.add_row("Status", str(result.fetch.status_code) if result.fetch.status_code is not None else "none")
    fetch_table.add_row("Error", result.fetch.error or "none")
    console.print(fetch_table)

    if not result.fetch.allowed:
        raise typer.Exit(code=2)

    if result.fetch.error:
        raise typer.Exit(code=3)

    summary = Table(title="Website Recon Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("HTML links", str(len(result.html_recon.links) if result.html_recon else 0))
    summary.add_row("HTML scripts", str(len(result.html_recon.scripts) if result.html_recon else 0))
    summary.add_row("HTML forms", str(len(result.html_recon.forms) if result.html_recon else 0))
    summary.add_row("JS sources", str(len(result.js_recon.sources) if result.js_recon else 0))
    summary.add_row("Merged endpoints", str(len(result.endpoints)))
    summary.add_row(
        "Agent assignments",
        str(len(result.orchestration_plan.assignments) if result.orchestration_plan else 0),
    )

    console.print(summary)

    if result.endpoints:
        endpoint_table = Table(title="Merged Endpoint Inventory")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(result.endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)

    if result.orchestration_plan:
        assignment_table = Table(title="Agent Assignments")
        assignment_table.add_column("#", justify="right")
        assignment_table.add_column("Endpoint")
        assignment_table.add_column("Agent")
        assignment_table.add_column("Mode")
        assignment_table.add_column("Human Approval")

        for index, assignment in enumerate(result.orchestration_plan.assignments, start=1):
            assignment_table.add_row(
                str(index),
                assignment.endpoint,
                assignment.agent_name,
                assignment.mode,
                "YES" if assignment.requires_human_approval else "NO",
            )

        console.print(assignment_table)

        _print_endpoint_priority_table(result.orchestration_plan.endpoint_priorities)
        _print_attack_surface_table(result.orchestration_plan.attack_surface_map)
        _print_evidence_requirements_table(result.orchestration_plan.evidence_requirement_plan)

        if json_output:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(result.orchestration_plan.to_dict(), indent=2), encoding="utf-8")
            console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("import-har")
def import_har_command(
    har_file: Path = typer.Argument(..., help="HAR file exported from browser DevTools, proxy, or compatible traffic capture."),
    target_name: str = typer.Option("har-import", "--target", "-t", help="Target/workspace name."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for orchestration plan."),
):
    """Import a HAR file, extract endpoints, and optionally save a multi-agent plan."""
    if not har_file.exists():
        console.print(f"[bold red]HAR file not found:[/bold red] {har_file}")
        raise typer.Exit(code=1)

    result = load_har(har_file)

    summary = Table(title="HAR Import Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("HAR file", str(har_file))
    summary.add_row("Entries", str(len(result.entries)))
    summary.add_row("Unique endpoints", str(len(result.endpoints)))
    summary.add_row("API-like entries", str(len(result.api_entries)))

    console.print(summary)

    if result.entries:
        table = Table(title="HAR Entries")
        table.add_column("#", justify="right")
        table.add_column("Method")
        table.add_column("Status")
        table.add_column("Category")
        table.add_column("Endpoint")

        for index, entry in enumerate(result.entries, start=1):
            table.add_row(
                str(index),
                entry.method,
                str(entry.status_code) if entry.status_code is not None else "none",
                entry.category,
                entry.endpoint,
            )

        console.print(table)

    if result.endpoints:
        plan = create_orchestration_plan(
            target_name=target_name,
            endpoints=result.endpoints,
        )

        console.print()
        console.print(f"[bold green]Created orchestration plan for:[/bold green] {target_name}")
        console.print(f"[bold]Agent assignments:[/bold] {len(plan.assignments)}")

        assignment_table = Table(title="Agent Assignments from HAR")
        assignment_table.add_column("#", justify="right")
        assignment_table.add_column("Endpoint")
        assignment_table.add_column("Agent")
        assignment_table.add_column("Mode")
        assignment_table.add_column("Human Approval")

        for index, assignment in enumerate(plan.assignments, start=1):
            assignment_table.add_row(
                str(index),
                assignment.endpoint,
                assignment.agent_name,
                assignment.mode,
                "YES" if assignment.requires_human_approval else "NO",
            )

        console.print(assignment_table)

        _print_endpoint_priority_table(plan.endpoint_priorities, title="Endpoint Priorities from HAR")
        _print_attack_surface_table(plan.attack_surface_map, title="Attack Surface Groups from HAR")
        _print_evidence_requirements_table(plan.evidence_requirement_plan, title="Evidence Requirements from HAR")

        if json_output:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
            console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("analyze-android")
def analyze_android_command(
    manifest_file: Path = typer.Argument(..., help="AndroidManifest.xml file to analyze."),
    extra_file: Path | None = typer.Option(None, "--extra", help="Optional extra config/source text file to mine endpoints from."),
):
    """Analyze Android manifest/config text for components, permissions, deep links, and endpoints."""
    if not manifest_file.exists():
        console.print(f"[bold red]Manifest file not found:[/bold red] {manifest_file}")
        raise typer.Exit(code=1)

    manifest_text = manifest_file.read_text(encoding="utf-8", errors="replace")
    extra_text = ""

    if extra_file:
        if not extra_file.exists():
            console.print(f"[bold red]Extra file not found:[/bold red] {extra_file}")
            raise typer.Exit(code=1)
        extra_text = extra_file.read_text(encoding="utf-8", errors="replace")

    result = analyze_android_manifest(
        manifest_text=manifest_text,
        extra_text=extra_text,
    )

    summary = Table(title="Android Analysis Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("Package", result.package_name or "unknown")
    summary.add_row("Permissions", str(len(result.permissions)))
    summary.add_row("Components", str(len(result.components)))
    summary.add_row("Exported components", str(len(result.exported_components)))
    summary.add_row("Deep links", str(len(result.deep_links)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.permissions:
        table = Table(title="Permissions")
        table.add_column("#", justify="right")
        table.add_column("Permission")
        for index, permission in enumerate(result.permissions, start=1):
            table.add_row(str(index), permission)
        console.print(table)

    if result.components:
        table = Table(title="Components")
        table.add_column("#", justify="right")
        table.add_column("Kind")
        table.add_column("Name")
        table.add_column("Exported")
        for index, component in enumerate(result.components, start=1):
            table.add_row(
                str(index),
                component.kind,
                component.name,
                "YES" if component.exported is True else "NO" if component.exported is False else "unknown",
            )
        console.print(table)

    if result.deep_links:
        table = Table(title="Deep Links")
        table.add_column("#", justify="right")
        table.add_column("Component")
        table.add_column("Scheme")
        table.add_column("Host")
        table.add_column("Path")
        for index, link in enumerate(result.deep_links, start=1):
            table.add_row(str(index), link.component, link.scheme, link.host, link.path)
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints Mined from Android Text")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("analyze-ios")
def analyze_ios_command(
    plist_file: Path = typer.Argument(..., help="iOS Info.plist XML file to analyze."),
    extra_file: Path | None = typer.Option(None, "--extra", help="Optional extra config/source text file to mine endpoints from."),
):
    """Analyze iOS plist/config text for bundle info, URL schemes, associated domains, ATS, hosts, and endpoints."""
    if not plist_file.exists():
        console.print(f"[bold red]Plist file not found:[/bold red] {plist_file}")
        raise typer.Exit(code=1)

    plist_text = plist_file.read_text(encoding="utf-8", errors="replace")
    extra_text = ""

    if extra_file:
        if not extra_file.exists():
            console.print(f"[bold red]Extra file not found:[/bold red] {extra_file}")
            raise typer.Exit(code=1)
        extra_text = extra_file.read_text(encoding="utf-8", errors="replace")

    result = analyze_ios_plist(
        plist_text=plist_text,
        extra_text=extra_text,
    )

    summary = Table(title="iOS Analysis Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("Bundle ID", result.bundle_id or "unknown")
    summary.add_row("Display name", result.display_name or "unknown")
    summary.add_row("URL scheme groups", str(len(result.url_schemes)))
    summary.add_row("Associated domains", str(len(result.associated_domains)))
    summary.add_row(
        "ATS arbitrary loads",
        "YES" if result.ats_allows_arbitrary_loads is True else "NO" if result.ats_allows_arbitrary_loads is False else "unknown",
    )
    summary.add_row("Hosts", str(len(result.hosts)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.url_schemes:
        table = Table(title="URL Schemes")
        table.add_column("#", justify="right")
        table.add_column("Name")
        table.add_column("Schemes")
        for index, item in enumerate(result.url_schemes, start=1):
            table.add_row(str(index), item.name, ", ".join(item.schemes))
        console.print(table)

    if result.associated_domains:
        table = Table(title="Associated Domains")
        table.add_column("#", justify="right")
        table.add_column("Domain")
        for index, domain in enumerate(result.associated_domains, start=1):
            table.add_row(str(index), domain)
        console.print(table)

    if result.hosts:
        table = Table(title="Hosts")
        table.add_column("#", justify="right")
        table.add_column("Host")
        for index, host in enumerate(result.hosts, start=1):
            table.add_row(str(index), host)
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints Mined from iOS Text")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("plan-browser")
def plan_browser_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to plan."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Plan browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Plan screenshot evidence capture."),
):
    """Create a safe browser automation plan after Scope Guard approval."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    table = Table(title="Browser Action Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", plan.target_name)
    table.add_row("Start URL", plan.start_url)
    table.add_row("Browser", plan.browser)
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Human approval required", "YES" if plan.requires_human_approval else "NO")
    table.add_row("Actions", str(len(plan.actions)))

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)

    if plan.actions:
        action_table = Table(title="Planned Browser Actions")
        action_table.add_column("#", justify="right")
        action_table.add_column("Action")
        action_table.add_column("Value")
        action_table.add_column("Description")

        for index, action in enumerate(plan.actions, start=1):
            action_table.add_row(
                str(index),
                action.action_type,
                action.value,
                action.description,
            )

        console.print(action_table)


@app.command("preview-playwright")
def preview_playwright_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to preview."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Preview browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Preview screenshot evidence capture."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Preview HTML snapshot capture."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Preview headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Preview browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Preview page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Preview screenshot artifact path."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Mark preview as live-execution allowed. This command still does not launch a browser."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Preview routing through the real Playwright adapter."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the preview JSON."),
):
    """
    Build a safe Playwright execution preview.

    This command does not launch a browser. It validates the start URL through
    Scope Guard, builds a BrowserPlan, and emits a Playwright execution preview
    that can later feed browser execution/evidence workflows.
    """
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    if not plan.allowed:
        console.print(f"[bold red]Browser plan blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    preview = build_playwright_execution_preview(
        plan=plan,
        config=config,
    )

    table = Table(title="Playwright Execution Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Runner", str(preview["runner"]))
    table.add_row("Status", str(preview["status"]))
    table.add_row("Browser", str(preview["browser"]))
    table.add_row("Start URL", str(preview["start_url"]))
    table.add_row("Live execution allowed", "YES" if preview["live_execution_allowed"] else "NO")
    table.add_row("Use real adapter", "YES" if preview.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if preview["playwright_available"] else "NO")
    table.add_row("Reason", str(preview["reason"]))
    table.add_row("Headless", "YES" if preview["headless"] else "NO")
    table.add_row("Timeout ms", str(preview["timeout_ms"]))
    table.add_row("Wait until", str(preview["wait_until"]))
    table.add_row("Capture network", "YES" if preview["capture_network"] else "NO")
    table.add_row("Capture screenshot", "YES" if preview["capture_screenshot"] else "NO")
    table.add_row("Capture HTML", "YES" if preview["capture_html"] else "NO")
    table.add_row("Screenshot path", str(preview["screenshot_path"]))
    table.add_row("Planned actions", str(len(preview["planned_actions"])))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(preview, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Preview JSON saved:[/bold green] {json_output}")




@app.command("execute-playwright-plan")
def execute_playwright_plan_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to execute."),
    task_name: str = typer.Option("playwright execution", "--task-name", help="Task name for the future browser capture result."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Request browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Request screenshot evidence capture."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Request HTML snapshot capture."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Future headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Future browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Future page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Future screenshot artifact path."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Explicitly pass the live execution safety gate."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Route through the real Playwright adapter after safety gates pass."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the capture result JSON."),
):
    """
    Exercise the safety-gated Playwright execution skeleton.

    This command does not launch a browser yet. By default, it refuses execution.
    It exists to validate that future live browser execution stays behind the
    Scope Guard, explicit human approval, and Playwright availability gates.
    """
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    try:
        result = execute_playwright_plan(
            plan=plan,
            task_name=task_name,
            config=config,
            notes="Captured by bugintel execute-playwright-plan skeleton.",
        )
    except PlaywrightExecutionSafetyError as exc:
        console.print(f"[bold red]Playwright execution blocked:[/bold red] {exc}")
        raise typer.Exit(code=2)

    table = Table(title="Playwright Execution Skeleton")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    output = result.execution_output

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Runner", str(output.get("runner", "playwright")))
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Reason", str(output.get("reason", "")))
    table.add_row("Live execution allowed", "YES" if output.get("live_execution_allowed") else "NO")
    table.add_row("Use real adapter", "YES" if output.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if output.get("playwright_available") else "NO")

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")




@app.command("build-playwright-request")
def build_playwright_request_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL for the future request."),
    task_name: str = typer.Option("playwright request", "--task-name", help="Task name for the browser job ticket."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Include future network capture in the request."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Include future screenshot capture in the request."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Include future HTML snapshot capture in the request."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Future headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Future browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Future page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Future screenshot config path."),
    base_artifact_dir: Path = typer.Option(Path("artifacts/browser"), "--base-artifact-dir", help="Base directory for planned browser artifacts."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Record explicit live-execution approval in the request."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Record real Playwright adapter routing in the request."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the request JSON."),
):
    """Build a reviewable Playwright execution request JSON."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    if not plan.allowed:
        console.print(f"[bold red]Playwright request blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name=task_name,
        config=config,
        base_artifact_dir=base_artifact_dir,
    )

    request_data = request.to_dict()

    table = Table(title="Playwright Execution Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", request.target_name)
    table.add_row("Task", request.task_name)
    table.add_row("Browser", request.browser)
    table.add_row("Start URL", request.start_url)
    table.add_row("Live execution allowed", "YES" if request.config.allow_live_execution else "NO")
    table.add_row("Use real adapter", "YES" if request.config.use_real_adapter else "NO")
    table.add_row("Artifact directory", request.artifacts.artifact_dir)
    table.add_row("Screenshot path", request.artifacts.screenshot_path)
    table.add_row("HTML snapshot path", request.artifacts.html_snapshot_path)
    table.add_row("Network log path", request.artifacts.network_log_path)
    table.add_row("Trace path", request.artifacts.trace_path)
    table.add_row("Planned actions", str(len(request.planned_actions)))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(request_data, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Request JSON saved:[/bold green] {json_output}")




@app.command("preview-playwright-request")
def preview_playwright_request_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the preview JSON."),
):
    """Build a Playwright execution preview from a saved request JSON."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser", "config", "planned_actions"]
    missing_fields = [
        field
        for field in required_fields
        if field not in data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    config_data = data.get("config") or {}
    actions_data = data.get("planned_actions") or []

    actions = [
        BrowserAction(
            action_type=str(action.get("action_type", "")),
            value=str(action.get("value", "")),
            description=str(action.get("description", "")),
        )
        for action in actions_data
        if isinstance(action, dict)
    ]

    plan = BrowserPlan(
        allowed=True,
        reason="Loaded from Playwright execution request JSON.",
        target_name=str(data["target_name"]),
        start_url=str(data["start_url"]),
        browser=str(data["browser"]),
        actions=actions,
        requires_human_approval=True,
    )

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=bool(config_data.get("allow_live_execution", False)),
        use_real_adapter=bool(config_data.get("use_real_adapter", False)),
    )

    preview = build_playwright_execution_preview(
        plan=plan,
        config=config,
    )

    preview["target_name"] = str(data["target_name"])
    preview["task_name"] = str(data["task_name"])
    preview["request_file"] = str(request_file)
    if "artifacts" in data:
        preview["artifacts"] = data["artifacts"]

    table = Table(title="Playwright Request Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", str(preview["target_name"]))
    table.add_row("Task", str(preview["task_name"]))
    table.add_row("Runner", str(preview["runner"]))
    table.add_row("Status", str(preview["status"]))
    table.add_row("Browser", str(preview["browser"]))
    table.add_row("Start URL", str(preview["start_url"]))
    table.add_row("Live execution allowed", "YES" if preview["live_execution_allowed"] else "NO")
    table.add_row("Playwright available", "YES" if preview["playwright_available"] else "NO")
    table.add_row("Reason", str(preview["reason"]))
    table.add_row("Planned actions", str(len(preview["planned_actions"])))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(preview, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Preview JSON saved:[/bold green] {json_output}")




@app.command("execute-playwright-request")
def execute_playwright_request_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file for re-validation."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Explicitly pass the live execution safety gate."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Route through the real Playwright adapter after safety gates pass."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the capture result JSON."),
):
    """Run the safety-gated Playwright execution handoff from a saved request."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    request_data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser", "config", "planned_actions"]
    missing_fields = [
        field
        for field in required_fields
        if field not in request_data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    with scope_file.open("r", encoding="utf-8") as f:
        scope_data = yaml.safe_load(f)

    scope = load_scope_from_dict(scope_data)
    config_data = request_data.get("config") or {}

    plan = build_browser_plan(
        scope=scope,
        start_url=str(request_data["start_url"]),
        browser=str(request_data["browser"]),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
    )

    if not plan.allowed:
        console.print(f"[bold red]Playwright request execution blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=allow_live_execution,
        use_real_adapter=bool(config_data.get("use_real_adapter", False)) or use_real_adapter,
    )

    try:
        result = execute_playwright_plan(
            plan=plan,
            task_name=str(request_data["task_name"]),
            config=config,
            notes="Captured by bugintel execute-playwright-request skeleton.",
        )
    except PlaywrightExecutionSafetyError as exc:
        console.print(f"[bold red]Playwright request execution blocked:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output = result.execution_output

    table = Table(title="Playwright Request Execution Skeleton")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Runner", str(output.get("runner", "playwright")))
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Reason", str(output.get("reason", "")))
    table.add_row("Live execution allowed", "YES" if output.get("live_execution_allowed") else "NO")
    table.add_row("Use real adapter", "YES" if output.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if output.get("playwright_available") else "NO")

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")



@app.command("load-browser-artifacts")
def load_browser_artifacts_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the capture result JSON."),
):
    """Load planned browser artifacts into a capture result JSON."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    request_data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = [
        "target_name",
        "task_name",
        "start_url",
        "browser",
        "config",
        "planned_actions",
        "artifacts",
    ]
    missing_fields = [
        field
        for field in required_fields
        if field not in request_data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    config_data = request_data.get("config") or {}
    artifacts_data = request_data.get("artifacts") or {}

    required_artifact_fields = [
        "artifact_dir",
        "screenshot_path",
        "html_snapshot_path",
        "network_log_path",
        "trace_path",
    ]
    missing_artifact_fields = [
        field
        for field in required_artifact_fields
        if field not in artifacts_data
    ]

    if missing_artifact_fields:
        console.print(
            "[bold red]Playwright request artifacts missing required fields:[/bold red] "
            + ", ".join(missing_artifact_fields)
        )
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=bool(config_data.get("allow_live_execution", False)),
        use_real_adapter=bool(config_data.get("use_real_adapter", False)),
    )

    artifacts = PlaywrightArtifactPlan(
        artifact_dir=str(artifacts_data["artifact_dir"]),
        screenshot_path=str(artifacts_data["screenshot_path"]),
        html_snapshot_path=str(artifacts_data["html_snapshot_path"]),
        network_log_path=str(artifacts_data["network_log_path"]),
        trace_path=str(artifacts_data["trace_path"]),
    )

    request = PlaywrightExecutionRequest(
        target_name=str(request_data["target_name"]),
        task_name=str(request_data["task_name"]),
        start_url=str(request_data["start_url"]),
        browser=str(request_data["browser"]),
        config=config,
        artifacts=artifacts,
        planned_actions=list(request_data.get("planned_actions") or []),
    )

    context = build_playwright_adapter_context(request)

    try:
        result = load_browser_capture_result_from_artifacts(
            context,
            notes="Loaded by bugintel load-browser-artifacts.",
        )
    except ValueError as exc:
        console.print(f"[bold red]Browser artifact loading failed:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output = result.execution_output

    table = Table(title="Browser Artifacts Loaded")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Network events", str(output.get("loaded_network_events", 0)))
    table.add_row("Screenshots", str(output.get("loaded_screenshots", 0)))
    table.add_row("HTML snapshots", str(output.get("loaded_html_snapshots", 0)))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")




if __name__ == "__main__":
    app()
