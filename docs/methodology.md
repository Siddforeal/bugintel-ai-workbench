# Methodology

Blackhole AI Workbench follows a human-in-the-loop methodology for authorized vulnerability research.

## Workflow

1. Define target scope.
2. Mine endpoints from passive inputs such as JavaScript, HTML, HAR, logs, and Burp exports.
3. Build a task tree from discovered attack surfaces.
4. Plan safe commands through Scope Guard.
5. Execute only explicitly approved actions.
6. Parse HTTP responses.
7. Redact sensitive data.
8. Save structured evidence.
9. Compare responses for interesting security signals.
10. Generate research notes and report material.

## Browser Evidence Workflow

Browser automation should follow the same safety pattern as command execution:

1. Validate the browser start URL through Scope Guard.
2. Build a reviewable browser action plan.
3. Require human approval before execution.
4. Capture browser-observed network events.
5. Save screenshot metadata and artifact references.
6. Save redacted HTML snapshot previews and hashes.
7. Save execution output previews from future Playwright runs.
8. Normalize browser execution output into a Browser Capture Result.
9. Save browser capture output with `save-browser-capture`.
10. Store evidence as redacted JSON for later reporting and validation.

Browser evidence should avoid saving raw secrets, raw tokens, raw private HTML, or raw sensitive response bodies by default. Instead, it should preserve enough metadata, previews, and hashes to support reproducible analysis.

## Current MVP Capabilities

- Scope validation
- Endpoint mining
- Task-tree generation
- Safe curl planning
- Controlled curl execution
- HTTP response parsing
- Evidence storage
- Browser evidence storage
- Secret redaction
- Response-diff analysis

## Browser Evidence Command Workflow

The browser evidence workflow can be exercised with the safe example capture result:

    bugintel plan-browser examples/target.example.yaml https://demo.example.com/dashboard --browser chromium

    bugintel save-browser-capture examples/browser_capture_result.example.json

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/browser-evidence-report.md

The example capture result represents the output shape expected from a future Playwright/browser execution adapter. It should be treated as a handoff file, not as proof that live browser automation has executed.

## Deterministic Research Planner

The research planner converts existing browser evidence into structured research hypotheses and recommendations:

    bugintel plan-research browser-evidence.json --json-output research-plan.json --markdown-output research-plan.md

The planner is intentionally offline and deterministic. It does not call an LLM, execute shell commands, launch a browser, or send network requests.

Current hypothesis categories include:

1. API authorization review.
2. Object-level authorization review.
3. Sensitive-surface review.
4. Error-handling review.
5. Browser artifact review.

Planner output should be treated as a manual review guide, not as a confirmed vulnerability. Each recommendation must still be validated using authorized test accounts, Scope Guard, and read-only checks before any report is prepared.

### Safe LLM Prompt Packaging

A deterministic research plan can be converted into a reviewable prompt package:

    bugintel build-llm-prompt research-plan.json --json-output llm-prompt.json --markdown-output llm-prompt.md

This packaging step is intentionally offline. It does not call OpenAI, Anthropic, local models, or any other LLM provider. It does not read API keys, send network requests, execute shell commands, or run browser actions.

The prompt package includes:

1. A system prompt with authorization and safety rules.
2. A user prompt containing the deterministic research plan.
3. Safety notes for human review.
4. Basic redaction for common sensitive patterns such as emails, JWTs, API-key-like values, passwords, and AWS access key IDs.

The package is a bridge for future optional provider integration. It should be reviewed before any model receives it.

### LLM Prompt Safety Audit

Prompt packages should be audited locally before any future provider receives them:

    bugintel audit-llm-prompt llm-prompt.json --json-output llm-prompt-audit.json --markdown-output llm-prompt-audit.md

The audit does not call an LLM provider, read API keys, send network requests, or execute commands. It inspects the prompt package text and produces a local safety report.

Audit statuses:

1. `pass`: no local findings detected.
2. `review`: medium-severity findings detected.
3. `blocked`: high-severity findings detected.

Current checks include sensitive values such as emails, JWT-like tokens, bearer tokens, API-key-like assignments, passwords, secrets, generic tokens, and AWS access key IDs. It also flags risky prompt instructions such as prompt-injection language, safety-bypass requests, credential theft instructions, and destructive-action instructions.

A clean audit is only a helper signal. It should not be treated as a formal data-loss guarantee.

### Disabled LLM Provider Stub

The disabled provider stub can consume a prompt package and return a structured disabled result:

    bugintel run-llm-provider llm-prompt.json --json-output llm-provider-result.json

This command is intentionally non-operational as a model runner. It does not call any provider, read API keys, send prompts over the network, or execute generated actions. It exists to validate result shape and future integration boundaries.

### UFO Startup Intro

The terminal intro can be shown with:

    bugintel intro

Running `bugintel` with no command shows the UFO startup screen. This is a human-facing UX layer only and should not be used as part of machine-readable workflows.

## Playwright Preview Workflow

The Playwright preview workflow is part of the v0.59.0 path toward live browser execution:

    bugintel preview-playwright examples/target.example.yaml https://demo.example.com/dashboard --browser chromium --json-output reports/playwright-preview.json

This command:

1. Loads the authorized target scope.
2. Builds a browser plan through Scope Guard.
3. Checks whether the optional Playwright Python package is importable.
4. Produces a safe execution preview JSON.
5. Does not launch a browser.
6. Does not install Playwright.
7. Does not download browser binaries.
8. Keeps live execution disabled by default.

## Playwright Execution Safety Gate

The safety-gated Playwright execution skeleton defines the future adapter boundary:

    execute_playwright_plan(plan, task_name, config)

The function currently does not launch a browser. It exists to enforce the required safety checks before live browser execution is implemented.

It blocks execution when:

1. The browser plan is out of scope or otherwise blocked.
2. `allow_live_execution` is false.
3. The optional Playwright package is missing.

When blocked, it raises `PlaywrightExecutionSafetyError`. Future live execution should be implemented behind this same gate, not beside it.

The CLI safety-gate command is:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard

Expected default behavior is refusal, because `allow_live_execution` is false unless explicitly requested.

Real adapter routing is also opt-in. The real Playwright adapter path requires both:

1. `--allow-live-execution`
2. `--use-real-adapter`

Without `--use-real-adapter`, the safety-gated execution path continues to use the adapter stub.

For local validation, prefer a temporary `127.0.0.1` HTTP server and a scope file that only allows that local host. A successful real-adapter smoke test should produce:

1. `status: completed`
2. At least one browser-observed network event.
3. One screenshot artifact.
4. One HTML snapshot artifact.
5. A capture-result JSON that can be passed into `save-browser-capture`.

When the handoff path writes a capture-result JSON, it remains compatible with the browser evidence pipeline.

The full safe handoff chain is:

1. `execute-playwright-plan --json-output` creates a future capture-result JSON.
2. `save-browser-capture` stores that JSON as redacted browser evidence.
3. `generate-report` renders the browser evidence into Markdown.
4. The report includes Playwright execution-output fields such as runner, status, and reason.
5. The current skeleton still does not launch a browser.

## Playwright Execution Request Model

Before live browser execution is implemented, Blackhole builds a reviewable execution request.

The request contains:

1. Target name.
2. Task name.
3. Start URL.
4. Browser label.
5. Execution config.
6. Planned browser actions.
7. Planned artifact paths for screenshot, HTML, network log, and trace output.

This request is the future adapter input. It is safe because building it does not create files, does not install Playwright, and does not launch a browser.

The CLI command is:

    bugintel build-playwright-request examples/target.example.yaml https://demo.example.com/dashboard --task-name "Capture Dashboard" --json-output reports/playwright-request.json

Use this command when you want to review the future browser job before attempting any execution workflow.

A safe example request lives at:

    examples/playwright_request.example.json

Treat this example as a request format reference, not as evidence of browser execution.

To preview a saved request:

    bugintel preview-playwright-request examples/playwright_request.example.json --json-output reports/playwright-request-preview.json

This command is useful when the request has already been created and you want to review the execution preview without reloading the original scope file.

To execute a saved request through the safety gate:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml

This command intentionally requires the scope file again. Saved request JSON can be edited, so Blackhole re-validates the start URL before applying the execution safety gate.

Default behavior is refusal because `allow_live_execution` is false. Passing only `--allow-live-execution` keeps the stub route by default.

To route a saved request through the real adapter, use:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --use-real-adapter

## Browser Artifact Loading

The artifact-loading command converts existing planned artifact files into a browser capture result:

    bugintel load-browser-artifacts examples/playwright_request.example.json --json-output reports/browser-capture-result.json

It reads the artifact paths from the saved request JSON. Supported inputs are:

1. `network.json` for browser-observed network events.
2. `page.html` for the HTML snapshot.
3. `screenshot.png` for screenshot metadata and SHA-256 hashing.

The output is compatible with the browser evidence workflow:

    bugintel save-browser-capture reports/browser-capture-result.json

This command does not execute Playwright or launch a browser.

## Playwright Adapter Context

The adapter context is the internal package that will later be handed to the real Playwright engine.

It contains:

1. The Playwright execution request.
2. Planned artifact paths.
3. Whether the artifact directory was created.
4. Safety notes confirming no browser launch or capture happened.
5. A flag showing browser launch is not implemented yet.

Creating the context is safe. It does not launch a browser. Optional directory creation creates only the planned artifact folder, not screenshots, HTML, network logs, or traces.

## Playwright Adapter Stub Runner

The adapter stub runner is the placeholder for the future real Playwright engine.

Current behavior:

1. Accepts a Playwright adapter context.
2. Returns a browser capture result.
3. Sets execution status to `not_implemented`.
4. Preserves artifact path metadata.
5. Confirms no browser launch is implemented.
6. Produces no network events, screenshots, HTML snapshots, or traces.

This lets Blackhole test the future adapter-to-evidence handoff before real browser execution is added.

## Endpoint Investigation Profiles

Blackhole can turn one discovered endpoint into a planning-only investigation profile.

Example:

    blackhole endpoint-investigation "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-profile.json

The profile is designed to help the future orchestrator and specialist agents decide what to inspect next.

The generated plan may include:

- method policy review
- parameter and schema review
- error and oracle review
- authorization boundary planning
- tenant isolation review
- object reference mutation planning
- identifier source mapping
- file surface safety review
- session/auth-flow review
- evidence and report checklist

The output is a reviewable plan only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Endpoint Priority Scoring

Blackhole can score and rank endpoints before active testing.

Single endpoint example:

    blackhole endpoint-priority "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-priority.json

Endpoint inventory example:

    blackhole prioritize-endpoints endpoints.txt --json-output /tmp/prioritized-endpoints.json

The scoring layer is designed to help the future orchestrator decide which endpoint branches should be investigated first.

Priority signals include:

- authorization-sensitive resources
- object identifiers and object-reference patterns
- file upload/download surfaces
- authentication/session/OAuth/SSO/MFA flows
- billing, invoice, payment, and subscription routes
- integrations, webhooks, OAuth callbacks, and API keys
- write-like workflow names such as create, update, delete, assign, invite, migrate, transfer, grant, and revoke
- low-signal deprioritization for health, status, ping, static, asset, public, robots, and sitemap routes

The output is a reviewable plan only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Priority-Aware Orchestration

When Blackhole creates an orchestration plan, it now attaches endpoint priority scoring to the plan and displays endpoint priorities in CLI output.

Example:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

The output helps the researcher decide which endpoint branches deserve attention first.

A typical priority table ranks endpoints such as:

- critical: account, user, permission, token, secret, billing, or object-reference routes
- high: file download/upload, project boundary, integration, webhook, export, or auth-flow routes
- info: status, health, ping, public, static, or asset routes

The orchestration JSON includes endpoint priority metadata so future specialist agents can consume it without re-scoring.

This remains a planning artifact only. Active testing still requires Scope Guard, explicit approval, and controlled authorized targets.

## Attack Surface Grouping

Blackhole can group endpoints into attack-surface buckets before active testing.

Example:

    blackhole attack-surface endpoints.txt --json-output /tmp/attack-surface.json

The grouping layer is designed to help the future orchestrator and specialist agents reason about related endpoints together.

Groups include:

- identity-access: accounts, users, members, teams, roles, permissions, and access-management surfaces
- tenant-project-boundary: projects, tenants, organizations, workspaces, and cross-boundary object references
- file-surface: upload, download, attachments, avatars, images, media, and document endpoints
- auth-flow: login, logout, session, SSO, OAuth, MFA, password reset, and callback routes
- billing-money: billing, invoice, payment, subscription, checkout, and plan-management routes
- integration-webhook: third-party integrations, webhooks, callbacks, and connected-app routes
- secret-token-key: token, secret, key, API-key, and credential-management routes
- object-reference: identifiers, UUIDs, numeric IDs, and IDOR/BAC candidates
- parameter-heavy: search, query, filter, sort, page, and limit behavior
- low-signal: health, status, ping, public, static, asset, robots, and sitemap routes
- general-api: endpoints that do not match a more specific group

When Blackhole creates an orchestration plan, attack-surface groups are attached to the orchestration JSON and printed in terminal output.

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Evidence Requirements Planning

Blackhole can plan report-quality evidence requirements for endpoints before active testing.

Example:

    blackhole evidence-requirements endpoints.txt --json-output /tmp/evidence-requirements.json

The evidence planner translates endpoint priority and attack-surface groups into safe proof requirements.

Typical evidence requirements include:

- scope-and-authorization-proof: record program scope, authorization, target, account ownership, and constraints
- baseline-request-response-sample: collect redacted baseline request/response shape for an owned or allowed path
- redaction-checklist: confirm tokens, cookies, emails, user data, secrets, and identifiers are redacted
- controlled-account-role-matrix: document controlled test identities, roles, membership, and expected boundaries
- authorization-decision-diff: capture allowed vs denied behavior without exposing real user data
- identifier-source-map: map where object identifiers came from, such as UI, JS, HAR, API, or mobile config
- owned-foreign-random-response-matrix: compare owned, foreign controlled, random, and malformed object references
- safe-test-file-manifest: document safe synthetic files and avoid real customer data
- file-access-control-evidence: capture owned vs unauthorized file access behavior safely
- integration-secret-redaction-proof: confirm integration tokens, webhook URLs, OAuth codes, and secrets are redacted
- integration-boundary-evidence: capture integration visibility or boundary behavior without invoking third-party webhooks
- low-signal-deprioritization-note: record why a route is low priority unless later evidence changes that

When Blackhole creates an orchestration plan, evidence requirements are attached to endpoint metadata, exported in JSON, and displayed in CLI output.

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Evidence Workspace Builder

Blackhole can turn orchestration JSON into a local evidence workspace.

Example:

    blackhole evidence-workspace /tmp/orchestration.json --output-dir ./case-demo

The workspace builder creates a structured local case folder with:

- manifest.json: machine-readable workspace manifest
- README.md: target overview and safety notes
- redaction-checklist.md: global redaction checklist
- report-notes.md: draft report notes
- endpoint README files
- endpoint evidence checklists
- endpoint researcher notes
- request, response, and screenshot folders

This helps move Blackhole from a planning engine toward a research operating system.

The workspace is designed for safe evidence handling:

- store only redacted request and response samples
- avoid live secrets, cookies, tokens, API keys, and private customer data
- use controlled accounts and authorized targets only
- review screenshots before sharing
- link evidence to a clear validation decision and impact statement

This remains local-only and planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Report Draft Builder

Blackhole can turn orchestration JSON into a safe vulnerability report draft skeleton.

Example:

    blackhole report-draft /tmp/orchestration.json --output-file ./report-draft.md

The report draft builder uses orchestration data such as:

- endpoint priority scoring
- attack-surface groups
- evidence requirements
- endpoint inventory
- planning-only safety metadata

Generated sections include:

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

The generated draft is not a final vulnerability report. It is a structured starting point for a human researcher to fill with validated observations, redacted evidence, impact, and reproduction steps.

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Validation Runbook Builder

Blackhole can turn orchestration JSON into a manual validation runbook.

Example:

    blackhole validation-runbook /tmp/orchestration.json --output-file ./validation-runbook.md

The validation runbook builder uses orchestration data such as:

- endpoint priority scoring
- attack-surface groups
- evidence requirements
- endpoint-specific safety metadata
- redaction requirements
- human approval requirements

Generated runbooks help the researcher validate safely by defining:

- preflight checks
- baseline collection steps
- authorization boundary checks
- object-reference validation
- file-surface validation
- auth/session validation
- integration/webhook validation
- secret/token handling
- low-signal deprioritization
- reportability decision points
- stop conditions

The generated runbook is not an exploit executor. It is a manual, human-in-the-loop validation plan.

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## Research State / Case Memory

Blackhole can turn orchestration JSON into structured case memory.

Example:

    blackhole research-state /tmp/orchestration.json --output-file ./research-state.md

The research state layer is the foundation for future AI reasoning. It gives the future AI brain a structured representation of the current case instead of forcing it to reason from raw logs.

The research state stores:

- target identity
- endpoint priority
- attack-surface groups
- endpoint triage state
- validation hypotheses
- planned evidence artifacts
- redaction requirements
- human approval requirements
- global decisions
- planning-only execution state

Endpoint triage states include:

- ready-for-manual-validation: high-signal endpoint ready for human-reviewed validation
- queued: medium-priority endpoint worth later review
- watchlist: low-priority endpoint to keep in memory
- deprioritized: low-signal endpoint unless later evidence changes its value

This lets future reasoning modules ask:

- what do we know?
- what is still open?
- what evidence is planned?
- which endpoint should be reviewed first?
- what requires approval?
- where should the researcher stop?

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

## AI Brain Interface

Blackhole can turn research-state JSON into a planning-only AI brain plan.

Example:

    blackhole ai-brain /tmp/research-state.json --output-file ./ai-brain-plan.md

The AI Brain Interface is the bridge between structured case memory and the future LLM-powered reasoning brain.

It reads:

- target name
- endpoint memory
- endpoint priority
- attack-surface groups
- triage state
- hypotheses
- planned evidence artifacts
- global decisions
- safety metadata

It produces:

- focus queue
- next best planning actions
- approval-gated actions
- safety blockers
- artifact planning actions
- state-update actions
- global preflight actions

The current brain is deterministic and provider execution is disabled. This is intentional: Blackhole should first reason safely from structured case memory before live LLM/tool execution is added.

This layer helps future reasoning modules answer:

- which endpoint should be reviewed first?
- why is it high signal?
- which hypothesis should be validated?
- what evidence is required?
- what requires human approval?
- which safety gate blocks execution?
- when should the researcher stop?

This remains planning-only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, use Kali tools, or bypass authorization.

## LLM Brain Prompt Package

Blackhole can turn AI brain JSON into a provider-ready prompt package without calling an LLM provider.

Example:

    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md

The prompt package builder creates four reviewable message blocks:

- system: Blackhole security research planning brain identity and limits
- developer: safety requirements and active safety gates
- user: structured AI brain plan context, focus queue, hypotheses, artifacts, and global actions
- assistant_task: required reasoning output format

The prompt package includes:

- target name
- focus endpoint
- focus queue
- endpoint priority
- triage state
- open hypotheses
- required artifacts
- next actions
- human approval blockers
- active safety gates
- provider execution status

This is the safe bridge toward future LLM reasoning. It lets Blackhole prepare structured, auditable context for an LLM while keeping provider execution disabled.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, or bypass authorization.

## Brain Review / Reasoning Draft

Blackhole can turn a brain-prompt JSON package into a planning-only reasoning review.

Example:

    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md

The Brain Review layer reads the provider-ready prompt package and creates a deterministic reasoning draft without calling any LLM provider.

It extracts and summarizes:

- recommended focus endpoint
- endpoint priority and triage state
- why the endpoint is high signal
- open hypotheses
- required evidence artifacts
- human approval requirements
- safety gates blocking execution
- next manual validation step
- stop conditions
- research state updates after validation

This is the first deterministic reasoning-output layer in the safe brain chain:

    orchestrate
    → research-state
    → ai-brain
    → brain-prompt
    → brain-review

The generated review is not a vulnerability confirmation. It is a safe planning artifact that helps the human researcher decide what to validate next.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, or bypass authorization.

## Brain Decision Gate

Blackhole can turn brain-review JSON into a planning-only decision gate.

Example:

    blackhole brain-decision /tmp/brain-review.json --output-file ./brain-decision.md

The Brain Decision Gate is a conservative safety layer after the reasoning draft.

It answers:

- is this ready for manual validation?
- what blocks validation?
- what requires approval?
- what evidence is still missing?
- is this reportable?

The gate does not confirm vulnerabilities. It keeps findings unconfirmed until manually validated evidence exists.

Decision states include:

- blocked
- blocked-pending-scope-and-controls
- ready-for-human-approval
- ready-for-manual-validation
- needs-more-planning

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, or bypass authorization.

## Human Approval Packet

Blackhole can turn brain-decision JSON into a planning-only human approval packet.

Example:

    blackhole brain-approval /tmp/brain-decision.json --output-file ./brain-approval.md

The Human Approval Packet is the safety bridge before any future human-approved tool loop.

It answers:

- what needs approval?
- what is still blocked?
- what must be confirmed before validation?
- what redaction is required?
- is provider execution disabled?
- is the finding still non-reportable?

The approval packet does not execute validation. It prepares a checklist for the human researcher.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, or bypass authorization.

## Tool Request Manifest

Blackhole can turn brain-approval JSON into a planning-only tool request manifest.

Example:

    blackhole tool-request-manifest /tmp/brain-approval.json --output-file ./tool-request-manifest.md

The Tool Request Manifest is the safety bridge before any future human-approved tool loop.

It answers:

- what tool/action would be requested later?
- why is it needed?
- what approval is required?
- what safety gate blocks it?
- what artifact should it produce?
- is execution allowed?

Execution is always disabled in this layer.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, or bypass authorization.

## Tool Execution Gate

Blackhole can turn tool-request-manifest JSON into a planning-only execution gate.

Example:

    blackhole tool-execution-gate /tmp/tool-request-manifest.json --output-file ./tool-execution-gate.md

The Tool Execution Gate is the final safety checkpoint before any future human-approved execution layer.

It answers:

- is execution allowed?
- why is execution blocked?
- what confirmations are required?
- which tool requests are blocked?
- is provider execution disabled?
- is the workflow still planning-only?

The gate fails closed by default. It keeps execution disabled until a future explicit human-approved execution layer exists.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, bypass authorization, or execute tools.

## Deterministic Brain Chat

Blackhole can answer simple planning-only questions from saved brain-state artifacts.

Example:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo

The brain-chat command reads local artifacts generated by the safe brain chain and returns a deterministic response.

It can summarize:

- target name
- recommended focus endpoint
- endpoint priority
- current decision
- approval status
- execution gate
- execution allowed status
- next safe planning step

This is the first local chat-style interface, but it is not an LLM. It only replies from saved state.

This remains planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, bypass authorization, or execute tools.

## Brain Chat Session Memory

Blackhole can append deterministic brain-chat replies to a local session JSON file.

Example:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo --session /tmp/blackhole-chat-session.json

The session memory helps preserve a local conversation trail while staying planning-only.

It records each turn with:

- user question
- Blackhole answer
- target name
- focus endpoint
- decision state
- approval status
- execution gate
- execution allowed flag
- timestamp

This remains local and deterministic. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, bypass authorization, or execute tools.

## Research State Update Planner

Blackhole can plan safe research-state updates after a manual validation result.

Example:

    blackhole research-state-update /tmp/research-state.json --endpoint "/api/accounts/123/users/{id}/permissions" --validation-result supported --note "Validated with controlled accounts." --output-file ./research-state-update.md

The update planner does not apply changes automatically. It produces a reviewable plan that a human can inspect first.

Validation results include:

- supported: move the endpoint toward report-candidate and mark hypotheses supported
- rejected: deprioritize the endpoint and mark hypotheses/artifacts rejected
- needs-more-evidence: keep the endpoint open and plan additional evidence
- deprioritize: explicitly move the endpoint out of the active validation queue

This remains planning-only. It does not mutate files, call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, or bypass authorization.

## Research State Patch Applier

Blackhole can apply a reviewed research-state update plan to a local copy of research-state JSON.

Example:

    blackhole research-state-apply /tmp/research-state.json --update-plan /tmp/research-state-update.json --output-file /tmp/research-state.updated.json

The patch applier is the next step after the update planner:

    research-state
    → research-state-update
    → research-state-apply

It applies only known safe paths from the update plan:

- endpoint triage state
- hypothesis status
- artifact status
- validation notes

The original research-state file is not mutated automatically. The output is written to a separate file.

This remains local-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, bypass authorization, or execute tools.

## Case Timeline Builder

Blackhole can turn local case artifacts into a planning-only timeline.

Example:

    blackhole case-timeline /tmp/blackhole-safe-brain-demo --output-file /tmp/case-timeline.md --json-output /tmp/case-timeline.json

The timeline builder helps answer:

- what happened in this case?
- what was generated first?
- what decisions were made?
- when did the case become blocked?
- what approval or execution gates were created?
- what state updates were planned or applied?

This remains local-only and planning-only. It does not call LLM providers, run curl, launch browsers, make network requests, execute shell commands, use Kali tools, mutate targets, bypass authorization, or execute tools.


## Result Interpreter

Blackhole can interpret local, human-provided validation result summaries.

Example:

    blackhole interpret-result --endpoint "/api/accounts/123/users/{id}/permissions" --observed-status 200 --expected-status 403 --note "Observed foreign account private data and permission bypass." --json-output /tmp/result-interpretation.json

The interpreter produces a planning-only suggestion:

- supported
- rejected
- needs-more-evidence

This helps connect manual validation output back into the state update loop:

    manual validation result
    → interpret-result
    → research-state-update
    → research-state-apply

The interpreter does not confirm vulnerabilities by itself. It only suggests a next research-state update category for human review.


## Result Evidence Importer

Blackhole can normalize local result evidence JSON before interpretation.

Example:

    blackhole import-result-evidence /tmp/evidence.json --json-output /tmp/normalized-result.json

The importer supports fields such as:

- endpoint or url
- observed_status or status_code
- expected_status
- observed_body or body
- expected_body
- note or notes

The importer is local-only and planning-only. It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities.

This helps the result loop:

    saved result evidence
    → import-result-evidence
    → interpret-result
    → result-flow

## Result Evidence Batch Importer

Blackhole can normalize a folder of saved local result evidence JSON files into one batch object.

Example:

    blackhole import-result-evidence-batch /tmp/evidence-folder --json-output /tmp/result-evidence-batch.json

This is useful when a researcher has multiple manual observations from separate endpoints or test cases and wants to preserve them in a consistent structure before interpretation.

The batch importer supports:

- directory-based evidence import
- glob pattern selection with --pattern
- source labeling with --source
- normalized evidence entries
- local-only safety metadata

This helps the result loop:

    saved result evidence folder
    → import-result-evidence-batch
    → review normalized batch
    → import-result-evidence or interpret-result on selected observations
    → result-flow

The batch importer does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Batch Review

Blackhole can review a normalized local result evidence batch and produce a planning-only triage summary.

Example:

    blackhole review-result-evidence-batch /tmp/result-evidence-batch.json --json-output /tmp/result-evidence-batch-review.json

This is useful after importing a folder of saved observations with import-result-evidence-batch. The review step helps identify which observations look supported, rejected, or still need more evidence.

The batch review output includes:

- supported candidates
- rejected candidates
- needs-more-evidence candidates
- missing expected status count
- endpoint list
- per-item suggested result
- confidence and rationale
- local-only safety metadata

This helps the result loop:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → select observations for manual review
    → interpret-result
    → result-flow

The batch review command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Review Report

Blackhole can render a normalized result evidence batch review into a human-readable Markdown report.

Example:

    blackhole result-evidence-review-report /tmp/result-evidence-batch-review.json --output-file /tmp/result-evidence-review-report.md

This helps turn local saved evidence into a reviewable artifact after batch import and batch review.

The report includes:

- total evidence count
- supported, rejected, and needs-more-evidence counts
- missing expected status count
- endpoint-by-endpoint review items
- suggested result and confidence
- source labels
- observed and expected status values
- signal count
- rationale
- recommended manual review checklist

This helps the result loop:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-review-report
    → manual review
    → interpret-result
    → result-flow

The report command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Finding Draft

Blackhole can render a reviewed local evidence batch into a candidate finding draft for human report writing.

Example:

    blackhole result-evidence-finding-draft /tmp/result-evidence-batch-review.json --output-file /tmp/finding-draft.md

The draft selects supported candidates by default. Use --include-all when the researcher wants the draft to include rejected and needs-more-evidence observations for context.

This helps the result loop:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-review-report
    → result-evidence-finding-draft
    → manual validation
    → final human-written report
    → result-flow

The finding draft includes:

- candidate title placeholder
- candidate description section
- affected evidence items
- manual validation checklist
- proof-of-concept draft steps
- impact hypothesis placeholder
- limitations and open questions
- local-only safety metadata

The finding draft is intentionally cautious. It does not claim that a vulnerability is confirmed. A human researcher must still verify scope, authorization, reproducibility, sensitive data exposure, exploitability, and impact before submitting a report.

The command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Finding Package

Blackhole can build a local finding package from a reviewed evidence batch.

Example:

    blackhole result-evidence-finding-package /tmp/result-evidence-batch-review.json --output-dir /tmp/finding-package

The package includes:

- finding-draft.md
- review-report.md
- submission-checklist.md
- metadata.json
- manifest.json

This helps the result evidence workflow:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → manual validation
    → final human-written report
    → result-flow

The package is designed as a local review bundle, not a submission replacement. A human researcher must still validate scope, authorization, reproducibility, sensitive data exposure, exploitability, and impact before reporting.

The command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Evidence-to-Hypothesis Engine

Blackhole can generate planning-only security hypotheses from reviewed local result evidence.

Example:

    blackhole result-evidence-hypothesis /tmp/result-evidence-batch-review.json --output-file /tmp/hypotheses.md --json-output /tmp/hypotheses.json

This is the first layer that turns saved evidence into structured security reasoning. It does not confirm vulnerabilities; it suggests what the evidence may indicate and what manual tests should come next.

The hypothesis engine can identify candidate classes such as:

- object or tenant authorization boundary candidate
- cross-account or cross-tenant access candidate
- information disclosure candidate
- authorization bypass candidate
- likely expected blocking or false positive
- needs more evidence

This helps the result evidence workflow:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-hypothesis
    → manual validation planner
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The engine also produces safe next manual tests such as own-object baseline, second-account behavior, random-object baseline, role checks, and raw request/response preservation.

The command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Manual Validation Planner

Blackhole can turn local evidence hypotheses into structured manual validation plans.

Example:

    blackhole result-evidence-validation-plan /tmp/hypotheses.json --output-file /tmp/validation-plan.md --json-output /tmp/validation-plan.json

This is the layer after the Evidence-to-Hypothesis Engine. It helps the researcher move from “what might this evidence mean?” to “what safe manual checks should I perform next?”

The planner generates:

- prioritized validation plans
- manual validation steps
- expected evidence per step
- safety notes
- stop conditions
- report-readiness checks

This helps the result evidence workflow:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-hypothesis
    → result-evidence-validation-plan
    → manual evidence capture
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Intelligence Summary

Blackhole can summarize a local validation plan into a case-level intelligence view.

Example:

    blackhole result-evidence-case-summary /tmp/validation-plan.json --output-file /tmp/case-summary.md --json-output /tmp/case-summary.json

This is the layer after the Manual Validation Planner. It helps the researcher understand the whole case at a glance:

- strongest candidates
- weak or rejected candidates
- likely false positives
- missing evidence
- next actions
- report-readiness signals

This helps the result evidence workflow:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-hypothesis
    → result-evidence-validation-plan
    → result-evidence-case-summary
    → manual evidence capture
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The command remains local-only and planning-only. It does not send requests, run curl, launch browsers, use Kali tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Local Research Chat

Blackhole can answer simple local research questions from a result evidence case summary.

Example:

    blackhole case-chat /tmp/case-summary.json --question "what should I test next?"

This is the first deterministic chat layer in the result evidence workflow. It does not use an LLM provider. It reads the local case summary and answers from saved fields such as strongest candidates, weak or rejected candidates, missing evidence, readiness, priority, and next actions.

Supported v1 question styles include:

- what should I test next?
- what is strongest?
- what is weak or false positive?
- is this report ready?
- what evidence is missing?
- what should I not claim?
- summarize this case

This helps the result evidence workflow:

    saved result evidence folder
    → import-result-evidence-batch
    → review-result-evidence-batch
    → result-evidence-hypothesis
    → result-evidence-validation-plan
    → result-evidence-case-summary
    → case-chat
    → manual evidence capture
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Local Research Chat Session Memory

Blackhole can persist deterministic local case-chat turns to a JSON session file.

Example:

    blackhole case-chat /tmp/case-summary.json --question "what should I test next?" --session-file /tmp/case-chat-session.json

The session file accumulates:

- questions
- answers
- intents
- cited endpoints
- next actions
- safety metadata

This helps the result evidence workflow:

    result-evidence-case-summary
    → case-chat
    → local session memory
    → follow-up questions
    → manual evidence capture

The session memory is intentionally local-only and deterministic. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Hypothesis Priority Ranking

Blackhole can rank local case-summary candidates so the researcher can decide what deserves attention first.

Example:

    blackhole result-evidence-priority-ranking /tmp/case-summary.json --output-file /tmp/priority-ranking.md --json-output /tmp/priority-ranking.json

The ranking considers:

- priority
- readiness
- evidence strength
- severity hint
- likely false-positive signals
- missing evidence count

This helps the result evidence workflow:

    result-evidence-case-summary
    → result-evidence-priority-ranking
    → case-chat
    → manual evidence capture
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Multi-Agent Review Planner

Blackhole can build deterministic specialist review plans from a local priority ranking.

Example:

    blackhole result-evidence-multi-agent-review /tmp/priority-ranking.json --output-file /tmp/multi-agent-review.md --json-output /tmp/multi-agent-review.json

The planner creates specialist review tasks for:

- authorization and object-boundary review
- false-positive review
- impact review
- evidence quality review
- report wording and submission readiness review

This helps the result evidence workflow:

    result-evidence-case-summary
    → result-evidence-priority-ranking
    → result-evidence-multi-agent-review
    → case-chat
    → manual evidence capture
    → result-evidence-review-report
    → result-evidence-finding-draft
    → result-evidence-finding-package
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case-to-Report Assistant

Blackhole can turn local case intelligence artifacts into a planning-only report skeleton.

Example:

    blackhole case-report-assistant /tmp/case-summary.json --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --output-file /tmp/report-assistant.md --json-output /tmp/report-assistant.json

This is the bridge from local research intelligence to human report writing. It uses case summary, priority ranking, and multi-agent review artifacts to generate a cautious draft structure.

The assistant includes:

- title candidates
- affected endpoints
- summary draft
- proof-of-concept skeleton
- evidence checklist
- missing evidence
- specialist review notes
- next actions
- impact wording guardrails
- final readiness state

This helps the result evidence workflow:

    result-evidence-case-summary
    → result-evidence-priority-ranking
    → result-evidence-multi-agent-review
    → case-report-assistant
    → manual evidence capture
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Strong Local Research Chat

Blackhole can answer local research questions across multiple result evidence artifacts.

Example:

    blackhole case-chat-context /tmp/case-summary.json --question "is this ready to report?" --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --json-output /tmp/strong-chat-answer.json

This is the stronger version of local research chat. Instead of reading only a case summary, it can combine:

- case summary
- priority ranking
- multi-agent review
- case report assistant output
- case chat session memory

This helps the result evidence workflow:

    result-evidence-case-summary
    → result-evidence-priority-ranking
    → result-evidence-multi-agent-review
    → case-report-assistant
    → case-chat-context
    → manual evidence capture
    → final human-written report

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Chat Context Router

Blackhole can inspect a local result evidence artifact and route the researcher to the best local chat or review command.

Example:

    blackhole chat-context-router /tmp/artifact.json --output-file /tmp/route.md --json-output /tmp/route.json

This helps when the researcher has a saved artifact but is not sure what to ask next. The router explains:

- what the artifact is
- what questions it supports
- what command to use next
- what safe next actions are available

This helps the local research workflow:

    local artifact
    → chat-context-router
    → recommended local command
    → case-chat-context or specialist review
    → manual evidence capture

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Natural Question Expansion

Blackhole can normalize messy researcher questions into local deterministic chat intents.

Examples:

    what should I do now?
    can I submit this?
    what proof is missing here?
    what do agents think?
    what should final report focus on?

These are mapped into known local intents such as next-tests, report-ready, missing-evidence, reviewers, and final-report-focus.

This makes case-chat and case-chat-context more natural without calling an LLM provider. The mapping is rule-based, deterministic, local-only, and planning-only.

The command behavior remains safe: no requests, no curl, no browser, no Kali tools, no mutation, no authorization bypass, and no vulnerability confirmation.

## Evidence Snippet Grounding

Blackhole can ground local chat answers in specific fields from local artifacts.

Example:

    blackhole case-chat-grounded /tmp/case-summary.json --question "can I submit this?" --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --json-output /tmp/grounded-answer.json

This helps make local chat answers more trustworthy by showing what artifact field supported the answer.

Grounding snippets include:

- artifact name
- field path
- field value
- reason the field matters

This helps the local research workflow:

    local artifacts
    → case-chat-grounded
    → grounded answer
    → manual evidence capture
    → final human-written report

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Multi-Artifact Case Memory

Blackhole can combine multiple local result evidence artifacts into a single case memory object.

Example:

    blackhole case-memory-build --case-summary /tmp/case-summary.json --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --grounded-answer /tmp/grounded-answer.json --output-file /tmp/case-memory.json

The memory object captures:

- which artifacts were present
- the top endpoint
- cited endpoints
- open next actions
- missing evidence
- strongest candidates
- weak candidates
- safety metadata

This helps the local research workflow:

    local artifacts
    → case-memory-build
    → local case memory
    → case-chat-context / grounded answers
    → manual evidence capture
    → final human-written report

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Chat Prompt Package

Blackhole can build a safe, reviewable prompt package from local case memory and grounded answers.

Example:

    blackhole case-chat-prompt-package --case-memory /tmp/case-memory.json --grounded-answer /tmp/grounded-answer.json --question "can I submit this?" --output-file /tmp/case-chat-prompt.md --json-output /tmp/case-chat-prompt.json

This is a bridge toward optional future LLM-assisted case chat, but it does not call any provider. It only packages local artifacts into a redacted prompt for human review.

The package includes:

- system prompt
- user prompt
- local artifact JSON
- safety notes
- redaction status
- provider_execution=false

This helps the local research workflow:

    local case memory
    → grounded answer
    → case-chat-prompt-package
    → human review
    → optional future LLM provider gate

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Chat Provider Gate

Blackhole can check a local case-chat prompt package against the provider gate before any future LLM use.

Example:

    blackhole case-chat-provider-gate /tmp/case-chat-prompt.json --output-file /tmp/provider-gate.md --json-output /tmp/provider-gate.json

The gate checks local prompt package safety and provider configuration. It keeps provider execution disabled by default.

This helps the local research workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → human review
    → optional future provider support

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Chat Provider Dry-Run

Blackhole can run a local dry-run for a case-chat prompt package before any future provider integration.

Example:

    blackhole case-chat-provider-dry-run /tmp/case-chat-prompt.json --output-file /tmp/provider-dry-run.md --json-output /tmp/provider-dry-run.json

The dry-run combines:

- prompt safety audit
- provider gate decision
- disabled provider stub result

This gives a full local preview of what would happen before any future LLM provider execution.

The command remains local-only and planning-only. It does not call real LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Chat Provider Result Importer

Blackhole can import manually saved provider output as an untrusted local suggestion.

Example:

    blackhole case-chat-provider-result-import --provider-result /tmp/provider-output.txt --prompt-package /tmp/case-chat-prompt.json --output-file /tmp/imported-provider-result.md --json-output /tmp/imported-provider-result.json

This is useful when a human has used a model outside Blackhole and wants to preserve the output safely inside the case workflow.

The importer:

- marks output as untrusted
- extracts suggested actions
- flags overclaims such as confirmed vulnerability or severity claims
- keeps provider_execution=false
- keeps vulnerability_confirmation=false

This helps the local research workflow:

    external/manual model output
    → case-chat-provider-result-import
    → untrusted local suggestion
    → human verification against local evidence
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Provider Suggestion Review Bridge

Blackhole can review an imported provider suggestion against local case evidence.

Example:

    blackhole case-chat-provider-result-review --imported-result /tmp/imported-provider-result.json --case-memory /tmp/case-memory.json --grounded-answer /tmp/grounded-answer.json --output-file /tmp/provider-result-review.md --json-output /tmp/provider-result-review.json

This is the safety bridge after importing manually saved model output. It helps decide whether the imported suggestion can be used as a planning note, needs more evidence, or contains unsafe/overclaimed parts.

The review bridge:

- treats provider output as untrusted
- reviews suggested actions
- flags overclaims
- compares actions with local next actions
- identifies missing evidence
- keeps provider_execution=false
- keeps vulnerability_confirmation=false

This helps the local research workflow:

    external/manual model output
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → human verification against local evidence
    → final human-written report

The command remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, use Kali tools, mutate targets, bypass authorization, or confirm vulnerabilities.

## Provider Suggestion Action Plans

After importing and reviewing a provider result, Blackhole can turn the reviewed suggestion into a manual action plan.

This step is intentionally conservative. Provider output is treated as untrusted. The action plan only organizes what a human researcher can review next, including approved planning actions, evidence gaps, rejected actions, and report guardrails.

The command does not call a provider, execute tools, send requests, run a browser, or confirm vulnerabilities.

## Action Plan Apply Previews

After building a provider suggestion action plan, Blackhole can preview safe local updates for case memory and research state.

The preview step is deliberately non-mutating. It shows what could be added later, but it does not write any state files. Evidence-needed and rejected actions remain blocked.

This keeps the workflow useful for human-in-the-loop research while preserving the local-only safety model.

## Apply Preview Reviews

After generating an action plan apply preview, Blackhole can review the preview before any state-writing feature exists.

The review checks for duplicate update candidates, blocked actions, evidence gaps, unsafe or rejected items, and report overclaim risks. Safe items remain planning notes only.

This protects the local-only workflow from accidentally treating provider-derived planning text as proof or as an approved state mutation.

## Reviewed Apply Packets

After reviewing an action plan apply preview, Blackhole can create a final human approval packet.

The packet separates approved planning notes from duplicates, blocked items, evidence gaps, unsafe or rejected suggestions, and report overclaim risks. It also includes a human approval checklist.

This protects the workflow from treating provider-derived planning text as proof or as an approved state mutation.

## Reviewed Apply Packet Export Bundles

After creating a reviewed apply packet, Blackhole can build a local export bundle manifest.

The bundle summarizes the packet, references local artifacts, records section counts, preserves human review checklist items, and carries safety metadata. It is designed for review and evidence organization only.

This protects the workflow from treating a packaged bundle as proof, execution approval, or a state mutation.

## Export Bundle Review Gates

After creating a reviewed apply packet export bundle, Blackhole can review the bundle before report or future workflow use.

The gate checks artifact presence, artifact integrity, unsafe counts, blocked counts, evidence-gap counts, overclaim risks, and safety metadata. It classifies the bundle as review-only and keeps human approval required.

This protects the workflow from treating a bundle as report-ready proof or as approval for state mutation.
