---
title: Common Frontmatter Standard
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-14
description: Adopts a composable block frontmatter schema as the universal standard
  for all governed documents. Defines 3 block types (identity, discovery, lifecycle)
  that compose additively per document type. Requires every file with frontmatter
  to self-identify via options.type so validation scripts load the correct spoke config.
  Eliminates directory-based type inference, fixes inconsistent date semantics, and
  replaces flat required-fields lists with additive block inheritance. Hub config
  (.vadocs/conf.json) defines field registry, block composition, and 10-type taxonomy;
  spoke configs (.vadocs/types/<type>.conf.json) add type-specific required fields,
  allowed statuses, and severity values.
tags:
- governance
- documentation
- context_management
options:
  type: adr
  birth: 2026-03-11
  version: 1.1.0
  token_size: 2858
  id: 26042
  status: accepted
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26042: Common Frontmatter Standard

## Date

2026-04-14 (accepted — enforcement of `options.type` as mandatory field)

## Status

accepted

Supersedes {term}`ADR-26023`.

## Context

As of March 2026, the repository has 10 governed document types (9 content + 1 service) across multiple directories, but frontmatter governance is fragmented. Only 4 types (ADR, analysis, retrospective, source) have full schema validation — each defined independently in `adr_config.yaml` and `evidence.config.yaml`. The remaining 5 content types (tutorial, guide, script instruction, package spec, policy) have no frontmatter validation at all.

{term}`ADR-26023` established MyST-native field names (`title`, `author`, `date`, `options.version`, `options.birth`) for content articles but did not define a type system or cover non-article types. The `options.*` nesting hides fields from validation scripts. Meanwhile, `evidence.config.yaml` defines its own `common_required_fields` as a stopgap, duplicating field definitions across configs.

A systematic audit in [A-26008](/architecture/evidence/analyses/A-26008_frontmatter_standard_taxonomy_audit.md) revealed three structural problems:

1. **No type self-identification** — validation scripts infer type from directory path rather than from the document itself.
2. **Flat field model fails** — a single required-fields list cannot serve both service files (2 fields) and full content types (10+ fields).
3. **`date` semantics are inconsistent** — ADRs treat `date` as birth date; analyses treat it as last-modified; {term}`ADR-26023` defines it as last-modified. The same field means different things depending on type.

The audit proposed a composable block architecture following the DITA specialization principle: types compose blocks additively, never removing fields. This eliminates the need for exclusion rules while accommodating the full range from minimal service files to rich content types.

## Decision

We adopt a composable block frontmatter schema as the universal standard for all governed documents. Every `.md` and Jupytext-paired `.ipynb` file in a governed directory carries frontmatter composed from three blocks. Types declare which blocks they use; blocks are only added, never subtracted.

### 1. Composable Blocks

**Identity block** — present in every governed document:

| Field | Purpose | Maintenance | MyST-native? |
|---|---|---|---|
| `title` | Document identity | Human | Yes |
| `type` | Self-describing file type | Human (set once) | No (`options.type`) |
| `authors` | Responsible party (owner, not necessarily the writer — documents may be AI-generated under human control) | Human | Yes |

**Discovery block** — enables agent progressive disclosure:

| Field | Purpose | Maintenance | MyST-native? |
|---|---|---|---|
| `description` | Brief elevator pitch | Human | Yes |
| `tags` | Domain classification | Human (validated against vocabulary) | Yes |
| `token_size` | Context budget cost | Auto (pre-commit hook) | No (`options.token_size`) |

**Lifecycle block** — production traceability:

| Field | Purpose | Maintenance | MyST-native? |
|---|---|---|---|
| `date` | Last meaningful update | Auto (pre-commit hook) | Yes |
| `birth` | Creation date | Auto (pre-commit hook on new file) | No (`options.birth`) |
| `version` | SemVer traceability | Human bump, auto-validated — if `date` changed, `version` must change | No (`options.version`) |

Fields marked "MyST-native" in the tables above are top-level YAML keys rendered by the MyST site. All other fields go under `options.*` — invisible to MyST but accessible to validation scripts and RAG pipelines. The authoritative list of which fields are MyST-native is the block tables, not this prose.

This preserves {term}`ADR-26023`'s principle of leveraging MyST frontmatter natively while extending it with ecosystem-specific metadata.

### 2. Type Composition

Each type declares which blocks it composes, plus type-specific required and optional fields:

| Type | Blocks | Type-Specific Required | Type-Specific Optional |
|---|---|---|---|
| `adr` | identity + discovery + lifecycle | `id`, `status` | `superseded_by` |
| `analysis` | identity + discovery + lifecycle | `id`, `status` | `sources`, `produces` |
| `retrospective` | identity + discovery + lifecycle | `id`, `status`, `severity` | `produces` |
| `source` | identity + discovery | `id`, `model` | `extracted_into` |
| `tutorial` | identity + discovery + lifecycle | — | — |
| `guide` | identity + discovery + lifecycle | — | — |
| `script_instruction` | identity + discovery + lifecycle | — | — |
| `package_spec` | identity + discovery + lifecycle | — | — |
| `policy` | identity + discovery + lifecycle | — | — |
| `service` | identity | — | `role` (generated/template/navigation), `version` |

Sources skip lifecycle because they are ephemeral (three-commit workflow). Service files skip both discovery and lifecycle because they are infrastructure, not authored content. The `manifesto` type from A-26008 is absorbed into `policy` — it is a singleton document that shares the same governance needs.

### 3. `date` Semantic Unification

All types adopt the same `date` semantics: **last meaningful update**. The `birth` field captures creation date. This resolves the inconsistency where ADRs treated `date` as birth date while other types treated it as last-modified.

### 4. `id` Is Type-Specific

The `id` field is not universal. Only types that cross-reference each other via frontmatter fields carry `id`: ADR, analysis, retrospective, source. Types referenced solely via file path links (tutorials, guides, etc.) do not need synthetic IDs.

### 5. Jupytext Dual-Block Parsing

Validation scripts must support Jupytext dual-block files, parsing the content frontmatter block (Block 2, after the H1 title) rather than the Jupytext config block (Block 1).

### 6. Centralized Configuration

The block definitions, type registry, and shared tag vocabulary are codified in the project's centralized governance config directory ({term}`ADR-26036`). The shared config (`conf.yaml`) is the SSoT for what fields every type must have. Doc type configs (`<doc_type>.conf.yaml`) retain domain-specific operational rules and inherit common vocabulary via `parent_config`. See [A-26010](/architecture/evidence/analyses/A-26010_config_file_distribution_patterns.md) for the evidence base behind the scope-isolated directory pattern.

> **Important: Strict Additive Inheritance**
>
> Between ecosystem projects, the hub project's config provides defaults. Spoke projects' configs extend them:
>
> 1. **Hub fields are immutable** — spokes cannot remove, rename, or change semantics of hub-defined fields.
> 2. **Spokes add** — type-specific fields extend the hub schema.
> 3. **Spokes tighten** — a spoke may promote a hub optional field to required for its type, but never the reverse.
> 4. **Spokes that override hub semantics are invalid** and rejected by validation.

### 7. Migration

Automated, in two phases: (A) ADRs first — one-shot script to fix the `date` → `birth` semantic shift, since lazy migration would leave 41 files with silently wrong semantics; (B) all other governed files — auto-fix script analogous to `check_adr.py --fix`, adding missing fields per the type registry. Human-authored fields (`description`) get `TODO` placeholders for later review.

## Consequences

### Positive

- **Universal governance**: All 10 types validated against a single schema, closing the gap for 5 currently unvalidated content types.
- **Agent-optimized**: The discovery block (`description`, `tags`, `token_size`) enables progressive disclosure — agents read lightweight metadata before deciding whether to load the full document.
- **Config unification**: Hub-and-spoke model eliminates config fragmentation — one SSoT for shared fields, spokes for domain rules.
- **Self-describing documents**: The `type` field eliminates directory-path inference, making documents portable across refactors.
- **Additive-only composition**: No exclusion rules to maintain. Adding a new type means declaring which blocks it composes.

### Negative / Risks

- **Migration scope**: 41 ADRs need `date` → `birth` data migration plus new fields (`type`, `description`, `token_size`). All governed files need at minimum `type` added. **Mitigation**: migration script for bulk changes; lazy migration for optional fields like `description`.
- **Pre-commit hook complexity**: Three auto-maintained fields (`date`, `birth`, `token_size`) require hooks that understand content vs. metadata changes. **Mitigation**: incremental implementation — start with `token_size` (stateless calculation), then `birth` (set-once), then `date` (requires diff analysis).
- **Dual-block parser**: Jupytext files require special parsing logic. **Mitigation**: limited scope — only ~7 tutorial files currently use Jupytext pairing.
- **Ecosystem fields invisible on site**: `type`, `birth`, `version`, `token_size` live under `options.*` and are not rendered by the default MyST theme. **Mitigation**: accessible via CLI and RAG pipelines; rendering deferred to future custom MyST template work (consistent with {term}`ADR-26023` approach).

## Alternatives

- **Flat "8 universal fields" model** (A-26005 proposal): Rejected. Service files and ephemeral sources don't need all fields. Exclusion rules ("everything except X for type Y") are harder to reason about than additive composition.
- **Keep {term}`ADR-26023` + extend per-type configs**: Rejected. Perpetuates config fragmentation and leaves 5 content types without any validation. Does not solve the `date` semantic inconsistency.
- **`id` as universal field**: Rejected. ID formats differ across types (numeric for ADRs, prefixed for evidence). Types referenced by file path gain no value from synthetic IDs. For RAG retrieval, `title` + `type` + file path provides sufficient identity.
- **Inheritance with exclusions**: Rejected in favor of additive-only composition (DITA specialization principle). "What did this type remove?" is harder to reason about than "what blocks does this type compose?"

## References

- [A-26008: Taxonomy Audit and Composable Block Design](/architecture/evidence/analyses/A-26008_frontmatter_standard_taxonomy_audit.md) — Design specification for this ADR
- [A-26005: Agentic OS Filesystem Architecture](/architecture/evidence/analyses/A-26005_doc_type_interfaces_unified_validation.md) — Taxonomy design, VFS/inode model, DITA specialization analysis
- [A-26009: Compass — The Realistic State of Agentic AI 2026](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) — SKILL.md progressive disclosure pattern
- {term}`ADR-26023` — Superseded by this ADR
- {term}`ADR-26035` — Evidence pipeline and three-commit workflow
- {term}`ADR-26036` — Config file location and naming conventions; rationale for section 6 config design
- `evidence.config.yaml` — Current evidence schemas (migrates into centralized config per {term}`ADR-26036`)
- `adr_config.yaml` — Current ADR schema (migrates into centralized config per {term}`ADR-26036`)

## Participants

1. Vadim Rudakov
2. Claude (claude-opus-4-6, AI Engineering Advisor)
