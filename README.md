# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)
[![Latest release](https://img.shields.io/github/v/release/Siddforeal/Blackhole_AI?label=release)](https://github.com/Siddforeal/Blackhole_AI/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Blackhole AI Workbench** is a human-in-the-loop security research workbench for authorized vulnerability research, bug bounty workflows, endpoint intelligence, evidence planning, and report preparation.

It is **not a scanner** and it is **not an auto-exploitation tool**.

Blackhole is built around safe planning, local evidence, explicit human approval, and conservative report-readiness gates.

**Current release:** `v0.69.0`
**Project status:** active research prototype

---

## Why Blackhole Exists

Security research produces fragmented material: endpoints, HAR files, screenshots, API responses, notes, hypotheses, validation steps, evidence bundles, and report-readiness decisions.

Blackhole turns that material into a structured workflow:

```text
inputs
→ endpoint intelligence
→ research state / case memory
→ deterministic planning
→ provider-gated review
→ evidence/action review gates
→ report-readiness review
→ human-written report support
```

The goal is to help a researcher think clearly, prioritize high-signal paths, preserve evidence, avoid overclaims, and produce stronger human-reviewed reports.

---

## Core Principles

- Authorized research only
- Local-first by default
- Planning-first, not execution-first
- Human approval before risky actions
- Provider output is untrusted until reviewed
- No automatic vulnerability confirmation
- No automatic report submission
- No target mutation by default
- Evidence before severity or impact claims

---

## Current Safety Model

Blackhole currently does **not** automatically:

- call LLM providers
- execute curl commands
- launch browsers
- run Kali tools
- mutate targets
- bypass authorization
- confirm vulnerabilities
- submit reports

Every provider/tool/browser/execution-oriented workflow is represented as a reviewable plan, gate, packet, or checklist until a human explicitly validates the next step.

---

## Current Workflow Highlights

### Endpoint and Evidence Planning

Blackhole can organize endpoints and evidence into structured research artifacts:

```text
endpoint list
→ orchestration
→ research state
→ endpoint priority
→ attack surface groups
→ validation runbooks
→ evidence requirements
```

### Case Chat and Provider Review Pipeline

Blackhole supports a safety-gated case-chat workflow that treats external or provider-generated text as untrusted planning input:

```text
case-chat-prompt-package
→ case-chat-provider-gate
→ case-chat-provider-dry-run
→ case-chat-provider-result-import
→ case-chat-provider-result-review
→ case-chat-suggestion-action-plan
→ case-chat-action-plan-apply-preview
→ case-chat-action-plan-apply-preview-review
→ case-chat-reviewed-apply-packet
→ case-chat-reviewed-apply-packet-export-bundle
→ case-chat-export-bundle-review-gate
→ case-chat-export-bundle-report-readiness-review
```

### Report Readiness

The current release can review whether a gated export bundle is ready to support a human-written report draft.

It separates report-ready support notes, blockers, missing evidence, unsafe items, artifact problems, overclaim risks, safety blockers, final checklist items, and report guardrails.

It still does **not** generate or submit reports automatically.

---

## Quick Start

```bash
git clone https://github.com/Siddforeal/Blackhole_AI.git
cd Blackhole_AI

python -m venv .venv
source .venv/bin/activate

pip install -e .
blackhole --help
```

The legacy CLI name is also kept for compatibility:

```bash
bugintel --help
```

---

## Minimal Demo

```bash
cat > /tmp/blackhole-endpoints.txt <<'EOF'
/api/accounts/123/users/{id}/permissions
/api/files/{id}/download
/api/status
EOF

blackhole orchestrate /tmp/blackhole-endpoints.txt \
  --target demo \
  --json-output /tmp/orchestration.json

blackhole research-state /tmp/orchestration.json \
  --output-file /tmp/research-state.md \
  --json-output /tmp/research-state.json
```

---

## Example: Report-Readiness Review

```bash
blackhole case-chat-export-bundle-report-readiness-review \
  --review-gate /tmp/export-bundle-review-gate.json \
  --output /tmp/report-readiness.md \
  --json-output /tmp/report-readiness.json
```

This produces a planning-only readiness review. It does not generate a report, submit a report, call providers, execute tools, or confirm a vulnerability.

---

## Documentation

| Document | Purpose |
|---|---|
| [CLI Reference](docs/cli-reference.md) | Commands and examples |
| [Feature Reference](docs/feature-reference.md) | Full feature list |
| [Methodology](docs/methodology.md) | Research workflow and methodology |
| [Safety Model](docs/safety-model.md) | Safety guarantees and boundaries |
| [Architecture](docs/architecture.md) | Internal design |
| [Threat Model](docs/threat_model.md) | Misuse and risk analysis |
| [Limitations](docs/limitations.md) | Current limitations |

---

## Latest Release Line

| Version | Focus |
|---|---|
| `v0.69.0` | Human Report Skeleton Packet |
| `v0.68.0` | Finding Draft Packet Review Gate |
| `v0.67.0` | Report Readiness Finding Draft Packet |
| `v0.66.0` | Export Bundle Report Readiness Review |
| `v0.65.0` | Export Bundle Review Gate |
| `v0.64.0` | Reviewed Apply Packet Export Bundle |
| `v0.63.0` | Case Chat Reviewed Apply Packet |
| `v0.62.0` | Case Chat Apply Preview Reviewer |
| `v0.61.0` | Case Chat Action Plan Apply Preview |
| `v0.60.0` | Case Chat Suggestion Action Plan |
| `v0.59.0` | Provider Suggestion Review Bridge |

---

## Ethical Use

Use Blackhole only on systems you own, local labs, CTFs, written-scope penetration tests, or explicitly authorized bug bounty programs.

Do not use it for unauthorized scanning, exploitation, credential theft, persistence, stealth, denial-of-service activity, destructive testing, or accessing private data.

---

## License

MIT License.
