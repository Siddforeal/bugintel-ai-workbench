# Blackhole Safety Model

Blackhole AI Workbench is designed for authorized security research only.

The project is planning-first, local-first, and human-in-the-loop.

## Core Principles

- Confirm program scope before active validation.
- Use controlled accounts, tenants, projects, objects, and files.
- Prefer synthetic test data.
- Redact cookies, tokens, API keys, emails, IDs, screenshots, and private data.
- Keep findings unconfirmed until manually validated evidence exists.
- Keep provider execution disabled unless explicitly enabled through future safety gates.
- Keep tool execution disabled unless explicitly approved through future execution gates.

## Current Non-Execution Guarantees

Current Blackhole brain and planning commands do not:

- call LLM providers
- send target requests
- execute shell commands
- launch browsers
- use Kali tools
- mutate targets
- bypass authorization
- execute tools automatically

## Safe Brain Chain

The safe brain chain is:

    orchestrate
    → research-state
    → ai-brain
    → brain-prompt
    → brain-review
    → brain-decision
    → brain-approval
    → tool-request-manifest
    → tool-execution-gate

Execution remains blocked unless a future explicit human-approved execution layer is implemented.

## Reportability Rule

Blackhole must not mark a finding as confirmed or reportable until manually validated evidence exists.

## Human Approval Requirements

Human approval should be required before:

- collecting approval-gated evidence
- running future browser actions
- running future curl requests
- using future Kali/tool execution
- interacting with sensitive endpoints
- handling files, billing, authentication, integrations, tokens, or cross-tenant boundaries

## Stop Conditions

Stop immediately if:

- the target is out of scope
- authorization is unclear
- controlled accounts are unavailable
- real customer data appears
- live secrets appear
- the action may mutate real data
- the action may trigger payments or irreversible effects
- redaction cannot be done safely
