# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml)

Blackhole AI Workbench is a human-in-the-loop security research workbench for authorized vulnerability discovery, endpoint intelligence, response analysis, and structured evidence collection.

Current version: 0.45.0

## Research Goal

This project explores AI-assisted vulnerability discovery and bug intelligence workflows for modern web and API security research.

The long-term goal is to support scope-controlled testing, endpoint mining, task-tree based research workflows, safe Kali command planning, controlled execution, response analysis, evidence storage, secret redaction, and report generation.

## Implemented Features

- Scope Guard for authorized testing boundaries
- CLI commands
- Endpoint miner for JavaScript, logs, HAR-style text, and Burp-style exports
- Safe curl planner
- Controlled curl execution with explicit approval
- HTTP response parser
- Secret and email redactor
- Structured evidence store
- Response diff analyzer
- Research task tree builder
- Passive HTML analysis for links, scripts, forms, and endpoints
- Scope-guarded website page fetcher
- JavaScript source collector
- Website Mode pipeline with endpoint merging and orchestration
- HAR traffic importer for Browser/DevTools exports
- HAR-to-orchestration workflow for captured browser traffic
- Android manifest/config analyzer
- Android permissions, components, exported components, deep links, and endpoint extraction
- iOS plist/config analyzer
- iOS bundle ID, URL schemes, associated domains, ATS, hosts, and endpoint extraction
- Browser action planner for Chromium, Chrome, and Firefox workflows
- Browser network capture, screenshot, and HTML extraction planning
- Unit tests
- GitHub Actions CI

## Planned Features

- Playwright browser traffic capture
- HAR and Burp importers
- AI planning layer
- Markdown report generator
- Finding severity scoring
- Duplicate finding detection
- Android APK static analysis
- iOS IPA/plist analysis
- Dashboard UI

## Safety Model

Blackhole AI Workbench is designed for authorized security testing only.

Every network-capable module should pass through the Scope Guard before execution.

The Scope Guard validates allowed domains, allowed schemes, allowed HTTP methods, forbidden path patterns, and human approval requirements.

The run-curl command requires explicit approval before execution.

## Ethical Use

Use this project only against your own systems, local labs, CTF environments, explicitly authorized bug bounty programs, or written-scope penetration testing engagements.

Do not use this project for unauthorized scanning, exploitation, credential attacks, denial-of-service activity, stealth, evasion, or destructive testing.

## License

MIT License.

## Research Planner Workflow

Blackhole includes a deterministic research planner that turns existing browser evidence into structured hypotheses and recommendations.

Example:

    bugintel plan-research /tmp/browser-evidence-sample.json --json-output /tmp/research-plan.json --markdown-output /tmp/research-plan.md

The planner does not call an LLM, does not execute commands, and does not make network requests. It only analyzes existing evidence.

Example output categories include:

    api-authorization
    object-authorization
    sensitive-surface-review
    error-handling
    browser-evidence-review

Use the output as a manual research guide. Confirm every hypothesis with authorized, in-scope testing before treating it as a finding.

### Safe LLM Prompt Package

Blackhole can convert a deterministic research plan into a reviewable LLM prompt package:

    bugintel build-llm-prompt /tmp/research-plan.json --json-output /tmp/llm-prompt.json --markdown-output /tmp/llm-prompt.md

This command does not call an LLM provider, does not read API keys, does not make network requests, and does not execute commands. It only creates a redacted system/user prompt package for human review.

Use this package as an optional bridge to a future LLM provider. Treat any future LLM output as suggestions only, not confirmed findings.

### LLM Prompt Safety Audit

Blackhole can audit a prompt package locally before provider use:

    bugintel audit-llm-prompt /tmp/llm-prompt.json --json-output /tmp/llm-prompt-audit.json --markdown-output /tmp/llm-prompt-audit.md

The audit is fully local. It scans for common sensitive values and risky prompt instructions, then returns `pass`, `review`, or `blocked`.

Current checks include:

    emails
    JWT-like tokens
    bearer tokens
    API-key-like assignments
    passwords/secrets/tokens
    AWS access key IDs
    prompt-injection style instructions
    safety-bypass instructions
    credential theft or destructive-action instructions

### Case Timeline Builder

Blackhole can create a planning-only case timeline from local Blackhole artifacts:

    blackhole case-timeline /tmp/blackhole-safe-brain-demo --output-file /tmp/case-timeline.md --json-output /tmp/case-timeline.json

The timeline builder reads known local artifacts such as:

- orchestration JSON
- research-state JSON
- AI brain plan
- brain prompt package
- brain review
- brain decision gate
- human approval packet
- tool request manifest
- tool execution gate
- brain-chat session
- research-state update plan
- research-state apply result

It creates a chronological summary of what happened in the case.

This command is local-only and planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Research State Patch Applier

Blackhole can apply a research-state update plan to a local copy of research-state JSON:

    blackhole research-state-apply /tmp/research-state.json --update-plan /tmp/research-state-update.json --output-file /tmp/research-state.updated.json

It can also write a full apply result JSON:

    blackhole research-state-apply /tmp/research-state.json --update-plan /tmp/research-state-update.json --output-file /tmp/research-state.updated.json --result-json ./research-state-apply-result.json

The applier updates a local copy only.

It can apply planned changes for:

- endpoint triage state
- hypothesis status
- artifact status
- validation notes

This command is local-only and planning-safe. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Research State Update Planner

Blackhole can create a planning-only update plan for research-state JSON after manual validation:

    blackhole research-state-update /tmp/research-state.json --endpoint "/api/accounts/123/users/{id}/permissions" --validation-result supported --note "Validated with controlled accounts." --output-file ./research-state-update.md

It can also write structured JSON:

    blackhole research-state-update /tmp/research-state.json --endpoint "/api/accounts/123/users/{id}/permissions" --validation-result needs-more-evidence --json-output ./research-state-update.json

Supported validation results:

- supported
- rejected
- needs-more-evidence
- deprioritize

The update planner proposes changes for:

- endpoint triage state
- hypothesis status
- artifact status
- validation notes

The command is planning-only. It does not mutate research-state files automatically, call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, or bypass authorization.

### Brain Chat Session Memory

Blackhole can persist local brain-chat turns into a session JSON file:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo --session /tmp/blackhole-chat-session.json
    blackhole brain-chat "status" --state-dir /tmp/blackhole-safe-brain-demo --session /tmp/blackhole-chat-session.json

The session file stores:

- question
- answer
- target name
- focus endpoint
- decision state
- approval status
- execution gate
- execution allowed flag
- timestamp

This is local, deterministic, and planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Deterministic Brain Chat

Blackhole can answer simple local questions from saved brain-state artifacts:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo

It can also write structured JSON:

    blackhole brain-chat "status" --state-dir /tmp/blackhole-safe-brain-demo --json-output ./brain-chat.json

The brain-chat command reads existing planning artifacts such as:

- AI brain plan
- brain decision gate
- human approval packet
- tool execution gate

It can answer planning-only questions like:

- hello
- status
- what should we do next?
- why this endpoint?
- can we execute?

The current implementation is deterministic and local. It does not call an LLM provider.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Tool Execution Gate

Blackhole can create a planning-only execution gate from tool-request-manifest JSON:

    blackhole tool-execution-gate /tmp/tool-request-manifest.json --output-file ./tool-execution-gate.md

It can also write structured JSON:

    blackhole tool-execution-gate /tmp/tool-request-manifest.json --output-file ./tool-execution-gate.md --json-output ./tool-execution-gate.json

The Tool Execution Gate is the final safety checkpoint before any future human-approved execution layer.

It records:

- target name
- focus endpoint
- gate decision
- execution allowed flag
- gate items
- required confirmations
- provider execution status
- execution state

The gate fails closed by default. Execution remains disabled until a future explicit human-approved execution layer exists.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Tool Request Manifest

Blackhole can create a planning-only tool request manifest from brain-approval JSON:

    blackhole tool-request-manifest /tmp/brain-approval.json --output-file ./tool-request-manifest.md

It can also write structured JSON:

    blackhole tool-request-manifest /tmp/brain-approval.json --output-file ./tool-request-manifest.md --json-output ./tool-request-manifest.json

The Tool Request Manifest converts approval requirements into reviewable future tool/action requests.

It records:

- target name
- focus endpoint
- source approval status
- requested tool/action family
- purpose
- human approval requirement
- blocked-by safety gates
- expected artifact
- execution allowed flag

Execution remains disabled. This command does not execute tools.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Human Approval Packet

Blackhole can create a planning-only human approval packet from brain-decision JSON:

    blackhole brain-approval /tmp/brain-decision.json --output-file ./brain-approval.md

It can also write structured JSON:

    blackhole brain-approval /tmp/brain-decision.json --output-file ./brain-approval.md --json-output ./brain-approval.json

The Human Approval Packet turns a brain decision into a human-reviewable approval checklist before any future tool/browser/curl execution is allowed.

It records:

- source decision
- approval status
- approval-required flag
- focus endpoint
- approval items
- human checklist
- reportability status
- provider execution status

The packet is intentionally conservative. It keeps reportability false until manually validated evidence exists.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Brain Decision Gate

Blackhole can create a planning-only decision gate from brain-review JSON:

    blackhole brain-decision /tmp/brain-review.json --output-file ./brain-decision.md

It can also write structured JSON:

    blackhole brain-decision /tmp/brain-review.json --output-file ./brain-decision.md --json-output ./brain-decision.json

The Brain Decision Gate reads a brain review and decides the next safe state:

- blocked
- blocked-pending-scope-and-controls
- ready-for-human-approval
- ready-for-manual-validation
- needs-more-planning

It also records:

- focus endpoint
- decision rationale
- blockers
- required next steps
- reportability status
- provider execution status

The gate is intentionally conservative. It never marks a vulnerability as confirmed or reportable without manually validated evidence.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Brain Review / Reasoning Draft

Blackhole can create a planning-only reasoning review from a brain-prompt JSON package:

    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md

It can also write structured JSON:

    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md --json-output ./brain-review.json

The Brain Review layer is the first deterministic reasoning-output layer after the LLM Brain Prompt Package.

Current safe brain flow:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json
    blackhole research-state /tmp/orchestration.json --json-output /tmp/research-state.json
    blackhole ai-brain /tmp/research-state.json --json-output /tmp/ai-brain-plan.json
    blackhole brain-prompt /tmp/ai-brain-plan.json --json-output /tmp/brain-prompt.json
    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md --json-output ./brain-review.json

Generated brain reviews include:

- recommended focus endpoint
- why the endpoint is high signal
- open hypotheses to review
- evidence artifacts needed
- human approvals required
- safety gates still blocking execution
- next manual validation step
- stop conditions
- research state updates after validation

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### LLM Brain Prompt Package

Blackhole can create a provider-ready, planning-only prompt package from AI brain JSON:

    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md

It can also write structured JSON:

    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md --json-output ./brain-prompt.json

The LLM Brain Prompt Package is the bridge between deterministic AI brain planning and future provider-gated LLM reasoning.

It packages:

- system instructions
- developer safety requirements
- structured user context from the AI brain plan
- assistant task instructions
- focus endpoint
- safety gates
- provider execution status

The generated prompt package is provider-ready, but Blackhole does not call an LLM provider yet.

Current flow:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json
    blackhole research-state /tmp/orchestration.json --json-output /tmp/research-state.json
    blackhole ai-brain /tmp/research-state.json --json-output /tmp/ai-brain-plan.json
    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md --json-output ./brain-prompt.json

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### AI Brain Interface

Blackhole can create a planning-only AI brain plan from research-state JSON:

    blackhole ai-brain /tmp/research-state.json --output-file ./ai-brain-plan.md

It can also write structured JSON:

    blackhole ai-brain /tmp/research-state.json --output-file ./ai-brain-plan.md --json-output ./ai-brain-plan.json

The AI Brain Interface is the first deterministic brain layer for Blackhole.

It reads structured case memory and decides:

- which endpoint to focus on first
- why the endpoint matters
- which hypotheses are open
- which artifacts are required
- which actions require human approval
- which safety gates block execution
- what the next planning action should be

The current AI brain is deterministic and planning-only. It does not call LLM providers yet.

Generated brain plans include:

- focus queue
- endpoint priority
- triage state
- hypotheses
- required artifacts
- next actions
- global actions
- safety gates
- provider execution status

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, use Kali tools, mutate targets, or bypass authorization.

### Research State / Case Memory

Blackhole can create planning-only research state from orchestration JSON:

    blackhole research-state /tmp/orchestration.json --output-file ./research-state.md

It can also write structured JSON:

    blackhole research-state /tmp/orchestration.json --output-file ./research-state.md --json-output ./research-state.json

Research state is the base layer for the future Blackhole AI brain.

It stores:

- target name
- endpoint memory
- endpoint priority
- attack-surface groups
- triage state
- hypotheses
- planned evidence artifacts
- redaction requirements
- approval requirements
- global decisions

Example endpoint states include:

- ready-for-manual-validation
- queued
- watchlist
- deprioritized

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Validation Runbook Builder

Blackhole can create a safe manual validation runbook from orchestration JSON:

    blackhole validation-runbook /tmp/orchestration.json --output-file ./validation-runbook.md

It can also write structured JSON:

    blackhole validation-runbook /tmp/orchestration.json --output-file ./validation-runbook.md --json-output ./validation-runbook.json

The runbook helps answer:

- what should be validated first
- which endpoint requires approval
- what evidence should be collected
- what must be redacted
- when the researcher should stop
- how to make a reportability decision

Generated runbooks include:

- global safety rules
- endpoint priority
- attack-surface groups
- validation phases
- expected evidence artifacts
- redaction requirements
- human approval requirements
- stop conditions

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Report Draft Builder

Blackhole can create a safe report draft skeleton from orchestration JSON:

    blackhole report-draft /tmp/orchestration.json --output-file ./report-draft.md

It can also write structured JSON:

    blackhole report-draft /tmp/orchestration.json --output-file ./report-draft.md --json-output ./report-draft.json

The draft includes sections for:

- Summary
- Scope and Authorization
- Priority Triage
- Attack Surface Grouping
- Evidence Requirements
- Validation Notes
- Impact
- Steps to Reproduce
- Evidence References
- Safety and Redaction Checklist

The report draft is a skeleton only. It must be filled with manually validated evidence before submission.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Evidence Workspace Builder

Blackhole can create a local evidence workspace from orchestration JSON:

    blackhole evidence-workspace /tmp/orchestration.json --output-dir ./case-demo

The workspace builder creates a local folder structure for safe, organized research evidence.

Example output structure:

    case-demo/
    ├── README.md
    ├── manifest.json
    ├── redaction-checklist.md
    ├── report-notes.md
    └── endpoints/
        └── 001-api-accounts-123-users-id-permissions/
            ├── README.md
            ├── checklist.md
            ├── notes.md
            ├── requests/
            ├── responses/
            └── screenshots/

The generated files help organize:

- endpoint evidence summaries
- evidence checklists
- researcher notes
- redacted request samples
- redacted response samples
- approved screenshots
- global redaction checklist
- report notes

This command is local-only and planning-only. It does not send requests, execute shell commands against targets, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Evidence Requirements Planning

Blackhole can plan what evidence is needed to validate and report findings safely:

    blackhole evidence-requirements endpoints.txt --json-output /tmp/evidence-requirements.json

Evidence requirements help the researcher understand what proof artifacts are needed before active testing.

Example requirements include:

- scope-and-authorization-proof
- baseline-request-response-sample
- redaction-checklist
- controlled-account-role-matrix
- authorization-decision-diff
- identifier-source-map
- owned-foreign-random-response-matrix
- safe-test-file-manifest
- file-access-control-evidence
- integration-secret-redaction-proof
- integration-boundary-evidence
- low-signal-deprioritization-note

Blackhole orchestration also includes evidence requirements in JSON and terminal output:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

This helps prioritize not only what to inspect first, but also what proof is needed for safe validation and report writing.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Attack Surface Grouping

Blackhole can group endpoint inventories into planning-only attack-surface buckets:

    blackhole attack-surface endpoints.txt --json-output /tmp/attack-surface.json

Attack-surface groups help organize research around meaningful security areas.

Example groups include:

- identity-access
- tenant-project-boundary
- file-surface
- auth-flow
- billing-money
- integration-webhook
- secret-token-key
- object-reference
- parameter-heavy
- low-signal
- general-api

Blackhole orchestration also includes attack-surface groups in JSON and terminal output:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

This helps the researcher see which endpoint clusters deserve focused review.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Priority-Aware Orchestration

Blackhole orchestration now includes endpoint priority scoring in the generated plan and terminal output.

Example:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

The orchestration output includes:

- task tree expansion
- specialist agent assignments
- endpoint priority scores
- score bands such as critical, high, medium, low, and info
- top scoring signals for each endpoint

This helps prioritize high-value endpoints before any active testing.

Priority-aware orchestration is still planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Endpoint Priority Scoring

Blackhole can score a single endpoint using planning-only security heuristics:

    blackhole endpoint-priority "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-priority.json

Blackhole can also rank endpoint inventories from a text file:

    blackhole prioritize-endpoints endpoints.txt --json-output /tmp/prioritized-endpoints.json

Priority scoring helps focus manual research on endpoints that look more security-sensitive.

Signals include:

- authorization-sensitive routes
- object references
- file upload/download surfaces
- authentication/session flows
- billing/payment/invoice routes
- integrations/webhooks/OAuth callbacks
- token/key/secret routes
- low-signal public/static/status routes

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Endpoint Investigation Profiles

Blackhole can expand a single endpoint into a planning-only investigation profile:

    blackhole endpoint-investigation "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-profile.json

The command classifies the endpoint and creates a reviewable task plan for specialist agents.

Example task categories include:

- baseline and method policy review
- parameter and schema review
- authorization boundary planning
- tenant isolation review
- object reference mutation planning
- file surface safety review
- auth-flow review
- evidence and report checklist

This command does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Disabled LLM Provider Stub

Blackhole includes a disabled-by-default provider stub:

    bugintel run-llm-provider /tmp/llm-prompt.json --json-output /tmp/llm-provider-result.json

The current provider does not call OpenAI, Anthropic, local models, or any network API. It returns a structured disabled result so future provider integration can be added behind explicit opt-in gates.

### UFO Startup Intro

Blackhole includes an optional terminal UFO startup screen:

    bugintel intro

Running `bugintel` with no command also shows the UFO loading screen. Normal commands remain separate and should be used for scripted workflows.

## Browser Evidence Workflow

Blackhole v0.45.0 includes a safe browser automation foundation.

Install optional Playwright support with:

    pip install -e ".[browser]"

Then install browser binaries when you are ready to run real Playwright locally:

    python -m playwright install chromium


Current browser workflow:

1. Plan browser actions with Scope Guard.
2. Review the plan before execution.
3. Save future browser/Playwright capture output as redacted evidence.
4. Generate a Markdown report from the saved evidence.

Example:

    bugintel plan-browser examples/target.example.yaml https://demo.example.com/dashboard --browser chromium

    bugintel save-browser-capture examples/browser_capture_result.example.json

The `save-browser-capture` command stores browser capture output through the evidence model. It redacts sensitive previews and stores hashes for response bodies and HTML snapshots.

After saving evidence, generate a report from the saved JSON path:

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/browser-evidence-report.md

Browser execution itself is still a future step. The current implementation provides planning, capture-result normalization, redacted evidence storage, and report rendering.

### Playwright Execution Preview

The v0.45.0 foundation adds a safe Playwright execution preview command. It does not launch a browser. It validates scope, checks whether the optional Playwright package is available, and writes a JSON preview that can later feed execution/evidence workflows.

Example:

    bugintel preview-playwright examples/target.example.yaml https://demo.example.com/dashboard --browser chromium --json-output reports/playwright-preview.json

The preview keeps live execution disabled by default.

### Playwright Execution Safety Gate

Blackhole now includes a safety-gated `execute_playwright_plan()` skeleton for future live browser execution.

The skeleton does not launch a browser yet. It blocks execution unless:

1. The browser plan was approved by Scope Guard.
2. `allow_live_execution=True` is explicitly set after human approval.
3. The optional Playwright Python package is available.

If any gate fails, execution raises `PlaywrightExecutionSafetyError`.

You can exercise the safety gate from the CLI:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard

By default, this command blocks with a safety message. Passing `--allow-live-execution` only passes the explicit opt-in gate; the command still does not launch a browser until real Playwright execution is implemented.

The command can also write a capture-result handoff JSON when the safety gates pass:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

By default, this still routes through the adapter stub. To opt into the real Playwright adapter route, pass both gates explicitly:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --use-real-adapter --json-output reports/playwright-capture-result.json

Real adapter routing requires:

1. Scope Guard approval.
2. `--allow-live-execution`.
3. `--use-real-adapter`.
4. The optional Playwright Python package to be installed and importable.

A safe local smoke test can be run against a temporary `127.0.0.1` HTTP server. Use a local scope file that only allows `http://127.0.0.1`, then run:

    bugintel execute-playwright-plan /tmp/bugintel-local-scope.yaml http://127.0.0.1:8765/dashboard.html --task-name "local real adapter smoke" --allow-live-execution --use-real-adapter --json-output /tmp/bugintel-real-playwright-success.json

Expected successful local result:

    status: completed
    loaded_network_events: >= 1
    loaded_screenshots: 1
    loaded_html_snapshots: 1

The safe handoff chain is:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

    bugintel save-browser-capture reports/playwright-capture-result.json

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/playwright-browser-report.md

This validates the evidence/report pipeline before live browser execution is implemented.

### Playwright Execution Request Model

Blackhole also has a pre-execution request model for future Playwright jobs.

A Playwright request records the target, task, start URL, browser type, config, planned actions, and artifact paths before execution.

The artifact planner prepares future paths like:

    artifacts/browser/<target>/<task>/screenshot.png
    artifacts/browser/<target>/<task>/page.html
    artifacts/browser/<target>/<task>/network.json
    artifacts/browser/<target>/<task>/trace.zip

Creating this request does not create files and does not launch a browser.

You can create a request JSON from the CLI:

    bugintel build-playwright-request examples/target.example.yaml https://demo.example.com/dashboard --task-name "Capture Dashboard" --json-output reports/playwright-request.json

This creates a reviewable Playwright request before live execution is implemented.

A safe example request is included at:

    examples/playwright_request.example.json

This file is a sample request shape only. It is not browser evidence and does not mean a browser was launched.

You can preview a saved request JSON:

    bugintel preview-playwright-request examples/playwright_request.example.json --json-output reports/playwright-request-preview.json

This reads the Playwright request and generates an execution preview without launching a browser.

You can also pass a saved request through the execution safety gate:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml

This re-checks the saved request against scope, then blocks by default because live execution is disabled.

To route a saved request through the real Playwright adapter, both opt-in flags must be passed:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --use-real-adapter

To test the future handoff path:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --json-output reports/playwright-request-capture-result.json

In the current skeleton, this still does not launch a browser. It only reaches the safe `not_implemented` handoff path when the safety gates pass.

### Browser Artifact Loading

Blackhole can load planned browser artifacts from a saved Playwright request and convert them into a browser capture result JSON.

Expected artifact paths come from the request JSON:

    artifacts/browser/<target>/<task>/network.json
    artifacts/browser/<target>/<task>/page.html
    artifacts/browser/<target>/<task>/screenshot.png

Example:

    bugintel load-browser-artifacts examples/playwright_request.example.json --json-output reports/browser-capture-result.json

Then save the capture result as redacted evidence:

    bugintel save-browser-capture reports/browser-capture-result.json

This command does not launch a browser. It only reads artifact files that already exist.

### Playwright Adapter Context

Blackhole now has an internal Playwright adapter context.

The adapter context carries the request and planned artifact paths toward the browser adapter.

By default it does not create files. It can optionally create only the artifact directory, but it still does not launch a browser, capture network traffic, save screenshots, save HTML, or create traces.

### Playwright Adapter Stub Runner

Blackhole now has a stub runner for the future Playwright adapter.

The adapter stub returns `status: not_implemented` as a browser capture result.

It proves the adapter can hand results into the evidence pipeline shape, but it still does not launch a browser, capture network traffic, save screenshots, save HTML, or create traces.
