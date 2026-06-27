---
id: 26021
title: Content Lifecycle Policy for RAG-Consumed Repositories
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-05.
tags:
- governance
- documentation
- context_management
date: 2026-02-05
options:
  type: adr
  birth: '2026-02-05'
  version: 1.0.0
  token_size: 1281
  status: accepted
  superseded_by: null
---
# ADR-26021: Content Lifecycle Policy for RAG-Consumed Repositories

## Date

2026-02-05

## Status

Accepted

## Context

This repository is consumed by RAG pipelines for weighted decision-making. Two categories of documentation artifacts coexist — **content articles** (tutorials, guides, reference material) and **ADRs** (architectural decision records) — but they have fundamentally different risk profiles when retrieved by AI assistants:

1. **Stale content articles present outdated recommendations as current truth.** A superseded article stating "use GPT-4 as your frontier model" or "use 3B–8B for chats" pollutes retrieval with harmful misinformation. Unlike ADRs, content articles carry no metadata signaling their obsolescence.

2. **Stale ADRs provide valuable negative knowledge.** A superseded ADR retrieved by RAG says "this approach was tried and replaced by ADR-26XXX because [reason]" — this prevents teams from re-exploring dead ends.

The existing ADR infrastructure ({term}`ADR-26016`) already handles the ADR lifecycle via YAML `status` field and `superseded_by` pointer. However, no equivalent policy exists for content articles, leading to an accumulation of outdated material that degrades RAG retrieval quality.

**Triggering incident:** Two early articles (`llm_usage_patterns.md` v0.1.5, `choosing_model_size.md` v0.2.3, both born 2025-10-19) were found to contain outdated model references and oversimplified taxonomies superseded by newer content (Jan 2026 model zoo, `aidx` framework). These articles had no mechanism to signal their obsolescence to RAG consumers.

## Decision

We adopt an **asymmetric lifecycle policy** for content articles vs. ADRs:

### Content Articles

1. **Delete superseded content articles entirely.** Git history serves as the archive. Do not retain stale articles in the working tree under any deprecation marker — their presence in the file system means RAG will retrieve and present them as current guidance.
2. **Before deletion, verify no unique technical value remains.** If the article contains concepts not covered elsewhere, extract and integrate them into the successor article before deletion.
3. **After deletion, sweep all cross-references.** Run `check_broken_links.py` to catch dangling references to deleted files.

### ADRs (No Change)

ADRs continue to follow the immutable lifecycle defined in {term}`ADR-26016`:
- Never delete ADRs from the file system
- Mark superseded ADRs via `status: superseded` and `superseded_by: ADR-XXXXX`
- The `adr_index.md` partitions records into Active Architecture / Evolutionary Proposals / Historical Context for human navigation
- RAG pipelines can filter on `status` to distinguish binding constraints (`accepted`) from historical context (`superseded`)

### RAG Risk Matrix

| Artifact Type | What RAG Retrieves | Risk if Stale | Policy |
|---|---|---|---|
| **Content article** | Recommendations, how-to guidance | **Misleading** — presents outdated advice as current truth | **Delete.** Git history is the archive. |
| **ADR** | Decision rationale ("we chose X because Y") | **Valuable** — prevents re-exploring dead ends | **Never delete.** Use status metadata for RAG filtering. |

## Consequences

### Positive

- **RAG Hygiene:** Eliminates the primary source of stale retrieval — outdated content articles presenting superseded recommendations.
- **Clear Policy:** Engineers know the expected action when content is superseded: delete the article, not deprecate it.
- **Leverages Existing Infrastructure:** ADR lifecycle ({term}`ADR-26016`), YAML frontmatter ({term}`ADR-26018`), and `adr_index.md` already handle the ADR side.

### Negative / Risks

- **Irreversibility Perception:** Deletion feels more permanent than deprecation. **Mitigation:** Git history preserves full content; `git log --all --full-history -- <path>` recovers any deleted file.
- **Judgment Required:** Deciding "is this superseded?" requires understanding the content landscape. **Mitigation:** Require explicit analysis (as in this ADR's triggering incident) before deletion — never delete reactively.

## Alternatives

1. **Deprecation Markers in Content Articles:** Add `status: deprecated` YAML frontmatter to stale articles. Rejected: RAG pipelines would need custom filtering logic for content articles (unlike ADRs, which already have this). More importantly, deprecated articles remain in the file system and get retrieved by keyword-based search regardless of metadata.

2. **Archive Directory:** Move stale articles to an `archive/` directory excluded from RAG indexing. Rejected: Breaks cross-references ({term}`ADR-26016` explicitly rejects this pattern for ADRs; the same reasoning applies to content).

3. **No Policy (Status Quo):** Let stale articles accumulate. Rejected: Directly degrades RAG retrieval quality, the primary consumer of this repository.

## References

- {term}`ADR-26016`: Metadata-Driven Architectural Records Lifecycle
- {term}`ADR-26018`: Universal YAML Frontmatter Adoption for Machine-Readable Documentation

## Participants

1. Vadim Rudakov
2. Claude (AI Engineering Advisor)
