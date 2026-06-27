---
id: 26023
title: MyST-Aligned Frontmatter Standard
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-08.
tags:
- governance
- documentation
- context_management
date: 2026-02-08
options:
  type: adr
  birth: '2026-02-08'
  version: 1.0.0
  token_size: 1765
  status: accepted
  superseded_by: null
---
# ADR-26023: MyST-Aligned Frontmatter Standard

## Date

2026-02-08

## Status

accepted

Supersedes: {term}`ADR-26018`, {term}`ADR-26019`

## Context

{term}`ADR-26018` mandated universal YAML frontmatter with four fields: `owner`, `version`, `birth`, and `last_modified`. These names were chosen for human clarity but do not match the [MyST frontmatter API](https://mystmd.org/guide/frontmatter). As a result, the MyST static site renderer (`myst build --html`) silently ignores them — they never appear on the published documentation site.

{term}`ADR-26019` proposed a workaround: a **reflection block** script (`sync_metadata.py`) that would project YAML metadata into the document body as visible Markdown. This added automation complexity (pre-commit hooks, positional parsing, Jupytext sync) to solve a problem that MyST already solves natively — if the correct field names are used.

### Key Finding

MyST renders the following frontmatter fields **natively** with the default `book-theme`:

| Field | Format | Rendered on Site? | Notes |
|---|---|---|---|
| `title` | string | **Yes** | Page title |
| `author` | string | **Yes** | Full string rendered (including email if present) |
| `authors` | array of objects | **Partially** | Only `name` renders; `email` is not displayed |
| `date` | ISO 8601 string | **Yes** | Rendered on the page |
| `options.*` | dict | **No** | Custom fields — invisible to default MyST theme |

By renaming `owner` to `author` and `last_modified` to `date`, MyST renders ownership and freshness information without any custom scripts, templates, or reflection blocks.

### Two-Block Jupytext Structure

When editing in JupyterLab (the primary editing environment), the frontmatter lives in the **first markdown cell** of the `.ipynb` file. On `jupytext --sync`, the `.md` file receives two YAML blocks:

| `.ipynb` | `.md` | Purpose |
|---|---|---|
| Notebook-level metadata (invisible in JupyterLab) | **Block 1** — first `---` block (`jupytext:`, `kernelspec:`) | Jupytext sync config |
| First markdown cell | **Block 2** — second `---` block (`title:`, `author:`, `date:`, etc.) | Content frontmatter |

**This two-block structure is necessary.** Merging them into a single `.md` block causes metadata loss in the `.ipynb` file because the `.md` takes priority during sync. The `.ipynb` editing workflow is primary — two blocks must remain.

## Decision

We adopt MyST-native field names for all content article frontmatter. This supersedes the field naming in {term}`ADR-26018` and eliminates the need for reflection block scripts proposed in {term}`ADR-26019`.

### 1. Canonical Frontmatter Schema

| Field | Location | Rendered by MyST? | Notes |
|---|---|---|---|
| `title` | top-level | **Yes** | Document title |
| `author` / `authors` | top-level | **Yes** | Author's choice of format |
| `date` | top-level | **Yes** | Semantically = last modified date |
| `version` | `options.version` | **No** | For RAG/tooling; future custom template |
| `birth` | `options.birth` | **No** | For RAG/tooling; future custom template |

Both `author` (string) and `authors` (array of objects) are valid MyST formats. Individual document authors choose which they prefer.

### 2. Example: `author` as String

```yaml

title: Article Title
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-02-08
options:
  version: "0.1.0"
  birth: 2026-01-03
  token_size: 1688
  type: adr
---
```

### 3. Example: `authors` as Array

```yaml

title: Article Title
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-02-08
options:
  version: "0.1.0"
  birth: 2026-01-03
  type: adr
---
```

### 4. Reflection Block Scripts Eliminated (Content Articles)

MyST renders `author` and `date` natively. The `sync_metadata.py` pre-commit hook proposed in {term}`ADR-26019` is no longer needed for content articles. The reflection block pattern (first cell after H1 title) is retired.

### 5. ADR Scope Exclusion

ADRs retain their own format defined by {term}`ADR-26016` and {term}`ADR-26017`. ADR body/YAML synchronization (Status, Date sections matching YAML fields) remains a separate concern.

### 6. Migration Strategy

Lazy migration — files are updated to the new schema as they are touched. No big-bang migration required.

## Consequences

### Positive

* **Native Rendering**: `author` and `date` appear on the MyST static site without custom scripts, templates, or reflection blocks.
* **Reduced Complexity**: Eliminates the planned `sync_metadata.py` pre-commit hook and the positional parsing logic it required.
* **Standard Compliance**: Field names align with the MyST frontmatter API, ensuring forward compatibility with future MyST features.
* **RAG Compatibility**: `version` and `birth` remain in structured YAML (under `options.*`) for AI/RAG ingestion and CLI tooling (`yq`).

### Negative / Risks

* **Hidden Fields**: `version` and `birth` are not rendered by the default MyST theme. Readers of the static site cannot see them. **Mitigation**: These fields remain accessible via CLI (`cat`, `less`, `yq`) and RAG pipelines. Rendering them is deferred to future custom MyST template work.
* **Field Name Change**: Existing articles using `owner`/`last_modified` must be updated. **Mitigation**: Lazy migration — update on touch, no big-bang required.

## Alternatives

* **Keep ADR-26018 Field Names + Reflection Scripts**: Rejected. Adds automation complexity to solve a problem MyST solves natively. The reflection block pattern introduces positional fragility and sync overhead without benefit when standard field names are used.
* **Custom MyST Plugin for `owner`/`last_modified`**: Rejected for now. Building a plugin adds development and maintenance burden. May be revisited for `version`/`birth` rendering in the future.

## References

- {term}`ADR-26018`: Universal YAML Frontmatter Adoption (superseded by this ADR)
- {term}`ADR-26019`: Mirroring YAML Metadata to Document Body (superseded by this ADR)
- {term}`ADR-26016`: Metadata-Driven Architectural Records Lifecycle
- {term}`ADR-26017`: ADR Format Validation Workflow
- [MyST Frontmatter API](https://mystmd.org/guide/frontmatter)
- [YAML Frontmatter for AI-Enabled Engineering](/ai_system_layers/5_context/yaml_frontmatter_for_ai_enabled_engineering.ipynb)

## Participants

1. Vadim Rudakov
2. Claude (AI Engineering Advisor)
