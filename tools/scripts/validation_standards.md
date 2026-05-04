---
title: Validation Script Standards
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: '2026-05-04'
description: Engineering standards for all validation scripts (quality gates) in tools/scripts/.
tags:
- governance
- documentation
options:
  type: guide
  birth: '2026-05-04'
  version: 1.0.0
  token_size: 743
---
# Validation Script Standards

This document defines the engineering standards for all validation scripts (quality gates) within the `tools/scripts/` directory. These scripts are designed to be consumed primarily by AI agents via pre-commit hooks.

## 1. Config-Driven Logic (Hub-and-Spoke)

Validation rules must never be hardcoded in Python. Logic must be decoupled from policy using a Hub-and-Spoke configuration pattern.

### The Hub (`.vadocs/conf.json`)
The hub serves as the central vocabulary for the entire repository. It defines:
- Global tags and their descriptions.
- Common date formats.
- Universal field requirements.

### The Spokes (`.vadocs/types/<type>.conf.json`)
Each document type (e.g., `adr`, `evidence`, `analysis`) has its own spoke configuration. The spoke defines:
- **Required Fields:** Which fields must be present in the frontmatter.
- **Value Constraints:** Allowed values for specific fields.
- **Parent Pointer:** A reference to the hub or a higher-level config to inherit global rules.

**Benefit:** Policy changes (e.g., adding a mandatory `version` field to all ADRs) are performed by editing JSON, not by modifying code.

---

## 2. Agent-Actionable Reporting

Since these scripts are consumed by AI agents, the output must be optimized for **zero-ambiguity navigation**.

### The Reporting Contract
Every error must follow this exact format:
`{file_path}:{field} [{error_type}] — {message} [{config_source}]`

- **`file_path`**: The absolute path to the file. Never use `unknown` or relative paths.
- **`field`**: The specific field that failed (e.g., `:status`, `:authors`).
- **`error_type`**: A category for the error (e.g., `[frontmatter]`, `[naming]`, `[link]`).
- **`message`**: A clear, actionable instruction on how to fix the error.
- **`config_source`**: A pointer to the exact config file and rule that triggered the failure (e.g., `[evidence.conf.json → required_fields]`).

### Implementation Pattern
Use a standardized `ValidationError` dataclass to ensure consistency:

```python
@dataclass
class ValidationError:
    file_path: Path
    error_type: str
    message: str
    field: str | None = None
    config_source: str = "..."
```

---

## 3. Operational Rules

### No Side Effects
Validation scripts must be **read-only**.
- **Forbidden:** Automatically modifying files, updating indices, or staging changes.
- **Allowed:** Reporting errors and returning a non-zero exit code.
- **Exception:** If a script provides a `--fix` flag, the modifications must be explicit, logged, and subject to the same review process as any other code change.

### Exit Code Contract
- `0`: All files passed validation.
- `1`: One or more validation errors were found.
- `>1`: A system error occurred (e.g., config file missing, crash).
