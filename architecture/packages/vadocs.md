---
title: "vadocs - Documentation Validation Engine"
authors:
  - name: Vadim Rudakov
    email: rudakow.wadim@gmail.com
date: "2026-05-03"
description: "Documentation of the vadocs validation engine, its purpose, and core capabilities."
tags: [development, governance, architecture]
---
---
options:
  type: guide
  version: 1.0.0
  birth: '2026-03-02'
  token_size: 1080
---
# vadocs - Documentation Validation Engine

## Motivation

**Documentation-as-Code** treats documentation with the same rigor as software: version control, automated testing, CI/CD pipelines, and structured metadata. This approach enables:

- **Consistency** - Enforced standards across all documents
- **Automation** - Pre-commit hooks catch issues before merge
- **Discoverability** - YAML frontmatter enables search, filtering, and index generation
- **Quality Gates** - CI pipelines validate documentation like code

However, implementing Documentation-as-Code requires validation tooling:

- Is the frontmatter complete and valid?
- Are cross-references (like `{term}` in MyST) correctly formatted?
- Are required sections present in ADRs?
- Is the index synchronized with individual documents?

**vadocs** provides this validation infrastructure as a reusable package, eliminating the need to copy scripts between documentation repositories.

## Purpose

A reusable Python package for validating structured documentation with YAML frontmatter. Extracted from `tools/scripts/` per {term}`ADR-26012`.

## Target Users

- **Documentation maintainers** who want automated quality checks
- **Teams adopting ADRs** (Architecture Decision Records) with structured workflows
- **MyST/Jupytext users** who need frontmatter and cross-reference validation
- **DevOps engineers** integrating documentation validation into CI/CD

## Scope

### In Scope

- YAML frontmatter validation (required fields, allowed values)
- ADR-specific validation (status, tags, sections, term references)
- Configuration loading from YAML files
- Validator and Fixer base classes for extensibility

### Out of Scope

- CLI interface (deferred to v0.2.0)
- pyproject.toml `[tool.vadocs]` config loading (deferred)
- Project scaffolding (`vadocs init`)
- Link validation (separate concern)
- Jupytext sync (separate concern)

## Required Capabilities

### Core Models

- `Document` - Represents a file with path, content, frontmatter, and doc_type
- `ValidationError` - Structured error with path, line, error_type, message, suggestion
- `SyncField` / `SyncResult` - For bi-directional sync operations

### Validators

| Validator | Purpose |
|-----------|---------|
| `FrontmatterValidator` | Generic YAML frontmatter validation |
| `AdrValidator` | ADR-specific validation (extends frontmatter) |
| `AdrTermValidator` | MyST `{term}` reference validation |

### Fixers

| Fixer | Purpose |
|-------|---------|
| `AdrFixer` | Auto-fix ADR frontmatter issues |
| `SyncFixer` | Bi-directional YAML ↔ markdown sync |

### Configuration

- `load_config(path)` - Load validation rules from YAML file
- Support for: required_fields, valid statuses, valid tags, date format, term reference patterns

## Interface Contracts

### Validator Protocol

```python
class Validator(ABC):
    name: str

    def validate(self, document: Document, config: dict) -> list[ValidationError]: ...
    def supports(self, document: Document) -> bool: ...
```

### Fixer Protocol

```python
class Fixer(ABC):
    name: str

    def fix(self, document: Document, errors: list[ValidationError], config: dict) -> FixResult: ...
    def supports(self, document: Document) -> bool: ...
```

## Governing ADRs

- {term}`ADR-26012`: Extraction of Documentation Validation Engine (founding document)
- {term}`ADR-26001`: Use of Python and OOP for Git Hook Scripts
- {term}`ADR-26011`: Formalization of the Mandatory Script Suite Workflow
- {term}`ADR-26020`: Hub-and-Spoke Ecosystem Documentation Architecture

## Version Roadmap

| Version | Milestone |
|---------|-----------|
| v0.1.0 | Library-only PoC with core validators (current) |
| v0.2.0 | CLI + pyproject.toml config loading |
| v0.3.0 | Index sync validation |
| v0.4.0 | Additional validators (broken links, jupytext) |
| v1.0.0 | PyPI release, stable API |

## Implementation

**Repository**: `packages/vadocs/` (PoC, will move to standalone repo)

**Tests**: 79 passing

**Installation** (after move to standalone repo):
```bash
uv add "vadocs @ git+https://github.com/<org>/vadocs.git"
```
