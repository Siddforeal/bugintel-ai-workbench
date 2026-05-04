# Blackhole Brain Workflow

Blackhole's brain workflow is a planning-first, human-in-the-loop chain for authorized security research.

It does not execute targets automatically.

## Safe Brain Chain

orchestrate
→ research-state
→ ai-brain
→ brain-prompt
→ brain-review
→ brain-decision
→ brain-approval
→ tool-request-manifest
→ tool-execution-gate
→ brain-chat
→ brain-chat session memory
→ research-state-update
→ research-state-apply
→ case-timeline
→ case-summary

## Purpose

The workflow helps a researcher move from raw endpoints to a structured case:

- organize endpoints
- prioritize high-signal surfaces
- create case memory
- generate hypotheses
- plan evidence
- create reviewable reasoning
- block unsafe execution
- prepare approval packets
- plan future tool requests
- preserve local chat and case history
- update research state after manual validation

## Non-Execution Rule

The brain workflow does not:

- call LLM providers
- execute curl
- launch browsers
- run Kali tools
- mutate targets
- bypass authorization
- confirm vulnerabilities without evidence

## Human Approval

Future execution layers must require:

- confirmed scope
- controlled accounts or assets
- redaction plan
- non-destructive validation
- explicit human approval
- clear stop conditions

## Current State

The current brain is deterministic and local. It can reason from saved case artifacts, but it is not yet a live LLM agent.

Provider-gated LLM reasoning should only be added after safety gates, prompt audits, and approval checks pass.
