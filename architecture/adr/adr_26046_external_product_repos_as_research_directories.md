
---
title: External Product Repos as Research Directories
authors:
- name: Vadim Rudakov
  email: rudakow.wadim@gmail.com
date: 2026-04-06
description: Governance for directories containing nested git repos of external products
  used for comparative source-level research — centralized path registry with relocation
  safety.
tags:
- architecture
- agents
- governance
options:
  type: adr
  birth: 2026-04-06
  version: 0.1.0
  token_size: 1237
  id: 26046
  status: proposed
  superseded_by: null
---
<!-- Quality guidelines: /architecture/architecture_decision_workflow_guide.md -->

# ADR-26046: External Product Repos as Research Directories

## Date

2026-04-06

## Status

proposed

## Context

This repo contains directories of nested git repositories — external products cloned in for source-level comparative research. These directories must be excluded from parent git tracking, validation scripts, and documentation builds.

Their exclusion paths are defined independently in multiple places: git tracking config, the shared path utility module consumed by all validation scripts, the documentation build config, and whichever script manages the repos. There is no single place that answers "which directories contain external product repos?" — you must grep for the path across the codebase.

When the repo was restructured to separate component layers from assembled products, 3 of the 4 exclusion references broke silently. The paths they pointed to no longer existed, but no validation caught it. The break was only discovered manually. This is a structural fragility: any future rename or move of a research directory repeats the same failure mode.

The shared path utility module (`paths.py`) contains an acknowledged techdebt note: "Exclusion constants will migrate to `.vadocs/validation/`". The external product repo case is the first and only consumer of those constants — making it the trigger to resolve the debt.

{term}`ADR-26020` governs the hub-and-spoke ecosystem model but does not address the case of external git repos cloned into this repo. As more products are added for source-level study, the problem compounds.

## Decision

### 1. Registry as Single Source of Truth

The complete set of directories containing nested git repos of external products will be maintained in a single registry config. The registry is the authoritative record of "which directories contain external product repos" and is the only place these paths are defined.

### 2. All Consumers Read from the Registry

Every system that needs to exclude a research directory — validation scripts, documentation builds, git tracking, management operations — will obtain the path from the registry. No consumer may define its own copy of a research directory path.

### 3. Safe Relocation Is Supported

When a research directory is renamed, all consumers must be updated atomically. A mechanism exists to perform this update as a single operation, verifying that every consumer resolves correctly after the change.

### 4. Drift Is Detected Before Commit

Any manual edit to exclusion lists that is not reflected in the registry will be caught by a pre-commit validation hook.

## Consequences

### Positive

- **Single edit point**: adding a new research directory means one config entry + running the sync command
- **Safe renames**: relocation updates all consumers atomically, eliminating the silent breakage that motivated this ADR
- **Extensible**: the same registry pattern handles future external product repos without ad-hoc path duplication
- **Self-documenting**: the registry serves as an index of all external products under source-level study, answering "what are we researching?" without grepping the codebase
- **Resolves paths.py techdebt**: "Exclusion constants will migrate to `.vadocs/validation/`" is addressed for this use case

### Negative / Risks

- **Registry drift**: manual edits to exclusion files that bypass the registry cause divergence. **Mitigation**: validation hook in pre-commit pipeline catches drift before commit.
- **New script dependency**: a management script for external product repos must be created. **Mitigation**: follows the dyad pattern (script + test) from {term}`ADR-26045`.
- **External git repos increase repo disk footprint**: cloned repos add weight even when excluded from tracking. **Mitigation**: directories are excluded from git; repos are fetched on-demand via the management script, not all at once.
- **Schema maintenance**: the registry config needs its own schema. **Mitigation**: follows JSON schema convention from {term}`ADR-26054`; schema lives alongside the config.

## Alternatives

### Keep hardcoded constants (status quo)
Rejected — the rename proved this is fragile. Every structural change to the repo layout silently breaks references in `.gitignore`, `paths.py`, and `myst.yml`.

### Put config in `pyproject.toml`
Rejected — {term}`ADR-26029` reserves `pyproject.toml` for tool configuration (linters, formatters, test runners). This is an operational governance concern, not a tool config.

### Put config in `.vadocs/types/`
Rejected — `.vadocs/types/` is for document-type configs (ADR, evidence). External product repos are not a document type — they are an infrastructure concern, not a content type.

## References

- {term}`ADR-26020` — Hub-and-Spoke Ecosystem
- {term}`ADR-26029` — Tool Configuration in pyproject.toml
- {term}`ADR-26036` — Config File Location and Naming Conventions
- {term}`ADR-26045` — Script Suite
- {term}`ADR-26054` — JSON as Governance Config Format
- `tools/scripts/paths.py` — techdebt comment: "Exclusion constants will migrate to `.vadocs/validation/`"

## Participants

1. Vadim Rudakov
2. Qwen Code (ADR drafting, context analysis)
