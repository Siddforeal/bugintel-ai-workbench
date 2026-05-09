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

## Result Evidence Finding Package

Build a local finding package from result evidence batch review JSON:

    blackhole result-evidence-finding-package /tmp/result-evidence-batch-review.json --output-dir /tmp/finding-package

The package contains:

- finding-draft.md
- review-report.md
- submission-checklist.md
- metadata.json
- manifest.json

By default, the package includes only evidence items whose review suggestion is supported.

To include rejected and needs-more-evidence items as well:

    blackhole result-evidence-finding-package /tmp/result-evidence-batch-review.json --include-all --output-dir /tmp/finding-package

The package builder remains local-only and planning-only. It creates review artifacts for human validation and does not confirm vulnerabilities automatically.

## Result Evidence Hypothesis

Generate planning-only security hypotheses from local result evidence batch review JSON:

    blackhole result-evidence-hypothesis /tmp/result-evidence-batch-review.json --output-file /tmp/hypotheses.md --json-output /tmp/hypotheses.json

Generate hypotheses only for supported review items:

    blackhole result-evidence-hypothesis /tmp/result-evidence-batch-review.json --supported-only --json-output /tmp/hypotheses.json

The hypothesis engine produces:

- endpoint-level hypothesis class
- confidence
- evidence strength
- severity hint
- rationale
- supporting signals
- safe next manual tests

Example hypothesis classes include:

- object-or-tenant-authorization-boundary-candidate
- cross-account-or-cross-tenant-access-candidate
- information-disclosure-candidate
- authorization-bypass-candidate
- likely-expected-blocking-or-false-positive
- needs-more-evidence

The hypothesis engine remains local-only and planning-only. It does not send requests, run curl, launch browsers, execute tools, call LLM providers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Validation Plan

Build a planning-only manual validation plan from local result evidence hypotheses:

    blackhole result-evidence-validation-plan /tmp/hypotheses.json --output-file /tmp/validation-plan.md --json-output /tmp/validation-plan.json

Generate plans only for high and medium-high priority hypotheses:

    blackhole result-evidence-validation-plan /tmp/hypotheses.json --high-priority-only --json-output /tmp/validation-plan.json

The validation planner produces:

- endpoint-level manual validation plans
- priority classification
- step-by-step manual checks
- expected evidence for each step
- safety notes for each step
- stop conditions
- report-readiness checks
- local-only and planning-only safety metadata

The validation planner does not run tests automatically. It only converts local hypotheses into a safe manual validation plan for a human researcher.

## Result Evidence Case Summary

Build a case-level intelligence summary from local result evidence validation plan JSON:

    blackhole result-evidence-case-summary /tmp/validation-plan.json --output-file /tmp/case-summary.md --json-output /tmp/case-summary.json

The case summary identifies:

- strongest candidates
- weak or likely false-positive candidates
- priority counts
- readiness counts
- missing evidence
- next actions
- case-level next steps
- local-only and planning-only safety metadata

The case summary does not confirm vulnerabilities automatically. It summarizes local validation plans so a human researcher can decide what to validate next.

## Local Research Chat

Ask a local research question against a result evidence case summary JSON:

    blackhole case-chat /tmp/case-summary.json --question "what should I test next?"

Write the answer as JSON:

    blackhole case-chat /tmp/case-summary.json --question "what is strongest?" --json-output /tmp/case-chat-answer.json

Supported question styles in v1 include:

- what should I test next?
- what is strongest?
- what is weak?
- is this report ready?
- what evidence is missing?
- what should I not claim?
- summarize this case

The local research chat answers only from local case-summary JSON. It is deterministic, local-only, and planning-only. It does not call LLM providers, send requests, execute tools, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Local Research Chat Session Memory

Append local case-chat turns to a deterministic JSON session file:

    blackhole case-chat /tmp/case-summary.json --question "what should I test next?" --session-file /tmp/case-chat-session.json

Ask another question and append it to the same session:

    blackhole case-chat /tmp/case-summary.json --question "what evidence is missing?" --session-file /tmp/case-chat-session.json

The session file stores:

- previous questions
- answers
- detected intents
- cited endpoints
- accumulated next actions
- local-only and planning-only safety metadata

The session memory remains local-only and deterministic. It does not call LLM providers, send requests, execute tools, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Result Evidence Priority Ranking

Rank local case-summary candidates by priority, readiness, evidence strength, severity hints, and missing evidence:

    blackhole result-evidence-priority-ranking /tmp/case-summary.json --output-file /tmp/priority-ranking.md --json-output /tmp/priority-ranking.json

Exclude weak or likely false-positive candidates:

    blackhole result-evidence-priority-ranking /tmp/case-summary.json --exclude-weak --json-output /tmp/priority-ranking.json

The ranking output includes:

- top candidate
- ranked candidate list
- score
- priority
- readiness
- evidence strength
- severity hint
- hypothesis class
- ranking reason
- missing evidence
- next actions
- local-only and planning-only safety metadata

The priority ranking command does not confirm vulnerabilities automatically. It only ranks local case-summary candidates for human review.

## Result Evidence Multi-Agent Review

Build deterministic specialist review plans from a local result evidence priority ranking JSON:

    blackhole result-evidence-multi-agent-review /tmp/priority-ranking.json --output-file /tmp/multi-agent-review.md --json-output /tmp/multi-agent-review.json

Exclude low-priority or likely false-positive candidates:

    blackhole result-evidence-multi-agent-review /tmp/priority-ranking.json --exclude-low-priority --json-output /tmp/multi-agent-review.json

The multi-agent review planner creates specialist review tasks for:

- authz-reviewer
- false-positive-reviewer
- impact-reviewer
- evidence-reviewer
- report-reviewer

Each agent task includes:

- focus
- review questions
- checklist
- risk flags

The multi-agent review planner remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case-to-Report Assistant

Build a planning-only report skeleton from local case intelligence artifacts:

    blackhole case-report-assistant /tmp/case-summary.json --output-file /tmp/report-assistant.md --json-output /tmp/report-assistant.json

Use priority ranking and multi-agent review artifacts for richer output:

    blackhole case-report-assistant /tmp/case-summary.json --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --output-file /tmp/report-assistant.md --json-output /tmp/report-assistant.json

The report assistant produces:

- candidate title options
- primary candidate summary
- affected endpoint candidates
- summary draft
- proof-of-concept skeleton
- evidence checklist
- missing evidence section
- specialist review notes
- next actions
- impact wording guardrails
- final report readiness state

The report assistant remains local-only and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Strong Local Research Chat

Ask a stronger local research question across multiple result evidence artifacts:

    blackhole case-chat-context /tmp/case-summary.json --question "is this ready to report?" --json-output /tmp/strong-chat-answer.json

Use additional local artifacts for richer answers:

    blackhole case-chat-context /tmp/case-summary.json --question "what should the final report focus on?" --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --json-output /tmp/strong-chat-answer.json

The strong local chat can use:

- case summary JSON
- priority ranking JSON
- multi-agent review JSON
- case report assistant JSON
- case chat session JSON

Supported v1 context questions include:

- what should I test next?
- what is strongest?
- what do reviewers think?
- what evidence is missing?
- is this ready to report?
- what should I not claim?
- what should the final report focus on?
- summarize chat memory

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Chat Context Router

Inspect a local result evidence artifact and show what chat/review command should be used next:

    blackhole chat-context-router /tmp/artifact.json --output-file /tmp/route.md --json-output /tmp/route.json

The router identifies:

- artifact kind
- artifact label
- recommended command
- supported question styles
- safe next actions
- local-only and planning-only safety metadata

Supported artifact kinds include:

- result_evidence_case_summary
- result_evidence_priority_ranking
- result_evidence_multi_agent_review_plan
- result_evidence_report_assistant
- result_evidence_case_chat_session

The router is deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Natural Question Expansion

Blackhole expands messy human research questions into deterministic local chat intents.

Examples now understood by case-chat and case-chat-context include:

- what should I do now?
- can I submit this?
- is this reportable?
- what proof is missing?
- what should I avoid saying?
- what do agents think?
- what should final report focus on?
- summarize chat memory

The expansion maps these questions to local intents such as:

- next-tests
- strongest
- weak
- report-ready
- missing-evidence
- do-not-claim
- reviewers
- final-report-focus
- session-summary

This behavior is deterministic, local-only, and planning-only. It does not call LLM providers or confirm vulnerabilities.

## Evidence Snippet Grounding

Answer a local research question and include deterministic grounding snippets from local artifacts:

    blackhole case-chat-grounded /tmp/case-summary.json --question "can I submit this?" --json-output /tmp/grounded-answer.json

Use additional artifacts for richer grounding:

    blackhole case-chat-grounded /tmp/case-summary.json --question "what should the final report focus on?" --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --json-output /tmp/grounded-answer.json

The grounded answer includes:

- answer
- intent
- cited endpoints
- next actions
- grounding snippets
- artifact path
- artifact value
- reason for each snippet
- local-only and planning-only safety metadata

The command remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Multi-Artifact Case Memory

Build a local case memory JSON from multiple result evidence artifacts:

    blackhole case-memory-build --case-summary /tmp/case-summary.json --ranking /tmp/priority-ranking.json --multi-agent-review /tmp/multi-agent-review.json --report-assistant /tmp/report-assistant.json --grounded-answer /tmp/grounded-answer.json --output-file /tmp/case-memory.json

Optionally write Markdown too:

    blackhole case-memory-build --case-summary /tmp/case-summary.json --ranking /tmp/priority-ranking.json --output-file /tmp/case-memory.json --markdown-output /tmp/case-memory.md

The case memory includes:

- artifact inventory
- top endpoint
- cited endpoints
- open next actions
- missing evidence
- strongest candidates
- weak candidates
- local-only and planning-only safety metadata

The case memory builder remains deterministic, local-only, and planning-only. It does not call LLM providers, send requests, run curl, launch browsers, mutate targets, bypass authorization, or confirm vulnerabilities.

## Case Chat Prompt Package

Build a safe, reviewable LLM prompt package from local case-chat artifacts without calling any provider:

    blackhole case-chat-prompt-package --case-memory /tmp/case-memory.json --question "can I submit this?" --output-file /tmp/case-chat-prompt.md --json-output /tmp/case-chat-prompt.json

Use a grounded answer for more context:

    blackhole case-chat-prompt-package --case-memory /tmp/case-memory.json --grounded-answer /tmp/grounded-answer.json --question "what should I do next?" --output-file /tmp/case-chat-prompt.md --json-output /tmp/case-chat-prompt.json

The prompt package includes:

- system prompt
- user prompt
- local artifact JSON
- question
- artifact kinds
- redaction status
- safety notes
- provider_execution=false
- local-only and planning-only safety metadata

This command does not call any LLM provider. It only prepares a local prompt package for human review.

## Case Chat Provider Gate

Check whether a local case-chat prompt package would be allowed to use a future LLM provider:

    blackhole case-chat-provider-gate /tmp/case-chat-prompt.json --json-output /tmp/provider-gate.json

Write a Markdown gate report too:

    blackhole case-chat-provider-gate /tmp/case-chat-prompt.json --output-file /tmp/provider-gate.md --json-output /tmp/provider-gate.json

The provider gate checks:

- prompt package shape
- local prompt safety audit status
- provider name
- explicit provider execution opt-in
- required actions before any future provider execution

The current default provider is disabled. This command does not call any LLM provider. It only returns a local gate decision.

## Case Chat Provider Dry-Run

Run a local dry-run for a case-chat prompt package:

    blackhole case-chat-provider-dry-run /tmp/case-chat-prompt.json --output-file /tmp/provider-dry-run.md --json-output /tmp/provider-dry-run.json

The dry-run performs:

- local prompt safety audit
- local provider gate decision
- disabled provider stub result
- required actions summary

The dry-run always reports provider_execution=false. It does not call any real LLM provider.

The output includes:

- provider name
- prompt audit status
- gate allowed/blocked
- gate reason
- disabled provider status
- disabled provider reason
- required actions
- local-only and planning-only safety metadata

## Case Chat Provider Result Importer

Import manually saved provider output as an untrusted local suggestion:

    blackhole case-chat-provider-result-import --provider-result /tmp/provider-output.txt --prompt-package /tmp/case-chat-prompt.json --output-file /tmp/imported-provider-result.md --json-output /tmp/imported-provider-result.json

The importer records:

- provider output text
- suggested actions extracted from the text
- warning flags for overclaims or unsafe wording
- source prompt package metadata
- untrusted_suggestion=true
- provider_execution=false
- vulnerability_confirmation=false

This command does not call any LLM provider. It only imports text that a human saved separately and marks it as untrusted.

## Case Chat Provider Result Review

Review an imported case-chat provider result against local evidence artifacts:

    blackhole case-chat-provider-result-review --imported-result /tmp/imported-provider-result.json --case-memory /tmp/case-memory.json --grounded-answer /tmp/grounded-answer.json --output-file /tmp/provider-result-review.md --json-output /tmp/provider-result-review.json

The review bridge checks:

- imported provider suggestion status
- suggested actions
- warning flags
- unsupported claims
- missing evidence
- overlap with local next actions
- local evidence support

The output includes:

- recommendation
- reviewed actions
- warning flags
- unsupported claims
- missing evidence
- untrusted_suggestion=true
- provider_execution=false
- vulnerability_confirmation=false

This command does not call any LLM provider. It only reviews imported local text against local evidence artifacts.

## case-chat-suggestion-action-plan

Build a safe manual action plan from a reviewed provider suggestion.

Example:

    blackhole case-chat-suggestion-action-plan \
      --provider-review /tmp/provider-review.json \
      --case-memory /tmp/case-memory.json \
      --output /tmp/suggestion-action-plan.md \
      --json-output /tmp/suggestion-action-plan.json

The command reads a local provider review artifact and produces a planning-only action plan. It separates:

- approved manual planning actions
- actions that need more local evidence
- rejected or unsafe actions
- missing evidence
- report guardrails
- safety metadata

Safety properties:

- no provider execution
- no LLM provider calls
- no browser execution
- no curl or Kali execution
- no automatic vulnerability confirmation

## case-chat-action-plan-apply-preview

Preview safe local case memory and research state updates from a suggestion action plan.

Example:

    blackhole case-chat-action-plan-apply-preview \
      --action-plan /tmp/suggestion-action-plan.json \
      --case-memory /tmp/case-memory.json \
      --output /tmp/apply-preview.md \
      --json-output /tmp/apply-preview.json

The command reads a local action plan artifact and produces a planning-only apply preview. It separates:

- case memory update previews
- research state update previews
- blocked updates
- missing evidence
- report guardrails
- safety metadata

Safety properties:

- no state mutation
- no case memory write
- no research state write
- no provider execution
- no LLM provider calls
- no browser execution
- no curl or Kali execution
- no automatic vulnerability confirmation

## case-chat-action-plan-apply-preview-review

Review a case-chat action plan apply preview before any future state-write command exists.

Example:

    blackhole case-chat-action-plan-apply-preview-review \
      --apply-preview /tmp/apply-preview.json \
      --case-memory /tmp/case-memory.json \
      --output /tmp/apply-preview-review.md \
      --json-output /tmp/apply-preview-review.json

The command reads a local apply preview artifact and produces a planning-only review. It flags:

- duplicate update candidates
- blocked actions
- missing evidence
- unsafe or rejected update risks
- report overclaim risks
- safe planning notes
- report guardrails
- safety metadata

Safety properties:

- no state mutation
- no case memory write
- no research state write
- no provider execution
- no LLM provider calls
- no browser execution
- no curl or Kali execution
- no automatic vulnerability confirmation

## case-chat-reviewed-apply-packet

Build a final human approval packet from an apply-preview review.

Example:

    blackhole case-chat-reviewed-apply-packet \
      --apply-preview-review /tmp/apply-preview-review.json \
      --case-memory /tmp/case-memory.json \
      --output /tmp/reviewed-apply-packet.md \
      --json-output /tmp/reviewed-apply-packet.json

The command reads a local apply-preview review artifact and produces a planning-only human approval packet. It separates:

- approved planning-note updates
- duplicate updates
- blocked updates
- evidence gaps
- unsafe or rejected items
- report overclaim risks
- report guardrails
- human approval checklist
- safety metadata

Safety properties:

- human approval required
- no state mutation
- no case memory write
- no research state write
- no provider execution
- no LLM provider calls
- no browser execution
- no curl or Kali execution
- no automatic vulnerability confirmation

## case-chat-reviewed-apply-packet-export-bundle

Build a local export bundle manifest from a reviewed apply packet.

Example:

    blackhole case-chat-reviewed-apply-packet-export-bundle \
      --reviewed-apply-packet /tmp/reviewed-apply-packet.json \
      --artifact /tmp/reviewed-apply-packet.md \
      --artifact-role packet-markdown \
      --output /tmp/export-bundle.md \
      --json-output /tmp/export-bundle.json

The command reads a reviewed apply packet and produces a planning-only export bundle manifest. It summarizes:

- reviewed apply packet recommendation
- approved planning-note update counts
- duplicate update counts
- blocked update counts
- evidence-gap counts
- unsafe / rejected item counts
- overclaim-risk counts
- included artifact references
- human review checklist
- report guardrails
- safety metadata

Safety properties:

- no state mutation
- no case memory write
- no research state write
- no provider execution
- no LLM provider calls
- no browser execution
- no curl or Kali execution
- no automatic vulnerability confirmation
