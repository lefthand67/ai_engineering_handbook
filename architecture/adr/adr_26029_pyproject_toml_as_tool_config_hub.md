
---
title: pyproject.toml as Tool Configuration Hub
date: 2026-02-16
tags:
- governance
- workflow
options:
  token_size: 1131
  id: 26029
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-16'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: 2026-02-16.
---
# ADR-26029: pyproject.toml as Tool Configuration Hub

## Date

2026-02-16

## Status

Accepted

## Context

Scripts in `tools/scripts/` need shared, machine-readable configuration — valid commit types, CHANGELOG section mappings, ArchTag-required types, and similar domain constants. Previously these were hardcoded as Python constants duplicated across scripts, creating drift risk when conventions evolved.

The hub-spoke architecture ({term}`ADR-26020`) adds a further constraint: configuration must travel with the package when a module is extracted to a spoke repository. A config mechanism tied to the monorepo layout (e.g., a shared `paths.py` constant) would not survive extraction.

## Decision

`pyproject.toml [tool.X]` sections are the canonical location for machine-readable tool configuration in this repository and its spoke packages.

### Why pyproject.toml

- **stdlib support**: `tomllib` is available since Python 3.11, requiring no external dependencies.
- **Package portability**: config travels with the package when extracted to a spoke repo ({term}`ADR-26020`}).
- **Ecosystem convention**: `black`, `ruff`, `pytest`, `mypy`, and `commitizen` all use `[tool.X]` — the pattern is familiar to any Python developer.
- **TOML preserves key order**: enables ordered mappings (e.g., CHANGELOG section ordering matters for display).
- **Single file**: avoids proliferating per-tool config files (`commit_convention.yml`, `adr_config.yml`, etc.).

### Loading convention

Scripts load config via `tomllib` (stdlib) and expose parsed values as module-level constants for testability:

```python
import tomllib
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"
with _PYPROJECT.open("rb") as f:
    _CONFIG = tomllib.load(f)["tool"]["commit-convention"]

VALID_TYPES: list[str] = _CONFIG["valid-types"]
```

### What NOT to put in pyproject.toml

- **Path constants** → `tools/scripts/paths.py` (Python-native, imports cleanly)
- **Build/CI config** → `.pre-commit-config.yaml`, `quality.yml` (tool-specific formats)
- **MyST config** → `myst.yml` (MyST-specific toolchain)
- **Governance validation rules** → `.vadocs/` directory ({term}`ADR-26036`, {term}`ADR-26054`)

### First use

`[tool.commit-convention]` — valid types, ArchTag-required types, and type-to-section mapping for CHANGELOG generation. Consumed by `validate_commit_msg.py` and `generate_changelog.py` ({term}`ADR-26024`).

## Consequences

### Positive

- **Single source of truth**: commit types and section mappings are defined once and consumed by all scripts.
- **Package-portable**: `pyproject.toml` is the standard Python package metadata file — config survives spoke extraction.
- **stdlib-only**: `tomllib` requires no additional dependencies.
- **IDE support**: most editors provide TOML syntax highlighting and validation.

### Negative / Risks

- **TOML is less expressive than YAML** for deeply nested or complex config (no anchors, limited nesting). **Mitigation**: keep `[tool.X]` sections flat; use governance configs in `.vadocs/` for deeply nested validation rules ({term}`ADR-26036`).
- **File size growth**: as more tools add `[tool.X]` sections, `pyproject.toml` grows. **Mitigation**: each section is self-contained and clearly commented; the file remains navigable.

## Alternatives

- **Dedicated YAML files** (e.g., `commit_convention.yml`): Rejected — proliferates config files and requires `pyyaml` dependency for what `tomllib` handles natively.
- **Extend `paths.py`** with domain constants: Rejected — mixes path resolution concerns with domain configuration, violating single-responsibility.
- **`.commitlintrc.yml`**: Rejected — implies the Node.js `commitlint` toolchain, which was rejected in {term}`ADR-26003`.

## References

- {term}`ADR-26020`: Hub-Spoke Ecosystem Architecture
- {term}`ADR-26024`: Structured Commit Bodies and Automated Changelog
- {term}`ADR-26003`: Conventional Commits Standard
- [PEP 518 — Specifying Minimum Build System Requirements](https://peps.python.org/pep-0518/)
- [`pyproject.toml [tool.commit-convention]`](/pyproject.toml) — first implementation

## Participants

1. Vadim Rudakov
2. Claude Opus 4.6
