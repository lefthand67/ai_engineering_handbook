
---
title: Ecosystem Package Boundary
author: Vadim Rudakov, rudakow.wadim@gmail.com
date: 2026-03-14
tags:
- governance
- architecture
options:
  token_size: 2072
  id: 26043
  status: proposed
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-03-14'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: '<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md
  -->.'
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26043: Ecosystem Package Boundary

## Date

2026-03-14

## Status

proposed

## Context

As of March 2026, the repository's governance tooling lives in `tools/scripts/` as a flat collection of 16 standalone Python scripts. These scripts share configuration files (`adr_config.yaml`, `evidence.config.yaml`), a common path module (`paths.py`), and overlapping concerns — yet they have no package structure, no shared abstractions, and no explicit boundaries between concerns.

This flat layout creates three problems as the ecosystem grows:

1. **Shotgun surgery** — adding a new document type (e.g., `skill`) requires touching a validator script, its config, the path constants, and potentially a fixer — all in the same flat directory with no grouping to guide discovery.
2. **No reuse boundary** — other ecosystem projects (`vadocs`, `mentor_generator`) cannot import governance logic without copying scripts. There is no installable package with a public API.
3. **Concern bleeding** — doc content validation (frontmatter, sections, cross-refs), git policy enforcement (commit messages, changelog), and repo scaffolding (pre-commit setup, jupytext sync) are interleaved in one directory. A developer working on commit message validation must navigate past 14 unrelated scripts.

The [A-26009 Compass analysis](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) established context engineering as the core design principle. A well-bounded package is itself a context engineering artifact — it tells agents and humans where to look and what belongs together.

## Decision

We establish `vadocs` as an installable Python package that consolidates all repository governance tooling. The package is organized by concern, not by operation layer.

### 1. Package Structure

```{mermaid}
graph TD
    vadocs[vadocs]
    core[core/]
    docs[docs/]
    git[git/]
    init[init/]
    cli[cli.py]

    vadocs --> core
    vadocs --> docs
    vadocs --> git
    vadocs --> init
    vadocs --> cli

    core --> C1[paths & config loading]
    core --> C2["base classes (Validator, Fixer)"]
    core --> C3[shared utilities]

    docs --> D1["content validation (frontmatter, sections, cross-refs)"]
    docs --> D2["link checking (targets & format)"]
    docs --> D3["file integrity (JSON, API keys)"]
    docs --> D4["evidence pipeline (HTML extraction)"]

    git --> G1[commit message validation]
    git --> G2[changelog generation]

    init --> I1[environment setup]
    init --> I2[jupytext sync & verify]
    init --> I3[script suite triad]

    docs -.->|imports| core
    git -.->|imports| core
    init -.->|imports| core

    style vadocs fill:#2d3748,color:#fff
    style core fill:#4a5568,color:#fff
    style docs fill:#2b6cb0,color:#fff
    style git fill:#2f855a,color:#fff
    style init fill:#b7791f,color:#fff
    style cli fill:#4a5568,color:#fff
```

Each concern directory is self-contained: its validators, fixers, and helpers live together. When a new document type is added, all related logic goes into `docs/` — one directory, one concern. `prepare_prompt.py` stays outside vadocs — it belongs to the AI system's prompt layer, not to repository governance.

### 2. Package Boundary Rule

A script belongs in vadocs if it enforces repository governance: document structure, content quality, git policy, or development environment consistency. Content transformation tools (like `extract_html_text.py`) belong when they serve the evidence pipeline — the document lifecycle from acquisition to validation.

Scripts that serve the AI system architecture (prompt preparation, model interaction) stay outside vadocs as standalone tools.

### 3. Installability

vadocs is an installable Python package (`pip install -e .` / `uv pip install -e .`) with a `pyproject.toml` defining entry points. Pre-commit hooks invoke vadocs via its CLI entry point rather than calling scripts directly. This enables other ecosystem projects to depend on vadocs for shared governance logic.

### 4. Configuration Inheritance

vadocs loads configuration through the hub-and-spoke model established in [ADR-26042](/architecture/adr/adr_26042_common_frontmatter_standard.md). Config paths are resolved relative to the repository root, not the package installation path.

### 5. Org-Agnostic Design

The package contains no hardcoded organization-specific values. Repository name, ADR prefixes, directory paths, and tag vocabularies are loaded from configuration. This allows vadocs to govern any repository that provides the expected config structure.

## Consequences

### Positive

- **Single-concern navigation**: Adding a new document type means working in `docs/` — validators, fixers, and helpers for that type live together. No shotgun surgery across directories.
- **Importable governance**: Other ecosystem projects can `import vadocs.docs` to reuse validation logic, eliminating script copying.
- **Agent-friendly boundaries**: The package structure itself is a progressive disclosure map — agents read the top-level directories to understand concerns, then drill into the relevant module.
- **Test co-location**: Tests mirror the concern structure (`tests/docs/`, `tests/git/`, `tests/init/`), making it obvious which tests cover which concern.
- **CLI unification**: The CLI mirrors the concern structure (`vadocs docs check-broken-links`, `vadocs git generate-changelog`, `vadocs init configure-repo`). The concern prefix reduces cognitive load — the developer always knows which domain they are operating in.

### Negative / Risks

- **Migration effort**: 15 scripts need to be restructured into modules, imports updated, and pre-commit hooks repointed. **Mitigation**: incremental migration — move one concern at a time, starting with `core/` (paths, config), then `docs/`, then `git/`, then `init/`. Old script paths can be thin wrappers during transition.
- **Import path changes**: Any external references to `tools.scripts.check_adr` break. **Mitigation**: the current codebase has no external consumers — all invocations are via pre-commit hooks and direct `uv run` calls, which are updated as part of migration.
- **Increased package complexity**: A flat script directory is simpler to understand at small scale. **Mitigation**: the project has already passed the threshold (16 scripts, 3 config files) where flat structure hinders rather than helps.

## Alternatives

- **Keep flat `tools/scripts/` with naming conventions** (e.g., `doc_check_adr.py`, `git_validate_commit.py`): Rejected. Naming conventions provide discoverability but not importability. Scripts cannot share base classes or be installed as a package. The naming prefix approach degrades quickly — `doc_check_adr_frontmatter.py` vs `doc_check_adr_sections.py` vs `doc_fix_adr_index.py`.
- **Group by operation layer** (`validators/`, `fixers/`, `generators/`): Rejected. This separates code that changes together. Adding a document type requires touching `validators/`, `fixers/`, and `tests/` — three directories for one conceptual change. Real-world projects (Django, pytest) moved away from this pattern as they scaled.
- **Monorepo with separate packages per concern** (`vadocs-docs`, `vadocs-git`, `vadocs-init`): Rejected as premature. The concerns share `core/` primitives and configuration loading. Separate packages would require publishing, versioning, and dependency management overhead with no current consumer demand. If a concern grows large enough to warrant extraction, the by-concern structure makes that refactor straightforward.

## References

- [ADR-26042: Common Frontmatter Standard](/architecture/adr/adr_26042_common_frontmatter_standard.md) — Hub-and-spoke configuration model inherited by vadocs
- [ADR-26038: Context Engineering as Core Design Principle](/architecture/adr/adr_26038_context_engineering_as_core_design_principle.md) — Package structure as context engineering artifact
- [A-26009: Compass — The Realistic State of Agentic AI 2026](/architecture/evidence/analyses/A-26009_compass_realistic_state_of_agentic_ai_2026.md) — Single-agent emphasis, progressive disclosure patterns
- [ADR-26011: Formalization of Mandatory Script Suite](/architecture/adr/adr_26011_formalization_of_mandatory_script_suite.md) — Current script triad convention (script + test + doc)

## Participants

1. Vadim Rudakov
2. Claude (claude-opus-4-6, AI Engineering Advisor)
