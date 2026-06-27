---
id: 26012
title: Extraction of Documentation Validation Engine
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: Extracting validation scripts into a standalone, reusable Python package..
tags:
- governance
date: 2026-01-31
options:
  type: adr
  birth: '2026-01-31'
  version: 1.0.0
  token_size: 1154
  status: proposed
  superseded_by: null
---
# ADR-26012: Extraction of Documentation Validation Engine

## Title

Extracting validation scripts into a standalone, reusable Python package.

## Status

Proposed

## Date

2026-01-27

## Context

The `tools/scripts/` directory has evolved into a cohesive validation engine for MyST-based documentation repositories. This engine includes:

- **Link validation** (`check_broken_links.py`, `check_link_format.py`)
- **Notebook synchronization** (`jupytext_sync.py`, `jupytext_verify_pair.py`)
- **Secret detection** (`check_api_keys.py`)
- **Schema validation** (`check_json_files.py`)
- **Development workflow enforcement** (`check_script_suite.py`)

These scripts follow established patterns ({term}`ADR-26001`, {term}`ADR-26002`, {term}`ADR-26011`) and have comprehensive test suites. The codebase now represents a mature, battle-tested validation framework.

**The catalyst for extraction:** Multiple new documentation repositories are planned that would benefit from identical validation infrastructure. Copying scripts between repos leads to drift, duplicated maintenance, and inconsistent behavior.

**Current coupling:** Repository-specific configuration (exclusion patterns, paths) is hardcoded in `paths.py`. This must be externalized for the engine to be reusable.

## Decision

We will extract the validation scripts into a **standalone pip-installable Python package** named `docs-validation-engine` (or similar). The package will:

1. **Provide CLI entry points** for each validation script
2. **Read configuration from `pyproject.toml`** in the consuming repository under `[tool.docs-validator]`
3. **Integrate with pre-commit** as a remote repository hook source
4. **Maintain backward compatibility** with current script interfaces

**Package structure:**

```
docs-validation-engine/
├── pyproject.toml
├── src/
│   └── docs_validator/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py           # Configuration loader
│       ├── check_broken_links.py
│       ├── check_link_format.py
│       ├── check_script_suite.py
│       ├── jupytext_sync.py
│       ├── jupytext_verify_pair.py
│       ├── check_api_keys.py
│       └── check_json_files.py
└── tests/
```

**Configuration schema (in consuming repos):**

```toml
[tool.docs-validator]
exclude_dirs = ["drafts", ".venv", "node_modules"]
exclude_files = [".aider.chat.history.md"]
exclude_link_strings = ["example.com", "placeholder"]
scripts_dir = "tools/scripts"
tests_dir = "tools/tests"
docs_dir = "tools/scripts"
```

**Pre-commit integration:**

```yaml
repos:
  - repo: https://github.com/username/docs-validation-engine
    rev: v0.1.0
    hooks:
      - id: check-broken-links
      - id: check-link-format
      - id: jupytext-sync
```

## Consequences

### Positive

- **Single Source of Truth:** All documentation repos share identical, versioned validation logic.
- **Reduced Maintenance:** Bug fixes and improvements propagate to all consumers via version updates.
- **Faster Repo Bootstrap:** New repos only need to add a dependency and minimal configuration.
- **Community Potential:** The package can be open-sourced for broader MyST/Jupytext community use.
- **Clear Versioning:** Semantic versioning allows consumers to pin stable versions while the engine evolves.

### Negative

- **Initial Extraction Effort:** Refactoring for configurability requires upfront investment. **Mitigation:** Phased approach—extract core scripts first, add configuration layer incrementally.
- **Version Coordination:** Breaking changes require coordinated updates across repos. **Mitigation:** Strict semantic versioning; maintain backward compatibility in minor versions.
- **Dependency Management:** Consumers add an external dependency. **Mitigation:** Package remains zero-dependency (stdlib only) per SVA principles.
- **Testing Complexity:** Must test both the package and integration with consuming repos. **Mitigation:** Comprehensive integration test suite using fixtures that simulate real repo structures.

## Alternatives

- **Git Submodule:** Rejected due to submodule management complexity and poor developer experience.
- **Copy-Paste with Manual Sync:** Rejected as it guarantees drift and multiplies maintenance burden.
- **Monorepo:** Considered but rejected; the engine serves repos with different lifecycles and ownership.
- **Template Repository:** Rejected because updates don't propagate to existing repos.

## References

- {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
- {term}`ADR-26002`: Adoption of the Pre-commit Framework
- {term}`ADR-26011`: Formalization of the Mandatory Script Suite Workflow
- Development Plan: `misc/plan/docs_validation_engine_development_plan.md`

## Participants

1. Vadim Rudakov
2. Claude (AI Engineering Advisor)
