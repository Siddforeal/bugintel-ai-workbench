# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)

Blackhole AI Workbench is a human-in-the-loop AI security research workbench for authorized vulnerability discovery, bug bounty research, endpoint intelligence, evidence planning, and report preparation.

It is not a scanner.

The long-term goal is to become a world-class AI-assisted security research system that can reason over structured case memory, prioritize attack surfaces, plan validation safely, and help researchers produce high-quality evidence and reports.

Current version: 0.46.0

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
