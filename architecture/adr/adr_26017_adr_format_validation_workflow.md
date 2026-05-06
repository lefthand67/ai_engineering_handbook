
---
title: ADR Format Validation Workflow
date: 2026-02-01
tags:
- governance
- documentation
- ci
options:
  token_size: 820
  id: 26017
  status: accepted
  superseded_by: null
  type: adr
  version: 1.0.0
  birth: '2026-02-01'
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
description: ADR Format Validation Workflow.
---
# ADR-26017: ADR Format Validation Workflow

## Title

ADR Format Validation Workflow

## Date

2026-02-01

## Status

Accepted

## Context

Architecture Decision Records (ADRs) are critical governance artifacts that document significant technical decisions. Without consistent format enforcement, ADRs can drift in structure, making them harder to maintain and parse programmatically.

Previous validation (`check_adr.py`) only covered:
- Index synchronization
- Status value validation
- Title consistency between header and frontmatter

Missing validations led to inconsistent ADRs:
- Some lacked required frontmatter fields (id, date, tags)
- Date formats varied (ISO vs text dates)
- Tags were undefined or inconsistent
- Required sections (Context, Decision, Consequences) were sometimes missing

The ADR template (`adr_template.md`) defined expected structure, but there was no automated enforcement.

## Decision

We will implement comprehensive ADR format validation in `check_adr.py` with config-driven rules stored in `adr.conf.json`.

**Validation rules added:**
1. **Required frontmatter fields**: id, title, date, status, tags
2. **Date format**: Must match YYYY-MM-DD (ISO 8601)
3. **Tag validation**: Only tags from predefined list in config
4. **Required sections**: Context, Decision, Consequences, Alternatives, References, Participants

**Migration support:**
- New `--migrate` flag to add YAML frontmatter to legacy ADRs
- Extracts status from `## Status` section
- Uses file modification date as `date` field
- Adds default tags

**Single Source of Truth:**
All validation rules defined in `adr.conf.json` to avoid drift between template and validator.

## Consequences

### Positive

- Consistent ADR format across all records
- Early error detection during CI/pre-commit
- Self-documenting configuration (adr.conf.json)
- Legacy ADRs can be migrated automatically
- ADRs are parseable by other tools (documentation generators, search)

### Negative / Risks

- Initial migration effort for non-compliant ADRs. **Mitigation:** `--migrate` flag automates frontmatter generation.
- Stricter validation may require updates to existing ADRs. **Mitigation:** Run `--verbose` to identify issues before enforcement.
- Adding new tags requires config update. **Mitigation:** Config is version-controlled and documented.

## Alternatives

1. **Manual review only**: Rejected - doesn't scale, inconsistent enforcement.
2. **Separate linter tool**: Rejected - adds dependency, duplicates ADR parsing logic.
3. **JSON Schema validation**: Rejected - YAML frontmatter validation needs custom logic for section detection.
4. **IDE-based validation**: Rejected - not portable across editors, no CI integration.

## References

- [ADR template](/architecture/adr/adr_template.md)
- {term}`ADR-26036` — Config file location and naming conventions (`.vadocs/` directory)
- [ADR 26016: Metadata-Driven ADR Lifecycle](/architecture/adr/adr_26016_metadata_driven_architectural_records_life.md)
- [check_adr.py documentation](/tools/docs/scripts_instructions/check_adr_py_script.ipynb)

## Participants

1. Claude Code (implementation)
2. Repository maintainers (review)
