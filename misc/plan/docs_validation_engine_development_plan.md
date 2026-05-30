---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
---

title: 'Development Plan: docs-validation-engine'
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: "Detailed development plan for extracting validation scripts into a standalone Python package."
tags:
  - development
  - ci
  - documentation
options:
  type: guide
  version: "0.1.0"
  birth: "2026-01-27"
  token_size: 2304
---
# Development Plan: docs-validation-engine

+++

## Overview

This document outlines the development plan for extracting the validation scripts from `tools/scripts/` into a standalone, reusable Python package. See {term}`ADR-26012` for the architectural decision and rationale.

+++

## Motivation: Why Extract?

### The Problem

As the number of documentation repositories grows, maintaining identical validation logic across them becomes unsustainable:

1. **Copy-Paste Drift:** Scripts copied between repos diverge over time as fixes are applied inconsistently.
2. **Duplicated Testing:** Each repo maintains its own test suite for identical logic.
3. **Inconsistent Behavior:** Different repos may have subtly different validation rules, causing confusion.
4. **Bootstrap Overhead:** New repos require significant setup effort to replicate the validation infrastructure.

### The Solution

A **standalone pip package** that:

- Provides a single source of truth for validation logic
- Allows semantic versioning for controlled updates
- Integrates seamlessly with pre-commit hooks
- Supports per-repo configuration without code changes

### Target Consumers

1. **ai_engineering_book** (this repository) - Primary development testbed
2. **Future documentation repositories** - Planned projects using MyST/Jupytext workflow
3. **Community** - Potential open-source release for MyST/Jupyter ecosystem

+++

## Architecture

### Package Structure

```
docs-validation-engine/
├── pyproject.toml              # Package metadata, dependencies, entry points
├── README.md                   # Usage documentation
├── LICENSE                     # MIT or similar
├── src/
│   └── docs_validator/
│       ├── __init__.py         # Version, public API
│       ├── cli.py              # Click-based CLI dispatcher
│       ├── config.py           # Configuration loader (pyproject.toml)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── file_finder.py  # Shared file discovery logic
│       │   ├── link_extractor.py
│       │   └── reporter.py     # Shared reporting/output logic
│       ├── validators/
│       │   ├── __init__.py
│       │   ├── broken_links.py
│       │   ├── link_format.py
│       │   ├── api_keys.py
│       │   ├── json_files.py
│       │   └── script_suite.py
│       └── sync/
│           ├── __init__.py
│           ├── jupytext_sync.py
│           └── jupytext_verify.py
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── test_config.py
    ├── test_broken_links.py
    ├── test_link_format.py
    └── ...
```

### Configuration Schema

Consuming repositories configure the engine via `pyproject.toml`:

```toml
[tool.docs-validator]
# Directory exclusions (applied to all validators)
exclude_dirs = [
    "drafts",
    ".venv",
    "node_modules",
    ".git",
]

# File exclusions
exclude_files = [
    ".aider.chat.history.md",
    "CHANGELOG.md",
]

# Link strings to ignore (for broken links checker)
exclude_link_strings = [
    "example.com",
    "placeholder",
    "your-domain.com",
]

# Script suite paths (for script_suite validator)
[tool.docs-validator.script_suite]
scripts_dir = "tools/scripts"
tests_dir = "tools/tests"
docs_dir = "tools/docs/scripts_instructions"
excluded_scripts = ["paths.py", "__init__.py"]
```

### CLI Interface

```bash
# Individual validators
docs-validator check-broken-links [--paths PATH...] [--verbose]
docs-validator check-link-format [--paths PATH...] [--fix | --fix-all]
docs-validator check-api-keys [--paths PATH...]
docs-validator check-json-files [--paths PATH...]
docs-validator check-script-suite [--verbose]

# Jupytext operations
docs-validator jupytext-sync [--paths PATH...]
docs-validator jupytext-verify [--paths PATH...]

# Run all validators
docs-validator check-all [--paths PATH...]
```

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml in consuming repos
repos:
  - repo: https://github.com/username/docs-validation-engine
    rev: v0.1.0
    hooks:
      - id: check-broken-links
        types: [markdown]
      - id: check-link-format
        types: [markdown]
      - id: check-api-keys
        types_or: [python, markdown, json]
      - id: check-json-files
        types: [json]
      - id: jupytext-sync
        types_or: [markdown, jupyter]
      - id: jupytext-verify
        types_or: [markdown, jupyter]
      - id: check-script-suite
        types: [python]
```

+++

## Development Phases

### Phase 1: Foundation (Week 1-2)

**Goal:** Create package skeleton with configuration system.

**Tasks:**

1. Initialize new repository with `uv init`
2. Set up package structure (`src/docs_validator/`)
3. Implement `config.py` - load from `pyproject.toml`
4. Create CLI skeleton with Click
5. Add CI/CD pipeline (GitHub Actions)
6. Write configuration tests

**Deliverable:** Empty package that reads configuration and provides CLI help.

### Phase 2: Core Extraction (Week 3-4)

**Goal:** Extract and refactor existing validators.

**Tasks:**

1. Extract shared utilities (`file_finder.py`, `reporter.py`, `link_extractor.py`)
2. Port `check_broken_links.py` with configuration support
3. Port `check_link_format.py` with configuration support
4. Port remaining validators (`api_keys`, `json_files`, `script_suite`)
5. Migrate existing tests, adapt for new structure
6. Ensure 100% test coverage

**Deliverable:** All validators working via CLI with configuration.

### Phase 3: Jupytext Integration (Week 5)

**Goal:** Extract notebook synchronization tools.

**Tasks:**

1. Port `jupytext_sync.py`
2. Port `jupytext_verify_pair.py`
3. Add Jupytext as optional dependency
4. Write integration tests with real notebook fixtures

**Deliverable:** Full Jupytext support in package.

### Phase 4: Pre-commit Hooks (Week 6)

**Goal:** Enable pre-commit integration.

**Tasks:**

1. Create `.pre-commit-hooks.yaml` in package repo
2. Define hook entry points for each validator
3. Test integration with this repository as consumer
4. Document hook configuration options

**Deliverable:** Package usable as pre-commit repo source.

### Phase 5: Migration & Documentation (Week 7-8)

**Goal:** Migrate this repository to use the package.

**Tasks:**

1. Add `docs-validation-engine` as dev dependency
2. Update `.pre-commit-config.yaml` to use remote hooks
3. Remove local scripts (keep as reference/archive)
4. Update all documentation to reflect new workflow
5. Write comprehensive README for the package
6. Create migration guide for future repos

**Deliverable:** This repo fully migrated; package ready for v1.0.0.

+++

## Design Decisions

### Why Click for CLI?

- Industry standard for Python CLIs
- Built-in help generation
- Easy subcommand composition
- Decorator-based, clean syntax

### Why pyproject.toml for Configuration?

- Already present in Python projects
- Standard location for tool configuration (`[tool.X]`)
- No additional config files needed
- Supports complex nested structures

### Why Zero External Dependencies (Core)?

- Follows SVA (Smallest Viable Architecture) principle
- Faster installation
- No dependency conflicts
- Jupytext is optional (only needed for sync commands)

### Why Semantic Versioning?

- Clear compatibility guarantees
- Consumers can pin to major versions
- Breaking changes are explicit

+++

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Configuration complexity | Medium | Medium | Sensible defaults; minimal required config |
| Breaking changes affecting consumers | Medium | High | Strict semver; deprecation warnings before removal |
| Test coverage gaps during extraction | Low | High | Migrate tests alongside code; CI enforces coverage |
| Performance regression | Low | Medium | Benchmark before/after; optimize hot paths |
| Scope creep | Medium | Medium | Stick to existing functionality; new features after v1.0 |

+++

## Success Criteria

1. **Functional Parity:** All existing validation behavior preserved
2. **Test Coverage:** >= 90% line coverage
3. **Documentation:** README, migration guide, API docs
4. **Performance:** No measurable slowdown vs current scripts
5. **Adoption:** This repository successfully migrated
6. **Usability:** New repo setup < 15 minutes with package

+++

## Open Questions

1. **Package Name:** `docs-validation-engine`, `myst-docs-validator`, `jupytext-validator`?
2. **Hosting:** GitHub (public) or private registry?
3. **License:** MIT? Apache 2.0?
4. **Minimum Python Version:** 3.11? 3.12? 3.13?

+++

## References

- {term}`ADR-26012`: Extraction of Documentation Validation Engine
- {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
- {term}`ADR-26002`: Adoption of the Pre-commit Framework
- {term}`ADR-26011`: Formalization of the Mandatory Script Suite Workflow
- [Pre-commit: Creating new hooks](https://pre-commit.com/#creating-new-hooks)
- [Click Documentation](https://click.palletsprojects.com/)
