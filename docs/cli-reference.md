# Blackhole CLI Reference

Blackhole supports two CLI names:

- blackhole
- bugintel

Both point to the same CLI app.

## Status

This reference is for the current planning-first Blackhole CLI.

Blackhole commands are local-first and human-in-the-loop unless explicitly stated otherwise.

## Core Workflow

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

## Command Groups

- Version and intro
- Endpoint intelligence
- Evidence and reporting
- Brain workflow
- Tool planning
- Case state
- Browser and recon
- Provider and LLM safety

## Safety

Current safe default:

- no LLM provider calls
- no browser execution
- no curl execution without approval
- no Kali tool execution
- no target mutation
- no authorization bypass
- no confirmed vulnerability claims without evidence


## Result Interpretation

Interpret a human-provided validation result summary:

    blackhole interpret-result --endpoint "/api/accounts/123/users/{id}/permissions" --observed-status 200 --expected-status 403 --note "Observed foreign account private data and permission bypass." --json-output /tmp/result-interpretation.json

Suggested results:

- supported
- rejected
- needs-more-evidence

The interpreter does not confirm vulnerabilities automatically. It only suggests a planning category for human review.


## Result Evidence Importer

Normalize a local result evidence JSON file:

    blackhole import-result-evidence /tmp/evidence.json --json-output /tmp/normalized-result.json

Example input:

    {
      "endpoint": "/api/accounts/123/users/{id}/permissions",
      "observed_status": 200,
      "expected_status": 403,
      "note": "Observed foreign account private data and permission bypass."
    }

The importer normalizes fields for use with interpret-result and result-flow.

## Result Evidence Batch Importer

Normalize a directory of local result evidence JSON files:

    blackhole import-result-evidence-batch /tmp/evidence-folder --json-output /tmp/result-evidence-batch.json

The batch importer reads matching local JSON files, normalizes each evidence object, and writes one planning-only batch result.

Useful options:

- --pattern "*.json"
- --source manual-json-batch
- --json-output /tmp/result-evidence-batch.json

The batch importer remains local-only and planning-only. It does not send requests, run curl, launch browsers, execute tools, call LLM providers, mutate targets, or confirm vulnerabilities.

## Result Evidence Batch Review

Review a normalized local result evidence batch:

    blackhole review-result-evidence-batch /tmp/result-evidence-batch.json --json-output /tmp/result-evidence-batch-review.json

The review command summarizes local batch evidence into planning-only categories:

- supported
- rejected
- needs-more-evidence

The review output includes:

- total evidence count
- endpoint list
- supported count
- rejected count
- needs-more-evidence count
- missing expected status count
- per-item suggested result and confidence
- local-only safety metadata

The batch review command does not confirm vulnerabilities automatically. It only helps the researcher triage saved evidence before deeper manual review.
