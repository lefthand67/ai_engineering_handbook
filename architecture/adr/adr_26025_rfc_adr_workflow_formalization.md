
---
title: RFC→ADR Workflow Formalization
date: 2026-02-10
tags:
- governance
- documentation
- workflow
options:
  token_size: 1455
  id: ADR-26025
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-10'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: RFC→ADR Workflow Formalization.
---
# ADR-26025: RFC→ADR Workflow Formalization

## Title

RFC→ADR Workflow Formalization

## Date

2026-02-10

## Status

Accepted

## Context

The ADR lifecycle ({term}`ADR-26016`) defines `proposed` status, and `adr_index.md` partitions these as "Evolutionary Proposals." But the RFC nature of this phase is undocumented — contributors and AI agents don't know that `proposed` ADRs are living design documents collecting discourse before promotion to `accepted`.

In practice, the workflow already functions as an RFC process: proposed ADRs are drafted, discussed via Git PR comments, iterated on through AI consultations (Gemini, Claude), and eventually promoted or rejected. This implicit behavior needs formal codification to:

1. **Prevent document-type proliferation.** Without a clear statement that ADRs serve as RFCs, future contributors may create separate `misc/rfc/` or `architecture/rfc/` directories, fragmenting the knowledge base.
2. **Define promotion criteria.** The transition from `proposed` to `accepted` currently has no checklist — an ADR can be promoted with zero alternatives analyzed and no participants listed.
3. **Clarify AI consultation records.** Raw Gemini/Claude transcripts are voluminous working files. Their relationship to the final ADR needs a defined pattern.

## Decision

Formalize that `status: proposed` ADRs serve as the RFC phase. No new document type is introduced.

1. **RFC = Proposed ADR.** No separate RFC directory or document format. Discourse occurs via Git PR comments and iterative updates to `## Alternatives` and `## Context` sections within the ADR itself.

2. **Promotion Gate** (proposed → accepted). An ADR MAY NOT transition to `accepted` unless:
   - `## Alternatives` contains ≥2 rejected options, each with an empirical rejection reason.
   - `## Participants` is non-empty (at least one named contributor).
   - `## References` contains ≥1 entry.

3. **Stale Proposal Handling.** ADRs remaining `proposed` for >90 days without git-tracked modifications trigger a CI warning. Resolution options: update the ADR, reject it, or add an `active-investigation` tag to suppress the warning.

4. **AI Consultation Records (Fat ADR Pattern).** Raw Gemini/Claude transcripts are working files — they are NOT committed to the repository. All analytical value from consultations is absorbed into the ADR's `## Alternatives` section with thorough treatment: each rejected option gets a full analysis paragraph, not a 2-sentence summary. Share URLs or transcript provenance are ephemeral and not preserved.

5. **RAG Filtering Guidance.** Implementation tasks that consume ADRs via RAG should prioritize `status: accepted` as authoritative. `status: proposed` provides context and ongoing analysis, not binding architectural authority.

## Consequences

### Positive

- **Single document type.** No RFC/ADR fragmentation. The `architecture/adr/` directory remains the sole location for architectural discourse.
- **Quality gate.** Promotion criteria prevent premature acceptance of under-analyzed decisions.
- **AI agent clarity.** Agents can be instructed: "proposed = open for input, accepted = treat as constraint."
- **Stale detection.** CI warnings surface abandoned proposals before they become ghost knowledge.

### Negative / Risks

- **Promotion friction.** The ≥2 alternatives requirement may slow acceptance of obvious decisions. **Mitigation:** The alternatives can include a brief "do nothing" option where appropriate — the intent is to document that alternatives were considered, not to manufacture false choices.
- **Fat ADR verbosity.** Thorough alternative analysis increases ADR length. **Mitigation:** This is intentional. The ADR is the permanent record; verbosity here prevents the need to hunt through external transcripts that no longer exist.

## Alternatives

- **Separate RFC directory** (`architecture/rfc/` or `misc/rfc/`). Rejected. Creates document fragmentation — RFCs that never become ADRs produce "Ghost Knowledge" (documents that exist but aren't referenced by any active decision). Adds a governance layer (RFC numbering, RFC→ADR linking) that must be maintained separately. Violates the single-document-type simplicity that makes the current `architecture/adr/` system work. When an RFC is promoted, its content must be migrated into the ADR anyway, creating double-entry bookkeeping.

- **GitHub Issues as RFCs.** Rejected. Issues are not version-controlled in the filesystem, making them invisible to local RAG pipelines — a direct violation of SVA (Smallest Viable Architecture) principle C3 (all architectural knowledge must be git-tracked and locally queryable). Discussion context becomes trapped in a platform-specific format that cannot be searched by offline LLMs or standard CLI tools. Additionally, issue threads lack the structured sections (Alternatives, Consequences) that make ADRs machine-parseable.

- **Full IETF-style RFC process.** Rejected. The IETF (Internet Engineering Task Force) defines the original RFC (Request for Comments) standard used to govern internet protocols — a multi-phase process with formal review boards, working groups, and public comment periods. Adopting this for a single-maintainer project with AI consultation partners adds process overhead with no proportional benefit. The formal review period alone (typically weeks to months) would stall decisions that can be resolved in a single Gemini/Claude session.

- **Stateful RFC buffer files** (similar to Debian `dch` — the `debchange` tool that appends entries to a changelog buffer before release). Rejected. Maintains a separate "RFC buffer" file that accumulates changes before being rolled into the ADR. Creates "Double-Entry Bookkeeping" — the same information exists in both the buffer and the eventual ADR, with metadata drift risk. Introduces SVA violations: C1 (requires a manual CLI step to "flush" the buffer) and C4 (persistent state-tracking layer that must be synchronized).

## References

- {term}`ADR-26016`: Metadata-Driven Architectural Records Lifecycle
- {term}`ADR-26017`: ADR Format Validation Workflow

## Participants

1. Vadim Rudakov
2. Gemini (AI Thought Partner)
3. Claude (AI Implementation Partner)
