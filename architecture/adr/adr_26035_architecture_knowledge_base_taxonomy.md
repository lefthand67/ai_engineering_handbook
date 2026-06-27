---
id: 26035
title: Architecture Knowledge Base Taxonomy
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Adopt a three-category Architecture Knowledge Base taxonomy aligned with
  ISO 42010, formalized as a directory structure and machine-readable configuration.
tags:
- governance
- documentation
date: 2026-02-26
options:
  type: adr
  birth: 2026-02-26
  version: 1.0.0
  token_size: 2348
  status: accepted
  superseded_by: null
---
# ADR-26035: Architecture Knowledge Base Taxonomy

## Date
2026-02-26

## Status
accepted

## Context

Research and analytical artifacts — dialogue transcripts, trade studies, analytical summaries — that support architectural decisions have no formal home in the repository. They end up scattered across `misc/` or deleted entirely. This wastes architectural knowledge and makes it impossible for future engineers (human or AI) to trace *how* and *why* decisions were made.

The existing ADR system ({term}`ADR-26016`) handles decisions well. Post-mortems handle failure analysis. But the upstream research pipeline — the dialogues and analyses that *produce* those decisions — is undocumented and unmanaged. There is a gap between "we had a conversation" and "here is the ADR."

### The Problem in ISO 42010 Terms

ISO/IEC/IEEE 42010 defines an Architecture Knowledge Base as the combination of architectural decisions, their rationale, and the evidence that supports them. Our repository captures decisions (ADRs) but discards evidence. This violates the standard's intent: decisions without traceable evidence become opaque assertions.

### Current State

| Artifact type | Current location | Status |
|---|---|---|
| ADRs | `architecture/adr/` | Managed (ADR-26016, ADR-26017) |
| Post-mortems | `architecture/post-mortems/` | Partially managed, no frontmatter |
| Analyses | `misc/` or deleted | Unmanaged |
| Transcripts | Not committed | Lost |

## Decision

Adopt a three-category Architecture Knowledge Base taxonomy aligned with ISO 42010, formalized as a directory structure and machine-readable configuration.

### 1. Conceptual Taxonomy

```
Architecture Knowledge Base
├── Decisions        → ADRs (binding constraints)
├── Evidence
│   ├── Prospective  → Analyses, trade studies, comparisons
│   ├── Retrospective→ Post-mortems, failure analyses
│   └── Sources      → Dialogues, transcripts (ephemeral)
└── Governance       → Manifesto, guides, config
```

### 2. Physical Directory Structure

```
architecture/
├── evidence/
│   ├── analyses/           # A-YYNNN_slug.md
│   ├── retrospective/      # R-YYNNN_slug.md
│   └── sources/            # S-YYNNN_slug.md (ephemeral)
│       └── README.md       # Permanent: explains git archaeology
└── ...                     # Existing directories unchanged
```

### 3. Namespace Convention

Each artifact type gets an independent ID namespace with a year prefix:

| Type | Prefix | Pattern | Example |
|---|---|---|---|
| Analysis | `A` | `A-YYNNN` | `A-26001` |
| Retrospective | `R` | `R-YYNNN` | `R-26001` |
| Source | `S` | `S-YYNNN` | `S-26001` |
| Decision (ADR) | `ADR` | `ADR-NNNNN` | `ADR-26035` |

**Rationale:** One analysis can produce many ADRs (1:many mapping), so analyses need independent IDs. Year prefix (YY) makes artifact age visible from the filename.

### 4. Frontmatter Schemas

All schemas are defined in the evidence validation config in `.vadocs/` (the single source of truth, see {term}`ADR-26036`). Tags are inherited from the shared governance config — no duplication. The ADR establishes the principle; the config is the living specification that can evolve without amending this ADR.

**Analysis** (`evidence/analyses/A-YYNNN_slug.md`):
```yaml---
title: Architecture Knowledge Base Taxonomy
date: 2026-02-26
tags:
- governance
- documentation
options:
  id: A-26001
  status: active
  sources:
  - S-26001
  produces:
  - ADR-26035
  type: adr
  token_size: 2218
---
```

**Retrospective** (`evidence/retrospective/R-YYNNN_slug.md`):
```yaml
---
id: R-26001
title: "SLM Non-Determinism in Commit Generation"
date: 2026-02-01
status: active          # active | resolved | superseded
severity: high          # low | medium | high | critical
tags: [ci, model]
produces: [ADR-26003]
---
```

**Source** (`evidence/sources/S-YYNNN_slug.md`):
```yaml
---
id: S-26001
title: "Claude — AKB Taxonomy Discussion"
date: 2026-02-26
model: claude-opus-4     # AI model or "human" for meeting notes
extracted_into: A-26001  # null until analysis exists
---
```

### 5. Source Lifecycle (Three-Commit Workflow)

Sources are ephemeral by design — committed for traceability, deleted after extraction:

1. **Commit 1 — Capture:** Add transcript to `evidence/sources/S-YYNNN_slug.md`
2. **Commit 2 — Extract:** Write analysis to `evidence/analyses/A-YYNNN_slug.md` with `sources: [S-YYNNN]`. Update source's `extracted_into` field.
3. **Commit 3 — Delete:** Remove the source file. Git history preserves it.

**Rule:** A source file is only deleted AFTER its `extracted_into` field points to a committed analysis.

**Git archaeology** commands for recovering deleted sources are documented in [evidence/sources/README](/architecture/evidence/sources/README.ipynb).

### 6. Validation

[check_evidence.py](/tools/scripts/check_evidence.py) validates evidence artifacts against the `.vadocs/` evidence config, following the same pattern as [check_adr.py](/tools/scripts/check_adr.py) validates ADRs ({term}`ADR-26017`).

Validation covers:
- Frontmatter schema compliance per artifact type
- Naming convention adherence (regex patterns in config)
- Orphaned source detection (committed but never extracted)

### 7. Portability

This taxonomy is designed to be adoptable by any repository:

1. Copy the `.vadocs/` evidence config and [check_evidence.py](/tools/scripts/check_evidence.py) — adapt tags and sections to your domain
2. Create the `evidence/` directory structure
3. (Optional) Add pre-commit hook and CI job

The conceptual taxonomy (Decisions / Evidence / Governance) is universal. The physical structure and tooling are the reference implementation.

## Consequences

### Positive
- **Traceability:** Every ADR can trace back through analyses to source dialogues
- **Machine-readability:** Frontmatter schemas enable automated validation and future RAG retrieval
- **Knowledge preservation:** Dialogue insights survive extraction into analyses instead of being lost
- **ISO 42010 alignment:** Evidence completes the Architecture Knowledge Base alongside decisions
- **Separation of concerns:** The ADR decides *that* we have a taxonomy; the config defines *how* it works. Rules evolve without ADR amendments

### Negative / Risks
- **Overhead for small changes:** Not every conversation warrants the three-commit workflow. **Mitigation:** Sources are optional — if the analysis is straightforward, skip directly to writing it.
- **Orphaned sources accumulate:** Sources might be committed but never extracted. **Mitigation:** [check_evidence.py](/tools/scripts/check_evidence.py) warns about orphaned sources older than 30 days.

## Alternatives

- **Option A: Embed evidence in ADRs themselves.** Add "Research Notes" sections directly in ADR files. **Rejection Reason:** Bloats ADR files, mixes decision records with research artifacts, breaks the single-responsibility principle. ADRs in other frameworks (MADR, Nygard) are intentionally concise.

- **Option B: Use a wiki or external tool for research.** Store dialogues and analyses in Notion, Confluence, or a separate wiki. **Rejection Reason:** Breaks the "documentation as code" principle ({term}`ADR-26021`). External tools are not version-controlled, not validated by CI, and not portable across repositories.

- **Option C: Status-based subdirectories for ADRs** (e.g., `decisions/accepted/`, `decisions/proposed/`). **Rejection Reason:** Evaluated and rejected — moving files between directories on status change breaks all inbound links, creates dual source of truth (directory vs. frontmatter), and adds operational overhead. Real-world precedent: KEPs, PEPs, MADR, and Google ADRs all use flat directories with metadata-driven lifecycle. Full analysis in [A-26001](/architecture/evidence/analyses/A-26001_architecture_knowledge_base_taxonomy.md).

## References
- [ISO/IEC/IEEE 42010:2022 — Architecture description](https://www.iso.org/standard/74393.html)
- [A-26001: Architecture Knowledge Base Taxonomy](/architecture/evidence/analyses/A-26001_architecture_knowledge_base_taxonomy.md) — analysis that produced this ADR
- {term}`ADR-26036` — Config file location and naming conventions (`.vadocs/` directory)
- {term}`ADR-26042` — Common frontmatter standard (shared governance vocabulary)
- [evidence/sources/README](/architecture/evidence/sources/README.ipynb) — source lifecycle and git archaeology
- {term}`ADR-26016` — Metadata-Driven Architectural Records Lifecycle
- {term}`ADR-26017` — ADR Format Validation Workflow
- {term}`ADR-26036` — Config File Location and Naming Conventions
- {term}`ADR-26031` — Prefixed Namespace System for Architectural Records
- [MADR — Markdown Any Decision Records](https://adr.github.io/madr/)
- [Michael Nygard — Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

## Participants
1. Vadim Rudakov
2. Claude (AI Systems Architect)
