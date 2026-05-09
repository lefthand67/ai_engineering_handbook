
---
title: Architecture Knowledge Base Taxonomy
date: 2026-02-26
tags:
- governance
- documentation
- architecture
options:
  token_size: 2505
  id: A-26001
  status: active
  sources: []
  produces:
  - ADR-26035
  type: analysis
  version: 1.0.0
  birth: '2026-02-26'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 'Architectural knowledge is generated through a pipeline: conversations
  produce insights, insights produce analyses, analyses produce decisions (ADRs).'
---
# A-26001: Architecture Knowledge Base Taxonomy

## Problem Statement

Architectural knowledge is generated through a pipeline: conversations produce insights, insights produce analyses, analyses produce decisions (ADRs). But in most repositories — including this one — only the final output (the ADR) is managed. The upstream pipeline is invisible:

- **Dialogue transcripts** are never committed or deleted after the session
- **Trade studies and analyses** end up in `misc/` with no naming convention or frontmatter
- **Post-mortems** exist but lack machine-readable metadata and live in an unrelated directory

The result: ADRs appear as disconnected assertions. A new engineer reading "We chose X over Y" cannot find the analysis that compared X and Y, or the dialogue that surfaced the trade-offs.

### The ISO 42010 Gap

ISO/IEC/IEEE 42010 defines an Architecture Knowledge Base as decisions *plus* the evidence that supports them. Our repository implements Decisions (ADRs) and partially implements Governance (manifesto, guides). But Evidence — the category that connects research to decisions — has no formal representation.

## Research Pipeline Model

Every architectural decision follows a pipeline, whether explicit or implicit:

```
Sources → Analyses → Decisions
(dialogues, notes)   (trade studies)   (ADRs)
         ↑                               ↑
    Retrospectives ──────────────────────┘
    (post-mortems feed future decisions)
```

The pipeline has three stages:

1. **Capture** — Raw inputs: AI dialogues, meeting notes, research sessions. These are high-volume, low-structure, ephemeral.
2. **Synthesis** — Structured analyses: trade studies, comparison matrices, evaluation frameworks. These distill raw inputs into actionable insights.
3. **Decision** — ADRs: binding constraints derived from analyses. These are the stable output.

The key insight: **stages 1 and 2 have no home in most repositories**. ADR frameworks (Nygard, MADR, adr-tools) manage stage 3 only.

## Approach Evaluation

Three approaches were evaluated for managing the full pipeline:

### Approach 1: Extend ADRs to Include Evidence

Add "Research Notes" and "Source Transcripts" sections directly to ADR files.

| Criterion | Assessment |
|---|---|
| Simplicity | High — no new directories or tooling |
| ADR readability | Low — bloats concise decision records with research artifacts |
| Separation of concerns | Violated — mixes decision records with evidence |
| 1:many mapping | Broken — one analysis producing 5 ADRs requires duplicating the analysis 5 times |
| Portability | Low — other frameworks expect concise ADRs |

**Verdict:** Rejected. ADRs are intentionally concise in every major framework.

### Approach 2: External Tool (Wiki, Notion, Confluence)

Store research in a separate system with links from ADRs.

| Criterion | Assessment |
|---|---|
| Rich editing | High — wikis have good editors |
| Version control | None — external tools are not git-managed |
| CI validation | Impossible — can't lint or validate external content |
| Link stability | Low — external URLs break, services sunset |
| Portability | None — tied to a specific vendor |

**Verdict:** Rejected. Violates "documentation as code" principle (ADR-26021).

### Approach 3: In-Repository Evidence Taxonomy

Create a structured `evidence/` directory within `architecture/` with typed subdirectories, frontmatter schemas, and automated validation.

| Criterion | Assessment |
|---|---|
| Version control | Full git history, including deleted sources |
| CI validation | [check_evidence.py](/tools/scripts/check_evidence.py) validates schemas |
| 1:many mapping | Natural — analyses and ADRs have independent ID namespaces |
| Portability | Copy config + script + directory structure to any repo |
| Overhead | Medium — requires naming convention and frontmatter discipline |

**Verdict:** Selected. The overhead is manageable because it mirrors the existing ADR workflow.

## Taxonomy Design

### ISO 42010 Alignment

The taxonomy maps to ISO 42010's Architecture Knowledge Base concept:

| ISO 42010 Concept | Repository Implementation |
|---|---|
| Architecture Decision | `decisions/` (ADRs) |
| Decision Rationale | ADR "Context" and "Alternatives" sections |
| Architecture Evidence | `evidence/` (analyses, retrospectives, sources) |
| Architecture Framework | `governance/` (manifesto, guides, config) |

### Directory-Metadata Separation Principle

A critical design decision: **directories encode location (type), metadata encodes state (lifecycle)**.

- An analysis moves from `active` → `absorbed` via a frontmatter change, not a directory move
- An ADR moves from `proposed` → `accepted` via a frontmatter change, not a directory move
- The directory tells you *what kind* of artifact it is; the frontmatter tells you *where it is in its lifecycle*

This principle was hard-won. The alternative — status-based subdirectories — was evaluated and rejected (see below).

### Namespace Independence

Each artifact type has an independent ID namespace:

| Namespace | Format | Rationale |
|---|---|---|
| `A-YYNNN` | Analysis | Year prefix makes age visible; independent from ADR numbering |
| `R-YYNNN` | Retrospective | `R` matches directory name `retrospective/`; consistent with `A-` → `analyses/`, `S-` → `sources/` |
| `S-YYNNN` | Source | Ephemeral — IDs needed only for cross-referencing |
| `ADR-NNNNN` | Decision | Existing convention preserved (ADR-26016) |

The year prefix (`YY`) was chosen over a flat sequence because it provides instant temporal context without opening the file.

## Rejected Ideas

### Status-Based Subdirectories

The most debated alternative: organize ADRs into `accepted/`, `proposed/`, `rejected/` subdirectories instead of a flat directory.

**Arguments for:**
- Visual grouping in file explorers
- Immediately obvious which ADRs are active vs. historical

**Arguments against (decisive):**

1. **Link breakage:** When an ADR moves from `proposed/` to `accepted/`, every inbound link breaks — every markdown file, every CI script, every CLAUDE.md reference pointing to the old path. In a repository with 53+ cross-references per rename, this is operationally catastrophic.

2. **Dual source of truth:** The directory *and* the frontmatter both encode status. When they disagree (and they will), which is authoritative? This creates a class of bugs that flat directories eliminate entirely.

3. **Operational overhead:** Every status change becomes a file move + link update + commit, instead of a one-line frontmatter edit.

4. **Real-world precedent:** Every major decision record framework uses flat directories:
   - **KEPs** (Kubernetes Enhancement Proposals): flat `keps/` directory, metadata-driven
   - **PEPs** (Python Enhancement Proposals): flat `peps/` directory since 2000
   - **MADR** (Markdown Any Decision Records): flat, metadata-driven lifecycle
   - **Google's internal ADR system:** flat, labels for lifecycle management

The gap between conceptual models (categories feel natural) and physical constraints (file moves break links) is where most conventions fail. This taxonomy respects that gap.

## Key Insights

### 1. Directories Encode Location, Metadata Encodes State

This is the most important principle in the taxonomy. When state (lifecycle stage) is encoded as location (directory), every state transition becomes a move operation that breaks references. When state is encoded as metadata (frontmatter), transitions are single-field edits that break nothing.

### 2. The Gap Between Conceptual and Physical Models

Humans think in categories: "active decisions", "rejected decisions", "archived analyses." But file systems punish categorization with link breakage. The taxonomy bridges this gap by using directories for *type* (stable) and metadata for *state* (mutable).

### 3. Post-Mortems Are Retrospective Evidence

Post-mortems are not a separate category — they are evidence viewed through a retrospective lens. Taxonomically, they are siblings of analyses: analyses look forward (prospective), post-mortems look backward (retrospective). Both produce ADRs. Placing them under `evidence/` unifies the evidence hierarchy.

### 4. Sources as Ephemeral, Traceable Artifacts

The three-commit workflow solves a dilemma: transcripts are too large and noisy to keep permanently, but too valuable to lose entirely. By committing at a predictable path and then deleting, we get permanent git history without permanent directory clutter.

## Portability Design

The taxonomy is designed to be portable to any repository:

**To adopt:**
1. Copy the `.vadocs/` evidence config — adapt tags and sections to your domain
2. Copy [check_evidence.py](/tools/scripts/check_evidence.py) — runs against the config
3. Create the `evidence/` directory structure
4. (Optional) Add pre-commit hook and CI job

**What's universal:**
- The three-category model (Decisions / Evidence / Governance)
- The directory-metadata separation principle
- The namespace convention (prefix-YYNNN)
- The three-commit source lifecycle

**What's customizable:**
- Tag vocabulary (domain-specific)
- Required/allowed sections per artifact type
- Orphan detection thresholds

## References

- [ISO/IEC/IEEE 42010:2022 — Architecture description](https://www.iso.org/standard/74393.html)
- [ADR-26035: Architecture Knowledge Base Taxonomy](/architecture/adr/adr_26035_architecture_knowledge_base_taxonomy.md) — the ADR this analysis produces
- [ADR-26016: Metadata-Driven Architectural Records Lifecycle](/architecture/adr/adr_26016_metadata_driven_architectural_records_life.md)
- [ADR-26017: ADR Format Validation Workflow](/architecture/adr/adr_26017_adr_format_validation_workflow.md)
- [ADR-26036: Config File Location and Naming Conventions](/architecture/adr/adr_26036_config_file_location_and_naming_conventions.md)
- [ADR-26042: Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md) — shared governance vocabulary
- [MADR — Markdown Any Decision Records](https://adr.github.io/madr/)
- [Michael Nygard — Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [KEP process documentation](https://github.com/kubernetes/enhancements/tree/master/keps)
- [PEP 1 — PEP Purpose and Guidelines](https://peps.python.org/pep-0001/)
