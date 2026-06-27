---
id: 26016
title: Metadata-Driven Architectural Records Lifecycle
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Metadata-Driven Architectural Records Lifecycle.
tags:
- devops
- documentation
- governance
date: 2026-02-01
options:
  type: adr
  birth: '2026-02-01'
  version: 1.0.0
  token_size: 770
  status: accepted
  superseded_by: null
---
# ADR-26016: Metadata-Driven Architectural Records Lifecycle

## Title

Metadata-Driven Architectural Records Lifecycle

## Date

2026-02-01

## Status

accepted

## Context

Our current documentation process relies on unstructured Markdown files. This creates two primary failures in production-grade maintenance:
1. **Traceability Decay:** Moving "dismissed" records to an archive directory breaks relative links and obscures the decision-making timeline [SWEBOK: Quality-2.1].
2. **Machine-Inscrutability:** Local LLMs (aider, qwen2.5-coder) and CLI tools (grep, yq) cannot efficiently query the state of the architecture without parsing irregular prose.

We require a system that maintains **Link Integrity** while providing **Machine-Readable Metadata** for automated auditing.

## Decision
We will implement a **Status-Driven Immutable Path** pattern for all ADRs.
1. **Location:** All ADRs shall reside in a flat directory (`architecture/adr/`). Files will **never** be moved to an archive folder.
2. **Schema:** Every ADR must include a YAML frontmatter block containing `id`, `title`, `date`, `status`, `superseded_by`, and `tags`.
3. **State Machine:** ADR statuses are strictly limited to the following enum: `proposed`, `accepted`, `rejected`, `superseded`, `deprecated`.
4. **Linkage:** When a decision is superseded, the `superseded_by` field must be updated with the ID of the new record, and the file body must link to the new record.

## Consequences

### Local Stack Impact (SVA Audit)
- **Developer Workflow:** Minimal overhead. Developers must fill out ~6 lines of YAML.
- **Tooling:** Enables the use of `yq` or `python-frontmatter` for automated index generation.
- **CI/CD:** Pre-commit hooks can now programmatically validate that no "Accepted" ADRs conflict with new "Proposed" ones.

### Positive
- **Link Integrity:** All internal documentation links remain valid for the life of the project.
- **Searchability:** Architectural state can be queried via CLI: `grep "status: accepted" docs/adr/*.md`.
- **LLM Context:** Provides a clear "source of truth" for `aider` to understand current constraints.

### Negative / Risks
- **Metadata Drift:** Risk of the YAML status becoming out of sync with the body text. **Mitigation:** Implementation of a `pre-commit` validation script.

## Alternatives
- **Physical Archiving:** Rejected. Breaks cross-references and fragments git history.
- **Centralized Spreadsheet:** Rejected. Violates "Documentation as Code" and SVA principles (not versionable via Git).

## References
- *Documenting Architecture Decisions* [Michael Nygard], 2011.
- *ISO/IEC/IEEE 29148:2018 Standards for Software Requirements.*

## Participants

1. Vadim Rudakov
2. Gemini (AI Thought Partner)
