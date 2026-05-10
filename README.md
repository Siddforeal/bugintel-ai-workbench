# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)

Blackhole AI Workbench is a human-in-the-loop AI security research workbench for authorized vulnerability discovery, bug bounty research, endpoint intelligence, evidence planning, and report preparation.

It is not a scanner.

The long-term goal is to become a world-class AI-assisted security research system that can reason over structured case memory, prioritize attack surfaces, plan validation safely, and help researchers produce high-quality evidence and reports.

Current version: 0.66.0

## Status

Blackhole is an active research prototype.

Current execution model:

- planning-first
- local-first
- human-in-the-loop
- scope-aware
- provider execution disabled by default
- no automatic exploitation
- no automatic browser, curl, or Kali execution

## What Blackhole Does

Blackhole turns endpoint and evidence inputs into a structured research workflow:

    endpoints
    → orchestration
    → research-state
    → ai-brain
    → brain-prompt
    → brain-review
    → brain-decision
    → brain-approval
    → tool-request-manifest
    → tool-execution-gate
    → brain-chat
    → research-state-update
    → research-state-apply
    → case-timeline
    → case-summary

## Current Capabilities

- Endpoint mining and orchestration
- Endpoint investigation profiles
- Endpoint priority scoring
- Attack-surface grouping
- Evidence requirement planning
- Evidence workspace generation
- Validation runbooks
- Report draft generation
- Research state / case memory
- Deterministic AI brain planning
- Provider-ready prompt packages without provider calls
- Brain review and decision gates
- Human approval packets
- Tool request manifests
- Tool execution gates
- Deterministic brain-chat from saved state
- Brain-chat session memory
- Research-state update and patch planning
- Case timeline and case summary generation

## Quick Demo

Create an endpoint list:

    cat > /tmp/blackhole-endpoints.txt <<'EOF2'
    /api/accounts/123/users/{id}/permissions
    /api/files/{id}/download
    /api/status
    EOF2

Run orchestration:

    blackhole orchestrate /tmp/blackhole-endpoints.txt \
      --target demo \
      --json-output /tmp/orchestration.json

Build research state:

    blackhole research-state /tmp/orchestration.json \
      --output-file /tmp/research-state.md \
      --json-output /tmp/research-state.json

Generate an AI brain plan:

    blackhole ai-brain /tmp/research-state.json \
      --output-file /tmp/ai-brain.md \
      --json-output /tmp/ai-brain.json

Ask the local deterministic brain:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo

## Safety Model

Blackhole is designed for authorized security research only.

It does not currently:

- call LLM providers by default
- execute curl automatically
- launch browsers automatically
- run Kali tools automatically
- mutate real targets automatically
- bypass authorization
- confirm vulnerabilities without evidence

Every future execution layer should require explicit human approval, confirmed scope, controlled assets, redaction, and non-destructive validation.

## Documentation

Detailed documentation lives in `docs/`.

- [CLI Reference](docs/cli-reference.md)
- [Safety Model](docs/safety-model.md)
- [Architecture](docs/architecture.md)
- [Methodology](docs/methodology.md)
- [Threat Model](docs/threat_model.md)
- [Limitations](docs/limitations.md)
- [Full Feature Reference](docs/feature-reference.md)

## CLI Compatibility

Both CLI names are supported:

    blackhole version
    bugintel version

## Ethical Use

Use Blackhole only for systems you own or are explicitly authorized to test.

Do not use it for unauthorized exploitation, credential theft, persistence, destructive testing, or accessing private data.

## License

MIT License.

## v0.60.0 - Case Chat Suggestion Action Plan

Blackhole can now convert a reviewed provider suggestion into a safe, local-only manual action plan.

The workflow is:

1. Build a case-chat prompt package.
2. Gate and dry-run provider use.
3. Import manually saved provider output as an untrusted suggestion.
4. Review the suggestion against local evidence.
5. Convert the reviewed suggestion into a manual action plan.

The new `case-chat-suggestion-action-plan` command separates approved planning actions, actions needing more local evidence, rejected or unsafe actions, missing evidence, report guardrails, and safety metadata.

This remains local-only and safety-gated. Blackhole does not execute provider suggestions, does not call LLM providers, does not run tools, and does not confirm vulnerabilities automatically.

## v0.61.0 - Case Chat Action Plan Apply Preview

Blackhole can now turn a reviewed provider suggestion action plan into a safe local apply preview.

The new `case-chat-action-plan-apply-preview` command reads the v0.60.0 suggestion action plan JSON and previews what could later be added to local case memory or research state.

The preview separates:

- case memory update candidates
- research state update candidates
- blocked updates
- missing evidence
- report guardrails
- safety metadata

This is preview-only. It does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.

## v0.62.0 - Case Chat Apply Preview Reviewer

Blackhole can now review a case-chat action plan apply preview before any future state-write command exists.

The new `case-chat-action-plan-apply-preview-review` command reads a v0.61.0 apply preview JSON and checks whether the preview is safe to keep as a planning note.

The review flags:

- duplicate update candidates
- blocked actions
- missing evidence
- unsafe or rejected update risks
- report overclaim risks
- safe planning notes
- report guardrails
- safety metadata

This is still review-only and local-only. It does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.

## v0.63.0 - Case Chat Reviewed Apply Packet

Blackhole can now convert an apply-preview review into a final human approval packet.

The new `case-chat-reviewed-apply-packet` command reads a v0.62.0 apply-preview review JSON and creates a planning-only packet for human approval.

The packet separates:

- approved planning-note updates
- duplicate updates
- blocked updates
- evidence gaps
- unsafe or rejected items
- report overclaim risks
- report guardrails
- human approval checklist
- safety metadata

This remains non-mutating and local-only. It does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.

## v0.64.0 - Reviewed Apply Packet Export Bundle

Blackhole can now build a local export bundle manifest from a reviewed apply packet.

The new `case-chat-reviewed-apply-packet-export-bundle` command reads a v0.63.0 reviewed apply packet JSON and produces a planning-only bundle summary for human review.

The bundle includes:

- reviewed apply packet summary
- bundle manifest
- included artifact references
- approved / blocked / evidence-gap counts
- unsafe and overclaim counts
- human review checklist
- report guardrails
- safety metadata

This remains local-only and non-mutating. It does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.

## v0.65.0 - Export Bundle Review Gate

Blackhole can now review a local export bundle before it is used in a report or future workflow.

The new `case-chat-export-bundle-review-gate` command reads a v0.64.0 reviewed apply packet export bundle JSON and checks whether it is safe only as a review package.

The review gate flags:

- missing artifact files
- artifact hash or size problems
- duplicate artifact references
- unsafe or rejected item counts
- blocked update counts
- evidence-gap counts
- report overclaim counts
- safety metadata problems
- approved review notes
- human review checklist
- report guardrails

This remains local-only and non-mutating. It does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.

## v0.66.0 - Export Bundle Report Readiness Review

Blackhole can now review an export bundle review gate and decide whether it is ready to support a human-written report draft.

The new `case-chat-export-bundle-report-readiness-review` command reads a v0.65.0 export bundle review gate JSON and separates report-supporting material from blockers.

The review separates:

- report-ready support notes
- report blockers
- missing evidence
- unsafe or rejected items
- artifact problems
- report overclaim risks
- safety blockers
- final report-readiness checklist
- report guardrails
- safety metadata

This remains local-only and non-mutating. It does not generate reports, does not submit reports, does not write case memory, does not write research state, does not execute tools, does not call LLM providers, and does not confirm vulnerabilities automatically.
