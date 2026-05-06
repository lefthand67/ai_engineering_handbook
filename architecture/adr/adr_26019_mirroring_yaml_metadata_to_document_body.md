
---
title: Mirroring YAML Metadata to Document Body for Human Verification
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-01
description: A pre-commit hook automatically mirrors YAML frontmatter fields into
  a prose reflection block in the document body, making metadata visible on the MyST-rendered
  static site.
tags:
- governance
- documentation
- context_management
options:
  type: adr
  birth: 2026-02-01
  version: 1.0.1
  token_size: 1745
  id: 26019
  status: superseded
  superseded_by: ADR-26023
---
# ADR-26019: Mirroring YAML Metadata to Document Body for Human Verification

## Date

2026-02-01 (revised 2026-02-05)

## Status

superseded

Superseded by: {term}`ADR-26023`

## Supersession Rationale

The reflection block script was a workaround for custom frontmatter fields ({term}`ADR-26018`) being invisible in the MyST-rendered site. When {term}`ADR-26023` replaced non-standard field names with MyST-native equivalents, the renderer natively displays them — eliminating the need for a prose projection layer.

## Context

Following the mandate for universal YAML frontmatter ({term}`ADR-26018`), we face a usability gap on the **published documentation site**. While YAML is the Single Source of Truth (SSoT) for machines and AI agents, the MyST static site renderer (`myst build --html`) only renders well-known frontmatter fields (`title`, `authors`, `date`, `doi`). Custom fields such as `owner`, `version`, `birth`, and `last_modified` are **silently ignored** in the HTML output. Additionally, `mystmd` has no substitution syntax (e.g., `{{ frontmatter.owner }}`) — [Issue #852](https://github.com/jupyter-book/mystmd/issues/852) remains open.

Note: CLI tools (`cat`, `less`), JupyterLab, and raw Git diffs **do** display the full YAML block. The gap is specific to readers who consume the rendered static site.

Without a visible projection of metadata in the document body, **Metadata Drift** becomes undetectable during peer review of the published site: a reader may assume a document is current based on prose, while the YAML marks it as `superseded` or `deprecated`.

### Current State (Pre-ADR-26018)

Every content article in the repo already uses a hand-written metadata block positioned immediately after the title:

```markdown
# Article Title

+++


Owner: Vadim Rudakov, lefthand67@gmail.com
Version: 0.1.3
Birth: 2026-01-14
Last Modified: 2026-01-17
options:
  type: adr
---

+++
```

This pattern is consistent across all articles (early and Jan 2026 generations). The `+++` MyST cell breaks and `---` thematic breaks provide a visually distinct, positionally stable block. However, this block is **manually authored** — there is no YAML source backing it, and no automation ensures consistency.

### Prerequisite

This ADR is sequenced **after** {term}`ADR-26018` (Universal YAML Frontmatter Adoption). The reflection block requires a machine-readable YAML source to mirror from. Until content articles carry `owner`, `version`, `birth`, `last_modified` fields in their YAML frontmatter, there is nothing to automate.

## Decision

We will automate the existing reflection block pattern as a **positional projection** of YAML frontmatter into the document body.

1. **Reflection Block Format**: The block uses the established pattern — `---` thematic breaks wrapping key-value lines, enclosed in `+++` MyST cell breaks. This is the pattern already in use across all content articles; we formalize rather than replace it.

2. **Positional Convention**: The reflection block is always the **first cell after the H1 title**. This positional stability makes it identifiable by both humans (visual scanning) and scripts (parse the first `+++`-delimited cell after `# Title`) without requiring special delimiters.

3. **Automated Sync**: A `pre-commit` hook (`tools/scripts/sync_metadata.py`) will:
   - Parse the YAML frontmatter via `python-frontmatter`
   - Format the reflection block from `owner`, `version`, `birth`, `last_modified` fields
   - Replace the content of the first post-title cell
   - Run `jupytext --sync` if a paired `.ipynb` exists

4. **Scope**: Content articles only (files under `ai_system/`, `tools/docs/`, etc.). ADRs use their own format defined in {term}`ADR-26016` and {term}`ADR-26017`.

### Target State

After {term}`ADR-26018` implementation, an article will have:

```markdown

jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
kernelspec:
  name: python3
owner: Vadim Rudakov
last_modified: 2026-01-17
options:
  birth: 2026-01-14
  version: "0.1.3"
  type: adr
---

# Article Title

+++


Owner: Vadim Rudakov
Version: 0.1.3
Birth: 2026-01-14
Last Modified: 2026-01-17
options:
  type: adr
---

+++

Technical content begins here...
```

The YAML block is the source; the `---` / prose / `---` block is the deterministic projection.

## Consequences

### Positive

* **Visual Integrity**: Engineers can verify ownership and freshness on the rendered static site, where custom YAML fields would otherwise be invisible. The reflection block renders as normal Markdown content, making metadata visible in every output format.
* **Zero New Syntax**: Formalizes the pattern already adopted by every content article. No migration required for existing files once YAML fields are added.
* **RAG Compatibility**: The positional convention allows RAG ingestion pipelines to strip the reflection block (first post-title cell) before generating embeddings, preventing metadata from polluting the semantic space.

### Negative / Risks

* **Positional Fragility**: If an author inserts content between the title and the reflection block, the sync script will overwrite the wrong cell. **Mitigation**: The pre-commit hook validates that the first post-title cell matches the expected reflection format before overwriting.
* **Sync Overhead**: Requires `python-frontmatter` and Jupytext as development dependencies. **Mitigation**: Both are already project dependencies.
* **Prerequisite Dependency**: This ADR is inert until {term}`ADR-26018` is implemented. **Mitigation**: Explicit sequencing documented in this ADR.

## Alternatives

* **HTML Comment Anchors** (`<!-- meta -->...<!-- /meta -->`): Rejected. Introduces a new delimiter syntax not present in any existing article. Adds parsing complexity without solving a real collision problem — the existing `+++` / `---` pattern has been used across 20+ articles without a single parsing ambiguity. Would require migrating all existing articles to a new format.
* **Prose-only Metadata (No YAML Source)**: Rejected. Cannot be validated or synced by automation. Current manual approach — the very pattern we aim to automate.
* **No Reflection Block (YAML Only)**: Rejected. Custom YAML frontmatter fields are not rendered by the MyST book-theme on the static site (`myst build --html` silently ignores them). Readers of the published documentation would have no way to verify document ownership or freshness without accessing the raw source file.

## References

* {term}`ADR-26016`: Metadata-Driven Architectural Records Lifecycle
* {term}`ADR-26017`: ADR Format Validation Workflow
* {term}`ADR-26018`: Universal YAML Frontmatter Adoption for Machine-Readable Documentation

## Participants

1. Vadim Rudakov
2. Claude (AI Engineering Advisor)
