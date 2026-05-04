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

## Result Evidence Review Report

Render a local result evidence batch review JSON into a human-readable Markdown report:

    blackhole result-evidence-review-report /tmp/result-evidence-batch-review.json --output-file /tmp/result-evidence-review-report.md

The command can also write a JSON wrapper containing the rendered Markdown:

    blackhole result-evidence-review-report /tmp/result-evidence-batch-review.json --output-file /tmp/result-evidence-review-report.md --json-output /tmp/result-evidence-review-report.json

The report includes:

- summary counts
- supported candidates
- rejected candidates
- needs-more-evidence candidates
- missing expected status count
- endpoint-by-endpoint review items
- suggested result, confidence, source, status comparison, signal count, and rationale
- recommended human review checklist
- local-only and planning-only safety framing

The report renderer does not confirm vulnerabilities automatically. It only turns local review JSON into a readable Markdown artifact for human review.

## Result Evidence Finding Draft

Render a local result evidence batch review JSON into a candidate finding draft:

    blackhole result-evidence-finding-draft /tmp/result-evidence-batch-review.json --output-file /tmp/finding-draft.md

The command can also write a JSON wrapper containing the rendered Markdown:

    blackhole result-evidence-finding-draft /tmp/result-evidence-batch-review.json --output-file /tmp/finding-draft.md --json-output /tmp/finding-draft.json

By default, the draft includes only evidence items whose review suggestion is supported.

To include rejected and needs-more-evidence items as well:

    blackhole result-evidence-finding-draft /tmp/result-evidence-batch-review.json --include-all --output-file /tmp/finding-draft.md

The finding draft includes:

- candidate finding status
- summary counts
- candidate title placeholder
- candidate description section
- affected evidence items
- observed and expected status values
- review suggestion, confidence, signal count, and rationale
- manual validation checklist
- proof-of-concept draft steps
- impact hypothesis placeholder
- limitations and open questions
- local-only and planning-only safety framing

The finding draft does not confirm vulnerabilities automatically. It is a report-writing helper for human review after local evidence triage.
